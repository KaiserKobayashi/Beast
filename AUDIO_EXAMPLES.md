# Audio Enhancement Examples and Tutorials

This document provides practical examples for using Beast's audio enhancement features.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Basic Audio Separation](#basic-audio-separation)
3. [Improved Transcription Workflow](#improved-transcription-workflow)
4. [Audio Cleanup for Videos](#audio-cleanup-for-videos)
5. [Advanced Remixing](#advanced-remixing)
6. [Subtitle Post-Editing](#subtitle-post-editing)
7. [Complete End-to-End Workflow](#complete-end-to-end-workflow)

## Prerequisites

### Install Dependencies
```bash
# Install basic dependencies
pip install -r requirements.txt

# For Whisper transcription (recommended)
pip install openai-whisper

# Install ffmpeg (required for video support)
# Ubuntu/Debian:
sudo apt-get install ffmpeg

# macOS:
brew install ffmpeg

# Windows: Download from https://ffmpeg.org/
```

### Verify Installation
```bash
# Check Python modules
python audio_separation.py --list-models
python audio_cleanup.py --help
python audio_workflow.py --help

# Check ffmpeg
ffmpeg -version
```

## Basic Audio Separation

### Example 1: Separate a song into stems
```bash
# Separate into vocals, drums, bass, and other
python audio_separation.py --input song.mp3 --output separated/

# Output:
# separated/song_vocals.wav
# separated/song_drums.wav
# separated/song_bass.wav
# separated/song_other.wav
```

### Example 2: Use 6-stem model for more detail
```bash
# Separates into vocals, drums, bass, guitar, piano, other
python audio_separation.py --input song.mp3 --output separated/ --model htdemucs_6s
```

### Example 3: Batch processing
```bash
# Process all audio files in a folder
python audio_separation.py --input music_folder/ --output all_separated/
```

### Example 4: Use GPU for faster processing
```bash
python audio_separation.py --input song.mp3 --output separated/ --device cuda
```

## Improved Transcription Workflow

### The Problem
Whisper transcription fails or produces poor results when:
- Background music is playing
- Multiple people talking simultaneously
- Environmental noise (traffic, wind, etc.)
- Audio quality is poor

### The Solution: Preprocess Audio First

#### Method 1: Quick Workflow (Recommended)
```bash
# One command does it all: separate audio, extract vocals, run Whisper
python audio_workflow.py transcribe \
  --input podcast_with_music.mp3 \
  --output results/ \
  --whisper-model base \
  --language en

# Results:
# results/separated/     - All separated audio sources
# results/transcription/ - SRT, VTT, TXT, JSON subtitles
```

#### Method 2: Step-by-Step (More Control)
```bash
# Step 1: Separate audio sources
python audio_separation.py --input interview.mp3 --output separated/

# Step 2: Manually transcribe the clean vocals
whisper separated/interview_vocals.wav --model base --output_format all

# Step 3: Enhance the subtitles
python subtitle_editor.py enhance --input interview_vocals.srt --output final.srt
```

### Comparison: Before vs After

**Before (direct Whisper on noisy audio):**
```
1
00:00:01,000 --> 00:00:05,000
[music] today we're going to [inaudible] about...

2
00:00:05,000 --> 00:00:10,000
[music] ...is important [music]
```

**After (Whisper on clean vocals):**
```
1
00:00:01,000 --> 00:00:05,000
Today we're going to talk about audio processing.

2
00:00:05,000 --> 00:00:10,000
This is important for achieving professional results.
```

## Audio Cleanup for Videos

### Example 1: Remove background noise from interview
```bash
# Clean up video audio (removes noise, normalizes volume)
python audio_cleanup.py video \
  --input interview.mp4 \
  --output interview_clean.mp4 \
  --normalize \
  --simple-denoise

# Original video: interview.mp4 (with background hum and noise)
# Clean video: interview_clean.mp4 (crisp, clear audio)
```

### Example 2: Advanced noise reduction
```bash
# Use spectral noise reduction for best results
python audio_cleanup.py video \
  --input noisy_video.mp4 \
  --output clean_video.mp4 \
  --normalize \
  --advanced-denoise \
  --compress

# Note: Advanced noise reduction requires noisereduce package:
# pip install noisereduce
```

### Example 3: Just extract and clean audio
```bash
# Step 1: Extract audio from video
python audio_cleanup.py extract --input video.mp4 --output audio.wav

# Step 2: Clean the audio
python audio_cleanup.py audio \
  --input audio.wav \
  --output clean_audio.wav \
  --normalize \
  --simple-denoise \
  --remove-silence

# Step 3: (Optional) Replace audio in video manually with ffmpeg
```

## Advanced Remixing

### Example 1: Create instrumental (karaoke track)
```bash
# Step 1: Separate sources
python audio_separation.py --input song.mp3 --output separated/

# Step 2: Create instrumental by removing vocals
python audio_mixing.py instrumental --input separated/ --output karaoke.wav

# Result: karaoke.wav contains music without vocals
```

### Example 2: Create acapella
```bash
python audio_mixing.py acapella --input separated/ --output acapella.wav

# Result: acapella.wav contains only vocals
```

### Example 3: Custom remix with volume adjustments
```bash
# Boost vocals by 3dB, reduce drums by 2dB
python audio_mixing.py mix \
  --input separated/ \
  --output remix.wav \
  --volumes "vocals:+3,drums:-2,bass:+1"
```

### Example 4: Replace vocals with cover version
```bash
# Separate original song
python audio_separation.py --input original.mp3 --output separated/

# Record your own vocals: my_vocals.wav

# Mix your vocals with original instrumental
python audio_mixing.py replace \
  --input separated/ \
  --source vocals \
  --replacement my_vocals.wav \
  --output my_cover.wav
```

### Example 5: Add new instrument to existing song
```bash
# Add guitar recording to separated song
python audio_mixing.py add \
  --input separated/ \
  --new guitar_solo.wav \
  --name guitar \
  --volume +2 \
  --output with_guitar.wav
```

## Subtitle Post-Editing

### Example 1: Auto-enhance Whisper subtitles (Recommended)
```bash
# Apply all automatic enhancements
python subtitle_editor.py enhance \
  --input whisper_output.srt \
  --output enhanced.srt

# This will:
# - Remove empty subtitles
# - Fix overlapping timestamps
# - Merge very short subtitles
# - Split overly long subtitles
# - Adjust for comfortable reading speed
# - Display statistics
```

### Example 2: Adjust timing (sync subtitles)
```bash
# Shift all subtitles forward by 2.5 seconds
python subtitle_editor.py adjust \
  --input subtitles.srt \
  --output synced.srt \
  --offset 2.5

# Shift backward by 1 second
python subtitle_editor.py adjust \
  --input subtitles.srt \
  --output synced.srt \
  --offset -1.0
```

### Example 3: Fix reading speed
```bash
# Ensure comfortable reading speed (18 chars/second)
python subtitle_editor.py reading-speed \
  --input subtitles.srt \
  --output readable.srt \
  --max-cps 18
```

### Example 4: Convert format
```bash
# Convert SRT to WebVTT
python subtitle_editor.py convert \
  --input subtitles.srt \
  --output subtitles.vtt \
  --format vtt
```

### Example 5: Get statistics
```bash
# Analyze subtitle quality
python subtitle_editor.py stats --input subtitles.srt

# Output:
# Subtitle Statistics:
# ========================================
# Total subtitles: 150
# Total duration: 300.5s (5.0m)
# 
# Duration per subtitle:
#   Average: 2.00s
#   Range: 0.50s - 5.20s
# 
# Characters per subtitle:
#   Average: 42.3
#   Range: 5 - 85
# 
# Reading speed: 21.2 chars/sec
# ========================================
```

## Complete End-to-End Workflow

### Scenario: Transcribe a podcast with background music

```bash
# 1. Start with a podcast episode that has intro/outro music
INPUT="podcast_episode_05.mp3"

# 2. Run the complete audio workflow
python audio_workflow.py transcribe \
  --input "$INPUT" \
  --output results/ \
  --whisper-model medium \
  --language en

# 3. Enhance the generated subtitles
python subtitle_editor.py enhance \
  --input results/transcription/*.srt \
  --output final_subtitles.srt

# 4. Check the statistics
python subtitle_editor.py stats --input final_subtitles.srt

# 5. (Optional) Create instrumental version for music-free playback
python audio_mixing.py instrumental \
  --input results/separated/ \
  --output podcast_instrumental.wav
```

### Scenario: Clean up and transcribe a noisy interview video

```bash
INPUT_VIDEO="interview_raw.mp4"

# 1. Clean up video audio
python audio_cleanup.py video \
  --input "$INPUT_VIDEO" \
  --output interview_clean.mp4 \
  --normalize \
  --simple-denoise

# 2. Extract audio from cleaned video
python audio_cleanup.py extract \
  --input interview_clean.mp4 \
  --output interview_audio.wav

# 3. Transcribe with Whisper workflow
python audio_workflow.py transcribe \
  --input interview_audio.wav \
  --output transcription/ \
  --whisper-model base

# 4. Enhance subtitles
python subtitle_editor.py enhance \
  --input transcription/transcription/*.srt \
  --output interview_final.srt

# Result: Clean video with accurate subtitles!
```

## Tips and Best Practices

### For Best Transcription Results:
1. **Always preprocess audio first** - Separate sources or clean noise before Whisper
2. **Choose appropriate Whisper model** - `tiny/base` for speed, `medium/large` for accuracy
3. **Post-edit subtitles** - Use subtitle_editor.py to fix timing and formatting issues
4. **Use GPU if available** - Add `--device cuda` for 10x+ speed improvement

### For Audio Quality:
1. **Use WAV format internally** - Better quality than MP3 for intermediate files
2. **Normalize audio** - Always use `--normalize` for consistent volume
3. **Use advanced denoising sparingly** - Can sometimes remove desired sounds
4. **Test with small files first** - Audio processing is resource-intensive

### For Remixing:
1. **Start with highest quality sources** - Use lossless audio when possible
2. **Adjust volumes carefully** - Small changes (±3dB) make big differences
3. **Check for clipping** - Normalization helps prevent distortion
4. **Export to WAV first** - Convert to MP3/other formats as final step

## Troubleshooting

### "Demucs dependencies not available"
```bash
pip install demucs torch torchaudio
```

### "ffmpeg not found"
Install ffmpeg for your system (see Prerequisites section)

### "CUDA out of memory" when using GPU
```bash
# Use CPU instead
python audio_separation.py --input file.mp3 --output separated/ --device cpu
```

### Whisper is slow
```bash
# Use smaller model
python audio_workflow.py transcribe --input audio.mp3 --output results/ --whisper-model tiny

# Or use GPU
python audio_workflow.py transcribe --input audio.mp3 --output results/ --device cuda
```

### Subtitles have poor timing
```bash
# Auto-enhance will fix most issues
python subtitle_editor.py enhance --input bad.srt --output good.srt

# Or manually adjust
python subtitle_editor.py adjust --input bad.srt --output good.srt --offset 1.5
```

## Getting Help

For any issues or questions:
1. Check script help: `python <script>.py --help`
2. Review error messages carefully
3. Open an issue on GitHub with:
   - Command you ran
   - Error message
   - System info (OS, Python version)

## What's Next?

These tools are building blocks - combine them creatively for your specific needs!

Ideas:
- Batch transcribe multiple videos with clean audio
- Create karaoke tracks from any song
- Build a podcast processing pipeline
- Clean up and subtitle educational videos
- Create remixes and covers
