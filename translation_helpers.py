"""
translation_helpers.py

Translation helper wrapping deep-translator with:
- deterministic caching by text hash and language pair
- support for multiple translation services (Google Translate as default)
- batch translation support
- SRT file translation
"""
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Union

try:
    from deep_translator import GoogleTranslator
except Exception:
    GoogleTranslator = None


def _text_hash(text: str, source_lang: str = "auto", target_lang: str = "en") -> str:
    """Generate a deterministic hash for caching translations."""
    combined = f"{source_lang}_{target_lang}_{text}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()[:12]


def translate_text(
    text: str,
    target_lang: str = "en",
    source_lang: str = "auto",
    cache_dir: Optional[Path] = None,
    use_cache: bool = True
) -> str:
    """
    Translate a single text string from source_lang to target_lang.
    
    Args:
        text: The text to translate
        target_lang: Target language code (e.g., 'en', 'es', 'fr')
        source_lang: Source language code or 'auto' for auto-detection
        cache_dir: Directory to cache translations
        use_cache: Whether to use cached translations
    
    Returns:
        Translated text string
    """
    if GoogleTranslator is None:
        raise RuntimeError("deep-translator not installed. Install with: pip install deep-translator")
    
    if not text or not text.strip():
        return text
    
    # Check cache if enabled
    if use_cache and cache_dir:
        cache_dir = Path(cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        text_hash = _text_hash(text, source_lang, target_lang)
        cache_file = cache_dir / f"trans_{text_hash}.json"
        
        if cache_file.exists():
            try:
                with cache_file.open("r", encoding="utf-8") as f:
                    cached = json.load(f)
                    return cached.get("translation", text)
            except Exception:
                pass
    
    # Perform translation
    try:
        translator = GoogleTranslator(source=source_lang, target=target_lang)
        translated = translator.translate(text)
        
        # Cache result if enabled
        if use_cache and cache_dir:
            cache_data = {
                "original": text,
                "translation": translated,
                "source_lang": source_lang,
                "target_lang": target_lang
            }
            try:
                with cache_file.open("w", encoding="utf-8") as f:
                    json.dump(cache_data, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
        
        return translated
    except Exception as e:
        raise RuntimeError(f"Translation failed: {e}")


def translate_batch(
    texts: List[str],
    target_lang: str = "en",
    source_lang: str = "auto",
    cache_dir: Optional[Path] = None,
    use_cache: bool = True
) -> List[str]:
    """
    Translate a batch of text strings.
    
    Args:
        texts: List of texts to translate
        target_lang: Target language code
        source_lang: Source language code or 'auto'
        cache_dir: Directory to cache translations
        use_cache: Whether to use cached translations
    
    Returns:
        List of translated strings in the same order as input
    """
    results = []
    for text in texts:
        translated = translate_text(
            text,
            target_lang=target_lang,
            source_lang=source_lang,
            cache_dir=cache_dir,
            use_cache=use_cache
        )
        results.append(translated)
    return results


def translate_srt_segments(
    segments: List[Dict],
    target_lang: str = "en",
    source_lang: str = "auto",
    cache_dir: Optional[Path] = None,
    use_cache: bool = True
) -> List[Dict]:
    """
    Translate SRT segments.
    
    Args:
        segments: List of segment dicts with 'idx', 'start', 'end', 'text' keys
        target_lang: Target language code
        source_lang: Source language code or 'auto'
        cache_dir: Directory to cache translations
        use_cache: Whether to use cached translations
    
    Returns:
        List of translated segments with the same structure
    """
    translated_segments = []
    for seg in segments:
        text = seg.get("text", "")
        if text and text.strip():
            translated_text = translate_text(
                text,
                target_lang=target_lang,
                source_lang=source_lang,
                cache_dir=cache_dir,
                use_cache=use_cache
            )
        else:
            translated_text = text
        
        translated_seg = seg.copy()
        translated_seg["text"] = translated_text
        translated_segments.append(translated_seg)
    
    return translated_segments


def get_supported_languages() -> Dict[str, str]:
    """
    Get a dictionary of supported language codes and names.
    
    Returns:
        Dict mapping language codes to language names
    """
    if GoogleTranslator is None:
        return {}
    
    try:
        return GoogleTranslator().get_supported_languages(as_dict=True)
    except Exception:
        # Return a basic set of common languages as fallback
        return {
            "auto": "Automatic Detection",
            "en": "English",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "it": "Italian",
            "pt": "Portuguese",
            "ru": "Russian",
            "ja": "Japanese",
            "ko": "Korean",
            "zh-CN": "Chinese (Simplified)",
            "ar": "Arabic",
            "hi": "Hindi"
        }


def translate_srt_file(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    target_lang: str = "en",
    source_lang: str = "auto",
    cache_dir: Optional[Path] = None,
    use_cache: bool = True
) -> Path:
    """
    Translate an entire SRT file and save to a new file.
    
    Args:
        input_path: Path to input SRT file
        output_path: Path to output translated SRT file
        target_lang: Target language code
        source_lang: Source language code or 'auto'
        cache_dir: Directory to cache translations
        use_cache: Whether to use cached translations
    
    Returns:
        Path to the translated SRT file
    """
    import re
    
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Parse SRT file
    with input_path.open("r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    
    # Split into subtitle blocks
    blocks = content.strip().split("\n\n")
    translated_blocks = []
    
    timecode_re = re.compile(r'(\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3})')
    
    for block in blocks:
        if not block.strip():
            continue
        
        lines = block.split("\n")
        if len(lines) < 3:
            # Invalid block, keep as is
            translated_blocks.append(block)
            continue
        
        # First line is index, second is timecode, rest is text
        idx_line = lines[0]
        timecode_line = lines[1]
        text_lines = lines[2:]
        
        # Check if timecode line is valid
        if not timecode_re.search(timecode_line):
            # Not a valid SRT block, keep as is
            translated_blocks.append(block)
            continue
        
        # Translate the text
        text = "\n".join(text_lines)
        if text.strip():
            translated_text = translate_text(
                text,
                target_lang=target_lang,
                source_lang=source_lang,
                cache_dir=cache_dir,
                use_cache=use_cache
            )
        else:
            translated_text = text
        
        # Reconstruct block
        translated_block = f"{idx_line}\n{timecode_line}\n{translated_text}"
        translated_blocks.append(translated_block)
    
    # Write translated SRT
    with output_path.open("w", encoding="utf-8") as f:
        f.write("\n\n".join(translated_blocks))
        if translated_blocks:
            f.write("\n")
    
    return output_path
