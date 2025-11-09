from __future__ import annotations
def join_args(*parts: object) -> list[str]:
    out: list[str] = []
    for p in parts:
        if p is None: continue
        s = str(p).strip()
        if not s: continue
        out.append(s)
    return out
def extend_args(base: list[str], *more: object) -> list[str]:
    base.extend(join_args(*more)); return base
