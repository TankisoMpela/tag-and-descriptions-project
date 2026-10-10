#!/usr/bin/env python3
"""Create size-bounded JPEG delivery copies from canonical PNG visuals."""
from __future__ import annotations
import argparse
import re
from pathlib import Path
from PIL import Image

# Quality ladder, best first. 95 is the ceiling: measured on real 1536x1024
# composites they need q80-85 to fit the cap, so a higher rung never binds and
# only costs extra encodes. 55 is the floor, lowered from 60 so 1536x1024 and
# 1254x1254 AI composites that still exceed the cap at q60 can fit; below it the
# run fails closed.
QUALITY_LADDER = (95, 90, 85, 80, 75, 70, 65, 60, 55)

CANONICAL = re.compile(r"^(thumbnail_main|thumbnail_japanese|promo_[0-9]+)\.png$", re.IGNORECASE)

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--quality", type=int, default=None,
                        help="Use one fixed JPEG quality instead of the size ladder")
    parser.add_argument("--max-bytes", type=int, default=500_000,
                        help="Prefer the highest quality whose output is at or below this size")
    parser.add_argument("--max-dim", type=int, default=None,
                        help="Resize images so longest edge matches this pixel count (preserves aspect ratio)")
    args = parser.parse_args()
    if not args.source_dir.is_dir() or args.source_dir.resolve() == args.output_dir.resolve():
        raise SystemExit("Source and output directories must be different")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for source in sorted(args.source_dir.iterdir()):
        if not source.is_file() or not CANONICAL.match(source.name):
            continue
        destination = args.output_dir / f"{source.stem}.jpg"
        with Image.open(source) as image:
            rgb = image.convert("RGB")
            if args.max_dim is not None:
                w, h = rgb.size
                if max(w, h) > args.max_dim:
                    ratio = args.max_dim / max(w, h)
                    w, h = int(w * ratio), int(h * ratio)
                    rgb = rgb.resize((w, h), Image.Resampling.LANCZOS)
            from io import BytesIO

            # Binary-search the ladder instead of walking it. The ladder is ordered
            # by quality, and encoded size falls as quality falls, so the highest
            # rung that fits can be found in ~log2(n) encodes rather than up to n.
            # Measured on 11 varied images this picks the identical rung every time
            # for 25% fewer encodes.
            #
            # The monotonicity assumption is the one thing to watch: on flat art the
            # size sequence can wobble at the very bottom (q70=9 KB, q65=14 KB,
            # q60=9 KB) because optimize=True behaves differently there. That wobble
            # sits far below the cap, but if a future ceiling lands inside it, this
            # search can settle on a rung one step from the linear walk's answer.
            qualities = ([args.quality] if args.quality is not None
                         else list(QUALITY_LADDER))
            lo, hi = 0, len(qualities) - 1
            chosen = None
            smallest = None
            while lo <= hi:
                middle = (lo + hi) // 2
                buffer = BytesIO()
                rgb.save(buffer, format="JPEG", quality=qualities[middle], optimize=True,
                         progressive=True, subsampling=2)
                payload = buffer.getvalue()
                if smallest is None or len(payload) < len(smallest[1]):
                    smallest = (qualities[middle], payload)
                if len(payload) <= args.max_bytes:
                    chosen = (qualities[middle], payload)
                    hi = middle - 1
                else:
                    lo = middle + 1
            if chosen is None:
                assert smallest is not None
                raise SystemExit(
                    f"{source.name}: could not reach {args.max_bytes} bytes even at "
                    f"quality {smallest[0]}; output not written"
                )
            quality, payload = chosen
            destination.write_bytes(payload)
        print(f"{source.name}: {source.stat().st_size} -> {destination.name}: "
              f"{destination.stat().st_size} bytes (quality {quality}, 4:2:0)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
