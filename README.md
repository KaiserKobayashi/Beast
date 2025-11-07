# Beast

Beast is still a work in progress, also a massive pain in my a**!  But there's a lot of potential that none of my friends can see   I hesitate to explain it what it (hopefully) can do since that's seems to cause spontaneous narcolepsy. Its basically a toolkit and GUI with a four basic functions, downloading URLs, embedding subtitles in movies, and producing TTS audio, and translation.  as functions they're pretty standard, so I've working on interesting ways of combining their talents. I will most likely use this repository to avoid deleting all my work for the 3rd time :) (thanks repository!)

## New Features

### Voice Configuration & Multi-User Support
- **36+ Languages** with authentic regional accents (English, Spanish, French, German, Japanese, Korean, Chinese, Arabic, and many more)
- **Male and Female voices** for each language with appropriate accents
- **Multi-user profiles** - Two or more people can use the app with their own settings
- **Easy switching** between profiles, languages, and genders
- See [VOICE_CONFIG_GUIDE.md](VOICE_CONFIG_GUIDE.md) for detailed documentation

## Quick start (GUI)

1. Ensure you have Python 3.8+ installed.
2. Install the runtime dependencies:

```bash
python -m pip install -r requirements.txt
```

3. **Test your connection** (if behind a firewall):

```bash
python network_utils.py
```

If you see connection errors, see [FIREWALL_TROUBLESHOOTING.md](FIREWALL_TROUBLESHOOTING.md) for solutions.

4. Run the GUI:

```bash
python beast_gui.py
```

Use the GUI to pick an input video folder or SRT files and run the TTS/auto-SRT wrapper. The GUI will run the existing scripts and display live logs.

**Note:** Beast uses Microsoft Azure Edge TTS, which requires internet access. Click "Test Connection" in the GUI to verify connectivity.

## Quick start (CLI)

You can also run the existing scripts directly:

```bash
python auto_srt_all_tts_wrapper.py --input path/to/video --no-cache --rate 1.0
```

Refer to each script for available flags and options.

## Project layout

- tts_helpers.py — low-level TTS helpers with network error handling
- tts_run.py — CLI entrypoint for TTS operations
- playlist_helpers.py — helpers to build HTML playlists
- auto_srt_all_tts_wrapper.py — wrapper that runs auto-SRT and TTS end-to-end
- beast_gui.py — PySimpleGUI-based GUI with connectivity testing
- voice_config.py — voice library with 36+ languages
- network_utils.py — network connectivity testing and diagnostics
- **[FIREWALL_TROUBLESHOOTING.md](FIREWALL_TROUBLESHOOTING.md)** — firewall configuration help

## Contributing

- Create a branch for changes (feature/<name>) and open a pull request.
- Run tests and linters before opening a PR.

## License

This project is licensed under the MIT License — see LICENSE for details.