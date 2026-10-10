# Deterministic Font Visual Prototype (Legacy)

This isolated prototype renders Troska promotional images from the actual
Troska Regular and Troska Stamp font outlines. It does not use AI-generated
backgrounds or modify the production font-preparation workflow.

This is an isolated, hand-authored Troska evaluation prototype. It is not a
production design generator and must not be used as a reusable campaign
template. New Agent-27 work is authored one image at a time in
`visual-direction/openpencil/`, compiled to `.fig`, then passed through
`bin/rasterize_font_visual_handoff.py`, which only renders and validates the
completed OpenPencil sources with the local font files registered.
`bin/generate_font_visual_handoff.py` is a compatibility renderer for older
plans and is not a production path for new fonts.

## Toolchain

- Python 3.14
- `fontTools` for font parsing and SVG glyph outlines
- `uharfbuzz` for kerning and OpenType shaping
- `rsvg-convert` for SVG to PNG rasterization
- ImageMagick and `pngquant` remain available for later delivery compression

The product-font lettering is converted into SVG paths before rasterization.
The auxiliary labels use a fixed local DejaVu Sans font. Texture consists of
seeded vector dots and scratches, so repeated runs produce the same SVG.

## Regenerate

```bash
cd /home/tankiso/Projects/Business-and-Tools/tag-and-description-project
.venv-deterministic-fonts/bin/python bin/deterministic_font_visuals.py \
  --regular "font-factory/fonts/Troska/Troska XBPGX5C/Troska Regular/Troska.otf" \
  --stamp "font-factory/fonts/Troska/Troska XBPGX5C/Troska Stamp/Troska Stamp.otf" \
  --sans /usr/share/fonts/TTF/DejaVuSans.ttf \
  --font-name Troska \
  --output outputs/deterministic-visual-prototype/troska
```

Outputs:

- `3x2/thumbnail_main.png` and `promo_1.png` through `promo_4.png`
- `1x1/thumbnail_main.png` and `promo_1.png` through `promo_4.png`
- matching editable SVG sources under `svg/`

These are evaluation images, not approved `/font-prep` handoff files.
