#!/usr/bin/env python3
"""Audit the prepared font binaries (Agent 13 release gate).

Checks OS/2 fsType, branded name values, platform/language normalization,
removed metadata records and tables, glyph count, and CFF names/identifiers.
The audit is read-only and fails if the package folder is missing, empty, or
any font file cannot be inspected.

Usage:
    python3 bin/font_package_audit.py \
        "outputs/font-preparation/{NUM}-{slug}/{Font-Name}"
"""
from __future__ import annotations

import argparse
import struct
from pathlib import Path

from fontTools.misc.timeTools import timestampToString
from fontTools.ttLib import TTFont

from prepare_font_package import (
    BRAND,
    BRANDED_NAME_IDS,
    REMOVED_NAME_IDS,
    REMOVED_TABLES,
    postscript_name,
    postscript_prefix,
    referenced_name_ids,
)

FONT_SUFFIXES = (".otf", ".ttf", ".woff", ".woff2")
REQUIRED_NAME_IDS = set(range(15)) - {10}
WINDOWS_ENGLISH = (3, 1, 0x409)


def woff_optional_blocks_absent(path: Path) -> bool:
    """Check that WOFF containers have no extended metadata or private block."""
    is_woff2 = path.suffix.lower() == ".woff2"
    fmt = ">4s4sIHHIIHHIIIII" if is_woff2 else ">4s4sIHHIHHIIIII"
    header_size = struct.calcsize(fmt)
    with path.open("rb") as stream:
        header = stream.read(header_size)
    if len(header) != header_size:
        return False
    fields = struct.unpack(fmt, header)
    expected_signature = b"wOF2" if is_woff2 else b"wOFF"
    if fields[0] != expected_signature:
        return False
    optional_fields = fields[9:] if is_woff2 else fields[8:]
    return not any(optional_fields)


def audit_file(path: Path) -> bool:
    """Print one file's audit. Return True only if all checks pass."""
    print(f"--- Auditing: {path.name} ---")
    try:
        with TTFont(str(path)) as font:
            fstype = font["OS/2"].fsType
            names = {name_id: font["name"].getDebugName(name_id)
                     for name_id in (1, 4, 6)}
            glyph_count = len(font.getGlyphOrder())
            designer = font["name"].getDebugName(9)
            description = font["name"].getDebugName(10)
            created = font["head"].created
            modified = font["head"].modified
            if fstype != 0:
                print(f"OS/2 fsType: {fstype} — ❌ FAIL (expected 0)")
            else:
                print("OS/2 fsType: 0 — ✅ PASS")
            print(f"Name ID 1 (Family): {names[1]}")
            print(f"Name ID 4 (Full Name): {names[4]}")
            print(f"Name ID 6 (PostScript): {names[6]}")
            print(f"Name ID 9 (Designer): {designer}")
            print(f"Name ID 10 (Description): {description or '(removed)'}")
            print(f"head.created: {created} ({timestampToString(created)})")
            print(f"head.modified: {modified} ({timestampToString(modified)})")
            print(f"Glyph count: {glyph_count}")
            names_table = font["name"]
            name_records_ok = True
            for name_id in BRANDED_NAME_IDS:
                records = [r for r in names_table.names if r.nameID == name_id]
                if name_id in REQUIRED_NAME_IDS and not records:
                    name_records_ok = False
                    print(f"Name ID {name_id}: ❌ FAIL (required branded record is missing)")
                elif records and (
                    len(records) != 1
                    or (records[0].platformID, records[0].platEncID, records[0].langID)
                    != WINDOWS_ENGLISH
                ):
                    name_records_ok = False
                    print(f"Name ID {name_id}: ❌ FAIL (stale platform/language variant remains)")
            for name_id in REMOVED_NAME_IDS:
                if any(r.nameID == name_id for r in names_table.names):
                    name_records_ok = False
                    print(f"Name ID {name_id}: ❌ FAIL (source-only/reserved record remains)")
            family = names_table.getDebugName(1) or ""
            style = names_table.getDebugName(2) or ""
            expected_names = {
                0: BRAND["copyright_pro"],
                1: family,
                2: style,
                3: f"{BRAND['year']};{BRAND['foundry']};{family}-{style}",
                4: f"{family} {style}",
                5: f"Version 1.000;{BRAND['year']};{BRAND['version_tag']}",
                6: postscript_name(family, style),
                7: BRAND["trademark"].format(name=family),
                8: BRAND["foundry"],
                9: BRAND["foundry"],
                11: BRAND["store_url"],
                12: BRAND["store_url"],
                13: BRAND["license_line"],
                14: BRAND["store_url"],
                16: family,
                17: style,
                19: f"{family} {style}",
                20: names_table.getDebugName(6) or "",
                21: family,
                22: style,
                25: postscript_prefix(family, style),
            }
            for name_id, expected in expected_names.items():
                records = [r for r in names_table.names if r.nameID == name_id]
                if records and records[0].toUnicode() != expected:
                    name_records_ok = False
                    print(f"Name ID {name_id}: ❌ FAIL (value does not match branded metadata)")
            ps_name = names_table.getDebugName(6) or ""
            if (
                not ps_name
                or len(ps_name) > 63
                or any(not (char.isascii() and (char.isalnum() or char == "-")) for char in ps_name)
            ):
                name_records_ok = False
                print("Name ID 6: ❌ FAIL (invalid PostScript name)")
            refs = referenced_name_ids(font)
            unused_custom_names = sorted({
                r.nameID for r in names_table.names
                if 26 <= r.nameID <= 0xFFFF and r.nameID not in refs
            })
            if unused_custom_names:
                name_records_ok = False
                print(f"Unreferenced custom name IDs: ❌ FAIL ({unused_custom_names})")
            else:
                print("Name metadata: ✅ managed records normalized; no unreferenced custom IDs")
            forbidden_tables = [tag for tag in REMOVED_TABLES if tag in font]
            if forbidden_tables:
                print(f"Removed metadata/signature tables: ❌ FAIL ({', '.join(forbidden_tables)})")
            else:
                print("Removed metadata/signature tables: ✅ DSIG/FFTM/PCLT/meta absent")
            woff_data_ok = True
            if path.suffix.lower() in (".woff", ".woff2"):
                woff_data_ok = woff_optional_blocks_absent(path)
                print(
                    "WOFF metadata/private blocks: "
                    f"{'✅ absent' if woff_data_ok else '❌ FAIL (unexpected or malformed block)'}"
                )
            for tag in ("GSUB", "GPOS"):
                if tag in font:
                    feature_list = font[tag].table.FeatureList
                    records = feature_list.FeatureRecord if feature_list else []
                    feature_tags = sorted({record.FeatureTag for record in records})
                    print(f"{tag} features: {', '.join(feature_tags) if feature_tags else '(empty)'}")
                else:
                    print(f"{tag} features: (table absent)")

            passed = (
                fstype == 0 and all(names.values()) and glyph_count > 0
                and name_records_ok and not forbidden_tables and woff_data_ok
            )
            if "CFF " in font:
                cff = font["CFF "].cff
                top_dict = cff.topDictIndex[0]
                actual_cff_names = (
                    getattr(top_dict, "FamilyName", None),
                    getattr(top_dict, "FullName", None),
                    cff.fontNames[0] if cff.fontNames else None,
                )
                expected_cff_names = (names[1], names[4], names[6])
                cff_ok = actual_cff_names == expected_cff_names
                print(
                    "CFF FamilyName / FullName / FontName: "
                    f"{actual_cff_names} — {'✅ PASS' if cff_ok else '❌ FAIL'}"
                )
                if not cff_ok:
                    print(f"Expected CFF names from name IDs 1 / 4 / 6: {expected_cff_names}")
                cff_identity_ok = (
                    not hasattr(top_dict, "UniqueID")
                    and not hasattr(top_dict, "XUID")
                    and getattr(top_dict, "Weight", None) == font["name"].getDebugName(2)
                    and getattr(top_dict, "Copyright", None) == font["name"].getDebugName(0)
                    and getattr(top_dict, "Notice", None) == font["name"].getDebugName(13)
                )
                print(
                    "CFF identifiers and notices: "
                    f"{'✅ PASS' if cff_identity_ok else '❌ FAIL'}"
                )
                passed = passed and cff_ok and cff_identity_ok
            else:
                print("CFF internal names: n/a (no CFF table)")
            if not all(names.values()):
                print("Name table: ❌ FAIL (missing branded name ID 1, 4, or 6)")
            if glyph_count == 0:
                print("Glyph count: ❌ FAIL (font has no glyphs)")
            return bool(passed)
    except Exception as error:  # noqa: BLE001 - report a failed file, not a traceback
        print(f"❌ FAIL (cannot audit: {error})")
        return False


def audit_dir(directory: Path) -> tuple[int, int]:
    """Audit every font in a directory. Return (audited, failed)."""
    if not directory.is_dir():
        print(f"❌ FAIL (package folder does not exist: {directory})")
        return 0, 1
    files = sorted(p for p in directory.iterdir()
                   if p.is_file() and p.suffix.lower() in FONT_SUFFIXES)
    if not files:
        print(f"❌ FAIL (no font files in {directory})")
        return 0, 1
    passed = sum(1 for path in files if audit_file(path))
    return len(files), len(files) - passed


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("package_dir", type=Path,
                        help="font-named package folder containing prepared binaries")
    args = parser.parse_args()

    audited, failed = audit_dir(args.package_dir)
    print(f"\naudited {audited} file(s); failures: {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
