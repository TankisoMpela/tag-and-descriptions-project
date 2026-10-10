from pathlib import Path
import subprocess
from fontTools.ttLib import TTFont


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / 'font-factory/fonts/vantrelle'
OUTPUT = ROOT / 'font-factory/font-preparation/vantrelle'
PRO = OUTPUT / 'pro'

COPYRIGHT = 'Copyright (c) 2026 PaperMoon. All Rights Reserved.'
VENDOR_URL = 'https://creativemarket.com/TankisoMpela'
DESIGNER_URL = 'https://masterbundles.com/vendor/papermoon/'

STYLES = [
    ('Velmorin.otf', 'Regular'),
    ('Velmorin Italic.otf', 'Italic'),
]


def unique_name_values(font, name_id):
    values = []
    for record in font['name'].names:
        if record.nameID != name_id:
            continue
        try:
            value = record.toUnicode()
        except Exception:
            continue
        if value not in values:
            values.append(value)
    return values


def snapshot(path):
    font = TTFont(str(path), lazy=False)
    os2 = font.get('OS/2')
    cmap = font.getBestCmap() or {}
    basic = all(ord(c) in cmap for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz')
    vendor = getattr(os2, 'achVendID', b'')
    if isinstance(vendor, bytes):
        vendor = vendor.decode('ascii', 'replace')
    return {
        'path': str(path.relative_to(ROOT)),
        'glyphs': len(font.getGlyphOrder()),
        'tables': ', '.join(font.keys()),
        'upm': font['head'].unitsPerEm,
        'units_per_em': font['head'].unitsPerEm,
        'fsType': getattr(os2, 'fsType', 'n/a'),
        'vendor': vendor,
        'weight': getattr(os2, 'usWeightClass', 'n/a'),
        'basic_latin': basic,
        'cmap_entries': len(cmap),
        'gsub': 'present' if 'GSUB' in font else 'absent',
        'gpos': 'present' if 'GPOS' in font else 'absent',
        'family': unique_name_values(font, 1),
        'subfamily': unique_name_values(font, 2),
        'full': unique_name_values(font, 4),
        'postscript': unique_name_values(font, 6),
    }


def write_names(font, subfamily):
    name_table = font['name']
    name_ids = {
        0: COPYRIGHT,
        1: 'VANTRELLE',
        2: subfamily,
        3: f'2026;PaperMoon;VANTRELLE-{subfamily}',
        4: f'VANTRELLE {subfamily}',
        5: 'Version 1.000;2026;paper-moon',
        6: f'VANTRELLE-{subfamily}',
        7: 'VANTRELLE is a trademark of PaperMoon.',
        8: 'PaperMoon',
        9: 'PaperMoon',
        11: VENDOR_URL,
        12: DESIGNER_URL,
        13: 'PaperMoon Commercial Font License. All Rights Reserved.',
        14: VENDOR_URL,
    }
    name_table.names = [
        record for record in name_table.names
        if record.nameID not in name_ids and record.platformID != 1
    ]
    for name_id, value in name_ids.items():
        name_table.setName(value, name_id, 3, 1, 0x409)

    os2 = font['OS/2']
    os2.fsType = 0
    os2.achVendID = b'PMON'
    os2.usWinAscent = max(os2.usWinAscent, 1025)
    os2.usWinDescent = max(os2.usWinDescent, 252)
    os2.sTypoLineGap = 0
    font['hhea'].lineGap = 0
    os2.fsSelection |= 0x0100
    if 'DSIG' in font:
        del font['DSIG']
    cmap = font.getBestCmap() or {}
    space_glyph = cmap.get(0x20)
    if space_glyph:
        for table in font['cmap'].tables:
            if table.isUnicode():
                table.cmap[0x00A0] = space_glyph
    if subfamily == 'Italic':
        font['post'].italicAngle = -10.0
    if 'CFF ' in font:
        cff = font['CFF '].cff
        cff.topDictIndex[0].FontName = f'VANTRELLE-{subfamily}'
        cff.fontNames[0] = f'VANTRELLE-{subfamily}'
    if subfamily == 'Italic':
        os2.fsSelection |= 0x01
        font['head'].macStyle |= 0x02
    else:
        os2.fsSelection &= ~0x01
        font['head'].macStyle &= ~0x02


def convert_to_woff(source, destination, flavor):
    font = TTFont(str(source), lazy=False)
    font.flavor = flavor
    font.save(str(destination))


def run_fontspector(path):
    result = subprocess.run(
        ['fontspector', '--profile', 'universal', str(path)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return result.returncode, result.stdout


def main():
    PRO.mkdir(parents=True, exist_ok=True)
    (OUTPUT / 'freemium').mkdir(parents=True, exist_ok=True)
    source_dir = next(INPUT.glob('Velmorin Bold Elegant Serif S3QSE7D'))
    source_otfs = [source_dir / filename for filename, _ in STYLES]
    before = []
    for source in source_otfs:
        before.append(snapshot(source))
    source_fontspector = [(source, *run_fontspector(source)) for source in source_otfs]

    output_paths = []
    fontspector = []
    for source, (_, subfamily) in zip(source_otfs, STYLES):
        output_base = PRO / f'VANTRELLE-{subfamily}'
        pro_otf = output_base.with_suffix('.otf')
        font = TTFont(str(source), lazy=False)
        write_names(font, subfamily)
        font.save(str(pro_otf))

        pro_ttf = output_base.with_suffix('.ttf')
        forge = subprocess.run(
            ['fontforge', '-lang=ff', '-c', 'Open($1); Generate($2)', str(pro_otf), str(pro_ttf)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        if forge.returncode != 0 or not pro_ttf.exists():
            raise RuntimeError(f'FontForge conversion failed for {source}:\n{forge.stdout}')

        ttf_font = TTFont(str(pro_ttf), lazy=False)
        write_names(ttf_font, subfamily)
        ttf_font.save(str(pro_ttf))
        convert_to_woff(pro_ttf, output_base.with_suffix('.woff'), 'woff')
        convert_to_woff(pro_ttf, output_base.with_suffix('.woff2'), 'woff2')

        for path in [pro_otf, pro_ttf, output_base.with_suffix('.woff'), output_base.with_suffix('.woff2')]:
            output_paths.append(path)
            fontspector.append((path, *run_fontspector(path)))

    after = [snapshot(path) for path in output_paths]
    report = []
    report.append('# VANTRELLE Font Preparation Audit')
    report.append('')
    report.append('## PRE-FLIGHT')
    report.append('')
    report.append('User-supplied final name: **VANTRELLE**')
    report.append('')
    report.append('The staged package contains two source masters: Regular and Italic. No separate Bold or Bold Italic files were present in the folder or ZIP archive, so no synthetic weight was generated.')
    report.append('')
    for item in before:
        report.append(f"### `{item['path']}`")
        report.append('')
        report.append(f"- Family / subfamily: {item['family']} / {item['subfamily']}")
        report.append(f"- Glyphs / cmap entries: {item['glyphs']} / {item['cmap_entries']}")
        report.append(f"- UPM / weight: {item['upm']} / {item['weight']}")
        report.append(f"- fsType / vendor: {item['fsType']} / `{item['vendor']}`")
        report.append(f"- Basic Latin A–Z/a–z: {'present' if item['basic_latin'] else 'missing'}")
        report.append(f"- GSUB / GPOS: {item['gsub']} / {item['gpos']}")
        report.append('')
    report.append('## RAW SOURCE FONTSPECTOR OUTPUT')
    report.append('')
    for path, code, output in source_fontspector:
        report.append(f"### `{path.relative_to(ROOT)}` (exit {code})")
        report.append('')
        report.append('```text')
        report.append(output.rstrip())
        report.append('```')
        report.append('')
    report.append('## METADATA TRANSFORMATION')
    report.append('')
    report.append('- Family: VANTRELLE')
    report.append('- Foundry: PaperMoon')
    report.append('- Copyright: Copyright (c) 2026 PaperMoon. All Rights Reserved.')
    report.append('- Vendor ID: `PMON`')
    report.append('- Pro embedding permission: `fsType=0` (Installable Embedding)')
    report.append('- Formats generated per supplied style: OTF, TTF, WOFF, WOFF2')
    report.append('')
    report.append('## FONT SPECTOR OUTPUT')
    report.append('')
    for path, code, output in fontspector:
        report.append(f"### `{path.relative_to(ROOT)}` (exit {code})")
        report.append('')
        report.append('```text')
        report.append(output.rstrip())
        report.append('```')
        report.append('')
    report.append('## POST-PROCESSING VERIFICATION')
    report.append('')
    for item in after:
        report.append(f"- `{item['path']}` — fsType `{item['fsType']}`, vendor `{item['vendor']}`, family `{item['family']}`, subfamily `{item['subfamily']}`, glyphs `{item['glyphs']}`")
    report.append('')
    report.append('## FREEMIUM STATUS')
    report.append('')
    report.append('Freemium demo generation was skipped because the project is operating in its default Pro-only mode. No freemium files are included in this package.')
    (OUTPUT / 'audit-report.md').write_text('\n'.join(report) + '\n', encoding='utf-8')

    inventory = '''# VANTRELLE Source Inventory\n\n- Supplied masters: `VANTRELLE-Regular`, `VANTRELLE-Italic`\n- Missing from supplied folder/archive: separate Bold and Bold Italic masters\n- Source glyph count: 279 per master\n- Source formats present: OTF, TTF, WOFF\n- Pro formats produced: OTF, TTF, WOFF, WOFF2\n'''
    (OUTPUT / 'source-inventory.md').write_text(inventory, encoding='utf-8')


if __name__ == '__main__':
    main()
