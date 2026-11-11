---
name: agent-daily-pinterest-run
description: Daily Pinterest pipeline. Picks up to 10 registered fonts within Buffer's account limit, uses each preparer's saved board assignment, writes fresh per-pin title/description/alt/keywords from the font's profile and pin history, and assembles buffer.csv plus the Pinterest-native pins.csv fallback. Manual import stays a human step.
user-invocable: true
---

# Daily-Pinterest-Run

You produce one day's Pinterest pin batch from the font registry — a
`buffer.csv` for Buffer's free bulk uploader (carries alt text; primary
destination) plus a `pins.csv` Pinterest-native fallback. All
mechanics live in `bin/` tools — run them from the project root; never
reimplement selection, validation, staggering or CSV writing yourself.

## Preconditions

1. `python3 bin/pinterest_registry.py list --ready --json` — you need at least
   one ready font. If none are ready, stop and tell the user to run
   `/pinterest-prepare` first. Report how many are eligible.
2. Run date `D` = tomorrow (UTC) unless the user names a date. The CSV
   schedules future publish times, so a past/today date will fail validation —
   that is expected, not a bug to route around.
3. The user confirmed the Buffer Free account has verified email. Use `N=10`
   by default. If the user later reports that verification is absent, use
   `N=5` until it is restored.

## Step 1 — pick and brief

```bash
python3 bin/make_daily_pins.py pick --date D --count N
python3 bin/make_daily_pins.py brief --date D
```

`pick` excludes any font pinned in the previous 14 days and writes
`outputs/pinterest/D/selection.json`. `brief` writes `brief.md` with per-font
name, the preparer's saved board assignment, one date-stable image choice with its manifest index
and layout type, both product-page URLs, description excerpt, the preparer's
metadata-and-visual profile and keyword bank, historical Pinterest keywords,
and confirmed prior pins. The tool balances image
indexes across selected fonts, then uses that same choice in both CSVs. When
both product pages exist, destinations split as evenly as possible.

## Step 2 — write pin copy (your only creative work)

For each selected font write a title, description, alt text, and final
keywords. Follow the assigned image shown in `brief.md`; keep copy consistent
with its visible text and composition. Vary intent across the batch
(aesthetic/specimen, crafter/Cricut, project/use-case) so the copy does not
read as one template. Do not read the retired Agent 10 listing workflow.

First look at what this font has already been pinned with. `brief.md` prints
an `ALREADY PINNED` block per font with its past dates, titles, keywords and
most recent alt text; for anything older than that block use
`python3 bin/pinterest_tag_ledger.py history --slug <slug> --full` (add
`--json` for machine-readable). A new pin that reuses one of your own strings
cannibalizes the old one, so write a different title shape, a different hook,
and different keywords — not a synonym swap of the same sentence. A font with
no history block is on its first pin; say so rather than inventing a past.

### Keywords (decide per font)

1. Start from the brief's reviewed profile and "Candidate keywords" line.
   The profile contains up to 60 phrases grounded in the font metadata and
   inspected artwork; use the phrases that fit this exact Pin's assigned
   image and buyer intent. Add a missing style/use-case phrase only when the
   metadata or image supports it. Select about 12 strong candidates for the
   rotation command, spanning multiple relevant angles rather than synonyms.
   If the brief marks the profile MISSING, use only its description fallback,
   do not claim a visual review, and report the font for preparer refresh.
2. Rotate: `python3 bin/pinterest_tag_ledger.py avoid --slug <slug> --candidates "<c1, c2, …>" --take 6`
   → prefer never-used for this font, then least-used across the full Pinterest
   history. Prefer *fresh, accurate phrasing* over synonym churn ("wedding
   script font" → "script font for wedding invitations") — exact-string
   repetition is what cannibalizes your own pins. Across today's batch, avoid
   reusing the same exact keyword phrase for different fonts unless it is a
   useful shared category; each font should keep several clearly specific
   terms.
3. Final mix of 6: 2 style terms + 2 use-case terms + 1 qualifier/audience
   term + 1 further supported style/use-case term. A seasonal phrase may take
   one of these slots only when it fits the font and its lead window below.

The candidate pool and rotation are Pinterest-specific. Do not import BOOTH
tags or its tag ledger: BOOTH's evidence-validated Japanese marketplace tags
are a separate system. The Pinterest ledger stores each font's confirmed Pin
keywords and tracks global phrase use only as a tie-breaker, so keep the
current batch differentiated using the profile and your cross-font review.

### Title (writing heuristic)

- Target **45–65 chars** (tool enforces 1–100). **Title Case.** Unique in
  the batch (tool enforces).
- Put the primary keyword phrase early, ideally within the **first 30–35 chars**.
- Vary the template across the batch:
  1. `{Primary Keyword} — {Font Name} | {Use Case}`
  2. `{Use Case} Font: {Style} {Font Name}`
  3. Question/curiosity form, max 2 per batch.
- Never the word "click", no bait, and don't restate the description's
  opening — the title adds its own info.

### Description (≤500 chars tool limit; aim 150–300)

- Sentence 1: primary keyword + use-case hook, keyword within the first
  ~75 chars.
- Sentences 2–3: style/vibe, 3–5 keywords woven into natural sentences,
  features from the brief only (formats, commercial license — never invent).
- Close with a soft CTA, never "click": "Perfect for invitations, logos, and
  packaging." / "Download {Font Name} for your next project."

### Alt text (required for the Buffer file; accessibility description)

- One concise sentence describing the assigned image: its visible wording,
  layout, and font treatment. Inspect the brief's local source image first;
  if it is unavailable, inspect the matching public Media URL. Do not infer a
  final-image composite's contents from its filename or generic layout label.
- 80–200 chars target (tool enforces 1–500). Pinterest exposes alt text to
  screen-reader users, so do not stuff keywords or make unsupported claims
  ([Pinterest alt-text guidance](https://help.pinterest.com/en/business/article/add-alternative-text-to-your-pins)). Do not copy the description wholesale.

### Placement notes

- Board: copy the exact board assigned by the preparer and shown in `brief.md`.
  The preparer classifies the font once from its metadata and visual review;
  the daily agent must not reclassify it based on today's selected image or copy.
  If any selected font has no valid board, stop the run and send it back to
  `/pinterest-prepare` for classification. Do not invent or substitute a board.
- Pinterest-native `Keywords` are comma-separated phrases. Buffer has no
  Pinterest Keywords column; its `Tags` column is Buffer-internal labels and
  remains empty in this workflow.
- Link: leave it out — the tool derives it from the registry and appends
  unique utm params per row.

### Seasonal keyword calendar (lead: publish 45–60 days ahead, 60–90 for Christmas)

| Quarter | Themes | Example phrases |
|---|---|---|
| Q1 | Valentine's (Dec–Feb lead), winter | romantic script font, valentine font, winter handwriting font |
| Q2 | Easter (Feb–Mar), Mother's Day (Mar), wedding season (Apr–Jun) | easter font, floral script font, wedding invitation font |
| Q3 | Summer crafts, Halloween (Jul–Aug lead) | summer display font, halloween font, spooky gothic font |
| Q4 | Christmas (Sep–Oct lead), New Year | christmas script font, festive display font, new year font |

Write `outputs/pinterest/D/copy.json` — a JSON list, one object per selected
font, in the selection order:

```json
[{"slug": "…", "title": "…", "description": "…", "alt": "…", "keywords": ["…"], "board": "<exact board from brief>"}]
```

## Step 3 — assemble

```bash
python3 bin/make_daily_pins.py assemble --date D
```

Default stagger: 09:00 UTC start, one pin per hour (N pins over N hours).
The tool validates everything (lengths, alt text, uniqueness, boards, keyword
format, future-dated slots within 14 days), writes `buffer.csv` (Buffer
import — exact column order of Buffer's own Pinterest template: Text /
Image URL / Board Name / Tags / Posting Time / Title / Alt Text / Link —
the primary file), `pins.csv` (Pinterest-native fallback, no alt column),
and `tag-report.md`. It saves wording to `prepared_pins` only; it does not
update tag counts, pin history, or the 14-day exclusion. On validation failure,
fix `copy.json` and re-run — never edit a CSV by hand.

## Step 4 — report and stop

Report: `outputs/pinterest/D/buffer.csv` path (primary), number of rows,
publish window (first/last UTC times), boards used, and the manual import
step:

1. One-time setup: create a Buffer free account (or use an existing one) →
   connect the Pinterest business account as a channel → open that channel's
   settings (⚙️) and set its timezone to a UTC city with no DST (search
   "Reykjavik") so the CSV's UTC times publish exactly as written. The user
   has already created the seven Pinterest boards. Keep each CSV `Board Name`
   identical to the preparer's assignment and the Pinterest board title; use
   [`agents/reference/pinterest-board-setup.md`](reference/pinterest-board-setup.md)
   for the canonical titles and descriptions. If a board is missing or renamed,
   stop before import and have the user restore the exact title.
2. Each run: publish.buffer.com → select the Pinterest channel → settings
   cog → General → Bulk Upload → upload `buffer.csv` → review the preview →
   **Add Posts to Queue**. Inspect the image preview on every row first; if any
   thumbnail is missing or broken, stop without queueing and rerun the preparer's
   upload check. Check remaining queue capacity first; the free plan
   allows up to 10 posts per channel per upload, limited by open queue slots.
   Buffer's Pinterest help currently states a daily posting limit of 25 for
   email-verified accounts and 5 for accounts without verified email. This
   account is verified, so use 10; if verification is later absent, make a
   5-pin batch with `--count 5` ([Buffer Pinterest guide](https://support.buffer.com/articles/using-pinterest-with-buffer-PB6dp33lMG)).
3. Fallback: `pins.csv` works via Pinterest Business on desktop → Settings →
   Import content, but carries no alt-text column. Pinterest creates missing
   boards from this native CSV.
4. After the destination confirms which rows it accepted, record only those
   rows. This records import acceptance, not publication:

   ```bash
   python3 bin/pinterest_tag_ledger.py mark-imported --date D --slugs slug-a slug-b
   ```

End with "Import is pending — human step." You never upload the CSV, never
touch Pinterest or Buffer, and make no publication claim.

## Hard rules

- One CSV set per date folder. Re-running `assemble` updates unimported drafts;
  it refuses to overwrite a date with confirmed imports.
- Alt text is required on each Buffer row (1–500 chars) and must accurately
  describe its assigned image for accessibility.
- Only rows confirmed accepted by Buffer/Pinterest enter pin history or the
  14-day exclusion. Read that confirmed history before writing new copy.
- No hashtags anywhere in Pinterest Keywords — plain comma-separated search
  terms. Buffer's template has no Pinterest Keywords column; its `Tags` column
  is for Buffer-internal labels, so the current CSV emits it empty. Pinterest
  Keywords live in pins.csv only.
- Titles: Title Case, 45–65 char target, primary keyword in the first 35
  chars, unique in batch. Descriptions: primary keyword in the first sentence
  (~75 chars). Never "click" in title or description; soft CTAs only.
- Aim for 6 keywords per pin using the mix rule; 3–10 accepted by the tool.
- Facts come from the brief only. If a font's description excerpt contradicts
  its name/category, flag it instead of writing copy for it.
- Blob tokens and `.env` contents must never appear in any output.
