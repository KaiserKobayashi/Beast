import os, sys
print("cwd:", os.getcwd())
print("sys.path[0]:", sys.path[0])
try:
    import tts_helpers, playlist_helpers
    print("IMPORT OK")
except Exception as e:
    print("IMPORT FAILED:", e)
