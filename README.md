# Beast

Beast is still a work in progress, also a massive pain in my a**!  But there's a lot of potential that none of my friends can see   I hesitate to explain it what it (hopefully) can do since that's seems to cause spontaneous narcolepsy. Its basically a toolkit and GUI with four basic functions: downloading URLs, embedding subtitles in movies, producing TTS audio, and translation. As functions they're pretty standard, so I've been working on interesting ways of combining their talents. I will most likely use this repository to avoid deleting all my work for the 3rd time :) (thanks repository!)

## New Features

### Video Downloading (DownloadBeast)
Download videos and audio from YouTube and other platforms using yt-dlp:
- Single video or playlist downloads
- Audio extraction (MP3, WAV, FLAC, etc.)
- Subtitle download and embedding
- Format selection and quality control

### Whisper Transcription
Automatic speech recognition with language detection using OpenAI's Whisper:
- Auto-detect language or specify manually
- Generate SRT subtitles with timestamps
- Multiple model sizes (tiny to large) for accuracy/speed trade-off
- Batch processing support
- Output in SRT, TXT, and JSON formats

### Integrated Workflow
Combine downloading and transcription in one command:
- Download → Transcribe → Generate Subtitles
- Supports single videos or playlists
- Automatic cleanup options
- Perfect for creating subtitles from online videos

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
# Auto-SRT and TTS wrapper
python auto_srt_all_tts_wrapper.py --input path/to/video --no-cache --rate 1.0

# Download videos
python download_beast.py https://youtube.com/watch?v=VIDEO_ID --output downloads

# Transcribe with Whisper (language detection + SRT generation)
python whisper_transcribe.py video.mp4 --model base

# Download and transcribe in one command
python download_and_transcribe.py https://youtube.com/watch?v=VIDEO_ID --model medium
```

Refer to each script for available flags and options.

## Project layout

- tts_helpers.py — low-level TTS helpers
- tts_run.py — CLI entrypoint for TTS operations
- playlist_helpers.py — helpers to build HTML playlists
- auto_srt_all_tts_wrapper.py — wrapper that runs auto-SRT and TTS end-to-end
- beast_gui.py — new PySimpleGUI-based GUI (this file)
- download_beast.py — download videos from URLs using yt-dlp
- whisper_transcribe.py — transcribe audio/video using OpenAI Whisper with language detection
- download_and_transcribe.py — integrated workflow combining download and transcription

## Contributing

- Create a branch for changes (feature/<name>) and open a pull request.
- Run tests and linters before opening a PR.

## License

This project is licensed under the MIT License — see LICENSE for details.