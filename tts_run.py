#!/usr/bin/env python3
"""
tts_run.py

Read one or more SRT files, synthesize TTS per-segment (or stitched per-language),
and produce multilingual playlists (m3u and HTML).

Usage examples:
  # per-segment TTS for English and French SRTs (lang:path)
  python tts_run.py --srt en:out.en.srt fr:out.fr.srt --outdir out/tts --tts-engine edge --tts-voices "en:en-US-AriaNeural,fr:fr-FR-DeniseNeural" --playlist out/playlist.m3u --playlist-html out/playlist.html

  # stitch per-language into stitched_{lang}.mp3
  python tts_run.py --srt en:out.en.srt fr:out.fr.srt --outdir out/tts --tts-stitch-template "out/stitched_{lang}.mp3"

Notes:
 - Requires tts_helpers.py and playlist_helpers.py in the same folder (repo root).
 - Requires edge-tts and pydub for the provided edge+pydub implementation.
"""
import argparse
import os
import re
from pathlib import Path
from typing import Dict, List

# Local helpers (repo root)
import tts_helpers
import playlist_helpers


TIMECODE_RE = re.compile(r'(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})')

def parse_srt(path: Path) -> Dict[int, Dict]:
    """
    Parse an SRT file into a mapping: idx -> {"start": float, "end": float, "text": str}
    """
    out = {}
    text_buf = []
    idx = None
    start = end = None
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        lines = [l.rstrip("\n\r") for l in fh]
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        # Expect index
        if line.isdigit():
            try:
                idx = int(line)
            except Exception:
                idx = None
            i += 1
            if i < len(lines) and TIMECODE_RE.search(lines[i]):
                m = TIMECODE_RE.search(lines[i])
                def to_seconds(h, m_, s, ms):
                    return int(h)*3600 + int(m_)*60 + int(s) + int(ms)/1000.0
                start = to_seconds(m.group(1), m.group(2), m.group(3), m.group(4))
                end = to_seconds(m.group(5), m.group(6), m.group(7), m.group(8))
                i += 1
                # collect text until blank
                text_buf = []
                while i < len(lines) and lines[i].strip() != "":
                    text_buf.append(lines[i])
                    i += 1
                text = "\n".join(text_buf).strip()
                if idx is not None:
                    out[idx] = {"start": start, "end": end, "text": text}
                # skip blank line (loop will advance)
            else:
                # Not a normal SRT segment; skip until next blank
                i += 1
        else:
            i += 1
    return out

def parse_lang_srt_entries(srt_args: List[str]) -> Dict[str, Path]:
    """
    Parse args like ["en:out.en.srt", "fr:out.fr.srt"] into {lang: Path}
    """
    m = {}
    for entry in srt_args:
        if ":" in entry:
            lang, p = entry.split(":", 1)
            m[lang.strip()] = Path(p.strip())
        else:
            # if user didn't give lang, try to infer from filename (e.g., name.en.srt)
            p = Path(entry)
            name = p.name
            parts = name.split(".")
            lang = None
            if len(parts) >= 3 and len(parts[-2]) <= 3:
                lang = parts[-2]
            else:
                lang = "auto"
            m[lang] = p
    return m

def build_segments_map(lang_srt_map: Dict[str, Path]) -> List[Dict]:
    """
    Build a unified list of segments (ordered by idx) containing texts per-language.
    Returns a list of dicts:
      {"idx": idx, "start": start, "end": end, "texts": {lang: text}, "lang": source_lang}
    source_lang will be the first language in lang_srt_map iteration order.
    """
    per_lang_parsed = {}
    for lang, path in lang_srt_map.items():
        if not path.exists():
            raise FileNotFoundError(f"SRT not found: {path}")
        per_lang_parsed[lang] = parse_srt(path)

    # union of indices
    idxs = set()
    for d in per_lang_parsed.values():
        idxs.update(d.keys())
    idxs = sorted(idxs)

    # choose source_lang as first key
    source_lang = next(iter(lang_srt_map.keys()))
    segments = []
    for idx in idxs:
        texts = {}
        start = None
        end = None
        for lang, mapping in per_lang_parsed.items():
            seg = mapping.get(idx)
            if seg:
                texts[lang] = seg["text"]
                if start is None:
                    start = seg["start"]
                if end is None:
                    end = seg["end"]
        # if no text at all, skip
        if not texts:
            continue
        segments.append({"idx": idx, "start": start or 0.0, "end": end or 0.0, "texts": texts, "lang": source_lang})
    return segments

def parse_voice_map(voices_str: str) -> Dict[str, str]:
    m = {}
    if not voices_str:
        return m
    for entry in voices_str.split(","):
        if ":" in entry:
            lang, voice = entry.split(":", 1)
            m[lang.strip()] = voice.strip()
    return m

def main():
    p = argparse.ArgumentParser(description="Synthesize TTS from SRTs and create multilingual playlists.")
    p.add_argument("--srt", nargs="+", required=True, help="SRT inputs as lang:path (e.g. en:out.en.srt fr:out.fr.srt). If lang omitted, will try to infer.")
    p.add_argument("--outdir", default="out/tts", help="Directory to write TTS files and playlists")
    p.add_argument("--tts-engine", default="edge", help="TTS engine to use (edge supported)")
    p.add_argument("--tts-voices", default="", help="Comma separated lang:voice mappings; e.g. en:en-US-AriaNeural,fr:fr-FR-DeniseNeural")
    p.add_argument("--tts-cache-dir", default=None, help="Directory to cache synthesized audio (defaults to outdir/cache)")
    p.add_argument("--tts-per-segment", action="store_true", help="Create one file per segment (default behavior)")
    p.add_argument("--tts-stitch-template", default=None, help="If set, create stitched audio per language. Use {lang} in the template, e.g. out/stitched_{lang}.mp3")
    p.add_argument("--playlist", default=None, help="Write an M3U playlist")
    p.add_argument("--playlist-style", choices=["alternate","bilingual"], default="alternate", help="Playlist ordering style")
    p.add_argument("--playlist-repeats", type=int, default=1, help="Repeats per segment in playlist")
    p.add_argument("--playlist-html", default=None, help="Write an HTML playlist player")
    p.add_argument("--gap-ms", type=int, default=250, help="Gap between stitched segments (ms)")
    args = p.parse_args()

    lang_srt_map = parse_lang_srt_entries(args.srt)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    cache_dir = Path(args.tts_cache_dir) if args.tts_cache_dir else (outdir / "cache")
    cache_dir.mkdir(parents=True, exist_ok=True)
    voice_map = parse_voice_map(args.tts_voices)

    segments = build_segments_map(lang_srt_map)
    if not segments:
        print("No segments parsed from provided SRTs.")
        return

    # For each language, synthesize per-segment files
    langs = list(lang_srt_map.keys())
    tts_map: Dict[int, Dict[str, Path]] = {}

    for lang in langs:
        # build a list of segments for this language (text may be missing for some idxs)
        segs_for_lang = []
        for s in segments:
            text_for_lang = s["texts"].get(lang)
            if not text_for_lang:
                # fallback: use source_text if available
                text_for_lang = s["texts"].get(s["lang"], "")
            segs_for_lang.append({"idx": int(s["idx"]), "text": text_for_lang, "lang": lang})

        per_lang_outdir = cache_dir / lang
        per_lang_outdir.mkdir(parents=True, exist_ok=True)
        print(f"Synthesizing {len(segs_for_lang)} segments for language '{lang}' -> {per_lang_outdir}")
        per_lang_result = tts_helpers.synthesize_per_segments(segs_for_lang, outdir=per_lang_outdir, engine=args.tts_engine, voice_map=voice_map, cache=True)
        # record into tts_map
        for idx, path in per_lang_result.items():
            tts_map.setdefault(int(idx), {})[lang] = path

        # optional stitched output per-language
        if args.tts_stitch_template:
            out_template = args.tts_stitch_template
            out_path_str = out_template.format(lang=lang) if "{lang}" in out_template else out_template.replace("{lang}", lang)
            out_path = Path(out_path_str)
            per_order = [tts_map[int(s["idx"])].get(lang) for s in segments if int(s["idx"]) in tts_map and lang in tts_map[int(s["idx"])]]
            per_order = [p for p in per_order if p is not None]
            if per_order:
                print(f"Stitching {len(per_order)} files into {out_path}")
                tts_helpers.stitch_audio(per_order, out_path, gap_ms=args.gap_ms)

    # create playlists if requested
    if args.playlist:
        print(f"Creating playlist {args.playlist}")
        playlist_helpers.create_multilingual_playlist(segments, tts_map, Path(args.playlist), style=args.playlist_style, repeats=args.playlist_repeats)
    if args.playlist_html:
        print(f"Creating HTML playlist {args.playlist_html}")
        playlist_helpers.create_html_playlist(segments, tts_map, Path(args.playlist_html))

    print("Done.")
    print(f"Cached TTS files: {cache_dir}")
    if args.playlist:
        print(f"Playlist: {args.playlist}")
    if args.playlist_html:
        print(f"HTML playlist: {args.playlist_html}")

if __name__ == "__main__":
    main()