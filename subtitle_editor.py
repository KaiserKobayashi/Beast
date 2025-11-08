#!/usr/bin/env python3
"""
subtitle_editor.py

Subtitle editing and enhancement module for post-processing Whisper transcriptions.
Provides tools for:
- Correcting timing issues
- Fixing text errors
- Splitting/merging subtitles
- Adding speaker labels
- Adjusting subtitle length and reading speed
- Format conversion (SRT, VTT, etc.)
- Batch editing operations

Works with SRT, VTT, and other subtitle formats.
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import timedelta


@dataclass
class Subtitle:
    """Represents a single subtitle entry."""
    index: int
    start: float  # seconds
    end: float    # seconds
    text: str
    
    def duration(self) -> float:
        """Get duration in seconds."""
        return self.end - self.start
    
    def char_count(self) -> int:
        """Get character count."""
        return len(self.text)
    
    def reading_speed(self) -> float:
        """Get reading speed in characters per second."""
        duration = self.duration()
        if duration <= 0:
            return 0
        return self.char_count() / duration
    
    def to_srt(self) -> str:
        """Convert to SRT format."""
        start_time = self._format_time(self.start, srt=True)
        end_time = self._format_time(self.end, srt=True)
        return f"{self.index}\n{start_time} --> {end_time}\n{self.text}\n"
    
    def to_vtt(self) -> str:
        """Convert to WebVTT format."""
        start_time = self._format_time(self.start, srt=False)
        end_time = self._format_time(self.end, srt=False)
        return f"{start_time} --> {end_time}\n{self.text}\n"
    
    @staticmethod
    def _format_time(seconds: float, srt: bool = True) -> str:
        """Format time for subtitle files."""
        td = timedelta(seconds=seconds)
        hours = int(td.total_seconds() // 3600)
        minutes = int((td.total_seconds() % 3600) // 60)
        secs = int(td.total_seconds() % 60)
        millis = int((td.total_seconds() % 1) * 1000)
        
        if srt:
            return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
        else:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


class SubtitleEditor:
    """Editor for subtitle files with various enhancement operations."""
    
    TIMECODE_RE_SRT = re.compile(
        r'(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})'
    )
    TIMECODE_RE_VTT = re.compile(
        r'(\d{2}):(\d{2}):(\d{2})\.(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})\.(\d{3})'
    )
    
    def __init__(self, subtitles: Optional[List[Subtitle]] = None):
        self.subtitles = subtitles or []
    
    @classmethod
    def from_file(cls, path: str) -> 'SubtitleEditor':
        """Load subtitles from file (auto-detect format)."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Subtitle file not found: {path}")
        
        content = path.read_text(encoding='utf-8', errors='replace')
        
        # Detect format
        if path.suffix.lower() == '.vtt' or content.startswith('WEBVTT'):
            return cls._parse_vtt(content)
        else:
            return cls._parse_srt(content)
    
    @classmethod
    def _parse_srt(cls, content: str) -> 'SubtitleEditor':
        """Parse SRT format."""
        subtitles = []
        lines = [l.rstrip('\n\r') for l in content.split('\n')]
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
            
            # Try to parse index
            if line.isdigit():
                index = int(line)
                i += 1
                
                # Parse timecode
                if i < len(lines):
                    match = cls.TIMECODE_RE_SRT.search(lines[i])
                    if match:
                        start = cls._time_to_seconds(
                            int(match.group(1)), int(match.group(2)),
                            int(match.group(3)), int(match.group(4))
                        )
                        end = cls._time_to_seconds(
                            int(match.group(5)), int(match.group(6)),
                            int(match.group(7)), int(match.group(8))
                        )
                        i += 1
                        
                        # Collect text
                        text_lines = []
                        while i < len(lines) and lines[i].strip():
                            text_lines.append(lines[i])
                            i += 1
                        
                        text = '\n'.join(text_lines).strip()
                        if text:
                            subtitles.append(Subtitle(index, start, end, text))
                    else:
                        i += 1
                else:
                    break
            else:
                i += 1
        
        return cls(subtitles)
    
    @classmethod
    def _parse_vtt(cls, content: str) -> 'SubtitleEditor':
        """Parse WebVTT format."""
        subtitles = []
        lines = [l.rstrip('\n\r') for l in content.split('\n')]
        
        index = 1
        i = 0
        
        # Skip header
        while i < len(lines) and not cls.TIMECODE_RE_VTT.search(lines[i]):
            i += 1
        
        while i < len(lines):
            line = lines[i]
            
            # Parse timecode
            match = cls.TIMECODE_RE_VTT.search(line)
            if match:
                start = cls._time_to_seconds(
                    int(match.group(1)), int(match.group(2)),
                    int(match.group(3)), int(match.group(4))
                )
                end = cls._time_to_seconds(
                    int(match.group(5)), int(match.group(6)),
                    int(match.group(7)), int(match.group(8))
                )
                i += 1
                
                # Collect text
                text_lines = []
                while i < len(lines) and lines[i].strip():
                    text_lines.append(lines[i])
                    i += 1
                
                text = '\n'.join(text_lines).strip()
                if text:
                    subtitles.append(Subtitle(index, start, end, text))
                    index += 1
            else:
                i += 1
        
        return cls(subtitles)
    
    @staticmethod
    def _time_to_seconds(hours: int, minutes: int, seconds: int, millis: int) -> float:
        """Convert time components to seconds."""
        return hours * 3600 + minutes * 60 + seconds + millis / 1000.0
    
    def save(self, path: str, format: str = 'srt'):
        """Save subtitles to file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        if format.lower() == 'vtt':
            content = "WEBVTT\n\n" + "\n".join(sub.to_vtt() for sub in self.subtitles)
        else:
            content = "\n".join(sub.to_srt() for sub in self.subtitles)
        
        path.write_text(content, encoding='utf-8')
        print(f"✓ Saved {len(self.subtitles)} subtitles to: {path}")
    
    def adjust_timing(self, offset_seconds: float):
        """Shift all subtitle timings by offset (can be negative)."""
        print(f"Adjusting timing by {offset_seconds:+.2f}s")
        for sub in self.subtitles:
            sub.start = max(0, sub.start + offset_seconds)
            sub.end = max(sub.start, sub.end + offset_seconds)
    
    def fix_overlaps(self, min_gap: float = 0.1):
        """Fix overlapping subtitles by adjusting end times."""
        print("Fixing overlapping subtitles...")
        fixed = 0
        
        for i in range(len(self.subtitles) - 1):
            current = self.subtitles[i]
            next_sub = self.subtitles[i + 1]
            
            if current.end > next_sub.start:
                # Overlap detected, adjust current subtitle end time
                current.end = max(current.start, next_sub.start - min_gap)
                fixed += 1
        
        print(f"Fixed {fixed} overlapping subtitles")
    
    def adjust_reading_speed(self, max_chars_per_second: float = 20.0, min_duration: float = 1.0):
        """Adjust subtitle durations based on reading speed."""
        print(f"Adjusting reading speed (max {max_chars_per_second} chars/sec, min {min_duration}s)")
        adjusted = 0
        
        for i, sub in enumerate(self.subtitles):
            char_count = sub.char_count()
            min_needed_duration = max(min_duration, char_count / max_chars_per_second)
            
            if sub.duration() < min_needed_duration:
                # Extend duration
                extra_time = min_needed_duration - sub.duration()
                sub.end += extra_time
                
                # Make sure we don't overlap with next subtitle
                if i < len(self.subtitles) - 1:
                    next_sub = self.subtitles[i + 1]
                    if sub.end > next_sub.start:
                        sub.end = next_sub.start - 0.1
                
                adjusted += 1
        
        print(f"Adjusted {adjusted} subtitles for better readability")
    
    def merge_short_subtitles(self, min_duration: float = 1.0, max_chars: int = 80):
        """Merge very short subtitles with adjacent ones."""
        print(f"Merging short subtitles (< {min_duration}s)")
        
        i = 0
        merged_count = 0
        while i < len(self.subtitles) - 1:
            current = self.subtitles[i]
            next_sub = self.subtitles[i + 1]
            
            # Check if current is too short and merging won't exceed max chars
            if (current.duration() < min_duration and
                current.char_count() + next_sub.char_count() + 1 <= max_chars):
                # Merge with next
                current.text = current.text + " " + next_sub.text
                current.end = next_sub.end
                self.subtitles.pop(i + 1)
                merged_count += 1
            else:
                i += 1
        
        # Reindex
        for idx, sub in enumerate(self.subtitles, 1):
            sub.index = idx
        
        print(f"Merged {merged_count} short subtitles")
    
    def split_long_subtitles(self, max_chars: int = 80):
        """Split overly long subtitles."""
        print(f"Splitting long subtitles (> {max_chars} chars)")
        
        new_subtitles = []
        split_count = 0
        
        for sub in self.subtitles:
            if sub.char_count() <= max_chars:
                new_subtitles.append(sub)
            else:
                # Split text
                words = sub.text.split()
                chunks = []
                current_chunk = []
                current_length = 0
                
                for word in words:
                    if current_length + len(word) + 1 <= max_chars:
                        current_chunk.append(word)
                        current_length += len(word) + 1
                    else:
                        if current_chunk:
                            chunks.append(' '.join(current_chunk))
                        current_chunk = [word]
                        current_length = len(word)
                
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                
                # Create new subtitles with proportional timing
                duration_per_char = sub.duration() / sub.char_count()
                current_start = sub.start
                
                for chunk in chunks:
                    chunk_duration = len(chunk) * duration_per_char
                    chunk_end = min(current_start + chunk_duration, sub.end)
                    
                    new_subtitles.append(Subtitle(
                        index=len(new_subtitles) + 1,
                        start=current_start,
                        end=chunk_end,
                        text=chunk
                    ))
                    current_start = chunk_end
                
                split_count += 1
        
        self.subtitles = new_subtitles
        
        # Reindex
        for idx, sub in enumerate(self.subtitles, 1):
            sub.index = idx
        
        print(f"Split {split_count} long subtitles into {len(self.subtitles)} total")
    
    def remove_empty(self):
        """Remove empty or whitespace-only subtitles."""
        original_count = len(self.subtitles)
        self.subtitles = [sub for sub in self.subtitles if sub.text.strip()]
        
        # Reindex
        for idx, sub in enumerate(self.subtitles, 1):
            sub.index = idx
        
        removed = original_count - len(self.subtitles)
        if removed > 0:
            print(f"Removed {removed} empty subtitles")
    
    def auto_enhance(self):
        """Apply automatic enhancements for better quality."""
        print("\n" + "="*60)
        print("AUTO-ENHANCING SUBTITLES")
        print("="*60)
        
        original_count = len(self.subtitles)
        
        # 1. Remove empty subtitles
        self.remove_empty()
        
        # 2. Fix overlaps
        self.fix_overlaps()
        
        # 3. Merge very short subtitles
        self.merge_short_subtitles(min_duration=0.8, max_chars=80)
        
        # 4. Split overly long subtitles
        self.split_long_subtitles(max_chars=80)
        
        # 5. Adjust reading speed
        self.adjust_reading_speed(max_chars_per_second=20.0)
        
        # 6. Fix any new overlaps created by adjustments
        self.fix_overlaps()
        
        print(f"\nSummary: {original_count} → {len(self.subtitles)} subtitles")
        print("="*60)
    
    def get_statistics(self) -> Dict:
        """Get statistics about the subtitles."""
        if not self.subtitles:
            return {}
        
        durations = [sub.duration() for sub in self.subtitles]
        char_counts = [sub.char_count() for sub in self.subtitles]
        reading_speeds = [sub.reading_speed() for sub in self.subtitles if sub.duration() > 0]
        
        total_duration = sum(durations)
        
        return {
            'count': len(self.subtitles),
            'total_duration': total_duration,
            'avg_duration': sum(durations) / len(durations),
            'min_duration': min(durations),
            'max_duration': max(durations),
            'avg_char_count': sum(char_counts) / len(char_counts),
            'min_char_count': min(char_counts),
            'max_char_count': max(char_counts),
            'avg_reading_speed': sum(reading_speeds) / len(reading_speeds) if reading_speeds else 0,
        }
    
    def print_statistics(self):
        """Print statistics about the subtitles."""
        stats = self.get_statistics()
        
        if not stats:
            print("No subtitles loaded")
            return
        
        print("\nSubtitle Statistics:")
        print("="*40)
        print(f"Total subtitles: {stats['count']}")
        print(f"Total duration: {stats['total_duration']:.1f}s ({stats['total_duration']/60:.1f}m)")
        print(f"\nDuration per subtitle:")
        print(f"  Average: {stats['avg_duration']:.2f}s")
        print(f"  Range: {stats['min_duration']:.2f}s - {stats['max_duration']:.2f}s")
        print(f"\nCharacters per subtitle:")
        print(f"  Average: {stats['avg_char_count']:.1f}")
        print(f"  Range: {stats['min_char_count']} - {stats['max_char_count']}")
        print(f"\nReading speed: {stats['avg_reading_speed']:.1f} chars/sec")
        print("="*40)


def main():
    """CLI entry point for subtitle editing."""
    parser = argparse.ArgumentParser(
        prog="subtitle_editor",
        description="Edit and enhance subtitle files (post-processing for Whisper transcriptions)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-enhance subtitles (recommended after Whisper)
  python subtitle_editor.py enhance --input subtitles.srt --output fixed.srt

  # Shift timing by 2 seconds forward
  python subtitle_editor.py adjust --input subtitles.srt --output adjusted.srt --offset 2.0

  # Convert SRT to WebVTT
  python subtitle_editor.py convert --input subtitles.srt --output subtitles.vtt --format vtt

  # Get statistics about subtitles
  python subtitle_editor.py stats --input subtitles.srt

  # Fix reading speed issues
  python subtitle_editor.py reading-speed --input subtitles.srt --output readable.srt --max-cps 18

Common workflow after Whisper:
  1. python audio_workflow.py transcribe --input audio.mp3 --output results/
  2. python subtitle_editor.py enhance --input results/transcription/*.srt --output final.srt
        """,
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Enhance command
    enhance_parser = subparsers.add_parser('enhance', help='Auto-enhance subtitles (recommended)')
    enhance_parser.add_argument('--input', required=True, help='Input subtitle file')
    enhance_parser.add_argument('--output', required=True, help='Output subtitle file')
    enhance_parser.add_argument('--format', choices=['srt', 'vtt'], default='srt', help='Output format')
    
    # Adjust timing command
    adjust_parser = subparsers.add_parser('adjust', help='Adjust subtitle timing')
    adjust_parser.add_argument('--input', required=True, help='Input subtitle file')
    adjust_parser.add_argument('--output', required=True, help='Output subtitle file')
    adjust_parser.add_argument('--offset', type=float, required=True, help='Time offset in seconds (can be negative)')
    adjust_parser.add_argument('--format', choices=['srt', 'vtt'], default='srt', help='Output format')
    
    # Reading speed command
    speed_parser = subparsers.add_parser('reading-speed', help='Adjust for comfortable reading speed')
    speed_parser.add_argument('--input', required=True, help='Input subtitle file')
    speed_parser.add_argument('--output', required=True, help='Output subtitle file')
    speed_parser.add_argument('--max-cps', type=float, default=20.0, help='Max characters per second (default: 20)')
    speed_parser.add_argument('--format', choices=['srt', 'vtt'], default='srt', help='Output format')
    
    # Convert command
    convert_parser = subparsers.add_parser('convert', help='Convert subtitle format')
    convert_parser.add_argument('--input', required=True, help='Input subtitle file')
    convert_parser.add_argument('--output', required=True, help='Output subtitle file')
    convert_parser.add_argument('--format', required=True, choices=['srt', 'vtt'], help='Output format')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show subtitle statistics')
    stats_parser.add_argument('--input', required=True, help='Input subtitle file')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        if args.command == 'enhance':
            print(f"Loading subtitles from: {args.input}")
            editor = SubtitleEditor.from_file(args.input)
            editor.auto_enhance()
            editor.save(args.output, format=args.format)
            editor.print_statistics()
        
        elif args.command == 'adjust':
            print(f"Loading subtitles from: {args.input}")
            editor = SubtitleEditor.from_file(args.input)
            editor.adjust_timing(args.offset)
            editor.save(args.output, format=args.format)
        
        elif args.command == 'reading-speed':
            print(f"Loading subtitles from: {args.input}")
            editor = SubtitleEditor.from_file(args.input)
            editor.adjust_reading_speed(max_chars_per_second=args.max_cps)
            editor.fix_overlaps()
            editor.save(args.output, format=args.format)
        
        elif args.command == 'convert':
            print(f"Loading subtitles from: {args.input}")
            editor = SubtitleEditor.from_file(args.input)
            editor.save(args.output, format=args.format)
        
        elif args.command == 'stats':
            print(f"Loading subtitles from: {args.input}")
            editor = SubtitleEditor.from_file(args.input)
            editor.print_statistics()
        
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
