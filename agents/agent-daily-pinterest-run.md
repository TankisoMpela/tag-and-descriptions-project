---
name: agent-daily-pinterest-run
description: Daily Pinterest pipeline. Randomly picks 10 registered fonts, writes fresh per-pin title/description/alt/keywords with tag rotation from the anti-cannibalization ledger, and assembles the staggered bulk-import buffer.csv (Buffer free import — carries alt text) plus pins.csv fallback. Manual import stays a human step.
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

## Step 1 — pick and brief

```bash
python3 bin/make_daily_pins.py pick --date D --count 10
python3 bin/make_daily_pins.py brief --date D
```

`pick` excludes any font pinned in the previous 14 days and writes
`outputs/pinterest/D/selection.json`. `brief` writes `brief.md` with per-font
name, board suggestion, ALL FOUR blob image URLs, both product-page URLs,
description excerpt, a mechanical candidate-keyword seed (extracted from
description.txt), the font's most-used tags to rotate away from, and its
previous pins. You do not choose the image or the destination link — `assemble`
takes one of the four images per pin (seeded by date, so a re-run gives the
same CSV) and splits fonts that have both market pages evenly between Creative
Market and Creative Fabrica.

## Step 2 — write pin copy (your only creative work)

For each selected font write a title, description, alt text, and final
keywords. The archive spec `archive/specs/agent-10-pinterest-fonts-specialist.md` §"PINTEREST
FONT SEO STRATEGY" and the 3-PIN intent framework are your writing reference —
read the two strategy sections only, not the whole file. Across the day's
fonts, vary intent (aesthetic/specimen, crafter/Cricut, project/use-case) so
the batch does not read as one template.

First look at what this font has already been pinned with. `brief.md` prints
an `ALREADY PINNED` block per font with its past dates, titles, keywords and
most recent alt text; for anything older than that block use
`python3 bin/pinterest_tag_ledger.py history --slug <slug> --full` (add
`--json` for machine-readable). A new pin that reuses one of your own strings
cannibalizes the old one, so write a different title shape, a different hook,
and different keywords — not a synonym swap of the same sentence. A font with
no history block is on its first pin; say so rather than inventing a past.

### Keywords (decide per font)

1. Start from the brief's "Candidate keywords" line — a mechanical seed from
   the description. Extend with style/use-case words the seed missed; target
   8–14 candidates total.
2. Rotate: `python3 bin/pinterest_tag_ledger.py avoid --slug <slug> --candidates "<c1, c2, …>" --take 6`
   → prefer never-used, then least-used. Prefer *fresh phrasings* of the same
   intent over repeating last run's strings ("wedding script font" →
   "script font for wedding invitations") — exact-string repetition is what
   cannibalizes your own pins.
3. Final mix of 6: 2 style terms + 2 use-case terms + 1 qualifier/audience
   term + 1 seasonal/experimental slot (from the calendar below, when in its
   lead window).

### Title (research: 1M-pin study 2025)

- Target **45–65 chars** (tool enforces 1–100). **Title Case.** Unique in
  the batch (tool enforces).
- Primary keyword phrase inside the **first 30–35 chars** (feed truncates).
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

### Alt text (required — buffer.csv carries it; the biggest documented click lever)

- One sentence describing what the image shows: font name + style + specimen
  ("Elegant serif font specimen spelling 'Marren' in luxury logo style").
- 80–200 chars target (tool enforces 1–500). The primary keyword may appear
  naturally; never copy the description wholesale; never invent features not
  in the brief.

### Placement notes

- Board: use the brief's suggestion unless another of the four clearly fits.
  Board title/description are ranking signals — don't park everything on one.
- The CSV Keywords column mirrors the 3–6 final phrases, comma-separated.
  Pinterest indexes title + description + board + alt text; treat the
  Keywords column (pins.csv only) as supporting, not the ranking lever.
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
[{"slug": "…", "title": "…", "description": "…", "alt": "…", "keywords": ["…"], "board": "…"}]
```

## Step 3 — assemble

```bash
python3 bin/make_daily_pins.py assemble --date D
```

Default stagger: 09:00 UTC start, one pin per hour (10 pins over 10 hours).
The tool validates everything (lengths, alt text, uniqueness, boards, keyword
format, future-dated slots within 14 days), writes `buffer.csv` (Buffer
import — exact column order of Buffer's own Pinterest template: Text /
Image URL / Board Name / Tags / Posting Time / Title / Alt Text / Link —
the primary file), `pins.csv` (Pinterest-native fallback, no alt column),
and `tag-report.md`, and records the day's tags and pin dates in the ledger.
On validation failure, fix `copy.json` and re-run — never edit a CSV by hand.

## Step 4 — report and stop

Report: `outputs/pinterest/D/buffer.csv` path (primary), number of rows,
publish window (first/last UTC times), boards used, and the manual import
step:

1. One-time setup: create a Buffer free account (or use an existing one) →
   connect the Pinterest business account as a channel → open that channel's
   settings (⚙️) and set its timezone to a UTC city with no DST (search
   "Reykjavik") so the CSV's UTC times publish exactly as written.
2. Each run: publish.buffer.com → select the Pinterest channel → settings
   cog → General → Bulk Upload → upload `buffer.csv` → review the preview →
   **Add Posts to Queue**. Only do this after the previous batch's last pin
   has published — the free plan holds 10 waiting posts and silently drops
   any rows beyond the free slots.
3. Fallback: `pins.csv` still works via Pinterest Business on desktop →
   Settings → Import content, but carries no alt text.

Recommend testing the first small batch and never exceeding ~10 pins/day on a
young account.

End with "Import is pending — human step." You never upload the CSV, never
touch Pinterest or Buffer, and make no publication claim.

## Hard rules

- One CSV set per date folder; re-running `assemble` regenerates both files
  idempotently.
- Alt text is required on every pin (1–500 chars) — buffer.csv carries it and
  it is our biggest documented click lever.
- Every pin's text is recorded in the ledger when `assemble` runs. Read that
  history before writing new copy and never re-ship a title, alt sentence or
  keyword string this font has already used.
- No hashtags anywhere in Keywords — plain comma-separated search terms.
  Buffer's template has no Pinterest Keywords column; its `Tags` column is
  Buffer-internal labels (emit it empty, never fill it). Keywords live in
  pins.csv only.
- Titles: Title Case, 45–65 char target, primary keyword in the first 35
  chars, unique in batch. Descriptions: primary keyword in the first sentence
  (~75 chars). Never "click" in title or description; soft CTAs only.
- Aim for 6 keywords per pin using the mix rule; 3–10 accepted by the tool.
- Facts come from the brief only. If a font's description excerpt contradicts
  its name/category, flag it instead of writing copy for it.
- Blob tokens and `.env` contents must never appear in any output.
