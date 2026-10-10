# Tag & Description Project — Claude Code Workspace Guide

You are running inside **Claude Code** for the tag-and-description-project: a
multi-marketplace product-copy pipeline (fonts, brushes, presentations,
mockups) with listing, preparation, and visual specialists.

## Read the master guide first

`AGENTS.md` at the project root is the authoritative workspace guide. Read it
before any substantial work: listing-agent scope, the platform constraint
matrix, unified product numbering, tag tracking/rules, web-research fetch
policy, and pricing/seller-entry doctrine all live there. The canonical agent
specs live in `agents/agent-*.md` and are the single source of truth for each
role.

## Three runtimes — do not cross them

- **OpenCode** — registry `opencode.json`, agents/commands defined there.
- **omp** — wrappers in `.omp/agents/`, commands in `.omp/commands/`.
- **Claude Code (this runtime)** — subagents in `.claude/agents/`, commands in
  `.claude/commands/`, skills in `.claude/skills/`.

### Crossover guard (hard rule for Claude Code sessions)

- ALWAYS delegate with the **Agent tool** to Claude Code subagents registered
  in `.claude/agents/`, matching their `name` frontmatter.
- NEVER spawn, invoke, or delegate to the `opencode`, `omp`, `claude`, or
  `codex` CLIs/daemons through Bash or any subprocess.
- NEVER treat `opencode.json` agent entries, `.omp/agents/*.md`, or Codex
  agents as delegation targets.
- When an agent spec mentions OpenCode/omp/Codex runtime names or IDs,
  translate them to the Claude Code subagent with the same purpose in
  `.claude/agents/` (their wrappers document the mapping).
- A stage counts as delegated only when the Claude Code Agent tool call for a
  `.claude/agents/` subagent returned that child's final result. Never report
  completion from a partial file, a started child, or a parallel runtime.

## Agent layout

- `.claude/agents/{name}.md` — one wrapper per specialist/workflow. Each
  wrapper's body tells the subagent to first read `AGENTS.md` and its canonical
  `agents/agent-*.md` spec, then notes the Claude Code tool mapping and the
  crossover guard. The canonical spec is the actual system prompt: follow it
  exactly (execution modes, evidence rules, output paths, validators).
- `.claude/commands/{name}.md` — slash-command mirrors of the OpenCode
  commands (`/booth-font`, `/full-workflow`, `/all-brushes`, ...). They
  delegate to the corresponding subagent.
- `.claude/skills/` — mirrors `.opencode/skills/`. When a spec references
  `.opencode/skills/{name}/SKILL.md`, read `.claude/skills/{name}/SKILL.md`.

## MCP tools (project `.mcp.json`)

The five research servers are available to Claude Code sessions under these
tool names: context7 (`context7_query-docs`), tavily (`tavily_search`), exa
(`exa_search`), serper (`serper_search`), firecrawl (`firecrawl_scrape`,
`firecrawl_search`).

Tool-name translation (never call the other runtimes' spellings):

| OpenCode/omp name | Claude Code name |
| --- | --- |
| `serper_serper_search` | `serper_search` |
| `firecrawl_firecrawl_scrape` / `firecrawl_firecrawl_search` | `firecrawl_scrape` / `firecrawl_search` |
| `exa_exa_search` | `exa_search` |
| `tavily_tavily_search` | `tavily_search` |
| `context7_query_docs` | `context7_query-docs` |
| `agent_browser` | unavailable in Claude Code (record as limitation) |
| `webfetch` | `WebFetch` (Firecrawl-fallback only, one attempt) |

Local tooling runs through Bash: `node bin/search.js ...`,
`python3 bin/*.py` collectors/validators, etc. After writing a listing, the
responsible agent runs its validator (e.g. `python3 bin/validate_booth_listing.py
outputs/booth/{NUM}-{slug}-booth.md`) and reports PASS/FAIL honestly.

## Key workflows (strictly sequential, one stage at a time)

- `/font-images` → `font-image-generator` (Agent 27): bespoke OpenPencil visual
  handoff (creative thumbnail, 4-8 supporting images, four factual specimen
  PNGs, `.fig`/`.jsx` sources). When the user does not supply a final font name,
  Agent 27 decides the best evocative name from the description — name
  uniqueness research and the namemaker agent are forbidden (uniqueness does not
  matter). The handoff is validated with deterministic machine checks only; the
  agent has no vision or OCR tool and never attempts image inspection.
- `/font-prep` → `font-prep-specialist` (Agent 13): metadata/package/audit,
  both videos, unchanged factual-specimen copy; creative marketing images are
  deferred.
- `/all-fonts` → `all-fonts-workflow`: BOOTH (Agent 20) → Marketore (Agent 24)
  → YellowImages (Agent 23), one at a time. Creative Market, MasterBundles,
  Cubebrush, Pixiv, Behance, Pinterest, Etsy, DaFont/FontSpace are explicit
  request only / paused.
- `/full-workflow` → `full-workflow` (Agent 28): Agent 27 → continuous Agent 13
  → BOOTH → Marketore → YellowImages, strictly sequential. Never invokes the
  final-image processor.
- `/font-final-images` → `font-final-visual-processor` (Agent 30): explicit
  post-workflow only, after the seller places final raw images in
  `visuals/New-Images/`.
- Brushes: `/all-brushes` (Agent 18 → 15 → 16 → 17) and `/booth-brush`
  (standalone Agent 25). No font/Etsy/Pinterest stages.
- `/ivoryglass-marketplaces` → BOOTH → Cubebrush → YellowImages → DLsite.
- Standalone specialists: `/cm-font`, `/cm-powerpoint`, `/cm-mockup`,
  `/cm-general`, `/etsy`, `/etsy-font`, `/etsy-powerpoint`,
  `/masterbundles-font`, `/masterbundles-general`, `/cubebrush-font`,
  `/behance-font`, `/pixiv-font`, `/x-font`, `/yellowimages-font`,
  `/creative-fabrica-font`, `/dlsite-font`, `/pinterest-font`, `/freemium-font`,
  `/namemaker`, `/cm-brush`, `/cb-brush`.

All new-font launches default to `CAMPAIGN_MODE: NORMAL_PAID` (paid-only:
Personal Use ¥500, Commercial Use ¥1,500+; no 無料/free-promotion copy). Free
or trial campaigns run only when the seller explicitly reactivates them with
real scope, dates/trigger, and Commercial Use state. Zero-fee default path does
not upload anywhere; agents produce copy/research handoffs and never claim
publication.