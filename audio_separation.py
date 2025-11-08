#!/usr/bin/env python3
"""
audio_separation.py

Audio source separation module using Demucs for identifying and isolating
different sound sources (vocals, drums, bass, other instruments) from audio tracks.

This module provides:
- Command-line interface for audio separation
- Support for various audio formats (mp3, wav, flac, etc.)
- Multiple separation models (4-stem default: vocals, drums, bass, other)
- Batch processing capabilities
"""

import argparse
import os
import sys
from pathlib import Path
from typing import List, Optional, Dict

try:
    import torch
    from demucs.pretrained import get_model
    from demucs.apply import apply_model
    from demucs.audio import AudioFile, save_audio
    DEMUCS_AVAILABLE = True
except ImportError:
    DEMUCS_AVAILABLE = False
    torch = None


def check_dependencies():
    """Check if required dependencies are installed."""
    if not DEMUCS_AVAILABLE:
        print("ERROR: Demucs is not installed.")
        print("Please install it with: pip install demucs")
        print("\nDemucs is a state-of-the-art audio source separation library.")
        print("It can separate audio into vocals, drums, bass, and other instruments.")
        return False
    return True


def separate_audio(
    input_path: str,
    output_dir: str,
    model_name: str = "htdemucs",
    device: str = "cpu",
    shifts: int = 1,
    split: bool = True,
    overlap: float = 0.25,
) -> Dict[str, Path]:
    """
    Separate an audio file into its constituent sources.
    
    Args:
        input_path: Path to input audio file
        output_dir: Directory to save separated tracks
        model_name: Model to use (htdemucs, htdemucs_ft, htdemucs_6s, etc.)
        device: Device to use for processing ('cpu' or 'cuda')
        shifts: Number of random shifts for equivariant stabilization
        split: Whether to split audio into chunks for processing
        overlap: Overlap between splits
        
    Returns:
        Dictionary mapping source names to output file paths
    """
    if not check_dependencies():
        raise RuntimeError("Demucs dependencies not available")
    
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    print(f"Loading model: {model_name}")
    model = get_model(model_name)
    
    # Move model to device
    if device == "cuda" and torch.cuda.is_available():
        model = model.cuda()
    else:
        device = "cpu"
        model = model.cpu()
    
    print(f"Processing on device: {device}")
    print(f"Loading audio: {input_path}")
    
    # Load audio
    wav = AudioFile(input_path).read(
        streams=0,
        samplerate=model.samplerate,
        channels=model.audio_channels,
    )
    
    ref = wav.mean(0)
    wav = (wav - ref.mean()) / ref.std()
    
    print("Separating sources...")
    # Apply model
    sources = apply_model(
        model,
        wav[None],
        device=device,
        shifts=shifts,
        split=split,
        overlap=overlap,
        progress=True,
    )[0]
    
    sources = sources * ref.std() + ref.mean()
    
    # Save separated sources
    output_paths = {}
    source_names = model.sources
    
    print(f"\nSaving separated tracks to: {output_dir}")
    for source_idx, source_name in enumerate(source_names):
        source_audio = sources[source_idx]
        output_path = output_dir / f"{input_path.stem}_{source_name}.wav"
        save_audio(source_audio, output_path, samplerate=model.samplerate)
        output_paths[source_name] = output_path
        print(f"  - {source_name}: {output_path}")
    
    return output_paths


def process_batch(
    input_paths: List[str],
    output_dir: str,
    model_name: str = "htdemucs",
    device: str = "cpu",
) -> Dict[str, Dict[str, Path]]:
    """
    Process multiple audio files in batch.
    
    Args:
        input_paths: List of input audio file paths
        output_dir: Base directory for output
        model_name: Model to use
        device: Device to use for processing
        
    Returns:
        Dictionary mapping input filenames to their separated tracks
    """
    results = {}
    total = len(input_paths)
    
    for idx, input_path in enumerate(input_paths, 1):
        print(f"\n{'='*60}")
        print(f"Processing file {idx}/{total}: {input_path}")
        print(f"{'='*60}")
        
        try:
            input_name = Path(input_path).stem
            file_output_dir = Path(output_dir) / input_name
            separated = separate_audio(
                input_path=input_path,
                output_dir=str(file_output_dir),
                model_name=model_name,
                device=device,
            )
            results[input_name] = separated
            print(f"✓ Successfully processed: {input_path}")
        except Exception as e:
            print(f"✗ Error processing {input_path}: {e}", file=sys.stderr)
            results[input_name] = {}
    
    return results


def list_available_models():
    """List available Demucs models."""
    if not check_dependencies():
        return
    
    print("Available Demucs models:")
    print("  - htdemucs: 4-stem model (vocals, drums, bass, other) [DEFAULT]")
    print("  - htdemucs_ft: Fine-tuned 4-stem model")
    print("  - htdemucs_6s: 6-stem model (vocals, drums, bass, guitar, piano, other)")
    print("  - mdx: Hybrid transformer model")
    print("  - mdx_extra: Extra large hybrid model")
    print("  - mdx_q: Quantized hybrid model (faster, smaller)")
    print("\nNote: Some models require additional downloads on first use.")


def main():
    """CLI entry point for audio source separation."""
    parser = argparse.ArgumentParser(
        prog="audio_separation",
        description="Separate audio tracks into constituent sources (vocals, drums, bass, instruments, etc.)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Separate a single audio file
  python audio_separation.py --input song.mp3 --output separated/

  # Use 6-stem model for more detailed separation
  python audio_separation.py --input song.mp3 --output separated/ --model htdemucs_6s

  # Process all audio files in a folder
  python audio_separation.py --input music_folder/ --output separated/

  # Use GPU acceleration (if available)
  python audio_separation.py --input song.mp3 --output separated/ --device cuda

  # List available models
  python audio_separation.py --list-models
        """,
    )
    
    parser.add_argument(
        "--input",
        help="Input audio file or folder containing audio files",
    )
    parser.add_argument(
        "--output",
        default="separated",
        help="Output directory for separated tracks (default: separated/)",
    )
    parser.add_argument(
        "--model",
        default="htdemucs",
        help="Separation model to use (default: htdemucs). Use --list-models to see options",
    )
    parser.add_argument(
        "--device",
        choices=["cpu", "cuda"],
        default="cpu",
        help="Device to use for processing (default: cpu)",
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List available models and exit",
    )
    parser.add_argument(
        "--shifts",
        type=int,
        default=1,
        help="Number of random shifts for equivariant stabilization (default: 1, higher = better quality but slower)",
    )
    
    args = parser.parse_args()
    
    if args.list_models:
        list_available_models()
        return 0
    
    if not args.input:
        parser.print_help()
        print("\nERROR: --input is required (unless using --list-models)", file=sys.stderr)
        return 1
    
    if not check_dependencies():
        return 1
    
    input_path = Path(args.input)
    
    if not input_path.exists():
        print(f"ERROR: Input path does not exist: {input_path}", file=sys.stderr)
        return 1
    
    # Collect input files
    input_files = []
    if input_path.is_file():
        input_files = [str(input_path)]
    elif input_path.is_dir():
        # Supported audio formats
        audio_extensions = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".wma"}
        for ext in audio_extensions:
            input_files.extend([str(f) for f in input_path.glob(f"*{ext}")])
            input_files.extend([str(f) for f in input_path.glob(f"*{ext.upper()}")])
        
        if not input_files:
            print(f"ERROR: No audio files found in directory: {input_path}", file=sys.stderr)
            return 1
        
        input_files = sorted(set(input_files))
        print(f"Found {len(input_files)} audio file(s) to process")
    
    try:
        if len(input_files) == 1:
            print(f"\nSeparating audio file: {input_files[0]}")
            separate_audio(
                input_path=input_files[0],
                output_dir=args.output,
                model_name=args.model,
                device=args.device,
                shifts=args.shifts,
            )
        else:
            print(f"\nProcessing {len(input_files)} files in batch mode")
            process_batch(
                input_paths=input_files,
                output_dir=args.output,
                model_name=args.model,
                device=args.device,
            )
        
        print("\n" + "="*60)
        print("✓ Audio separation completed successfully!")
        print(f"Output saved to: {Path(args.output).absolute()}")
        print("="*60)
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
