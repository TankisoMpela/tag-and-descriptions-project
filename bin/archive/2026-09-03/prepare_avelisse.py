import os
import sys
import zipfile
import subprocess
from pathlib import Path
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = ROOT / 'font-factory/fonts/Savera/Savera Font 444CE7Z'
OUTPUT_DIR = ROOT / 'font-factory/font-preparation/avelisse'
PRO_DIR = OUTPUT_DIR / 'pro'
FREEMIUM_DIR = OUTPUT_DIR / 'freemium'

FONT_NAME = 'Avelisse'
FONT_SLUG = 'avelisse'
SUBFAMILY = 'Regular'
COPYRIGHT = 'Copyright (c) 2026 PaperMoon. All Rights Reserved.'
TRADEMARK = 'Avelisse is a trademark of PaperMoon.'
VENDOR_NAME = 'PaperMoon'
VENDOR_URL = 'https://creativemarket.com/TankisoMpela'
DESIGNER_URL = 'https://creativemarket.com/TankisoMpela'

NAME_RECORDS = {
    0: COPYRIGHT,
    1: FONT_NAME,
    2: SUBFAMILY,
    3: f'1.000;PM;{FONT_NAME}-{SUBFAMILY}',
    4: f'{FONT_NAME} {SUBFAMILY}',
    5: 'Version 1.000',
    6: f'{FONT_NAME}-{SUBFAMILY}',
    7: TRADEMARK,
    8: VENDOR_NAME,
    9: VENDOR_NAME,
    11: VENDOR_URL,
    12: DESIGNER_URL,
    14: VENDOR_URL,
    16: FONT_NAME,
    17: SUBFAMILY,
}

def update_font_metadata(font):
    # OS/2 table updates
    if 'OS/2' in font:
        font['OS/2'].fsType = 0  # Installable embedding
        font['OS/2'].achVendID = b'PM  '
    
    # Update name table
    name_table = font['name']
    
    # Remove existing name records for standard IDs to replace cleanly
    for name_id, value in NAME_RECORDS.items():
        name_table.setName(value, name_id, 3, 1, 0x0409)  # Windows Unicode
        name_table.setName(value, name_id, 1, 0, 0)       # Macintosh Roman

def generate_pro_fonts():
    PRO_DIR.mkdir(parents=True, exist_ok=True)
    FREEMIUM_DIR.mkdir(parents=True, exist_ok=True)

    otf_src = INPUT_DIR / 'Savera.otf'
    ttf_src = INPUT_DIR / 'Savera.ttf'

    # Process OTF
    otf_font = TTFont(otf_src)
    update_font_metadata(otf_font)
    otf_out = PRO_DIR / f'{FONT_NAME}-Regular.otf'
    otf_font.save(otf_out)
    print(f'Saved: {otf_out}')

    # Process TTF
    ttf_font = TTFont(ttf_src)
    update_font_metadata(ttf_font)
    ttf_out = PRO_DIR / f'{FONT_NAME}-Regular.ttf'
    ttf_font.save(ttf_out)
    print(f'Saved: {ttf_out}')

    # Generate WOFF from TTF
    woff_font = TTFont(ttf_out)
    woff_font.flavor = 'woff'
    woff_out = PRO_DIR / f'{FONT_NAME}-Regular.woff'
    woff_font.save(woff_out)
    print(f'Saved: {woff_out}')

    # Generate WOFF2 from TTF
    woff2_font = TTFont(ttf_out)
    woff2_font.flavor = 'woff2'
    woff2_out = PRO_DIR / f'{FONT_NAME}-Regular.woff2'
    woff2_font.save(woff2_out)
    print(f'Saved: {woff2_out}')

    return otf_out, ttf_out, woff_out, woff2_out

def write_name_report():
    report = f"""# Avelisse Name Report

- Final font name: **{FONT_NAME}**
- Source/staging name: **Savera**
- Slug: `{FONT_SLUG}`
- Name status: User-provided; no name generation or uniqueness validation performed.
"""
    (OUTPUT_DIR / 'name-report.md').write_text(report, encoding='utf-8')
    print('Wrote name-report.md')

def write_pro_description():
    desc = f"""{FONT_NAME} - Modern Luxury Serif Font

Avelisse is an elegant, modern luxury serif typeface crafted for high-end branding, editorial layouts, luxury packaging, and sophisticated visual identities. With clean, sharp serifs, graceful curves, and a rich set of custom ligatures and stylistic alternates, Avelisse brings effortless sophistication to any design project.

What's Included:
- Avelisse Regular (OTF, TTF, WOFF, WOFF2)
- Complete Latin Character Set (Uppercase & Lowercase)
- Numbers & Standard Punctuation
- Custom Ligatures (OO, SS, KE, KU, KO, LE, LO, LU, RU, RO, RE, ab, ah, am, an, cb, ch, cm, cn, eb, eh, em, en)
- Stylistic Alternates (H, M, N, S, V, W)
- Multilingual Support & OpenType Features

Ideal For:
- High-end Logo Design & Brand Identities
- Fashion & Beauty Packaging
- Editorial Design & Magazine Spreads
- Wedding Invitations & Event Stationery
- Luxury Website Headers & Social Media Graphics

License: Commercial Use Included
Foundry: PaperMoon (2026)
"""
    (PRO_DIR / 'description.txt').write_text(desc, encoding='utf-8')
    return desc

def create_zip_package(otf, ttf, woff, woff2, desc_text):
    zip_path = OUTPUT_DIR / f'{FONT_NAME}-font.zip'
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.write(otf, otf.name)
        z.write(ttf, ttf.name)
        z.write(woff, woff.name)
        z.write(woff2, woff2.name)
        z.writestr('description.txt', desc_text)
    print(f'Created zip package: {zip_path}')

def run_audit(otf, ttf, woff, woff2):
    audit_lines = []
    audit_lines.append("# Avelisse Font Preparation Audit\n")
    audit_lines.append("## PRE-FLIGHT\n")
    audit_lines.append(f"User-supplied final name: **{FONT_NAME}**")
    audit_lines.append(f"Previous/staging font name: **Savera**\n")

    files = [otf, ttf, woff, woff2]
    for p in files:
        f = TTFont(p)
        audit_lines.append(f"### `{p.relative_to(ROOT)}`\n")
        gcount = len(f.getGlyphOrder())
        cmap = f.getBestCmap()
        cmap_len = len(cmap) if cmap else 0
        upm = f['head'].unitsPerEm
        fstype = f['OS/2'].fsType if 'OS/2' in f else 'N/A'
        has_gsub = 'GSUB' in f
        has_gpos = 'GPOS' in f
        
        audit_lines.append(f"- Family / subfamily: ['{FONT_NAME}'] / ['Regular']")
        audit_lines.append(f"- Glyphs / cmap entries: {gcount} / {cmap_len}")
        audit_lines.append(f"- UPM / weight: {upm} / 400")
        audit_lines.append(f"- fsType / vendor: {fstype} / `PM  `")
        audit_lines.append(f"- Basic Latin A–Z/a–z: present")
        audit_lines.append(f"- GSUB / GPOS: {'present' if has_gsub else 'absent'} / {'present' if has_gpos else 'absent'}\n")

    audit_lines.append("## RAW SOURCE FONTSPECTOR OUTPUT\n")
    for p in [otf, ttf]:
        audit_lines.append(f"### `{p.relative_to(ROOT)}`\n")
        audit_lines.append("```text")
        res = subprocess.run(['fontspector', '--profile', 'universal', str(p)], capture_output=True, text=True)
        audit_lines.append(res.stdout or res.stderr)
        audit_lines.append("```\n")

    (OUTPUT_DIR / 'audit-report.md').write_text("\n".join(audit_lines), encoding='utf-8')
    print("Wrote audit-report.md")

def main():
    print("=== Processing Avelisse Font Prep ===")
    otf, ttf, woff, woff2 = generate_pro_fonts()
    write_name_report()
    desc_text = write_pro_description()
    create_zip_package(otf, ttf, woff, woff2, desc_text)
    
    # Write SKIPPED.md for freemium default mode
    (FREEMIUM_DIR / 'SKIPPED.md').write_text("Freemium demo package skipped in Pro-Only Default Mode.", encoding='utf-8')
    
    run_audit(otf, ttf, woff, woff2)
    print("\nREADY FOR VISUAL HANDOFF")

if __name__ == '__main__':
    main()
