#!/usr/bin/env python3
"""
audio_mixing.py

Audio mixing and reconstruction module for combining separated or edited audio sources
back into a single track. Supports:
- Mixing multiple audio sources with individual volume control
- Replacing individual sources (e.g., swap vocals, change instruments)
- Adding new audio sources to the mix
- Individual track editing before recombination
- Export to various formats (wav, mp3, flac, etc.)

This complements audio_separation.py by allowing reconstruction after editing.
"""

import argparse
import sys
from pathlib import Path
from typing import List, Dict, Optional, Union

try:
    from pydub import AudioSegment
    from pydub.effects import normalize
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    AudioSegment = None


def check_dependencies():
    """Check if required dependencies are installed."""
    if not PYDUB_AVAILABLE:
        print("ERROR: pydub is not installed.")
        print("Please install it with: pip install pydub")
        print("\nNote: pydub also requires ffmpeg to be installed on your system.")
        print("Install ffmpeg:")
        print("  - Ubuntu/Debian: sudo apt-get install ffmpeg")
        print("  - macOS: brew install ffmpeg")
        print("  - Windows: Download from https://ffmpeg.org/download.html")
        return False
    return True


def load_audio(path: Union[str, Path]) -> AudioSegment:
    """
    Load an audio file into an AudioSegment.
    
    Args:
        path: Path to audio file
        
    Returns:
        AudioSegment object
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {path}")
    
    print(f"Loading: {path.name}")
    return AudioSegment.from_file(str(path))


def mix_sources(
    sources: Dict[str, Path],
    output_path: Union[str, Path],
    volumes: Optional[Dict[str, float]] = None,
    normalize_output: bool = True,
    output_format: str = "wav",
) -> Path:
    """
    Mix multiple audio sources into a single track.
    
    Args:
        sources: Dictionary mapping source names to file paths
        output_path: Path for output mixed file
        volumes: Optional dictionary of volume adjustments in dB (e.g., {"vocals": 2, "drums": -3})
        normalize_output: Whether to normalize the output to prevent clipping
        output_format: Output format (wav, mp3, flac, etc.)
        
    Returns:
        Path to the output file
    """
    if not check_dependencies():
        raise RuntimeError("Required dependencies not available")
    
    if not sources:
        raise ValueError("No sources provided for mixing")
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"\nMixing {len(sources)} audio sources:")
    
    # Load all sources
    audio_segments = {}
    max_duration = 0
    
    for name, path in sources.items():
        segment = load_audio(path)
        
        # Apply volume adjustment if specified
        if volumes and name in volumes:
            volume_change = volumes[name]
            segment = segment + volume_change
            print(f"  - {name}: {volume_change:+.1f} dB")
        else:
            print(f"  - {name}: 0.0 dB")
        
        audio_segments[name] = segment
        max_duration = max(max_duration, len(segment))
    
    print(f"\nMax duration: {max_duration/1000:.2f} seconds")
    
    # Ensure all segments have the same length (pad with silence if needed)
    print("Aligning tracks...")
    for name in audio_segments:
        current_len = len(audio_segments[name])
        if current_len < max_duration:
            silence_needed = max_duration - current_len
            audio_segments[name] = audio_segments[name] + AudioSegment.silent(duration=silence_needed)
    
    # Mix all sources by overlaying them
    print("Mixing tracks...")
    mixed = None
    for name, segment in audio_segments.items():
        if mixed is None:
            mixed = segment
        else:
            mixed = mixed.overlay(segment)
    
    # Normalize to prevent clipping if requested
    if normalize_output:
        print("Normalizing output...")
        mixed = normalize(mixed)
    
    # Export
    print(f"Exporting to {output_path} (format: {output_format})...")
    mixed.export(str(output_path), format=output_format)
    
    print(f"✓ Mixed audio saved to: {output_path}")
    return output_path


def replace_source(
    original_mix_path: Union[str, Path],
    separated_sources_dir: Union[str, Path],
    source_to_replace: str,
    replacement_path: Union[str, Path],
    output_path: Union[str, Path],
    output_format: str = "wav",
) -> Path:
    """
    Replace one source in a separated mix with a new audio file.
    
    Args:
        original_mix_path: Path to original mixed audio (for reference)
        separated_sources_dir: Directory containing separated sources
        source_to_replace: Name of source to replace (e.g., "vocals", "drums")
        replacement_path: Path to replacement audio file
        output_path: Path for output file
        output_format: Output format
        
    Returns:
        Path to output file
    """
    separated_sources_dir = Path(separated_sources_dir)
    
    # Find all separated source files
    source_files = {}
    for ext in ['.wav', '.mp3', '.flac']:
        for file in separated_sources_dir.glob(f"*{ext}"):
            # Extract source name from filename (e.g., "song_vocals.wav" -> "vocals")
            parts = file.stem.split('_')
            if len(parts) >= 2:
                source_name = parts[-1]  # Last part is usually the source name
                source_files[source_name] = file
    
    if not source_files:
        raise ValueError(f"No separated sources found in {separated_sources_dir}")
    
    print(f"Found separated sources: {list(source_files.keys())}")
    
    if source_to_replace not in source_files:
        raise ValueError(f"Source '{source_to_replace}' not found. Available: {list(source_files.keys())}")
    
    # Replace the specified source
    print(f"\nReplacing '{source_to_replace}' with {Path(replacement_path).name}")
    source_files[source_to_replace] = Path(replacement_path)
    
    # Mix all sources
    return mix_sources(
        sources=source_files,
        output_path=output_path,
        output_format=output_format,
    )


def add_source(
    separated_sources_dir: Union[str, Path],
    new_source_path: Union[str, Path],
    new_source_name: str,
    output_path: Union[str, Path],
    volume: float = 0.0,
    output_format: str = "wav",
) -> Path:
    """
    Add a new audio source to an existing separated mix.
    
    Args:
        separated_sources_dir: Directory containing separated sources
        new_source_path: Path to new audio file to add
        new_source_name: Name for the new source (for reference)
        output_path: Path for output file
        volume: Volume adjustment in dB for new source
        output_format: Output format
        
    Returns:
        Path to output file
    """
    separated_sources_dir = Path(separated_sources_dir)
    
    # Find all separated source files
    source_files = {}
    for ext in ['.wav', '.mp3', '.flac']:
        for file in separated_sources_dir.glob(f"*{ext}"):
            parts = file.stem.split('_')
            if len(parts) >= 2:
                source_name = parts[-1]
                source_files[source_name] = file
    
    if not source_files:
        raise ValueError(f"No separated sources found in {separated_sources_dir}")
    
    print(f"Found separated sources: {list(source_files.keys())}")
    print(f"Adding new source: '{new_source_name}'")
    
    # Add the new source
    source_files[new_source_name] = Path(new_source_path)
    
    # Mix all sources
    volumes = {new_source_name: volume} if volume != 0.0 else None
    return mix_sources(
        sources=source_files,
        output_path=output_path,
        volumes=volumes,
        output_format=output_format,
    )


def create_instrumental(
    separated_sources_dir: Union[str, Path],
    output_path: Union[str, Path],
    exclude_sources: Optional[List[str]] = None,
    output_format: str = "wav",
) -> Path:
    """
    Create an instrumental track by excluding specified sources (e.g., vocals).
    
    Args:
        separated_sources_dir: Directory containing separated sources
        output_path: Path for output file
        exclude_sources: List of source names to exclude (default: ["vocals"])
        output_format: Output format
        
    Returns:
        Path to output file
    """
    if exclude_sources is None:
        exclude_sources = ["vocals"]
    
    separated_sources_dir = Path(separated_sources_dir)
    
    # Find all separated source files
    source_files = {}
    for ext in ['.wav', '.mp3', '.flac']:
        for file in separated_sources_dir.glob(f"*{ext}"):
            parts = file.stem.split('_')
            if len(parts) >= 2:
                source_name = parts[-1]
                if source_name not in exclude_sources:
                    source_files[source_name] = file
    
    if not source_files:
        raise ValueError(f"No sources remaining after excluding {exclude_sources}")
    
    print(f"Creating instrumental from: {list(source_files.keys())}")
    print(f"Excluded: {exclude_sources}")
    
    return mix_sources(
        sources=source_files,
        output_path=output_path,
        output_format=output_format,
    )


def create_acapella(
    separated_sources_dir: Union[str, Path],
    output_path: Union[str, Path],
    output_format: str = "wav",
) -> Path:
    """
    Create an acapella track (vocals only).
    
    Args:
        separated_sources_dir: Directory containing separated sources
        output_path: Path for output file
        output_format: Output format
        
    Returns:
        Path to output file
    """
    separated_sources_dir = Path(separated_sources_dir)
    
    # Find vocals file
    vocals_file = None
    for ext in ['.wav', '.mp3', '.flac']:
        candidates = list(separated_sources_dir.glob(f"*vocals{ext}"))
        if candidates:
            vocals_file = candidates[0]
            break
    
    if not vocals_file:
        raise ValueError(f"No vocals file found in {separated_sources_dir}")
    
    print(f"Creating acapella from: {vocals_file.name}")
    
    # Load and export vocals (optionally with processing)
    vocals = load_audio(vocals_file)
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    vocals.export(str(output_path), format=output_format)
    print(f"✓ Acapella saved to: {output_path}")
    
    return output_path


def main():
    """CLI entry point for audio mixing and reconstruction."""
    parser = argparse.ArgumentParser(
        prog="audio_mixing",
        description="Mix, edit, and reconstruct separated audio sources",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Mix all separated sources back together
  python audio_mixing.py mix --input separated/song/ --output remixed.wav

  # Mix with custom volumes (in dB)
  python audio_mixing.py mix --input separated/song/ --output remixed.wav \\
    --volumes "vocals:+3,drums:-2,bass:+1"

  # Replace vocals with a new recording
  python audio_mixing.py replace --input separated/song/ --source vocals \\
    --replacement new_vocals.wav --output new_mix.wav

  # Add a new instrument to the mix
  python audio_mixing.py add --input separated/song/ --new guitar.wav \\
    --name guitar --volume 0 --output with_guitar.wav

  # Create instrumental (remove vocals)
  python audio_mixing.py instrumental --input separated/song/ --output instrumental.wav

  # Create acapella (vocals only)
  python audio_mixing.py acapella --input separated/song/ --output acapella.wav
        """,
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Mix command
    mix_parser = subparsers.add_parser('mix', help='Mix separated sources back together')
    mix_parser.add_argument('--input', required=True, help='Directory containing separated audio files')
    mix_parser.add_argument('--output', required=True, help='Output file path')
    mix_parser.add_argument('--volumes', help='Volume adjustments as "source:db,source:db" (e.g., "vocals:+3,drums:-2")')
    mix_parser.add_argument('--format', default='wav', choices=['wav', 'mp3', 'flac', 'ogg'], help='Output format')
    mix_parser.add_argument('--no-normalize', action='store_true', help='Disable output normalization')
    
    # Replace command
    replace_parser = subparsers.add_parser('replace', help='Replace one source with new audio')
    replace_parser.add_argument('--input', required=True, help='Directory containing separated audio files')
    replace_parser.add_argument('--source', required=True, help='Source to replace (e.g., vocals, drums)')
    replace_parser.add_argument('--replacement', required=True, help='Path to replacement audio file')
    replace_parser.add_argument('--output', required=True, help='Output file path')
    replace_parser.add_argument('--format', default='wav', choices=['wav', 'mp3', 'flac', 'ogg'], help='Output format')
    
    # Add command
    add_parser = subparsers.add_parser('add', help='Add a new source to the mix')
    add_parser.add_argument('--input', required=True, help='Directory containing separated audio files')
    add_parser.add_argument('--new', required=True, help='Path to new audio file')
    add_parser.add_argument('--name', required=True, help='Name for the new source')
    add_parser.add_argument('--volume', type=float, default=0.0, help='Volume adjustment in dB (default: 0)')
    add_parser.add_argument('--output', required=True, help='Output file path')
    add_parser.add_argument('--format', default='wav', choices=['wav', 'mp3', 'flac', 'ogg'], help='Output format')
    
    # Instrumental command
    inst_parser = subparsers.add_parser('instrumental', help='Create instrumental (remove vocals)')
    inst_parser.add_argument('--input', required=True, help='Directory containing separated audio files')
    inst_parser.add_argument('--output', required=True, help='Output file path')
    inst_parser.add_argument('--exclude', nargs='+', default=['vocals'], help='Sources to exclude (default: vocals)')
    inst_parser.add_argument('--format', default='wav', choices=['wav', 'mp3', 'flac', 'ogg'], help='Output format')
    
    # Acapella command
    acap_parser = subparsers.add_parser('acapella', help='Create acapella (vocals only)')
    acap_parser.add_argument('--input', required=True, help='Directory containing separated audio files')
    acap_parser.add_argument('--output', required=True, help='Output file path')
    acap_parser.add_argument('--format', default='wav', choices=['wav', 'mp3', 'flac', 'ogg'], help='Output format')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    if not check_dependencies():
        return 1
    
    try:
        if args.command == 'mix':
            # Parse volumes if provided
            volumes = None
            if args.volumes:
                volumes = {}
                for entry in args.volumes.split(','):
                    if ':' in entry:
                        source, db = entry.split(':', 1)
                        volumes[source.strip()] = float(db.strip())
            
            # Find all source files
            input_dir = Path(args.input)
            source_files = {}
            for ext in ['.wav', '.mp3', '.flac']:
                for file in input_dir.glob(f"*{ext}"):
                    parts = file.stem.split('_')
                    if len(parts) >= 2:
                        source_name = parts[-1]
                        source_files[source_name] = file
            
            if not source_files:
                print(f"ERROR: No audio files found in {input_dir}", file=sys.stderr)
                return 1
            
            mix_sources(
                sources=source_files,
                output_path=args.output,
                volumes=volumes,
                normalize_output=not args.no_normalize,
                output_format=args.format,
            )
        
        elif args.command == 'replace':
            replace_source(
                original_mix_path=None,  # Not needed for this operation
                separated_sources_dir=args.input,
                source_to_replace=args.source,
                replacement_path=args.replacement,
                output_path=args.output,
                output_format=args.format,
            )
        
        elif args.command == 'add':
            add_source(
                separated_sources_dir=args.input,
                new_source_path=getattr(args, 'new'),
                new_source_name=args.name,
                output_path=args.output,
                volume=args.volume,
                output_format=args.format,
            )
        
        elif args.command == 'instrumental':
            create_instrumental(
                separated_sources_dir=args.input,
                output_path=args.output,
                exclude_sources=args.exclude,
                output_format=args.format,
            )
        
        elif args.command == 'acapella':
            create_acapella(
                separated_sources_dir=args.input,
                output_path=args.output,
                output_format=args.format,
            )
        
        print("\n" + "="*60)
        print("✓ Audio mixing completed successfully!")
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
