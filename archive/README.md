# Archive — tag-and-description-project

Everything here was moved out of the active setup on 2026-09-21 as part of the
omp consolidation. Nothing was deleted; restore with `git mv`.

## Active setup (what remains)

- `.omp/agents/` — **7** registered agents: `full-workflow`, `font-image-generator`,
  `font-prep-specialist`, `booth-fonts-specialist`, `pixiv-fonts-specialist`,
  `creative-fabrica-fonts-specialist`, `font-final-visual-processor` (standalone
  post-workflow, `/font-final-images`).
- `.omp/commands/` — matching 7 slash commands (`/full-workflow`, `/font-images`,
  `/font-prep`, `/booth-font`, `/pixiv-font`, `/creative-fabrica-font`,
  `/font-final-images`).
- `agents/` — their canonical specs + `research-checkpoint-protocol.md`.
- `AGENTS.md` — slimmed to the active font pipeline (21.5 KB, was 38 KB). The full
  original is preserved at `agents/reference/AGENTS-full-archive.md`.

## What was archived

| Path | Contents | Restore |
|---|---|---|
| `archive/omp-agents/` | 27 non-active omp wrappers (cm-*, etsy-*, cubebrush-*, yellowimages-*, dlsite-*, masterbundles-*, behance-*, pinterest-*, x-*, marketore-*, namemaker-*, the-converter, brush agents, all-fonts/all-brushes orchestrators) | `git mv archive/omp-agents/<name>.md .omp/agents/` |
| `archive/omp-agents-legacy/` | 32 legacy `agent-NN-*.md` files that embedded the whole spec as a system prompt (up to 95 KB each) | `git mv archive/omp-agents-legacy/* .omp/agents/` |
| `archive/commands/` | 28 commands for the archived agents | `git mv archive/commands/<name>.md .omp/commands/` |
| `archive/specs/` | archived canonical specs, stress-test/audit docs, `CLAUDE.md` | `git mv archive/specs/<name> agents/` |
| `archive/kilo/` | former `.kilo/` harness (agents, commands, skills) | `git mv archive/kilo .kilo` |
| `archive/claude/` | former `.claude/` harness (agents, commands, skills, settings) | `git mv archive/claude .claude` |

## Restore everything

```bash
git mv archive/kilo .kilo && git mv archive/claude .claude
git mv archive/claude/../specs/CLAUDE.md CLAUDE.md
git mv archive/omp-agents-legacy/* .omp/agents/
git mv archive/omp-agents/* .omp/agents/
git mv archive/commands/* .omp/commands/
git mv archive/specs/* agents/
```

Archived files are inert: omp discovers agents only from `.omp/agents`, so nothing
under `archive/` loads or costs context tokens.

## Stale Creative Fabrica research (archived 2026-09-21)

Ten experimental tag-crawl outputs were moved to `archive/research/`. None were
referenced by `agent-29`, `AGENTS.md`, or any current `bin/` script — only by the
legacy `.mjs` crawler toolchain, which recreates its directories on demand.

Kept in place (actually cited by the CF spec):

- `outputs/research/creative-fabrica-tag-metadata/` — the frozen 2026-09-11 vocabulary archive.
- `outputs/research/creative-fabrica-font-candidates/` — the 80-route candidate shortlist.

Current Creative Fabrica research lives directly in `outputs/research/`:

| File | Role |
|---|---|
| `creative-fabrica-tag-bank.json` | measured tag-page coverage |
| `creative-fabrica-tag-corpus.jsonl` | append-only tag-graph observations (411 lines) |
| `creative-fabrica-description-corpus.jsonl` | append-only seller descriptions (324 fonts) |
| `creative-fabrica-tag-patterns.md` | the learned idiom guide the agent reads |
| `creative-fabrica-tag-strategy.md` | per-category recipes and pools |
