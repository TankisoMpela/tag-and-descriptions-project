---
name: booth-ready-font-specialist
description: Processes an already named font folder, prepares its font package and BOOTH-ready image deliveries, then writes only the paid BOOTH listing markdown.
user-invocable: true
---

# Ready-Font BOOTH Specialist

Use this specialist for a font whose final name, artwork, and product facts
already exist. This is a separate shortcut from the naming/image-generator
launch path: do not rename the font, generate artwork, run Pixiv, Creative
Fabrica, YellowImages, X, DLsite, or create any other marketplace listing.
The final deliverables are the numbered `outputs/font-preparation/` folder and
one `outputs/booth/{NUM}-{slug}-booth.md` file.

## Required input

The caller must provide:

- the exact font directory containing the already-final font files and images;
- the final font name, exactly as it must appear in the listing and package;
- the product description/facts supplied by the seller;
- the unified product number, or permission to determine the next number by
  scanning only existing listing filenames under `outputs/`.

Do not infer unsupported weights, glyph coverage, licensing, or use cases.
Preserve the supplied name and facts.

## Sequential execution

1. Determine the unified number and output folder
   `outputs/font-preparation/{number}-{slug}/`.
2. Process every supported source image under the supplied font directory with
   `bin/prepare_booth_font_images.py`. Preserve raw files under
   `visuals/source/`, write original-ratio JPEGs under `visuals/main/`, and
   write square JPEGs under `visuals/squares/`. Every generated JPEG must be
   `<= 200000` bytes. The helper uses ImageMagick and centers white padding on
   the shorter axis; a landscape 3:2 image therefore receives equal
   top/bottom padding, while a portrait receives equal side padding. Do not
   overwrite the seller's raw images.
3. Run the registered `font-prep-specialist` sequentially for the same font
   name, description, number, and output directory. It remains authoritative
   for metadata, font QA, complete font binaries, Commercial Use and Personal
   Use archive copies, the like-request note, descriptions, videos, and audit
   reports. Its Commercial/Personal archive files are preparation outputs; the
   BOOTH listing itself is one complete-font offer and must not split them.
4. Run the registered `booth-fonts-specialist` sequentially using the completed
   preparation output, the supplied description, the processed image path, and
   the permanent paid state. Require exactly one BOOTH variant:
   `{FONT NAME} | 完全版 | Full Font`. Require 10–18 best validated tags;
  do not pad toward 18 or exceed 18. Run sibling overlap/saturation
  checks as advisory only (WARN, never a veto): use `--booth-dir` to
  compare tag sets with prior `outputs/booth/*.md`, and if overlap is
  high or saturation is low, suggest different tag choices to the agent.
  Never block launch on sibling results.
5. Confirm that the only marketplace listing created by this specialist is the
   BOOTH markdown file. Do not claim upload or publication.

## Image contract

The image helper is mechanical delivery work, not creative review. It must
inspect dimensions, pad square outputs with pure white, and encode every
delivery at or below 200 KB. If an image cannot meet the limit without an
unacceptable reduction, stop and report the exact filename; do not silently
discard it. The manifest must record source name, dimensions, output sizes,
and padding treatment.

## Completion response

Return:

- the exact preparation output directory;
- the exact processed-image manifest path;
- the exact BOOTH listing markdown path;
- the number of validated BOOTH tags (target 15, within the 10-18 range);
- a statement that sibling-advisory checks were run as WARN-only and no
  upload/publication was claimed.

Stop on any failed child, missing output, failed image-size gate, or missing
product fact. Never fabricate evidence.
