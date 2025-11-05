#!/usr/bin/env python3
"""
auto_srt_all_tts_wrapper.py - small argparse wrapper that delegates to the existing
implementation (repo-root auto_srt_all_tts_wrapper.py if present) or to modules/auto_srt_all_tts_wrapper.py.

This wrapper makes the CLI deterministic for the GUI:
  --input <path>   (file or folder)
  --output <path>  (optional)
  --no-cache       (flag)
  --rate <float>
  --voice <name>
  --format <mp3|wav>
  --workers <n>
  --dry-run
"""
import argparse
import os
import sys
import subprocess

def find_impl():
    candidates = [
        os.path.join(os.getcwd(), "auto_srt_all_tts_wrapper.py"),
        os.path.join(os.getcwd(), "Modules", "auto_srt_all_tts_wrapper.py"),
        os.path.join(os.getcwd(), "modules", "auto_srt_all_tts_wrapper.py"),
    ]
    this_file = os.path.abspath(__file__)
    for c in candidates:
        try:
            if os.path.abspath(c) == this_file:
                continue
        except Exception:
            pass
        if os.path.exists(c):
            return c
    return None

def build_cmd(args):
    impl = find_impl()
    if impl is None:
        print("No implementation found in repo (expected auto_srt_all_tts_wrapper.py in repo root or Modules/).")
        print("If you intended to run a different module, supply --dry-run to verify CLI construction.")
        return None
    cmd = [sys.executable, impl, "--input", args.input]
    if args.output:
        cmd += ["--output", args.output]
    if args.no_cache:
        cmd += ["--no-cache"]
    if args.rate is not None:
        cmd += ["--rate", str(args.rate)]
    if args.voice:
        cmd += ["--voice", args.voice]
    if args.format:
        cmd += ["--format", args.format]
    if args.workers is not None:
        cmd += ["--workers", str(args.workers)]
    return cmd

def main():
    parser = argparse.ArgumentParser(prog="auto_srt_all_tts_wrapper", description="Wrapper CLI for auto-SRT + TTS.")
    parser.add_argument("--input", required=True, help="Input video file or folder or SRT file")
    parser.add_argument("--output", help="Optional output folder")
    parser.add_argument("--no-cache", action="store_true", dest="no_cache", help="Disable cache")
    parser.add_argument("--rate", type=float, help="Playback / TTS rate")
    parser.add_argument("--voice", help="Voice name")
    parser.add_argument("--format", choices=["mp3", "wav"], help="Output audio format")
    parser.add_argument("--workers", type=int, help="Parallel worker count")
    parser.add_argument("--dry-run", action="store_true", help="Print command and exit")
    args = parser.parse_args()

    cmd = build_cmd(args)
    if args.dry_run:
        print("DRY RUN:", cmd)
        sys.exit(0 if cmd else 2)
    if not cmd:
        sys.exit(2)

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1)
    try:
        for line in iter(proc.stdout.readline, b''):
            if not line:
                break
            sys.stdout.write(line.decode(errors='replace'))
            sys.stdout.flush()
    except KeyboardInterrupt:
        proc.terminate()
        proc.wait()
        raise
    finally:
        proc.stdout.close()
    rc = proc.wait()
    sys.exit(rc)

if __name__ == "__main__":
    main()
