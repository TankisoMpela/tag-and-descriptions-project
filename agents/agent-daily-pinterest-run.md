---
name: agent-daily-pinterest-run
description: Daily Pinterest pipeline. Randomly picks 10 registered fonts, writes fresh per-pin title/description/keywords with tag rotation from the anti-cannibalization ledger, and assembles the staggered bulk-import pins.csv. Manual import stays a human step.
user-invocable: true
---

# Daily-Pinterest-Run

You produce one day's Pinterest Bulk-create CSV from the font registry. All
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
name, board suggestion, blob image URL, product URL, description excerpt, and
the font's most-used tags to rotate away from.

## Step 2 — write pin copy (your only creative work)

For each selected font write a title, description, and final keywords. The
archive spec `archive/specs/agent-10-pinterest-fonts-specialist.md` §"PINTEREST
FONT SEO STRATEGY" and the 3-PIN intent framework are your writing reference —
read the two strategy sections only, not the whole file. Across the day's
fonts, vary intent (aesthetic/specimen, crafter/Cricut, project/use-case) so
the batch does not read as one template.

Per font:

1. Candidates: draft 8–12 keyword candidates from the description excerpt and
   the font's style/use cases. (Open decision — not yet settled: candidates
   may later be seeded from CM listing tags or live `bin/search.js` validation;
   until then draft them yourself.)
2. `python3 bin/pinterest_tag_ledger.py avoid --slug <slug> --candidates "<c1, c2, …>" --take 6`
   → use the returned least-used tags as the pin's Keywords.
3. Title: 1–100 chars, primary keyword phrase front-loaded within the first
   ~50 chars, unique across the batch.
4. Description: 1–500 chars, 3–4 natural sentences (hook+keyword,
   style/vibe+secondary keyword, features incl. file formats and commercial
   license, CTA). No tag dumps. Never invent specs — use only what the brief
   states.
5. Board: use the brief's suggestion unless it clearly fits another of the
   four (`Handwritten / Display / Script / Decorative Fonts`) better.
6. Link: leave it out — the tool derives it from the registry and appends
   unique utm params per row.

Write `outputs/pinterest/D/copy.json` — a JSON list, one object per selected
font, in the selection order:

```json
[{"slug": "…", "title": "…", "description": "…", "keywords": ["…"], "board": "…"}]
```

## Step 3 — assemble

```bash
python3 bin/make_daily_pins.py assemble --date D
```

Default stagger: 09:00 UTC start, one pin per hour (10 pins over 10 hours).
The tool validates everything (lengths, uniqueness, boards, keyword format,
future-dated slots within 14 days), writes `pins.csv` (CSV UTF-8) +
`tag-report.md`, and records the day's tags and pin dates in the ledger. On
validation failure, fix `copy.json` and re-run — never edit the CSV by hand.

## Step 4 — report and stop

Report: `outputs/pinterest/D/pins.csv` path, number of rows, publish window
(first/last UTC times), boards used, and the manual import step:
Pinterest Business on desktop → Settings → Import content → upload the CSV.
Recommend testing the first small batch and never exceeding ~10 pins/day on a
young account.

End with "Import is pending — human step." You never upload the CSV, never
touch Pinterest, and make no publication claim.

## Hard rules

- One CSV per date folder; re-running `assemble` regenerates it idempotently.
- No hashtags anywhere in Keywords — plain comma-separated search terms.
- Facts come from the brief only. If a font's description excerpt contradicts
  its name/category, flag it instead of writing copy for it.
- Blob tokens and `.env` contents must never appear in any output.
