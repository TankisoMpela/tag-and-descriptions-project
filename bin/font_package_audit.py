#!/usr/bin/env python3
"""Technical audit of generated Pro and Freemium font packages (Agent 13, Step 6b).

Per font file it reports OS/2 fsType (expected 0 for Pro, 4 for Freemium) and
the name-table IDs, so the packaging step can be verified mechanically after
the metadata pass. Read-only: it never modifies a font.

Exit 1 if any expected fsType does not match, so the caller cannot report a
clean package on a real failure; otherwise 0.

Usage:
    python3 bin/font_package_audit.py "outputs/font-preparation/{NUM}-{slug}/{Font-Name}" \
        "outputs/font-preparation/{NUM}-{slug}/{Font-Name}-Demo"
"""
from __future__ import annotations

import argparse
from pathlib import Path

from fontTools.ttLib import TTFont

FONT_SUFFIXES = (".otf", ".ttf")


def audit_file(path: Path, is_demo: bool) -> bool:
    """Print one file's audit. Return True if it passed."""
    print(f"--- Auditing: {path.name} ---")
    try:
        font = TTFont(str(path))
    except Exception as error:  # noqa: BLE001 - report, do not crash the sweep
        print(f"❌ FAIL (cannot load: {error})")
        return False

    fstype = font["OS/2"].fsType
    expected = 4 if is_demo else 0
    status = "✅ PASS" if fstype == expected else f"❌ FAIL (got {fstype}, expected {expected})"
    print(f"OS/2 fsType: {fstype} — {status}")

    names = {r.nameID: r.toUnicode() for r in font["name"].names if r.platformID == 3}
    print(f"Name ID 1 (Family): {names.get(1)}")
    print(f"Name ID 6 (PostScript): {names.get(6)}")
    print(f"Glyph count: {len(font.getGlyphOrder())}")
    return fstype == expected


def audit_dir(directory: Path, is_demo: bool, label: str) -> tuple[int, int]:
    """Audit every font in a directory. Return (audited, failed)."""
    print(f"=== {label} ===")
    if not directory.is_dir():
        print(f"(skipped: {directory} does not exist — expected in PRO-ONLY mode)")
        return 0, 0
    files = sorted(p for p in directory.iterdir() if p.is_file() and p.suffix.lower() in FONT_SUFFIXES)
    if not files:
        print(f"(no .otf/.ttf files in {directory})")
        return 0, 0
    passed = sum(1 for path in files if audit_file(path, is_demo))
    return len(files), len(files) - passed


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("pro_dir", type=Path, help="the Pro package folder (font-named folder)")
    parser.add_argument("free_dir", nargs="?", type=Path, default=None,
                        help="the Freemium/Demo folder; omit in PRO-ONLY mode")
    args = parser.parse_args()

    audited = failed = 0
    a, f = audit_dir(args.pro_dir, is_demo=False, label="PRO AUDIT")
    audited += a; failed += f
    if args.free_dir is not None:
        a, f = audit_dir(args.free_dir, is_demo=True, label="FREEMIUM AUDIT")
        audited += a; failed += f

    print(f"\naudited {audited} file(s); failures: {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
