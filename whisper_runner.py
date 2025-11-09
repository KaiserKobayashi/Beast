from __future__ import annotations
from pathlib import Path
from typing import Optional, Tuple, List

def transcribe_to_srt(audio_path: Path, model: str="base", device: str="cpu") -> Path:
    """
    Stub for wiring Whisper/faster-whisper later.
    Returns a dummy .srt next to audio_path for pipeline integration.
    """
    srt = audio_path.with_suffix(".en.srt")
    srt.write_text("1\n00:00:00,000 --> 00:00:02,000\n[Transcription placeholder]\n", encoding="utf-8")
    return srt
