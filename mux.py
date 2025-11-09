from __future__ import annotations
from pathlib import Path
from typing import Iterable, Sequence, Optional
from .io_paths import which_tool
from .yt_dlp_runner import stream_proc

def mux_mp4_with_subs(video_in: Path, subs: Sequence[Path], out_path: Path,
                      ffmpeg_path: Optional[str] = None, copy_video_audio: bool = True) -> Iterable[str]:
    ffmpeg = which_tool(ffmpeg_path, "ffmpeg.exe")
    cmd: list[str] = [ffmpeg, "-y", "-i", str(video_in)]
    for s in subs: cmd += ["-i", str(s)]
    maps = ["-map", "0"] + sum((["-map", str(i+1)] for i in range(len(subs))), [])
    codec = (["-c:v","copy","-c:a","copy"] if copy_video_audio else []) + ["-c:s","mov_text"]
    meta: list[str] = []
    for idx, s in enumerate(subs):
        try: lang = s.suffixes[-2][1:] if len(s.suffixes)>=2 and len(s.suffixes[-2])==3 else "und"
        except: lang = "und"
        meta += ["-metadata:s:s:"+str(idx), f"language={lang}"]
    cmd += maps + codec + meta + [str(out_path)]
    for line in stream_proc(cmd): yield line

def to_mp3(input_media: Path, out_path: Path, ffmpeg_path: Optional[str]=None,
           title: Optional[str]=None, artist: Optional[str]=None) -> Iterable[str]:
    ffmpeg = which_tool(ffmpeg_path, "ffmpeg.exe")
    cmd = [ffmpeg,"-y","-i",str(input_media),"-vn","-c:a","libmp3lame","-q:a","2"]
    if title:  cmd += ["-metadata", f"title={title}"]
    if artist: cmd += ["-metadata", f"artist={artist}"]
    cmd += [str(out_path)]
    for line in stream_proc(cmd): yield line
