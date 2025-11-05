
#!/usr/bin/env python3
"""
auto_srt_all_tts_wrapper.py

A small non-destructive wrapper to run auto_srt_all.py (or your usual transcription flow)
and then run tts_run.py on the produced SRTs so transcription -> TTS is one-step.

Usage (example):
  python auto_srt_all_tts_wrapper.py --auto-args "--video 'my.mp4' --targets en" --tts-args "--tts-voices 'en:en-US-AriaNeural' --playlist out/playlist.m3u"
"""
import argparse
import shlex
import subprocess
import sys
from pathlib import Path
import glob

def find_srt_files(outdir: Path):
    return list(map(Path, glob.glob(str(outdir / '**' / '*.srt'), recursive=True)))

def main():
    p = argparse.ArgumentParser(description="Wrapper: run auto_srt_all.py then run tts_run.py on generated SRTs.")
    p.add_argument("--auto-script", default="auto_srt_all.py", help="Path to transcription script (auto_srt_all.py)")
    p.add_argument("--auto-args", default="", help="Arguments to pass to the transcription script (quoted string)")
    p.add_argument("--outdir", default=".", help="Top-level output directory to search for generated SRTs (often same as transcription --outdir)")
    p.add_argument("--tts-args", default="", help="Arguments to pass to tts_run.py (quoted string); do NOT include --srt, wrapper will create it.")
    args = p.parse_args()

    # 1) Run transcription (as a subprocess)
    cmd_auto = [sys.executable, args.auto_script] + shlex.split(args.auto_args)
    print("Running transcription:", " ".join(shlex.quote(c) for c in cmd_auto))
    rc = subprocess.run(cmd_auto).returncode
    if rc != 0:
        print(f"Transcription script failed with exit code {rc}. Aborting TTS step.")
        sys.exit(rc)

    # 2) Find SRT files
    outdir = Path(args.outdir)
    srt_files = find_srt_files(outdir)
    if not srt_files:
        print("No SRT files found under", outdir)
        return

    # 3) Build lang:path pairs for tts_run: try to infer language from filenames (filename.en.srt)
    srt_pairs = []
    for p in srt_files:
        name = p.name
        parts = name.split('.')
        lang = None
        if len(parts) >= 3 and len(parts[-2]) <= 3:
            lang = parts[-2]
        else:
            lang = "auto"
        srt_pairs.append(f"{lang}:{str(p)}")

    # 4) Run tts_run.py
    cmd_tts = [sys.executable, "tts_run.py", "--outdir", str(outdir / "tts"), "--srt"] + srt_pairs + shlex.split(args.tts_args)
    print("Running TTS:", " ".join(shlex.quote(c) for c in cmd_tts))
    rc2 = subprocess.run(cmd_tts).returncode
    if rc2 != 0:
        print(f"TTS script failed with exit code {rc2}.")
        sys.exit(rc2)

if __name__ == "__main__":
    main()

