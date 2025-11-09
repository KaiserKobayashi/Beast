from __future__ import annotations
from pathlib import Path
from typing import Iterable, Sequence

def cleanup_intermediates(files: Sequence[Path]) -> list[Path]:
    removed: list[Path] = []
    for f in files:
        try:
            if f and f.exists():
                f.unlink(missing_ok=True); removed.append(f)
        except: pass
    return removed

def cleanup_by_ext(folder: Path, exts: Iterable[str]) -> list[Path]:
    removed: list[Path] = []
    for ext in exts:
        for p in folder.glob(f"*{ext}"):
            try: p.unlink(missing_ok=True); removed.append(p)
            except: pass
    return removed
