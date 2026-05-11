#!/usr/bin/env python3
"""Parse HwAsic::Feature enum and output feature ID mapping table.

This tool is bundled with the asic feature override gflag patch so that
users can look up numeric feature IDs for --asic_feature_support_overrides.

Usage (from fboss repo root):
    python fboss/oss/scripts/parse_feature_enum.py
    python fboss/oss/scripts/parse_feature_enum.py --filter UDF
    python fboss/oss/scripts/parse_feature_enum.py --filter "73|126"
    python fboss/oss/scripts/parse_feature_enum.py --format csv
    python fboss/oss/scripts/parse_feature_enum.py --format json

No arguments needed — automatically locates HwAsic.h relative to script.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

# Auto-detect HwAsic.h relative to this script location
SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_HEADER = SCRIPT_DIR.parent.parent / "agent" / "hw" / "switch_asics" / "HwAsic.h"


def parse_feature_enum(header_path: Path) -> list[tuple[int, str]]:
    """Parse Feature enum from HwAsic.h, return list of (id, name) tuples."""
    content = header_path.read_text(encoding="utf-8")

    enum_match = re.search(r"enum\s+class\s+Feature\s*\{", content)
    if not enum_match:
        print("ERROR: Could not find 'enum class Feature {' in file.", file=sys.stderr)
        sys.exit(1)

    enum_start = enum_match.end()
    brace_depth = 1
    pos = enum_start
    while pos < len(content) and brace_depth > 0:
        if content[pos] == "{":
            brace_depth += 1
        elif content[pos] == "}":
            brace_depth -= 1
        pos += 1
    enum_body = content[enum_start : pos - 1]

    # Remove comments
    enum_body = re.sub(r"/\*.*?\*/", "", enum_body, flags=re.DOTALL)
    enum_body = re.sub(r"//[^\n]*", "", enum_body)

    features = []
    feature_id = 0
    for raw_line in enum_body.split("\n"):
        stripped = raw_line.strip().rstrip(",")
        if not stripped:
            continue
        match = re.match(r"^([A-Z][A-Za-z0-9_]+)\s*(?:=\s*(\d+))?$", stripped)
        if match:
            name = match.group(1)
            if match.group(2):
                feature_id = int(match.group(2))
            features.append((feature_id, name))
            feature_id += 1

    return features


def main():
    parser = argparse.ArgumentParser(
        description="Parse HwAsic::Feature enum and output ID mapping."
    )
    parser.add_argument(
        "header",
        nargs="?",
        default=None,
        help="Path to HwAsic.h (auto-detected if not provided)",
    )
    parser.add_argument(
        "--filter", default=None, help="Regex pattern to filter feature names or IDs"
    )
    parser.add_argument(
        "--format",
        choices=["table", "csv", "json"],
        default="table",
        help="Output format (default: table)",
    )
    args = parser.parse_args()

    header_path = Path(args.header) if args.header else DEFAULT_HEADER
    if not header_path.exists():
        print(f"ERROR: {header_path} not found.", file=sys.stderr)
        print("Run from fboss repo root or provide path as argument.", file=sys.stderr)
        sys.exit(1)

    features = parse_feature_enum(header_path)

    if not features:
        print("ERROR: No features found in enum.", file=sys.stderr)
        sys.exit(1)

    # Apply filter
    if args.filter:
        pattern = re.compile(args.filter, re.IGNORECASE)
        features = [
            (fid, name)
            for fid, name in features
            if pattern.search(name) or pattern.search(str(fid))
        ]

    # Output
    if args.format == "json":
        output = [{"id": fid, "name": name} for fid, name in features]
        print(json.dumps(output, indent=2))
    elif args.format == "csv":
        print("id,name")
        for fid, name in features:
            print(f"{fid},{name}")
    else:
        print(f"{'ID':<6} {'Feature Name'}")
        print(f"{'--':<6} {'------------'}")
        for fid, name in features:
            print(f"{fid:<6} {name}")
        print(f"\nTotal: {len(features)} features")
        print(
            "\nUsage: --asic_feature_support_overrides=<ID>=true|false[,<ID>=false,...]"
        )
        print("Example: --asic_feature_support_overrides=73=false,126=false")


if __name__ == "__main__":
    main()
