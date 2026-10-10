# Brush-Factory

Brush-Factory is the staging workspace for original Procreate brush products. It is parallel to `font-factory/`; it does not modify the font workflow.

## One product

Create one folder per brush product using a lowercase hyphenated slug:

```text
brush-factory/
└── brushes/
    └── {brush-slug}/
        ├── source/
        │   ├── {name}.brushset       # preferred delivery source
        │   └── {optional-name}.brush  # individual brushes are also accepted
        ├── description.md            # user-supplied product facts and concept
        ├── prepared_visuals/
        │   ├── thumbnail_main.png    # approved landscape cover, 3:2
        │   ├── promo_1.png            # approved supporting image, 3:2
        │   ├── promo_2.png            # more approved supporting images as needed
        │   └── thumbnail_pinterest.png # optional approved vertical image, 2:3
        └── references/                # optional old images for the image Custom GPT
```

The user creates and approves every creative image in the **FontFairy Procreate Brush Image Director** Custom GPT. The listing agents read these files directly; there is no brush preparation agent.

## Run order

```text
1. Put the .brushset/.brush files and description.md in this folder.
2. Create and approve the 3:2 visuals in the Custom GPT.
3. Save approved visuals under prepared_visuals/.
4. Run /cm-brush brush-factory/brushes/{slug}/.
5. Run /cb-brush brush-factory/brushes/{slug}/.
```

The listing agents use the source files, user facts, and approved visuals directly. They do not rewrite brush archives, package downloads, or invent metadata.

## Image handoff

- `thumbnail_main.png` and `promo_*.png` are approved landscape images. Keep the supplied 3:2 composition intact.
- `thumbnail_pinterest.png` is optional and remains a supplied 2:3 asset.
- `references/` is context for the image GPT only and is never a listing asset.
- If an image is missing, clipped, unreadable, or has the wrong ratio, the listing agent reports the gap instead of repairing it.
