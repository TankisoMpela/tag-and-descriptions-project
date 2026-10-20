---
description: "Package and audit the font, install Agent 27's verified Pinterest templates, and render factual specimens."
argument-hint: "font workspace, final name, and product number"
---

# /font-prep

Delegate to the `font-prep-specialist` subagent in the foreground and wait for
its final result. Follow `agents/agent-13-font-prep-specialist.md` and
`AGENTS.md` as the canonical instructions.

Pass the exact font workspace, final name, unified product number, and the
Agent-27 `prepared_visuals/` path. Agent 13 packages and audits the font, writes
the product description, installs the 23 checksummed Pinterest template pins
with `bin/install_template_pinterest_pins.py`, and renders four factual
specimen sheets. It does not inspect or copy Agent 27's thumbnail or support
layout drafts, and it does not render a second Pinterest set.

Leave final thumbnail artwork for the matching image-generation prompt and the
standalone `/font-final-images` stage. Report the preparation output path,
validation result, the 23 pins, four specimen sheets, and any blocker. Do not
claim upload or publication.

User request / input: $ARGUMENTS
