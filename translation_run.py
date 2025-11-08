#!/usr/bin/env python3
"""
translation_run.py

Translate text, SRT files, or batch process multiple files.
Supports caching and multiple language pairs.

Usage examples:
  # Translate a single SRT file
  python translation_run.py --input movie.en.srt --output movie.es.srt --target-lang es --source-lang en

  # Translate text directly
  python translation_run.py --text "Hello world" --target-lang es

  # Translate with auto-detect source language
  python translation_run.py --input movie.srt --output movie.en.srt --target-lang en --source-lang auto

  # List supported languages
  python translation_run.py --list-languages

Notes:
 - Requires translation_helpers.py and deep-translator library
 - Caches translations for efficiency
"""
import argparse
import sys
from pathlib import Path

# Local helper (repo root)
import translation_helpers


def main():
    parser = argparse.ArgumentParser(
        prog="translation_run",
        description="Translate text or SRT files using Google Translate"
    )
    
    parser.add_argument(
        "--input",
        help="Input SRT file to translate"
    )
    parser.add_argument(
        "--output",
        help="Output SRT file path (required with --input)"
    )
    parser.add_argument(
        "--text",
        help="Direct text to translate (alternative to --input)"
    )
    parser.add_argument(
        "--target-lang",
        default="en",
        help="Target language code (default: en)"
    )
    parser.add_argument(
        "--source-lang",
        default="auto",
        help="Source language code or 'auto' for auto-detection (default: auto)"
    )
    parser.add_argument(
        "--cache-dir",
        default=None,
        help="Directory to cache translations (default: ./translation_cache)"
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable translation caching"
    )
    parser.add_argument(
        "--list-languages",
        action="store_true",
        help="List supported language codes and exit"
    )
    
    args = parser.parse_args()
    
    # Handle list languages
    if args.list_languages:
        print("Supported languages:")
        try:
            langs = translation_helpers.get_supported_languages()
            for code, name in sorted(langs.items()):
                print(f"  {code:10s} - {name}")
        except Exception as e:
            print(f"Error getting languages: {e}", file=sys.stderr)
            sys.exit(1)
        return
    
    # Validate arguments
    if not args.input and not args.text:
        parser.error("Either --input or --text must be provided")
    
    if args.input and not args.output:
        parser.error("--output is required when using --input")
    
    # Set cache directory
    cache_dir = Path(args.cache_dir) if args.cache_dir else Path("./translation_cache")
    use_cache = not args.no_cache
    
    # Handle direct text translation
    if args.text:
        try:
            print(f"Translating text from '{args.source_lang}' to '{args.target_lang}'...")
            result = translation_helpers.translate_text(
                args.text,
                target_lang=args.target_lang,
                source_lang=args.source_lang,
                cache_dir=cache_dir if use_cache else None,
                use_cache=use_cache
            )
            print(f"\nOriginal: {args.text}")
            print(f"Translation: {result}")
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        return
    
    # Handle SRT file translation
    if args.input:
        input_path = Path(args.input)
        output_path = Path(args.output)
        
        if not input_path.exists():
            print(f"Error: Input file not found: {input_path}", file=sys.stderr)
            sys.exit(1)
        
        try:
            print(f"Translating SRT file: {input_path}")
            print(f"  Source language: {args.source_lang}")
            print(f"  Target language: {args.target_lang}")
            print(f"  Output: {output_path}")
            print(f"  Cache: {'enabled' if use_cache else 'disabled'}")
            
            result_path = translation_helpers.translate_srt_file(
                input_path,
                output_path,
                target_lang=args.target_lang,
                source_lang=args.source_lang,
                cache_dir=cache_dir if use_cache else None,
                use_cache=use_cache
            )
            
            print(f"\n✓ Translation complete!")
            print(f"  Output file: {result_path}")
            if use_cache:
                print(f"  Cache directory: {cache_dir}")
                
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    main()
