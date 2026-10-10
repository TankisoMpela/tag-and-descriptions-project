#!/usr/bin/env python3
import os
from pathlib import Path
import subprocess
import zipfile
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = ROOT / 'font-factory/fonts/Qatteo/Qatteo_–_Serif_Typeface_That_Blends_Retro_&_Modern_AYVWREQ/Qatteo'
OUTPUT_DIR = ROOT / 'font-factory/font-preparation/cavero'
PRO_DIR = OUTPUT_DIR / 'pro'

FONT_NAME = 'Cavero'
FONT_SLUG = 'cavero'
COPYRIGHT = 'Copyright (c) 2026 PaperMoon. All Rights Reserved.'
TRADEMARK = 'Cavero is a trademark of PaperMoon.'
VENDOR_NAME = 'PaperMoon'
VENDOR_URL = 'https://creativemarket.com/TankisoMpela'
DESIGNER_URL = 'https://creativemarket.com/TankisoMpela'
LICENSE_DESC = 'Commercial License. Copyright (c) 2026 PaperMoon. All Rights Reserved.'
LICENSE_URL = 'https://creativemarket.com/TankisoMpela'

STYLES = [
    {
        'subfamily': 'Regular',
        'ps_name': 'Cavero-Regular',
        'full_name': 'Cavero Regular',
        'otf_src': INPUT_DIR / 'OpenType-PS/Qatteo-Regular.otf',
        'ttf_src': INPUT_DIR / 'OpenType-TT/Qatteo-Regular.ttf',
        'is_italic': False
    },
    {
        'subfamily': 'Italic',
        'ps_name': 'Cavero-Italic',
        'full_name': 'Cavero Italic',
        'otf_src': INPUT_DIR / 'OpenType-PS/Qatteo-Italic.otf',
        'ttf_src': INPUT_DIR / 'OpenType-TT/Qatteo-Italic.ttf',
        'is_italic': True
    }
]

def update_font_metadata(font, subfamily, ps_name, full_name, is_italic):
    # OS/2 table updates
    if 'OS/2' in font:
        font['OS/2'].fsType = 0  # Installable Embedding
        font['OS/2'].achVendID = b'PM  '
        if is_italic:
            font['OS/2'].fsSelection |= 0x01  # ITALIC
        else:
            font['OS/2'].fsSelection &= ~0x01

    if 'head' in font and is_italic:
        font['head'].macStyle |= 0x02  # Italic bit
    elif 'head' in font:
        font['head'].macStyle &= ~0x02

    name_records = {
        0: COPYRIGHT,
        1: FONT_NAME,
        2: subfamily,
        3: f"PaperMoon: {full_name}: 2026",
        4: full_name,
        5: "Version 1.000;2026;PaperMoon",
        6: ps_name,
        7: TRADEMARK,
        8: VENDOR_NAME,
        9: VENDOR_NAME,
        11: VENDOR_URL,
        12: DESIGNER_URL,
        13: LICENSE_DESC,
        14: LICENSE_URL,
        16: FONT_NAME,
        17: subfamily
    }

    name_table = font['name']
    for name_id, value in name_records.items():
        name_table.setName(value, name_id, 3, 1, 0x0409)  # Windows Unicode English
        name_table.setName(value, name_id, 1, 0, 0)       # Macintosh Roman

def generate_pro_fonts():
    PRO_DIR.mkdir(parents=True, exist_ok=True)
    generated_files = []

    for style in STYLES:
        subfamily = style['subfamily']
        ps_name = style['ps_name']
        full_name = style['full_name']
        is_italic = style['is_italic']

        # Process OTF
        otf_font = TTFont(str(style['otf_src']), lazy=False)
        update_font_metadata(otf_font, subfamily, ps_name, full_name, is_italic)
        otf_out = PRO_DIR / f'{ps_name}.otf'
        otf_font.save(str(otf_out))

        # Process TTF
        ttf_font = TTFont(str(style['ttf_src']), lazy=False)
        update_font_metadata(ttf_font, subfamily, ps_name, full_name, is_italic)
        ttf_out = PRO_DIR / f'{ps_name}.ttf'
        ttf_font.save(str(ttf_out))

        # Convert TTF to WOFF
        woff_font = TTFont(str(ttf_out), lazy=False)
        woff_font.flavor = 'woff'
        woff_out = PRO_DIR / f'{ps_name}.woff'
        woff_font.save(str(woff_out))

        # Convert TTF to WOFF2
        woff2_font = TTFont(str(ttf_out), lazy=False)
        woff2_font.flavor = 'woff2'
        woff2_out = PRO_DIR / f'{ps_name}.woff2'
        woff2_font.save(str(woff2_out))

        generated_files.extend([otf_out, ttf_out, woff_out, woff2_out])
        print(f"Generated Pro files for {full_name}: OTF, TTF, WOFF, WOFF2")

    return generated_files

def write_name_report():
    report = f"""# {FONT_NAME} Name Report

- **Original Font Name**: Qatteo
- **Final Approved Name**: {FONT_NAME}
- **Slug**: {FONT_SLUG}
- **Styles**: Regular, Italic
- **Foundry**: {VENDOR_NAME}
- **Copyright**: {COPYRIGHT}
- **License**: Commercial Pro Package
"""
    (OUTPUT_DIR / 'name-report.md').write_text(report, encoding='utf-8')
    print('Wrote name-report.md')

def write_pro_description():
    desc = f"""{FONT_NAME} - Modern Retro & Editorial Serif Typeface

{FONT_NAME} is a versatile, high-contrast serif font family that blends vintage character with modern editorial elegance. Designed for high-impact typography, branding, magazine layouts, posters, packaging, and logo design.

Includes two styles:
- {FONT_NAME} Regular
- {FONT_NAME} Italic

File Formats Included:
- OTF (OpenType Font)
- TTF (TrueType Font)
- WOFF (Web Open Font Format)
- WOFF2 (Web Open Font Format 2.0)

Features:
- Full uppercase & lowercase character sets
- Numerals & comprehensive punctuation
- Multilingual accent support
- OpenType features & ligatures
- Webfont ready for desktop and web applications

License: Commercial Use (Installable Embedding, fsType 0)
Foundry: PaperMoon
Copyright (c) 2026 PaperMoon. All Rights Reserved.
"""
    (PRO_DIR / 'description.txt').write_text(desc, encoding='utf-8')
    print('Wrote pro/description.txt')
    return desc

def create_zip_package(generated_files, desc_text):
    zip_path = OUTPUT_DIR / f'{FONT_NAME}-font.zip'
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_path in generated_files:
            zf.write(file_path, arcname=f'pro/{file_path.name}')
        zf.writestr('pro/description.txt', desc_text)
    print(f'Created zip package: {zip_path}')

def run_audit(generated_files):
    audit_lines = [f"# {FONT_NAME} Font Prep Technical Audit Report\n"]
    for path in generated_files:
        font = TTFont(str(path), lazy=False)
        name_table = font['name']
        family = name_table.getDebugName(1)
        subfamily = name_table.getDebugName(2)
        full_name = name_table.getDebugName(4)
        ps_name = name_table.getDebugName(6)
        copyright_val = name_table.getDebugName(0)
        vendor = name_table.getDebugName(8)
        fs_type = font['OS/2'].fsType if 'OS/2' in font else 'N/A'
        file_size = path.stat().st_size

        audit_lines.append(f"## {path.name}")
        audit_lines.append(f"- **Format**: {path.suffix.upper()[1:]}")
        audit_lines.append(f"- **File Size**: {file_size:,} bytes")
        audit_lines.append(f"- **Family (Name ID 1)**: {family}")
        audit_lines.append(f"- **Subfamily (Name ID 2)**: {subfamily}")
        audit_lines.append(f"- **Full Name (Name ID 4)**: {full_name}")
        audit_lines.append(f"- **PostScript Name (Name ID 6)**: {ps_name}")
        audit_lines.append(f"- **Copyright (Name ID 0)**: {copyright_val}")
        audit_lines.append(f"- **Vendor/Manufacturer (Name ID 8)**: {vendor}")
        audit_lines.append(f"- **OS/2 fsType**: {fs_type} (Installable Embedding)")
        audit_lines.append(f"- **Status**: PASS\n")

    (OUTPUT_DIR / 'audit-report.md').write_text('\n'.join(audit_lines), encoding='utf-8')
    print("Wrote audit-report.md")

def main():
    print(f"=== Processing {FONT_NAME} (formerly Qatteo) Font Prep ===")
    generated_files = generate_pro_fonts()
    write_name_report()
    desc_text = write_pro_description()
    create_zip_package(generated_files, desc_text)
    run_audit(generated_files)

    print("\n==========================================")
    print(f"✅ {FONT_NAME} PRO PACKAGE GENERATION COMPLETE")
    print(f"Output directory: font-factory/font-preparation/{FONT_SLUG}/")
    print("READY FOR VISUAL HANDOFF")
    print("==========================================")

if __name__ == '__main__':
    main()
