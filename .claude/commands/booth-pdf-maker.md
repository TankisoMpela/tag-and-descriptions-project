---
description: "Build a single-page Japanese branded trial-insert PDF from a BOOTH item URL, font directory, trial URL, and New-Images squares thumbnail."
argument-hint: "product facts or workspace path"
---

# /booth-pdf-maker

Delegate the task below to the **`booth-pdf-maker`** subagent defined in `.claude/agents/booth-pdf-maker.md`. Use the Claude Code `Agent` tool, run it in the foreground, and wait for its final result before continuing. Do not delegate this to OpenCode, omp, or Codex, and do not attempt the specialist's work in the main session.

Task:

```
Please run the booth-pdf-maker agent to build a one-page portrait trial-insert PDF. Use the BOOTH item URL, the local font directory, and the trial URL supplied here: $ARGUMENTS. Take the product image from {font-dir}/visuals/New-Images/squares/ (prefer thumbnail_main, else the first lexicographic image — no vision). Set Japanese customer copy with restrained top branding, a huge specimen in the product font, a single large GET YOUR FONT button linking to the trial URL with the URL also printed in plain text, a short about-trial section, a secondary BOOTH full-version link, and a small shop footer. Do not put a please-like-on-BOOTH CTA in the PDF. Write outputs/booth-pdfs/{slug}-trial-insert.pdf via bin/make_booth_trial_pdf.py. No upload claim.
```

After the subagent returns, report its output paths, validator status, evidence, and any blocked facts. Never claim publication or an upload.