---
description: "Build four 2:3 Pinterest PNG variants from a product image directory and compress each below 700 KB."
---

# /pinterest-compose

Run the repository's deterministic four-variant Pinterest image composer for this request: $ARGUMENTS. Parse the supplied product image directory and product name, then run `python3 bin/compose_pinterest.py <source-directory> --product <product-name> --variants 4 --count 3 --seed 2026 --output-dir <output-directory>/visuals/pinterest` from the project root. The script must choose prepared 3:2 images from the untouched source directory, deterministically shuffle the full image pool for each variant, stack them with ImageMagick, write pinterest_1.png through pinterest_4.png under the separate Pinterest output directory, and report each exact output path, inputs, dimensions, and byte size. Apply the repository's bounded pngquant compression step afterward when marketplace-size files are required. Do not edit or overwrite source images and do not generate replacement artwork.
