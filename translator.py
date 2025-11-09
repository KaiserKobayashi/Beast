from __future__ import annotations
from typing import Optional
try:
    from deep_translator import GoogleTranslator
except Exception:
    GoogleTranslator = None

def translate_text(text: str, src: Optional[str]=None, dest: str="en") -> str:
    if GoogleTranslator is None:
        # Fallback: no-op
        return text
    return GoogleTranslator(source=src or "auto", target=dest).translate(text)
