#!/usr/bin/env python3
"""
modules/ffmpeg_utils.py

Utility to mux/attach a generated audio file into a video using ffmpeg.

Provides:
  mux_audio_into_video(video_path, audio_path, out_path=None,
                      keep_original_audio=False, audio_codec="aac",
                      bitrate="192k", audio_lang_tag="eng")

Behavior:
 - If keep_original_audio is True and the input video already has audio,
   adds the new audio as an additional audio stream (keeps original).
 - Otherwise replaces/sets the audio to the provided audio file.
 - Sets language metadata on the added audio stream.
 - Raises RuntimeError with ffmpeg stderr on failure.
"""
from __future__ import annotations
import shutil
import subprocess
from pathlib import Path
from typing import Optional
import tempfile
import sys
import os

def _which_or_raise(name: str) -> str:
    exe = shutil.which(name)
    if not exe:
        raise RuntimeError(f"{name} not found in PATH; please install it and ensure it is on PATH")
    return exe

def _ffprobe_has_audio(video_path: Path) -> bool:
    """
    Return True if video_path has at least one audio stream, else False.
    Requires ffprobe on PATH.
    """
    ffprobe = _which_or_raise("ffprobe")
    cmd = [
        ffprobe,
        "-v", "error",
        "-select_streams", "a",
        "-show_entries", "stream=index",
        "-of", "csv=p=0",
        str(video_path)
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        # If ffprobe fails for some reason, surface the error
        raise RuntimeError(f"ffprobe failed (code {proc.returncode}):\n{proc.stderr.strip()}")
    return bool(proc.stdout.strip())

def mux_audio_into_video(video_path: str,
                         audio_path: str,
                         out_path: Optional[str] = None,
                         keep_original_audio: bool = False,
                         audio_codec: str = "aac",
                         bitrate: str = "192k",
                         audio_lang_tag: str = "eng") -> str:
    """
    Mux audio_path into video_path producing out_path (or a temp file).
    Returns the path to the output file.

    Raises RuntimeError on failure.
    """
    video_path = Path(video_path)
    audio_path = Path(audio_path)

    if not video_path.exists():
        raise FileNotFoundError(f"video_path not found: {video_path}")
    if not audio_path.exists():
        raise FileNotFoundError(f"audio_path not found: {audio_path}")

    ffmpeg = _which_or_raise("ffmpeg")
    # Check whether video already contains audio
    has_audio = _ffprobe_has_audio(video_path)

    # Choose output path
    if out_path:
        out_path = Path(out_path)
    else:
        # keep same container as input if possible
        suffix = video_path.suffix or ".mp4"
        fd, tmp = tempfile.mkstemp(prefix="mux_", suffix=suffix)
        os.close(fd)
        out_path = Path(tmp)

    # Build ffmpeg args (single invocation)
    args = [ffmpeg, "-y", "-i", str(video_path), "-i", str(audio_path)]

    # Determine mapping and codec choices
    # If keeping original audio and the input actually has audio, map both audio streams (original + new)
    if keep_original_audio and has_audio:
        # map video, original audio (0:a?), and new audio (1:a)
        args += ["-map", "0:v", "-map", "0:a?", "-map", "1:a"]
        # copy video, copy original audio stream, encode new audio stream
        # Note: audio stream numbering in metadata is among audio streams only: new audio will be audio index 1
        args += ["-c:v", "copy", "-c:a:0", "copy", "-c:a:1", audio_codec, "-b:a:1", bitrate]
        lang_index = 1  # new audio is second audio stream => audio stream index 1
    else:
        # replace original audio (or original absent) with the new audio
        args += ["-map", "0:v", "-map", "1:a"]
        args += ["-c:v", "copy", "-c:a", audio_codec, "-b:a", bitrate]
        lang_index = 0  # new audio is the only audio stream => index 0

    # set language metadata for the added audio stream (audio stream index among audio streams)
    if audio_lang_tag:
        args += [f"-metadata:s:a:{lang_index}", f"language={audio_lang_tag}"]

    args += [str(out_path)]

    # For easier debugging, print the command in a shell-safe way
    def _sh_quote(s: str) -> str:
        # simple quoting for display only
        if sys.platform.startswith("win"):
            return f'"{s}"'
        import shlex
        return shlex.quote(s)

    print("[ffmpeg] running:", " ".join(_sh_quote(x) for x in args))

    proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        # Clean up partially written out file if ffmpeg failed
        try:
            if out_path.exists():
                out_path.unlink()
        except Exception:
            pass
        raise RuntimeError(f"ffmpeg failed (code {proc.returncode}):\n{proc.stderr.strip()}")

    return str(out_path)
