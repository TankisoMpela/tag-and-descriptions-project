#!/usr/bin/env python3
"""Render a font showcase video from a validated scene config.

Agent 13 is required to produce two showcase videos — the main 1920x1080 (16:9)
listing video and the 1920x960 (2:1) Etsy video — but no renderer was ever added
to `bin/`, so every run improvised an ffmpeg chain. That made the output
non-reproducible and wasted tokens rediscovering the same pipeline.

This is that pipeline, made deterministic. It reads the same
`showcase.config.json` shape the rest of the workflow already uses:

    {"segments": [{"text": "...", "seconds": 7, "fontSize": 220,
                   "charactersPerSecond": 10}, ... 5 segments]}

`write_etsy_video_script.py` documents the contract: exactly five segments, each
seven seconds, 30 fps, 35 seconds total, and scene 5 carrying exactly the font
name. The same rules are enforced here, so a config that renders is a config the
script writer accepts.

Text is revealed typewriter-style at `charactersPerSecond`, then holds for the
rest of the scene, on the project's dark canvas (background `#111111`, type
`#F4EEE7`). Frames are streamed straight into ffmpeg, so nothing large is
written to disk.

Usage:
  python3 bin/render_font_showcase.py \
    --config outputs/font-preparation/082-restrained-flourish/video/showcase.config.json \
    --font   outputs/font-preparation/082-restrained-flourish/Restrained-Flourish/Restrained-Flourish-Regular.otf \
    --output outputs/font-preparation/082-restrained-flourish/video/restrained-flourish-font-showcase.mp4

  # 2:1 Etsy variant
  python3 bin/render_font_showcase.py --config .../etsy-showcase.config.json --font ... \
    --width 1920 --height 960 --output .../etsy-font-showcase.mp4
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BACKGROUND = (17, 17, 17)
INK = (244, 238, 231)
SCENES = 5
SCENE_SECONDS = 7
FPS = 30
LINE_SPACING = 1.25
MARGIN = 0.08  # fraction of canvas width kept clear on each side


def load_config(path: Path) -> dict:
    if not path.is_file():
        sys.exit(f"error: config not found: {path}")
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        sys.exit(f"error: invalid showcase config JSON: {error}")
    segments = config.get("segments") if isinstance(config, dict) else None
    if not isinstance(segments, list) or len(segments) != SCENES:
        sys.exit(f"error: config must contain exactly {SCENES} segments")
    for index, segment in enumerate(segments, start=1):
        if not isinstance(segment, dict):
            sys.exit(f"error: scene {index} is not an object")
        text = segment.get("text")
        if not isinstance(text, str) or not text.strip():
            sys.exit(f"error: scene {index} has no text")
        if segment.get("seconds") != SCENE_SECONDS:
            sys.exit(f"error: scene {index} must last {SCENE_SECONDS} seconds")
        if not isinstance(segment.get("charactersPerSecond"), (int, float)):
            sys.exit(f"error: scene {index} needs a numeric charactersPerSecond")
        if not isinstance(segment.get("fontSize"), (int, float)):
            sys.exit(f"error: scene {index} needs a numeric fontSize")
    return config


def resolve_font(explicit: Path | None, config_path: Path, font_name: str) -> Path:
    if explicit is not None:
        if not explicit.is_file():
            sys.exit(f"error: font not found: {explicit}")
        return explicit
    # Look next to the video dir: <prep>/{WinningName}/{WinningName}-Regular.{otf,ttf}
    prep = config_path.parent.parent
    candidates = sorted(
        p for p in prep.rglob("*") if p.suffix.lower() in {".otf", ".ttf"}
    )
    if not candidates:
        sys.exit(f"error: no .otf/.ttf found under {prep}; pass --font")
    slug = font_name.replace(" ", "-").casefold()
    preferred = [p for p in candidates if slug in p.name.casefold() and "italic" not in p.name.casefold()]
    return preferred[0] if preferred else candidates[0]


def fit_font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size=size)


def wrap_to_width(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    """Honour explicit newlines, then wrap each paragraph to the canvas."""
    lines: list[str] = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        current = words[0]
        for word in words[1:]:
            trial = f"{current} {word}"
            if draw.textlength(trial, font=font) <= max_width:
                current = trial
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines


def visible_count(text: str, elapsed: float, cps: float) -> int:
    """Characters revealed so far at `cps`, clamped to the scene text."""
    return max(0, min(len(text), int(elapsed * cps)))


def render_segment(
    text: str, font_path: Path, font_size: int, cps: float, width: int, height: int
) -> bytes:
    """Yield the scene's frames as raw RGB, reusing the previous frame while idle."""
    canvas = Image.new("RGB", (width, height), BACKGROUND)
    draw = ImageDraw.Draw(canvas)
    font = fit_font(font_path, font_size)
    max_width = int(width * (1 - 2 * MARGIN))

    # Shrink until every wrapped line fits the canvas, so nothing is ever clipped.
    size = font_size
    while size > 12:
        font = fit_font(font_path, size)
        lines = wrap_to_width(draw, text, font, max_width)
        line_height = font_size_for_line(font)
        total = line_height * len(lines)
        widest = max((draw.textlength(line, font=font) for line in lines), default=0)
        if total <= height * (1 - 2 * MARGIN) and widest <= max_width:
            break
        size = int(size * 0.94)

    line_height = font_size_for_line(font)
    block_height = line_height * len(lines)
    start_y = (height - block_height) / 2

    total_frames = SCENE_SECONDS * FPS
    last_shown = -1
    last_bytes: bytes | None = None
    for frame in range(total_frames):
        shown = visible_count(text, frame / FPS, cps)
        # Redraw only when the reveal count changes; otherwise reuse the frame.
        if last_bytes is not None and shown == last_shown:
            yield last_bytes
            continue
        canvas.paste(BACKGROUND, (0, 0, width, height))
        remaining = shown
        y = start_y
        for line in lines:
            if remaining <= 0:
                break
            chunk = line[:remaining]
            remaining -= min(remaining, len(line))
            if chunk:
                text_width = draw.textlength(chunk, font=font)
                draw.text(((width - text_width) / 2, y), chunk, font=font, fill=INK)
            y += line_height
        last_shown = shown
        last_bytes = canvas.tobytes()
        yield last_bytes


def font_size_for_line(font) -> float:
    ascent, descent = font.getmetrics()
    return (ascent + descent) * LINE_SPACING


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Render a font showcase video from a scene config.")
    ap.add_argument("--config", type=Path, required=True, help="showcase.config.json")
    ap.add_argument("--font", type=Path, default=None, help="OTF/TTF to render the copy in")
    ap.add_argument("--output", type=Path, required=True, help="destination .mp4")
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--crf", type=int, default=20, help="x264 quality (lower is better)")
    ap.add_argument(
        "--audio",
        type=Path,
        default=None,
        help="optional audio file to mux in; omit for a silent video",
    )
    ap.add_argument("--dry-run", action="store_true", help="validate and print the plan only")
    args = ap.parse_args(argv)

    config = load_config(args.config)
    segments = config["segments"]
    font_name = config.get("fontName") or segments[-1]["text"].strip()
    if segments[-1]["text"].strip() != font_name:
        sys.exit("error: scene 5 must contain exactly the font name")
    font_path = resolve_font(args.font, args.config, font_name)

    duration = SCENES * SCENE_SECONDS
    print(
        f"showcase: {font_name}\n"
        f"  config   {args.config}\n"
        f"  font     {font_path}\n"
        f"  canvas   {args.width}x{args.height} @ {FPS}fps, {duration}s\n"
        f"  output   {args.output}"
    )
    if args.dry_run:
        for index, segment in enumerate(segments, start=1):
            print(f"  scene {index}: {segment['seconds']}s  cps={segment['charactersPerSecond']}  {segment['text']!r}")
        return 0

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        sys.exit("error: ffmpeg not found on PATH")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{args.width}x{args.height}", "-r", str(FPS), "-i", "-",
    ]
    if args.audio is not None:
        if not args.audio.is_file():
            sys.exit(f"error: audio not found: {args.audio}")
        command += ["-i", str(args.audio), "-c:a", "aac", "-b:a", "192k", "-shortest"]
    command += [
        "-c:v", "libx264", "-preset", "medium", "-crf", str(args.crf),
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(args.output),
    ]

    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    assert process.stdin is not None
    written = 0
    try:
        for segment in segments:
            for frame in render_segment(
                segment["text"], font_path, int(segment["fontSize"]),
                float(segment["charactersPerSecond"]), args.width, args.height,
            ):
                process.stdin.write(frame)
                written += 1
        process.stdin.close()
    except BrokenPipeError:
        pass
    finally:
        code = process.wait()

    if code != 0:
        sys.exit(f"error: ffmpeg exited {code}")
    expected = SCENES * SCENE_SECONDS * FPS
    if written != expected:
        sys.exit(f"error: wrote {written} frames, expected {expected}")
    print(f"  wrote {written} frames -> {args.output} ({args.output.stat().st_size / 1024 / 1024:.1f} MB)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        sys.exit(0)
