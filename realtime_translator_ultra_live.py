# -*- coding: utf-8 -*-
"""
realtime_translator_ultra_live.py
---------------------------------
Full realtime pipeline with:
- Mic input (optional) or WAV file input
- Simple energy VAD (no native deps) for segmentation
- faster-whisper ASR if available, fallback DummyASR otherwise
- Automatic source language detection (with faster-whisper)
- Runtime output-language switching (console commands)
- VoiceVox TTS over HTTP with connection pooling
- Optional WebSocket broadcast (if `websockets` is installed), otherwise dummy WS
- Optional local audio playback (if `sounddevice` is installed), otherwise muted
- Continues translating & synthesizing even if **no clients** are connected

Usage examples (CPU-only):
  python realtime_translator_ultra_live.py --asr-model tiny --asr-compute int8 --target-lang ja --show-latency
  python realtime_translator_ultra_live.py --wav sample.wav --target-lang en --show-latency
  python realtime_translator_ultra_live.py --ws-port 8765 --target-lang ja --auto-bidir --show-latency

Console commands while running:
  lang <code>      → set target (e.g., lang ja / lang en / lang es)
  list             → show example codes
  auto-bidir on    → enable en↔ja auto swap based on detected source
  auto-bidir off   → disable auto swap
  show             → show current target/auto-bidir
  help             → list commands

This file is designed to run in restricted environments:
- No required native deps (webrtcvad optional; sounddevice optional)
- On Windows/macOS/Linux without GPU (int8 CPU path)
"""
from __future__ import annotations
import argparse
import collections
import io
import json
import os
import queue
import sys
import threading
import time
from dataclasses import dataclass
from typing import Deque, Dict, Iterable, List, Optional, Tuple

import numpy as np
import requests

# ===================== Optional deps ===================== #
try:
    from faster_whisper import WhisperModel  # type: ignore
    _FW_OK = True
except Exception:
    WhisperModel = None  # type: ignore
    _FW_OK = False

try:
    import sounddevice as sd  # type: ignore
    _SD_OK = True
except Exception:
    sd = None  # type: ignore
    _SD_OK = False

try:
    import websockets  # type: ignore
    import asyncio
    _WS_OK = True
except Exception:
    websockets = None  # type: ignore
    asyncio = None  # type: ignore
    _WS_OK = False

# ========================================================= #

@dataclass
class RTConfig:
    # Audio
    sample_rate: int = 16000
    block_ms: int = 20  # 20ms frames
    input_device: Optional[int] = None
    output_device: Optional[int] = None
    play_audio: bool = False  # local playback if sounddevice present
    wav_path: Optional[str] = None  # if set, stream from wav instead of mic

    # ASR
    asr_model: str = "tiny"
    asr_compute: str = "int8"  # int8/float16/float32
    asr_beam: int = 1
    asr_lang: Optional[str] = None  # None = auto detect

    # MT/TTS
    target_lang: str = "ja"
    speaker_id: int = 1
    tts_speed: float = 1.1
    voicevox_url: str = "http://localhost:50021"

    # Behavior
    auto_bidir: bool = False  # en↔ja automatic swap

    # Diagnostics
    show_latency: bool = False

    # WebSocket
    ws_port: Optional[int] = None  # if set and websockets available, serve WS


# ===================== Utilities ===================== #

def float32_to_int16(audio: np.ndarray) -> bytes:
    audio = np.clip(audio, -1.0, 1.0)
    return (audio * 32767).astype(np.int16).tobytes()


def int16_to_float32(pcm16: bytes) -> np.ndarray:
    a = np.frombuffer(pcm16, dtype=np.int16).astype(np.float32)
    return a / 32768.0


def compute_energy(pcm16: bytes) -> float:
    a = np.frombuffer(pcm16, dtype=np.int16).astype(np.float32)
    a /= 32768.0
    return float(np.sqrt(np.mean(a * a)) if a.size else 0.0)


# ===================== Latency tracker ===================== #

class Latency:
    def __init__(self, window: int = 200):
        self.lock = threading.Lock()
        self.data: Deque[Dict[str, float]] = collections.deque(maxlen=window)
    def add(self, **kv):
        with self.lock:
            self.data.append(kv)
    def report(self) -> str:
        with self.lock:
            n = len(self.data)
        return f"Latency samples: {n}"


# ===================== Target language manager ===================== #

class TargetLangManager:
    def __init__(self, initial: str, auto_bidir: bool = False):
        self._lock = threading.Lock()
        self._target = initial
        self._auto_bidir = auto_bidir
    def set_target(self, code: str):
        with self._lock:
            self._target = code.lower()
    def get_target(self) -> str:
        with self._lock:
            return self._target
    def set_auto_bidir(self, enabled: bool):
        with self._lock:
            self._auto_bidir = enabled
    def get_auto_bidir(self) -> bool:
        with self._lock:
            return self._auto_bidir
    def resolve_target(self, src_lang: Optional[str]) -> str:
        with self._lock:
            if self._auto_bidir and src_lang:
                s = src_lang.lower()
                if s.startswith('en'):
                    return 'ja'
                if s.startswith('ja'):
                    return 'en'
            return self._target


# ===================== ASR backends ===================== #

class DummyASR:
    def __init__(self, cfg: RTConfig):
        self.cfg = cfg
        print("[ASR] Using DummyASR (faster-whisper unavailable)")
    def transcribe_words(self, audio_f32: np.ndarray) -> Tuple[List[Tuple[str, float, float]], Optional[str]]:
        # Emits placeholder text to keep pipeline running
        dur = len(audio_f32) / max(1, self.cfg.sample_rate)
        return [("[speech_detected]", 0.0, dur)], None


class FWASR:
    def __init__(self, cfg: RTConfig):
        device = "cuda" if os.environ.get("FORCE_CUDA") else "cpu"
        print(f"[ASR] faster-whisper/{cfg.asr_model} on {device} ({cfg.asr_compute})")
        self.model = WhisperModel(cfg.asr_model, device=device, compute_type=cfg.asr_compute, num_workers=1)
        self.cfg = cfg
    def transcribe_words(self, audio_f32: np.ndarray) -> Tuple[List[Tuple[str, float, float]], Optional[str]]:
        segs, info = self.model.transcribe(
            audio_f32,
            beam_size=self.cfg.asr_beam,
            best_of=1,
            temperature=0.0,
            vad_filter=False,
            condition_on_previous_text=False,
            language=self.cfg.asr_lang,  # None = auto-detect
            word_timestamps=True,
        )
        detected_lang = getattr(info, 'language', None)
        words: List[Tuple[str, float, float]] = []
        for seg in segs:
            if getattr(seg, "words", None):
                for w in seg.words:
                    words.append((w.word.strip(), float(w.start or 0.0), float(w.end or 0.0)))
        if not words:
            text = " ".join(getattr(seg, "text", "").strip() for seg in segs if getattr(seg, "text", "").strip())
            if text:
                dur = len(audio_f32) / self.cfg.sample_rate
                words = [(text, 0.0, dur)]
        return words, detected_lang


def make_asr(cfg: RTConfig):
    if _FW_OK:
        try:
            return FWASR(cfg)
        except Exception as e:
            sys.stderr.write(f"[ASR] faster-whisper failed to init: {e}\nUsing DummyASR instead.\n")
    return DummyASR(cfg)


# ===================== MT/TTS ===================== #

class FastMT:
    def __init__(self, cfg: RTConfig):
        self.cfg = cfg
    def translate(self, text: str, target_lang: str) -> str:
        # Placeholder – replace with your SubtitleTranslator or provider
        return f"[to {target_lang}] {text}"


class VoiceVoxTTS:
    def __init__(self, cfg: RTConfig):
        self.cfg = cfg
        self.sess = requests.Session()
        adapter = requests.adapters.HTTPAdapter(pool_connections=4, pool_maxsize=4, max_retries=0)
        self.sess.mount("http://", adapter)
        print("[TTS] VoiceVox HTTP client ready")
    def synthesize(self, text: str) -> Tuple[np.ndarray, int]:
        if not text.strip():
            return np.zeros(0, dtype=np.int16), self.cfg.sample_rate
        base = self.cfg.voicevox_url.rstrip('/')
        # 1) audio_query
        r = self.sess.post(f"{base}/audio_query", params={"text": text, "speaker": self.cfg.speaker_id}, timeout=8)
        r.raise_for_status()
        q = r.json()
        q["speedScale"] = self.cfg.tts_speed
        # 2) synthesis
        r = self.sess.post(f"{base}/synthesis", params={"speaker": self.cfg.speaker_id}, json=q, timeout=12)
        r.raise_for_status()
        import wave
        with wave.open(io.BytesIO(r.content), "rb") as w:
            frames = w.readframes(w.getnframes())
            audio = np.frombuffer(frames, dtype=np.int16)
            sr = w.getframerate()
        return audio, sr  # VoiceVox is typically 24000 Hz


# ===================== Audio output ===================== #

class NullPlayer:
    def start(self):
        pass
    def stop(self):
        pass
    def queue(self, audio: np.ndarray, sr: int):
        # Always called even if no playback (to keep behavior consistent)
        print(f"[AudioOut] queued {len(audio)} samples @ {sr} Hz")


class SDPlayer:
    def __init__(self, cfg: RTConfig):
        self.cfg = cfg
        self.stream = None
        self.lock = threading.Lock()
        self.buffer: Deque[int] = collections.deque()
    def _callback(self, outdata, frames, time_info, status):
        if status:
            sys.stderr.write(f"[Audio] {status}\n")
        with self.lock:
            for i in range(frames):
                outdata[i, 0] = self.buffer.popleft() if self.buffer else 0
    def start(self):
        if not _SD_OK or not self.cfg.play_audio:
            return
        self.stream = sd.OutputStream(samplerate=self.cfg.sample_rate, channels=1, dtype="int16",
                                      callback=self._callback, blocksize=1024, device=self.cfg.output_device)
        self.stream.start()
    def stop(self):
        if self.stream:
            self.stream.stop(); self.stream.close(); self.stream = None
    def queue(self, audio: np.ndarray, sr: int):
        if not _SD_OK or not self.cfg.play_audio:
            print(f"[AudioOut] muted (len={len(audio)}, sr={sr})")
            return
        if sr != self.cfg.sample_rate:
            # naive resample to cfg.sample_rate (linear)
            x = np.linspace(0, 1, len(audio), endpoint=False)
            y = np.linspace(0, 1, int(len(audio) * self.cfg.sample_rate / sr), endpoint=False)
            audio = np.interp(y, x, audio.astype(np.float32)).astype(np.int16)
        with self.lock:
            self.buffer.extend(audio.tolist())
            # add small gap
            self.buffer.extend([0] * int(self.cfg.sample_rate * 0.03))


# ===================== WebSocket broadcast ===================== #

class DummyWS:
    def __init__(self):
        self._running = False
    def start(self):
        self._running = True
        print("[WS] dummy server started (no websockets module)")
    def stop(self):
        self._running = False
        print("[WS] dummy server stopped")
    def broadcast(self, src: str, tgt: str, timings: Dict[str, float], audio: Optional[np.ndarray], sr: int):
        # Intentionally no-op; pipeline should still synthesize
        pass


class WSServer:
    def __init__(self, port: int):
        self.port = port
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._clients: 'set[websockets.WebSocketServerProtocol]' = set()
        self._server = None
        self._running = False
    async def _handler(self, websocket, path):  # type: ignore[override]
        self._clients.add(websocket)
        try:
            async for _ in websocket:
                pass
        finally:
            self._clients.discard(websocket)
    async def _serve(self):
        self._server = await websockets.serve(self._handler, "0.0.0.0", self.port)
        await self._server.wait_closed()
    def start(self):
        """Start the WebSocket server in a background thread."""
        if not _WS_OK:
            print("[WS] websockets not available; using dummy")
            return
        if self._running:
            return
        self._running = True
        def runner():
            try:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
                self._loop.run_until_complete(self._serve())
            except Exception as e:
                sys.stderr.write(f"[WS] server failed: {e}\n")
        self._thread = threading.Thread(target=runner, daemon=True)
        try:
            self._thread.start()
            print(f"[WS] server running on ws://0.0.0.0:{self.port}")
        except RuntimeError as e:
            self._running = False
            sys.stderr.write(f"[WS] cannot start thread: {e}\n")
    def stop(self):
        if not _WS_OK:
            return
        if not self._running:
            return
        self._running = False
        if self._server and self._loop:
            self._loop.call_soon_threadsafe(self._server.close)
        if self._thread:
            try:
                self._thread.join(timeout=1.0)
            except RuntimeError:
                pass
    def broadcast(self, src: str, tgt: str, timings: Dict[str,float], audio: Optional[np.ndarray], sr: int):
        if not _WS_OK or not self._loop or not self._clients:
            return
        payload = json.dumps({
            "src": src, "tgt": tgt, "timings": timings,
            "has_audio": bool(audio is not None and len(audio) > 0), "sr": sr,
        })
        async def _send_all():
            to_remove = []
            for ws in list(self._clients):
                try:
                    await ws.send(payload)
                except Exception:
                    to_remove.append(ws)
            for ws in to_remove:
                self._clients.discard(ws)
        try:
            self._loop.call_soon_threadsafe(lambda: asyncio.create_task(_send_all()))
        except RuntimeError:
            pass


# ===================== Simple energy VAD ===================== #

class EnergyVAD:
    def __init__(self, cfg: RTConfig, noise_floor: float = 0.008, min_silence_ms: int = 250, max_segment_ms: int = 6000):
        self.cfg = cfg
        self.noise_floor = noise_floor
        self.min_silence_ms = min_silence_ms
        self.max_segment_ms = max_segment_ms
        self.frame_len = int(cfg.sample_rate * cfg.block_ms / 1000)
        self.frames: List[bytes] = []
        self.in_speech = False
        self.silence_ms = 0
        self.segment_start_ts = 0.0
    def add(self, frame_pcm16: bytes, timestamp: float) -> Optional[Tuple[bytes, float]]:
        if len(frame_pcm16) != self.frame_len * 2:
            return None
        energy = compute_energy(frame_pcm16)
        is_speech = energy >= self.noise_floor
        if is_speech:
            if not self.in_speech:
                self.segment_start_ts = timestamp
                self.in_speech = True
            self.frames.append(frame_pcm16)
            self.silence_ms = 0
        else:
            if self.in_speech:
                self.frames.append(frame_pcm16)
                self.silence_ms += self.cfg.block_ms
                if self.silence_ms >= self.min_silence_ms:
                    return self._finalize()
        if self.in_speech:
            dur_ms = len(self.frames) * self.cfg.block_ms
            if dur_ms >= self.max_segment_ms:
                return self._finalize()
        return None
    def _finalize(self) -> Tuple[bytes, float]:
        seg = b"".join(self.frames)
        start = self.segment_start_ts
        self.frames = []
        self.in_speech = False
        self.silence_ms = 0
        return seg, start


# ===================== Pipeline ===================== #

class Pipeline:
    def __init__(self, cfg: RTConfig, tlm: TargetLangManager, asr, mt: FastMT, tts: VoiceVoxTTS, player, ws, lat: Latency):
        self.cfg, self.tlm, self.asr, self.mt, self.tts, self.player, self.ws, self.lat = cfg, tlm, asr, mt, tts, player, ws, lat
    def process_segment(self, pcm16: bytes, start_ts: float):
        # Convert to float32 for ASR
        audio_f32 = int16_to_float32(pcm16)
        t0 = time.time()
        words, src_lang = self.asr.transcribe_words(audio_f32)
        asr_ms = (time.time() - t0) * 1000
        text = " ".join(w for w, _, _ in words).strip()
        if not text:
            return
        # Decide target
        target = self.tlm.resolve_target(src_lang)
        if src_lang:
            print(f"[ASR] detected={src_lang} → target={target}")
        # Translate
        t1 = time.time()
        tgt = self.mt.translate(text, target)
        mt_ms = (time.time() - t1) * 1000
        # TTS
        t2 = time.time()
        audio, sr = self.tts.synthesize(tgt)
        tts_ms = (time.time() - t2) * 1000
        total_ms = (time.time() - start_ts) * 1000
        # Playback (optional) and WS broadcast (always allowed)
        self.player.queue(audio, sr)
        self.ws.broadcast(text, tgt, {"asr": asr_ms, "mt": mt_ms, "tts": tts_ms, "total": total_ms}, audio, sr)
        # Stats
        if self.cfg.show_latency:
            print(f"[LAT] total={total_ms:.0f}ms (ASR {asr_ms:.0f} / MT {mt_ms:.0f} / TTS {tts_ms:.0f})")
        self.lat.add(asr=asr_ms, mt=mt_ms, tts=tts_ms, total=total_ms)


# ===================== Input sources ===================== #

def stream_from_wav(cfg: RTConfig, frame_len: int) -> Iterable[Tuple[bytes, float]]:
    import wave
    with wave.open(cfg.wav_path, "rb") as w:
        assert w.getnchannels() == 1, "only mono supported in this simple reader"
        assert w.getsampwidth() == 2, "expect 16-bit PCM"
        assert w.getframerate() == cfg.sample_rate, f"resample your wav to {cfg.sample_rate}Hz"
        block = frame_len
        while True:
            frames = w.readframes(block)
            if not frames:
                break
            yield frames, time.time()
            time.sleep(cfg.block_ms / 1000.0)


def stream_from_mic(cfg: RTConfig, frame_len: int) -> Iterable[Tuple[bytes, float]]:
    if not _SD_OK:
        raise RuntimeError("sounddevice not available; use --wav")
    q: queue.Queue[Tuple[bytes, float]] = queue.Queue(maxsize=200)
    def cb(indata, frames, time_info, status):
        if status:
            sys.stderr.write(f"[Mic] {status}\n")
        pcm = float32_to_int16(indata[:, 0])
        ts = time.time()
        try:
            q.put_nowait((pcm, ts))
        except queue.Full:
            try:
                q.get_nowait()
            except queue.Empty:
                pass
            q.put_nowait((pcm, ts))
    stream = sd.InputStream(samplerate=cfg.sample_rate, channels=1, dtype="float32",
                            blocksize=frame_len, callback=cb, device=cfg.input_device)
    stream.start()
    try:
        while True:
            try:
                yield q.get(timeout=0.1)
            except queue.Empty:
                yield b"\x00" * (frame_len * 2), time.time()
    finally:
        stream.stop(); stream.close()


# ===================== Console controls ===================== #

def start_console_controls(tlm: TargetLangManager):
    def _loop():
        print("\nCommands: 'lang <code>' | 'list' | 'auto-bidir on/off' | 'show' | 'help'\n")
        while True:
            try:
                line = input().strip()
            except EOFError:
                break
            if not line:
                continue
            cmd = line.lower()
            if cmd == 'help':
                print("Commands:\n  lang <code>      set target language (e.g., lang en, lang ja, lang es)\n  list             show a few example codes\n  auto-bidir on    enable EN↔JA automatic swap\n  auto-bidir off   disable swap (fixed target)\n  show             display current target and swap mode\n  help             this help\n")
            elif cmd.startswith('lang '):
                _, code = cmd.split(' ', 1)
                code = code.strip()
                if code:
                    tlm.set_target(code)
                    print(f"[CTL] target_lang → {code}")
            elif cmd == 'list':
                print("Examples: en (English), ja (Japanese), es (Spanish), fr (French), de (German), zh (Chinese)")
            elif cmd == 'auto-bidir on':
                tlm.set_auto_bidir(True)
                print("[CTL] auto_bidir → ON (en↔ja)")
            elif cmd == 'auto-bidir off':
                tlm.set_auto_bidir(False)
                print("[CTL] auto_bidir → OFF")
            elif cmd == 'show':
                print(f"[CTL] target={tlm.get_target()} | auto_bidir={tlm.get_auto_bidir()}")
    th = threading.Thread(target=_loop, daemon=True)
    th.start()
    return th

# Non-threaded console polling (Windows console friendly)
class ConsolePoller:
    def __init__(self, tlm: TargetLangManager):
        self.tlm = tlm
        self._buf = ""
        try:
            import msvcrt  # type: ignore
            self._msvcrt = msvcrt
        except Exception:
            self._msvcrt = None
    def poll(self):
        if not self._msvcrt:
            return
        while self._msvcrt.kbhit():
            ch = self._msvcrt.getwch()
            if ch in ('\r', '\n'):
                self._handle_line(self._buf.strip())
                self._buf = ""
            elif ch == '\b':
                self._buf = self._buf[:-1]
            else:
                self._buf += ch
    def _handle_line(self, line: str):
        if not line:
            return
        cmd = line.lower()
        if cmd == 'help':
            print("Commands:\n  lang <code>      set target language (e.g., lang en, lang ja, lang es)\n  list             show a few example codes\n  auto-bidir on    enable EN↔JA automatic swap\n  auto-bidir off   disable swap (fixed target)\n  show             display current target and swap mode\n  help             this help\n")
        elif cmd.startswith('lang '):
            _, code = cmd.split(' ', 1)
            code = code.strip()
            if code:
                self.tlm.set_target(code)
                print(f"[CTL] target_lang → {code}")
        elif cmd == 'list':
            print("Examples: en (English), ja (Japanese), es (Spanish), fr (French), de (German), zh (Chinese)")
        elif cmd == 'auto-bidir on':
            self.tlm.set_auto_bidir(True)
            print("[CTL] auto_bidir → ON (en↔ja)")
        elif cmd == 'auto-bidir off':
            self.tlm.set_auto_bidir(False)
            print("[CTL] auto_bidir → OFF")
        elif cmd == 'show':
            print(f"[CTL] target={self.tlm.get_target()} | auto_bidir={self.tlm.get_auto_bidir()}")


# ===================== Self tests ===================== #

def _self_test():
    tlm = TargetLangManager('ja', auto_bidir=False)
    assert tlm.resolve_target('en') == 'ja'
    tlm.set_target('es')
    assert tlm.resolve_target('en') == 'es'
    tlm.set_auto_bidir(True)
    assert tlm.resolve_target('en') == 'ja'
    assert tlm.resolve_target('ja') == 'en'
    assert tlm.resolve_target('fr') == 'es'
    print('[TEST] TargetLangManager OK')


def _self_test_vad():
    cfg = RTConfig()
    vad = EnergyVAD(cfg)
    sr = cfg.sample_rate
    # build 200ms of silence then 400ms of tone then 300ms silence
    def tone(f, dur):
        t = np.arange(int(sr * dur)) / sr
        return (0.2 * np.sin(2 * np.pi * f * t)).astype(np.float32)
    def pack(a: np.ndarray) -> bytes:
        return (np.clip(a, -1, 1) * 32767).astype(np.int16).tobytes()
    frames: List[bytes] = []
    # 200ms silence
    frames += [pack(np.zeros(int(sr * cfg.block_ms / 1000), dtype=np.float32)) for _ in range(200 // cfg.block_ms)]
    # 400ms tone
    tone_frames = tone(440, 0.4)
    step = int(sr * cfg.block_ms / 1000)
    for i in range(0, len(tone_frames), step):
        chunk = tone_frames[i:i + step]
        if len(chunk) < step:
            chunk = np.pad(chunk, (0, step - len(chunk)))
        frames.append(pack(chunk))
    # 300ms silence
    frames += [pack(np.zeros(int(sr * cfg.block_ms / 1000), dtype=np.float32)) for _ in range(300 // cfg.block_ms)]
    got = False
    for f in frames:
        out = vad.add(f, time.time())
        if out:
            seg, st = out
            assert len(seg) > 0
            got = True
    assert got, "VAD failed to emit a segment"
    print("[TEST] EnergyVAD OK")


# ===================== Main ===================== #

def main():
    ap = argparse.ArgumentParser(description="Realtime translator (mic/WAV → ASR → MT → VoiceVox → out/WS)")
    ap.add_argument("--asr-model", default="tiny")
    ap.add_argument("--asr-compute", default="int8")
    ap.add_argument("--asr-lang", default=None)
    ap.add_argument("--target-lang", default="ja")
    ap.add_argument("--auto-bidir", action="store_true")
    ap.add_argument("--show-latency", action="store_true")
    ap.add_argument("--wav", dest="wav_path", default=None, help="Path to mono 16kHz 16-bit PCM WAV")
    ap.add_argument("--mic", action="store_true", help="Force mic input (default if no --wav)")
    ap.add_argument("--play", action="store_true", help="Enable local audio playback if available")
    ap.add_argument("--ws-port", type=int, default=None, help="Start WS server on this port if websockets is installed")
    args = ap.parse_args()

    cfg = RTConfig(
        asr_model=args.asr_model,
        asr_compute=args.asr_compute,
        asr_lang=args.asr_lang,
        target_lang=args.target_lang,
        auto_bidir=args.auto_bidir,
        show_latency=args.show_latency,
        wav_path=args.wav_path,
        play_audio=bool(args.play),
        ws_port=args.ws_port,
    )

    lat = Latency()
    tlm = TargetLangManager(cfg.target_lang, cfg.auto_bidir)
    asr = make_asr(cfg)
    mt = FastMT(cfg)
    tts = VoiceVoxTTS(cfg)
    player = SDPlayer(cfg) if (_SD_OK and cfg.play_audio) else NullPlayer()
    ws = WSServer(cfg.ws_port) if (_WS_OK and cfg.ws_port) else DummyWS()

    # Start console controls (threaded), but fall back to polling if threads are limited
    console_thread = None
    try:
        console_thread = start_console_controls(tlm)
    except RuntimeError as e:
        print(f"[CTL] Console thread unavailable: {e}. Falling back to non-threaded console polling.")
        console_thread = None

    player.start()
    ws.start()

    print("🎤 LIVE translator ready. Type 'help' in console for commands.")

    # Input source
    frame_len = int(cfg.sample_rate * cfg.block_ms / 1000)
    if cfg.wav_path:
        source = stream_from_wav(cfg, frame_len)
    else:
        if not _SD_OK and not cfg.wav_path:
            print("[WARN] sounddevice unavailable and no --wav provided → exiting")
            return
        source = stream_from_mic(cfg, frame_len)

    # Build pipeline ONCE (avoid per-segment object creation)
    pipeline = Pipeline(cfg, tlm, asr, mt, tts, player, ws, lat)
    vad = EnergyVAD(cfg)

    # Optional non-threaded console polling (Windows-only)
    poller = ConsolePoller(tlm)

    try:
        for frame, ts in source:
            # Poll for console commands without threads
            poller.poll()

            out = vad.add(frame, ts)
            if out:
                seg, start_ts = out
                pipeline.process_segment(seg, start_ts)
    except KeyboardInterrupt:
        print("\n[STOP] interrupted by user")
    finally:
        player.stop()
        ws.stop()
        print(lat.report())


if __name__ == "__main__":
    try:
        _self_test()
        _self_test_vad()
    except AssertionError as e:
        print(f"[TEST] failed: {e}")
    main()
