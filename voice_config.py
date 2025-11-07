"""
voice_config.py

Comprehensive voice configuration for edge-tts with male and female voices
for multiple languages with appropriate accents.

This module provides:
- Predefined male and female voices for common languages
- Voice selection helpers
- Language-specific accent support
"""

# Comprehensive voice mappings for edge-tts
# Format: language_code: {"male": [voice_names], "female": [voice_names]}
VOICE_LIBRARY = {
    "en-US": {
        "male": ["en-US-GuyNeural", "en-US-EricNeural", "en-US-BrianNeural"],
        "female": ["en-US-AriaNeural", "en-US-JennyNeural", "en-US-MichelleNeural"]
    },
    "en-GB": {
        "male": ["en-GB-RyanNeural", "en-GB-ThomasNeural"],
        "female": ["en-GB-SoniaNeural", "en-GB-LibbyNeural"]
    },
    "en-AU": {
        "male": ["en-AU-WilliamNeural", "en-AU-TimNeural"],
        "female": ["en-AU-NatashaNeural", "en-AU-AnnetteNeural"]
    },
    "en-CA": {
        "male": ["en-CA-LiamNeural"],
        "female": ["en-CA-ClaraNeural"]
    },
    "en-IN": {
        "male": ["en-IN-PrabhatNeural"],
        "female": ["en-IN-NeerjaNeural"]
    },
    "es-ES": {
        "male": ["es-ES-AlvaroNeural"],
        "female": ["es-ES-ElviraNeural", "es-ES-AbrilNeural"]
    },
    "es-MX": {
        "male": ["es-MX-JorgeNeural", "es-MX-LibertoNeural"],
        "female": ["es-MX-DaliaNeural", "es-MX-BeatrizNeural"]
    },
    "es-AR": {
        "male": ["es-AR-TomasNeural"],
        "female": ["es-AR-ElenaNeural"]
    },
    "fr-FR": {
        "male": ["fr-FR-HenriNeural", "fr-FR-AlainNeural"],
        "female": ["fr-FR-DeniseNeural", "fr-FR-BrigitteNeural"]
    },
    "fr-CA": {
        "male": ["fr-CA-AntoineNeural", "fr-CA-JeanNeural"],
        "female": ["fr-CA-SylvieNeural"]
    },
    "de-DE": {
        "male": ["de-DE-ConradNeural", "de-DE-KlausNeural"],
        "female": ["de-DE-KatjaNeural", "de-DE-AmalaNeural"]
    },
    "de-AT": {
        "male": ["de-AT-JonasNeural"],
        "female": ["de-AT-IngridNeural"]
    },
    "it-IT": {
        "male": ["it-IT-DiegoNeural", "it-IT-BenignoNeural"],
        "female": ["it-IT-ElsaNeural", "it-IT-IsabellaNeural"]
    },
    "pt-BR": {
        "male": ["pt-BR-AntonioNeural", "pt-BR-FabioNeural"],
        "female": ["pt-BR-FranciscaNeural", "pt-BR-BrendaNeural"]
    },
    "pt-PT": {
        "male": ["pt-PT-DuarteNeural"],
        "female": ["pt-PT-RaquelNeural"]
    },
    "ru-RU": {
        "male": ["ru-RU-DmitryNeural"],
        "female": ["ru-RU-SvetlanaNeural", "ru-RU-DariyaNeural"]
    },
    "ja-JP": {
        "male": ["ja-JP-KeitaNeural", "ja-JP-DaichiNeural"],
        "female": ["ja-JP-NanamiNeural", "ja-JP-AoiNeural"]
    },
    "ko-KR": {
        "male": ["ko-KR-InJoonNeural", "ko-KR-GookMinNeural"],
        "female": ["ko-KR-SunHiNeural", "ko-KR-JiMinNeural"]
    },
    "zh-CN": {
        "male": ["zh-CN-YunxiNeural", "zh-CN-YunjianNeural"],
        "female": ["zh-CN-XiaoxiaoNeural", "zh-CN-XiaoyiNeural"]
    },
    "zh-TW": {
        "male": ["zh-TW-YunJheNeural"],
        "female": ["zh-TW-HsiaoChenNeural", "zh-TW-HsiaoYuNeural"]
    },
    "ar-SA": {
        "male": ["ar-SA-HamedNeural"],
        "female": ["ar-SA-ZariyahNeural"]
    },
    "ar-EG": {
        "male": ["ar-EG-ShakirNeural"],
        "female": ["ar-EG-SalmaNeural"]
    },
    "hi-IN": {
        "male": ["hi-IN-MadhurNeural"],
        "female": ["hi-IN-SwaraNeural"]
    },
    "nl-NL": {
        "male": ["nl-NL-MaartenNeural"],
        "female": ["nl-NL-ColetteNeural", "nl-NL-FennaNeural"]
    },
    "pl-PL": {
        "male": ["pl-PL-MarekNeural"],
        "female": ["pl-PL-ZofiaNeural", "pl-PL-AgnieszkaNeural"]
    },
    "tr-TR": {
        "male": ["tr-TR-AhmetNeural"],
        "female": ["tr-TR-EmelNeural"]
    },
    "sv-SE": {
        "male": ["sv-SE-MattiasNeural"],
        "female": ["sv-SE-SofieNeural", "sv-SE-HilleviNeural"]
    },
    "no-NO": {
        "male": ["no-NO-FinnNeural"],
        "female": ["no-NO-PernilleNeural", "no-NO-IselinNeural"]
    },
    "da-DK": {
        "male": ["da-DK-JeppeNeural"],
        "female": ["da-DK-ChristelNeural"]
    },
    "fi-FI": {
        "male": ["fi-FI-HarriNeural"],
        "female": ["fi-FI-NooraNeural", "fi-FI-SelmaNeural"]
    },
    "th-TH": {
        "male": ["th-TH-NiwatNeural"],
        "female": ["th-TH-PremwadeeNeural", "th-TH-AcharaNeural"]
    },
    "vi-VN": {
        "male": ["vi-VN-NamMinhNeural"],
        "female": ["vi-VN-HoaiMyNeural"]
    },
    "uk-UA": {
        "male": ["uk-UA-OstapNeural"],
        "female": ["uk-UA-PolinaNeural"]
    },
    "cs-CZ": {
        "male": ["cs-CZ-AntoninNeural"],
        "female": ["cs-CZ-VlastaNeural"]
    },
    "el-GR": {
        "male": ["el-GR-NestorasNeural"],
        "female": ["el-GR-AthinaNeural"]
    },
    "he-IL": {
        "male": ["he-IL-AvriNeural"],
        "female": ["he-IL-HilaNeural"]
    }
}

# Language display names for UI
LANGUAGE_DISPLAY_NAMES = {
    "en-US": "English (US)",
    "en-GB": "English (UK)",
    "en-AU": "English (Australia)",
    "en-CA": "English (Canada)",
    "en-IN": "English (India)",
    "es-ES": "Spanish (Spain)",
    "es-MX": "Spanish (Mexico)",
    "es-AR": "Spanish (Argentina)",
    "fr-FR": "French (France)",
    "fr-CA": "French (Canada)",
    "de-DE": "German (Germany)",
    "de-AT": "German (Austria)",
    "it-IT": "Italian",
    "pt-BR": "Portuguese (Brazil)",
    "pt-PT": "Portuguese (Portugal)",
    "ru-RU": "Russian",
    "ja-JP": "Japanese",
    "ko-KR": "Korean",
    "zh-CN": "Chinese (Simplified)",
    "zh-TW": "Chinese (Traditional)",
    "ar-SA": "Arabic (Saudi Arabia)",
    "ar-EG": "Arabic (Egypt)",
    "hi-IN": "Hindi",
    "nl-NL": "Dutch",
    "pl-PL": "Polish",
    "tr-TR": "Turkish",
    "sv-SE": "Swedish",
    "no-NO": "Norwegian",
    "da-DK": "Danish",
    "fi-FI": "Finnish",
    "th-TH": "Thai",
    "vi-VN": "Vietnamese",
    "uk-UA": "Ukrainian",
    "cs-CZ": "Czech",
    "el-GR": "Greek",
    "he-IL": "Hebrew"
}


def get_voice(language: str, gender: str = "female", index: int = 0) -> str:
    """
    Get a voice for the specified language and gender.
    
    Args:
        language: Language code (e.g., 'en-US', 'es-MX')
        gender: 'male' or 'female'
        index: Index of the voice to use (default 0 for primary voice)
    
    Returns:
        Voice name string (e.g., 'en-US-AriaNeural')
    """
    if language not in VOICE_LIBRARY:
        # Fallback to US English
        language = "en-US"
    
    gender = gender.lower()
    if gender not in ["male", "female"]:
        gender = "female"
    
    voices = VOICE_LIBRARY[language].get(gender, [])
    if not voices:
        # Fallback to the other gender if this one is not available
        other_gender = "male" if gender == "female" else "female"
        voices = VOICE_LIBRARY[language].get(other_gender, [])
    
    if not voices:
        # Ultimate fallback
        return "en-US-AriaNeural"
    
    # Use index with wraparound
    index = index % len(voices)
    return voices[index]


def get_available_languages():
    """Get list of available language codes."""
    return sorted(VOICE_LIBRARY.keys())


def get_language_display_name(language_code: str) -> str:
    """Get the display name for a language code."""
    return LANGUAGE_DISPLAY_NAMES.get(language_code, language_code)


def get_all_voices_for_language(language: str):
    """Get all available voices (male and female) for a language."""
    if language not in VOICE_LIBRARY:
        return {"male": [], "female": []}
    return VOICE_LIBRARY[language].copy()


def build_voice_map(language_configs: list) -> dict:
    """
    Build a voice map for tts_helpers from language configurations.
    
    Args:
        language_configs: List of dicts with 'language' and 'gender' keys
                         e.g., [{"language": "en-US", "gender": "female"}, ...]
    
    Returns:
        Dict mapping language codes to voice names
    """
    voice_map = {}
    for config in language_configs:
        lang = config.get("language", "en-US")
        gender = config.get("gender", "female")
        voice = get_voice(lang, gender)
        voice_map[lang] = voice
    return voice_map
