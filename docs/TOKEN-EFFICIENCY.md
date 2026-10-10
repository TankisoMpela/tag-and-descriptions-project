# Token efficiency and workflow speed — development rules

**Token spend and wall clock are first-order requirements in this project, not
nice-to-haves.** Every change that adds cost must be justified by a measurement.

This file is the detail behind the short rule in `AGENTS.md`. It is read when
developing, not on every run.

---

## 1. The measurements that decide every trade-off

Per full `/full-workflow` run:

| | Tokens | Notes |
|---|---:|---|
| Input | 69,304 | prefill, caches at **$0.006/M** vs $0.300/M uncached |
| **Output** | **19,491** | generated **serially**, cannot be cached |
| Total | 88,795 | ≈**$0.044** per run |
| Mechanical work | — | **≈19 s**, under 10% of a run |

Three consequences:

1. **Money is not the constraint.** A run costs about four cents.
2. **Wall clock is output tokens.** 19,491 output tokens is ≈5.4 minutes of
   serial generation at 60 tok/s. That is the run.
3. **The mechanical layer is a rounding error.** Optimising it is almost always
   the wrong investment. Two examples were measured and rejected in
   `docs/PASTE5-FINDINGS.md`.

## 2. The rules

### Rule 1 — Output tokens are the budget

A run is dominated by what the model *writes*. Before adding any required output
artifact, answer: **what consumes this?** If the answer is "a human might glance
at it", derive it in code instead, or drop it.

Precedent: agent 27 was hand-writing `theme.txt`, `image-notes/` and
`art-direction.md` alongside the plan they restated — ~5,900 output tokens per
product. They had also drifted apart. The renderer now derives all three.

Precedent: the Pixiv agent reprinted its own 23-row evidence table as
`## APPENDIX: LEDGER UPDATE`, ~1,400 tokens per package, duplicating a table
already in the ledger.

### Rule 2 — Author once, derive the rest

One structured source of truth. Every human-facing document is generated from
it. A model must never transcribe something a script can compute.

Precedent: agent 27 authors `visual-plan.json`; the renderer derives the three
documents. `booth_evidence_table.py` computes the two URL columns and the
language from the tag — 63% of that table is a pure function of the tag.

### Rule 3 — Query, do not read

Bulk data gets a tool that answers a question. Never instruct an agent to read a
large file.

| Instead of reading | Use | Saving |
|---|---|---|
| `booth_owned_registry` | `booth_owned_registry.py` | 546,901 → **749** tokens |
| `booth-tag-ledger.md` (180 KB) | `booth_tag_ledger.py --check` | 63,417 → **411** |
| `pixiv-tag-ledger.md` | `pixiv_tag_ledger.py --check` | 3,031 → **28** |
| CF research banks | `creative_fabrica_tag_lookup.py` | 16,170 → **291** |
| CF owned registry | `creative_fabrica_owned.py` | 84,404 → **421** |

### Rule 4 — Rules belong in validators, not prose

A rule in a validator costs nothing until violated, then names the exact fault. A
rule in a spec costs tokens **on every run, even when never violated**.

State the contract once, then point at the validator that enforces it.

Precedent: the CF spec's `### Exactly 40 tags` section was 1,191 tokens
restating constants (`EXPECTED_TAG_COUNT`, `FORMAT_TAGS`, `JUNK_TAGS`,
`MAX_SINGLE_WORD_TAGS`) the validator already enforces. Reduced to pointer
sentences.

Precedent: the BOOTH spec carried a stale "fewer than 10 tags → BLOCKED" floor
that contradicted the validator's `MIN_BOOTH_TAGS = 18`.

### Rule 5 — One command, not many turns

Every turn is a full round-trip: prefill, generation, tool execution. A sequence
of shell steps costs far more wall clock than one script invocation.

Precedent: agent 13 was 9 numbered steps and 13 command blocks. Its mechanical
pass is now one command (`bin/prepare_font_package.py`) and the agent went from
~20 turns to ~4.

### Rule 6 — Measure before optimising the mechanical layer

The mechanical layer is ~19 s. Optimising it cannot move a ~6-minute run
meaningfully, and past attempts confirm it:

- **resvg** as a rasteriser: measured **2× slower** than `rsvg-convert` here,
  because the workload is complex glyph paths and tiny-skia is slower than cairo
  at filling them.
- **libvips** for image processing: **315 ms vs Pillow's 294 ms**.
- **In-process librsvg**: 1.9×, but only ~1.1% of a run, for a new dependency.

The one mechanical change that *did* pay was correctness, not speed: adding the
OpenType Sanitizer, which catches a defect class that shipped.

## 3. When to break the rules

Compression must never cost correctness or the deliverable.

- **Do not cut the listing prose.** It is 4–6% of a listing, and it is the
  product the seller uploads.
- **Do not cut rules that need judgement.** agent 27's 13,838-token spec is
  creative direction — the thing preventing generic output. Only the subset that
  restates a validator is fair game.
- **Do not shrink specs purely for input cost.** Input caches at 50× less and
  does not drive wall clock. Keep the prefix stable instead.
- **Always keep the artifact that is the deliverable**, however many tokens it
  costs.

## 4. How to verify a claim

1. Measure the baseline first: `docs/FULL-WORKFLOW-REFERENCE.md` §5 has the
   per-agent token model and §3 the timings.
2. For any output change, prove **byte- or behaviour-equality** on real data
   before switching over. Examples: the JPEG binary search was verified
   byte-identical across 7 images at 3 caps; the validator cleanup was verified
   by diffing failure sets over all 13 handoffs; the renderer derivation was
   verified in a sandbox with md5 comparison of the real directory.
3. Record the before/after in the commit message. An unmeasured "optimisation"
   is not accepted, and neither is an unmeasured regression claim.

## 5. Known-remaining costs

Not everything is reducible. These are understood and accepted:

| Item | Cost | Why it stays |
|---|---:|---|
| agent-20 spec | 14,242 tok in | research procedure and tag judgement |
| agent-27 spec | 13,838 tok in | creative direction; only ~2 lines duplicate a machine check |
| listing prose | ~4–6% of each listing | it is the deliverable |
| agent-20/29 evidence tables | 1,157 + 377 tok out | the observed columns must stay; only derivable columns move to code |

See `docs/LISTING-TOKEN-PLAN.md` for the remaining derivable-column work.
