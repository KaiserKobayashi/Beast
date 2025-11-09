import PySimpleGUI as sg
from pathlib import Path
from DownloadBeast.pipeline_core import run_core

sg.theme("SystemDefaultForReal")

layout = [
    [sg.Text("Source (URL or File)"), sg.Input(key="-SRC-", expand_x=True), sg.FileBrowse("Browse…")],
    [sg.Text("Output Folder"), sg.Input(key="-OUT-", expand_x=True), sg.FolderBrowse("Select…")],
    [sg.Text("Subtitle files (.srt, multi)"), sg.Input(key="-SUBS-", expand_x=True), sg.FilesBrowse("Pick…", file_types=(("SRT","*.srt"),))],
    [sg.Checkbox("Audio-only (MP3)", key="-MP3-")],
    [sg.Button("Start"), sg.Button("Open Output"), sg.Button("Exit")],
    [sg.Multiline(key="-LOG-", size=(100,20), autoscroll=True, expand_x=True, expand_y=True)]
]

win = sg.Window("DownloadBeast Pro (GUI)", layout, resizable=True)

def log(msg): win["-LOG-"].print(msg)

while True:
    ev, vals = win.read()
    if ev in (sg.WINDOW_CLOSED, "Exit"): break
    if ev == "Open Output":
        out = vals.get("-OUT-") or ""
        if out and Path(out).exists():
            try:
                import os
                os.startfile(out)  # Windows
            except Exception as e:
                log(f"Open folder failed: {e}")
        else:
            log("Output folder not set.")
    if ev == "Start":
        src  = vals.get("-SRC-","").strip()
        out  = vals.get("-OUT-","").strip() or str(Path.home() / "Videos")
        subs = [p for p in (vals.get("-SUBS-","").split(";") if vals.get("-SUBS-") else []) if p]
        make_mp3 = bool(vals.get("-MP3-"))
        if not src:
            log("Please enter a URL or choose a local file.")
            continue
        try:
            log("Starting…")
            result = run_core(source=src, out_dir=out, sub_files=subs, make_mp3=make_mp3)
            log(f"✅ Done: {result}")
        except Exception as e:
            log(f"❌ Error: {e}")

win.close()
