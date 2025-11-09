# Simple VoiceVox Engine client for synthesis + playback with a Windows fallback
# Place this file at src/DownloadBeast/voicevox_client.py

import requests
import tempfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
import platform

# Playback backends: try simpleaudio if installed, otherwise use winsound on Windows
try:
    import simpleaudio as sa  # optional, may require build tools
    _HAVE_SIMPLEAUDIO = True
except Exception:
    sa = None
    _HAVE_SIMPLEAUDIO = False

if platform.system() == "Windows":
    try:
        import winsound
        _HAVE_WINSOUND = True
    except Exception:
        _HAVE_WINSOUND = False
else:
    _HAVE_WINSOUND = False

ENGINE_URL_DEFAULT = "http://127.0.0.1:50021"
_POOL = ThreadPoolExecutor(max_workers=2)


def synthesize_wav_bytes(text: str, speaker: int = 1, engine_url: str = ENGINE_URL_DEFAULT, timeout: int = 30) -> bytes:
    audio_query_url = f"{engine_url}/audio_query"
    synthesis_url = f"{engine_url}/synthesis"

    r = requests.post(audio_query_url, params={"text": text, "speaker": speaker}, timeout=timeout)
    r.raise_for_status()
    audio_query = r.json()

    r2 = requests.post(synthesis_url, params={"speaker": speaker}, json=audio_query, timeout=timeout)
    r2.raise_for_status()
    return r2.content


def _write_temp_wav(wav_bytes: bytes) -> Path:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp_path = Path(tmp.name)
    tmp.write(wav_bytes)
    tmp.flush()
    tmp.close()
    return tmp_path


def _play_wav_file(path: Path, wait: bool = True):
    # Prefer simpleaudio if available (non-blocking playback control). Otherwise use winsound on Windows.
    if _HAVE_SIMPLEAUDIO:
        wave = sa.WaveObject.from_wave_file(str(path))
        play_obj = wave.play()
        if wait:
            play_obj.wait_done()
        return
    if _HAVE_WINSOUND:
        # winsound.PlaySound blocks until sound finishes by default
        flags = winsound.SND_FILENAME
        if not wait:
            flags |= winsound.SND_ASYNC
        winsound.PlaySound(str(path), flags)
        return
    # Last resort: try the OS default player (spawn) — cross-platform but may not be installed
    import subprocess
    try:
        if platform.system() == "Darwin":
            subprocess.Popen(["afplay", str(path)])
        elif platform.system() == "Linux":
            subprocess.Popen(["aplay", str(path)])
        elif platform.system() == "Windows":
            # Use start to open associated player (non-blocking)
            subprocess.Popen(["cmd", "/c", "start", "", str(path)])
        else:
            subprocess.Popen(["python", "-m", "webbrowser", str(path)])
    except Exception as e:
        raise RuntimeError(f"No available audio backend to play WAV file: {e}")


def synthesize_and_play(text: str, speaker: int = 1, engine_url: str = ENGINE_URL_DEFAULT, wait: bool = True) -> Path:
    wav = synthesize_wav_bytes(text, speaker=speaker, engine_url=engine_url)
    tmp_path = _write_temp_wav(wav)
    _play_wav_file(tmp_path, wait=wait)
    return tmp_path


def synthesize_and_play_async(text: str, speaker: int = 1, engine_url: str = ENGINE_URL_DEFAULT, wait: bool = False):
    return _POOL.submit(synthesize_and_play, text, speaker, engine_url, wait)
