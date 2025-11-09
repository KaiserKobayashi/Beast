from __future__ import annotations
import os, re, shutil
from pathlib import Path
from typing import Optional

_ILLEGAL = r'<>:"/\\|?*'

def normalize_input_path(p: str) -> Path:
    p = p.strip().strip('"').strip("'")
    p = os.path.expandvars(os.path.expanduser(p))
    path = Path(p).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Input not found: {path}")
    return path

def ensure_dir(path: Path) -> Path:
    path = Path(path).expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path

def safe_filename(name: str, max_len: int = 180) -> str:
    s = "".join(ch for ch in name if ch not in _ILLEGAL)
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) > max_len: s = s[:max_len].rstrip()
    return s

def which_tool(preferred_path: Optional[str], fallback_name: str, bundled_dir: Optional[Path]=None) -> str:
    if preferred_path:
        pp = Path(preferred_path)
        if pp.exists(): return str(pp)
    if bundled_dir:
        cand = bundled_dir / fallback_name
        if cand.exists(): return str(cand)
    found = shutil.which(fallback_name)
    if not found:
        raise FileNotFoundError(f"Required tool not found: {fallback_name}")
    return found
