#!/usr/bin/env python3
"""Pre-flight audit of raw font input files (Agent 13, Step 2).

Per file: loads cleanly, required tables, units per em, OS/2 fsType, glyph
count, basic-Latin cmap coverage, existing name-table IDs, GSUB/GPOS presence.
Read-only: it never modifies a font.

Exit 1 if any file is missing or cannot be loaded (CRITICAL); otherwise 0.
Warnings and issues are reported but do not fail the run, because Step 3
corrects them in the output.

Family-consistency check (automatic when >1 file supplied, or with --family):
  • All members share the same UPM.
  • All members share the same typographic family name (nameID 16, falling
    back to nameID 1).
  • Every member has a distinct style name (nameID 17, falling back to nameID 2).
  • No two members share the same OS/2 usWeightClass + italic-flag combination.
  • Basic Latin A-Z/a-z coverage is identical across all members.

Usage:
    # Single file
    python3 bin/font_preflight_audit.py font-factory/fonts/{slug}/{Primary}.otf

    # Whole family directory (family check is automatic)
    python3 bin/font_preflight_audit.py font-factory/fonts/{slug}/

    # Explicit multi-file with forced family check
    python3 bin/font_preflight_audit.py Regular.otf Bold.otf Italic.otf --family

    # Skip family check
    python3 bin/font_preflight_audit.py Regular.otf Bold.otf --no-family
"""
from __future__ import annotations

import argparse
from pathlib import Path

from fontTools.ttLib import TTFont

REQUIRED_TABLES = ("head", "hhea", "maxp", "OS/2", "name", "cmap", "post")
FSTYPE_LABELS = {
    0: "Installable (best)",
    2: "Restricted (BAD — apps will refuse to embed)",
    4: "Print & Preview",
    8: "Editable",
}


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _name_str(font: TTFont, *ids: int) -> str:
    """Return the first non-empty Windows-platform Unicode value for any of ids."""
    for nid in ids:
        for rec in font["name"].names:
            if rec.nameID == nid and rec.platformID == 3:
                try:
                    val = rec.toUnicode().strip()
                    if val:
                        return val
                except Exception:  # noqa: BLE001
                    pass
    return ""


def _latin_frozenset(font: TTFont) -> frozenset[int]:
    cmap = font.getBestCmap() or {}
    return frozenset(c for c in cmap if 0x41 <= c <= 0x5A or 0x61 <= c <= 0x7A)


# ──────────────────────────────────────────────────────────────────────────────
# Per-file audit
# ──────────────────────────────────────────────────────────────────────────────

def audit(path: Path) -> tuple[list[str], list[str], list[str]]:
    """Return (info, warnings, issues) for one font file."""
    info: list[str] = []
    warnings: list[str] = []
    issues: list[str] = []

    if not path.is_file():
        return info, warnings, [f"\u274c CRITICAL \u2014 File not found: {path}"]

    try:
        font = TTFont(str(path))
    except Exception as error:  # noqa: BLE001 - any load failure is critical
        return info, warnings, [f"\u274c CRITICAL \u2014 File cannot be loaded: {error}"]

    info.append(f"\u2705 File loads cleanly: {path.name}")

    for table in REQUIRED_TABLES:
        if table not in font:
            issues.append(f"\u274c MISSING TABLE: {table}")
        else:
            info.append(f"\u2705 Table present: {table}")

    upm = font["head"].unitsPerEm
    if upm not in (1000, 2048):
        warnings.append(f"\u26a0\ufe0f  Unusual UPM: {upm} (expected 1000 for OTF or 1000/2048 for TTF)")
    else:
        info.append(f"\u2705 UPM: {upm}")

    fstype = font["OS/2"].fsType
    if fstype == 2:
        issues.append("\u274c OS/2 fsType=2 RESTRICTED \u2014 will be fixed to 0 in output")
    else:
        label = FSTYPE_LABELS.get(fstype, f"Unknown ({fstype})")
        info.append(f"\u2705 OS/2 fsType: {fstype} \u2014 {label}")

    info.append(f"\u2705 Glyph count: {len(font.getGlyphOrder())}")

    cmap = font.getBestCmap()
    if cmap is None:
        issues.append("\u274c No usable cmap table found")
    else:
        missing = [c for c in range(0x0041, 0x007B) if c not in cmap]
        if missing:
            warnings.append(f"\u26a0\ufe0f  Missing {len(missing)} basic Latin glyphs from cmap")
        else:
            info.append("\u2705 Basic Latin A-Z/a-z present in cmap")

    existing: dict[int, str] = {}
    for record in font["name"].names:
        if record.platformID == 3:
            try:
                existing[record.nameID] = record.toUnicode()
            except Exception:  # noqa: BLE001 - a bad name record is not fatal
                pass
    info.append(f"\u2705 Existing Name IDs found: {sorted(existing.keys())}")
    for name_id, value in sorted(existing.items()):
        info.append(f"   ID {name_id}: {value[:80]}")

    info.append(f"\u2705 GSUB (ligatures/alternates): {'present' if 'GSUB' in font else 'absent'}")
    info.append(f"\u2705 GPOS (kerning/positioning): {'present' if 'GPOS' in font else 'absent'}")

    return info, warnings, issues


# ──────────────────────────────────────────────────────────────────────────────
# Family-consistency check
# ──────────────────────────────────────────────────────────────────────────────

def family_check(paths: list[Path]) -> tuple[list[str], list[str], list[str]]:
    """Cross-member consistency checks for a multi-style family.

    Returns (info, warnings, issues).  Files that cannot be loaded are skipped
    (they are already flagged CRITICAL by per-file audit) so the rest of the
    family is still checked.
    """
    info: list[str] = []
    warnings: list[str] = []
    issues: list[str] = []

    members: list[tuple[Path, TTFont]] = []
    for p in paths:
        if not p.is_file():
            continue
        try:
            members.append((p, TTFont(str(p))))
        except Exception:  # noqa: BLE001
            continue

    if len(members) < 2:
        info.append("\u2139\ufe0f  Only one loadable file \u2014 family consistency check skipped.")
        return info, warnings, issues

    sep = "\u2500" * 60
    info.append(f"\n{sep}")
    info.append(f"FAMILY CONSISTENCY CHECK \u2014 {len(members)} members")
    info.append(sep)

    # 1. UPM consistency
    upms = {p.name: f["head"].unitsPerEm for p, f in members}
    unique_upms = set(upms.values())
    if len(unique_upms) == 1:
        info.append(f"\u2705 UPM consistent across family: {next(iter(unique_upms))}")
    else:
        issues.append(
            "\u274c UPM MISMATCH across family:\n"
            + "\n".join(f"   {n}: {v}" for n, v in sorted(upms.items()))
        )

    # 2. Shared typographic family name (nameID 16 preferred, 1 as fallback)
    fam_names = {p.name: _name_str(f, 16, 1) for p, f in members}
    unique_fams = set(fam_names.values())
    if len(unique_fams) == 1:
        info.append(f"\u2705 Typographic family name consistent: \u201c{next(iter(unique_fams))}\u201d")
    else:
        issues.append(
            "\u274c FAMILY NAME MISMATCH \u2014 members report different family names:\n"
            + "\n".join(f"   {n}: \u201c{v}\u201d" for n, v in sorted(fam_names.items()))
        )

    # 3. Distinct style names (nameID 17 preferred, 2 as fallback)
    style_names = {p.name: _name_str(f, 17, 2) or "(empty)" for p, f in members}
    seen_styles: dict[str, list[str]] = {}
    for fname, style in style_names.items():
        seen_styles.setdefault(style, []).append(fname)
    dupes = {s: fs for s, fs in seen_styles.items() if len(fs) > 1}
    if not dupes:
        info.append(f"\u2705 All style names are distinct: {sorted(style_names.values())}")
    else:
        issues.append(
            "\u274c DUPLICATE STYLE NAMES \u2014 these members share a style name:\n"
            + "\n".join(f"   \u201c{s}\u201d: {fs}" for s, fs in sorted(dupes.items()))
        )

    # 4. Unique weight-class + italic-flag signature (catches accidental duplicates)
    sigs: dict[str, list[str]] = {}
    for p, f in members:
        wc = f["OS/2"].usWeightClass
        italic = bool(f["OS/2"].fsSelection & 0x01)
        sig = f"weight={wc} italic={italic}"
        sigs.setdefault(sig, []).append(p.name)
    dupe_sigs = {s: fs for s, fs in sigs.items() if len(fs) > 1}
    if not dupe_sigs:
        info.append("\u2705 OS/2 weight+italic signatures are unique per member")
        for p, f in members:
            wc = f["OS/2"].usWeightClass
            italic = bool(f["OS/2"].fsSelection & 0x01)
            style_label = _name_str(f, 17, 2) or "?"
            info.append(f"   {p.name}: weight={wc}, italic={italic} \u2192 \u201c{style_label}\u201d")
    else:
        warnings.append(
            "\u26a0\ufe0f  DUPLICATE OS/2 weight+italic signature \u2014 possible mislabelled styles:\n"
            + "\n".join(f"   {s}: {fs}" for s, fs in sorted(dupe_sigs.items()))
        )

    # 5. Latin coverage consistency
    latin_sets = {p.name: _latin_frozenset(f) for p, f in members}
    ref_name, ref_set = next(iter(latin_sets.items()))
    coverage_issues: list[str] = []
    for fname, lset in list(latin_sets.items())[1:]:
        missing_vs_ref = ref_set - lset
        extra_vs_ref = lset - ref_set
        if missing_vs_ref or extra_vs_ref:
            parts = []
            if missing_vs_ref:
                parts.append(
                    f"missing {len(missing_vs_ref)} chars vs {ref_name}: "
                    + "".join(chr(c) for c in sorted(missing_vs_ref))
                )
            if extra_vs_ref:
                parts.append(
                    f"extra {len(extra_vs_ref)} chars vs {ref_name}: "
                    + "".join(chr(c) for c in sorted(extra_vs_ref))
                )
            coverage_issues.append(f"   {fname}: {'; '.join(parts)}")
    if coverage_issues:
        warnings.append(
            "\u26a0\ufe0f  LATIN COVERAGE DIFFERS across family members:\n"
            + "\n".join(coverage_issues)
        )
    else:
        info.append("\u2705 Basic Latin coverage is identical across all family members")

    # Summary
    info.append(
        f"\nFamily check: {len(issues)} issue(s), {len(warnings)} warning(s)"
    )

    return info, warnings, issues


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "paths", nargs="+", type=Path,
        help=".otf/.ttf files, or directories containing them"
    )
    parser.add_argument(
        "--family", action="store_true",
        help="Force family-consistency check (default: automatic when >1 file)"
    )
    parser.add_argument(
        "--no-family", action="store_true",
        help="Skip family-consistency check"
    )
    args = parser.parse_args()

    targets: list[Path] = []
    for entry in args.paths:
        if entry.is_dir():
            targets.extend(
                sorted(
                    p for p in entry.rglob("*")
                    if p.suffix.lower() in (".otf", ".ttf") and not p.name.startswith("._")
                )
            )
        else:
            targets.append(entry)

    if not targets:
        print("\u274c no .otf/.ttf files found in the supplied paths")
        return 1

    # Per-file audit
    critical = 0
    for target in targets:
        info, warnings, issues = audit(target)
        print(f"=== Auditing: {target.name} ===")
        print("\n".join(info))
        if warnings:
            print("\nWARNINGS:")
            print("\n".join(warnings))
        if issues:
            fatal = any("CRITICAL" in issue for issue in issues)
            print("\nCRITICAL:" if fatal else "\nISSUES (will be corrected in output):")
            print("\n".join(issues))
            if fatal:
                critical += 1
        print()

    print(f"audited {len(targets)} file(s); critical failures: {critical}")

    # Family consistency check
    run_family = (len(targets) > 1 or args.family) and not args.no_family
    if run_family:
        f_info, f_warnings, f_issues = family_check(targets)
        print()
        print("\n".join(f_info))
        if f_warnings:
            print("\nFAMILY WARNINGS:")
            print("\n".join(f_warnings))
        if f_issues:
            print("\nFAMILY ISSUES:")
            print("\n".join(f_issues))
            critical += len([i for i in f_issues if "CRITICAL" in i])

    return 1 if critical else 0


if __name__ == "__main__":
    raise SystemExit(main())
