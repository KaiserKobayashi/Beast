#!/usr/bin/env python3
"""
whisper_transcribe.py

Language detection and transcription using OpenAI Whisper.
Generates SRT subtitles from audio/video files.
"""
import argparse
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
import warnings

try:
    import whisper
except ImportError:
    whisper = None


def format_timestamp(seconds: float) -> str:
    """
    Format seconds to SRT timestamp format (HH:MM:SS,mmm).
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted timestamp string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def write_srt(segments: List[Dict[str, Any]], output_path: str) -> None:
    """
    Write transcription segments to SRT subtitle file.
    
    Args:
        segments: List of segment dictionaries with 'start', 'end', and 'text'
        output_path: Path to output SRT file
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, segment in enumerate(segments, start=1):
            start_time = format_timestamp(segment['start'])
            end_time = format_timestamp(segment['end'])
            text = segment['text'].strip()
            
            f.write(f"{i}\n")
            f.write(f"{start_time} --> {end_time}\n")
            f.write(f"{text}\n\n")


def transcribe_audio(
    audio_path: str,
    model_size: str = "base",
    language: Optional[str] = None,
    output_dir: Optional[str] = None,
    output_format: str = "srt",
    verbose: bool = True,
    device: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Transcribe audio/video file using Whisper.
    
    Args:
        audio_path: Path to audio or video file
        model_size: Whisper model size (tiny, base, small, medium, large)
        language: Language code (e.g., 'en', 'es', 'fr'). Auto-detected if None
        output_dir: Directory to save output files. Uses input directory if None
        output_format: Output format ('srt', 'txt', 'json')
        verbose: Show progress output
        device: Device to use ('cpu', 'cuda'). Auto-detected if None
        
    Returns:
        Dictionary with transcription results or None on error
    """
    if whisper is None:
        raise RuntimeError(
            "OpenAI Whisper is not installed. Install with: pip install openai-whisper")
    
    if not os.path.exists(audio_path):
        print(f"Error: File not found: {audio_path}", file=sys.stderr)
        return None
    
    # Suppress FP16 warning if on CPU
    if device == "cpu" or (device is None and not whisper.available_models()):
        warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")
    
    try:
        if verbose:
            print(f"Loading Whisper model: {model_size}")
        
        model = whisper.load_model(model_size, device=device)
        
        if verbose:
            print(f"Transcribing: {audio_path}")
            if language:
                print(f"Language: {language}")
            else:
                print("Detecting language...")
        
        # Transcribe with Whisper
        result = model.transcribe(
            audio_path,
            language=language,
            verbose=verbose
        )
        
        detected_language = result.get('language', 'unknown')
        if verbose:
            print(f"\nDetected language: {detected_language}")
            print(f"Transcription completed!")
        
        # Determine output path
        audio_path_obj = Path(audio_path)
        if output_dir:
            output_dir_path = Path(output_dir)
            output_dir_path.mkdir(parents=True, exist_ok=True)
            base_name = audio_path_obj.stem
        else:
            output_dir_path = audio_path_obj.parent
            base_name = audio_path_obj.stem
        
        # Write output files
        if output_format in ['srt', 'all']:
            srt_path = output_dir_path / f"{base_name}.srt"
            write_srt(result['segments'], str(srt_path))
            if verbose:
                print(f"SRT saved to: {srt_path}")
        
        if output_format in ['txt', 'all']:
            txt_path = output_dir_path / f"{base_name}.txt"
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(result['text'])
            if verbose:
                print(f"Text saved to: {txt_path}")
        
        if output_format in ['json', 'all']:
            import json
            json_path = output_dir_path / f"{base_name}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            if verbose:
                print(f"JSON saved to: {json_path}")
        
        return result
        
    except Exception as e:
        print(f"Error transcribing audio: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return None


def batch_transcribe(
    input_paths: List[str],
    model_size: str = "base",
    language: Optional[str] = None,
    output_dir: Optional[str] = None,
    output_format: str = "srt",
    verbose: bool = True
) -> List[Dict[str, Any]]:
    """
    Transcribe multiple audio/video files.
    
    Args:
        input_paths: List of paths to audio/video files
        model_size: Whisper model size
        language: Language code (auto-detected if None)
        output_dir: Directory to save output files
        output_format: Output format
        verbose: Show progress output
        
    Returns:
        List of transcription results
    """
    results = []
    
    for i, path in enumerate(input_paths, start=1):
        if verbose:
            print(f"\n=== Processing {i}/{len(input_paths)}: {path} ===")
        
        result = transcribe_audio(
            path,
            model_size=model_size,
            language=language,
            output_dir=output_dir,
            output_format=output_format,
            verbose=verbose
        )
        
        if result:
            results.append(result)
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Transcribe audio/video using OpenAI Whisper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Transcribe a video and generate SRT
  python whisper_transcribe.py video.mp4

  # Transcribe with specific language
  python whisper_transcribe.py audio.mp3 --language en

  # Use larger model for better accuracy
  python whisper_transcribe.py video.mkv --model medium

  # Generate all output formats
  python whisper_transcribe.py audio.wav --format all

  # Batch transcribe multiple files
  python whisper_transcribe.py video1.mp4 video2.mp4 video3.mp4

Model sizes (accuracy vs speed):
  - tiny: Fastest, least accurate (~1GB VRAM)
  - base: Good balance (~1GB VRAM) [default]
  - small: Better accuracy (~2GB VRAM)
  - medium: High accuracy (~5GB VRAM)
  - large: Best accuracy (~10GB VRAM)

Supported languages: Auto-detected or specify code (en, es, fr, de, it, etc.)
        """
    )
    
    parser.add_argument('input', nargs='+',
                        help='Audio or video file(s) to transcribe')
    parser.add_argument('--model', '-m', default='base',
                        choices=['tiny', 'base', 'small', 'medium', 'large'],
                        help='Whisper model size (default: base)')
    parser.add_argument('--language', '-l',
                        help='Language code (e.g., en, es, fr). Auto-detected if not specified')
    parser.add_argument('--output', '-o',
                        help='Output directory for transcriptions')
    parser.add_argument('--format', '-f', default='srt',
                        choices=['srt', 'txt', 'json', 'all'],
                        help='Output format (default: srt)')
    parser.add_argument('--device', choices=['cpu', 'cuda'],
                        help='Device to use (default: auto-detect)')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Suppress progress output')
    
    args = parser.parse_args()
    
    if whisper is None:
        print("Error: OpenAI Whisper is not installed.", file=sys.stderr)
        print("Install it with: pip install openai-whisper", file=sys.stderr)
        print("\nNote: You also need ffmpeg installed:", file=sys.stderr)
        print("  Ubuntu/Debian: sudo apt install ffmpeg", file=sys.stderr)
        print("  macOS: brew install ffmpeg", file=sys.stderr)
        print("  Windows: Install via Chocolatey or download from ffmpeg.org", file=sys.stderr)
        sys.exit(1)
    
    verbose = not args.quiet
    
    # Single or batch transcription
    if len(args.input) == 1:
        result = transcribe_audio(
            args.input[0],
            model_size=args.model,
            language=args.language,
            output_dir=args.output,
            output_format=args.format,
            verbose=verbose,
            device=args.device
        )
        if not result:
            sys.exit(1)
    else:
        results = batch_transcribe(
            args.input,
            model_size=args.model,
            language=args.language,
            output_dir=args.output,
            output_format=args.format,
            verbose=verbose
        )
        if verbose:
            print(f"\n=== Completed {len(results)}/{len(args.input)} transcriptions ===")
        if len(results) < len(args.input):
            sys.exit(1)


if __name__ == '__main__':
    main()
