# Beast Architecture & Integration Guide

## Overview

Beast is a modular audio/video processing toolkit with multiple independent modules that can be combined in creative ways. This document describes how all modules work together and provides integration patterns.

## Module Architecture

### Core Modules Map

```
Beast Architecture
│
├── Audio Enhancement Layer (NEW)
│   ├── audio_separation.py      - Source separation (vocals, drums, bass, other)
│   ├── audio_cleanup.py          - Noise reduction & enhancement
│   ├── audio_mixing.py           - Mix/edit/reconstruct audio
│   └── audio_workflow.py         - Integrated preprocessing pipeline
│
├── Transcription & Translation Layer
│   ├── auto_srt_all_tts_wrapper.py - Auto-subtitle generation workflow
│   ├── subtitle_editor.py        - Post-editing & enhancement (NEW)
│   └── [External: Whisper]       - Speech-to-text transcription
│
├── Text-to-Speech Layer
│   ├── tts_helpers.py            - Low-level TTS synthesis
│   ├── tts_run.py                - CLI for TTS operations
│   └── [External: edge-tts]      - Microsoft Edge TTS engine
│
├── Presentation Layer
│   ├── playlist_helpers.py       - HTML/M3U playlist generation
│   └── beast_gui.py              - GUI interface
│
└── Configuration Layer
    └── beast_config.py           - Persistent settings
```

## Integration Points

### 1. Audio Enhancement → Transcription Pipeline

**Flow:** Raw Audio → Source Separation → Clean Vocals → Whisper → Enhanced Subtitles

```python
# Workflow integration
audio_workflow.py (orchestrates):
  └─> audio_separation.py (separate sources)
      └─> Extract vocals
          └─> Whisper (transcribe)
              └─> subtitle_editor.py (enhance)
```

**API Integration:**
```python
# In auto_srt_all_tts_wrapper.py (future enhancement)
from audio_workflow import prepare_for_transcription
from subtitle_editor import SubtitleEditor

# Preprocess audio
separated = prepare_for_transcription(audio_path, temp_dir)
vocals_path = separated['vocals']

# Transcribe clean vocals (existing Whisper call)
subtitles = run_whisper(vocals_path)

# Post-process subtitles
editor = SubtitleEditor.from_file(subtitles)
editor.auto_enhance()
editor.save(final_srt_path)
```

### 2. Audio Cleanup → Video Processing

**Flow:** Noisy Video → Extract Audio → Cleanup → Replace in Video

```python
# In video processing (future)
from audio_cleanup import cleanup_video_audio

# One-line video cleanup
clean_video = cleanup_video_audio(
    input_video="raw.mp4",
    output_video="clean.mp4",
    normalize_audio=True,
    simple_noise_reduction=True
)
```

### 3. Source Separation → TTS Enhancement

**Flow:** Generate TTS → Separate → Mix with Background Music

```python
# In tts_run.py (future enhancement)
from audio_mixing import mix_sources

# Generate TTS for subtitles (existing)
tts_audio = synthesize_stitched(segments, output_path)

# Add background music
mixed = mix_sources(
    sources={
        'narration': tts_audio,
        'music': background_music_path
    },
    volumes={'narration': 0, 'music': -10},  # Music at -10dB
    output_path='final_with_music.wav'
)
```

### 4. Audio Mixing → Playlist Generation

**Flow:** Separated Sources → Multiple Versions → Playlist

```python
# Create multiple versions for playlist
from audio_mixing import create_instrumental, create_acapella
from playlist_helpers import create_multilingual_playlist

# Generate versions
instrumental = create_instrumental(separated_dir, "inst.wav")
acapella = create_acapella(separated_dir, "vocals.wav")

# Add to playlist with originals
playlist_items = [
    {'path': 'original.mp3', 'title': 'Original'},
    {'path': 'inst.wav', 'title': 'Instrumental'},
    {'path': 'vocals.wav', 'title': 'Acapella'}
]
```

## Creative Integration Patterns

### Pattern 1: Clean Transcription for Translation

**Problem:** Translation quality depends on transcription accuracy  
**Solution:** Preprocess audio → Clean transcription → Better translation

```bash
# Step 1: Get clean transcription
python audio_workflow.py transcribe --input video.mp4 --output temp/

# Step 2: Enhance subtitles
python subtitle_editor.py enhance --input temp/transcription/*.srt --output clean.srt

# Step 3: Use clean.srt for translation (existing workflow)
# Translation will be more accurate because source text is better
```

### Pattern 2: Karaoke Video Creation

**Problem:** Need instrumental track + lyrics display  
**Solution:** Source separation → GUI playlist

```bash
# Step 1: Separate audio
python audio_separation.py --input song.mp3 --output separated/

# Step 2: Create instrumental
python audio_mixing.py instrumental --input separated/ --output karaoke.wav

# Step 3: Use existing GUI/playlist for lyrics display
python tts_run.py --srt lyrics.srt --output-format karaoke.html
```

### Pattern 3: Multi-Language Audio Books with Music

**Problem:** TTS sounds robotic, want background music  
**Solution:** TTS → Audio mixing → Subtle background

```bash
# Step 1: Generate TTS (existing)
python tts_run.py --srt book.srt --output tts/

# Step 2: Add ambient background
python audio_mixing.py add \
  --input tts/ \
  --new ambient_music.wav \
  --name background \
  --volume -15 \
  --output audiobook_with_music.wav
```

### Pattern 4: Podcast Post-Production

**Problem:** Interview has noise + needs transcription  
**Solution:** Cleanup → Transcribe → Edit subtitles

```bash
# Step 1: Clean video audio
python audio_cleanup.py video \
  --input raw_interview.mp4 \
  --output clean_interview.mp4 \
  --normalize --simple-denoise

# Step 2: Transcribe clean audio
python audio_workflow.py transcribe \
  --input clean_interview.mp4 \
  --output results/

# Step 3: Enhance subtitles
python subtitle_editor.py enhance \
  --input results/transcription/*.srt \
  --output final.srt
```

### Pattern 5: Voice Replacement in Videos

**Problem:** Want to dub video with different voice  
**Solution:** Separate → Replace vocals → Remix

```bash
# Step 1: Separate video audio
python audio_separation.py --input video.mp4 --output separated/

# Step 2: Generate new TTS vocals
python tts_run.py --srt script.srt --output new_vocals.wav

# Step 3: Replace vocals
python audio_mixing.py replace \
  --input separated/ \
  --source vocals \
  --replacement new_vocals.wav \
  --output new_audio.wav

# Step 4: Replace audio in video (ffmpeg)
ffmpeg -i video.mp4 -i new_audio.wav -c:v copy -map 0:v:0 -map 1:a:0 dubbed_video.mp4
```

## Module Communication Protocol

### Data Exchange Format

All modules should support standard formats:

**Audio Formats:**
- Primary: WAV (lossless, best quality)
- Secondary: MP3, FLAC, OGG
- Video: MP4, MKV, AVI (extract audio as needed)

**Subtitle Formats:**
- Primary: SRT (most compatible)
- Secondary: VTT (web), JSON (data exchange)

**Metadata Format (JSON):**
```json
{
  "source_file": "original.mp3",
  "processing_steps": [
    {
      "step": "separation",
      "module": "audio_separation",
      "timestamp": "2024-11-08T01:00:00Z",
      "outputs": {
        "vocals": "separated/vocals.wav",
        "drums": "separated/drums.wav",
        "bass": "separated/bass.wav",
        "other": "separated/other.wav"
      }
    },
    {
      "step": "transcription",
      "module": "audio_workflow",
      "timestamp": "2024-11-08T01:05:00Z",
      "outputs": {
        "srt": "transcription/output.srt",
        "vtt": "transcription/output.vtt"
      }
    }
  ]
}
```

### Shared Utilities

Common functions should be in shared modules:

```python
# beast_utils.py (future)
class AudioFile:
    """Standard audio file wrapper used by all modules"""
    def __init__(self, path):
        self.path = path
    
    def get_duration(self):
        """Get duration in seconds"""
        pass
    
    def get_format(self):
        """Get file format"""
        pass
    
    def convert_to(self, format, output_path):
        """Convert to another format"""
        pass

class WorkflowContext:
    """Shared context across modules"""
    def __init__(self):
        self.temp_dir = None
        self.metadata = {}
    
    def add_output(self, step_name, output_files):
        """Track outputs from each step"""
        pass
    
    def get_output(self, step_name):
        """Retrieve outputs from previous steps"""
        pass
```

## GUI Integration Plan

The GUI should expose all new functionality:

```python
# In beast_gui.py (future enhancement)

# Add new tab for Audio Enhancement
audio_tab = [
    [sg.Text("Audio Enhancement & Source Separation")],
    [sg.Radio("Clean Audio (Noise Reduction)", "AUDIO_MODE", key="MODE_CLEAN")],
    [sg.Radio("Separate Sources (Vocals, Instruments)", "AUDIO_MODE", key="MODE_SEPARATE")],
    [sg.Radio("Transcribe with Preprocessing", "AUDIO_MODE", key="MODE_TRANSCRIBE")],
    [sg.Checkbox("Auto-enhance subtitles", key="ENHANCE_SUBS")],
    [sg.Button("Process Audio")]
]

# Integration logic
if values['MODE_TRANSCRIBE']:
    # Use audio_workflow
    from audio_workflow import transcription_workflow
    from subtitle_editor import SubtitleEditor
    
    results = transcription_workflow(input_file, output_dir)
    
    if values['ENHANCE_SUBS'] and 'transcription_srt' in results:
        editor = SubtitleEditor.from_file(results['transcription_srt'])
        editor.auto_enhance()
        editor.save(results['transcription_srt'])
```

## Configuration Integration

All modules should respect shared configuration:

```python
# In beast_config.py (enhancement)
default_config = {
    # Existing settings
    "theme": "SystemDefault",
    "voices": ["default"],
    
    # New audio enhancement settings
    "audio": {
        "separation_model": "htdemucs",  # Default separation model
        "device": "cpu",  # or "cuda" for GPU
        "noise_reduction": "simple",  # or "advanced"
        "normalize": True,
        "whisper_model": "base",  # Default Whisper model
        "auto_enhance_subtitles": True
    }
}
```

## Future Integration Opportunities

### 1. Real-time Processing Pipeline
```
Video → Audio Extract → Cleanup → Separate → Transcribe → TTS → Mix → Final Video
```

### 2. Batch Processing Dashboard
- Process multiple files with different profiles
- Track progress across all modules
- Generate reports with statistics

### 3. Plugin Architecture
- Allow third-party modules to hook into workflow
- Standard interfaces for audio processing, transcription, etc.

### 4. Cloud Integration
- Upload to cloud for GPU processing
- Download results
- Share processed files

### 5. Quality Metrics
- Audio quality scores (SNR, clarity)
- Transcription accuracy (WER - Word Error Rate)
- Subtitle readability scores

## Best Practices for Module Development

### 1. Use Standard Interfaces
```python
def process(input_path, output_path, **options):
    """
    Standard signature for all processing modules.
    
    Args:
        input_path: Path to input file
        output_path: Path for output file
        **options: Module-specific options
    
    Returns:
        Dict with output paths and metadata
    """
    pass
```

### 2. Support Both CLI and API
```python
# CLI entry point
def main():
    args = parse_args()
    result = process(args.input, args.output, **args.options)
    return 0 if result else 1

# API for integration
def process_audio(input_path, output_path, **options):
    """Use directly from other modules"""
    return do_processing(input_path, output_path, **options)

if __name__ == "__main__":
    sys.exit(main())
```

### 3. Return Structured Results
```python
# Good: Structured return value
return {
    'success': True,
    'outputs': {
        'main': output_path,
        'metadata': metadata_path
    },
    'stats': {
        'duration': 120.5,
        'quality_score': 0.95
    }
}

# Bad: Just return True/False
return True
```

### 4. Support Progress Callbacks
```python
def process(input_path, output_path, progress_callback=None):
    for i, step in enumerate(steps):
        process_step(step)
        if progress_callback:
            progress_callback(i / len(steps))
```

### 5. Handle Errors Gracefully
```python
try:
    result = risky_operation()
except SpecificError as e:
    logger.error(f"Failed: {e}")
    return {'success': False, 'error': str(e)}
```

## Cross-Module Testing

Test integration between modules:

```python
# tests/test_integration.py
def test_transcription_workflow():
    # Test: audio_separation → audio_workflow → subtitle_editor
    
    # Step 1: Separate
    separated = audio_separation.separate_audio(test_audio, temp_dir)
    assert 'vocals' in separated
    
    # Step 2: Transcribe (mock Whisper)
    srt = mock_whisper_transcribe(separated['vocals'])
    
    # Step 3: Enhance
    editor = SubtitleEditor.from_file(srt)
    editor.auto_enhance()
    
    # Verify end-to-end
    assert editor.subtitles  # Has subtitles
    assert all(s.duration() > 0 for s in editor.subtitles)  # Valid timing
```

## Documentation Standards

Each module should document integration points:

```python
"""
module_name.py

Integration Points:
- INPUT: Accepts WAV/MP3 audio files
- OUTPUT: Produces separated WAV files in output_dir/
- USED BY: audio_workflow.py, beast_gui.py
- USES: torch, demucs (external), pydub (internal)
- CONFIG: Respects beast_config.audio.separation_model

Example Integration:
    from audio_separation import separate_audio
    
    separated = separate_audio(
        input_path='song.mp3',
        output_dir='output/',
        model_name=config['audio']['separation_model']
    )
    
    vocals_path = separated['vocals']
    # Use vocals_path with other modules...
"""
```

## Summary

All Beast modules are designed to work together through:

1. **Standard file formats** (WAV, SRT, JSON)
2. **Shared configuration** (beast_config.py)
3. **Composable APIs** (can call from other modules)
4. **Consistent CLI** (similar argument patterns)
5. **Clear data flow** (documented input/output)

This allows developers to:
- Build new features that leverage existing modules
- Create complex workflows by chaining modules
- Integrate new modules easily
- Maintain consistency across the codebase

The goal is to enable **creative combinations** where 1+1+1 > 3!
