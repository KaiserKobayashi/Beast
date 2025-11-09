"""
Module entrypoint used by `python -m downloadbeast` and the console script `kaiser-communicator`.
It tries to call a GUI main() if present; otherwise prints diagnostics.
"""

import importlib
import sys

def _try_import_and_run(module_name, func_name="main"):
    try:
        mod = importlib.import_module(module_name)
    except Exception:
        return False
    fn = getattr(mod, func_name, None)
    if callable(fn):
        fn()
        return True
    # try alternate names
    for alt in ("run", "start", "launch"):
        fn = getattr(mod, alt, None)
        if callable(fn):
            fn()
            return True
    return False

def main():
    candidates = [
        "downloadbeast.gui",
        "downloadbeast.app",
        "downloadbeast.interface",
        "gui",
        "app",
    ]
    for c in candidates:
        if _try_import_and_run(c, "main"):
            return

    print("No GUI entrypoint found by kaiser-communicator.")
    print("Tried importing these modules (looking for a callable main/run/start):")
    for t in candidates:
        print(" -", t)
    print()
    print("To fix: create src/downloadbeast/gui.py with a main() function, or tell me where your GUI entrypoint lives.")
    sys.exit(1)

if __name__ == "__main__":
    main()