---
description: Build deterministic 2:3 Pinterest PNG variants from a 3:2 product image directory.
---

Run the repository's deterministic Pinterest image composer. The user arguments are already substituted below.

Directory: "$1"
Product name: "$@[2:]"

If either value is missing, ask the user for this format:
`/pinterest-compose "/absolute/path/to/product-images" "Product Name"`

Otherwise run this exact four-variant command from the project root:
```bash
cd /home/tankiso/Projects/Business-and-Tools/tag-and-description-project && python3 bin/compose_pinterest.py "$1" --product "$@[2:]" --variants 4 --count 3 --seed 2026 --output-dir "$1/pinterest"
```

The script chooses the prepared 3:2 thumbnail plus supporting images, decodes each unique source once, and composes the deterministic 2:3 variants with Pillow. Square images are not valid Pinterest sources. The helper writes PNGs and reports the output path, images used, dimensions, and byte size; the final-image processor applies pngquant only when a PNG exceeds 700 KB and does not create JPEG companions unless explicitly requested. Do not edit or overwrite the source images and do not generate replacement artwork.
