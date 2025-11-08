#!/usr/bin/env python3
"""
download_and_transcribe.py

Integrated workflow: Download video and transcribe it using Whisper.
Combines download_beast.py and whisper_transcribe.py functionality.
"""
import argparse
import os
import sys
from pathlib import Path
from typing import Optional, List

# Import our modules
try:
    from download_beast import download_video, download_playlist
except ImportError:
    download_video = None
    download_playlist = None

try:
    from whisper_transcribe import transcribe_audio, batch_transcribe
except ImportError:
    transcribe_audio = None
    batch_transcribe = None


def download_and_transcribe_single(
    url: str,
    output_dir: str = "downloads",
    whisper_model: str = "base",
    language: Optional[str] = None,
    audio_only: bool = False,
    keep_video: bool = True,
    verbose: bool = True
) -> Optional[dict]:
    """
    Download a video and transcribe it.
    
    Args:
        url: Video URL to download
        output_dir: Directory to save downloads and transcriptions
        whisper_model: Whisper model size (tiny, base, small, medium, large)
        language: Language code for transcription (auto-detected if None)
        audio_only: Download only audio (faster)
        keep_video: Keep video file after transcription
        verbose: Show progress output
        
    Returns:
        Dictionary with download and transcription info or None on error
    """
    if download_video is None:
        raise RuntimeError("download_beast module not available")
    if transcribe_audio is None:
        raise RuntimeError("whisper_transcribe module not available")
    
    # Step 1: Download video
    if verbose:
        print("=" * 60)
        print("STEP 1: DOWNLOADING VIDEO")
        print("=" * 60)
    
    downloaded_file = download_video(
        url,
        output_dir=output_dir,
        format_spec="best" if not audio_only else "bestaudio",
        extract_audio=audio_only,
        audio_format="mp3" if audio_only else None,
        verbose=verbose
    )
    
    if not downloaded_file:
        print("Error: Failed to download video", file=sys.stderr)
        return None
    
    # Step 2: Transcribe
    if verbose:
        print("\n" + "=" * 60)
        print("STEP 2: TRANSCRIBING AUDIO")
        print("=" * 60)
    
    result = transcribe_audio(
        downloaded_file,
        model_size=whisper_model,
        language=language,
        output_dir=output_dir,
        output_format="all",  # Generate SRT, TXT, and JSON
        verbose=verbose
    )
    
    if not result:
        print("Error: Failed to transcribe", file=sys.stderr)
        return None
    
    # Step 3: Cleanup (optional)
    if audio_only and not keep_video:
        if verbose:
            print(f"\nRemoving downloaded file: {downloaded_file}")
        try:
            os.remove(downloaded_file)
        except Exception as e:
            print(f"Warning: Could not remove file: {e}", file=sys.stderr)
    
    if verbose:
        print("\n" + "=" * 60)
        print("WORKFLOW COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"Downloaded: {downloaded_file}")
        print(f"Language: {result.get('language', 'unknown')}")
        print(f"Transcription files saved to: {output_dir}")
    
    return {
        'downloaded_file': downloaded_file,
        'transcription': result,
        'output_dir': output_dir
    }


def download_and_transcribe_playlist(
    url: str,
    output_dir: str = "downloads",
    whisper_model: str = "base",
    language: Optional[str] = None,
    max_downloads: Optional[int] = None,
    audio_only: bool = False,
    keep_video: bool = True,
    verbose: bool = True
) -> List[dict]:
    """
    Download a playlist and transcribe all videos.
    
    Args:
        url: Playlist URL
        output_dir: Directory to save downloads and transcriptions
        whisper_model: Whisper model size
        language: Language code for transcription
        max_downloads: Maximum number of videos to process
        audio_only: Download only audio
        keep_video: Keep video files after transcription
        verbose: Show progress output
        
    Returns:
        List of result dictionaries for each video
    """
    if download_playlist is None:
        raise RuntimeError("download_beast module not available")
    if batch_transcribe is None:
        raise RuntimeError("whisper_transcribe module not available")
    
    # Step 1: Download playlist
    if verbose:
        print("=" * 60)
        print("STEP 1: DOWNLOADING PLAYLIST")
        print("=" * 60)
    
    downloaded_files = download_playlist(
        url,
        output_dir=output_dir,
        format_spec="best",
        max_downloads=max_downloads,
        verbose=verbose
    )
    
    if not downloaded_files:
        print("Error: Failed to download playlist", file=sys.stderr)
        return []
    
    # Step 2: Transcribe all videos
    if verbose:
        print("\n" + "=" * 60)
        print("STEP 2: TRANSCRIBING ALL VIDEOS")
        print("=" * 60)
    
    results = batch_transcribe(
        downloaded_files,
        model_size=whisper_model,
        language=language,
        output_dir=output_dir,
        output_format="all",
        verbose=verbose
    )
    
    # Step 3: Cleanup (optional)
    if audio_only and not keep_video:
        if verbose:
            print("\nCleaning up downloaded files...")
        for file in downloaded_files:
            try:
                os.remove(file)
                if verbose:
                    print(f"Removed: {file}")
            except Exception as e:
                print(f"Warning: Could not remove {file}: {e}", file=sys.stderr)
    
    if verbose:
        print("\n" + "=" * 60)
        print("PLAYLIST WORKFLOW COMPLETED!")
        print("=" * 60)
        print(f"Processed: {len(results)}/{len(downloaded_files)} videos")
        print(f"Transcription files saved to: {output_dir}")
    
    return [{'downloaded_file': f, 'transcription': r, 'output_dir': output_dir}
            for f, r in zip(downloaded_files, results)]


def main():
    parser = argparse.ArgumentParser(
        description="Download and transcribe videos using yt-dlp and Whisper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download and transcribe a single video
  python download_and_transcribe.py https://youtube.com/watch?v=VIDEO_ID

  # Transcribe with specific language and model
  python download_and_transcribe.py URL --language en --model medium

  # Download audio only and transcribe (faster)
  python download_and_transcribe.py URL --audio-only

  # Process a playlist (first 3 videos)
  python download_and_transcribe.py PLAYLIST_URL --playlist --max 3

  # Custom output directory
  python download_and_transcribe.py URL --output my_transcriptions

Workflow:
  1. Downloads video/audio from URL using yt-dlp
  2. Transcribes using OpenAI Whisper with language detection
  3. Generates SRT subtitles, plain text, and JSON output
  4. Optionally cleans up downloaded files

Model sizes (accuracy vs speed):
  - tiny: Fastest, least accurate
  - base: Good balance [default]
  - small: Better accuracy
  - medium: High accuracy
  - large: Best accuracy (requires powerful GPU)

Requirements:
  - yt-dlp: pip install yt-dlp
  - openai-whisper: pip install openai-whisper
  - ffmpeg: System package (apt/brew/choco)
        """
    )
    
    parser.add_argument('url', help='Video or playlist URL')
    parser.add_argument('--output', '-o', default='downloads',
                        help='Output directory (default: downloads)')
    parser.add_argument('--model', '-m', default='base',
                        choices=['tiny', 'base', 'small', 'medium', 'large'],
                        help='Whisper model size (default: base)')
    parser.add_argument('--language', '-l',
                        help='Language code (e.g., en, es, fr). Auto-detected if not specified')
    parser.add_argument('--playlist', '-p', action='store_true',
                        help='Download and transcribe playlist')
    parser.add_argument('--max', type=int, metavar='N',
                        help='Maximum number of videos from playlist')
    parser.add_argument('--audio-only', '-a', action='store_true',
                        help='Download audio only (faster, smaller)')
    parser.add_argument('--remove-source', action='store_true',
                        help='Remove downloaded files after transcription')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Suppress progress output')
    
    args = parser.parse_args()
    
    # Check dependencies
    if download_video is None or download_playlist is None:
        print("Error: download_beast module not available", file=sys.stderr)
        print("Make sure download_beast.py is in the same directory", file=sys.stderr)
        sys.exit(1)
    
    if transcribe_audio is None or batch_transcribe is None:
        print("Error: whisper_transcribe module not available", file=sys.stderr)
        print("Make sure whisper_transcribe.py is in the same directory", file=sys.stderr)
        sys.exit(1)
    
    verbose = not args.quiet
    keep_video = not args.remove_source
    
    # Execute workflow
    try:
        if args.playlist:
            results = download_and_transcribe_playlist(
                args.url,
                output_dir=args.output,
                whisper_model=args.model,
                language=args.language,
                max_downloads=args.max,
                audio_only=args.audio_only,
                keep_video=keep_video,
                verbose=verbose
            )
            if not results:
                sys.exit(1)
        else:
            result = download_and_transcribe_single(
                args.url,
                output_dir=args.output,
                whisper_model=args.model,
                language=args.language,
                audio_only=args.audio_only,
                keep_video=keep_video,
                verbose=verbose
            )
            if not result:
                sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
