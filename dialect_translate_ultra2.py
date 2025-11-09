# -*- coding: utf-8 -*-
"""
dialect_translate_ultra2.py
---------------------------
Ultra²: faster overlap handling, safer boundaries, cached protections, real context hints,
stronger JP boundary checks, slotted dataclasses, leaner hashing, and a few safety guards.

Public API (same as your ultra version):
- DialectTranslator(rng_seed: Optional[int]=None, enable_profiling: bool=False)
- translate(source_lang: str, target_dialect: str, text: str, consistent: bool=False) -> str
- translate_stream(...)
- set_mix_ratio(target: str, ratio: float)
- set_group_mix(target: str, group: PhraseGroup, ratio: float)
- configure_protection(ProtectionConfig(...))
- load_csv(path, dialect, source_lang) / export_json(path, dialect, source_lang)
- get_available_dialects() / get_stats(dialect)
"""

from __future__ import annotations
import csv, json, hashlib, random, re, threading, time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Tuple, Optional, Iterable, Set, Generator
from collections import defaultdict

# -------------------- Optional dependency --------------------
try:
    import ahocorasick  # pip install pyahocorasick
    HAS_AC = True
except Exception:
    HAS_AC = False

# -------------------- Case handling --------------------
class CaseStrategy(Enum):
    PRESERVE_FIRST = auto()
    PRESERVE_ALL   = auto()
    LOWERCASE      = auto()
    ORIGINAL       = auto()

def _detect_case(word: str) -> str:
    if not word: return "lower"
    if word.isupper(): return "UPPER"
    if word[0:1].isupper() and word[1:].islower(): return "Title"
    if word.islower(): return "lower"
    return "mixed"

def _apply_case(src_word: str, target: str, strategy: CaseStrategy) -> str:
    if strategy == CaseStrategy.ORIGINAL:
        return target
    if strategy == CaseStrategy.LOWERCASE:
        return target.lower()
    style = _detect_case(src_word)
    if strategy == CaseStrategy.PRESERVE_ALL:
        if style == "UPPER":  return target.upper()
        if style == "Title":  return target.capitalize()
        if style == "lower":  return target.lower()
        return target
    # PRESERVE_FIRST
    if style == "UPPER":  return target.upper()
    if style == "Title":  return target[:1].upper() + target[1:]
    if style == "lower":  return target.lower()
    return target

# -------------------- Boundaries & protections --------------------
# stdlib re-safe classes (Latin-1 + Greek + Cyrillic)
WORD_CHAR  = r"[0-9A-Za-z_\u00C0-\u024F\u0370-\u03FF\u0400-\u04FF]"
APOSTROPHE = r"[’'`]"

def build_boundary_pattern(phrase: str) -> str:
    """Flexible whitespace inside phrase, hard boundaries left/right."""
    esc = re.escape(phrase)
    esc = re.sub(r"\\\s+", r"\\s+", esc)
    left  = rf"(?:(?<!{WORD_CHAR})(?<!{APOSTROPHE}))"
    right = rf"(?:(?!{APOSTROPHE})(?!{WORD_CHAR}))"
    return left + esc + right

class ProtectionConfig:
    """Configurable protection with caching."""
    __slots__ = ('urls','emails','code_inline','code_blocks','custom_patterns','_cache','_sig')
    def __init__(self, urls=True, emails=True, code_inline=True, code_blocks=True, custom_patterns=None):
        self.urls = urls; self.emails = emails
        self.code_inline = code_inline; self.code_blocks = code_blocks
        self.custom_patterns = custom_patterns or []
        self._cache = None
        self._sig = None
    def _signature(self) -> tuple:
        return (self.urls, self.emails, self.code_inline, self.code_blocks, tuple(self.custom_patterns))
    def build_pattern(self) -> Optional[re.Pattern]:
        sig = self._signature()
        if self._cache is not None and sig == self._sig:
            return self._cache
        parts = []
        if self.code_blocks: parts.append(r"```[\s\S]*?```")
        if self.code_inline: parts.append(r"`[^`]*?`")
        if self.urls:       parts.append(r"https?://\S+")
        if self.emails:     parts.append(r"\b[\w\.-]+@[\w\.-]+\.\w{2,}")
        parts.extend(self.custom_patterns)
        self._cache = re.compile("|".join(f"(?:{p})" for p in parts), re.IGNORECASE) if parts else None
        self._sig = sig
        return self._cache

# -------------------- Profiling --------------------
class Profiler:
    __slots__ = ('enabled','timings','counts')
    def __init__(self, enabled: bool=False):
        self.enabled = enabled
        self.timings: Dict[str, List[float]] = defaultdict(list)
        self.counts: Dict[str, int] = defaultdict(int)
    def time(self, label: str):
        if not self.enabled: return _NoOpCtx()
        return _TimingCtx(self, label)
    def report(self) -> str:
        if not self.enabled or not self.timings:
            return "Profiling disabled or no data"
        lines = ["Performance Profile:"]
        for label, times in sorted(self.timings.items()):
            count = self.counts.get(label, len(times))
            total = sum(times); avg = total / max(count,1)
            lines.append(f"  {label}: {count}x, {total*1000:.2f}ms total, {avg*1000:.3f}ms avg")
        return "\n".join(lines)

class _NoOpCtx:
    def __enter__(self): return self
    def __exit__(self, *a): pass

class _TimingCtx:
    __slots__ = ('p','label','start')
    def __init__(self, p: Profiler, label: str):
        self.p = p; self.label = label; self.start = 0.0
    def __enter__(self):
        self.start = time.perf_counter(); return self
    def __exit__(self, *a):
        self.p.timings[self.label].append(time.perf_counter() - self.start)
        self.p.counts[self.label] += 1

# -------------------- Phrase metadata & groups --------------------
class PhraseGroup(Enum):
    COMMON    = auto()
    RARE      = auto()
    SLANG     = auto()
    TECHNICAL = auto()
    CUSTOM    = auto()

class ContextHint(Enum):
    SENTENCE_START     = auto()
    SENTENCE_END       = auto()
    BEFORE_PUNCTUATION = auto()
    AFTER_PUNCTUATION  = auto()
    STANDALONE         = auto()
    EMBEDDED           = auto()

class PhraseMetadata:
    __slots__ = ('target','weight','group','context_hints','added_by')
    def __init__(self, target: str, weight: float=1.0, group: PhraseGroup=PhraseGroup.COMMON,
                 context_hints: Optional[Set[ContextHint]]=None, added_by: str="builtin"):
        self.target = target
        self.weight = float(max(0.0, min(1.0, weight)))
        self.group = group
        self.context_hints = context_hints or set()
        self.added_by = added_by

# -------------------- Dialect storage (slotted dataclass) --------------------
@dataclass(slots=True)
class DialectData:
    name: str
    source_lang: str
    phrases: Dict[str, PhraseMetadata] = field(default_factory=dict)
    sorted_keys: List[str] = field(default_factory=list)
    regex_cache: Dict[str, re.Pattern] = field(default_factory=dict)
    case_strategy: CaseStrategy = CaseStrategy.PRESERVE_FIRST
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    _ac_compiled: bool = False
    _ac: Optional[object] = None

    def _rebuild_indices(self) -> None:
        if self.source_lang == "ja":
            self.sorted_keys = sorted(self.phrases, key=lambda k: (len(k), k), reverse=True)
            self.regex_cache.clear()
        else:
            self.sorted_keys = sorted(self.phrases, key=lambda k: (len(k.split()), len(k), k), reverse=True)
            self.regex_cache.clear()
        self._ac_compiled = False
        self._ac = None

    def get_or_compile_regex(self, phrase: str) -> re.Pattern:
        pat = self.regex_cache.get(phrase)
        if pat is None:
            pat = re.compile(build_boundary_pattern(phrase), re.IGNORECASE)
            self.regex_cache[phrase] = pat
        return pat

    def get_or_build_ac(self) -> Optional[object]:
        if not HAS_AC or self.source_lang == "ja":
            return None
        if self._ac_compiled:
            return self._ac
        with self._lock:
            if self._ac_compiled:
                return self._ac
            ac = ahocorasick.Automaton()
            for key in self.sorted_keys:
                ac.add_word(key.lower(), key)
            ac.make_automaton()
            self._ac = ac
            self._ac_compiled = True
            return self._ac

    def add_phrase(self, src: str, meta: PhraseMetadata) -> None:
        src = (src or "").strip()
        if not src or not meta.target.strip(): return
        with self._lock:
            self.phrases[src] = meta
            self._rebuild_indices()

    def add_phrases_bulk(self, mapping: Dict[str, PhraseMetadata]) -> int:
        c = 0
        with self._lock:
            for s, m in mapping.items():
                s = (s or "").strip()
                if s and m.target.strip():
                    self.phrases[s] = m; c += 1
            if c: self._rebuild_indices()
        return c

# -------------------- Built-in lexicons --------------------
COCKNEY_FULL = {
    "apples and pears": "apples", "dog and bone": "dog", "butcher's hook": "butcher's",
    "loaf of bread": "loaf", "trouble and strife": "trouble", "boat race": "boat",
    "barnet fair": "Barnet", "plates of meat": "plates", "mince pies": "minces",
    "rosie lee": "rosie", "ruby murray": "ruby", "whistle and flute": "whistle",
    "pork pies": "porkies", "adam and eve": "Adam and Eve", "jam jar": "jam",
    "north and south": "north", "dustbin lid": "dustbin", "frog and toad": "frog",
    "weasel and stoat": "weasel", "hampstead heath": "Hampsteads", "china plate": "china",
    "sky rocket": "sky", "brown bread": "brown", "bees and honey": "bees",
    "hank marvin": "Hank Marvin", "britney spears": "Britneys",
    "use your head": "use your loaf", "look": "have a butcher's", "phone": "dog",
    "stairs": "apples", "hair": "Barnet", "eyes": "minces", "feet": "plates",
    "suit": "whistle", "tea": "rosie", "curry": "ruby", "lies": "porkies",
    "car": "jam", "mouth": "gob", "toilet": "loo", "umbrella": "brolly",
    "sleep": "kip", "very": "proper", "really": "proper", "great": "ace",
    "cool": "sound", "boss": "guv", "friend": "mate",
    "very good": "well good", "great job": "proper job", "annoyed": "gutted",
    "happy": "chuffed", "hard work": "graft", "cheap": "naff", "fixed": "sorted",
    "stole": "nicked", "broke": "skint",
}

KANSAI_FULL = {
    "本当に": "ほんまに", "本当だ": "ほんまや", "そうだよ": "せやで", "そうだね": "せやな",
    "だめだ": "あかん", "違う": "ちゃう", "とても": "めっちゃ", "すごく": "めっちゃ",
    "面白い": "おもろい", "ありがとう": "おおきに", "寒い": "さぶい", "暖かい": "ぬくい",
    "片付ける": "なおす", "捨てる": "ほかす", "だよ": "やで", "だね": "やな",
    "だよね": "やろ", "どうする": "どないする", "いくら": "なんぼ", "本気で": "ガチで",
    "そうです": "せや", "なんで": "なんでやねん",
}

KANTO_FULL = {
    "本当に": "マジで", "とても": "超", "すごく": "超", "だよね": "じゃん",
    "でしょう": "っしょ", "気持ち悪い": "キモい", "うざい": "ウザい",
    "すごい": "やばい", "ちょっと疲れた": "だるい", "面倒くさい": "めんどい",
    "普通に": "普通に", "本気で": "ガチで", "いいね": "いいじゃん",
}

AINU_JA = {
    "こんにちは": "イランカラプテ", "ありがとう": "イヤイライケレ",
    "村": "コタン", "神": "カムイ", "家": "チセ", "言葉": "アイヌ イタク", "詩": "ユーカラ",
}
AINU_EN = {
    "hello": "Irankarapte", "thank you": "Iyairaikere", "village": "kotan",
    "deity": "kamuy", "spirit": "ramat", "house": "cise", "language": "Ainu itak", "epic": "yukar",
}

# -------------------- Helpers (context & JP boundary) --------------------
SENT_END = re.compile(r"[.!?]\s+$")

def _context_multiplier(text: str, start: int, end: int) -> float:
    mult = 1.0
    left = text[:start]
    if not left or SENT_END.search(left[-4:]):
        mult *= 1.15
    if end < len(text) and text[end:end+1] in ",.;:!?":
        mult *= 1.05
    return mult

def _is_kana_or_cjk(ch: str) -> bool:
    if not ch: return False
    o = ord(ch)
    return (0x3040 <= o <= 0x30FF) or (0x4E00 <= o <= 0x9FFF) or (0x3400 <= o <= 0x4DBF) or (0xF900 <= o <= 0xFAFF)

# -------------------- Consistency hashing --------------------
def _decide_consistent(seed: int, phrase: str, span: Tuple[int,int], text_hash: str, ratio: float) -> bool:
    key = f"{seed}|{phrase}|{span[0]}|{span[1]}|{text_hash}".encode("utf-8")
    h = int(hashlib.blake2b(key, digest_size=8).hexdigest(), 16) % 10000
    return h <= int(max(0.0, min(1.0, ratio)) * 10000)

def _decide_batch(seed: int, phrases, spans, text_hash: str, ratios) -> List[bool]:
    pre = f"{seed}|".encode("utf-8")
    out = []
    blake = hashlib.blake2b
    for (p,(s,e),r) in zip(phrases, spans, ratios):
        key = pre + f"{p}|{s}|{e}|{text_hash}".encode("utf-8")
        h = int(blake(key, digest_size=8).hexdigest(), 16) % 10000
        out.append(h <= int(max(0.0, min(1.0, r)) * 10000))
    return out

# -------------------- Main translator --------------------
class DialectTranslator:
    def __init__(self, rng_seed: Optional[int]=None, enable_profiling: bool=False):
        self._rng = random.Random(rng_seed)
        self._seed = rng_seed if rng_seed is not None else random.randrange(1<<30)
        self._lock = threading.Lock()
        self._dialects: Dict[str, DialectData] = {}
        self._mix_ratios: Dict[str, float] = {}
        self._group_mix: Dict[str, Dict[PhraseGroup, float]] = {}
        self._protection = ProtectionConfig()
        self._profiler = Profiler(enabled=enable_profiling)
        self._register_defaults()

    # ---- registry ----
    def _register_defaults(self):
        cockney_meta = {
            k: PhraseMetadata(v, weight=(0.9 if len(k.split()) > 2 else 0.75), group=PhraseGroup.SLANG)
            for k, v in COCKNEY_FULL.items()
        }
        self._register_dialect("cockney", "en", cockney_meta, 0.75, CaseStrategy.PRESERVE_FIRST)

        self._register_dialect("kansai", "ja",
            {k: PhraseMetadata(v, group=PhraseGroup.COMMON) for k, v in KANSAI_FULL.items()}, 0.60)

        self._register_dialect("kanto", "ja",
            {k: PhraseMetadata(v, group=PhraseGroup.SLANG) for k, v in KANTO_FULL.items()}, 0.50)

        self._register_dialect("ainu_ja", "ja",
            {k: PhraseMetadata(v, group=PhraseGroup.RARE) for k, v in AINU_JA.items()}, 0.30)

        self._register_dialect("ainu_en", "en",
            {k: PhraseMetadata(v, group=PhraseGroup.RARE) for k, v in AINU_EN.items()}, 0.30)

    def _register_dialect(self, name: str, source_lang: str, meta: Dict[str, PhraseMetadata],
                          mix_ratio: float, case_strategy: CaseStrategy=CaseStrategy.PRESERVE_FIRST):
        d = DialectData(name=name.lower(), source_lang=source_lang.lower(), case_strategy=case_strategy)
        d.add_phrases_bulk(meta)
        with self._lock:
            self._dialects[d.name] = d
            self._mix_ratios[d.name] = float(max(0.0, min(1.0, mix_ratio)))
            self._group_mix[d.name] = {g: 1.0 for g in PhraseGroup}

    def register_dialect(self, name: str, source_lang: str, phrases: Dict[str,str],
                         mix_ratio: float=0.5, case_strategy: CaseStrategy=CaseStrategy.PRESERVE_FIRST,
                         phrase_group: PhraseGroup=PhraseGroup.CUSTOM):
        meta = {k: PhraseMetadata(v, group=phrase_group) for k, v in phrases.items()}
        self._register_dialect(name, source_lang, meta, mix_ratio, case_strategy)

    # ---- knobs ----
    def set_mix_ratio(self, target: str, ratio: float) -> None:
        t = target.lower()
        if t not in self._dialects: raise ValueError(f"Unknown dialect: {t}")
        self._mix_ratios[t] = float(max(0.0, min(1.0, ratio)))

    def set_group_mix(self, target: str, group: PhraseGroup, ratio: float) -> None:
        t = target.lower()
        if t not in self._dialects: raise ValueError(f"Unknown dialect: {t}")
        self._group_mix[t][group] = float(max(0.0, min(1.0, ratio)))

    def configure_protection(self, config: ProtectionConfig) -> None:
        self._protection = config

    # ---- I/O ----
    def load_csv(self, path: str, dialect: str, source_lang: str) -> int:
        name = self._resolve_name(dialect, source_lang)
        if name not in self._dialects: raise ValueError(f"Unknown dialect: {name}")
        def _safe_float(x, default=1.0):
            try: return float(x)
            except (TypeError, ValueError): return default
        count = 0
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                src = (row.get("source") or "").strip()
                tgt = (row.get("target") or "").strip()
                if not src or not tgt: continue
                group_raw = (row.get("group") or "COMMON").upper().strip()
                group = PhraseGroup.__members__.get(group_raw, PhraseGroup.CUSTOM)
                weight = _safe_float(row.get("weight"), 1.0)
                meta = PhraseMetadata(tgt, weight, group)
                self._dialects[name].add_phrase(src, meta)
                count += 1
        return count

    def export_json(self, path: str, dialect: str, source_lang: str) -> None:
        name = self._resolve_name(dialect, source_lang)
        if name not in self._dialects: raise ValueError(f"Unknown dialect: {name}")
        data = {
            k: {"target": m.target, "weight": m.weight, "group": m.group.name}
            for k, m in self._dialects[name].phrases.items()
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ---- Public translate ----
    def translate(self, source_lang: str, target_dialect: str, text: str, consistent: bool=False) -> str:
        with self._profiler.time("translate_total"):
            name = self._resolve_name(target_dialect, source_lang)
            d = self._dialects.get(name)
            if not d: raise ValueError(f"Unknown dialect: {name}")
            if d.source_lang != source_lang.lower(): return text

            # Protection carve-out (cached)
            with self._profiler.time("protection_scan"):
                segs = self._extract_protected(text)

            out = []
            for chunk, is_prot in segs:
                if is_prot or not chunk:
                    out.append(chunk); continue
                if d.source_lang == "ja":
                    out.append(self._translate_ja(chunk, d, name, consistent))
                else:
                    out.append(self._translate_en(chunk, d, name, consistent))
            return "".join(out)

    def translate_stream(self, source_lang: str, target_dialect: str,
                         text_stream: Iterable[str], consistent: bool=False) -> Generator[str, None, None]:
        for chunk in text_stream:
            yield self.translate(source_lang, target_dialect, chunk, consistent)

    # ---- Stats ----
    def get_profiler_report(self) -> str:
        return self._profiler.report()

    def get_available_dialects(self) -> List[str]:
        return list(self._dialects.keys())

    def get_stats(self, dialect: str) -> Dict[str, object]:
        t = dialect.lower()
        if t not in self._dialects: return {}
        d = self._dialects[t]
        by_group = defaultdict(int)
        for m in d.phrases.values():
            by_group[m.group.name] += 1
        return {
            "total_phrases": len(d.phrases),
            "by_group": dict(by_group),
            "has_ac": d._ac_compiled,
            "regex_cached": len(d.regex_cache)
        }

    # ---- internals ----
    def _resolve_name(self, dialect: str, src_lang: str) -> str:
        dialect = dialect.lower()
        if dialect == "ainu": return f"ainu_{src_lang.lower()}"
        return dialect

    def _extract_protected(self, text: str) -> List[Tuple[str, bool]]:
        pat = self._protection.build_pattern()
        if not pat: return [(text, False)]
        segs: List[Tuple[str,bool]] = []
        last = 0
        for m in pat.finditer(text):
            if m.start() > last: segs.append((text[last:m.start()], False))
            segs.append((m.group(0), True))
            last = m.end()
        if last < len(text): segs.append((text[last:], False))
        return segs if segs else [(text, False)]

    def _translate_en(self, text: str, d: DialectData, name: str, consistent: bool) -> str:
        if not text or not d.sorted_keys: return text

        # Collect matches (AC if available)
        matches: List[Tuple[int,int,str]] = []
        with self._profiler.time("en_matching"):
            ac = d.get_or_build_ac() if HAS_AC else None
            if ac:
                low = text.lower()
                for end, key in ac.iter(low):
                    start = end - len(key) + 1
                    if d.get_or_compile_regex(key).match(text, start):
                        matches.append((start, start+len(key), key))
            else:
                for key in d.sorted_keys:
                    pat = d.get_or_compile_regex(key)
                    for m in pat.finditer(text):
                        matches.append((m.start(), m.end(), key))

        if not matches: return text

        # Resolve overlaps: longest first, then greedy linear sweep
        with self._profiler.time("en_overlap_resolution"):
            matches.sort(key=lambda t: (-(t[1]-t[0]), t[0]))
            chosen: List[Tuple[int,int,str]] = []
            for s,e,k in matches:
                if not chosen or s >= chosen[-1][1]:
                    chosen.append((s,e,k))
                else:
                    i = len(chosen) - 1
                    while i >= 0 and not (e <= chosen[i][0] or s >= chosen[i][1]):
                        i -= 1
                    if i < 0 or s >= chosen[i][1]:
                        chosen.insert(i+1, (s,e,k))
            chosen.sort(key=lambda x: x[0])

        # Replacement with context multipliers
        with self._profiler.time("en_replacement"):
            base = self._mix_ratios[name]
            group_mults = self._group_mix[name]
            txt_hash = hashlib.blake2b(text.encode("utf-8"), digest_size=8).hexdigest()

            if consistent:
                phrases = [k for _,_,k in chosen]
                spans   = [(s,e) for s,e,_ in chosen]
                ratios  = []
                for (s,e,k) in chosen:
                    meta = d.phrases[k]
                    eff = base * group_mults.get(meta.group, 1.0) * meta.weight * _context_multiplier(text, s, e)
                    ratios.append(eff)
                decisions = _decide_batch(self._seed, phrases, spans, txt_hash, ratios)

            out = []
            cur = 0
            for idx, (s,e,k) in enumerate(chosen):
                if s > cur: out.append(text[cur:s])
                meta = d.phrases[k]
                eff = base * group_mults.get(meta.group, 1.0) * meta.weight * _context_multiplier(text, s, e)
                choose = decisions[idx] if consistent else (self._rng.random() <= eff)
                segment = text[s:e]
                if choose:
                    first_word = segment.split()[0] if " " in segment else segment
                    out.append(_apply_case(first_word, meta.target, d.case_strategy))
                else:
                    out.append(segment)
                cur = e
            if cur < len(text): out.append(text[cur:])
            return "".join(out)

    def _translate_ja(self, text: str, d: DialectData, name: str, consistent: bool) -> str:
        if not text or not d.sorted_keys: return text
        with self._profiler.time("ja_replacement"):
            res = text
            base = self._mix_ratios[name]
            group_mults = self._group_mix[name]
            txt_hash = hashlib.blake2b(text.encode("utf-8"), digest_size=8).hexdigest()
            for key in d.sorted_keys:
                meta = d.phrases[key]
                parts = []; i = 0; L = len(res)
                while i < L:
                    j = res.find(key, i)
                    if j < 0:
                        parts.append(res[i:]); break
                    parts.append(res[i:j])
                    # boundary guard (kana/kanji adjacency)
                    left_ok  = (j == 0) or not (_is_kana_or_cjk(res[j-1]) and _is_kana_or_cjk(key[0]))
                    right_idx = j + len(key)
                    right_ok = (right_idx >= L) or not (_is_kana_or_cjk(res[right_idx]) and _is_kana_or_cjk(key[-1]))
                    if not (left_ok and right_ok):
                        parts.append(key); i = j + len(key); continue
                    eff = base * group_mults.get(meta.group, 1.0) * meta.weight
                    choose = _decide_consistent(self._seed, key, (j, j+len(key)), txt_hash, eff) if consistent \
                             else (self._rng.random() <= eff)
                    parts.append(meta.target if choose else key)
                    i = j + len(key)
                res = "".join(parts); L = len(res)
            return res

# -------------------- CLI quick test --------------------
if __name__ == "__main__":
    tx = DialectTranslator(rng_seed=42, enable_profiling=True)
    tests = [
        ("en","cockney","Use your head, look at his face, and pick up the phone near the stairs."),
        ("en","cockney","Look at the phone. Look at the phone again. Pick up the phone."),
        ("ja","kansai","本当に？それはだめだよ。ありがとう、面白いね。"),
        ("ja","kanto","本当に？それはだめだよ。気持ち悪い。"),
        ("en","cockney","Check https://example.com/phone and `code: phone` then LOOK at the PHONE!"),
    ]
    for src, dia, s in tests:
        print("\n", dia.upper(), f"({src})")
        print("IN :", s)
        print("OUT:", tx.translate(src, dia, s, consistent=True))
    print("\n--- Stats ---")
    for d in tx.get_available_dialects():
        print(d, tx.get_stats(d))
    print("\n--- Profile ---")
    print(tx.get_profiler_report())