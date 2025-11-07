#!/usr/bin/env python3
"""
download_beast.py

Download videos from URLs using yt-dlp.
Supports YouTube and many other video platforms.
"""
import argparse
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import yt_dlp
except ImportError:
    yt_dlp = None


class DownloadProgress:
    """Simple progress tracker for downloads."""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose

    def __call__(self, d: Dict[str, Any]):
        if d['status'] == 'downloading':
            if self.verbose:
                percent = d.get('_percent_str', 'N/A')
                speed = d.get('_speed_str', 'N/A')
                eta = d.get('_eta_str', 'N/A')
                print(
                    f"\rDownloading: {percent} at {speed} ETA: {eta}",
                    end='',
                    flush=True)
        elif d['status'] == 'finished':
            if self.verbose:
                print("\nDownload completed, now processing...")


def download_video(
    url: str,
    output_dir: str = "downloads",
    format_spec: str = "best",
    extract_audio: bool = False,
    audio_format: str = "mp3",
    subtitles: bool = False,
    auto_subs: bool = False,
    embed_subs: bool = False,
    verbose: bool = True,
    cookies_file: Optional[str] = None
) -> Optional[str]:
    """
    Download a video from URL using yt-dlp.

    Args:
        url: Video URL to download
        output_dir: Directory to save downloads
        format_spec: Format specification (e.g., 'best', 'bestvideo+bestaudio')
        extract_audio: Extract audio only
        audio_format: Audio format when extracting audio (mp3, wav, etc.)
        subtitles: Download subtitles
        auto_subs: Download auto-generated subtitles
        embed_subs: Embed subtitles in video file
        verbose: Show progress output
        cookies_file: Path to cookies file for authentication

    Returns:
        Path to downloaded file or None on error
    """
    if yt_dlp is None:
        raise RuntimeError(
            "yt-dlp is not installed. Install with: pip install yt-dlp")

    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    # Build yt-dlp options
    ydl_opts = {
        'format': format_spec,
        'outtmpl': str(output_dir_path / '%(title)s.%(ext)s'),
        'progress_hooks': [DownloadProgress(verbose)],
        'quiet': not verbose,
        'no_warnings': not verbose,
    }

    if extract_audio:
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': audio_format,
        }]

    if subtitles or auto_subs:
        ydl_opts['writesubtitles'] = subtitles
        ydl_opts['writeautomaticsub'] = auto_subs
        ydl_opts['subtitleslangs'] = ['all']
        if embed_subs:
            ydl_opts['postprocessors'] = ydl_opts.get(
                'postprocessors', []) + [{'key': 'FFmpegEmbedSubtitle'}]

    if cookies_file and os.path.exists(cookies_file):
        ydl_opts['cookiefile'] = cookies_file

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info:
                # Get the actual filename
                filename = ydl.prepare_filename(info)

                # If audio extraction, adjust extension
                if extract_audio:
                    filename = Path(filename).with_suffix(f'.{audio_format}')

                if verbose:
                    print(f"\nSaved to: {filename}")

                return str(filename)
    except Exception as e:
        print(f"Error downloading video: {e}", file=sys.stderr)
        return None


def download_playlist(
    url: str,
    output_dir: str = "downloads",
    format_spec: str = "best",
    max_downloads: Optional[int] = None,
    verbose: bool = True
) -> list:
    """
    Download all videos from a playlist.

    Args:
        url: Playlist URL
        output_dir: Directory to save downloads
        format_spec: Format specification
        max_downloads: Maximum number of videos to download (None for all)
        verbose: Show progress output

    Returns:
        List of downloaded file paths
    """
    if yt_dlp is None:
        raise RuntimeError(
            "yt-dlp is not installed. Install with: pip install yt-dlp")

    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    ydl_opts = {
        'format': format_spec,
        'outtmpl': str(output_dir_path / '%(playlist_index)s-%(title)s.%(ext)s'),
        'progress_hooks': [DownloadProgress(verbose)],
        'quiet': not verbose,
        'no_warnings': not verbose,
        'noplaylist': False,
    }

    if max_downloads:
        ydl_opts['playlistend'] = max_downloads

    downloaded_files = []
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info and 'entries' in info:
                for entry in info['entries']:
                    if entry:
                        filename = ydl.prepare_filename(entry)
                        downloaded_files.append(filename)
                        if verbose:
                            print(f"Downloaded: {filename}")
    except Exception as e:
        print(f"Error downloading playlist: {e}", file=sys.stderr)

    return downloaded_files


def main():
    parser = argparse.ArgumentParser(
        description="Download videos from URLs using yt-dlp",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download a video
  python download_beast.py https://www.youtube.com/watch?v=VIDEO_ID

  # Download video to specific directory
  python download_beast.py https://example.com/video --output downloads/videos

  # Extract audio only as MP3
  python download_beast.py https://example.com/video --audio-only --audio-format mp3

  # Download with subtitles
  python download_beast.py https://example.com/video --subtitles --embed-subs

  # Download playlist (first 5 videos)
  python download_beast.py https://www.youtube.com/playlist?list=... --playlist --max 5
        """
    )

    parser.add_argument('url', help='Video or playlist URL to download')
    parser.add_argument('--output', '-o', default='downloads',
                        help='Output directory (default: downloads)')
    parser.add_argument('--format', '-f', default='best',
                        help='Format specification (default: best)')
    parser.add_argument('--audio-only', '-a', action='store_true',
                        help='Extract audio only')
    parser.add_argument(
        '--audio-format',
        default='mp3',
        choices=[
            'mp3',
            'wav',
            'flac',
            'm4a',
            'opus'],
        help='Audio format when using --audio-only (default: mp3)')
    parser.add_argument('--subtitles', '-s', action='store_true',
                        help='Download subtitles')
    parser.add_argument('--auto-subs', action='store_true',
                        help='Download auto-generated subtitles')
    parser.add_argument('--embed-subs', action='store_true',
                        help='Embed subtitles in video file')
    parser.add_argument('--playlist', '-p', action='store_true',
                        help='Download entire playlist')
    parser.add_argument(
        '--max',
        type=int,
        metavar='N',
        help='Maximum number of videos to download from playlist')
    parser.add_argument('--cookies', metavar='FILE',
                        help='Path to cookies file for authentication')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Suppress progress output')

    args = parser.parse_args()

    if yt_dlp is None:
        print("Error: yt-dlp is not installed.", file=sys.stderr)
        print("Install it with: pip install yt-dlp", file=sys.stderr)
        sys.exit(1)

    verbose = not args.quiet

    if args.playlist:
        if verbose:
            print(f"Downloading playlist from: {args.url}")
        files = download_playlist(
            args.url,
            output_dir=args.output,
            format_spec=args.format,
            max_downloads=args.max,
            verbose=verbose
        )
        if files:
            print(f"\nDownloaded {len(files)} videos to {args.output}")
        else:
            print("No videos were downloaded.", file=sys.stderr)
            sys.exit(1)
    else:
        if verbose:
            print(f"Downloading video from: {args.url}")
        result = download_video(
            args.url,
            output_dir=args.output,
            format_spec=args.format,
            extract_audio=args.audio_only,
            audio_format=args.audio_format,
            subtitles=args.subtitles,
            auto_subs=args.auto_subs,
            embed_subs=args.embed_subs,
            verbose=verbose,
            cookies_file=args.cookies
        )
        if not result:
            sys.exit(1)


if __name__ == '__main__':
    main()
