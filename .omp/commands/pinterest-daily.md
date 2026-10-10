---
description: Run the daily Pinterest pipeline — pick 10 fonts, write pin copy from the font's pin history, assemble the staggered Buffer CSV.
---

Dispatch the registered FontFairy task agent `daily-pinterest-run` for this request (the agent reads its canonical spec in `agents/` and executes it).

If the completion reports a `buffer.csv` path with row count and publish window, report it and remind the user that uploading it in Buffer (Pinterest channel → Bulk Upload) is the human step; `pins.csv` is the Pinterest-native fallback and carries no alt text. Otherwise report the blocker honestly.

User request / input:

Please run the daily-pinterest-run agent to produce the daily `buffer.csv` (plus the `pins.csv` fallback) for tomorrow (UTC) unless a date is supplied here. Pick 10 ready fonts with the 14-day exclusion, read each font's previous pins (`brief.md` ALREADY PINNED / `bin/pinterest_tag_ledger.py history`) before writing a fresh title/description/alt text/keywords, assemble via `bin/make_daily_pins.py`, and report the CSV path, publish window, and manual import step. Never upload the CSV or claim publication. Date (optional): $@
