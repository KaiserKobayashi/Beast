#!/usr/bin/env python3
"""
audio_cleanup.py

Audio noise reduction and cleanup module for removing unwanted noises and improving
audio quality. This module provides:

- Background noise reduction
- Click/pop removal
- Hum/hiss removal
- Silence trimming
- Volume normalization
- Audio enhancement filters

Works with both standalone audio files and audio extracted from videos.
"""

import argparse
import sys
import subprocess
from pathlib import Path
from typing import Optional, Dict, Tuple

try:
    from pydub import AudioSegment
    from pydub.effects import normalize, compress_dynamic_range, low_pass_filter, high_pass_filter
    from pydub.silence import detect_nonsilent
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    AudioSegment = None

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

try:
    import noisereduce as nr
    NOISEREDUCE_AVAILABLE = True
except ImportError:
    NOISEREDUCE_AVAILABLE = False
    nr = None


def check_dependencies(require_noisereduce: bool = False):
    """Check if required dependencies are installed."""
    if not PYDUB_AVAILABLE:
        print("ERROR: pydub is not installed.")
        print("Please install it with: pip install pydub")
        return False
    
    if require_noisereduce and not NOISEREDUCE_AVAILABLE:
        print("WARNING: noisereduce is not installed.")
        print("Advanced noise reduction will not be available.")
        print("Install with: pip install noisereduce")
        print("\nBasic cleanup operations will still work.")
        return True
    
    if require_noisereduce and not NUMPY_AVAILABLE:
        print("ERROR: numpy is not installed (required for noise reduction).")
        print("Please install it with: pip install numpy")
        return False
    
    return True


def extract_audio_from_video(video_path: str, output_audio: str, format: str = "wav") -> Path:
    """
    Extract audio from video file using ffmpeg.
    
    Args:
        video_path: Path to video file
        output_audio: Path for output audio file
        format: Audio format (wav, mp3, etc.)
        
    Returns:
        Path to extracted audio file
    """
    video_path = Path(video_path)
    output_audio = Path(output_audio)
    
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    output_audio.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Extracting audio from video: {video_path.name}")
    
    # Use ffmpeg to extract audio
    cmd = [
        "ffmpeg",
        "-i", str(video_path),
        "-vn",  # No video
        "-acodec", "pcm_s16le" if format == "wav" else "libmp3lame",
        "-ar", "44100",  # Sample rate
        "-ac", "2",  # Stereo
        "-y",  # Overwrite
        str(output_audio)
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✓ Audio extracted to: {output_audio}")
        return output_audio
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to extract audio: {e.stderr.decode()}")
    except FileNotFoundError:
        raise RuntimeError("ffmpeg not found. Please install ffmpeg:\n"
                         "  Ubuntu/Debian: sudo apt-get install ffmpeg\n"
                         "  macOS: brew install ffmpeg\n"
                         "  Windows: Download from https://ffmpeg.org/")


def replace_video_audio(video_path: str, new_audio: str, output_video: str) -> Path:
    """
    Replace audio in a video file with cleaned audio.
    
    Args:
        video_path: Path to original video
        new_audio: Path to cleaned audio
        output_video: Path for output video
        
    Returns:
        Path to output video
    """
    video_path = Path(video_path)
    new_audio = Path(new_audio)
    output_video = Path(output_video)
    
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")
    if not new_audio.exists():
        raise FileNotFoundError(f"Audio file not found: {new_audio}")
    
    output_video.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Replacing audio in video: {video_path.name}")
    
    # Use ffmpeg to replace audio
    cmd = [
        "ffmpeg",
        "-i", str(video_path),
        "-i", str(new_audio),
        "-c:v", "copy",  # Copy video without re-encoding
        "-map", "0:v:0",  # Use video from first input
        "-map", "1:a:0",  # Use audio from second input
        "-shortest",  # Match shortest stream
        "-y",  # Overwrite
        str(output_video)
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✓ Video with cleaned audio saved to: {output_video}")
        return output_video
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to replace audio: {e.stderr.decode()}")


def reduce_noise_simple(
    audio: AudioSegment,
    high_pass_freq: int = 80,
    low_pass_freq: int = 15000,
) -> AudioSegment:
    """
    Apply simple noise reduction using frequency filters.
    
    Args:
        audio: Input audio segment
        high_pass_freq: High-pass filter frequency (remove low rumble)
        low_pass_freq: Low-pass filter frequency (remove high hiss)
        
    Returns:
        Filtered audio segment
    """
    print(f"Applying frequency filters (high-pass: {high_pass_freq}Hz, low-pass: {low_pass_freq}Hz)")
    
    # Remove low-frequency rumble
    audio = high_pass_filter(audio, high_pass_freq)
    
    # Remove high-frequency hiss
    audio = low_pass_filter(audio, low_pass_freq)
    
    return audio


def reduce_noise_advanced(
    input_path: Path,
    output_path: Path,
    noise_sample_start: float = 0.0,
    noise_sample_duration: float = 1.0,
    stationary: bool = True,
) -> Path:
    """
    Apply advanced noise reduction using spectral analysis.
    
    Args:
        input_path: Path to input audio
        output_path: Path for output audio
        noise_sample_start: Start time for noise profile sample (seconds)
        noise_sample_duration: Duration of noise profile sample (seconds)
        stationary: Whether noise is stationary (constant) or non-stationary
        
    Returns:
        Path to output file
    """
    if not NOISEREDUCE_AVAILABLE or not NUMPY_AVAILABLE:
        raise RuntimeError("Advanced noise reduction requires noisereduce and numpy")
    
    print("Applying advanced noise reduction (spectral analysis)...")
    
    # Load audio
    audio = AudioSegment.from_file(str(input_path))
    
    # Convert to numpy array
    samples = np.array(audio.get_array_of_samples())
    
    # Reshape for stereo if needed
    if audio.channels == 2:
        samples = samples.reshape((-1, 2))
    
    sample_rate = audio.frame_rate
    
    # Extract noise sample for profile
    noise_start_sample = int(noise_sample_start * sample_rate)
    noise_end_sample = int((noise_sample_start + noise_sample_duration) * sample_rate)
    
    if audio.channels == 2:
        noise_sample = samples[noise_start_sample:noise_end_sample, :]
    else:
        noise_sample = samples[noise_start_sample:noise_end_sample]
    
    print(f"Using noise profile from {noise_sample_start}s to {noise_sample_start + noise_sample_duration}s")
    
    # Apply noise reduction
    reduced = nr.reduce_noise(
        y=samples,
        sr=sample_rate,
        y_noise=noise_sample,
        stationary=stationary,
        prop_decrease=1.0,
    )
    
    # Convert back to AudioSegment
    reduced_int = reduced.astype(np.int16)
    
    if audio.channels == 2:
        reduced_int = reduced_int.flatten()
    
    reduced_audio = AudioSegment(
        reduced_int.tobytes(),
        frame_rate=sample_rate,
        sample_width=audio.sample_width,
        channels=audio.channels
    )
    
    # Export
    output_path.parent.mkdir(parents=True, exist_ok=True)
    reduced_audio.export(str(output_path), format=output_path.suffix[1:] or "wav")
    
    print(f"✓ Noise-reduced audio saved to: {output_path}")
    return output_path


def remove_silence(
    audio: AudioSegment,
    min_silence_len: int = 1000,
    silence_thresh: int = -40,
    keep_silence: int = 100,
) -> AudioSegment:
    """
    Remove long silences from audio.
    
    Args:
        audio: Input audio segment
        min_silence_len: Minimum silence length to remove (ms)
        silence_thresh: Silence threshold in dBFS
        keep_silence: Amount of silence to keep at edges (ms)
        
    Returns:
        Audio with silence removed
    """
    print(f"Removing silences (threshold: {silence_thresh} dBFS, min length: {min_silence_len}ms)")
    
    # Detect non-silent chunks
    nonsilent_chunks = detect_nonsilent(
        audio,
        min_silence_len=min_silence_len,
        silence_thresh=silence_thresh,
        seek_step=10
    )
    
    if not nonsilent_chunks:
        print("WARNING: No non-silent audio detected")
        return audio
    
    # Combine non-silent chunks with some padding
    output = AudioSegment.empty()
    for start, end in nonsilent_chunks:
        start = max(0, start - keep_silence)
        end = min(len(audio), end + keep_silence)
        output += audio[start:end]
    
    original_duration = len(audio) / 1000
    new_duration = len(output) / 1000
    removed = original_duration - new_duration
    
    print(f"Removed {removed:.2f}s of silence ({removed/original_duration*100:.1f}%)")
    
    return output


def cleanup_audio(
    input_path: str,
    output_path: str,
    normalize_audio: bool = True,
    remove_silence_option: bool = False,
    simple_noise_reduction: bool = True,
    advanced_noise_reduction: bool = False,
    compress: bool = False,
    output_format: str = "wav",
) -> Path:
    """
    Clean up audio with various enhancement options.
    
    Args:
        input_path: Path to input audio
        output_path: Path for output audio
        normalize_audio: Whether to normalize volume
        remove_silence_option: Whether to remove long silences
        simple_noise_reduction: Whether to apply simple frequency filtering
        advanced_noise_reduction: Whether to apply advanced spectral noise reduction
        compress: Whether to apply dynamic range compression
        output_format: Output format
        
    Returns:
        Path to cleaned audio
    """
    if not check_dependencies(require_noisereduce=advanced_noise_reduction):
        raise RuntimeError("Required dependencies not available")
    
    input_path = Path(input_path)
    output_path = Path(output_path)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    print("="*60)
    print("AUDIO CLEANUP")
    print("="*60)
    print(f"Input: {input_path}")
    print(f"Output: {output_path}")
    print("="*60)
    
    # Load audio
    print("\nLoading audio...")
    audio = AudioSegment.from_file(str(input_path))
    print(f"Duration: {len(audio)/1000:.2f}s")
    print(f"Sample rate: {audio.frame_rate}Hz")
    print(f"Channels: {audio.channels}")
    
    # Apply advanced noise reduction first (if requested)
    if advanced_noise_reduction:
        temp_path = output_path.parent / f"temp_{output_path.name}"
        audio.export(str(temp_path), format="wav")
        reduce_noise_advanced(temp_path, temp_path)
        audio = AudioSegment.from_file(str(temp_path))
        temp_path.unlink()
    
    # Apply simple noise reduction
    if simple_noise_reduction:
        print("\nApplying simple noise reduction...")
        audio = reduce_noise_simple(audio)
    
    # Remove silence
    if remove_silence_option:
        print("\nRemoving silence...")
        audio = remove_silence(audio)
    
    # Compress dynamic range
    if compress:
        print("\nApplying dynamic range compression...")
        audio = compress_dynamic_range(audio)
    
    # Normalize volume
    if normalize_audio:
        print("\nNormalizing volume...")
        audio = normalize(audio)
    
    # Export
    print(f"\nExporting to {output_format}...")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    audio.export(str(output_path), format=output_format)
    
    print("\n" + "="*60)
    print("✓ Audio cleanup complete!")
    print(f"Output: {output_path}")
    print("="*60)
    
    return output_path


def cleanup_video_audio(
    input_video: str,
    output_video: str,
    temp_dir: Optional[str] = None,
    **cleanup_options
) -> Path:
    """
    Clean up audio in a video file.
    
    Args:
        input_video: Path to input video
        output_video: Path for output video
        temp_dir: Optional directory for temporary files
        **cleanup_options: Options to pass to cleanup_audio()
        
    Returns:
        Path to output video
    """
    input_video = Path(input_video)
    output_video = Path(output_video)
    
    if temp_dir:
        temp_dir = Path(temp_dir)
    else:
        temp_dir = output_video.parent / "temp"
    
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    print("="*60)
    print("VIDEO AUDIO CLEANUP")
    print("="*60)
    
    try:
        # Step 1: Extract audio
        print("\nStep 1: Extracting audio from video...")
        temp_audio_in = temp_dir / f"{input_video.stem}_original.wav"
        extract_audio_from_video(str(input_video), str(temp_audio_in))
        
        # Step 2: Clean up audio
        print("\nStep 2: Cleaning up audio...")
        temp_audio_out = temp_dir / f"{input_video.stem}_cleaned.wav"
        cleanup_audio(str(temp_audio_in), str(temp_audio_out), **cleanup_options)
        
        # Step 3: Replace audio in video
        print("\nStep 3: Replacing audio in video...")
        replace_video_audio(str(input_video), str(temp_audio_out), str(output_video))
        
        print("\n" + "="*60)
        print("✓ Video audio cleanup complete!")
        print(f"Output: {output_video}")
        print("="*60)
        
        return output_video
        
    finally:
        # Clean up temp files
        if temp_dir.exists():
            for f in temp_dir.glob("*"):
                try:
                    f.unlink()
                except Exception:
                    pass
            try:
                temp_dir.rmdir()
            except Exception:
                pass


def main():
    """CLI entry point for audio cleanup."""
    parser = argparse.ArgumentParser(
        prog="audio_cleanup",
        description="Remove unwanted noises and clean up audio (works with audio files and videos)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Clean up an audio file (basic)
  python audio_cleanup.py audio --input noisy.wav --output clean.wav

  # Clean up audio with all options enabled
  python audio_cleanup.py audio --input noisy.wav --output clean.wav \\
    --normalize --remove-silence --simple-denoise --compress

  # Clean up audio with advanced noise reduction
  python audio_cleanup.py audio --input noisy.wav --output clean.wav \\
    --advanced-denoise --normalize

  # Clean up a video's audio
  python audio_cleanup.py video --input movie.mp4 --output movie_clean.mp4 \\
    --normalize --simple-denoise

  # Extract and clean audio from video separately
  python audio_cleanup.py extract --input movie.mp4 --output audio.wav
  python audio_cleanup.py audio --input audio.wav --output clean.wav --normalize
        """,
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Audio cleanup command
    audio_parser = subparsers.add_parser('audio', help='Clean up audio file')
    audio_parser.add_argument('--input', required=True, help='Input audio file')
    audio_parser.add_argument('--output', required=True, help='Output audio file')
    audio_parser.add_argument('--normalize', action='store_true', help='Normalize volume')
    audio_parser.add_argument('--remove-silence', action='store_true', help='Remove long silences')
    audio_parser.add_argument('--simple-denoise', action='store_true', help='Apply simple noise reduction (frequency filters)')
    audio_parser.add_argument('--advanced-denoise', action='store_true', help='Apply advanced noise reduction (spectral analysis)')
    audio_parser.add_argument('--compress', action='store_true', help='Apply dynamic range compression')
    audio_parser.add_argument('--format', default='wav', choices=['wav', 'mp3', 'flac', 'ogg'], help='Output format')
    
    # Video cleanup command
    video_parser = subparsers.add_parser('video', help='Clean up audio in video file')
    video_parser.add_argument('--input', required=True, help='Input video file')
    video_parser.add_argument('--output', required=True, help='Output video file')
    video_parser.add_argument('--normalize', action='store_true', help='Normalize volume')
    video_parser.add_argument('--remove-silence', action='store_true', help='Remove long silences')
    video_parser.add_argument('--simple-denoise', action='store_true', help='Apply simple noise reduction')
    video_parser.add_argument('--advanced-denoise', action='store_true', help='Apply advanced noise reduction')
    video_parser.add_argument('--compress', action='store_true', help='Apply dynamic range compression')
    video_parser.add_argument('--temp-dir', help='Directory for temporary files')
    
    # Extract audio command
    extract_parser = subparsers.add_parser('extract', help='Extract audio from video')
    extract_parser.add_argument('--input', required=True, help='Input video file')
    extract_parser.add_argument('--output', required=True, help='Output audio file')
    extract_parser.add_argument('--format', default='wav', choices=['wav', 'mp3'], help='Output format')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    if not check_dependencies(require_noisereduce=getattr(args, 'advanced_denoise', False)):
        return 1
    
    try:
        if args.command == 'audio':
            cleanup_audio(
                input_path=args.input,
                output_path=args.output,
                normalize_audio=args.normalize,
                remove_silence_option=args.remove_silence,
                simple_noise_reduction=args.simple_denoise,
                advanced_noise_reduction=args.advanced_denoise,
                compress=args.compress,
                output_format=args.format,
            )
        
        elif args.command == 'video':
            cleanup_video_audio(
                input_video=args.input,
                output_video=args.output,
                temp_dir=args.temp_dir,
                normalize_audio=args.normalize,
                remove_silence_option=args.remove_silence,
                simple_noise_reduction=args.simple_denoise,
                advanced_noise_reduction=args.advanced_denoise,
                compress=args.compress,
                output_format='wav',
            )
        
        elif args.command == 'extract':
            extract_audio_from_video(
                video_path=args.input,
                output_audio=args.output,
                format=args.format,
            )
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
