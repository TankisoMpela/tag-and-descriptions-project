# What the optimization pass actually changed

Measured from git, comparing `e0a3672~1` ("Snapshot before workflow token-reduction
pass") against `HEAD`. 40 commits, 181 files, **+5,714 / −23,180 lines** (net
−17,466).

Every figure below is measured from the repository at both ends, not estimated.
Method is stated so it can be re-run.

---

## 1. The headline

| | Before | After | Change |
|---|---:|---:|---:|
| Input tokens | 113,066 | 70,984 | **−37.2%** |
| **Output tokens** | **25,646** | **17,960** | **−30.0%** |
| **Total tokens per run** | **138,712** | **88,944** | **−35.9%** |
| Cost per run (uncached) | $0.0647 | $0.0428 | **−33.8%** |
| Cost per run (80% cache hit) | $0.0381 | $0.0262 | −31.4% |
| Generation time @ 60 tok/s | 7.1 min | 5.0 min | **−30% (−2.1 min)** |
| Generation time @ 100 tok/s | 4.3 min | 3.0 min | −30% (−1.3 min) |

**Per 10 products:** 497,680 fewer tokens, ~$0.22 less, **~21 minutes less
waiting**.

**Output is the number that matters.** Input is prefill and caches at $0.006/M
against $0.300/M uncached; output is generated serially and cannot be cached.
A 30% output cut is a 30% cut in the part of the run you actually wait for.

---

## 2. What changed, by size of effect

### AGENTS.md — 9,508 → 2,082 tokens (−78%)

The single biggest win, because it is injected into **every** agent by the harness
and could not be routed per agent by instruction. 77% of it was listing-only
content — listing scope, the platform constraint matrix, tag tracking, the fetch
policy, campaign mode — read by the visual, preparation and final-image agents for
nothing. Moved into `agents/reference/AGENTS-annex-listing.md`, read only by the
three listing agents.

Verified mechanically at the time: all 15 original sections byte-identical across
the two files, 0 lost.

### agent-13 — 6,891 → 2,799 tokens (−59%), and 9 steps → 2

Its entire mechanical pass became one command, `bin/prepare_font_package.py`:
pre-flight audit, name table, OS/2 flags, OTF/TTF/WOFF/WOFF2, specimens, drop
directory, reports, both archives, the technical audit, and now an OpenType
Sanitizer pass. The agent's only judgement work is `description.txt`.

This is the change that cuts **turns**, which matters independently of tokens:
every turn is a full round-trip (prefill, generation, tool execution).

### agent-27 output — ~10,900 → 6,045 tokens (−45%)

Validated against real artifacts rather than modelled: `11-qegor`'s
hand-written `theme.txt` + `art-direction.md` + `candidate-review.md` + ten
`image-notes/` files total **10,383 tokens**. Three of those four documents were
restatements of the plan they accompanied, and they had **drifted** — one
product's `theme.txt` and design note described different copy for the same promo.

The renderer now derives all three from `visual-plan.json`, so the agent authors
one artifact instead of four.

### Bulk reads → queries (four tools)

| Instead of reading | Tool | Before | After |
|---|---|---:|---:|
| owned-product registry | `booth_owned_registry.py` | 546,901 | **749** |
| `booth-tag-ledger.md` (180 KB) | `booth_tag_ledger.py --check` | 63,417 | **411** |
| `pixiv-tag-ledger.md` | `pixiv_tag_ledger.py --check` | 3,031 | **28** |
| CF tag bank / owned registry | `creative_fabrica_tag_lookup.py`, `_owned.py` | 16,170 / 84,404 | **291 / 421** |

### agent-22 output — 3,725 → 2,194 tokens (−41%)

The agent was reprinting its own 23-row evidence table as
`## APPENDIX: LEDGER UPDATE`: 6,009 B of a table already in the ledger, left for
a human to copy across. `pixiv_tag_ledger.py --append` now takes the table
straight from the listing.

### Mechanical time — the videos are gone

Both showcase videos rendered in ~29 s. Archived, along with Pinterest
composition, so the mechanical layer is now ≈19 s (renderer 11.5–14.3 s, packager
2.95 s, final images 1.92 s, validators under 1.5 s each). The OTS gate added
~0.3 s back — correctness, not speed.

---

## 3. What did *not* improve

Recorded so the picture is not flattering rather than accurate.

| Item | Before | After | Why |
|---|---:|---:|---|
| agent-29 spec | 6,303 | 7,613 | **+21%** — validator pointers and a gate added |
| agent-22 spec | 4,391 | 5,132 | **+17%** — ledger tool, gate, contradiction fix |
| agent-20 spec | 13,587 | 14,242 | **+5%** — judgement rules kept verbatim, pointers added |
| agent-27 spec | 13,290 | 13,838 | **+4%** — fact-sheet section added |
| agent-20 output | 3,674 | 3,674 | **unchanged** — derivable columns still pending |
| agent-29 output | 4,247 | 4,247 | **unchanged** — same |

**Several specs grew.** Pointers to validators, the fact-sheet section, the
ledger-tool instructions and the new gates all cost input tokens. That was
accepted deliberately: rules stated once plus a validator pointer cost less than
the bulk prose they replaced, and the gate text prevents real defects. But the
specs were not uniformly shrunk, and pretending otherwise would be wrong.

**agent-20 and agent-29 output is untouched.** 63% of BOOTH's evidence table and
25% of CF's is a pure function of the tag, and both are still written by the
model. That is ~1,534 output tokens per run left on the table —
`docs/LISTING-TOKEN-PLAN.md` items 2 and 3.

---

## 4. Defects found and fixed along the way

The optimisation pass is also where most of these surfaced, because measuring
forced reading the code:

| Defect | Consequence if shipped |
|---|---|
| `AGENTS.md` 77% listing-only | read by three agents that never list |
| agent-27 hand-wrote three derived documents | ~5,900 output tokens, and they drifted |
| Pixiv reprinted its evidence table | ~1,531 output tokens for nothing |
| **Pixiv's validator would reject every new listing** | em-dash, parenthetical heading and `platform:` case all failed exact matches |
| **The Pixiv agent never ran its listing validator** | no structural gate at all |
| agent-22 contradicted itself | one-per-line tags required *and* listed as a failure |
| Four wrappers referenced tools their agent never uses | `search.js`, `validate_booth_listing.py` in visual agents |
| `fontforge` wrote OS/2 v5 with a v4-length table | fontTools refused to load the file at all |
| `fontforge` regenerated Name ID 6 | TTF shipped upstream's PostScript name |
| The packager silently dropped the pre-flight audit | I introduced this; caught and restored |
| Duplicate `.otf`/`.ttf` sources overwrote each other | the OTF master could be lost to the TTF, work done twice |
| `SPECIMEN_NAMES` was a `set` | validator failure order changed between runs |
| `white_text` accepted by the renderer, rejected by the validator | new listings would fail |
| Two omp agents had invalid YAML frontmatter | they may not have registered at all |
| **opencode.json was fatally broken** | 24 of 31 entries pointed at archived specs; opencode refused to start |

That last one is worth dwelling on: opencode would not launch at all before this
pass.

---

## 5. Method

```bash
# baseline and current sizes
git show e0a3672~1:AGENTS.md | wc -c
git show e0a3672~1:agents/agent-13-font-prep-specialist.md | wc -c

# output validated against real artifacts, not modelled
du -b font-factory/fonts/11-qegor/visual-direction/{theme.txt,art-direction.md,candidate-review.md}
du -cb font-factory/fonts/11-qegor/visual-direction/image-notes/*.md
```

Token counts are bytes ÷ 4 throughout, applied identically at both ends, which is
what makes the percentages comparable.

**Not measured:** an actual timed before/after agent run. The wall-clock figures
are derived from output tokens at a stated generation rate, because output
generation is serial and dominates. Treat them as a model, not a stopwatch.

---

## 6. Where it stands

| | |
|---|---|
| Total reduction | **−35.9%** |
| Output reduction | **−30.0%** |
| Cost reduction | **−33.8%** |
| Turn reduction (agent 13) | 13 command blocks → 1 |
| Lines removed | net −17,466 |
| Remaining identified opportunity | ~1,534 output tokens (BOOTH + CF derivable columns) |

The mechanical layer is now ~19 s against a ~5-minute run, so it is a rounding
error. **Output tokens are the remaining lever**, and the three listing agents are
still 60% of them.
