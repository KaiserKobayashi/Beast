from __future__ import annotations
from pathlib import Path
from typing import Optional, Sequence
from DownloadBeast.core.io_paths import normalize_input_path, ensure_dir, safe_filename
from DownloadBeast.core.yt_dlp_runner import download_if_url
from DownloadBeast.core.mux import mux_mp4_with_subs, to_mp3
from DownloadBeast.core.cleanup import cleanup_by_ext

def _consume_and_get(gen):
    it = iter(gen)
    try:
        while True: _ = next(it)
    except StopIteration as e:
        return getattr(e,"value",None)

def run_core(source: str, out_dir: str, sub_files: Sequence[str], make_mp3: bool=False) -> str:
    out = ensure_dir(Path(out_dir))
    if source.startswith(("http://","https://")):
        result_path: Optional[Path] = _consume_and_get(download_if_url(source, out))
        if not result_path or not result_path.exists():
            candidates = sorted(out.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
            if not candidates: raise FileNotFoundError("Download failed; no output found.")
            result_path = candidates[0]
        video_in = result_path
    else:
        video_in = normalize_input_path(source)
    subs = [Path(s) for s in sub_files if s and Path(s).exists()]
    mp4_out = out / f"{safe_filename(video_in.stem)} (subbed).mp4"
    for _ in mux_mp4_with_subs(video_in, subs, mp4_out): pass
    if make_mp3:
        mp3_out = out / f"{safe_filename(video_in.stem)}.mp3"
        for _ in to_mp3(video_in, mp3_out): pass
    cleanup_by_ext(out, [".vtt",".tmp",".json"])
    return str(mp4_out)
