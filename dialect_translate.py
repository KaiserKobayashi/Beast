# -*- coding: utf-8 -*-
"""
dialect_translate.py
--------------------
A pluggable phrase-substitution engine for:
  - Cockney (English -> Cockney mix)
  - Kansai-ben (Standard Japanese -> Kansai)
  - Kanto-ben (Standard Japanese -> Kanto/Tokyo colloquial)
  - Ainu (JP/EN seed → Ainu terms where sensible)

Features
- Longest-match, multiword-first substitution
- Case-preserving for English (UPPER, Title, lower)
- Probabilistic mixing (e.g., 0.75 = ~75% of eligible phrases replaced)
- Non-destructive: leaves text intact where no match
- Extensible: load_extra_csv/json() to append or override dictionaries

Usage
------
from dialect_translate import DialectTranslator

tx = DialectTranslator()
print(tx.translate("en", "cockney", "Pick up the phone and close your mouth."))
print(tx.translate("ja", "kansai", "本当に？それはだめだよ。"))
print(tx.translate("ja", "kanto", "本当に？それはだめだよ。"))
print(tx.translate("ja", "ainu", "こんにちは。村へ行く。"))

You can tune mix ratios:
tx.set_mix_ratio(target="cockney", ratio=0.75)  # 75% chance per eligible phrase

License: MIT
"""

from __future__ import annotations
import json
import csv
import os
import re
import random
from typing import Dict, List, Tuple, Iterable, Optional

# -------------------------------
# Helpers
# -------------------------------

def _detect_case_style(word: str) -> str:
    if word.isupper():
        return "UPPER"
    if word[:1].isupper() and word[1:].islower():
        return "Title"
    if word.islower():
        return "lower"
    return "mixed"

def _apply_case_style(src: str, target: str) -> str:
    style = _detect_case_style(src)
    if style == "UPPER":
        return target.upper()
    if style == "Title":
        return target[:1].upper() + target[1:].lower() if target else target
    if style == "lower":
        return target.lower()
    return target

def _escape_regex_token(token: str) -> str:
    return re.escape(token)

def _word_boundary_pattern(phrase: str) -> str:
    p = re.sub(r"\s+", r"\\s+", _escape_regex_token(phrase))
    return r"(?<!\w)" + p + r"(?!\w)"

def _build_sorted_keys(d: Dict[str, str], lang: str) -> List[str]:
    if lang == "ja":
        return sorted(d.keys(), key=lambda k: (len(k), k), reverse=True)
    else:
        return sorted(d.keys(), key=lambda k: (len(k.split()), len(k)), reverse=True)

# -------------------------------
# Lexicons
# -------------------------------

COCKNEY_SEED: Dict[str, str] = {
    "apples and pears": "apples",
    "dog and bone": "dog",
    "butcher's (hook)": "butcher's",
    "butchers": "butcher's",
    "loaf (of bread)": "loaf",
    "trouble and strife": "trouble",
    "boat race": "boat",
    "barnet fair": "Barnet",
    "plates of meat": "plates",
    "mince pies": "minces",
    "rosie lee": "rosie",
    "ruby murray": "ruby",
    "whistle and flute": "whistle",
    "pork pies": "porkies",
    "adam and eve": "Adam and Eve",
    "jam jar": "jam",
    "north and south": "north",
    "dustbin lid": "dustbin",
    "frog and toad": "frog",
    "weasel and stoat": "weasel",
    "hampstead heath": "Hampsteads",
    "china plate": "china",
    "sky rocket": "sky",
    "brown bread": "brown",
    "bees and honey": "bees",
    "brass tacks": "brass tacks",
    "hank marvin": "Hank Marvin",
    "britney spears": "Britneys",
    "duke of kent": "the Duke",
    "jack jones": "on me Jack",
    "jam tart": "jam tart",
    "jimmy riddle": "Jimmy",
    "kettle and hob": "kettle",
    "bobby moore": "Bobby",
    "scooby doo": "Scooby",
    "half inch": "half-inch",
    "police": "Old Bill",
    "boss": "guv",
    "friend": "mate",
    "mouth": "gob",
    "toilet": "loo",
    "umbrella": "brolly",
    "sleep": "kip",
    "very": "proper",
    "really": "proper",
    "great": "ace",
    "cool": "sound",
    "annoying": "well dodgy",
    "phone": "dog",
    "stairs": "apples",
    "hair": "Barnet",
    "eyes": "minces",
    "feet": "plates",
    "suit": "whistle",
    "tea": "rosie",
    "curry": "ruby",
    "lies": "porkies",
    "car": "jam",
    "mouth (tag)": "north",
}

COCKNEY_EXTRA: Dict[str, str] = {
    "look": "have a butcher's",
    "use your head": "use your loaf",
    "i'm starving": "I'm Hank Marvin",
    "beer": "Britneys",
    "door": "Bobby",
    "coat": "weasel",
    "road": "frog",
    "teeth": "Hampsteads",
    "believe": "Adam and Eve",
    "money": "bees",
    "watch": "kettle",
    "alone": "on me Jack",
    "shut up": "shut your north",
    "face": "boat",
    "fart": "raspberry",
    "easy": "lemon squeezy",
    "policeman": "plod",
    "stole": "nicked",
    "broke": "skint",
    "fixed": "sorted",
    "very good": "well good",
    "great job": "proper job",
    "annoyed": "gutted",
    "happy": "chuffed",
    "hard work": "graft",
    "cheap": "naff",
    "neighbourhood": "my ends",
    "guys": "the mandem",
    "girl": "a nice ting",
    "handsome": "peng",
    "unlucky": "peak",
    "leave it": "allow it",
}

KANSAI_SEED: Dict[str, str] = {
    "本当に": "ほんまに",
    "本当だ": "ほんまや",
    "そうだよ": "せやで",
    "そうだね": "せやな",
    "だめだ": "あかん",
    "違う": "ちゃう",
    "とても": "めっちゃ",
    "すごく": "めっちゃ",
    "面白い": "おもろい",
    "ありがとう": "おおきに",
    "寒い": "さぶい",
    "暖かい": "ぬくい",
    "片付ける": "なおす",
    "捨てる": "ほかす",
    "〜している": "〜してはる",
    "〜している？": "〜してはる？",
    "だよ": "やで",
    "だね": "やな",
    "だよね": "やろ",
    "〜だと思う": "〜やと思う",
    "どうする": "どないする",
    "いくら": "なんぼ",
    "本気で": "ガチで（関西）",
    "冗談": "ちゃうちゃう（冗談）",
    "そうです": "せや",
    "なんで": "なんでやねん",
}

KANTO_SEED: Dict[str, str] = {
    "本当に": "マジで",
    "とても": "超",
    "すごく": "超",
    "だよ": "だよ",
    "だね": "だね",
    "だよね": "じゃん",
    "でしょう": "っしょ",
    "気持ち悪い": "キモい",
    "うざい": "ウザい",
    "すごい": "やばい",
    "ちょっと疲れた": "だるい",
    "面倒くさい": "めんどい",
    "普通に": "普通に",
    "本気で": "ガチで",
    "いいね": "いいじゃん",
}

AINU_SEED_JA: Dict[str, str] = {
    "こんにちは": "イランカラプテ",
    "ありがとう": "イヤイライケレ",
    "村": "コタン",
    "神": "カムイ",
    "家": "チセ",
    "言葉": "アイヌ イタク",
    "詩": "ユーカラ",
}

AINU_SEED_EN: Dict[str, str] = {
    "hello": "Irankarapte",
    "thank you": "Iyairaikere",
    "village": "kotan",
    "deity": "kamuy",
    "spirit": "ramat",
    "house": "cise",
    "language": "Ainu itak",
    "epic": "yukar",
}

# ---------------------------------------------------
# Translator class
# ---------------------------------------------------

class DialectTranslator:
    def __init__(self, rng_seed: int = 42):
        self.random = random.Random(rng_seed)
        self.mix = {
            "cockney": 0.75,  # default: use Cockney 75% of the time where applicable
            "kansai":  0.60,
            "kanto":   0.50,
            "ainu":    0.30,
        }

        self._cockney_map = self._canonicalize_map(COCKNEY_SEED | COCKNEY_EXTRA, "en")
        self._cockney_keys = _build_sorted_keys(self._cockney_map, "en")
        self._cockney_regexes = {k: re.compile(_word_boundary_pattern(k), re.IGNORECASE) for k in self._cockney_keys}

        self._kansai_map = self._canonicalize_map(KANSAI_SEED, "ja")
        self._kansai_keys = _build_sorted_keys(self._kansai_map, "ja")

        self._kanto_map = self._canonicalize_map(KANTO_SEED, "ja")
        self._kanto_keys = _build_sorted_keys(self._kanto_map, "ja")

        self._ainu_ja_map = self._canonicalize_map(AINU_SEED_JA, "ja")
        self._ainu_ja_keys = _build_sorted_keys(self._ainu_ja_map, "ja")

        self._ainu_en_map = self._canonicalize_map(AINU_SEED_EN, "en")
        self._ainu_en_keys = _build_sorted_keys(self._ainu_en_map, "en")
        self._ainu_en_regexes = {k: re.compile(_word_boundary_pattern(k), re.IGNORECASE) for k in self._ainu_en_keys}

    def set_mix_ratio(self, target: str, ratio: float) -> None:
        if target not in self.mix:
            raise ValueError(f"Unknown target: {target}")
        self.mix[target] = max(0.0, min(1.0, float(ratio)))

    def translate(self, src_lang: str, target: str, text: str) -> str:
        src_lang = src_lang.lower()
        target = target.lower()
        if target == "cockney":
            if src_lang != "en":
                return text
            return self._replace_en(text, self._cockney_map, self._cockney_regexes, self.mix["cockney"])
        if target == "kansai":
            if src_lang != "ja":
                return text
            return self._replace_ja(text, self._kansai_map, self._kansai_keys, self.mix["kansai"])
        if target == "kanto":
            if src_lang != "ja":
                return text
            return self._replace_ja(text, self._kanto_map, self._kanto_keys, self.mix["kanto"])
        if target == "ainu":
            ratio = self.mix["ainu"]
            if src_lang == "ja":
                return self._replace_ja(text, self._ainu_ja_map, self._ainu_ja_keys, ratio)
            elif src_lang == "en":
                return self._replace_en(text, self._ainu_en_map, self._ainu_en_regexes, ratio)
            else:
                return text
        raise ValueError(f"Unknown target: {target}")

    def _replace_en(self, text: str, mapping: Dict[str, str], regexes: Dict[str, re.Pattern], ratio: float) -> str:
        out = text
        for src in mapping.keys():
            rgx = regexes[src]
            tgt = mapping[src]
            def _sub(m: re.Match) -> str:
                if self.random.random() > ratio:
                    return m.group(0)
                s = m.group(0)
                if " " in s.strip():
                    first_src = s.split()[0]
                    return _apply_case_style(first_src, tgt)
                return _apply_case_style(s, tgt)
            out = rgx.sub(_sub, out)
        return out

    def _replace_ja(self, text: str, mapping: Dict[str, str], keys: List[str], ratio: float) -> str:
        s = text
        for src in keys:
            tgt = mapping[src]
            idx = 0
            result = []
            while idx < len(s):
                hit = s.find(src, idx)
                if hit < 0:
                    result.append(s[idx:])
                    break
                result.append(s[idx:hit])
                frag = s[hit:hit+len(src)]
                if self.random.random() <= ratio:
                    result.append(tgt)
                else:
                    result.append(frag)
                idx = hit + len(src)
            s = "".join(result)
        return s

    def load_extra_csv(self, path: str, dialect: str, source_lang: str) -> int:
        dialect = dialect.lower()
        n = 0
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                src = (row.get("source") or "").strip()
                tgt = (row.get("target") or "").strip()
                if not src or not tgt:
                    continue
                if dialect == "cockney" and source_lang == "en":
                    self._cockney_map[src] = tgt
                elif dialect == "kansai" and source_lang == "ja":
                    self._kansai_map[src] = tgt
                elif dialect == "kanto" and source_lang == "ja":
                    self._kanto_map[src] = tgt
                elif dialect == "ainu" and source_lang == "ja":
                    self._ainu_ja_map[src] = tgt
                elif dialect == "ainu" and source_lang == "en":
                    self._ainu_en_map[src] = tgt
                else:
                    continue
                n += 1
        return n

    def load_extra_json(self, path: str, dialect: str, source_lang: str) -> int:
        with open(path, "r", encoding="utf-8") as f:
            obj = json.load(f)
        if not isinstance(obj, dict):
            return 0
        tmp = path + ".tmp.csv"
        with open(tmp, "w", newline="", encoding="utf-8") as w:
            wr = csv.writer(w)
            wr.writerow(["source", "target"])
            for k, v in obj.items():
                wr.writerow([k, v])
        try:
            return self.load_extra_csv(tmp, dialect=dialect, source_lang=source_lang)
        finally:
            try:
                os.remove(tmp)
            except Exception:
                pass

    def _canonicalize_map(self, m: Dict[str, str], lang: str) -> Dict[str, str]:
        out = {}
        for k, v in m.items():
            kk = k.strip()
            vv = v.strip()
            if kk and vv:
                out[kk] = vv
        return out


if __name__ == "__main__":
    tx = DialectTranslator(rng_seed=7)

    print("COCKNEY TEST:")
    s = "Use your head, look at his face, and pick up the phone near the stairs."
    print("IN :", s)
    print("OUT:", tx.translate("en", "cockney", s))

    print("\nKANSAI TEST:")
    s2 = "本当に？それはだめだよ。ありがとう、面白いね。"
    print("IN :", s2)
    print("OUT:", tx.translate("ja", "kansai", s2))

    print("\nKANTO TEST:")
    s3 = "本当に？それはだめだよ。気持ち悪い。"
    print("IN :", s3)
    print("OUT:", tx.translate("ja", "kanto", s3))

    print("\nAINU (JP) TEST:")
    s4 = "こんにちは。神の詩と村の家。"
    print("IN :", s4)
    print("OUT:", tx.translate("ja", "ainu", s4))

    print("\nAINU (EN) TEST:")
    s5 = "Hello, thank you, spirit, language, and village."
    print("IN :", s5)
    print("OUT:", tx.translate("en", "ainu", s5))
