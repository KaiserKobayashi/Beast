# Beast

Beast is still a work in progress, also a massive pain in my a**!  But there's a lot of potential that none of my friends can see   I hesitate to explain it what it (hopefully) can do since that's seems to cause spontaneous narcolepsy. Its basically a toolkit and GUI with four basic functions: downloading URLs, embedding subtitles in movies, producing TTS audio, and translation. As functions they're pretty standard, so I've been working on interesting ways of combining their talents. I will most likely use this repository to avoid deleting all my work for the 3rd time :) (thanks repository!)

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

Use the GUI to:
- **Download Tab**: Download videos from URLs (YouTube, etc.) with options for audio extraction, subtitles, and playlists
- **TTS/Auto-SRT Tab**: Pick an input video folder or SRT files and run the TTS/auto-SRT wrapper

The GUI will run the existing scripts and display live logs.

## Quick start (CLI)

### Download videos

Download videos from URLs:

```bash
# Download a video
python download_beast.py https://www.youtube.com/watch?v=VIDEO_ID

# Extract audio only
python download_beast.py https://example.com/video --audio-only --audio-format mp3

# Download with subtitles
python download_beast.py https://example.com/video --subtitles --embed-subs

# Download playlist
python download_beast.py https://www.youtube.com/playlist?list=... --playlist --max 5
```

### TTS and Auto-SRT

You can also run the existing scripts directly:

```bash
python auto_srt_all_tts_wrapper.py --input path/to/video --no-cache --rate 1.0
```

Refer to each script for available flags and options.

## Project layout

- **download_beast.py** — CLI for downloading videos from URLs using yt-dlp
- **beast_gui.py** — PySimpleGUI-based GUI with tabs for Download and TTS/Auto-SRT
- **beast_config.py** — Configuration management for GUI settings
- **tts_helpers.py** — low-level TTS helpers
- **tts_run.py** — CLI entrypoint for TTS operations
- **playlist_helpers.py** — helpers to build HTML playlists
- **auto_srt_all_tts_wrapper.py** — wrapper that runs auto-SRT and TTS end-to-end

## Contributing

- Create a branch for changes (feature/<name>) and open a pull request.
- Run tests and linters before opening a PR.

## License

This project is licensed under the MIT License — see LICENSE for details.