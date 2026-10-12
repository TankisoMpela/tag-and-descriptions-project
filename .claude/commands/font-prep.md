---
description: "FontFairy font preparation — package, audit and lay out the font, then render the five pins and the specimen sheets."
argument-hint: "product facts or workspace path"
---

# /font-prep

Delegate the task below to the **`font-prep-specialist`** subagent defined in `.claude/agents/font-prep-specialist.md`. Use the Claude Code `Agent` tool, run it in the foreground, and wait for its final result before continuing. Do not delegate this to OpenCode, omp, or Codex, and do not attempt the specialist's work in the main session.

Task:

```
Please run the font-prep-specialist agent with this exact instruction: $ARGUMENTS. Finish the font metadata, package/archive copies, and technical audit. Treat Agent-27 prepared_visuals as deferred for creative artwork: do not copy, compress, rename, inspect, or compose any thumbnail, supporting promo, or video asset from them. Then run Step 2: write pins.brief.json with five fresh headlines in five colour worlds and render it with bin/render-pins. Add `"class": "blackletter"` to the brief only when the seller's own words say blackletter, celtic, uncial, gaelic or gothic, and `"class": "sports"` only when they say sport, athletic, esports, racing, gym, varsity, letterman or jersey, and `"class": "script"` only when they say handwritten, hand lettering, script, cursive, calligraphy, signature or wedding lettering. Then run Step 2b: render the two factual specimen sheets at both ratios into the numbered output's specimens/ folder with bin/render-specimens --class <the brief's class, or elegant>, which refuses to guess the class. Copy nothing from prepared_visuals. Leave visuals/New-Images/ empty for the seller's own artwork, apart from the pinterest/ pins you rendered.
```

After the subagent returns, report its output paths, validator status, evidence, and any blocked facts. Never claim publication or an upload.