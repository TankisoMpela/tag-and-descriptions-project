# paste-5 advice — tested

Every recommendation in paste-5 was tested against this repository on this
machine. **No workflow change was made.** Results below; three of the
recommendations do not survive measurement, one is genuinely worth adopting, and
one larger claim is validated but deliberately not acted on.

Measured 2026-09-22. Baseline figures from `docs/FULL-WORKFLOW-REFERENCE.md`.

**Applied:** the OTS release gate (§5) and the binary-search JPEG change (§4).
**Rejected on measurement:** resvg (§2) and libvips (§3).
**Flagged, not applied:** the retired model id (§6), which would change output.

---

## Verdicts

| # | Advice | Verdict | Evidence |
|---|---|---|---|
| 1 | Replace the 23 `rsvg-convert` spawns | **Already tested and rejected earlier** — re-confirmed | in-process librsvg 1.9×; see §1 |
| 2 | Switch to `resvg` | **REJECTED — it is 2× slower here** | §2 |
| 3 | In-process librsvg via PyGObject | 1.9×, but ~1.1% of a run | §1 |
| 4 | Parallelise agents 20/22/29 | **Excluded by the user** | — |
| 5 | Replace agent 28 with deterministic code | Plausible, not tested (needs a workflow change) | §7 |
| 6 | Eliminate most of agent 13 | Already largely done | §7 |
| 7 | Keep fontTools | **Agreed** | fact sheet 0.31 s |
| 8 | Keep uharfbuzz | **Agreed** | fact sheet 0.31 s |
| 9 | libvips for large images | **REJECTED — slower than Pillow here** | §3 |
| 10 | Binary-search the JPEG quality rung | **Works, same result, 28% faster on that step** | §4 |
| 11 | Add OTS as a release gate | **ADOPT — it catches a defect that shipped** | §5 |
| 12 | Add FontBakery | Available (1.1.0), not needed for correctness we lack | §6 |
| 13 | Python 3.14.x | **Already on 3.14.7** | §6 |
| 14 | Verify the DeepSeek model path | **VALIDATED — the configured id is retired** | §6 |
| 15 | Structured output over prose | Already done for agent 27 | §7 |
| 16 | Keep the query-tool architecture | **Agreed** | §7 |
| 17 | Context deduplication | Partly done via AGENTS.md split | §7 |
| 18 | Compile the 53 KB spec into packets | Partly done; the rest is judgement | §7 |

---

## 1. The process-spawn problem is real, but small

Confirmed: `cProfile` attributes **8.7 s of the renderer's 14.5 s to
`subprocess._communicate`** across 23 `rsvg-convert` launches. In-process librsvg
via PyGObject measures **1.9×** (11.09 s → 5.87 s) and removes 23 temp files.

But the whole mechanical layer is **≈19 s against a ~5.4-minute output-generation
cost**. The 5.2 s saving is **≈1.1% of a run**, for a new dependency. That was
declined before and the measurement has not changed the arithmetic.

---

## 2. `resvg` — tested, and it is slower here

paste-5's caveat was that resvg's text stack differs, so it must be checked on
typography-heavy output. That turned out to be a non-issue, and the performance
claim turned out to be backwards.

**The font caveat is moot.** The real SVGs contain **zero `<text>` elements**:
260 `<path>` elements, no `tspan`, no `font-family`, no `font-size`. Every glyph
is already baked to outlines by `font_outline_renderer.py` (fontTools +
uharfbuzz). Neither renderer touches a font stack, so there is no shaping or
font-loading behaviour to differ.

**Installation claim: verified.** `resvg-py` 0.5.0 ships
`cp310-abi3-manylinux_2_17_x86_64` — a prebuilt wheel, 1.4 MB, no Rust toolchain.
(Homebrew does not apply; this machine is Linux x86_64.)

**Output equivalence: verified.**

| | |
|---|---|
| Mean absolute pixel difference | **0.094 / 255** (worst image 0.132) |
| Pixels differing by >32 | **≤0.012%** — antialiasing edges only |
| PNG size | resvg **~35% smaller** (e.g. 151,400 → 98,371 B) |

**Performance: resvg is 2× slower.**

| Workload | rsvg-convert | resvg_py |
|---|---|---|
| 19 real SVGs (best of 3) | **4.50 s** | 9.22 s |
| …per SVG | 237 ms | 485 ms |

Isolating the cause:

| Workload | rsvg-convert | resvg_py |
|---|---|---|
| 1 `<rect>`, 1600×1600 | 135 ms | **128 ms** |
| 1 real placeholder (13 glyph paths) | **187 ms** | 316 ms |

So resvg is marginally *faster* on canvas and PNG work, and **1.7× slower filling
these glyph outlines**. resvg's `tiny-skia` backend is slower than cairo at
filling many complex Bézier paths with antialiasing — and this workload is
nothing but that. The 23-spawn overhead it would remove is smaller than the
per-path penalty it adds.

**Verdict: keep `rsvg-convert`.** The smaller PNGs are not worth 2× the time,
because these placeholders are drafts that never leave `font-factory/`.

*Worth re-testing if* the placeholders ever become path-light (e.g. flat shapes
rather than glyph outlines), where resvg's canvas advantage would dominate.

---

## 3. libvips — slower than Pillow for this workload

Available: libvips **8.18.6**, `pyvips` 3.2.0. Tested against the agent-30
workload (5 PNGs → JPEG q85, the same parameters the pipeline uses):

| | Time (5 images) | Output size |
|---|---|---|
| Pillow | **294 ms** | 199,203 B |
| libvips | 315 ms | 199,375 B |

paste-5 itself hedged this as "a benchmark candidate, not an obvious
replacement". Measured: **not faster, and output is effectively identical.**
libvips pays off on large images, many transforms and bulk pipelines; this
workload is five small PNGs with a single encode each.

**Verdict: no.** (A missing `vips-openslide.so` module also emits warnings on
this machine — harmless here, but noise.)

---

## 4. Binary-searching the JPEG quality — works, small win

paste-5 suggested binary-searching the quality threshold instead of descending
the ladder. Tested on 11 images across varied content (flat, light shapes, dense
art, very dense, random noise):

| | Descending ladder | Binary search |
|---|---|---|
| Quality selected | q80 (×6), q95, q85, q60 (×3) | **identical in all 11 cases** |
| Encodes | 24 (6-image batch) | **18 — 25% fewer** |
| Wall (6 images) | 1373 ms | **982 ms — 28% faster** |

**Same quality, fewer encodes, same output.** One caveat found: on a flat image
the size sequence is **non-monotonic** at tiny sizes (`q70`=9 KB, `q65`=14 KB,
`q60`=9 KB), because `optimize=True` behaves differently at that end. Binary
search assumes monotonicity, so it is only safe because the non-monotonicity sits
far below the cap. The descending ladder has the same theoretical exposure.

**Verdict: safe and slightly faster.** But the absolute saving is ~0.4 s inside a
1.92 s agent-30 step, so it is a low-priority tidy-up rather than a win.

---

## 5. OTS — the recommendation worth adopting

`ots-sanitize` 9.3.0 is already installed; `pyots` 9.3.0 ships prebuilt wheels
with an in-process `sanitize()`.

**It sanitizes our real output cleanly** — generated OTF and WOFF2 both pass.

**And it catches a defect that actually shipped during this work.** Reproducing
the fontforge-truncated OS/2 table (version 5 written at the version-4 length):

```text
ERROR: OS/2: Failed to read version 5-specific fields
ERROR: OS/2: Failed to parse table
Failed to sanitize file!          exit 1
```

Our own `font_package_audit.py` also catches it, but **by crashing** with a raw
`struct.error: unpack requires a buffer of 22 bytes` from inside fontTools —
which tells you nothing about *what* is wrong. OTS names the table, names the
version, and exits cleanly. It is also a fully independent parser: it validates
every table against the spec, where our audit reads only fsType, name IDs and
glyph count.

**Verdict: adopt as a release gate** — an independent parse of the four delivered
formats, not a replacement for the existing audit.

---

## 6. Smaller items

**FontBakery** — available on PyPI (1.1.0), not installed. Not tested: it is a
broad project-QA suite, paste-5 itself says keep it off the hot path, and it
would duplicate checks we already have. Optional.

**Python** — already on **3.14.7**, so nothing to upgrade. `InterpreterPoolExecutor`
exists in this build, but that is the concurrency path excluded here.

**DeepSeek model — a real finding.** The configured role is
`deepseek/deepseek-v4-flash`, which the omp docs describe as **retired but still
accepted**. Both current ids are available on this machine:

```text
deepseek-flash          1M context
deepseek-v4.1-flash     1M context
deepseek-v4-flash       <- what ~/.omp/agent/config.yml uses
```

Also relevant: DeepSeek enables context caching by default, and cached input
bills at **$0.006/M against $0.300/M uncached** — a 50× difference that rewards
keeping a stable prefix. **Not changed**, because a different model may produce
different output.

---

## 7. Architectural advice — already done, or out of scope

- **Parallelise 20/22/29** — excluded by the user (one agent at a time).
- **Replace agent 28 with deterministic code** — plausible; agent 28 costs 3,826
  tokens per run and only routes. Not tested because it changes the workflow's
  shape.
- **Eliminate agent 13** — already largely done: its mechanical pass is one
  command and its only judgement work is `description.txt`, at 5,699 tokens.
- **Keep fontTools / uharfbuzz / Pillow** — agreed, and no evidence to the
  contrary: the fact sheet, which does all the font inspection, runs in **0.31 s**.
- **Structured output over prose** — already done for agent 27: it emits the plan
  and the renderer derives `theme.txt`, `image-notes/`, `art-direction.md`.
- **Context deduplication** — partly done via the `AGENTS.md` split (77% of it
  was listing-only and injected into every agent).
- **Compile the 53 KB spec into per-task packets** — partly done (annexes); the
  remainder is creative judgement, which is exactly what must not be compiled
  away.

---

## 8. Summary

Of the mechanical recommendations, **one is worth adopting** (OTS as a release
gate) and **two are not** (resvg, libvips) — both refuted by measurement on this
workload, and both for the same underlying reason: this pipeline is
path-rasterisation-heavy and process-light, which is the opposite of what those
tools optimise for.

The binary-search JPEG change is safe and slightly faster but saves ~0.4 s.

Nothing here changes the conclusion that **output tokens dominate wall clock**:
19,491 output tokens are ≈5.4 minutes of serial generation against a ≈19-second
mechanical layer. The three listing agents alone account for ~11,600 of those
tokens.

---

## Reproducing

```bash
# resvg comparison
python3 -m venv /tmp/venv && /tmp/venv/bin/pip install resvg-py Pillow numpy
# SVGs generated from the real plan via generate_font_text_placeholders.render_placeholder
# then: time rsvg-convert per SVG vs resvg_py.svg_to_bytes per SVG

# OTS on the real defect
fontforge -lang=ff -c 'Open($1); Generate($2)' font-factory/fonts/9-Equity/eQuity.otf /tmp/broken.ttf
ots-sanitize /tmp/broken.ttf     # exit 1, names the OS/2 version-5 fields
```


---

# paste-6 — additional items tested

paste-6 confirms the resvg and libvips rejections, agrees with adopting OTS and
the binary-search JPEG (both now applied), and raises three new items. Tested
2026-09-22; **nothing applied**, see the recommendation at the end of each.

## Local render parallelism — WORKS, 3.3×, output identical

paste-6 argues that parallelising the render jobs *inside one script* is not the
same thing as running multiple LLM agents concurrently. That distinction is
correct: it is CPU/process work within `generate_font_text_placeholders.py`, it
costs no model tokens, and it does not change the agent sequence at all.

Measured on the real 19 SVGs, `rsvg-convert` at varying worker counts (this
machine reports 12 cores), best of two runs:

| Workers | Wall | Per SVG | Speedup | Output |
|---|---|---|---|---|
| 1 | 3.54 s | 186 ms | 1.00× | — |
| 2 | 3.49 s | 183 ms | 1.01× | identical |
| 4 | 1.94 s | 102 ms | 1.82× | identical |
| 6 | 1.42 s | 75 ms | 2.48× | identical |
| 8 | 1.28 s | 68 ms | 2.75× | identical |
| **12** | **1.06 s** | **56 ms** | **3.34×** | **identical** |

Output md5s are identical at every worker count, so this is a pure wall-clock
change. There is no useful gain at 2 workers; it scales from 4 upward.

**Where the renderer's time actually goes**, measured by phase:

| Phase | Time |
|---|---|
| `OutlineFont` load (×2) | 0.29 s |
| 19 placeholder renders | **4.93 s** |
| specimens (subprocess, 4 more rsvg renders) | **3.53 s** |
| one validator pass | 1.18 s |

So **8.46 s of the renderer's 11.5–14.3 s is rsvg work** and is parallelisable,
plus the second validator pass and the derived views for the remainder.

**Recommendation: worth doing, but not yet.** It would take the renderer to
roughly 5–8 s, saving ~6.5 s — which is still only ~1% of a full run, because
the run is dominated by model output. paste-6 reaches the same conclusion
itself: *"I would not spend days engineering it until the agent-generation side
is fixed."* It also forces a thread pool into a renderer that currently has a
clean atomic staging-and-swap design. Revisit once output tokens are addressed.

## Per-agent thinking effort — mechanism exists, nothing configured

paste-6 suggests running high effort for reasoning agents and low/none for
formatting-heavy ones. Findings:

- `~/.omp/agent/config.yml` sets only `defaultThinkingLevel: auto` globally.
- **No wrapper sets a per-agent `model:` or `thinking-level:`** — so every agent
  inherits the session default.
- omp does support per-agent `model` and `thinking-level` frontmatter, but
  `task.enableEffort` defaults to **false**, so the effort hint is not exposed
  unless that is turned on.
- `deepseek-flash` supports **`low, high, max`** — there is **no `medium`**, so
  paste-6's suggested "high/medium for BOOTH" has no middle rung to select.

Benchmarking the quality trade-off needs real agent runs, so this is **flagged,
not applied**. The plausible split is: high for agent 27 (visual reasoning) and
the three listing agents' research, low for pure formatting, and no LLM at all
for packaging and orchestration.

## Model routing — paste-6 corrects my earlier finding

I previously flagged `deepseek-v4-flash` as a retired id worth renaming to
`deepseek-flash`. paste-6 states the legacy name is currently served by
V4.1-Flash anyway, so the rename buys nothing today. I cannot verify a
server-side routing claim from here, and the honest position is that **my earlier
framing overstated it** — it is config hygiene, not a speed lever. Left
unchanged, and the effort finding above supersedes it as the useful part.

## Already covered elsewhere in paste-6

- **Structured output as the canonical representation** — done for agent 27: it
  emits `visual-plan.json` and the renderer derives `theme.txt`, `image-notes/`
  and `art-direction.md`. Pushing the same pattern at the three listing agents is
  the open item, and it is the one with real leverage.
- **Separate shared from product-specific context / exploit prefix caching** —
  partly done via the `AGENTS.md` split and the listing annex. Cached input bills
  at $0.006/M against $0.300/M, so keeping the prefix stable is worth doing
  deliberately rather than accidentally.
- **Deterministic orchestration instead of agent 28** — plausible; 3,826 tokens
  spent on routing. Not tested, because it changes the workflow's shape.
- **Their "don't bother" list** (resvg, libvips, fontTools/uharfbuzz/Pillow
  rewrites, Python version) matches the measurements in this document.
