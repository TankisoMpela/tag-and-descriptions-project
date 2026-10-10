---
description: Run the daily Pinterest pipeline — pick 10 fonts, write pin copy with tag rotation, assemble the staggered bulk-import CSV.
---

Dispatch the registered FontFairy task agent `daily-pinterest-run` for this request (the agent reads its canonical spec in `agents/` and executes it).

If the completion reports a `pins.csv` path with row count and publish window, report it and remind the user that uploading the CSV in Pinterest (desktop → Settings → Import content) is the human step. Otherwise report the blocker honestly.

User request / input:

Please run the daily-pinterest-run agent to produce the bulk-import `pins.csv` for tomorrow (UTC) unless a date is supplied here. Pick 10 ready fonts with the 14-day exclusion, write per-font title/description/keywords using the ledger's tag rotation, assemble via `bin/make_daily_pins.py`, and report the CSV path, publish window, and manual import step. Never upload the CSV or claim publication. Date (optional): $@
