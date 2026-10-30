#!/usr/bin/env python3
"""Deterministic font preparation for the FontFairy workflow (Agent 13).

This is the whole mechanical pass in one invocation: discover the raw fonts,
rewrite the name table and OS/2 flags, emit OTF/TTF/WOFF/WOFF2, leave the empty
image drop directory, write the audit reports, build the two delivery archives,
and sanitize every delivered format with the OpenType Sanitizer as an independent
second parser.

An OTF (CFF) source is the master and the TTF is derived from it with cu2qu. A
glyf-only source keeps its quadratic outlines and TrueType hinting in the TTF;
the OTF is derived with qu2cu. Outline conversion cannot preserve the source
hinting program, so the audit report identifies which formats retain it.
WOFF and WOFF2 are generated from the OTF master. Branded metadata is normalized
across name-table platforms, while head.created remains the source value and
head.modified reflects the save time.

The Commercial-Use and Personal-Use archives carry identical font binaries.
Personal-Use may add a like-request note at the archive root.

What it deliberately does NOT do, because it needs judgement:
  - description.txt          (marketplace copy)
Author it, then pass it with --description-file, or write it at the output root.

Showcase video rendering is archived; see archive/video/README.md to reinstate it.

Name ID 10 is the optional Description field, not an author-credit field. The
packager removes it from delivered fonts; the raw-input preflight report keeps
the source value for review. `head.created` is retained from the source and
fontTools refreshes `head.modified` when saving.

Usage:
    python3 bin/prepare_font_package.py \
        --workspace "font-factory/fonts/13-andallan" \
        --name "Andallan" --number 88
"""
from __future__ import annotations

import argparse
import datetime as _datetime
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

from fontTools.fontBuilder import FontBuilder
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
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
PACKAGE_FONT_SUFFIXES = (".otf", ".ttf", ".woff", ".woff2")


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


def postscript_name(name: str, subfamily: str) -> str:
    """Build a printable, space-free PostScript name, capped at 63 characters."""
    base = re.sub(r"[^A-Za-z0-9-]", "", file_basename(name)) or "FontFairy"
    style = re.sub(r"[^A-Za-z0-9-]", "", subfamily) or "Regular"
    base = base[:max(1, 62 - len(style))]
    return f"{base}-{style}"[:63]


def postscript_prefix(name: str, subfamily: str) -> str:
    """Return the family prefix from the generated PostScript name."""
    ps_name = postscript_name(name, subfamily)
    style = re.sub(r"[^A-Za-z0-9-]", "", subfamily) or "Regular"
    suffix = f"-{style}"
    return ps_name[:-len(suffix)] if ps_name.endswith(suffix) else ps_name


def subfamily_of(path: Path) -> str:
    """Derive a clean style label from OS/2 weight, width, and slant fields."""
    try:
        with TTFont(str(path)) as font:
            os2 = font["OS/2"]
            weights = {
                100: "Thin", 200: "Extra Light", 300: "Light", 350: "Book",
                400: "Regular", 500: "Medium", 600: "Semi Bold", 700: "Bold",
                800: "Extra Bold", 900: "Black", 1000: "Extra Black",
            }
            widths = {
                1: "Ultra Condensed", 2: "Extra Condensed", 3: "Condensed",
                4: "Semi Condensed", 5: "", 6: "Semi Expanded",
                7: "Expanded", 8: "Extra Expanded", 9: "Ultra Expanded",
            }
            weight = min(weights, key=lambda value: abs(value - os2.usWeightClass))
            style_parts = [weights[weight]]
            width = widths.get(os2.usWidthClass, "")
            if width:
                style_parts.append(width)
            if os2.fsSelection & (0x0001 | 0x0200):
                style_parts.append("Italic")
            return " ".join(style_parts)
    except Exception:  # noqa: BLE001 - fall back to the filename
        pass
    lowered = path.stem.lower()
    for candidate in ("italic", "bold", "regular", "light", "medium", "black", "thin"):
        if candidate in lowered:
            return candidate.capitalize()
    return "Regular"


def set_name(name_table, name_id: int, value: str) -> None:
    """Replace every platform/language variant with one Windows Unicode record."""
    remove_name(name_table, name_id)
    name_table.setName(value, name_id, 3, 1, 0x409)


def remove_name(name_table, name_id: int) -> None:
    """Remove all records for a name ID, regardless of platform or language."""
    name_table.names[:] = [record for record in name_table.names
                           if record.nameID != name_id]


def referenced_name_ids(font) -> set[int]:
    """Find name IDs referenced by other tables before dropping unused custom IDs."""
    referenced: set[int] = set()
    visited: set[int] = set()

    def visit(value) -> None:
        if value is None or isinstance(value, (str, bytes, bytearray, int, float, bool)):
            return
        identity = id(value)
        if identity in visited:
            return
        visited.add(identity)
        if isinstance(value, dict):
            children = value.items()
        elif isinstance(value, (list, tuple, set)):
            children = enumerate(value)
        else:
            attributes = getattr(value, "__dict__", None)
            if not attributes:
                return
            children = attributes.items()
        for key, child in children:
            if (isinstance(key, str) and key.lower().endswith("nameid")
                    and isinstance(child, int) and child != 0xFFFF):
                referenced.add(child)
            visit(child)

    for table_tag in ("fvar", "STAT", "CPAL"):
        if table_tag in font:
            try:
                visit(font[table_tag])
            except Exception:  # noqa: BLE001 - malformed optional table is reported elsewhere
                continue
    if "CPAL" in font:
        cpal = font["CPAL"].table
        for attribute in ("paletteLabels", "paletteEntryLabels"):
            values = getattr(cpal, attribute, ()) or ()
            referenced.update(
                value for value in values
                if isinstance(value, int) and value != 0xFFFF
            )
    for table_tag in ("GSUB", "GPOS"):
        if table_tag not in font:
            continue
        try:
            feature_list = font[table_tag].table.FeatureList
            for feature in getattr(feature_list, "FeatureRecord", ()) or ():
                visit(getattr(feature, "FeatureParams", None))
        except Exception:  # noqa: BLE001 - malformed optional table is reported elsewhere
            continue
    return referenced


def sanitize_cff_string_index(cff, source_metadata: set[str]) -> None:
    """Replace orphaned CFF strings from rewritten identity fields in place."""
    if not source_metadata:
        return
    top_dict = cff.topDictIndex[0]
    glyph_names = set(getattr(top_dict, "charset", ()))
    strings = cff.strings
    for index, value in enumerate(strings.strings):
        if value in source_metadata and value not in glyph_names:
            strings.strings[index] = "FontFairy"
    strings.__dict__.pop("stringMapping", None)
    strings.buildStringMapping()


# Optional platform-specific or descriptive records are rewritten or removed
# alongside IDs 0-14 and 16-17. Other referenced names are retained for features.
BRANDED_NAME_IDS = (
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13, 14,
    16, 17, 19, 20, 21, 22, 25,
)
REMOVED_NAME_IDS = (10, 15, 18)
REMOVED_TABLES = ("DSIG", "FFTM", "PCLT", "meta")


def set_metadata(font, name: str, subfamily: str, brand: dict) -> None:
    """Write branded name-table, CFF-name, and OS/2 metadata onto a font.

    Name ID 10 is the optional Description field, not an author-credit field;
    it is removed from the shipped font. head.created remains from the source,
    and fontTools refreshes head.modified when saving.
    """
    records = font["name"]
    present_name_ids = {record.nameID for record in records.names}
    refs = referenced_name_ids(font)
    for name_id in (*BRANDED_NAME_IDS, *REMOVED_NAME_IDS):
        remove_name(records, name_id)
    # Name IDs 26-65535 are reserved for future standard fields or font-specific
    # names. Retain values only when another table references them.
    for record in list(records.names):
        if 26 <= record.nameID <= 0xFFFF and record.nameID not in refs:
            records.names.remove(record)

    set_name(records, 0, brand["copyright_pro"])
    set_name(records, 1, name)
    set_name(records, 2, subfamily)
    set_name(records, 3, f"{brand['year']};{brand['foundry']};{name}-{subfamily}")
    set_name(records, 4, f"{name} {subfamily}")
    set_name(records, 5, f"Version 1.000;{brand['year']};{brand['version_tag']}")
    set_name(records, 6, postscript_name(name, subfamily))
    set_name(records, 7, brand["trademark"].format(name=name))
    set_name(records, 8, brand["foundry"])
    set_name(records, 9, brand["foundry"])
    set_name(records, 11, brand["store_url"])
    set_name(records, 12, brand["store_url"])
    set_name(records, 13, brand["license_line"])
    set_name(records, 14, brand["store_url"])
    if 16 in present_name_ids or 16 in refs:
        set_name(records, 16, name)
    if 17 in present_name_ids or 17 in refs:
        set_name(records, 17, subfamily)
    if 19 in present_name_ids or 19 in refs:
        set_name(records, 19, f"{name} {subfamily}")
    if 20 in present_name_ids:
        set_name(records, 20, records.getDebugName(6))
    if 21 in present_name_ids:
        set_name(records, 21, name)
    if 22 in present_name_ids:
        set_name(records, 22, subfamily)
    if 25 in present_name_ids:
        set_name(records, 25, postscript_prefix(name, subfamily))

    # CFF duplicates names and identifiers outside the OpenType name table.
    if "CFF " in font:
        cff = font["CFF "].cff
        top_dict = cff.topDictIndex[0]
        source_cff_metadata = {
            value for field in ("FamilyName", "FullName", "Weight", "Copyright", "Notice")
            if isinstance((value := getattr(top_dict, field, None)), str) and value
        }
        top_dict.FamilyName, top_dict.FullName = (
            records.getDebugName(1), records.getDebugName(4)
        )
        top_dict.Weight = records.getDebugName(2)
        cff.fontNames[0] = records.getDebugName(6)
        top_dict.Copyright = records.getDebugName(0)
        top_dict.Notice = records.getDebugName(13)
        sanitize_cff_string_index(cff, source_cff_metadata)
        for field in ("UniqueID", "XUID"):
            top_dict.rawDict.pop(field, None)
            if hasattr(top_dict, field):
                top_dict.__dict__.pop(field, None)

    # Editing any table invalidates an existing signature. FFTM, PCLT and meta
    # carry optional application, printer or descriptive metadata.
    for table_tag in REMOVED_TABLES:
        if table_tag in font:
            del font[table_tag]

    # These are the OS/2 identity/licensing fields this workflow owns. Weight,
    # width, coverage, selection, PANOSE and metrics remain source-derived.
    font["OS/2"].fsType = 0
    font["OS/2"].achVendID = brand["vendor_id"][:4].ljust(4)


def apply_layout_features(font, feature_file: Path) -> None:
    """Replace GSUB/GPOS from an explicit Adobe Feature File input."""
    feature_file = feature_file.expanduser().resolve()
    if not feature_file.is_file():
        raise FileNotFoundError(f"layout feature file not found: {feature_file}")
    addOpenTypeFeaturesFromString(
        font,
        feature_file.read_text(encoding="utf-8"),
        filename=str(feature_file),
        tables=("GSUB", "GPOS"),
    )


def apply_metadata(
    source: Path,
    destination: Path,
    name: str,
    subfamily: str,
    brand: dict,
    layout_features: Path | None = None,
) -> None:
    """Write branded metadata and optional replacement GSUB/GPOS tables."""
    font = TTFont(str(source), recalcTimestamp=True)
    set_metadata(font, name, subfamily, brand)
    if layout_features is not None:
        apply_layout_features(font, layout_features)
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
    font = TTFont(str(otf), recalcTimestamp=True)
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
    font = TTFont(str(ttf), recalcTimestamp=True)
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
    cff_top_dict = font["CFF "].cff.topDictIndex[0]
    cff_top_dict.Copyright = records.getDebugName(0)
    cff_top_dict.Notice = records.getDebugName(13)

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
        font = TTFont(str(otf), recalcTimestamp=True)
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


def verify_archive_font_payloads(commercial: Path, personal: Path) -> tuple[str, bool]:
    """Verify both license archives carry the same font paths and bytes."""
    with zipfile.ZipFile(commercial) as commercial_zip, zipfile.ZipFile(personal) as personal_zip:
        commercial_fonts = {
            name: commercial_zip.read(name)
            for name in commercial_zip.namelist()
            if Path(name).suffix.lower() in PACKAGE_FONT_SUFFIXES
        }
        personal_fonts = {
            name: personal_zip.read(name)
            for name in personal_zip.namelist()
            if Path(name).suffix.lower() in PACKAGE_FONT_SUFFIXES
        }
    ok = bool(commercial_fonts) and commercial_fonts == personal_fonts
    detail = (
        f"matching font payload: {len(commercial_fonts)} file(s)"
        if ok else "font paths or binary contents differ"
    )
    return detail, ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--workspace", required=True, type=Path, help="font-factory/fonts/{input-slug}")
    parser.add_argument("--name", required=True, help="final font name, exact spelling")
    parser.add_argument("--number", help="catalogue number; omit to read visual-direction/catalogue-number.txt")
    parser.add_argument("--description-file", type=Path, default=None,
                        help="authored description.txt to install at the output root")
    parser.add_argument("--layout-features", type=Path, default=None,
                        help="optional Adobe Feature File (.fea) that replaces GSUB/GPOS")
    parser.add_argument("--like-file", type=Path, default=None,
                        help=f"{LIKE_FILE_NAME} to include in the Personal-Use archive")
    parser.add_argument("--force", action="store_true", help="overwrite an existing output directory")
    args = parser.parse_args()

    workspace = args.workspace.expanduser().resolve()
    if not workspace.is_dir():
        raise SystemExit(f"workspace not found: {workspace}")

    sources = sorted(p for p in workspace.iterdir() if p.is_file() and p.suffix.lower() in FONT_SUFFIXES)
    if not sources:
        raise SystemExit(f"no .otf/.ttf files in {workspace}")
    if args.layout_features is not None and not args.layout_features.expanduser().is_file():
        raise SystemExit(f"layout feature file not found: {args.layout_features}")

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
        elif path.suffix.lower() == current.suffix.lower():
            raise SystemExit(
                f"multiple source files derive the same OS/2 style label {subfamily!r}: "
                f"{current.name}, {path.name}; split the styles or correct their OS/2 fields"
            )
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
    hinting_notes: list[str] = []
    for source in sources:
        subfamily = subfamily_of(source)
        flavor = outline_flavor(source)
        flavors.add(flavor)
        base = file_basename(args.name)

        if flavor == "cff":
            hinting_notes.append(
                f"- {source.name}: OTF/WOFF/WOFF2 retain the source CFF hint data; "
                "the cu2qu-derived TTF has no equivalent source hint program."
            )
            otf = package / f"{base}-{subfamily}.otf"
            apply_metadata(source, otf, args.name, subfamily, BRAND, args.layout_features)
            generated.append(otf)
            print(f"  metadata + otf  {otf.name}")

            ttf = otf.with_suffix(".ttf")
            convert_ttf(otf, ttf)
            generated.append(ttf)
        else:
            hinting_notes.append(
                f"- {source.name}: TTF retains source TrueType instructions; "
                "the qu2cu-derived OTF/WOFF/WOFF2 do not carry those instructions."
            )
            ttf = package / f"{base}-{subfamily}.ttf"
            apply_metadata(source, ttf, args.name, subfamily, BRAND, args.layout_features)
            generated.append(ttf)
            print(f"  metadata + ttf  {ttf.name} (glyf source; OTF derived)")

            otf = ttf.with_suffix(".otf")
            convert_otf(ttf, otf)
            generated.append(otf)

        generated.extend(make_woff(otf))
        print(f"  ttf/woff/woff2 {otf.stem}")

    (out / "visuals" / "New-Images").mkdir(parents=True, exist_ok=True)
    print("  drop directory ready; specimens are rendered in Step 2b")

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
        f"- **PostScript Name**: {postscript_name(args.name, subfamily_of(sources[0]))}",
        f"- **Source Font**: {sources[0].name}", "",
        "## Name Derivation",
        f"- Slug derivation: {args.name} → {slug}",
        f"- Package derivation: {args.name} → {package.name}", "",
        "## Output Paths",
        f"- Font Package: {rel(package)}/",
    ]
    (out / "name-report.md").write_text("\n".join(name_report) + "\n", encoding="utf-8")

    # Both license archives carry the same clean font binaries. Personal-Use
    # may additionally carry the like-request note at the archive root.
    like_file = args.like_file
    commercial_archive = out / f"{package.name}-Commercial-Use.zip"
    personal_archive = out / f"{package.name}-Personal-Use.zip"
    build_archive(commercial_archive, package, None)
    build_archive(personal_archive, package, like_file, note_entry_name=LIKE_FILE_NAME)
    archive_report, archives_ok = verify_archive_font_payloads(commercial_archive, personal_archive)
    print(f"  archives       {package.name}-Commercial-Use.zip (clean), "
          f"{package.name}-Personal-Use.zip (same font binaries)")
    print(f"  archive audit  {archive_report} — {'PASS' if archives_ok else 'FAIL'}")

    # technical audit
    audit = subprocess.run(
        [sys.executable, str(ROOT / "bin" / "font_package_audit.py"), str(package)],
        capture_output=True, text=True,
    )
    ots_report, ots_ok = run_ots(sorted(f for f in package.iterdir() if f.is_file()))
    legacy_trial_archive = out / f"{package.name}-Free-Trial-Demo.zip"
    legacy_archive_note = "no legacy trial archive present"
    if args.force and legacy_trial_archive.exists():
        if audit.returncode == 0 and ots_ok and archives_ok:
            try:
                legacy_trial_archive.unlink()
                legacy_archive_note = "removed obsolete Free-Trial-Demo archive during successful forced rebuild"
            except OSError as error:
                legacy_archive_note = f"failed to remove obsolete Free-Trial-Demo archive: {error}"
                archives_ok = False
        else:
            legacy_archive_note = "kept because the replacement package did not pass its audit"
        print(f"  legacy archive {legacy_archive_note}")
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
              f"- **GSUB/GPOS source**: {rel(args.layout_features) if args.layout_features else 'preserved from source font'}",
              "- **Archive payloads**: Commercial-Use and Personal-Use contain identical font binaries.", "",
              "## OUTLINE CONVERSION AND HINTING", "", *hinting_notes, "",
              f"- **Legacy trial archive cleanup**: {legacy_archive_note}.", "",
              "## PRE-FLIGHT AUDIT (raw inputs)", "", "```",
              preflight_report, "```", "", "## TECHNICAL FONT AUDIT (Pro package)", "", "```",
              audit.stdout.strip(), "```", "", "## OPENTYPE SANITIZER (independent parser)", "", "```",
              ots_report, "```", "", "## ARCHIVE FONT PAYLOAD CHECK", "", archive_report, ""]
    (out / "audit-report.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    print()
    print(f"✅ Font Metadata & Package Complete: {rel(out)}/")
    print(f"- Winning Font Name: {args.name} (Slug: {slug})")
    print(f"- Pro package: {', '.join(sorted({p.suffix[1:].upper() for p in generated}))}")
    print("- Archives: Commercial-Use and Personal-Use carry identical font binaries")
    print(f"- Final images: NOT PROCESSED — drop them into "
          f"{rel(out)}/visuals/New-Images/ then run /font-final-images")
    passed = audit.returncode == 0 and ots_ok and archives_ok
    print(f"- Audit: {'PASS' if passed else 'FAIL — see audit-report.md'}")
    if not passed:
        if audit.returncode != 0:
            print(audit.stdout.strip()[-600:])
        if not ots_ok:
            print(ots_report[-600:])
        if not archives_ok:
            print(archive_report)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
