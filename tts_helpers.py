
"""
tts_helpers.py

TTS helper wrapping edge-tts (async) with:
- deterministic caching by text hash
- per-segment and stitched synthesis
- simple concatenation using pydub (requires ffmpeg on PATH)
"""
import asyncio
import hashlib
from pathlib import Path
from typing import Dict, List, Optional

try:
    import edge_tts
except Exception:
    edge_tts = None

try:
    from pydub import AudioSegment
except Exception:
    AudioSegment = None

def _text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]

async def _synthesize_edge(text: str, out_path: Path, voice: str = "en-US-AriaNeural", rate: str = "+0%"):
    if edge_tts is None:
        raise RuntimeError("edge-tts not installed. pip install edge-tts")
    
    try:
        communicate = edge_tts.Communicate(text, voice=voice, rate=rate)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("wb") as f:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
    except Exception as e:
        error_msg_lower = str(e).lower()
        
        # Check for DNS-related errors
        if any(keyword in error_msg_lower for keyword in ["dns", "getaddrinfo", "no address"]):
            raise RuntimeError(
                "Network error: Cannot reach Microsoft Edge TTS service.\n"
                "DNS resolution failed - the service may be blocked by firewall.\n\n"
                "Solutions:\n"
                "  1. Check your internet connection\n"
                "  2. Verify firewall allows access to api.msedgeservices.com\n"
                "  3. Run: python network_utils.py (for detailed diagnosis)\n"
                "  4. See: FIREWALL_TROUBLESHOOTING.md for help\n\n"
                f"Original error: {e}"
            ) from e
        # Check for connection-related errors
        elif any(keyword in error_msg_lower for keyword in ["connection", "timeout", "refused"]):
            raise RuntimeError(
                "Network error: Cannot connect to Microsoft Edge TTS service.\n"
                "Connection timeout or refused - the service may be blocked by firewall.\n\n"
                "Solutions:\n"
                "  1. Check if you're behind a corporate firewall\n"
                "  2. Verify proxy settings are configured\n"
                "  3. Run: python network_utils.py (for detailed diagnosis)\n"
                "  4. See: FIREWALL_TROUBLESHOOTING.md for help\n\n"
                f"Original error: {e}"
            ) from e
        else:
            raise RuntimeError(
                f"Edge TTS error: {e}\n\n"
                "For network troubleshooting, run: python network_utils.py\n"
                "For detailed help, see: FIREWALL_TROUBLESHOOTING.md"
            ) from e

def synthesize_text(text: str, out_path: Path, engine: str = "edge", voice: str = "en-US-AriaNeural", rate: str = "+0%"):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if engine.lower() == "edge":
        if edge_tts is None:
            raise RuntimeError("edge-tts is not installed. Install with: pip install edge-tts")
        asyncio.run(_synthesize_edge(text, out_path, voice=voice, rate=rate))
    else:
        raise NotImplementedError(f"TTS engine '{engine}' is not implemented in this helper.")

def get_cached_tts_path(text: str, outdir: Path, prefix: str = "tts", ext: str = ".mp3") -> Path:
    h = _text_hash(text)
    safe = f"{prefix}_{h}{ext}"
    return Path(outdir) / safe

def stitch_audio(inputs: List[Path], out_path: Path, gap_ms: int = 250):
    if AudioSegment is None:
        raise RuntimeError("pydub not installed. Install with: pip install pydub")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    combined = None
    silence = AudioSegment.silent(duration=gap_ms)
    for p in inputs:
        seg = AudioSegment.from_file(p)
        if combined is None:
            combined = seg
        else:
            combined += silence
            combined += seg
    if combined is None:
        raise RuntimeError("No inputs provided to stitch_audio")
    fmt = out_path.suffix.replace(".", "") or "mp3"
    combined.export(out_path, format=fmt)

def synthesize_per_segments(segments: List[Dict], outdir: Path, engine: str = "edge", voice_map: Optional[Dict[str,str]] = None, cache: bool = True) -> Dict[int, Path]:
    results: Dict[int, Path] = {}
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    for seg in segments:
        idx = int(seg["idx"])
        text = seg["text"]
        lang = seg.get("lang", "en")
        voice = (voice_map or {}).get(lang, None)
        cache_path = get_cached_tts_path(f"{lang}__{text}", outdir, prefix=f"seg{idx}")
        if cache and cache_path.exists():
            results[idx] = cache_path
            continue
        tmp = outdir / (f"tmp_{cache_path.name}")
        synthesize_text(text, tmp, engine=engine, voice=voice or "en-US-AriaNeural")
        tmp.replace(cache_path)
        results[idx] = cache_path
    return results

def synthesize_stitched(segments: List[Dict], out_path: Path, outdir: Path, engine: str = "edge", voice_map: Optional[Dict[str,str]] = None, cache: bool = True, gap_ms: int = 250):
    per_seg = synthesize_per_segments(segments, outdir=outdir, engine=engine, voice_map=voice_map, cache=cache)
    order = [per_seg[int(s["idx"])] for s in segments]
    stitch_audio(order, out_path, gap_ms=gap_ms)
    return out_path

