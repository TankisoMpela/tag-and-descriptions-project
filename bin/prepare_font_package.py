#!/usr/bin/env python3
"""Deterministic font preparation for the FontFairy workflow (Agent 13).

This is the whole mechanical pass in one invocation: discover the raw fonts,
write branded OTF and TTF files plus WOFF web-font copies in separate folders,
leave the image drop directory, write audit reports, build one font-named ZIP,
then extract and test the exact archived files with fontTools, OpenType
Sanitizer, FreeType/fontconfig and HarfBuzz before declaring the package ready.

The source outline format remains the native package master. A CFF/OTF source
is normalized into OTF, converted to TTF, and copied to WOFF from OTF. A
glyf/TTF source is normalized directly into TTF, converted to CFF/OTF with
qu2cu, and copied to WOFF from TTF. The source-to-output audit checks character
mapping, layout, shaping, every legacy `kern` pair, and native-format hint
preservation; raster deltas are recorded in the same audit report. Branded
metadata is normalized across name-table platforms, while `head.created` remains
the source value and `head.modified` reflects the save time.

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
import math
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from fontTools.agl import toUnicode
from fontTools.fontBuilder import FontBuilder
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.pens.qu2cuPen import Qu2CuPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable
from fontTools.ttLib import TTFont
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageStat

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
FONT_SUFFIXES = (".otf", ".ttf")
DELIVERY_FORMATS = {"OTF": ".otf", "TTF": ".ttf", "WOFF": ".woff"}
TT_HINT_TABLES = ("cvt ", "fpgm", "prep", "gasp", "VDMX", "LTSH", "hdmx")
SHAPING_PROBES = (
    "Hamburgefontsiv AaBbZz",
    "office affinity AVATAR To Wa Yo Ta",
    "0123456789",
    ".,!?:;-()[]",
)


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

    # Normalize the face-style bits used by applications to identify regular,
    # bold and italic faces. Other OS/2 fields remain source-derived.
    font["OS/2"].fsType = 0
    font["OS/2"].achVendID = brand["vendor_id"][:4].ljust(4)
    os2 = font["OS/2"]
    style_bits = (0x0002 if os2.fsSelection & (0x0001 | 0x0200) else 0) | (
        0x0001 if os2.fsSelection & 0x0020 else 0
    )
    if style_bits:
        os2.fsSelection &= ~0x0040  # REGULAR cannot accompany bold or italic.
    font["head"].macStyle = (font["head"].macStyle & ~0x0003) | style_bits
    if "CFF " in font and "post" in font:
        # CFF OpenType fonts use post format 3, not the TrueType glyph-name table.
        font["post"].formatType = 3.0

    ensure_unicode_cmap(font)

    # cmap language IDs are reserved and must be zero for OpenType cmap
    # subtables. Some legacy source files carry a nonzero value; normalize the
    # delivered copies while leaving the source bytes untouched so the
    # independent sanitizer can validate every prepared format.
    if "cmap" in font:
        for cmap_table in font["cmap"].tables:
            cmap_table.language = 0


def ensure_unicode_cmap(font) -> None:
    """Add standard Unicode cmaps from Adobe glyph names when only legacy maps exist.

    Existing Unicode maps are kept intact. For legacy MacRoman/Windows-symbol
    fonts, glyph names provide Unicode semantics; ambiguous and multi-scalar
    names are omitted and the release audit checks resulting text coverage.
    """
    cmap_table = font["cmap"]
    if any(
        (table.platformID == 0 and table.platEncID in (3, 4, 6))
        or (table.platformID == 3 and table.platEncID in (1, 10))
        for table in cmap_table.tables
    ):
        return

    unicode_map: dict[int, str] = {}
    for glyph_name in font.getGlyphOrder():
        value = toUnicode(glyph_name)
        if len(value) != 1:
            continue
        codepoint = ord(value)
        if codepoint > 0x10FFFF or 0xD800 <= codepoint <= 0xDFFF:
            continue
        unicode_map.setdefault(codepoint, glyph_name)
    if not unicode_map:
        raise ValueError("font has no Unicode cmap and glyph names cannot supply one")

    cmap_table.tables.extend([
        _new_cmap_subtable(4, 0, 3, {cp: glyph for cp, glyph in unicode_map.items() if cp < 0xFFFF}),
        _new_cmap_subtable(4, 3, 1, {cp: glyph for cp, glyph in unicode_map.items() if cp < 0xFFFF}),
    ])
    supplementary = {cp: glyph for cp, glyph in unicode_map.items() if cp > 0xFFFF}
    if supplementary:
        cmap_table.tables.extend([
            _new_cmap_subtable(12, 0, 4, unicode_map),
            _new_cmap_subtable(12, 3, 10, unicode_map),
        ])


def _new_cmap_subtable(format_number: int, platform_id: int, encoding_id: int,
                       mapping: dict[int, str]):
    table = CmapSubtable.newSubtable(format_number)
    table.platformID = platform_id
    table.platEncID = encoding_id
    table.language = 0
    table.cmap = dict(mapping)
    return table


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


def outline_flavor(path: Path) -> str:
    """Return "cff" or "glyf" — which outline table the source carries.

    The source flavor determines the native master format; only the alternate
    outline format is derived.
    """
    with TTFont(str(path)) as font:
        if "CFF " in font:
            return "cff"
        if "glyf" in font:
            return "glyf"
    raise SystemExit(f"{path.name}: neither CFF nor glyf outlines")


def convert_otf(ttf: Path, otf: Path, max_err: float = 1.0) -> None:
    """Derive a CFF/OTF sibling from a glyf-only source, with fontTools qu2cu.

    A TrueType demo has no CFF table to carry over, so the outlines are rebuilt
    as cubic charstrings and every other table — name, OS/2, cmap, metrics,
    GSUB/GPOS, kern — is kept from the native branded TTF. TrueType-only tables (hinting,
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
    font["post"].formatType = 3.0
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


def convert_ttf(otf: Path, ttf: Path) -> None:
    """Generate a TrueType-outline sibling with FontForge, preserving layout."""
    fontforge = shutil.which("fontforge")
    if not fontforge:
        raise SystemExit("FontForge is required to produce the TTF delivery format")
    script = "import fontforge, sys\nfont = fontforge.open(sys.argv[1])\nfont.generate(sys.argv[2])\nfont.close()\n"
    with tempfile.NamedTemporaryFile("w", suffix=".py", encoding="utf-8", delete=False) as handle:
        handle.write(script)
        script_path = Path(handle.name)
    try:
        result = subprocess.run(
            [fontforge, "-lang=py", "-script", str(script_path), str(otf), str(ttf)],
            capture_output=True, text=True,
        )
        if result.returncode != 0 or not ttf.is_file():
            raise SystemExit(
                "FontForge TTF conversion failed: " + " ".join((result.stdout + result.stderr).split())[-600:]
            )
    finally:
        script_path.unlink(missing_ok=True)


def make_woff(master: Path, woff: Path) -> None:
    """Create a WOFF copy from the prepared native-outline master."""
    with TTFont(str(master)) as font:
        font.flavor = "woff"
        font.save(str(woff))
        font.flavor = None


def unicode_mapping(path: Path) -> dict[int, str]:
    """Read Unicode codepoint-to-glyph names, mirroring the package audit."""
    with TTFont(str(path)) as font:
        mapping: dict[int, str] = {}
        for table in font["cmap"].tables:
            if ((table.platformID == 0 and table.platEncID in (3, 4, 6)) or
                    (table.platformID == 3 and table.platEncID in (1, 10))):
                mapping.update(table.cmap)
        if mapping:
            return mapping
        # A legacy source without Unicode subtables is expected to receive this
        # same Adobe Glyph List fallback in ensure_unicode_cmap().
        for glyph_name in font.getGlyphOrder():
            value = toUnicode(glyph_name)
            if len(value) == 1:
                codepoint = ord(value)
                if codepoint <= 0x10FFFF and not 0xD800 <= codepoint <= 0xDFFF:
                    mapping.setdefault(codepoint, glyph_name)
        return mapping


def layout_inventory(path: Path) -> dict[str, tuple[tuple[str, ...], tuple[str, ...]]]:
    """Return the GSUB/GPOS script and feature tags for one font."""
    inventory: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {}
    with TTFont(str(path)) as font:
        for tag in ("GSUB", "GPOS"):
            if tag not in font:
                continue
            table = font[tag].table
            scripts = tuple(sorted(
                record.ScriptTag for record in table.ScriptList.ScriptRecord
            )) if table.ScriptList else ()
            features = tuple(sorted({
                record.FeatureTag for record in table.FeatureList.FeatureRecord
            })) if table.FeatureList else ()
            inventory[tag] = scripts, features
    return inventory


def legacy_kern_signature(path: Path) -> tuple[tuple[object, ...], ...]:
    """Return normalized legacy kern subtables and every pair adjustment."""
    with TTFont(str(path)) as font:
        if "kern" not in font:
            return ()
        signature = []
        for subtable in font["kern"].kernTables:
            pairs = tuple(sorted(
                getattr(subtable, "kernTable", {}).items(),
                key=lambda item: repr(item[0]),
            ))
            if pairs:
                signature.append((
                    getattr(subtable, "version", None),
                    getattr(subtable, "coverage", None),
                    getattr(subtable, "format", None),
                    pairs,
                ))
        return tuple(signature)


def _compiled_table(font, tag: str) -> bytes:
    return font[tag].compile(font)


def _truetype_hint_signature(path: Path) -> tuple[dict[str, bytes], dict[str, bytes]]:
    """Capture TrueType hint tables and each nonempty glyph instruction stream."""
    tables: dict[str, bytes] = {}
    programs: dict[str, bytes] = {}
    with TTFont(str(path)) as font:
        for tag in TT_HINT_TABLES:
            if tag in font:
                tables[tag] = _compiled_table(font, tag)
        if "glyf" in font:
            for glyph_name in font.getGlyphOrder():
                program = getattr(font["glyf"][glyph_name], "program", None)
                bytecode = program.getBytecode() if program is not None else b""
                if bytecode:
                    programs[glyph_name] = bytecode
    return tables, programs


def _outline_metrics_signature(path: Path, flavor: str) -> dict[str, bytes]:
    """Capture native outline and advance-metric tables for exact-copy checks."""
    tags = (("glyf", "loca") if flavor == "glyf" else ()) + (
        "hhea", "hmtx", "vhea", "vmtx", "VORG"
    )
    with TTFont(str(path)) as font:
        return {tag: _compiled_table(font, tag) for tag in tags if tag in font}


def _cff_hint_signature(
    path: Path,
) -> tuple[dict[str, tuple[object, ...]], tuple[tuple[str, object], ...]]:
    """Capture CFF charstring programs, subroutines, and hint parameters."""
    with TTFont(str(path)) as font:
        top = font["CFF "].cff.topDictIndex[0]

        def freeze(value):
            if isinstance(value, (list, tuple)):
                return tuple(freeze(item) for item in value)
            if isinstance(value, dict):
                return tuple(sorted((key, freeze(item)) for key, item in value.items()))
            if isinstance(value, bytearray):
                return bytes(value)
            return value

        def programs(charstrings) -> dict[str, tuple[object, ...]]:
            values: dict[str, tuple[object, ...]] = {}
            for name in charstrings.keys():
                charstring = charstrings[name]
                charstring.decompile()
                values[name] = tuple(freeze(charstring.program or ()))
            return values

        glyph_programs = programs(top.CharStrings)
        subroutines: list[tuple[str, object]] = []
        global_subrs = font["CFF "].cff.GlobalSubrs
        for index, charstring in enumerate(global_subrs):
            charstring.decompile()
            subroutines.append((f"global:{index}", tuple(freeze(charstring.program or ()))))
        private = getattr(top, "Private", None)
        if private is not None:
            local_subrs = getattr(private, "Subrs", None)
            if local_subrs is not None:
                for index, charstring in enumerate(local_subrs):
                    charstring.decompile()
                    subroutines.append((f"local:{index}", tuple(freeze(charstring.program or ()))))
        hint_names = (
            "BlueValues", "OtherBlues", "FamilyBlues", "FamilyOtherBlues",
            "BlueScale", "BlueShift", "BlueFuzz", "StdHW", "StdVW",
            "StemSnapH", "StemSnapV", "ForceBold", "LanguageGroup",
            "ExpansionFactor",
        )
        hint_values = tuple(
            (name, freeze(getattr(private, name)))
            for name in hint_names
            if private is not None and hasattr(private, name)
        )
    return glyph_programs, tuple(subroutines) + hint_values


def _shape_signature(path: Path, sample: str) -> tuple[tuple[object, ...], ...]:
    """Shape text with HarfBuzz and return names, clusters, and positions."""
    try:
        import uharfbuzz as hb
    except ImportError as error:
        raise RuntimeError("uharfbuzz is required for source-to-output shaping checks") from error

    shape_path = path
    with tempfile.TemporaryDirectory(prefix="fontfairy-shape-") as temporary:
        if path.suffix.casefold() == ".woff":
            decoded = Path(temporary) / "decoded-font.otf"
            with TTFont(str(path)) as parsed:
                parsed.flavor = None
                parsed.save(str(decoded))
            shape_path = decoded
        with TTFont(str(shape_path)) as parsed:
            glyph_order = parsed.getGlyphOrder()
            upem = parsed["head"].unitsPerEm
        face = hb.Face(hb.Blob.from_file_path(str(shape_path)))
        font = hb.Font(face)
        font.scale = (upem, upem)
        buffer = hb.Buffer()
        buffer.add_str(sample)
        buffer.guess_segment_properties()
        hb.shape(font, buffer)
        result: list[tuple[object, ...]] = []
        for info, position in zip(buffer.glyph_infos, buffer.glyph_positions):
            if info.codepoint >= len(glyph_order):
                raise RuntimeError(f"HarfBuzz returned invalid glyph ID {info.codepoint}")
            result.append((
                glyph_order[info.codepoint], info.cluster,
                position.x_advance, position.y_advance,
                position.x_offset, position.y_offset,
            ))
        return tuple(result)


def _shared_shape_samples(paths: list[Path]) -> list[str]:
    maps = [unicode_mapping(path) for path in paths]
    common = set.intersection(*(set(mapping) for mapping in maps)) if maps else set()
    samples: list[str] = []
    for probe in SHAPING_PROBES:
        sample = "".join(char for char in probe if ord(char) in common)
        if len(sample) >= 2 and sample not in samples:
            samples.append(sample)
    return samples


def _render_comparison(master: Path, converted: Path, sample: str) -> tuple[list[str], bool]:
    """Report grayscale render deltas at buyer-relevant small sizes."""
    try:
        have_raqm = bool(getattr(ImageFont.core, "HAVE_RAQM", False))
        engine = ImageFont.Layout.RAQM if have_raqm else ImageFont.Layout.BASIC
        engine_name = "RAQM" if have_raqm else "basic"
        lines = [f"Raster engine: Pillow/FreeType {engine_name}; text: {sample!r}"]
        for size in (9, 12, 16, 24, 96, 200):
            fonts = [
                ImageFont.truetype(str(path), size=size, layout_engine=engine)
                for path in (master, converted)
            ]
            boxes = [font.getbbox(sample, anchor="ls") for font in fonts]
            left = min(box[0] for box in boxes)
            top = min(box[1] for box in boxes)
            right = max(math.ceil(font.getlength(sample)) for font in fonts)
            bottom = max(box[3] for box in boxes)
            width = max(1, right - left + 20)
            height = max(1, bottom - top + 20)
            baseline = 10 - top
            images = []
            for font in fonts:
                image = Image.new("L", (width, height), 0)
                ImageDraw.Draw(image).text(
                    (10 - left, baseline), sample, font=font, fill=255, anchor="ls"
                )
                images.append(image)
            difference = ImageChops.difference(images[0], images[1])
            union = ImageChops.lighter(images[0], images[1])
            bounds = union.getbbox()
            if bounds is None:
                return [*lines, f"{size}px: no rendered ink"], False
            difference_crop = difference.crop(bounds)
            union_crop = union.crop(bounds)
            mae = ImageStat.Stat(difference_crop).mean[0]
            changed = difference_crop.point(lambda value: 255 if value > 8 else 0).histogram()[255]
            ink = union_crop.point(lambda value: 255 if value > 8 else 0).histogram()[255]
            changed_percent = changed * 100 / max(ink, 1)
            lines.append(
                f"{size}px: MAE={mae:.2f}/255; changed ink pixels={changed_percent:.1f}%"
            )
        return lines, True
    except Exception as error:  # noqa: BLE001 - keep rendering failures visible in the audit
        return [f"small-size render comparison unavailable: {type(error).__name__}: {error}"], False


def run_conversion_audit(
    records: list[tuple[Path, Path, Path, Path, str]],
    layout_replaced: bool = False,
) -> tuple[str, bool]:
    """Compare raw, native-master, converted, and WOFF files before release."""
    sections: list[str] = []
    all_ok = True

    def check(condition: bool, label: str) -> None:
        nonlocal all_ok
        sections.append(f"- {label}: {'PASS' if condition else 'FAIL'}")
        all_ok = all_ok and condition

    for source, master, converted, woff, flavor in records:
        sections.extend([
            f"### {source.name}",
            f"- Native master: `{master.name}`; converted outline: `{converted.name}`; WOFF: `{woff.name}`.",
        ])
        try:
            source_map = unicode_mapping(source)
            master_map = unicode_mapping(master)
            converted_map = unicode_mapping(converted)
            woff_map = unicode_mapping(woff)
            check(
                source_map == master_map,
                f"source → native Unicode codepoint-to-glyph mapping ({len(source_map)} codepoints)",
            )
            check(
                master_map == converted_map,
                f"native → converted Unicode codepoint-to-glyph mapping ({len(master_map)} codepoints)",
            )
            check(
                master_map == woff_map,
                f"native → WOFF Unicode codepoint-to-glyph mapping ({len(master_map)} codepoints)",
            )

            required_outline_tags = (
                ("glyf", "loca", "hhea", "hmtx")
                if flavor == "glyf" else ("hhea", "hmtx")
            )
            source_outline = _outline_metrics_signature(source, flavor)
            master_outline = _outline_metrics_signature(master, flavor)
            woff_outline = _outline_metrics_signature(woff, flavor)
            check(
                all(tag in source_outline for tag in required_outline_tags)
                and source_outline == master_outline,
                "source outline and advance metrics preserved in native master",
            )
            check(
                all(tag in master_outline for tag in required_outline_tags)
                and master_outline == woff_outline,
                "native outline and advance metrics preserved in WOFF",
            )

            master_layout = layout_inventory(master)
            converted_layout = layout_inventory(converted)
            woff_layout = layout_inventory(woff)
            if not layout_replaced:
                check(
                    layout_inventory(source) == master_layout,
                    "source → native GSUB/GPOS script and feature inventory",
                )
            check(master_layout == converted_layout,
                  "native → converted GSUB/GPOS script and feature inventory")
            check(master_layout == woff_layout,
                  "native → WOFF GSUB/GPOS script and feature inventory")

            source_kern = legacy_kern_signature(source)
            master_kern = legacy_kern_signature(master)
            converted_kern = legacy_kern_signature(converted)
            woff_kern = legacy_kern_signature(woff)
            pair_count = sum(len(record[3]) for record in source_kern)
            check(source_kern == master_kern,
                  f"legacy kern pairs preserved in native master ({pair_count} pairs)")
            check(source_kern == converted_kern,
                  "legacy kern pairs preserved in converted outline")
            check(source_kern == woff_kern,
                  "legacy kern pairs preserved in WOFF")

            if flavor == "glyf":
                source_hints = _truetype_hint_signature(source)
                master_hints = _truetype_hint_signature(master)
                woff_hints = _truetype_hint_signature(woff)
                hint_table_count = len(source_hints[0])
                instructed_glyphs = len(source_hints[1])
                check(source_hints == master_hints,
                      f"TrueType hint data preserved in native TTF ({hint_table_count} tables; {instructed_glyphs} instructed glyphs)")
                check(source_hints == woff_hints,
                      "TrueType hint data preserved in WOFF")
                sections.append("- Converted CFF/OTF intentionally has no TrueType hint program; native TTF/WOFF retain it.")
            else:
                source_hints = _cff_hint_signature(source)
                master_hints = _cff_hint_signature(master)
                woff_hints = _cff_hint_signature(woff)
                check(source_hints == master_hints,
                      f"CFF charstring and hint data preserved in native OTF ({len(source_hints[0])} glyph programs)")
                check(source_hints == woff_hints,
                      "CFF charstring and hint data preserved in WOFF")
                sections.append("- Converted glyf/TTF cannot carry the source CFF charstring hints; native OTF/WOFF retain them.")

            samples = _shared_shape_samples([master, converted, woff])
            if not samples:
                check(False, "no shared HarfBuzz sample text available")
            else:
                for comparison in (converted, woff):
                    matches = True
                    mismatch = ""
                    for sample in samples:
                        if _shape_signature(master, sample) != _shape_signature(comparison, sample):
                            matches = False
                            mismatch = sample
                            break
                    check(
                        matches,
                        f"HarfBuzz shaping: native master vs {comparison.name} ({len(samples)} probes)"
                        + (f"; first mismatch {mismatch!r}" if not matches else ""),
                    )

            raster_text = next(
                (sample for sample in samples if any(char.isalpha() for char in sample)),
                samples[0] if samples else "",
            )
            if raster_text:
                render_lines, render_ok = _render_comparison(master, converted, raster_text)
                sections.extend(["- Raster comparison (9–24 px small sizes; 96/200 px outline reference; informational):", *[
                    f"  - {line}" for line in render_lines
                ]])
                if not render_ok:
                    check(False, "small-size raster renderer completed")
        except Exception as error:  # noqa: BLE001 - report a blocking conversion-audit failure
            sections.append(f"- Conversion audit error: {type(error).__name__}: {error}")
            all_ok = False
        sections.append("")
    return "\n".join(sections).strip(), all_ok


def run_ots(files: list[Path]) -> tuple[str, bool]:
    """Sanitize every final delivered font with the OpenType Sanitizer.

    This is an independent, spec-level parser, not a duplicate of
    font_package_audit: that tool reads fsType, name IDs and glyph count through
    fontTools, which loads some malformed fonts without complaint until a broken
    table is touched. OTS parses every table and fails closed. It catches the
    class of defect that shipped here once — FontForge wrote OS/2 version 5 at
    the version-4 length, and OTS reports it as "OS/2: Failed to read version
    5-specific fields" while fontTools only raises a bare struct.error.

    This is a required release check; missing OTS blocks the package.
    """
    ots = shutil.which("ots-sanitize")
    if ots is None:
        return ("ots-sanitize not installed; required independent validation unavailable.", False)

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


def run_freetype_scan(files: list[Path]) -> tuple[str, bool]:
    """Require FreeType/fontconfig to open each final font and report a face."""
    scanner = shutil.which("fc-scan")
    if scanner is None:
        return ("fc-scan not installed; required FreeType validation unavailable.", False)
    lines: list[str] = []
    ok = True
    for path in files:
        result = subprocess.run(
            [scanner, "--format", "%{family}\\t%{style}\\n", str(path)],
            capture_output=True, text=True,
        )
        identity = result.stdout.strip()
        if result.returncode == 0 and identity:
            lines.append(f"{path.name}: opened by FreeType ({identity}) — PASS")
        else:
            ok = False
            detail = " ".join((result.stdout + result.stderr).split())
            lines.append(f"{path.name}: FreeType open failed — {detail[:200]}")
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


def build_archive(target: Path, package: Path) -> None:
    """Build one reproducible ZIP with distinct OTF, TTF, and WOFF folders."""
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for font_file in sorted(p for p in package.rglob("*") if p.is_file()):
            if font_file.suffix.casefold() in DELIVERY_FORMATS.values():
                relative = font_file.relative_to(package).as_posix()
                info = zipfile.ZipInfo(f"{package.name}/{relative}", date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, font_file.read_bytes())


def verify_archive_payload(
    archive_path: Path,
    package: Path,
    allowed_suffixes: tuple[str, ...] = tuple(DELIVERY_FORMATS.values()),
) -> tuple[str, bool]:
    """Require the named ZIP to contain exactly the allowed prepared fonts."""
    expected = {
        f"{package.name}/{path.relative_to(package).as_posix()}": path.read_bytes()
        for path in sorted(p for p in package.rglob("*") if p.is_file())
        if path.suffix.casefold() in allowed_suffixes
    }
    try:
        with zipfile.ZipFile(archive_path) as archive:
            actual = {name: archive.read(name) for name in archive.namelist()}
    except (OSError, zipfile.BadZipFile) as error:
        return f"cannot read archive: {error}", False
    ok = bool(expected) and actual == expected
    detail = (
        f"exact font payload: {len(expected)} file(s)"
        if ok else "archive entries do not exactly match the allowed prepared font files"
    )
    return detail, ok


def run_harfbuzz_smoke(files: list[Path]) -> tuple[str, bool]:
    """Shape representative text from the exact final files and reject .notdef."""
    try:
        import uharfbuzz as hb
    except ImportError:
        return ("uharfbuzz not installed; required shaping validation unavailable.", False)
    from fontTools.ttLib import TTFont

    lines: list[str] = []
    ok = True
    for path in files:
        shape_path = path
        decoded_woff = None
        with TTFont(path) as parsed:
            if path.suffix.casefold() == ".woff":
                decoded_woff = tempfile.TemporaryDirectory(prefix="fontfairy-woff-shape-")
                shape_path = Path(decoded_woff.name) / "decoded-font.otf"
                parsed.flavor = None
                parsed.save(str(shape_path))
            cmap = {}
            for table in parsed["cmap"].tables:
                if ((table.platformID == 0 and table.platEncID in (3, 4, 6)) or
                    (table.platformID == 3 and table.platEncID in (1, 10))) and hasattr(table, "cmap"):
                    cmap.update(table.cmap)
        letter_sample = "".join(
            char for char in "Hamburgefontsiv AaBbZz" if ord(char) in cmap
        )
        samples = [letter_sample] if letter_sample else []
        digit_sample = "".join(char for char in "0123456789" if ord(char) in cmap)
        if digit_sample:
            samples.append(digit_sample)
        punctuation = "".join(char for char in ".,!?;:-()[]" if ord(char) in cmap)
        if punctuation:
            samples.append(punctuation)
        if not samples:
            ok = False
            lines.append(f"{path.name}: no supported smoke-test characters in Unicode cmap")
            if decoded_woff is not None:
                decoded_woff.cleanup()
            continue
        for sample in samples:
            try:
                face = hb.Face(hb.Blob.from_file_path(str(shape_path)))
                font = hb.Font(face)
                font.scale = (face.upem, face.upem)
                buffer = hb.Buffer()
                buffer.add_str(sample)
                buffer.guess_segment_properties()
                hb.shape(font, buffer)
                missing = [info.cluster for info in buffer.glyph_infos if info.codepoint == 0]
                if missing or not buffer.glyph_infos:
                    ok = False
                    lines.append(f"{path.name}: FAIL shaping {sample!r}; missing glyph IDs at {missing}")
                else:
                    suffix = " (decoded WOFF content)" if path.suffix.casefold() == ".woff" else ""
                    lines.append(f"{path.name}: shaped {sample!r}{suffix} — PASS")
            except Exception as error:  # noqa: BLE001 - report a blocking validator failure
                ok = False
                lines.append(f"{path.name}: HarfBuzz error — {error}")
                break
        if decoded_woff is not None:
            decoded_woff.cleanup()
    return ("\n".join(lines), ok)


def verify_final_archive(
    archive_path: Path,
    package: Path,
    allowed_suffixes: tuple[str, ...] = tuple(DELIVERY_FORMATS.values()),
) -> tuple[str, bool, str, str, str]:
    """Extract and independently test the exact font files buyers will receive."""
    payload_report, payload_ok = verify_archive_payload(archive_path, package, allowed_suffixes)
    if not payload_ok:
        return payload_report, False, "not run (archive payload check failed)", "not run", "not run"
    with tempfile.TemporaryDirectory(prefix="fontfairy-final-zip-") as temporary:
        extracted = Path(temporary) / package.name
        extracted.mkdir()
        with zipfile.ZipFile(archive_path) as archive:
            for member in archive.namelist():
                parts = Path(member).parts
                if (len(parts) != 3 or parts[0] != package.name or
                        parts[1] not in DELIVERY_FORMATS or parts[2] in ("", ".", "..")):
                    return "unsafe or unexpected archive path", False, "not run", "not run", "not run"
                destination = extracted / parts[1] / parts[2]
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(archive.read(member))

        font_files = sorted(p for p in extracted.rglob("*") if p.is_file())
        from font_package_audit import audit_file
        audit_ok = bool(font_files) and all(
            path.suffix.casefold() in DELIVERY_FORMATS.values() and audit_file(path)
            for path in font_files
        )
        ots_report, ots_ok = run_ots(font_files)
        freetype_report, freetype_ok = run_freetype_scan(font_files)
        harfbuzz_report, harfbuzz_ok = run_harfbuzz_smoke(font_files)
        detail = (
            f"archive CRC/payload: PASS ({payload_report}); extracted font audit: "
            f"{'PASS' if audit_ok else 'FAIL'}"
        )
        return detail, audit_ok and ots_ok and freetype_ok and harfbuzz_ok, ots_report, freetype_report, harfbuzz_report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--workspace", required=True, type=Path, help="font-factory/fonts/{input-slug}")
    parser.add_argument("--name", required=True, help="final font name, exact spelling")
    parser.add_argument("--number", help="catalogue number; omit to read visual-direction/catalogue-number.txt")
    parser.add_argument("--description-file", type=Path, default=None,
                        help="authored description.txt to install at the output root")
    parser.add_argument("--layout-features", type=Path, default=None,
                        help="optional Adobe Feature File (.fea) that replaces GSUB/GPOS")
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
    package.mkdir(parents=True, exist_ok=True)
    if args.force:
        for old_entry in package.iterdir():
            if old_entry.is_file():
                old_entry.unlink()
            elif old_entry.is_dir():
                shutil.rmtree(old_entry)
    format_dirs = {label: package / label for label in DELIVERY_FORMATS}
    for directory in format_dirs.values():
        directory.mkdir(parents=True, exist_ok=True)
    print(f"product  {number}-{slug}")
    print(f"package  {rel(package)}/")

    for dropped, kept in skipped:
        print(f"  skipped        {dropped.name} — duplicate {subfamily_of(dropped)}; using {kept.name}")

    generated: list[Path] = []
    flavors: set[str] = set()
    conversion_records: list[tuple[Path, Path, Path, Path, str]] = []
    for source in sources:
        subfamily = subfamily_of(source)
        flavor = outline_flavor(source)
        flavors.add(flavor)
        base = file_basename(args.name)
        otf = format_dirs["OTF"] / f"{base}-{subfamily}.otf"
        ttf = format_dirs["TTF"] / f"{base}-{subfamily}.ttf"

        if flavor == "cff":
            apply_metadata(source, otf, args.name, subfamily, BRAND, args.layout_features)
            master = otf
            converted = ttf
            convert_ttf(master, converted)
            apply_metadata(converted, converted, args.name, subfamily, BRAND, args.layout_features)
        else:
            # Keep the original glyf outlines and TrueType instruction streams
            # in the TTF delivery. The CFF OTF is a separate derived format.
            apply_metadata(source, ttf, args.name, subfamily, BRAND, args.layout_features)
            master = ttf
            converted = otf
            convert_otf(master, converted)
        generated.append(otf)
        print(f"  prepared OTF   {otf.name}")

        generated.append(ttf)
        print(f"  prepared TTF   {ttf.name}")

        woff = format_dirs["WOFF"] / f"{base}-{subfamily}.woff"
        make_woff(master, woff)
        generated.append(woff)
        print(f"  prepared WOFF  {woff.name}")
        conversion_records.append((source, master, converted, woff, flavor))

    conversion_report, conversion_ok = run_conversion_audit(
        conversion_records, layout_replaced=args.layout_features is not None
    )
    print(f"  source/output audit {'PASS' if conversion_ok else 'FAIL'}")

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

    archive_path = out / f"{args.name.strip()}.zip"
    build_archive(archive_path, package)
    archive_report, final_files_ok, ots_report, freetype_report, harfbuzz_report = verify_final_archive(
        archive_path, package, allowed_suffixes=tuple(DELIVERY_FORMATS.values())
    )
    print(f"  archive        {archive_path.name}")
    print(f"  final files    {archive_report} — {'PASS' if final_files_ok else 'FAIL'}")

    # technical audit
    audit = subprocess.run(
        [sys.executable, str(ROOT / "bin" / "font_package_audit.py"), str(package)],
        capture_output=True, text=True,
    )
    legacy_archive_note = "no obsolete archives found"
    if audit.returncode == 0 and final_files_ok and conversion_ok:
        obsolete_archives = [path for path in out.glob("*.zip") if path != archive_path]
        try:
            for old_archive in obsolete_archives:
                old_archive.unlink()
            if obsolete_archives:
                legacy_archive_note = f"removed {len(obsolete_archives)} obsolete archive(s)"
        except OSError as error:
            final_files_ok = False
            legacy_archive_note = f"failed to remove an obsolete archive: {error}"
    print(f"  archive cleanup {legacy_archive_note}")
    stamp = _datetime.datetime.now(_datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    derivation = "CFF/OTF master preserved; TTF derived; WOFF copied from CFF master" if flavors == {"cff"} else (
        "TrueType master preserved in TTF/WOFF; CFF/OTF derived" if flavors == {"glyf"} else
        "native outline preserved per style; alternate outline derived; WOFF copied from native master"
    )
    package_inventory = [
        f"- `{path.relative_to(package).as_posix()}` ({path.stat().st_size} bytes)"
        for path in sorted(p for p in package.rglob("*") if p.is_file())
    ]
    report = ["# Font Preparation Audit Report", "", "## Product Information",
              f"- **Font Name**: {args.name}", f"- **Catalogue Number**: {number}",
              f"- **Output Slug**: {slug}", f"- **Package Basename**: {package.name}",
              f"- **Date**: {stamp}", f"- **Outline Derivation**: {derivation}",
              f"- **GSUB/GPOS source**: {rel(args.layout_features) if args.layout_features else 'preserved from source font'}",
              f"- **Archive**: `{archive_path.name}` contains OTF, TTF, and WOFF files in separate folders.", "",
              "## PACKAGE CONTENTS", "", *package_inventory, "",
              f"- **Archive cleanup**: {legacy_archive_note}.", "",
              "## PRE-FLIGHT AUDIT (raw inputs)", "", "```",
              preflight_report, "```", "", "## SOURCE-TO-OUTPUT CONVERSION AUDIT", "", "```",
              conversion_report, "```", "", "## TECHNICAL FONT AUDIT (Pro package)", "", "```",
              audit.stdout.strip(), "```", "", "## FINAL ARCHIVE FONT AUDIT (extracted buyer files)", "", "```",
              archive_report, "```", "", "## OPENTYPE SANITIZER", "", "```",
              ots_report, "```", "", "## FREETYPE / FONTCONFIG OPEN CHECK", "", "```",
              freetype_report, "```", "", "## HARFBUZZ SHAPING SMOKE TEST", "", "```",
              harfbuzz_report, "```", ""]
    (out / "audit-report.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    print()
    print(f"✅ Font Metadata & Package Complete: {rel(out)}/")
    print(f"- Winning Font Name: {args.name} (Slug: {slug})")
    print(f"- Font files: {len(generated)} files ({len(generated)//3} each in OTF, TTF, and WOFF)")
    print(f"- Archive: {archive_path.name}")
    print(f"- Final images: NOT PROCESSED — drop them into "
          f"{rel(out)}/visuals/New-Images/ then run /font-final-images")
    passed = audit.returncode == 0 and final_files_ok and conversion_ok
    print(f"- Audit: {'PASS' if passed else 'FAIL — see audit-report.md'}")
    if not passed:
        if audit.returncode != 0:
            print(audit.stdout.strip()[-600:])
        if not final_files_ok:
            print(archive_report[-900:])
            print(ots_report[-600:])
            print(freetype_report[-600:])
            print(harfbuzz_report[-600:])
        if not conversion_ok:
            print(conversion_report[-1600:])
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
