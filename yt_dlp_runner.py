from __future__ import annotations
import subprocess
from pathlib import Path
from typing import Iterable, Optional
from .io_paths import ensure_dir, safe_filename, which_tool

def stream_proc(cmd: list[str]) -> Iterable[str]:
    with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1) as p:
        for line in p.stdout or []:
            yield line.rstrip("\r\n")
        rc = p.wait()
        if rc != 0:
            raise RuntimeError(f"Process failed ({rc}): {' '.join(cmd[:3])} ...")

def derive_template(out_dir: Path) -> str:
    return str(out_dir / "%(title)s.%(ext)s")

def download_if_url(url_or_file: str, out_dir: Path,
                    yt_dlp_path: Optional[str] = None,
                    user_agent: Optional[str] = "Mozilla/5.0",
                    no_playlist: bool = True,
                    cookies_from_browser: Optional[str] = None,
                    extractor_args: Optional[str] = None):
    is_url = url_or_file.startswith(("http://","https://"))
    if not is_url: return None
    out_dir = ensure_dir(out_dir)
    ytdlp = which_tool(yt_dlp_path, "yt-dlp.exe")
    # probe title for final filename
    last_title: Optional[str] = None
    probe = [ytdlp, "--no-playlist", "--get-title", url_or_file]
    for line in stream_proc(probe): last_title = line
    # real download
    cmd = [ytdlp]
    if no_playlist: cmd += ["--no-playlist"]
    if user_agent: cmd += ["--user-agent", user_agent]
    if cookies_from_browser: cmd += ["--cookies-from-browser", cookies_from_browser]
    if extractor_args: cmd += ["--extractor-args", extractor_args]
    cmd += ["-o", derive_template(out_dir), "-f", "bv*+ba/best", url_or_file]
    for line in stream_proc(cmd): yield line
    if last_title:
        return (out_dir / f"{safe_filename(last_title)}.mp4")
    return None
