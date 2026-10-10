---
description: Build a 2:3 Pinterest PNG from a product image directory and compress it below 700 KB.
---

Run the repository's deterministic Pinterest image composer. The user arguments are already substituted below.

Directory: "$1"
Product name: "$@[2:]"

If either value is missing, ask the user for this format:
`/pinterest-compose "/absolute/path/to/product-images" "Product Name"`

Otherwise run this exact command from the project root:
```bash
cd /home/tankisompela/Projects/Business-and-Tools/tag-and-description-project && python3 bin/compose_pinterest.py "$1" --product "$@[2:]"
```

The script chooses the prepared 3:2 thumbnail plus supporting images when available, otherwise uses the square derivatives. It stacks the images into a 2:3 Pinterest composition with ImageMagick, compresses with pngquant, writes the PNG beside the input images, and reports the output path, images used, dimensions, and byte size. Do not edit or overwrite the source images and do not generate replacement artwork.
