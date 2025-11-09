from __future__ import annotations
import json, hashlib
from pathlib import Path

class KVCache:
    def __init__(self, folder: Path):
        self.folder = Path(folder); self.folder.mkdir(parents=True, exist_ok=True)
    def _key(self, text: str, meta: str="") -> Path:
        h = hashlib.sha256((text+"|"+meta).encode("utf-8")).hexdigest()
        return self.folder / (h + ".json")
    def get(self, text: str, meta: str=""):
        p = self._key(text, meta)
        if p.exists():
            try: return json.loads(p.read_text(encoding="utf-8"))
            except Exception: return None
        return None
    def set(self, text: str, data, meta: str=""):
        p = self._key(text, meta)
        p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return p
