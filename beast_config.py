"""
Small config helper to persist GUI settings.
Saves config to %APPDATA% on Windows or ~/.config/beast/config.json on Unix.
"""
import json
import os
from pathlib import Path

def config_path():
    if os.name == "nt":
        base = os.getenv("APPDATA") or str(Path.home())
    else:
        base = os.path.join(Path.home(), ".config")
    cfg_dir = os.path.join(base, "beast")
    os.makedirs(cfg_dir, exist_ok=True)
    return os.path.join(cfg_dir, "config.json")

default_config = {
    "theme": "SystemDefault",
    "voices": ["default"],
    "last_input": "",
    "last_output": "",
    "last_voice": "default",
    "last_format": "mp3",
    "last_rate": 1.0,
    "current_profile": "User 1",
    "profiles": {
        "User 1": {
            "language": "en-US",
            "gender": "female",
            "voice_index": 0
        },
        "User 2": {
            "language": "en-US",
            "gender": "male",
            "voice_index": 0
        }
    }
}

def load_config():
    p = config_path()
    try:
        with open(p, "r", encoding="utf-8") as f:
            d = json.load(f)
            if isinstance(d, dict):
                return {**default_config, **d}
    except Exception:
        pass
    return dict(default_config)

def save_config(cfg):
    p = config_path()
    try:
        with open(p, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass
