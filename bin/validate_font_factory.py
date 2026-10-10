#!/usr/bin/env python3
"""Validate `font-factory/fonts/` staging hygiene.

Walks every top-level font directory under `font-factory/fonts/` and flags two
failure classes that have bitten the pipeline before:

1. **Pathological space-joined slug** — a directory whose name is a
   concatenation of many independent font names (e.g.
   `arcshift avelisse braewick ... walljam`). Legitimate multi-word font slugs
   are normally 2–3 tokens ("Lost Contact", "Old Norse"); a slug with 5+ space
   separated tokens is almost certainly a shell-quoting bug.

2. **Stray raster reference in a font root** — a `.png/.jpg/.jpeg/.webp/.avif`
   file sitting directly in the font's own directory. Raster stage inputs
   belong under `visual-references/`; approved rasters belong under
   `prepared_visuals/`. A raster loose in the root is a staging mistake.

Exit code is 0 only when no violations are found (with `--strict`, otherwise
warnings are reported but exit stays 0).

This is a staging-hygiene check for the font-factory workspace; it is not a
marketplace listing QA gate and never inspects font binaries or packages.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FONTS = ROOT / "font-factory" / "fonts"

RASTER = {".png", ".jpg", ".jpeg", ".webp", ".avif"}
MAX_TOKENS = 5  # slugs with >= this many space-separated tokens are pathological


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--strict", action="store_true",
                    help="treat warnings as failures (exit 1)")
    args = ap.parse_args()

    if not FONTS.exists():
        print(f"[OK] fonts directory not present: {FONTS}")
        return 0

    errors: list[str] = []
    warnings: list[str] = []

    for entry in sorted(FONTS.iterdir()):
        if not entry.is_dir():
            continue  # stray file at fonts/ root is out of scope
        name = entry.name

        n_tokens = len(name.split())
        if n_tokens >= MAX_TOKENS:
            errors.append(
                f"Pathological space-joined slug ({n_tokens} tokens): {name!r} — "
                "likely a shell-quoting bug; quarantine to font-factory/.trash/"
            )

        # stray raster references in the font root (not packed into a subdir)
        for f in sorted(entry.iterdir()):
            if f.is_file() and f.suffix.lower() in RASTER:
                warnings.append(
                    f"Stray raster in font root (move to visual-references/ or "
                    f"prepared_visuals/): {f.relative_to(ROOT)}"
                )

    for w in warnings:
        print(f"[WARN] {w}")
    for e in errors:
        print(f"[FAIL] {e}")

    if errors or (args.strict and warnings):
        print(f"\n[FAIL] {len(errors)} error(s), {len(warnings)} warning(s)")
        return 1
    print(f"\n[PASS] {len(errors)} error(s), {len(warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
