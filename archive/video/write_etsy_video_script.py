#!/usr/bin/env python3
"""Write a human-readable Etsy video script from a validated scene config."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=960)
    args = parser.parse_args()

    try:
        config = json.loads(args.config.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"showcase config not found: {args.config}")
    except json.JSONDecodeError as error:
        raise SystemExit(f"invalid showcase config JSON: {error}")

    segments = config.get("segments") if isinstance(config, dict) else None
    if not isinstance(segments, list) or len(segments) != 5:
        raise SystemExit("Etsy script requires exactly five showcase segments")
    for index, segment in enumerate(segments):
        if not isinstance(segment, dict) or not isinstance(segment.get("text"), str) or not segment["text"].strip():
            raise SystemExit(f"scene {index + 1} has no text")
        if segment.get("seconds") != 7:
            raise SystemExit(f"scene {index + 1} must last 7 seconds")
    if segments[4]["text"] != args.name:
        raise SystemExit("scene 5 must contain exactly the final font name")

    lines = [
        "Etsy Font Video Script",
        f"Canvas: {args.width}x{args.height} (2:1)",
        "Frame rate: 30 FPS",
        "Duration: 35 seconds",
        "",
    ]
    for index, segment in enumerate(segments):
        start = index * 7
        end = start + 7
        lines.extend([f"Scene {index + 1} ({start // 60:02d}:{start % 60:02d}-{end // 60:02d}:{end % 60:02d}):", segment["text"], ""])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote Etsy video script: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
