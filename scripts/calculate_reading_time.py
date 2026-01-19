#!/usr/bin/env python3
"""
Calculate word counts and reading times for documentation files.

Uses standard reading speed of 200-250 words per minute for technical content.
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path


def count_words_in_text(text: str) -> int:
    """Count words in text, excluding HTML tags and code blocks."""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove code blocks (fenced)
    text = re.sub(r'```[\s\S]*?```', '', text)
    # Remove inline code
    text = re.sub(r'`[^`]+`', '', text)
    # Remove URLs
    text = re.sub(r'https?://\S+', '', text)
    # Split and count non-empty words
    words = [w for w in text.split() if w.strip()]
    return len(words)


def estimate_reading_time(word_count: int, wpm: int = 220) -> dict:
    """
    Estimate reading time based on word count.

    Uses 220 WPM as default for technical content (slower than average 250 WPM
    due to complexity of material).
    """
    minutes = word_count / wpm
    hours = int(minutes // 60)
    remaining_minutes = int(minutes % 60)

    if hours > 0:
        time_str = f"{hours} hr {remaining_minutes} min"
    elif minutes < 1:
        time_str = "< 1 min"
    else:
        time_str = f"{int(round(minutes))} min"

    return {
        "word_count": word_count,
        "minutes": round(minutes, 1),
        "display": time_str,
        "wpm_used": wpm
    }


def analyze_file(filepath: str) -> dict:
    """Analyze a single file for word count and reading time."""
    with open(filepath, encoding='utf-8') as f:
        content = f.read()

    word_count = count_words_in_text(content)
    reading_time = estimate_reading_time(word_count)

    # Get file stats
    stat = os.stat(filepath)

    return {
        "file": filepath,
        "filename": os.path.basename(filepath),
        "word_count": word_count,
        "reading_time": reading_time,
        "file_size_bytes": stat.st_size,
        "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
    }


def analyze_directory(directory: str, extensions: list = None) -> dict:
    """Analyze all matching files in a directory."""
    if extensions is None:
        extensions = ['.html', '.md', '.txt']

    results = {
        "directory": directory,
        "analyzed_at": datetime.now().isoformat(),
        "files": [],
        "totals": {
            "file_count": 0,
            "total_words": 0,
            "total_reading_time_minutes": 0
        }
    }

    path = Path(directory)
    if not path.exists():
        print(f"Directory not found: {directory}", file=sys.stderr)
        return results

    for ext in extensions:
        for filepath in path.rglob(f"*{ext}"):
            analysis = analyze_file(str(filepath))
            results["files"].append(analysis)
            results["totals"]["file_count"] += 1
            results["totals"]["total_words"] += analysis["word_count"]
            results["totals"]["total_reading_time_minutes"] += analysis["reading_time"]["minutes"]

    # Calculate total reading time display
    total_mins = results["totals"]["total_reading_time_minutes"]
    hours = int(total_mins // 60)
    mins = int(total_mins % 60)
    if hours > 0:
        results["totals"]["total_reading_time_display"] = f"{hours} hr {mins} min"
    else:
        results["totals"]["total_reading_time_display"] = f"{int(round(total_mins))} min"

    return results


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Calculate word counts and reading times for documentation files."
    )
    parser.add_argument(
        "path",
        help="File or directory to analyze"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )
    parser.add_argument(
        "--wpm",
        type=int,
        default=220,
        help="Words per minute for reading time calculation (default: 220)"
    )

    args = parser.parse_args()

    path = Path(args.path)

    if path.is_file():
        result = analyze_file(str(path))
        result["reading_time"] = estimate_reading_time(result["word_count"], args.wpm)
    elif path.is_dir():
        result = analyze_directory(str(path))
    else:
        print(f"Path not found: {args.path}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if path.is_file():
            print(f"File: {result['filename']}")
            print(f"Word Count: {result['word_count']:,}")
            print(f"Reading Time: {result['reading_time']['display']}")
            print(f"File Size: {result['file_size_bytes']:,} bytes")
        else:
            print(f"Directory: {result['directory']}")
            print(f"Files Analyzed: {result['totals']['file_count']}")
            print(f"Total Words: {result['totals']['total_words']:,}")
            print(f"Total Reading Time: {result['totals']['total_reading_time_display']}")
            print()
            print("Individual Files:")
            for f in sorted(result["files"], key=lambda x: x["word_count"], reverse=True):
                print(f"  {f['filename']}: {f['word_count']:,} words ({f['reading_time']['display']})")


if __name__ == "__main__":
    main()
