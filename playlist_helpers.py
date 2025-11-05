
"""
playlist_helpers.py

Helpers to create M3U playlists and a simple HTML playlist player that
lets a learner see text and play each track in sequence.
"""
from pathlib import Path
from typing import List, Dict

def create_m3u_playlist(paths: List[str], out_path: Path, title: str = "playlist"):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for p in paths:
            f.write(f"{p}\n")
    return out_path

def _build_sequence_alternate(segments: List[Dict], tts_map: Dict[int, Dict[str, Path]], repeats: int = 1):
    seq = []
    for seg in segments:
        idx = int(seg["idx"])
        languages = list(tts_map.get(idx, {}).keys())
        source_lang = seg.get("lang", languages[0] if languages else None)
        target_langs = [l for l in languages if l != source_lang]
        for _ in range(repeats):
            if source_lang and source_lang in tts_map.get(idx, {}):
                seq.append(str(tts_map[idx][source_lang]))
            for tl in target_langs:
                seq.append(str(tts_map[idx][tl]))
    return seq

def _build_sequence_bilingual(segments: List[Dict], tts_map: Dict[int, Dict[str, Path]], repeats: int = 1):
    seq = []
    for seg in segments:
        idx = int(seg["idx"])
        languages = list(tts_map.get(idx, {}).keys())
        source = seg.get("lang", languages[0] if languages else None)
        target_langs = [l for l in languages if l != source]
        for _ in range(repeats):
            for tl in target_langs:
                seq.append(str(tts_map[idx][tl]))
            if source and source in tts_map.get(idx, {}):
                seq.append(str(tts_map[idx][source]))
    return seq

def create_multilingual_playlist(segments: List[Dict], tts_map: Dict[int, Dict[str, Path]], out_path: Path, style: str = "alternate", repeats: int = 1, title: str = "multilingual_playlist"):
    if style == "alternate":
        seq = _build_sequence_alternate(segments, tts_map, repeats=repeats)
    elif style == "bilingual":
        seq = _build_sequence_bilingual(segments, tts_map, repeats=repeats)
    else:
        raise ValueError("Unsupported style")
    return create_m3u_playlist(seq, out_path, title=title)

def create_html_playlist(segments: List[Dict], tts_map: Dict[int, Dict[str, Path]], out_path: Path, title: str = "playlist"):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for seg in segments:
        idx = int(seg["idx"])
        text = seg.get("text", "").replace('"', '&quot;')
        langs = tts_map.get(idx, {})
        btns = []
        for lang, path in langs.items():
            btns.append(f'<button onclick="document.getElementById(\\\"audio_{idx}_{lang}\\\").play()">{lang}</button><audio id="audio_{idx}_{lang}" src="{str(path)}"></audio>')
        rows.append(f"<div><strong>#{idx}</strong> {text}<br>{' '.join(btns)}</div><hr>")
    html = f"""<!doctype html>
<html>
<head><meta charset="utf-8"><title>{title}</title></head>
<body>
<h1>{title}</h1>
{"".join(rows)}
</body>
</html>"""
    out_path.write_text(html, encoding="utf-8")
    return out_path

