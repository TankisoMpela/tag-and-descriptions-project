#!/usr/bin/env python3
"""Create size-bounded JPEG delivery copies from canonical PNG visuals."""
from __future__ import annotations
import argparse
import re
from pathlib import Path
from PIL import Image

# Quality ladder, best first. 95 is the ceiling: measured on real 1536x1024
# composites they need q80-85 to fit the cap, so a higher rung rarely binds.
# Keep lower rungs for unusually detailed seller-supplied support art: the
# processor must preserve full dimensions and may use the 200–300 KB allowance
# before failing closed, but should still find a valid JPEG when q55 is too large.
QUALITY_LADDER = (95, 90, 85, 80, 75, 70, 65, 60, 55, 50, 45, 40, 35)

CANONICAL = re.compile(r"^(thumbnail_(?:main|alt)|promo_[0-9]+)\.png$", re.IGNORECASE)

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--quality", type=int, default=None,
                        help="Use one fixed JPEG quality instead of the size ladder")
    parser.add_argument("--max-bytes", type=int, default=500_000,
                        help="Hard byte ceiling; the highest fitting quality is preferred")
    parser.add_argument("--target-bytes", type=int, default=None,
                        help="Preferred byte target; if no quality fits, retry up to --max-bytes")
    parser.add_argument("--allow-over-max", action="store_true",
                        help="write the smallest quality rung if no JPEG fits --max-bytes")
    parser.add_argument("--max-dim", type=int, default=None,
                        help="Resize images so longest edge matches this pixel count (preserves aspect ratio)")
    args = parser.parse_args()
    if not args.source_dir.is_dir() or args.source_dir.resolve() == args.output_dir.resolve():
        raise SystemExit("Source and output directories must be different")
    if args.max_bytes < 1 or (args.target_bytes is not None and
                              (args.target_bytes < 1 or args.target_bytes > args.max_bytes)):
        raise SystemExit("--target-bytes must be positive and no greater than --max-bytes")
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
            def highest_fit(cap):
                lo, hi = 0, len(qualities) - 1
                chosen, smallest = None, None
                while lo <= hi:
                    middle = (lo + hi) // 2
                    buffer = BytesIO()
                    rgb.save(buffer, format="JPEG", quality=qualities[middle], optimize=True,
                             progressive=True, subsampling=2)
                    payload = buffer.getvalue()
                    if smallest is None or len(payload) < len(smallest[1]):
                        smallest = (qualities[middle], payload)
                    if len(payload) <= cap:
                        chosen = (qualities[middle], payload)
                        hi = middle - 1
                    else:
                        lo = middle + 1
                return chosen, smallest

            chosen = None
            if args.target_bytes is not None:
                chosen, _ = highest_fit(args.target_bytes)
            if chosen is None:
                chosen, smallest = highest_fit(args.max_bytes)
                if chosen is None:
                    assert smallest is not None
                    if not args.allow_over_max:
                        raise SystemExit(
                            f"{source.name}: could not reach {args.max_bytes} bytes even at "
                            f"quality {smallest[0]}; output not written"
                        )
                    chosen = smallest
            quality, payload = chosen
            destination.write_bytes(payload)
        target_status = ("" if args.target_bytes is None else
                         f", {'target met' if destination.stat().st_size <= args.target_bytes else 'within hard limit'}")
        over_max = " (above configured ceiling; best available quality saved)" if destination.stat().st_size > args.max_bytes else ""
        print(f"{source.name}: {source.stat().st_size} -> {destination.name}: "
              f"{destination.stat().st_size} bytes (quality {quality}, 4:2:0{target_status}){over_max}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
