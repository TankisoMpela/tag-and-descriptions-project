---
description: "Research the rights status of the staged families in font-factory/input, one web pass per folder, and fan red/amber/green verdicts into each folder's rights-verdicts.json."
argument-hint: "optional folder number/name to scope the run, otherwise the whole unmarked backlog"
---

# /font-rights-check

Delegate the task below to the **`font-rights-researcher`** subagent defined in `.claude/agents/font-rights-researcher.md`. Use the Claude Code `Agent` tool, run it in the foreground, and wait for its final result before continuing. Do not attempt the specialist's work in the main session.

Task:

```
Please run the font-rights-researcher agent on the staged fonts under font-factory/input. Take the queue from python3 bin/font_rights.py status --unmarked — it lists FOLDERS, and the staged folder is the unit of research: one family per folder, one web pass per folder. Run python3 bin/font_rights.py plan --folder <N> for the representative (its Regular/normal cut) and the family/holder/fsType/licence it claims, then do ONE search (serper, with the marketplace sweep collapsed into a single query) — never one web pass per weight or style of the same design. Read its own name-table claim first, then live web evidence per the shared web research fetch policy, and write the verdict with bin/font_rights.py write ... --fanout so it covers the whole folder (fetch a page only when the verdict would be clear — red and amber both mean do not ship): claimed (still sold by an active holder — its evidence URL must sit on a shop, the holder's own domain, or a type-rights reference, never a name-table scraper), orphan (no holder and no licence found — unlicensed, not safe), or clear (a grant quote the tool verifies in each binary, or an author reached this run; it never inherits across holders). Drain every folder in natural order unless a folder is named; keep to the fetch/search budgets and the per-run pass cap; then run python3 bin/font_rights.py sync so the verdicts survive the gitignored staging in the tracked ledger under outputs/research/. Never edit a font, manifest, in-use.txt, or listing — sync is the only thing you may write under outputs/; never delete duplicates. Report counts per state, how many verdicts were inherited rather than researched, every clear with its grant quote or contacted author, every claimed with its evidence URL, and the remaining queue. Make no shipment, licence, or publication claim. Request: $ARGUMENTS
```

After the subagent returns, report the verdict counts per state, the fonts it could not judge, and tell the user to press ↻ Refresh in the Input Inspector to see the chips.
