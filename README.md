# Beast

Beast is still a work in progress, also a massive pain in my a**!  But there's a lot of potential that none of my friends can see   I hesitate to explain it what it (hopefully) can do since that's seems to cause spontaneous narcolepsy. Its basically a toolkit and GUI with functions for downloading URLs, embedding subtitles in movies, producing TTS audio, translation, **and now audio source separation with noise reduction for dramatically improved transcription accuracy!**  As functions they're pretty standard, so I've working on interesting ways of combining their talents. I will most likely use this repository to avoid deleting all my work for the 3rd time :) (thanks repository!)

## ✨ New Features: Audio Source Separation & Enhancement

**Problem**: When Whisper transcribes audio with background music, noise, or multiple voices, the transcriptions are inaccurate and incomplete.

**Solution**: Beast can now separate audio into isolated sources (vocals, instruments, drums, bass) and clean up unwanted noise, resulting in **dramatically more accurate subtitles and translations** across all app functions!

### Key Capabilities:
- 🎵 **Audio Source Separation**: Isolate vocals, drums, bass, and other instruments from mixed audio
- 🧹 **Noise Reduction**: Remove background noise, clicks, pops, hums, and hiss
- 🎤 **Clean Transcription**: Extract clean vocals for Whisper to transcribe with much better accuracy
- 🔧 **Audio Editing**: Individual sources can be edited, replaced, or remixed
- 🎬 **Video Support**: Works with both audio files and video files
- ✏️ **Subtitle Post-Editing**: Enhance Whisper-generated subtitles with automatic fixes

## Quick start (GUI)

1. Ensure you have Python 3.8+ installed.
2. Install the runtime dependencies:

```bash
python -m pip install -r requirements.txt
```

Note: For audio separation features, you'll also need ffmpeg installed:
- Ubuntu/Debian: `sudo apt-get install ffmpeg`
- macOS: `brew install ffmpeg`
- Windows: Download from https://ffmpeg.org/

3. Run the GUI:

```bash
python beast_gui.py
```

Use the GUI to pick an input video folder or SRT files and run the TTS/auto-SRT wrapper. The GUI will run the existing scripts and display live logs.

## Quick start (CLI)

You can also run the existing scripts directly:

### Original TTS/SRT Workflow:
```bash
python auto_srt_all_tts_wrapper.py --input path/to/video --no-cache --rate 1.0
```

### NEW: Audio Source Separation & Clean Transcription Workflow:

**Step 1: Separate audio sources and transcribe with Whisper**
```bash
# Full workflow: separate audio, extract clean vocals, transcribe with Whisper
python audio_workflow.py transcribe --input podcast.mp3 --output results/ --whisper-model base

# Or just prepare audio for manual transcription
python audio_workflow.py prepare --input audio.mp3 --output separated/
```

**Step 2: Post-edit and enhance the subtitles**
```bash
# Auto-enhance subtitles (fix timing, reading speed, etc.)
python subtitle_editor.py enhance --input results/transcription/*.srt --output final.srt
```

### Additional Audio Tools:

**Clean up noisy audio/video:**
```bash
# Clean up audio file
python audio_cleanup.py audio --input noisy.wav --output clean.wav --normalize --simple-denoise

# Clean up video audio
python audio_cleanup.py video --input movie.mp4 --output clean_movie.mp4 --normalize --simple-denoise
```

**Mix and edit separated audio:**
```bash
# Mix separated sources back together with custom volumes
python audio_mixing.py mix --input separated/song/ --output remixed.wav --volumes "vocals:+3,drums:-2"

# Create instrumental (remove vocals)
python audio_mixing.py instrumental --input separated/song/ --output instrumental.wav

# Replace vocals with new recording
python audio_mixing.py replace --input separated/song/ --source vocals --replacement new_vocals.wav --output new_mix.wav
```

Refer to each script with `--help` for all available flags and options.

## Project layout

### Core Modules:
- tts_helpers.py — low-level TTS helpers
- tts_run.py — CLI entrypoint for TTS operations
- playlist_helpers.py — helpers to build HTML playlists
- auto_srt_all_tts_wrapper.py — wrapper that runs auto-SRT and TTS end-to-end
- beast_gui.py — PySimpleGUI-based GUI

### NEW: Audio Enhancement Modules:
- **audio_separation.py** — Separate audio into sources (vocals, drums, bass, instruments)
- **audio_cleanup.py** — Remove noise and unwanted sounds from audio/video
- **audio_mixing.py** — Mix, edit, and reconstruct separated audio sources
- **audio_workflow.py** — Integrated workflow for separation + Whisper transcription
- **subtitle_editor.py** — Post-editing and enhancement of Whisper-generated subtitles

## Use Cases

### 1. Improved Transcription Accuracy
Problem: Whisper struggles with audio that has background music or multiple speakers.
```bash
python audio_workflow.py transcribe --input podcast.mp3 --output results/
python subtitle_editor.py enhance --input results/transcription/*.srt --output final.srt
```

### 2. Create Karaoke/Instrumental Tracks
```bash
python audio_separation.py --input song.mp3 --output separated/
python audio_mixing.py instrumental --input separated/ --output instrumental.wav
```

### 3. Clean Up Video Audio
```bash
python audio_cleanup.py video --input interview.mp4 --output clean_interview.mp4 --normalize --simple-denoise
```

### 4. Replace/Edit Audio in Mix
```bash
python audio_separation.py --input song.mp3 --output separated/
# Edit individual tracks with your DAW...
python audio_mixing.py mix --input separated/ --output new_mix.wav --volumes "vocals:+2,drums:-1"
```

## Contributing

- Create a branch for changes (feature/<name>) and open a pull request.
- Run tests and linters before opening a PR.

## License

This project is licensed under the MIT License — see LICENSE for details.