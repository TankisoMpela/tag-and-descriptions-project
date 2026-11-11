---
name: full-workflow
description: Run the project's sequential five-stage font launch workflow through preparation, BOOTH, Creative Market, and Creative Fabrica.
---

Use this skill when the user asks to run the full font launch. Read and follow
`agents/agent-28-full-workflow.md`, the single runtime-neutral source of truth
for source selection, product numbering, exact stage order, handoffs,
validation, and paused workflows. In OpenCode, delegate through its native
registered-agent mechanism, one child at a time, in foreground/wait mode.
Use the registered children `font-image-generator`, `font-prep-specialist`,
`booth-fonts-specialist`, `cm-fonts-specialist`, and
`creative-fabrica-fonts-specialist` in that order. Stop on the first failed or
incomplete stage. Do not claim upload or publication.

Preserve an exact source folder or staged workspace supplied by the user. If
none is supplied, Agent 27 begins with
`python3 bin/stage_saved_font.py --random`, stages that one Saved family, then
reads its metadata and reviews the full mapped-glyph atlas before recording the
factual description and observed vibe in the visual plan. Do not ask the user
to choose a Saved folder in this mode.
