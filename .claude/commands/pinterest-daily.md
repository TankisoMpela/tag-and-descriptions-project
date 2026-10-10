---
description: "Run the daily Pinterest pipeline: pick 10 fonts, write pin copy with tag rotation, assemble the staggered bulk-import CSV."
argument-hint: "optional run date YYYY-MM-DD"
---

# /pinterest-daily

Delegate the task below to the **`daily-pinterest-run`** subagent defined in `.claude/agents/daily-pinterest-run.md`. Use the Claude Code `Agent` tool, run it in the foreground, and wait for its final result before continuing. Do not attempt the specialist's work in the main session.

Task:

```
Please run the daily-pinterest-run agent to produce the bulk-import pins.csv for tomorrow (UTC) unless a date is supplied here. Pick 10 ready fonts with the 14-day exclusion, write per-font title/description/keywords using the ledger's tag rotation, assemble via bin/make_daily_pins.py, and report the CSV path, publish window, and the manual import step. Never upload the CSV or claim publication. Date (optional): $ARGUMENTS
```

After the subagent returns, report the pins.csv path, row count, publish window, and remind the user that uploading the CSV in Pinterest (desktop → Settings → Import content) is the human step.
