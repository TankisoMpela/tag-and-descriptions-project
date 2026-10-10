---
description: Build a single-page Japanese branded trial-insert PDF from a BOOTH item URL, font directory, trial URL, and New-Images squares thumbnail.
---

Dispatch the registered FontFairy task agent `booth-pdf-maker` for this request (the agent reads its canonical spec in `agents/` and executes it).

If the completion confirms a saved PDF path with success status, report that path, the embedded trial/BOOTH URLs, and the image/font used.
Otherwise report the blocker honestly; do not invent a completion.

User request / input:

Please run the booth-pdf-maker agent to build a one-page portrait trial-insert PDF. Use the BOOTH item URL, the local font directory, and the trial URL supplied here. Take the product image from `{font-dir}/visuals/New-Images/squares/` (prefer `thumbnail_main`, else the first lexicographic image — no vision). Set Japanese customer copy with restrained top branding, a huge specimen in the product font, a single large GET YOUR FONT button linking to the trial URL with the URL also printed in plain text, a short about-trial section, a secondary BOOTH full-version link, and a small shop footer. Do not put a “please like on BOOTH” CTA in the PDF. Write `outputs/booth-pdfs/{slug}-trial-insert.pdf` via `bin/make_booth_trial_pdf.py`. No upload claim: $@
