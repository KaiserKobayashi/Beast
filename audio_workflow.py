#!/usr/bin/env python3
"""
audio_workflow.py

Integrated workflow for audio source separation and transcription enhancement.
This module combines audio_separation.py and audio_mixing.py to provide:

1. Separate audio sources (vocals, instruments, etc.)
2. Isolate clean vocals for Whisper transcription
3. Provide mixing capabilities for reconstruction

This solves the problem where Whisper transcriptions are inaccurate due to
background noise, music, or other voices by preprocessing the audio first.
"""

import argparse
import sys
import subprocess
from pathlib import Path
from typing import Dict, Optional, List

# Local imports
try:
    import audio_separation
    SEPARATION_AVAILABLE = True
except ImportError:
    SEPARATION_AVAILABLE = False

try:
    import audio_mixing
    MIXING_AVAILABLE = True
except ImportError:
    MIXING_AVAILABLE = False


def check_dependencies():
    """Check if required modules are available."""
    if not SEPARATION_AVAILABLE:
        print("ERROR: audio_separation module not found")
        return False
    if not MIXING_AVAILABLE:
        print("ERROR: audio_mixing module not found")
        return False
    return True


def prepare_for_transcription(
    input_audio: str,
    output_dir: str,
    model_name: str = "htdemucs",
    device: str = "cpu",
    keep_all_sources: bool = True,
) -> Dict[str, Path]:
    """
    Prepare audio for transcription by separating sources and isolating vocals.
    
    This workflow:
    1. Separates audio into sources (vocals, drums, bass, other)
    2. Extracts clean vocals for transcription
    3. Optionally keeps all sources for later remixing
    
    Args:
        input_audio: Path to input audio file
        output_dir: Directory for output files
        model_name: Demucs model to use
        device: Processing device ('cpu' or 'cuda')
        keep_all_sources: Whether to keep all separated sources
        
    Returns:
        Dictionary with paths to separated files
    """
    if not audio_separation.check_dependencies():
        raise RuntimeError("Audio separation dependencies not available")
    
    print("="*60)
    print("AUDIO PREPARATION WORKFLOW FOR TRANSCRIPTION")
    print("="*60)
    print(f"Input: {input_audio}")
    print(f"Output: {output_dir}")
    print("="*60)
    
    # Step 1: Separate audio sources
    print("\nStep 1: Separating audio sources...")
    separated = audio_separation.separate_audio(
        input_path=input_audio,
        output_dir=output_dir,
        model_name=model_name,
        device=device,
    )
    
    # Step 2: Identify vocals for transcription
    print("\nStep 2: Identifying vocals for transcription...")
    if "vocals" not in separated:
        print("WARNING: No vocals track found in separated sources")
        print(f"Available sources: {list(separated.keys())}")
        # Try to find any voice-related source
        for key in separated.keys():
            if "vocal" in key.lower() or "voice" in key.lower():
                vocals_path = separated[key]
                break
        else:
            print("ERROR: Could not find vocals in separated sources")
            return separated
    else:
        vocals_path = separated["vocals"]
    
    print(f"\n{'='*60}")
    print("✓ Audio preparation complete!")
    print(f"{'='*60}")
    print(f"\nClean vocals for transcription: {vocals_path}")
    print("\nNext steps:")
    print("  1. Use the vocals track for Whisper transcription")
    print("  2. Edit any separated sources if needed")
    print("  3. Use audio_mixing.py to reconstruct the final mix")
    print(f"{'='*60}\n")
    
    return separated


def transcription_workflow(
    input_audio: str,
    output_dir: str,
    whisper_model: str = "base",
    language: Optional[str] = None,
    model_name: str = "htdemucs",
    device: str = "cpu",
    run_whisper: bool = True,
) -> Dict[str, Path]:
    """
    Complete workflow: separate audio, extract vocals, and optionally run Whisper.
    
    Args:
        input_audio: Path to input audio
        output_dir: Directory for output
        whisper_model: Whisper model size (tiny, base, small, medium, large)
        language: Language for transcription (None = auto-detect)
        model_name: Audio separation model
        device: Processing device
        run_whisper: Whether to run Whisper transcription
        
    Returns:
        Dictionary with paths to all outputs
    """
    output_dir = Path(output_dir)
    separated_dir = output_dir / "separated"
    
    # Step 1: Prepare audio (separate sources)
    separated = prepare_for_transcription(
        input_audio=input_audio,
        output_dir=str(separated_dir),
        model_name=model_name,
        device=device,
    )
    
    if not run_whisper:
        return separated
    
    # Step 2: Run Whisper on vocals
    if "vocals" not in separated:
        print("\nWARNING: Cannot run Whisper - no vocals track found")
        return separated
    
    vocals_path = separated["vocals"]
    
    print("\nStep 3: Running Whisper transcription on clean vocals...")
    print(f"Vocals: {vocals_path}")
    
    try:
        # Check if whisper is installed
        result = subprocess.run(
            ["whisper", "--help"],
            capture_output=True,
            timeout=5
        )
        whisper_available = result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        whisper_available = False
    
    if not whisper_available:
        print("\nWARNING: Whisper is not installed or not in PATH")
        print("Install with: pip install openai-whisper")
        print("Or use the vocals track with your preferred transcription tool")
        return separated
    
    # Run Whisper
    whisper_output = output_dir / "transcription"
    whisper_output.mkdir(exist_ok=True)
    
    cmd = [
        "whisper",
        str(vocals_path),
        "--model", whisper_model,
        "--output_dir", str(whisper_output),
        "--output_format", "all",  # Generate all formats (srt, vtt, txt, json)
    ]
    
    if language:
        cmd.extend(["--language", language])
    
    print(f"Running: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
        print(f"\n✓ Transcription saved to: {whisper_output}")
        
        # Add transcription files to results
        separated["transcription_dir"] = whisper_output
        for ext in [".srt", ".vtt", ".txt", ".json"]:
            for file in whisper_output.glob(f"*{ext}"):
                separated[f"transcription_{ext[1:]}"] = file
        
    except subprocess.CalledProcessError as e:
        print(f"\nERROR running Whisper: {e}")
    except Exception as e:
        print(f"\nERROR: {e}")
    
    return separated


def main():
    """CLI entry point for integrated audio workflow."""
    parser = argparse.ArgumentParser(
        prog="audio_workflow",
        description="Integrated workflow for audio separation and transcription enhancement",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Prepare audio for transcription (separate sources, extract vocals)
  python audio_workflow.py prepare --input song.mp3 --output prepared/

  # Full workflow: separate + transcribe with Whisper
  python audio_workflow.py transcribe --input podcast.mp3 --output results/ \\
    --whisper-model base --language en

  # Use GPU for faster processing
  python audio_workflow.py transcribe --input interview.wav --output results/ \\
    --device cuda --whisper-model medium

Workflow explanation:
  1. Audio is separated into sources (vocals, drums, bass, other)
  2. Clean vocals are isolated (free from background music/noise)
  3. Whisper transcribes the clean vocals with much better accuracy
  4. All sources are kept for later editing/remixing if needed
        """,
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Prepare command
    prep_parser = subparsers.add_parser(
        'prepare',
        help='Prepare audio for transcription by separating sources'
    )
    prep_parser.add_argument('--input', required=True, help='Input audio file')
    prep_parser.add_argument('--output', required=True, help='Output directory')
    prep_parser.add_argument('--model', default='htdemucs', help='Separation model (default: htdemucs)')
    prep_parser.add_argument('--device', choices=['cpu', 'cuda'], default='cpu', help='Processing device')
    
    # Transcribe command
    trans_parser = subparsers.add_parser(
        'transcribe',
        help='Complete workflow: separate audio and transcribe vocals with Whisper'
    )
    trans_parser.add_argument('--input', required=True, help='Input audio file')
    trans_parser.add_argument('--output', required=True, help='Output directory')
    trans_parser.add_argument('--whisper-model', default='base', 
                             choices=['tiny', 'base', 'small', 'medium', 'large'],
                             help='Whisper model size (default: base)')
    trans_parser.add_argument('--language', help='Language code (e.g., en, es, fr). Auto-detect if not specified')
    trans_parser.add_argument('--model', default='htdemucs', help='Separation model (default: htdemucs)')
    trans_parser.add_argument('--device', choices=['cpu', 'cuda'], default='cpu', help='Processing device')
    trans_parser.add_argument('--no-whisper', action='store_true', help='Skip Whisper transcription')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    if not check_dependencies():
        return 1
    
    try:
        if args.command == 'prepare':
            prepare_for_transcription(
                input_audio=args.input,
                output_dir=args.output,
                model_name=args.model,
                device=args.device,
            )
        
        elif args.command == 'transcribe':
            transcription_workflow(
                input_audio=args.input,
                output_dir=args.output,
                whisper_model=args.whisper_model,
                language=args.language,
                model_name=args.model,
                device=args.device,
                run_whisper=not args.no_whisper,
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
