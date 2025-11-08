# Usage Examples for Download and Whisper Transcription

This document provides practical examples for using the new download and transcription features.

## Prerequisites

Install required dependencies:
```bash
pip install -r requirements.txt
```

You also need ffmpeg installed on your system:
- **Ubuntu/Debian**: `sudo apt install ffmpeg`
- **macOS**: `brew install ffmpeg`
- **Windows**: Install via Chocolatey (`choco install ffmpeg`) or download from ffmpeg.org

## 1. Download Videos (download_beast.py)

### Basic video download
```bash
python download_beast.py https://youtube.com/watch?v=VIDEO_ID
```

### Download to specific directory
```bash
python download_beast.py https://example.com/video --output downloads/videos
```

### Extract audio only (MP3)
```bash
python download_beast.py https://youtube.com/watch?v=VIDEO_ID --audio-only --audio-format mp3
```

### Download with subtitles
```bash
python download_beast.py https://youtube.com/watch?v=VIDEO_ID --subtitles --embed-subs
```

### Download playlist (first 5 videos)
```bash
python download_beast.py https://youtube.com/playlist?list=PLAYLIST_ID --playlist --max 5
```

## 2. Transcribe Audio/Video (whisper_transcribe.py)

### Transcribe a video and generate SRT
```bash
python whisper_transcribe.py video.mp4
```
This will create `video.srt` in the same directory.

### Transcribe with specific language
```bash
python whisper_transcribe.py audio.mp3 --language en
```

### Use larger model for better accuracy
```bash
python whisper_transcribe.py video.mkv --model medium
```

### Generate all output formats (SRT, TXT, JSON)
```bash
python whisper_transcribe.py audio.wav --format all
```

### Batch transcribe multiple files
```bash
python whisper_transcribe.py video1.mp4 video2.mp4 video3.mp4
```

### Save transcriptions to specific directory
```bash
python whisper_transcribe.py video.mp4 --output transcriptions/
```

## 3. Download and Transcribe in One Command (download_and_transcribe.py)

### Basic workflow: download and transcribe
```bash
python download_and_transcribe.py https://youtube.com/watch?v=VIDEO_ID
```
This will:
1. Download the video to `downloads/` directory
2. Transcribe it using Whisper (base model)
3. Generate SRT, TXT, and JSON files

### Download audio only and transcribe (faster)
```bash
python download_and_transcribe.py https://youtube.com/watch?v=VIDEO_ID --audio-only
```

### Use specific language and model
```bash
python download_and_transcribe.py URL --language en --model medium
```

### Process a playlist (first 3 videos)
```bash
python download_and_transcribe.py PLAYLIST_URL --playlist --max 3
```

### Clean up after transcription
```bash
python download_and_transcribe.py URL --audio-only --remove-source
```
This will download audio, transcribe it, then delete the audio file (keeping only the transcriptions).

### Custom output directory
```bash
python download_and_transcribe.py URL --output my_transcriptions/
```

## Model Selection Guide

Choose the right Whisper model based on your needs:

| Model  | VRAM    | Speed      | Accuracy | Use Case                    |
|--------|---------|------------|----------|-----------------------------|
| tiny   | ~1GB    | Very Fast  | Basic    | Quick drafts, testing       |
| base   | ~1GB    | Fast       | Good     | General use (default)       |
| small  | ~2GB    | Medium     | Better   | Higher quality needed       |
| medium | ~5GB    | Slow       | High     | Professional transcription  |
| large  | ~10GB   | Very Slow  | Best     | Critical accuracy needed    |

## Language Codes

Common language codes for `--language` option:
- `en` - English
- `es` - Spanish
- `fr` - French
- `de` - German
- `it` - Italian
- `pt` - Portuguese
- `ru` - Russian
- `ja` - Japanese
- `zh` - Chinese
- `ar` - Arabic

If not specified, Whisper will automatically detect the language.

## Real-World Workflows

### Creating subtitles for a YouTube video
```bash
# Download video and create subtitles
python download_and_transcribe.py https://youtube.com/watch?v=VIDEO_ID --model small

# The output includes:
# - Video file: downloads/Video Title.mp4
# - Subtitles: downloads/Video Title.srt
# - Text: downloads/Video Title.txt
# - JSON: downloads/Video Title.json
```

### Transcribing lecture recordings
```bash
# Process a playlist of lectures
python download_and_transcribe.py PLAYLIST_URL --playlist --audio-only --model medium --output lectures/

# This creates organized transcriptions for each lecture
```

### Quick audio extraction and transcription
```bash
# Extract audio, transcribe, remove audio file
python download_and_transcribe.py URL --audio-only --remove-source --output transcripts/
```

### Multilingual content processing
```bash
# Auto-detect language and transcribe
python download_and_transcribe.py URL --model base

# Force specific language if detection fails
python download_and_transcribe.py URL --language es --model base
```

## Troubleshooting

### "yt-dlp is not installed"
```bash
pip install yt-dlp
```

### "OpenAI Whisper is not installed"
```bash
pip install openai-whisper
```

### "ffmpeg not found"
Install ffmpeg for your operating system (see Prerequisites above).

### Slow transcription
- Use a smaller model: `--model tiny` or `--model base`
- Download audio only: `--audio-only`
- Use GPU if available (automatically detected)

### Out of memory
- Use a smaller model: `--model tiny` or `--model base`
- Close other applications
- Process files individually instead of batch

### Incorrect language detection
- Specify language explicitly: `--language en`
- Use a larger model for better detection: `--model medium`

## Tips for Best Results

1. **Use the right model**: Start with `base` and upgrade to `small` or `medium` if needed
2. **Specify language**: When you know the language, use `--language` for faster processing
3. **Audio-only for transcription**: Use `--audio-only` if you only need transcriptions
4. **Organize output**: Use `--output` to keep transcriptions organized
5. **Clean up**: Use `--remove-source` to save disk space after transcription
6. **Test first**: Try with one video before processing a large playlist

## Integration with Existing Beast Features

These new features integrate with Beast's existing functionality:

1. **TTS Integration**: Use transcribed text as input for TTS generation
2. **Subtitle Embedding**: Embed generated SRT files into videos
3. **Translation**: Translate transcribed text to other languages
4. **Playlist Management**: Create HTML playlists with transcribed content

See the main README for more information on Beast's complete feature set.
