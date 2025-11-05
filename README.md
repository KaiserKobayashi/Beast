# Beast

Beast is a toolkit and GUI for downloading, generating subtitles, and producing TTS audio for videos. This repository includes CLI helpers (tts_helpers.py, tts_run.py, playlist_helpers.py, auto_srt_all_tts_wrapper.py) and a new lightweight PySimpleGUI-based desktop GUI to run the TTS and playlist creation workflows.

## Quick start (GUI)

1. Ensure you have Python 3.8+ installed.
2. Install the runtime dependencies:

```bash
python -m pip install -r requirements.txt
```

3. Run the GUI:

```bash
python beast_gui.py
```

Use the GUI to pick an input video folder or SRT files and run the TTS/auto-SRT wrapper. The GUI will run the existing scripts and display live logs.

## Quick start (CLI)

You can also run the existing scripts directly:

```bash
python auto_srt_all_tts_wrapper.py --input path/to/video --no-cache --rate 1.0
```

Refer to each script for available flags and options.

## Project layout

- tts_helpers.py — low-level TTS helpers
- tts_run.py — CLI entrypoint for TTS operations
- playlist_helpers.py — helpers to build HTML playlists
- auto_srt_all_tts_wrapper.py — wrapper that runs auto-SRT and TTS end-to-end
- beast_gui.py — new PySimpleGUI-based GUI (this file)

## Contributing

- Create a branch for changes (feature/<name>) and open a pull request.
- Run tests and linters before opening a PR.

## License

This project is licensed under the MIT License — see LICENSE for details.