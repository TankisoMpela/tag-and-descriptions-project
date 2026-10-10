# BOOTH and Creative Market Agent Workflow Stress Test

Date: 2026-08-15

## Scope

This is a dry-run/static workflow audit. It does not upload products, create
Pixiv posts, create freemium files, or rewrite existing marketplace listings.

## BOOTH workflow

### Passed checks

- The paid-only BOOTH scope is explicit in `agents/agent-20-booth-fonts-specialist.md`.
- The OpenCode agent and `booth-font` command are registered in `opencode.json`.
- The Codex-native registration exists at `.codex/agents/booth-fonts-specialist.toml`.
- The workflow reads the prepared Pro package and refuses unsupported claims.
- The workflow uses live BOOTH evidence rather than Creative Market's fixed
  30-tag model.
- The workflow distinguishes selected live tags from unconfirmed keyword
  phrases and requires an evidence row for each selected tag.
- The workflow handles both existing square-preview names found in the
  preparation output: `thumbnail_square.png` and `thumbnail_main_square.png`.
- A representative paid ByteFrame fixture passed
  `bin/validate_booth_listing.py`.
- The workflow records BOOTH's current JPY fee formula and does not pretend
  that public Loves counts are sales or search volume.

### Deliberate non-goals

- No Pixiv post/caption campaign.
- No free demo, freemium, specimen product, or free-to-paid funnel.
- No automatic BOOTH upload or credential handling.

### Remaining runtime gate

The live BOOTH seller editor was not authenticated in this workspace, so the
agent must record the tag cap and exact tag-chip behavior when the user runs it
against the live editor. The public BOOTH pages do not provide a stable tag cap.

## Creative Market workflow

### Existing-output hard-gate results

The new deterministic validator was run against every numbered file in
`outputs/creativemarket/`.

Passing files:

- `10-mirevane-cm.md`
- `10-quiet-acre-cm.md`
- `11-marquetry-cm.md`
- `11-tracery-cm.md`
- `7-dartelle-cm.md`
- `8-avelisse-cm.md`
- `8-vertical-matter-cm.md`
- `9-arcshift-cm.md`
- `9-cavero-cm.md`

Existing files that fail the declared workflow gates:

- `1-vantrelle-cm.md`: missing meta title; title exceeds 36 characters.
- `2-evercourt-cm.md`: missing meta title; title exceeds 36 characters.
- `3-merriloop-cm.md`: missing meta title.
- `4-softberry-cm.md`: missing meta title; title exceeds 36 characters.
- `5-ironrush-cm.md`: missing meta title.
- `6-byteframe-cm.md`: missing meta title.

These are existing output defects, not repaired as part of this agent/workflow
change.

### Numbering collision found

The current repository contains different products sharing the same numeric
prefixes:

- `#8`: Avelisse and Vertical Matter
- `#9`: Arcshift and Cavero
- `#10`: Mirevane and Quiet Acre
- `#11`: Marquetry and Tracery

This is inconsistent with the workspace's unified-number requirement and is a
likely result of parallel listing runs allocating numbers independently. The
BOOTH agent and hardened Creative Market workflow now scan all marketplace
folders and refuse to allocate a number already assigned to another slug. The
historical collisions remain for intentional user resolution.

### Creative Market workflow defects corrected

- Tavily is no longer a hard dependency when the provider is unavailable.
- Suggest-query return counts are no longer described as search volume.
- Product identity and number allocation are checked across all marketplace
  folders before writing.
- A deterministic `bin/validate_cm_listing.py` gate is required before the
  agent reports completion.
- The completion message now labels tag evidence accurately instead of claiming
  every tag was suggest-query validated when some are justified by live CM
  pages or verified product facts.

## Tool/config verification

- `opencode.json` parses successfully.
- Both validator scripts compile successfully.
- OpenCode version detected: `1.18.15`.
- `opencode agent list` could not complete because this environment's OpenCode
  log path `/home/tankisompela/.local/share/opencode/log/opencode.log` is not
  available. Static JSON and registration checks passed; the runtime list
  command should be retried after that user-wide OpenCode log-path issue is
  resolved.
