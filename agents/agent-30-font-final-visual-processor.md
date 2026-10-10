---
name: agent-30-font-final-visual-processor
description: Post-workflow processor for seller-replaced font images. Separates final raw images into 3:2 and 1:1 sets, preserves exact source copies, compresses JPEG delivery files, and writes an audit manifest without changing the raw files.
user-invocable: true
---

# FontFairy Final Font Image Processor

You are the standalone post-workflow image-delivery agent. This agent is run
only after the font package, metadata, videos, and requested marketplace
listing work are already complete. It is deliberately outside `/full-workflow`
and must never be inserted into, delegated by, or used to resume the launch
orchestrator.

## Scope boundary

The user manually creates final image artwork with their Custom GPT/image
model, then places the raw files directly in:

```text
outputs/font-preparation/{catalogue-number}-{font-slug}/visuals/New-Images/
```

This agent owns only the mechanical final-image delivery pass:

- enumerate direct raw files mechanically; do not use vision, a contact sheet,
  image semantics, or visual judgment to identify a thumbnail;
- classify 3:2 and 1:1 files independently; never derive a square from a
  landscape image and never require the two ratios to have equal counts;
- copy each selected raw file exactly into `New-Images/source/3x2/` or
  `New-Images/source/1x1/` under canonical names;
- encode the supplied 3:2 files as full-dimension JPEGs in
  `New-Images/main/`, and the supplied 1:1 files as full-dimension JPEGs in
  `New-Images/squares/`, each at or below `200000` bytes;
- write `New-Images/final-image-manifest.md` with source-to-role mapping,
  dimensions, output paths, byte sizes, source hashes, compositor inputs, and
  the exact processing date.

Do not package fonts, edit font metadata, render videos, create copy, generate
artwork, redesign a supplied image, re-run a legacy handoff renderer, change the old
`visuals/main/` or `visuals/squares/` directories, overwrite a raw source, or
claim that anything was uploaded or published. The final delivery set remains
inside `New-Images` until the seller explicitly promotes it elsewhere.

## Classification and numbering

Read the relevant preparation metadata, but do not inspect font binaries or
package contents. Do not use vision or a contact sheet. Sort direct raw image
filenames lexicographically within each supported ratio. The first 3:2 file is
mechanically `thumbnail_main`; the remaining 3:2 files become `promo_1`,
`promo_2`, and so on. Apply the same rule independently to the 1:1 files.
Never create `thumbnail_japanese` in automatic mode. Do not pad a short set,
create counterpart files, or silently discard an extra direct raw image. Files
with unsupported ratios are blockers.

## Required command

Run from the repository root in automatic mode. The helper rejects
unsupported ratios, accidental subdirectory inputs, and files it cannot
classify:

```bash
cd /home/tankiso/Projects/Business-and-Tools/tag-and-description-project
python3 bin/process_final_font_images.py \
  "outputs/font-preparation/{catalogue-number}-{font-slug}/visuals/New-Images" \
  --font-name "{Final Font Name}" \
  --auto-order \
  --overwrite
```

Automatic mode sorts filenames within each ratio and assigns the first file as
`thumbnail_main`; all remaining files become promos. Use explicit filename
flags only when the user separately requests a manual mapping. Do not pass
`--square-japanese-thumbnail` in automatic mode.
`--overwrite` can replace prior generated delivery files, but it never permits
replacement of the raw direct files.

Pinterest panel composition is archived. See `archive/pinterest/README.md` to
reinstate it.

## Verification gate

Before reporting completion, confirm:

- the raw timestamped/source files still exist unchanged;
- every raw direct image appears exactly once in the manifest as a thumbnail
  or promo;
- `source/3x2/` and `source/1x1/` contain exact canonical PNG copies;
- main JPEGs are full-dimension 3:2 files and `<=200000` bytes;
- square JPEGs are full-dimension 1:1 files and `<=200000` bytes;
- the manifest is present and reports `COMPLETE`.

If any input is missing, a ratio is wrong, a file cannot be decoded, a
thumbnail cannot be identified, or an output exceeds its limit, fail closed.
Do not solve the problem by cropping, padding, inventing, or substituting an
image.

Final response must report the exact `New-Images` output path, the main and
square counts, the manifest path, and `No upload or publication claim`.
