#!/usr/bin/env python3
"""Deterministic font preparation for the FontFairy workflow (Agent 13).

This is the whole mechanical pass in one invocation: discover the raw fonts,
rewrite the name table and OS/2 flags, emit OTF/TTF/WOFF/WOFF2, copy the factual
specimens, leave the empty image drop directory, write the audit reports, and
build the three delivery archives, and sanitizes every delivered format with the
OpenType Sanitizer as an independent second parser.

An OTF (CFF) source is the master and the TTF is derived from it with cu2qu. A
glyf-only source — the usual shape of a marketplace demo download — is handled
the other way round: the branded TTF keeps the source's quadratic outlines and
hinting untouched, and the OTF master is derived from it by converting the
outlines to cubic charstrings (fontTools qu2cu). Either way the package carries
the same four formats with identical metadata.

The Commercial-Use and Personal-Use archives both carry the clean package
(Personal-Use may add a like-request note at the archive root). The
Free-Trial-Demo archive is rebuilt from a temporary copy whose digits and
ASCII punctuation have been replaced with the FontFairy demo stamp
(bin/stamp_personal_use.py); letters stay clean so the face can still be
previewed.

What it deliberately does NOT do, because it needs judgement:
  - description.txt          (marketplace copy)
Author it, then pass it with --description-file, or write it at the output root.

Showcase video rendering is archived; see archive/video/README.md to reinstate it.

Name IDs 0 and 10 are treated differently on purpose: ID 0 is overwritten with
the FontFairy copyright, ID 10 (the original upstream credit) is left untouched,
matching the packages already in outputs/font-preparation.

Usage:
    python3 bin/prepare_font_package.py \
        --workspace "font-factory/fonts/13-andallan" \
        --name "Andallan" --number 88
"""
from __future__ import annotations

import argparse
import datetime as _datetime
import hashlib
import json
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.qu2cuPen import Qu2CuPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont, newTable

ROOT = Path(__file__).resolve().parent.parent
OUTPUTS = ROOT / "outputs" / "font-preparation"

# Brand constants. Defaults mirror the Agent 13 spec (BRAND CONSTANTS table) and
# the newest packages in outputs/font-preparation. Override with --brand if the
# foundry changes.
BRAND = {
    "foundry": "FontFairy",
    "vendor_id": "FAIR",
    "version_tag": "fontfairy",
    "year": "2026",
    "store_url": "https://fontfairy.booth.pm/",
    "copyright_pro": "Copyright (c) 2026 FontFairy. All Rights Reserved.",
    "trademark": "{name} is a trademark of FontFairy.",
    "license_line": "FontFairy Commercial Font License. All Rights Reserved.",
}
LIKE_FILE_NAME = "PLEASE-GIVE-US-A-LIKE.txt"
FONT_SUFFIXES = (".otf", ".ttf")


def rel(path: Path) -> str:
    """Project-relative path for reports, falling back to absolute.

    The workspace is normally under the project root, but the packager must not
    crash when it is given one from elsewhere (a staging copy, for example).
    """
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path.resolve())


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return re.sub(r"-+", "-", value).strip("-")


def package_basename(name: str) -> str:
    """'Quill Crest' -> 'Quill-Crest'."""
    return re.sub(r"\s+", "-", name.strip())


def file_basename(name: str) -> str:
    """'Quill Crest' -> 'QuillCrest' (no spaces; used for on-disk font files)."""
    return re.sub(r"\s+", "", name.strip())


def subfamily_of(path: Path) -> str:
    """Derive the subfamily, preferring the font's own Name ID 2."""
    try:
        with TTFont(str(path)) as font:
            for record in font["name"].names:
                if record.nameID == 2 and record.platformID == 3:
                    value = record.toUnicode().strip()
                    if value:
                        return value
    except Exception:  # noqa: BLE001 - fall back to the filename
        pass
    lowered = path.stem.lower()
    for candidate in ("italic", "bold", "regular", "light", "medium", "black", "thin"):
        if candidate in lowered:
            return candidate.capitalize()
    return "Regular"


def set_name(name_table, name_id: int, value: str) -> None:
    """Replace a name ID on the Windows record, matching the shipped packages."""
    name_table.setName(value, name_id, 3, 1, 0x409)


# Name IDs this pass owns. Anything else (10 = upstream credit, 20/21/22, ...)
# is left exactly as the source shipped it.
BRANDED_NAME_IDS = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13, 14, 16, 17)


def set_metadata(font, name: str, subfamily: str, brand: dict) -> None:
    """Write the branded name table and OS/2 flags onto an open font object."""
    records = font["name"]
    file_base = file_basename(name)

    # A source carrying the typographic family/subfamily pair (IDs 16/17) would
    # otherwise keep announcing the old family name in every typography-aware
    # font menu, and legacy Mac-platform (1,0,0) records for the branded IDs
    # would keep the upstream name and copyright alive next to the Windows ones.
    # Shipped packages carry Windows records only, so drop the stale Mac records
    # and re-emit 16/17 on the Windows platform when the source had them.
    has_typo_family = any(r.nameID == 16 for r in records.names)
    has_typo_subfamily = any(r.nameID == 17 for r in records.names)
    for record in [r for r in records.names
                   if r.platformID == 1 and r.nameID in BRANDED_NAME_IDS]:
        records.names.remove(record)

    set_name(records, 0, brand["copyright_pro"])
    set_name(records, 1, name)
    set_name(records, 2, subfamily)
    set_name(records, 3, f"{brand['year']};{brand['foundry']};{name}-{subfamily}")
    set_name(records, 4, f"{name} {subfamily}")
    set_name(records, 5, f"Version 1.000;{brand['year']};{brand['version_tag']}")
    set_name(records, 6, f"{file_base}-{subfamily}")
    set_name(records, 7, brand["trademark"].format(name=name))
    set_name(records, 8, brand["foundry"])
    set_name(records, 9, brand["foundry"])
    set_name(records, 11, brand["store_url"])
    set_name(records, 12, brand["store_url"])
    set_name(records, 13, brand["license_line"])
    set_name(records, 14, brand["store_url"])
    if has_typo_family:
        set_name(records, 16, name)
    if has_typo_subfamily:
        set_name(records, 17, subfamily)

    font["OS/2"].fsType = 0
    font["OS/2"].achVendID = brand["vendor_id"][:4].ljust(4)


def apply_metadata(source: Path, destination: Path, name: str, subfamily: str, brand: dict) -> None:
    """Write the branded Pro font. Name ID 10 (upstream credit) is preserved."""
    font = TTFont(str(source))
    set_metadata(font, name, subfamily, brand)
    destination.parent.mkdir(parents=True, exist_ok=True)
    font.save(str(destination))
    font.close()


def convert_ttf(otf: Path, ttf: Path, max_err: float = 1.0) -> None:
    """Convert OTF (CFF cubic outlines) to TTF (glyf quadratic) with fontTools.

    FontForge used to do this and shipped two defects: it wrote OS/2 version 5
    with a version-4-length table (fontTools then refused to load the file at
    all), and it regenerated Name ID 6 from the CFF's internal FontName, so the
    TTF carried the upstream PostScript name while the OTF carried the branded
    one. cu2qu converts only the outlines: every other table, including the name
    table this script just wrote, is carried over untouched.

    Measured output is equivalent to FontForge's - rendering the same string from
    the original OTF, the FontForge TTF and this TTF, the two conversions differ
    from each other by 1.12 mean absolute intensity over 0.78% of pixels.
    """
    font = TTFont(str(otf))
    order = font.getGlyphOrder()
    glyph_set = font.getGlyphSet()

    glyf = newTable("glyf")
    glyf.glyphOrder = order
    glyf.glyphs = {}
    for name in order:
        pen = TTGlyphPen(glyph_set)
        glyph_set[name].draw(Cu2QuPen(pen, max_err, reverse_direction=True))
        glyf.glyphs[name] = pen.glyph()
    for glyph in glyf.glyphs.values():
        glyph.recalcBounds(glyf)  # empty glyphs have no bounds of their own
    font["glyf"] = glyf
    font["loca"] = newTable("loca")   # rebuilt from glyf on compile

    maxp = font["maxp"]
    maxp.tableVersion = 0x00010000
    maxp.maxZones = 1
    maxp.maxTwilightPoints = 0
    maxp.maxStorage = 0
    maxp.maxFunctionDefs = 0
    maxp.maxInstructionDefs = 0
    maxp.maxStackElements = 0
    maxp.maxSizeOfInstructions = 0
    maxp.maxComponentElements = max(
        (len(g.components) if hasattr(g, "components") else 0) for g in glyf.glyphs.values()
    )
    maxp.recalc(font)

    del font["CFF "]
    if "VORG" in font:
        del font["VORG"]
    font["head"].indexToLocFormat = 0
    font["post"].formatType = 2.0
    font["post"].extraNames = []
    font["post"].mapping = {}
    font["post"].glyphOrder = order
    font.sfntVersion = "\000\001\000\000"

    ttf.parent.mkdir(parents=True, exist_ok=True)
    font.save(str(ttf))
    font.close()


def outline_flavor(path: Path) -> str:
    """Return "cff" or "glyf" — which outline table the source carries.

    The workspace normally holds the released OTF, so the CFF branch below is
    the master and the TTF is the derived format. Marketplace demos are often
    TrueType-only, which reverses the two.
    """
    with TTFont(str(path)) as font:
        if "CFF " in font:
            return "cff"
        if "glyf" in font:
            return "glyf"
    raise SystemExit(f"{path.name}: neither CFF nor glyf outlines")


def convert_otf(ttf: Path, otf: Path, max_err: float = 1.0) -> None:
    """Derive the CFF/OTF master from a glyf-only source, with fontTools qu2cu.

    A TrueType demo has no CFF table to carry over, so the outlines are rebuilt
    as cubic charstrings and every other table — name, OS/2, cmap, metrics,
    GSUB/GPOS, kern — is kept from the branded TTF. All four delivered formats
    therefore still carry identical metadata. The TrueType-only tables (hinting,
    hinted metrics, legacy VDMX/LTSH) are dropped; a CFF font has no use for
    them.

    Measured on the 237-glyph hinted demo this branch was written for (upem
    1000) at max_err 1.0: tight outline bounds move by at most 0.89 unit (mean
    0.379), and rendering a mixed string at 200 px differs from the source by
    0.14 mean absolute intensity over 0.47% of pixels. OTS accepts the result.
    """
    font = TTFont(str(ttf))
    glyph_set = font.getGlyphSet()
    hmtx = font["hmtx"]
    charstrings = {}
    for name in font.getGlyphOrder():
        pen = T2CharStringPen(hmtx[name][0], glyph_set)
        glyph_set[name].draw(Qu2CuPen(pen, max_err, all_cubic=True, reverse_direction=True))
        charstrings[name] = pen.getCharString()

    records = font["name"]
    builder = FontBuilder(font["head"].unitsPerEm, isTTF=False)
    builder.font = font
    builder.setupCFF(
        records.getDebugName(6),
        {
            "FullName": records.getDebugName(4),
            "FamilyName": records.getDebugName(1),
            "Weight": records.getDebugName(2),
        },
        charstrings,
        {},
    )

    del font["glyf"]
    del font["loca"]
    for tag in ("cvt ", "fpgm", "prep", "gasp", "VDMX", "LTSH", "hdmx", "DSIG"):
        if tag in font:
            del font[tag]
    font["head"].indexToLocFormat = 0
    font["maxp"].tableVersion = 0x00005000  # a CFF maxp carries the glyph count only

    otf.parent.mkdir(parents=True, exist_ok=True)
    font.save(str(otf))
    font.close()


def make_woff(otf: Path) -> list[Path]:
    """WOFF + WOFF2 beside the OTF, never modifying the source."""
    written = []
    for flavor, suffix in (("woff", ".woff"), ("woff2", ".woff2")):
        target = otf.with_suffix(suffix)
        font = TTFont(str(otf))
        font.flavor = flavor
        font.save(str(target))
        font.close()
        written.append(target)
    return written


def run_ots(files: list[Path]) -> tuple[str, bool]:
    """Sanitize every delivered font format with the OpenType Sanitizer.

    This is an independent, spec-level parser, not a duplicate of
    font_package_audit: that tool reads fsType, name IDs and glyph count through
    fontTools, which loads some malformed fonts without complaint until a broken
    table is touched. OTS parses every table and fails closed. It catches the
    class of defect that shipped here once — FontForge wrote OS/2 version 5 at
    the version-4 length, and OTS reports it as "OS/2: Failed to read version
    5-specific fields" while fontTools only raises a bare struct.error.

    Skipped with a note when ots-sanitize is not installed, so the packager still
    runs on a machine without it.
    """
    ots = shutil.which("ots-sanitize")
    if ots is None:
        return ("ots-sanitize not installed; independent table validation skipped.", True)

    lines: list[str] = []
    ok = True
    for path in files:
        result = subprocess.run([ots, str(path)], capture_output=True, text=True)
        if result.returncode == 0:
            lines.append(f"{path.name}: sanitized OK")
        else:
            ok = False
            detail = " ".join((result.stdout + result.stderr).split())
            lines.append(f"{path.name}: FAILED — {detail[:200]}")
    return ("\n".join(lines), ok)


def run_preflight(workspace: Path) -> tuple[str, bool]:
    """Run the read-only pre-flight audit over the raw inputs, as Step 2 did.

    Returns (report_text, ok). A critical failure means a font is missing or
    cannot be loaded, which would fail later anyway; catching it here keeps the
    reason in the audit report.
    """
    result = subprocess.run(
        [sys.executable, str(ROOT / "bin" / "font_preflight_audit.py"), str(workspace)],
        capture_output=True, text=True,
    )
    return (result.stdout or result.stderr).strip(), result.returncode == 0


def copy_specimens(workspace: Path, out: Path) -> list[tuple[str, str, int, str]]:
    """Copy the four factual specimen PNGs unchanged. Return mapping rows."""
    source = workspace / "prepared_visuals" / "specimens"
    rows: list[tuple[str, str, int, str]] = []
    for ratio in ("3x2", "1x1"):
        src_dir = source / ratio
        if not src_dir.is_dir():
            continue
        dst_dir = out / "specimens" / ratio
        dst_dir.mkdir(parents=True, exist_ok=True)
        for png in sorted(src_dir.glob("*.png")):
            target = dst_dir / png.name
            shutil.copy2(png, target)
            digest = hashlib.sha256(target.read_bytes()).hexdigest()
            rows.append((rel(png), rel(target), target.stat().st_size, digest))
    return rows


def build_archive(
    target: Path,
    package: Path,
    like_file: Path | None,
    note_entry_name: str | None = None,
) -> None:
    """Build a delivery zip with fixed timestamps so it is reproducible.

    ``note_entry_name`` overrides the zip-root filename for ``like_file``
    (defaults to the source basename).
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for font_file in sorted(package.iterdir()):
            if font_file.is_file():
                info = zipfile.ZipInfo(f"{package.name}/{font_file.name}", date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, font_file.read_bytes())
        if like_file is not None and like_file.is_file():
            entry = note_entry_name or like_file.name
            info = zipfile.ZipInfo(entry, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, like_file.read_bytes())


def stamp_personal_package(package: Path) -> tuple[Path, dict[str, int], tempfile.TemporaryDirectory]:
    """Stamp a clean package into a temp tree for the Free-Trial-Demo archive.

    Returns (stamped_dir_with_same_basename, per-file glyph counts, tempdir).
    Caller must keep the TemporaryDirectory alive until the zip is written,
    then call .cleanup().
    """
    sys.path.insert(0, str(ROOT / "bin"))
    from stamp_personal_use import (  # noqa: PLC0415 - local helper module
        DEFAULT_STAMP_PATHS,
        DEFAULT_STAMP_SVG,
        outline_stamp,
        parse_coverage,
        stamp_package,
    )

    stamp_svg = DEFAULT_STAMP_PATHS
    if not stamp_svg.is_file() and DEFAULT_STAMP_SVG.is_file():
        outline_stamp(DEFAULT_STAMP_SVG, DEFAULT_STAMP_PATHS)

    tmp = tempfile.TemporaryDirectory(prefix="font-demo-stamp-")
    # stamp_package writes into out_dir as a flat folder; we need the zip
    # entries under package.name/, so stamp into tmp/package.name.
    stamped_root = Path(tmp.name) / package.name
    stats = stamp_package(package, stamped_root, stamp_svg, parse_coverage("digits,punct"))
    return stamped_root, stats, tmp


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--workspace", required=True, type=Path, help="font-factory/fonts/{slug}")
    parser.add_argument("--name", required=True, help="final font name, exact spelling")
    parser.add_argument("--number", help="catalogue number; omit to read visual-direction/catalogue-number.txt")
    parser.add_argument("--description-file", type=Path, default=None,
                        help="authored description.txt to install at the output root")
    parser.add_argument("--like-file", type=Path, default=None,
                        help=f"{LIKE_FILE_NAME} to include in the Personal-Use archive")
    parser.add_argument("--demo-readme", type=Path, default=None,
                        help="README.txt to include in the Free-Trial-Demo archive")
    parser.add_argument("--force", action="store_true", help="overwrite an existing output directory")
    args = parser.parse_args()

    workspace = args.workspace.expanduser().resolve()
    if not workspace.is_dir():
        raise SystemExit(f"workspace not found: {workspace}")

    sources = sorted(p for p in workspace.iterdir() if p.is_file() and p.suffix.lower() in FONT_SUFFIXES)
    if not sources:
        raise SystemExit(f"no .otf/.ttf files in {workspace}")

    # One source per subfamily. A workspace commonly carries both .otf and .ttf for
    # the same weight, and both would resolve to the SAME output filename, so the
    # second would silently overwrite the first — losing the OTF master to the TTF
    # and doing the whole metadata/format pass twice. Prefer the .otf and say what
    # was skipped.
    by_subfamily: dict[str, Path] = {}
    skipped: list[tuple[Path, Path]] = []
    for path in sources:
        subfamily = subfamily_of(path)
        current = by_subfamily.get(subfamily)
        if current is None:
            by_subfamily[subfamily] = path
        elif path.suffix.lower() == ".otf" and current.suffix.lower() != ".otf":
            by_subfamily[subfamily] = path
            skipped.append((current, path))
        else:
            skipped.append((path, current))
    sources = [by_subfamily[key] for key in sorted(by_subfamily)]

    number = args.number
    if not number:
        marker = workspace / "visual-direction" / "catalogue-number.txt"
        if marker.is_file():
            number = marker.read_text(encoding="utf-8").strip()
    if not number:
        raise SystemExit("--number is required (or write visual-direction/catalogue-number.txt)")

    preflight_report, preflight_ok = run_preflight(workspace)
    if not preflight_ok:
        print(preflight_report)
        raise SystemExit("pre-flight audit failed; fix the input files before packaging")

    slug = slugify(args.name)
    out = OUTPUTS / f"{number}-{slug}"
    if out.exists() and any(out.iterdir()) and not args.force:
        raise SystemExit(f"refusing to overwrite non-empty {out}; pass --force to replace")
    out.mkdir(parents=True, exist_ok=True)

    package = out / package_basename(args.name)
    print(f"product  {number}-{slug}")
    print(f"package  {rel(package)}/")

    for dropped, kept in skipped:
        print(f"  skipped        {dropped.name} — duplicate {subfamily_of(dropped)}; using {kept.name}")

    generated: list[Path] = []
    flavors: set[str] = set()
    for source in sources:
        subfamily = subfamily_of(source)
        flavor = outline_flavor(source)
        flavors.add(flavor)
        base = file_basename(args.name)

        if flavor == "cff":
            otf = package / f"{base}-{subfamily}.otf"
            apply_metadata(source, otf, args.name, subfamily, BRAND)
            generated.append(otf)
            print(f"  metadata + otf  {otf.name}")

            ttf = otf.with_suffix(".ttf")
            convert_ttf(otf, ttf)
            generated.append(ttf)
        else:
            ttf = package / f"{base}-{subfamily}.ttf"
            apply_metadata(source, ttf, args.name, subfamily, BRAND)
            generated.append(ttf)
            print(f"  metadata + ttf  {ttf.name} (glyf source; OTF derived)")

            otf = ttf.with_suffix(".otf")
            convert_otf(ttf, otf)
            generated.append(otf)

        generated.extend(make_woff(otf))
        print(f"  ttf/woff/woff2 {otf.stem}")

    specimen_rows = copy_specimens(workspace, out)
    (out / "visuals" / "New-Images").mkdir(parents=True, exist_ok=True)
    print(f"  specimens      {len(specimen_rows)} copied; drop directory ready")

    if args.description_file:
        shutil.copy2(args.description_file, out / "description.txt")
        print("  description.txt installed")

    # name-report.md
    name_report = [
        "# Font Name Report", "",
        "## Product Information",
        f"- **Catalogue Number**: {number}",
        f"- **Final Font Name**: {args.name}",
        f"- **Output Slug**: {slug}",
        f"- **Package Basename**: {package.name}",
        f"- **Font File Basename**: {file_basename(args.name)}",
        f"- **PostScript Name**: {file_basename(args.name)}-{subfamily_of(sources[0])}",
        f"- **Source Font**: {sources[0].name}", "",
        "## Name Derivation",
        f"- Slug derivation: {args.name} → {slug}",
        f"- Package derivation: {args.name} → {package.name}", "",
        "## Output Paths",
        f"- Font Package: {rel(package)}/",
        f"- Specimens: {rel(out / 'specimens')}/",
    ]
    (out / "name-report.md").write_text("\n".join(name_report) + "\n", encoding="utf-8")

    # specimen-source-manifest.md
    manifest = ["# Specimen Source Manifest", "",
                f"## Copy Status: {'SUCCESS' if specimen_rows else 'NO SPECIMENS FOUND'}", ""]
    if specimen_rows:
        manifest += ["All factual specimen PNGs were copied unchanged from the Agent 27 handoff.", "",
                     "### Source → Destination Mapping", "",
                     "| Source Path | Destination Path | Byte Size | SHA-256 |",
                     "|-------------|------------------|-----------|---------|"]
        for src, dst, size, digest in specimen_rows:
            manifest.append(f"| {src} | {dst} | {size} | {digest} |")
    else:
        manifest += [f"No specimens found under {rel(workspace / 'prepared_visuals' / 'specimens')}; nothing was copied.", ""]
    manifest += ["", "### Notes",
                 "- Specimens were copied byte-for-byte; no resize, recompress, rename or recolor",
                 "- Creative marketing images remain deferred and were not processed"]
    (out / "specimen-source-manifest.md").write_text("\n".join(manifest) + "\n", encoding="utf-8")

    # archives — Commercial and Personal both carry the clean package (Personal
    # may add the like note); Free-Trial-Demo is rebuilt from a temporary tree
    # whose digits/punctuation carry the FontFairy demo stamp.
    like_file = args.like_file
    demo_readme = args.demo_readme
    build_archive(out / f"{package.name}-Commercial-Use.zip", package, None)
    build_archive(out / f"{package.name}-Personal-Use.zip", package, like_file,
                  note_entry_name=LIKE_FILE_NAME)
    stamped_root, stamp_stats, stamp_tmp = stamp_personal_package(package)
    try:
        build_archive(
            out / f"{package.name}-Free-Trial-Demo.zip",
            stamped_root,
            demo_readme,
            note_entry_name="README.txt",
        )
        stamped_ots = run_ots(sorted(f for f in stamped_root.iterdir() if f.is_file()))
    finally:
        stamp_tmp.cleanup()
    stamp_total = sum(stamp_stats.values())
    stamp_note = (
        f"{len(stamp_stats)} file(s), {stamp_total} glyph replacement(s) "
        f"(coverage digits+punct)"
        if stamp_total
        else "NO GLYPHS STAMPED — free-trial-demo archive is not watermarked"
    )
    print(f"  archives       {package.name}-Commercial-Use.zip (clean), "
          f"{package.name}-Personal-Use.zip (clean), "
          f"{package.name}-Free-Trial-Demo.zip (stamped: {stamp_note})")

    # technical audit
    audit = subprocess.run(
        [sys.executable, str(ROOT / "bin" / "font_package_audit.py"), str(package)],
        capture_output=True, text=True,
    )
    ots_report, ots_ok = run_ots(sorted(f for f in package.iterdir() if f.is_file()))
    stamp_ots_report, stamp_ots_ok = stamped_ots
    stamp = _datetime.datetime.now(_datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    derivation = (
        "CFF source master; TTF derived with cu2qu" if flavors == {"cff"}
        else "glyf source master; OTF derived with qu2cu" if flavors == {"glyf"}
        else "mixed sources: " + ", ".join(sorted(flavors))
    )
    report = ["# Font Preparation Audit Report", "", "## Product Information",
              f"- **Font Name**: {args.name}", f"- **Catalogue Number**: {number}",
              f"- **Output Slug**: {slug}", f"- **Package Basename**: {package.name}",
              f"- **Date**: {stamp}", f"- **Outline Derivation**: {derivation}",
              f"- **Free-Trial-Demo Stamp**: {stamp_note}", "",
              "## PRE-FLIGHT AUDIT (raw inputs)", "", "```",
              preflight_report, "```", "", "## TECHNICAL FONT AUDIT (Pro package)", "", "```",
              audit.stdout.strip(), "```", "", "## OPENTYPE SANITIZER (independent parser)", "", "```",
              ots_report, "```", "", "## OPENTYPE SANITIZER (Free-Trial-Demo stamped)", "", "```",
              stamp_ots_report, "```", ""]
    (out / "audit-report.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    print()
    print(f"✅ Font Metadata & Package Complete: {rel(out)}/")
    print(f"- Winning Font Name: {args.name} (Slug: {slug})")
    print(f"- Pro package: {', '.join(sorted({p.suffix[1:].upper() for p in generated}))}")
    print(f"- Specimens: {len(specimen_rows)} file(s)")
    print(f"- Free-Trial-Demo watermark: {stamp_note}")
    print(f"- Final images: NOT PROCESSED — drop them into "
          f"{rel(out)}/visuals/New-Images/ then run /font-final-images")
    passed = audit.returncode == 0 and ots_ok and stamp_ots_ok and stamp_total > 0
    print(f"- Audit: {'PASS' if passed else 'FAIL — see audit-report.md'}")
    if not passed:
        if audit.returncode != 0:
            print(audit.stdout.strip()[-600:])
        if not ots_ok:
            print(ots_report[-600:])
        if not stamp_ots_ok:
            print(stamp_ots_report[-600:])
        if stamp_total == 0:
            print("free-trial-demo stamp replaced 0 glyphs — check the stamp SVG and coverage")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
