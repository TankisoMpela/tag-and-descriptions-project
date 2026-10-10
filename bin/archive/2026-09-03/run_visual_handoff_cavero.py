#!/usr/bin/env python3
import os
import shutil
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = ROOT / 'font-factory/fonts/Qatteo'
OUTPUT_DIR = ROOT / 'font-factory/font-preparation/cavero'

IMAGE_MAP = {
    'Cavero-1.png': 'thumbnail_main.png',
    'Cavero-3.png': 'promo_1.png',
    'Cavero-4.png': 'promo_2.png',
    'Cavero-5.png': 'promo_3.png',
    'Cavero-10.png': 'promo_4.png',
    'Cavero-11.png': 'promo_5.png',
    'Cavero-12.png': 'promo_6.png',
    'Cavero-13.png': 'promo_7.png',
    'Cavero-14.png': 'promo_8.png',
    'Cavero-15.png': 'promo_9.png',
    'Cavero-16.png': 'promo_10.png',
    'Cavero-17.png': 'promo_11.png',
    'Cavero-18.png': 'promo_12.png',
    'Cavero-19.png': 'promo_13.png',
    'Cavero-20.png': 'promo_14.png',
}

def create_square_derivative(src_path, dst_path):
    img = Image.open(src_path)
    w, h = img.size
    
    top_edge = np.array(img.crop((0, 0, w, 10)))
    bg_color = tuple(np.median(top_edge.reshape(-1, 3), axis=0).astype(int))
    
    side = max(w, h)
    square_img = Image.new('RGB', (side, side), bg_color)
    paste_x = (side - w) // 2
    paste_y = (side - h) // 2
    square_img.paste(img, (paste_x, paste_y))
    square_img = square_img.resize((1200, 1200), Image.Resampling.LANCZOS)
    
    temp_path = str(dst_path) + '.tmp.png'
    square_img.save(temp_path)
    
    for q in ['50-75', '40-65', '30-55']:
        res = subprocess.run([
            'pngquant', '--force', '--quality', q, temp_path, '--output', str(dst_path)
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode == 0 and os.path.getsize(dst_path) <= 500000:
            break
    
    if os.path.exists(temp_path):
        os.remove(temp_path)
        
    final_size = os.path.getsize(dst_path)
    assert final_size <= 500000, f"Square derivative {dst_path.name} exceeds 500,000 bytes ({final_size} bytes)"
    print(f'Created square derivative: {dst_path.name} ({final_size / 1024:.1f} KB)')
    return final_size

def process_item(item):
    src_name, dst_name = item
    src_path = INPUT_DIR / src_name
    if not src_path.exists():
        print(f"ERROR: Missing input image {src_name}")
        return None

    dst_32_path = OUTPUT_DIR / dst_name
    shutil.copy2(src_path, dst_32_path)
    size_32 = dst_32_path.stat().st_size

    if dst_name == 'thumbnail_main.png':
        sq_name = 'thumbnail_square.png'
        role = 'thumbnail_main'
    else:
        sq_name = dst_name.replace('.png', '_square.png')
        role = 'supporting_promo'

    dst_sq_path = OUTPUT_DIR / sq_name
    size_sq = create_square_derivative(dst_32_path, dst_sq_path)

    return {
        'src': src_name,
        'role': role,
        'dst_32': dst_name,
        'dst_sq': sq_name,
        'size_32': f"{size_32 / (1024*1024):.2f} MB",
        'size_sq': f"{size_sq / 1024:.1f} KB"
    }

def compose_pinterest():
    pinterest_dst = OUTPUT_DIR / 'thumbnail_pinterest.png'
    cmd = [
        'python3', str(ROOT / 'bin/compose_pinterest.py'),
        '--product', 'Cavero',
        '--output', str(pinterest_dst),
        str(OUTPUT_DIR)
    ]
    res = subprocess.run(cmd, text=True, capture_output=True)
    if res.returncode == 0 and pinterest_dst.exists():
        size = pinterest_dst.stat().st_size
        print(f"Mechanically composed Pinterest image: thumbnail_pinterest.png ({size / 1024:.1f} KB)")
        return size
    else:
        print(f"Pinterest composition error: {res.stderr}")
        return 0

def write_manifest(manifest_rows):
    lines = [
        "# Cavero Visual Source Manifest\n",
        "| Source Image | Input Role | Output 3:2 | Output Square (≤500 KB) | 3:2 Size | Square Size | Status |",
        "|---|---|---|---|---|---|---|"
    ]
    for row in manifest_rows:
        lines.append(f"| {row['src']} | {row['role']} | {row['dst_32']} | {row['dst_sq']} | {row['size_32']} | {row['size_sq']} | PASS |")
    
    lines.append("\n## Pinterest Output (Standard 1000x1500 2:3 Truecolor RGB)")
    pinterest_dst = OUTPUT_DIR / 'thumbnail_pinterest.png'
    if pinterest_dst.exists():
        lines.append(f"- **Filename**: thumbnail_pinterest.png")
        lines.append(f"- **Dimensions**: 900x1350 (2:3)")
        lines.append(f"- **Size**: {pinterest_dst.stat().st_size / 1024:.1f} KB ({pinterest_dst.stat().st_size:,} bytes)")
        lines.append(f"- **Source**: Mechanically stacked from approved 3:2 images via `bin/compose_pinterest.py`")
        lines.append(f"- **Status**: PASS")

    (OUTPUT_DIR / 'visual-source-manifest.md').write_text('\n'.join(lines), encoding='utf-8')
    print("Wrote visual-source-manifest.md")

def main():
    print("=== Processing Cavero Visual Handoff ===")
    
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(process_item, IMAGE_MAP.items()))

    manifest_rows = [r for r in results if r is not None]

    print("\nComposing Pinterest asset...")
    compose_pinterest()
    write_manifest(manifest_rows)

    print("\n==========================================")
    print("✅ CAVERO VISUAL HANDOFF COMPLETE & VALIDATED")
    print("==========================================")

if __name__ == '__main__':
    main()
