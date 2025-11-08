# Beast

Beast is still a work in progress, also a massive pain in my a**!  But there's a lot of potential that none of my friends can see   I hesitate to explain it what it (hopefully) can do since that's seems to cause spontaneous narcolepsy. Its basically a toolkit and GUI with four basic functions: downloading URLs, embedding subtitles in movies, producing TTS audio, and **translation**.  As functions they're pretty standard, so I've working on interesting ways of combining their talents. I will most likely use this repository to avoid deleting all my work for the 3rd time :) (thanks repository!)

## Features

- **TTS (Text-to-Speech)**: Convert subtitle files to audio using edge-tts
- **Auto-SRT**: Automatic subtitle generation and processing
- **Translation**: Translate subtitle files between languages with caching support
- **GUI**: User-friendly interface for all operations
- **Playlist Generation**: Create M3U and HTML playlists for learning

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
- **TTS / Auto-SRT Tab**: Pick an input video folder or SRT files and run the TTS/auto-SRT wrapper
- **Translation Tab**: Translate SRT subtitle files between languages

The GUI will run the existing scripts and display live logs.

## Quick start (CLI)

### TTS/Auto-SRT

You can run the existing scripts directly:

```bash
python auto_srt_all_tts_wrapper.py --input path/to/video --no-cache --rate 1.0
```

### Translation

Translate subtitle files:

```bash
# Translate an SRT file from Spanish to English
python translation_run.py --input movie.es.srt --output movie.en.srt --source-lang es --target-lang en

# Auto-detect source language
python translation_run.py --input movie.srt --output movie.en.srt --target-lang en --source-lang auto

# Translate text directly
python translation_run.py --text "Hola mundo" --target-lang en

# List supported languages
python translation_run.py --list-languages
```

Refer to each script for available flags and options.

## Project layout

- **tts_helpers.py** — low-level TTS helpers
- **tts_run.py** — CLI entrypoint for TTS operations
- **translation_helpers.py** — translation helpers with caching support
- **translation_run.py** — CLI entrypoint for translation operations
- **playlist_helpers.py** — helpers to build HTML playlists
- **auto_srt_all_tts_wrapper.py** — wrapper that runs auto-SRT and TTS end-to-end
- **beast_gui.py** — PySimpleGUI-based GUI with tabs for TTS and Translation
- **beast_config.py** — configuration management for persistent settings

## Contributing

- Create a branch for changes (feature/<name>) and open a pull request.
- Run tests and linters before opening a PR.

## License

This project is licensed under the MIT License — see LICENSE for details.