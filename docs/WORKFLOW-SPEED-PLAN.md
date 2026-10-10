# Workflow Speed & Token Plan

Working plan for making the font workflow faster and cheaper. Every number here
is measured from this repo, not estimated from intuition. Re-measure before
acting on any item — the model below is the baseline the projections are
relative to.

---

## 1. The measurement that decides everything

Per full `/full-workflow` run (agents 27, 13, 28, 20, 22, 29), before the cuts
committed in `01fdde5`:

| | Tokens | Cost (DeepSeek Flash card) |
|---|---|---|
| Input (specs, AGENTS.md, registries, product facts) | 81,650 | $0.0245 |
| Output (generated copy, notes, plans) | 25,646 | $0.0308 |
| **Total** | **107,296** | **$0.055** |

Mechanical work — every renderer, validator and video — totals **≈44 s**.

### The conclusion this forces

**Money is not the problem.** A full run costs about five and a half cents.
The problem is wall clock, and wall clock is almost entirely **serial output
generation**:

| Output rate | Time spent generating |
|---|---|
| 40 tok/s | 10.7 min |
| 60 tok/s | 7.1 min |
| 100 tok/s | 4.3 min |
| 150 tok/s | 2.8 min |

Input is prefill-heavy and largely cacheable (cached input bills at $0.006/M
versus $0.300/M uncached — 50×). Output is generated one token at a time and
cannot be cached at all.

> **The lever is output tokens. Everything else is second-order.**

This is why the earlier AGENTS.md split, while correct and worth keeping, only
moved ~9% of tokens: it cut input, and input was never the bottleneck.

---

## 2. Where the output goes (25,646 tokens)

| Agent | Output | Nature |
|---|---|---|
| agent-27 image generator | 10,900 | creative briefs, theme.txt, plan, image notes |
| agent-29 Creative Fabrica | 4,247 | listing copy + 40 tags |
| agent-22 Pixiv | 3,725 | listing copy |
| agent-20 BOOTH | 3,674 | listing copy + evidence rows |
| agent-13 font prep | 2,500 | description.txt, video configs, audit prose |
| agent-28 orchestrator | 600 | handoff prompts |

The listing agents (~11,650) are producing the actual deliverable — that copy
is the product and cannot be cut without cutting the product.

**agent-27 is the reducible half at 45% of all generated tokens.**

---

## 3. Work items, ranked by expected wall-clock return

### Item 1 — Stop generating artifacts nothing validates (agent-27)

**Measured waste:** `validate_image_record()` is gated on `direct_artwork`, and
the active `render_mode` is `text_placeholder`:

```python
direct_artwork = render_mode in {"direct_artwork","direct","openpencil","open-pencil"}
def validate_image_record(...):
    if not direct_artwork:
        return          # ← always taken in the active mode
```

| Artifact | Generated | Validated by |
|---|---|---|
| `image-notes/*.md` ×10 | ~3,400 tok | **nothing** in the active mode |
| `art-direction.md` | 1,468 tok | `is_file()` only |
| `candidate-review.md` | 302 tok | `is_file()` only |

~5,170 tokens generated for zero substantive checking — and they already drift
(one product's `theme.txt` and design note describe *different copy for the same
promo*).

**Change:** the agent emits the structured plan; the renderer derives the human
views from it, exactly as it already derives `visual-handoff-manifest.md` and
`VISUAL-HANDOFF-READY.md`. One representation, many views.

**Expected:** −5,000 output tokens ≈ **−1.4 min**.

**Blocked on a decision:** whether `theme.txt` + plan is enough for image-model
prompting, or the notes are read when crafting prompts. If they are read, they
stay and we take Item 4 instead.

---

### Item 2 — Move machine-checkable rule prose into the validators

Prose rules cost tokens on **every run even when never violated**. Validator
rules cost nothing until violated, then name the exact fault.

The CF spec's `### Exactly 40 tags` section is **1,191 tokens (4,767 B)** — and
`bin/validate_creative_fabrica_listing.py` already enforces all of it:

```
EXPECTED_TAG_COUNT = 40          FORMAT_TAGS = {otf,ttf,woff,woff2,opentype}
MAX_SINGLE_WORD_TAGS = 0         JUNK_TAGS = {best seller,popular,trendy,cute}
NEAR_DUPLICATE_FAMILIES = (...)  FONT_ROUTE_RE = ...
```

Across all specs there are **469 rule-ish lines (~16% of spec text)**. The
checkable subset should exist once, in code.

**Change:** for each rule already in a validator, replace the prose with one
sentence naming the rule and the validator that enforces it. Keep the rules that
need judgement (the 3-tier tag ordering, "defensible distinct-intent terms",
western-language guidance) — those are the model's actual job.

**Expected:** −1,500 to −3,000 input tokens. Modest for cost; the real gain is
removing prose that can go stale against its validator.

---

### Item 3 — Apply the same to agent-20 (14,376 tokens, the largest spec)

Same analysis as Item 2. Includes one dated artefact worth checking:
`### Authenticated editor observation (2026-08-19)` is 1,118 tokens (4,474 B).

---

### Item 4 — Collapse agent-13's deterministic work into one script ⭐

**The largest architectural item.** agent-13 is **10 numbered steps and 13
command blocks**, and almost all of it is mechanical:

| Step | Nature |
|---|---|
| 0 input ingestion | deterministic |
| 1 font name | user-supplied |
| 2 pre-flight audit | **now a script** (`font_preflight_audit.py`) |
| 2b Fontspector | external tool, deterministic |
| 3a name table, 3b OS/2 flags, 3c formats | deterministic (`font_make_woff.py`) |
| 3d description.txt | **creative — this is the real work** |
| 4c videos | **now a script** (`render_font_showcase.py`) |
| 5 specimens + drop dir | deterministic copy |
| 6b package audit | **now a script** (`font_package_audit.py`) |
| 7 summary | deterministic |

The agent's genuine contribution is `description.txt` and the two video scene
configs. Everything else is a script waiting to be written.

**Change:** `bin/prepare_font_package.py {workspace} {name} {number}` performs
steps 0–3c, 4c, 5 and 6b in one invocation. agent-13 becomes: run the script,
write `description.txt` + the two configs, report.

**Expected:** ~13 command blocks collapse to ~1–2, cutting both output tokens
(~1,000) and — more importantly — **turn count**. Every turn costs a full
round-trip (prefill + generation + tool exec). A 20-turn agent becomes a 4-turn
agent.

**Acceptance:** `prepare_font_package.py` reproduces the existing prepared
package byte-for-byte for a font already in `outputs/font-preparation/`.

---

### Item 5 — Make the spec a stable cached prefix

The wrappers currently instruct: *"Read `agents/agent-13-...md` in full with the
`read` tool."* That spends a whole round-trip before real work starts, and puts
the spec in the conversation body rather than the prefix.

**Change:** generate each wrapper's `systemPrompt` from its canonical spec at
build time, so the spec is present on turn 1 and sits in the stable prefix that
the provider cache keys on. One source of truth, no drift — the wrapper is
generated, not hand-maintained.

**Expected:** −1 round-trip per agent (×6 agents), better cache hit rate on the
largest stable block in every session.

---

## 4. Ideas evaluated and rejected — do not revisit without new evidence

| Idea | Verdict | Evidence |
|---|---|---|
| **Rust / Go rewrite of the scripts** | **No** | All mechanical work is ≈44 s against 7–10 min of model time — under 10% of wall clock. The scripts are Pillow/fontTools/subprocess-bound (ffmpeg, fontforge, pngquant), not CPU-bound, so a native rewrite would not even capture that 44 s. |
| **PyPy** | **No** | Same reason. Also poor fit for Pillow-bound work. |
| **Nuitka** | **No** | Optimises startup and CPU; neither is the bottleneck. |
| **JSON/TOML for agent consumption** | **No, as compression** | Measured on identical content: prose 81 tok, **JSON 93 tok (+15%)**, TOML 71 tok. Syntax does not compress meaning. |
| | **Yes, as an enabler** | Structured files permit *loading a subset* and *machine derivation*. That is the real value — but it only pays where a task needs a subset. A creative agent needs the whole brief, so converting agent-27's guidance to JSON would cost more, not less. |
| **Model routing per agent** | **No gain today** | All agents already inherit the session model (`deepseek-v4-flash`), which *is* the `smol` role. Nothing is running on the expensive role. Still worth setting explicitly, so a future session-default change cannot silently put mechanical agents on a heavy model. |
| **Prompt caching** | **Real but not the lever** | 50× cheaper on input. Input is not what makes a run slow. |
| **Parallelising the marketplace agents** | **Rejected by the user** | The workflow runs one font per run; the orchestrator is explicitly sequential. |

---

## 5. The honest answer on "is there nothing architectural?"

There is exactly one thing that is genuinely architectural, and it is Item 4.

Everything else on this list is expense reduction. Item 4 changes the *shape* of
the workflow: it converts a reasoning agent doing deterministic work into a
script invocation plus a small creative task. That is the same move that has
already worked three times in this repo — `booth_owned_registry.py` (546,901 →
749 tokens), `booth_tag_ledger.py` (63,417 → 411), and the three Agent-13 audit
scripts extracted on 2026-09-21.

The ceiling is set by how much of the workflow genuinely requires judgement.
After Item 4, that is: agent-27's art direction, `description.txt`, and the three
listing agents' copy. Everything else is already, or should become, a script.

**Projection if Items 1, 4 and 5 land together:**

| | Now | Projected |
|---|---|---|
| Output tokens | 25,646 | ~19,000 |
| Turn count (agent 13) | ~20 | ~4 |
| Wall clock at 60 tok/s | ~7–10 min | ~4–6 min |

Ranges, not promises: generation rate is provider-side.

---

## 6. Status

Landed on 2026-09-21 (`67b7be5`, `3fb363e`):

| Item | Result |
|---|---|
| 1 agent-27 derived views | done — renderer derives theme.txt, image-notes, art-direction.md from the plan |
| 2 CF rule prose | done — 31,588 -> 30,455 B, every removed rule paired to its validator constant |
| 3 agent-20 rule prose | done — 57,507 -> 56,968 B, incl. a stale "fewer than 10 tags" floor |
| 4 agent-13 collapse | done — `bin/prepare_font_package.py`; spec 10 steps -> 3, 20,615 -> 14,454 B |
| 5 wrapper from spec | NOT DONE — see below |

Whole-run tokens 106,549 -> 89,563 (-15.9%). **Output tokens 25,646 -> 19,491
(-24.0%)**, which is the number that governs wall clock.

### Item 5 reassessed

Generating each wrapper `systemPrompt` from its canonical spec removes one read
round-trip per agent and guarantees a stable cacheable prefix. It also creates a
build step and a new way for the wrapper to go stale if the generator is not run.
Given the measured result above, the case is weaker than it looked: the read is
one turn out of ~4-20, and the spec is cached from turn 2 onward either way.
Recommend leaving it unless turn count is the binding constraint.

### RESOLVED: the brand is FontFairy

Confirmed 2026-09-21. Everything active now reads FontFairy / FAIR /
`Version 1.000;2026;fontfairy` / `https://fontfairy.booth.pm/`: the Agent 13
brand-constants table, `bin/prepare_font_package.py`, and 40 references across
23 files (agent specs, wrappers, commands, `opencode.json`, the Custom GPT
knowledge bases, the font/brush-factory READMEs and the brush packagers).

Left deliberately unchanged:

- `outputs/**` and `font-factory/font-preparation/**` — these are records of what
  actually shipped. The fonts in them really do carry PaperMoon / PixelBrush /
  Letternity metadata, so rewriting the reports would falsify the record.
- `agents/reference/AGENTS-full-archive.md` — carries a HISTORICAL banner.
- **BOOTH DB internals still say `papermoon`**: the `papermoon_rank` SQLite table,
  the `--papermoon-tags` flag and the `booth-rank-papermoonstudio-*.csv` filename
  in `bin/build_booth_db.py`, `bin/refresh_booth_db.sh`,
  `bin/analyze_booth_collection.py` and the `booth-rank-tracker` extension. These
  are internal identifiers bound to a CSV the user downloads from BOOTH, and the
  shop-slug default (`papermoonstudio`) feeds the rank tracker. Renaming them is
  a schema/CLI change that would break existing DBs and the download convention,
  so it is a separate decision rather than part of this sweep. Note
  `build_booth_db.py` already documents the table as "FontFairy shop items".

One historical oddity worth a look: `outputs/font-preparation/079-semilya-fontera`
shipped with its upstream name table never rewritten at all (Letternity / HL), so
it carries neither brand.

---

## 7. Verification method for every item
## 7. Verification method for every item

1. Re-run the token model script (Section 1) and record before/after.
2. For Item 4, prove byte-equality of the regenerated package against an
   existing one in `outputs/font-preparation/`.
3. Run the real validators (`validate_font_visual_handoff.py`,
   `validate_booth_listing.py`, `validate_creative_fabrica_listing.py`).
4. Commit with the measured delta in the message, not an assertion.
