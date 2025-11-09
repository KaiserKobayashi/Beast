# -*- coding: utf-8 -*-
"""
auto_subs.py  — helper funcs for DownloadBeast

Provides:
- load_srt(), write_srt_from_tuples()
- translate_srt(in_path, target_lang, out_path, sleep_ms=120)

Modes:
- Standard languages (en, ja, fr, ru, es, …): GoogleTranslator
- 'cockney' : Cockney rhyming slang dictionary substitution
- 'kansai' / 'kansai-ben' : rule-based rewrite from Standard JP to Kansai-ben
- 'ainu' : experimental glossary swap (respectful, non-literal)
"""

from __future__ import annotations
import time, re
from pathlib import Path
from typing import List, Tuple

# --- Optional deps for standard languages
try:
    from deep_translator import GoogleTranslator
except Exception:
    GoogleTranslator = None


# -------------------------------
# SRT helpers
# -------------------------------
def load_srt(path: Path) -> List[Tuple[str, str, str, str]]:
    """
    Minimal SRT reader -> list of (num, start_str, end_str, text)
    Keeps times as strings to avoid drift.
    """
    if not path.exists():
        return []
    content = path.read_text(encoding="utf-8", errors="replace")
    blocks = [b for b in content.split("\n\n") if b.strip()]
    out = []
    for b in blocks:
        lines = b.splitlines()
        if len(lines) >= 3:
            num = lines[0].strip()
            times = lines[1].strip()
            text = "\n".join(lines[2:]).strip()
            if " --> " in times:
                start, end = times.split(" --> ", 1)
                out.append((num, start, end, text))
    return out


def write_srt_from_tuples(items: List[Tuple[str, str, str, str]], out_path: Path) -> None:
    lines = []
    for (num, start, end, text) in items:
        lines.append(str(num))
        lines.append(f"{start} --> {end}")
        lines.append(text.strip())
        lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")


# -------------------------------
# Cockney rhyming slang (expanded)
# -------------------------------
COCKNEY_MAP = {
    # Keep this list compact per line; it is already large.
    "look": "have a butcher’s (butcher’s hook)",
    "head": "loaf of bread",
    "face": "boat race",
    "eyes": "mince pies",
    "mouth": "north and south",
    "teeth": "Hampstead Heath",
    "ears": "lug holes",
    "nose": "sherbet dab",
    "hair": "Barnet Fair",
    "hands": "Duke of Yorks",
    "feet": "plates of meat",
    "legs": "bacon and eggs",
    "trousers": "Hampton Wick",
    "shirt": "dicky dirt",
    "coat": "goat",
    "hat": "tit for tat",
    "watch": "kettle and hob",
    "jacket": "scarlet jacket",
    "tie": "kipper tie",
    "boots": "daisy roots",
    "socks": "oxfords",
    "shoes": "blues",
    "umbrella": "round the houses",
    "bed": "Uncle Ned",
    "sleep": "Bo Peep",
    "dream": "cream",
    "beer": "pig’s ear",
    "drink": "Britney Spears",
    "wine": "Rosie Lee",  # playful
    "tea": "Rosie Lee",
    "coffee": "frothy",
    "food": "Scooby Doo",
    "pub": "rub-a-dub",
    "bar": "spar",
    "money": "bees and honey",
    "cash": "sausage and mash",
    "pound": "nicker",
    "fiver": "Lady Godiva",
    "tenner": "cockle and hen",
    "wallet": "Harry Wallit",
    "shop": "lemon drop",
    "market": "Barney Market",
    "car": "jam jar",
    "road": "frog and toad",
    "street": "candy beet",
    "house": "drum",
    "flat": "cat",
    "home": "ice cream cone",
    "door": "apple core",
    "window": "Jimbo",
    "stairs": "apples and pears",
    "lift": "rift",
    "floor": "trap door",
    "phone": "dog and bone",
    "mobile": "blow-up dial",
    "television": "custard and jelly",
    "computer": "scooter",
    "internet": "roulette",
    "email": "female",
    "book": "Captain Cook",
    "paper": "Joe Draper",
    "pen": "hen",
    "ink": "kitchen sink",
    "work": "nose bag",
    "job": "Bob",
    "office": "coffin",
    "boss": "floss",
    "friend": "china plate",
    "mate": "china",
    "wife": "trouble and strife",
    "husband": "duster",
    "mum": "tea and rum",
    "dad": "Alfie lad",
    "brother": "Danny Glover",
    "sister": "blister",
    "police": "old bill",
    "cop": "grass hopper",
    "thief": "tea leaf",
    "jail": "mail",
    "judge": "fudge",
    "lawyer": "sawyer",
    "fight": "dogfight",
    "gun": "old son",
    "murder": "gert lurder",
    "dead": "brown bread",
    "time": "bird lime",
    "hour": "flower",
    "minute": "spin it",
    "second": "reckon’d",
    "sun": "currant bun",
    "moon": "balloon",
    "rain": "drain",
    "snow": "Jack Frost",
    "sea": "cup of tea",
    "train": "drain",
    "bus": "Gus",
    "boat": "goat",
    "plane": "Jane",
    # Duplicates trimmed intentionally
}


def to_cockney(text: str) -> str:
    out = text
    # naive lower-case pass to catch base words; preserve original case poorly but effective for subs
    low = out.lower()
    for k, v in COCKNEY_MAP.items():
        low = low.replace(k, v)
    # crude reinject (keeps replacements; case-loss is acceptable for subs)
    return low


# -------------------------------
# Kansai-ben converter (rule-based)
# -------------------------------
# Notes:
# - This is a *stylistic* rewrite for conversational lines.
# - We prioritise common, natural swaps. Order matters.
KANSAI_PATTERNS = [
    # Copula / polarity
    (r"です(?!か)", "や"),
    (r"でした", "やった"),
    (r"だよ", "やで"),
    (r"だろう", "やろ"),
    (r"じゃない", "やない"),
    (r"ではない", "やない"),
    # Polite negatives → ～へん / ～ん
    (r"ませんでした", "まへんでした"),   # older flavour; optional
    (r"ません", "まへん"),             # しません→しまへん
    (r"ないです", "あらへん"),
    (r"ない", "へん"),                 # 行かない→行かへん
    # Existential
    (r"いません", "おらへん"),
    (r"いない", "おらん"),
    # Aspect / progressive
    (r"ている", "てる"),
    (r"でいる", "でる"),
    # Requests / invitations
    (r"ましょう", "しよか"),
    (r"ください", "くれへん？"),
    (r"ください。", "くれへん？"),
    # Necessity / obligation
    (r"なければならない", "なあかん"),
    (r"なければいけない", "なあかん"),
    (r"ないといけない", "なあかん"),
    # Particles/lexical
    (r"本当に", "ほんまに"),
    (r"本当に", "ほんまに"),
    (r"とても", "めっちゃ"),
    (r"すごく", "めっちゃ"),
    (r"すごい", "めっちゃ"),
    (r"ありがとう", "おおきに"),
    (r"すみません", "すんません"),
    (r"ごめんなさい", "ごめんな"),
    (r"私(は|が)", r"うち\1"),  # casual; better for female speakers but okay as style
    (r"僕(は|が)", r"わい\1"),   # playful Kansai coloring
    (r"あなた", "あんた"),
    (r"だよね", "やんな"),
    (r"ですよね", "やんな"),
    (r"じゃ(ん|ないか)", "やん"),
    # Sentence endings
    (r"ね。", "な。"),
    (r"ね？", "な？"),
    (r"よ。", "で。"),
]

# Small token swaps that don’t need regex boundaries
KANSAI_WORD_SWAPS = {
    "だから": "せやから",
    "でも": "せやけど",
    "そうだ": "せや",
    "そうです": "せや",
    "大丈夫": "だいじょうぶや",
    "本気": "ほんま",
    "本気で": "ほんまに",
    "冗談": "じょうだんちゃうで",
    "本場": "ほんまもん",
}


def to_kansai(text: str) -> str:
    out = text
    # Regex rules (ordered)
    for pat, rep in KANSAI_PATTERNS:
        out = re.sub(pat, rep, out)
    # Simple swaps (word-level)
    for k, v in KANSAI_WORD_SWAPS.items():
        out = out.replace(k, v)
    return out


# -------------------------------
# Ainu “glossary” mode (experimental)
# -------------------------------
# IMPORTANT:
# This is NOT a general Ainu translator. It respectfully swaps some common
# concepts into well-attested Ainu words/phrases while leaving the rest intact.
AINU_MAP = {
    # Greetings / expressions
    "こんにちは": "イランカラㇷ゚テ (irankarapte)",
    "ありがとう": "イヤイライケレ (iyairaikere)",
    "さようなら": "カムイ ヤイマチセ (kamuy yaimachise)",  # ceremonial-ish farewell nuance
    # Deities / beliefs / nature
    "神": "カムイ (kamuy)",
    "熊": "キムンカムイ (kimun kamuy)",
    "火": "アペ (ape)",
    "水": "ワッカ (wakka)",
    "川": "ワッカオマ (wakka-oma)",  # place with water
    "湖": "ト (to)",
    "海": "アトゥイ (atuy)",
    "山": "ヌプリ (nupuri)",
    "森": "ニ (ni)",
    "木": "ニ (ni)",
    "家": "チセ (cise)",
    "村": "コタン (kotan)",
    # Kinship / people
    "祖先": "アイヌ ランコロ (aynu rankoro)",   # “people who own themselves” — used carefully
    "長老": "エカㇻマㇷ゚ (ekarap)",            # elder/teacher nuance
    # Animals
    "鹿": "ユㇰ (yuk)",
    "狐": "チロンヌㇷ゚ (cironnup)",
    "犬": "セㇺ (sem)",
    "魚": "チェㇷ゚ (cep)",
    # Cultural terms
    "歌": "ウポポ (upopo)",
    "踊り": "リㇺセ (rimse)",
    "儀式": "イヨマンテ (iyomante)",
    "刀": "エムㇷ゚ (empu)",
    # Values / ideas (approximate, poetic use)
    "魂": "ラマッ (ramat)",
    "心": "ラマッ (ramat)",
    "命": "シネㇷ゚ (sinep)",
}

AINU_ROMAJI_FALLBACK = {
    # if the line is in English, we can still inject some Ainu key terms
    "god": "kamuy",
    "bear": "kimun kamuy",
    "fire": "ape",
    "water": "wakka",
    "lake": "to",
    "sea": "atuy",
    "mountain": "nupuri",
    "forest": "ni",
    "house": "cise",
    "village": "kotan",
    "deer": "yuk",
    "fox": "cironnup",
    "dog": "sem",
    "fish": "cep",
    "song": "upopo",
    "dance": "rimse",
    "ceremony": "iyomante",
    "soul": "ramat",
    "spirit": "ramat",
    "life": "sinep",
    "hello": "irankarapte",
    "thanks": "iyairaikere",
    "thank you": "iyairaikere",
}


def to_ainu(text: str) -> str:
    # If it looks like JP, apply Japanese glossary first
    out = text
    jp_hit = False
    for k, v in AINU_MAP.items():
        if k in out:
            out = out.replace(k, v)
            jp_hit = True

    # If it looks like English (or we didn’t hit JP keys), do a soft romanized swap
    if not jp_hit:
        low = out.lower()
        for k, v in AINU_ROMAJI_FALLBACK.items():
            low = low.replace(k, v)
        out = low
    return out


# -------------------------------
# Main translator
# -------------------------------
def normalize_lang_tag(tag: str) -> str:
    t = tag.strip().lower()
    # Friendly names → ISO-ish or mode-tags
    aliases = {
        "english": "en", "eng": "en",
        "japanese": "ja", "jp": "ja",
        "french": "fr", "français": "fr",
        "russian": "ru", "русский": "ru",
        "spanish": "es", "español": "es",
        "kansai": "kansai", "kansai-ben": "kansai", "kansaiben": "kansai",
        "cockney": "cockney", "rhyming": "cockney",
        "ainu": "ainu",
    }
    return aliases.get(t, t)


def translate_line(text: str, target_lang_norm: str, gtrans: GoogleTranslator | None) -> str:
    if target_lang_norm == "cockney":
        return to_cockney(text)
    if target_lang_norm == "kansai":
        return to_kansai(text)
    if target_lang_norm == "ainu":
        return to_ainu(text)

    # Standard language via Google Translator
    if gtrans is None:
        # Graceful fallback if deep_translator not installed
        return text
    try:
        return gtrans.translate(text)
    except Exception:
        time.sleep(0.8)
        return gtrans.translate(text)


def translate_srt(in_path: Path, target_lang: str, out_path: Path, sleep_ms: int = 120) -> None:
    blocks = load_srt(in_path)
    if not blocks:
        raise RuntimeError(f"No blocks found in {in_path}")

    mode = normalize_lang_tag(target_lang)

    # Prepare Google translator only for standard languages
    g = None
    if mode not in ("cockney", "kansai", "ainu"):
        if GoogleTranslator is None:
            g = None
        else:
            g = GoogleTranslator(source="auto", target=mode)

    out_blocks = []
    for (num, start, end, text) in blocks:
        translated = translate_line(text, mode, g)
        out_blocks.append((num, start, end, translated))
        time.sleep(sleep_ms / 1000.0)

    write_srt_from_tuples(out_blocks, out_path)
