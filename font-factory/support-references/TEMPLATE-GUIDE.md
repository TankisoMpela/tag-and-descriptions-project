# Supporting-template handoff guide

Source of truth for Agent 27 when the renderer selects 12 supporting
templates. The native Skia catalogue lives in six files: the original 26 panels in
`bin/pin-studio/pin_studio.py` and 44 reference remakes in
`bin/pin-studio/support_templates/{t30332,fashion,photo,poster,objects}.py`.
Every native slot name and guard quoted below is read from those files, so this
guide and the renderer cannot disagree. If you change one, change the other.
The stable slots from 71–172 hold the HTML-only source remakes documented
after the native layouts. The guide retains historical sections for retired
layouts; `support-html/catalog.json` and the renderer's retirement and eligibility
gates determine the live catalogue. Seller-selected retirements added on 2026-10-26:
`line32`, `duo32`, `card32`, `hand32`, `zebra32`, `electromagnetic32`,
`demolition32`, `skinbadge32`, `gelatocards32`, `angelinastyle32`, `beachclub32`,
`fluorescentduo32`, and `lastnightsweden32`.

Seller-selected retirements on 2026-11-03: slots 65, 101, 138, 139, 174, and
177 (`herbalproduct32`, `nectarambience32`, `playerglyph32`, `alicebadge32`,
`statueframe32`, and `fashioncard32`). Their slot numbers, source material, and
editors remain as history; they are excluded from the current 137-template
catalogue and future support runs.

Support images must not repeat the font's name — the thumbnail already does that.
Captions and alt text describe the rendered result, not an imagined product
photograph.

Image-backed templates use their documented text-free background plates.
Source-reference wording, studio credits, font names, and font-category claims
are not template copy: keep them removed from the plate and use generic,
buyer-relevant supporting text in the template's editable slots. The selected
font file renders display copy; functional labels use a neutral sans-serif.
Never let a reference typeface name or category stand in for the current font's
verified profile. New photo-led references and text-clean plates are documented
in `materials/user-batch-2026-11-03-a/README.md`.

Generic new copy that is drawn with a showcased font uses Title Case, with an
initial capital on each word. Source-led remakes preserve the wording and case
of their reference. Do not force all-caps display copy: a face intended for
capitals supplies that look through its own letterforms. Keep exact letter,
digit, and symbol specimens in their literal case.

## How to read this guide (token contract)

Read **Part 1** and **Part 2** in full, then open **only the catalogue sections for
the 12 templates this font actually shipped**, including later registered-
template additions. The renderer prints the selected names on the `supports:`
line; look them up rather than scrolling the whole catalogue. Other parts are
reference, not required reading every run.

Conventions used below:

- All type sizes are the renderer's own `N*scale` values. On the shipped 3:2
  surface (`FRAMES["3x2"] = 2400x1600`) `sh.scale = min(w,h)/1000 = 1.6`, so
  `560*scale` means 896 px. Sizes in Part 3 are the source numbers; multiply by
  1.6 for the PNG.
- `hi` / `lo` are the auto-fit search bounds; `min_read` is the legibility floor.
- "Locked" means the panel ignores the theme roll entirely — its palette is
  hard-coded RGB and no `--palette` / `--mode` / brief `theme` will move it.
- Each remake module defines its own local text helper with its own defaults, so
  a panel's entry says which helper governs it. Do not assume one module's
  defaults are another's.
- Every fixed string, size and floor quoted here was read out of
  `bin/pin-studio/support_templates/*.py`, which is under active edit. If your
  render disagrees with an entry, the code is right — re-read the panel function
  and fix this file, not the PNG.

---

# Part 1 — The system that protects you

You are not designing these panels. A shared renderer designs them and refuses to
ship a panel it cannot make work. Your job is to feed it honest copy and honest
font facts, and to read its errors instead of polishing PNGs. Thirteen mechanisms do
the protecting; know them before you read a single template.

## 1.1 One surface, one pass

Every Agent-27 support panel uses the shared HTML/CSS catalogue renderer and is
composed independently at 3:2 and 1:1. The regular native Skia renderer remains
available for catalogue maintenance, but is not used for this handoff.
`--support-count` is fixed at 12 by `bin/generate_font_text_placeholders.py`;
passing any other value is a hard
`SystemExit`.

## 1.2 A layout error fails the whole handoff

The renderer and handoff validator stop on any layout or asset failure.
**One bad panel means no handoff at all** — which is why
the errors in Part 3 are the interesting part of this document, not a footnote.
Fix the reported error and re-run; never hand-edit a generated PNG.

## 1.3 Copy inlets — use the selected template's authored copy

Agent 27 renders 12 selected templates through the shared HTML/CSS catalogue
with `--support-renderer html --support-ratios both`. Do not author custom
support promos or inject a second generic copy set. Each selected template's
authored copy, factual fields, and font-fitting rules govern its output; consult
only the Part 3 entries for the selected designs. The family showcase layouts
are eligible when the source has at least two real styles and participate in
the same seeded selection as the rest of the class-fit pool.

## 1.4 The blanking rules (why your copy may silently vanish)

The rules in §§1.4–1.11 describe the legacy native Skia layouts. Agent 27's
production handoff uses HTML/CSS templates; use their Part 3 contracts and the
renderer `contentWarnings` for that output.

Before any support panel runs, `render()` blanks a copy value if it:

- equals stock copy — `SUPPORT_STOCK_COPY` = `whisky`, `whiskey`,
  `midnight letters and loud labels`, `invitation suite editorial packaging`;
- **contains the font name** as a token sequence (`_support_has_font_name`).

Then per-panel helpers add their own refusals:

- `panel_text()` takes authored `word`, else `line` **only if it is 4 words or
  fewer**, else the panel's own pool, else `"TYPE STUDY"`. The font name never
  fills this slot.
- `lead_in()` ignores an authored `over` that is one of `STOCK_LEAD` —
  `introducing`, `now available`, `new release`, `coming soon`, `announcing`,
  `just released`, `launch day`, `available now` — and rolls its own instead.
- `_support_copy()` collapses a name-bearing fallback to `"LETTERFORMS IN MOTION"`.
- `_nm_free()` (used by `card32`, `sticker32`) additionally refuses any candidate
  containing a 3-character token of the font name, or any glyph the face cannot
  draw, and title-cases what survives.

## 1.5 Your copy is title-cased, not lowercased

`shout()` / `tc()` capitalise word initials and **never force lowercase**. A
display slot that reads `"quiet mornings"` comes back as `"Quiet Mornings"`. Small
companion type set in the companion face is the only place lowercase survives, and
only where a panel explicitly lowercases it (e.g. `wash32`'s lead-in).

## 1.6 Glyph coverage: tofu is impossible, empty slots are not

`usable(ctx, ch)` is true only when the character is in the font's cmap and not in
`flagged` (dense placeholder glyphs, shared-outline digits, zero-advance accents).
`clean(ctx, text)` strips every other character, so **no slot ever renders tofu**.

The trap this creates: on hard-coded panels a stripped string can become empty or
near-empty and the panel still reports a clean render. `zebra32`, `soldier32`,
`mirror32` and `alphabet32` all push fixed specimen strings through `clean()`. If a
face lacks `€ £ † ½`, those characters simply disappear.

**This is the one defect class the renderer cannot see, and it is measured, not
theoretical.** Every remake panel writes its wording as a literal, so a face without
the glyphs loses them silently. Running the check below over all 27 font binaries in
`font-factory/fonts` produced:

- **27/27** — `greetingsgrid32` renders `Привет!` on a tile labelled `RUSSIAN`. Not one
  face in the factory carries Cyrillic, so the tile ships as a bare `!`: 14% of the
  string survives, **zero layout errors, zero notes, exit code 0**. The `Å` in `HALLÅ!`
  and the `¡` in `¡HOLA!` thin on some faces (`Augallion`, `Retrofest`, `Blazher`), so
  the six tiles degrade unevenly within one grid.
- **11/27** — `glyphsheet32` sets the row `()[]{}+−=` with U+2212 MINUS SIGN; those 11
  faces lose the last operator.
- **2/27 each** — `blossom32`, `colosseum32` and `storyteller32` lose a typographic
  apostrophe. Cosmetic; the row still reads.

Note what `--json` cannot tell you: `greet4` reports a normal size (`165`) on a tile
that painted one glyph, because stripping happens **before** `fit()`. Slot sizes prove
how big, never how much — only the PNG or this predictor proves content.

This glyph predictor applies only to the legacy Python/Skia layouts. It does not
audit Agent 27's HTML/CSS support output and must not be reported as coverage
evidence for that handoff. Chromium preserves full text and uses a readable
fallback for missing glyphs; inspect the rendered HTML `contentWarnings` and
layout report instead. For a separate native/Skia render, the predictor can
identify empty or thinned fixed slots:

```bash
python3 bin/check_support_glyph_coverage.py \
  "font-factory/fonts/{input-slug}/{Primary}.{ext}"
```

It parses the renderer's own literals, checks them against the font's cmap, and
exits non-zero naming every panel that would ship an effectively empty slot
(`EMPTY`) versus a merely thinned one (`thin`). Treat an `EMPTY` line as a real
finding to report, not something to work around. Never hand-edit a PNG to
restore a lost glyph. The predictor needs only
`fontTools`, so plain `python3` is right for it — `pin_studio.py` itself needs the
Skia build in `bin/pin-studio/.venv/bin/python`.

Panels that must spell a whole word refuse it instead: `panel_text` takes a pool
candidate only when the face draws **every** letter of it — "a bitten word is a
worse sheet than a repeated name".

## 1.7 Sizing: fit between `lo` and `hi`, and the floor that errors

`fit()` binary-searches (16 steps) the largest size that fits the declared box
between `lo` and `hi`. Two distinct outcomes:

- **Too wide / too many lines to reach `lo`** → problem
  `"{slot}: cannot fit a WxH slot — …"`. Hard error.
- **Fits, but below `min_read`** → problem
  `"{slot}: {size}px is below the {min_read}px legibility floor — about {room}
  characters fit this slot, the copy has {len}"`. Also a hard error.

So the renderer will not quietly shrink type into unreadable small. It stops. The
word budgets in Part 3 exist so you never hit this.

Between those rails, panels do degrade *visually* without erroring: a long phrase
in `quote32` or `neon32` triggers a whole-block shrink factor `k`, which shrinks
the companion lines with it and flattens the hierarchy. That is the "unintended
bad derivation" you must watch for — it passes validation and looks merely
average. The word budgets prevent it; Part 5 tells you how to spot it.

## 1.8 Contrast: measured against the pixels actually painted

`Sheet._behind(box)` samples the **median relative luminance of the ground really
drawn under that slot** — after the gradient, device, texture, ghost and photo.
`_enforce()` then lifts the ink with `readable()`, which binary-searches the
shortest blend toward black or white that clears the floor (14 steps).

- Default floor `min_contrast = 4.5`. Panels pass other values where the artwork
  demands it: `duo32` 2.2 (type crosses palm silhouettes), `sticker32` 2.6/3.2/1.7
  (pre-resolved stock/ink/shadow settle), `neon32` 3.0 (a tube is not text),
  `crest32` 3.5, `feature32` 2.6, `hand32` 1.6 over linework, `card32` and
  `echo32` small type up to 6.5.
- A successful lift is a **note**, not an error: `"{slot}: ink lifted X:1 -> Y:1"`.
- An unreachable floor is an **error**: `"{slot}: X:1 against the ground behind it
  and {floor}:1 is unreachable there"`.

This is why the palette worlds are hand-tuned rather than hash-generated: the
paper worlds deliberately carry dark accents near 5:1, because a bright marigold
on cream measures 2.2:1 and the guard would drag it toward the ground colour until
every "coloured" row came back the same flat brown.

## 1.9 Geometry: off-canvas and overlap

`Sheet.verify()` adds exactly two checks beyond the queued problems:

- `OFF-CANVAS <slot>` — ink outside the frame, unless the slot declared `bleed`.
- `OVERLAP a/b: WxHpx` — two `collide`-enabled slots overlapping more than 2 px on
  both axes.

Decorative marks register `collide=False` (sun discs, palms, photo panels, frames,
ghosts), which is how `plakatart32` can legally drop its wordmark over the art's
lower-left corner. Do not read "no overlap error" as "these two elements do not
touch".

## 1.10 Themes: twelve worlds, and which panels ignore them

`THEMES` holds twelve worlds, each bundling a palette, a ground mode, a light-pool
intensity, a speckle count, a device (the graphic signature under the type: dots,
grid, rays, bands, rings, lanes, ruling) and an ornament set.

- Six shared worlds: `midnight, sage, ember, bone, moss, clay`.
- Class-owned worlds that never leak into another class: `vellum`/`gilded`
  (blackletter), `asphalt`/`chrome` (sports), `graphite`/`inkwell` (script).

`assign_themes()` rotates each panel's `THEME_PREF` shortlist by
`sha256(font name)` and takes the first world not already used in the roll, so a
re-run of the same font lands identically and two similar fonts do not ship the
same colour world. Because 120 active panels draw from at most eight usable worlds,
repeats across a 13-design set are possible once the shortlist is spent.

**Roughly half the catalogue ignores all of this.** Every panel that sets its
colours as literals (1.11) overrides the palette, so a `theme` you author for it
changes nothing on the dark ground it was built for. Do not spend reasoning on
theme choice for those — but read 1.11's fourth behaviour before assuming a
hard-coded panel is inert.

## 1.11 Locked vs flexible — the real split

The catalogue has four behaviours, not two. Which one a panel has decides whether
theme choice is worth any of your attention.

- **Flexible (theme-adaptive ground and ink):** `line32, duo32, card32,
  sticker32, neon32, quote32, crest32, echo32, hand32`. No remake panel
  belongs here: the two that used to set a headline in `P["ink"]` over their own
  ground — `ovalword32` and `cliffpostcard32` — are now built on a supplied clean
  plate with fixed ink.
- **Nudged (locked artwork, one accent tinted by the theme):** the eight
  `fashion.py` panels mix 7% of `P["accent"]` into their house red; the six
  `poster.py` panels mix 3–8% of `P["accent"]`/`P["accent2"]` into their ground and
  signal colours; the seven `photo.py` panels keep locked type and derive exactly
  one rule or chip through `theme_ink(ctx, ground)`; a few `t30332.py` remakes take
  only the `light_pool` or one star. The world changes the temperature of the
  sheet, never its identity.
- **Ink inherited from the theme (the one that surprises people):** `objects.py`
  has no palette reads inside its panels, yet its shared `type()` helper defaults
  `color=` to `ctx["pal"]["glow"]`, and thirteen of its fourteen panels never pass a
  colour. Their type is therefore the theme's glow, not a hard-coded white. In all
  ten palettes `glow` is a near-white, and these grounds are hard-coded dark, so the
  sheet looks immovable — until the contrast guard finds a lighter ground under it,
  lifts that near-white ink to a dark tone, and the whole panel changes. `typewall32`
  is the only `objects.py` panel that pins its own ink. This is the mechanism behind
  most of the `ink lifted` notes in the sweep (Part 5).
- **Locked by default (source-matched RGB; explicit CLI overrides still work):**
  `feature32`.
- **Locked (hard-coded RGB; theme roll ignored):** `mountain32, zebra32, soldier32,
  mirror32, brutal32, brutalpack32, rio32, boots32, plakatart32,
  mangos32, alphabet32, birvase32, weightfamily32, mangosboard32`.

`hand32` is the useful hybrid: its artwork and three words are fixed, but its
ground, type ink and hand tint follow the theme — and its hand ink follows the
**theme accent**, which is why pink is one option, not a rule.

### Who carries the theme

Palette reads live in shared helpers as often as inside the panel, so "this panel
never mentions `ctx["pal"]`" proves nothing.
`python3 bin/check_support_catalogue_facts.py` prints the panels that read the theme
in their own code, then names the helpers that read it on a panel's behalf:

| Helper | Reached by | What the theme controls |
|---|---|---|
| `fashion.colors()` | all eight `fashion.py` panels | house red, 7% accent |
| `poster.text()` / `line()` / `rounded()` | all six `poster.py` panels | ground wash, signal colours |
| `photo.theme_ink()` | the seven `photo.py` panels | one rule or chip |
| `objects.type()` | thirteen `objects.py` panels | every glyph's ink = `pal["glow"]` |
| `t30332._backdrop()` | remakes with no supplied plate | the fallback ground pair |

If a panel must be genuinely theme-proof, prove it with pixels rather than with a
reading: render one font twice with two opposite `--palette` values and compare the
folders — `python3 bin/check_support_theme_lock.py A/3x2 B/3x2`. Identical bytes mean
the theme cannot reach the sheet; a mean RGB delta under 1 says only the grain moved.

## 1.12 Eligibility and selection of the 12 designs

The active catalogue has 133 templates across 182 stable slots. The Agent-27
HTML/CSS handoff resolves the font class, excludes retired and class-incompatible
layouts, then applies each template's real-family-style gate. When the source has
at least two distinct styles from one family, `weightfamily32`, `mangosboard32`,
and `italicregular32` become eligible for selection; none is
guaranteed. Any selected showcase uses actual sibling files; `italicregular32` chooses the closest opposite
italic/upright style when available, otherwise the nearest distinct sibling,
and labels the comparison with the real style names. `boots32` is also gated on
two real styles but is sampled rather than guaranteed.
Seller-retired layouts `contour32` (10), `plakat32` (20), `voguecover32` (37),
`confident32` (38), and `parkstatement32` (179) remain described below as design
history but are excluded from selection and new handoffs.

All eligible layouts, including family showcases, use the same seeded
least-used/random class-fit selection based on
`sha256("{font_name}|{class}|support-catalogue")`; the same name, class, and
support-history counts produce the same 12 designs. The current eligible-pool sizes are blackletter
120, handwritten 125, tech/sports 121, brush 128, pixel 127, and display 128.
Each ratio folder receives 12 images named
`support-{N}_{template}.png`, where **N is the catalogue slot, not a 1–12
ordinal**. Gaps are normal and a panel keeps its number across runs.

The separate `--support-review-all --support-renderer html` mode is a full
catalogue review, not a normal font handoff; it bypasses class-fit filtering but
keeps retirement and actual-family-style gates.

## 1.13 Facts the panels assert for you

Some panels print real measurements taken from the binary, which is why you must
not overwrite them with claims:

- `EDGE(ctx)` prints `"{glyphs} Glyphs"` or `"{n} OpenType Features"` from the
  audit — used by `line32`, `contour32`, `crest32`'s lower arch.
- `plakat32` counts uppercase and lowercase coverage against A–Z/a–z with
  `usable()`, prints `"{caps}/26 CAPS · {lowers}/26 LOWER"`, and positions its
  weight marker at `(weight-100)/800` and its style marker from `slant > 0.01`.
- `weightfamily32` / `mangosboard32` label each row with the sibling's **real name
  ID 17 style string** and set each row in that sibling's own file. They never
  synthesise a weight.

Conversely, `mangos32`'s weight ramp, infinity loop, `100g`, `~ 272 kJ` and
`Mangifera indica L.` are **artwork, not font facts**. Selling that panel as
variable-font evidence is the single worst derivation error available here.

---

# Part 2 — Choosing what suits the face

You do not choose the 13. You choose the two things that steer them: the
`renderer_class` and the honesty of your `font_profile`. Get those right and the
catalogue self-selects.

## 2.1 The class call drives everything downstream

`renderer_class` must be one of `elegant`, `blackletter`, `sports`, `script`,
selected from the font's **actual forms**, and it is passed to the renderer as
`--class`. It controls which class-owned worlds enter the roll, and — with the
inferred `family` — which panels are unfit. A wrong class is not a cosmetic error:
it smuggles a crest onto a techno face, or dresses a blackletter in an elegant's
clothes.

`--about` (built from `font_profile.construction + personality + buyer_fit`,
truncated to 240 characters) is the other lever: `classify()` reads it, and the
renderer's own comment says it plainly — *"the outlines alone misclassify
handwritten, tech and blackletter faces"*. Write those three profile fields with
concrete structural language (`connected script with looping entry strokes`,
`geometric monoline with squared terminals`), not marketing adjectives.

## 2.2 Structural fit, by what the face is built from

| The face | Panels that flatter it | Panels that fight it |
|---|---|---|
| High-contrast display serif / elegant | `line32`, `echo32`, `crest32`, `card32`, `quote32` | `sticker32`, `neon32` (hairlines die in the fat treatment) |
| Flowing script / brush / swashy | `wash32`-style flow, `line32`, `quote32`, `card32`, `mountain32`, `plakatart32` | `crest32` arches and `line32`'s echo are auto-suppressed for `FLOWING` families (`script, brush, blackletter, swashy`) — expect the eyebrow/echo to be absent, not missing |
| Blackletter | `vellum`/`gilded` worlds, `crest32`, `echo32` | `sticker32`, `duo32` (silhouette posters fight texture) |
| Sports / geometric monoline / techno | See the tested Strong and Conditional sets, and exact hard exclusions, in the [six-style paired audit](class-audit-2026-10-14/README.md); its tech/sports group preserves conditional editorial/illustrative matches while excluding only reviewed hard mismatches | Use the audit’s class-specific list rather than assuming the whole group shares a single structural-fit rule |
| Ultra-bold display | `sticker32`, `duo32`, `echo32`, `feature32`, `birvase32` | `soldier32`/`mirror32` small rows (legibility floors bite) |
| Hairline / light | `line32`, `quote32`, `rio32`, `mountain32` | `sticker32`, `neon32`, `zebra32` — heavy flat treatments need mass to survive |
| Genuine multi-style family | `weightfamily32`, `mangosboard32`, and `italicregular32` (eligible, not guaranteed, when at least two real styles exist) | — |
| Single style only | — | family proofs are not offered; never claim a range |

## 2.3 Word budgets at a glance

Only for the 13 original panels that read copy. Anything outside these budgets either
errors at the legibility floor or survives by shrinking the whole block flat.

| Panel | Ideal | Hard limit | Never |
|---|---|---|---|
| `line32` | 2–4 words, 2 unbalanced lines | 2 lines | the font name |
| `duo32` | 1 word, 3–9 characters | tail capped at ~48% of initial height | words under 3 chars |
| `card32` | word 1–2, phrase 3–5, cap 2–4, foot 2–4 | phrase 2–3 card rows | name tokens |
| `feature32` | exactly 3 words | 3 rows (extra words are re-cut, not added) | name |
| `sticker32` | 1–2 words | 3 words | name |
| `neon32` | 1–4 words | 2 lines | >4 words (silently dropped to pool) |
| `quote32` | 3–6 words | 3 lines | >8 words (middle line collapses) |
| `crest32` | 1 word 4–9 chars + two 2–4 word arches | arch floor 24*scale | long arches |
| `echo32` | 1 word, or 2 short words | 2 lines | 5+ words |
| `contour32` · retired | any word — only its first letter is used | 1 glyph | a word the face cannot draw |
| `plakat32` · retired | 2–4 words | 2 lines | name |
| `plakatart32` | 1–2 words | 1 line | 3+ words |
| `birvase32` | 1–2 words | **hard-clipped to 2 words** | 3+ words |

The remakes split the same way between two inlets, and the difference matters:
**`panel_text` panels cap `line` at 4 words and roll their own pool above that**, so
over-long authored copy is *replaced*; **`_support_copy` panels have no cap at all**,
so over-long copy is *rendered* and shrinks toward the floor instead. Roughly half of
the 44 read authored copy somewhere; the rest are hard-coded end to end — all
fourteen of `objects.py`, plus whichever `t30332.py`/`fashion.py` panels currently
carry literal display lines. `python3 bin/check_support_catalogue_facts.py` prints the
split per panel (`reads` / `fixed` in its copy column) and reprints it every time the
modules move, so treat that column as current and this sentence as approximate. In
some of the `reads` panels the inlet only reaches the body or the small type, so their
**display lockup is a literal** and authoring a headline has no effect there — `voguecover32`
is the standing example, and the table below marks every panel whose display is fixed.

| Panel | Ideal | Hard limit | Never |
|---|---|---|---|
| `ovalword32` | 1 word, ≤9 characters | 1 line, floor 100 | a word the face cannot spell — its fallback is `Type Study` |
| `stardust32` | nothing (its stack is fixed) | 3 lines by construction | expecting authored display copy |
| `cliffpostcard32` | nothing (both headline lines are fixed) | 2 lines, floor 68 | expecting authored copy |
| `kindersea32` | 2–4 | 3 lines, floor 70 | >4 (pool) |
| `messageframe32` | 6–10 | 5 lines, floor 54 | — |
| `sunsetpromise32` | 4 fixed lines | 4 outlined lines, floor 52 | — |
| `pixelquote32` | nothing (its five-line quote is fixed) | 5 lines, floor 52 | authored display copy |
| `voguecover32` · retired | nothing (only its note rolls) | — | authored display copy |
| `confident32` · retired | 2 words | 1 line, floor 68 | 3+ |
| `storyteller32` | 10–16-word body | 3 lines at floor 16 | an ALL-CAPS body |
| `focusposter32` | exactly 1 word | floor 84 under `hi 420` | 2+ words |
| `blossom32` | 8–14-word body | 3 lines at floor 15 | — |
| `neue32` | 1 word, ≤7 characters | renders 6×: rows floor 82 **and** pills 13 | multi-word |
| `electromagnetic32` | 2–4 | 4 lines, floor 42 | one very long word |
| `demolition32` | 3–5 | 4 lines, floor 40 | 8+ |
| `yearposter32` | 4–6 characters | 1 line, floor 160 | 8+ characters |
| `stadiumposter32` | 3–4 (it auto-splits into 2 lines) | floor 80 twice | 1 word, 7+ |
| `signalclock32` | a short numeric-ish token | 1 line, floor 74 in `0.66w` | a long word |
| `amberdawn32` | 1–3 | 2 lines, floor 64 | >4 (pool) |
| `skinbadge32` | fixed `Skin / Tribe`; fixed `Tribe Tribe` repeat | headline 2 independent lines; repeat renders 5× | — |
| `latestlook32` | fixed three-row phrase | 3 independently measured lines, floor 56 | — |
| `gelatocards32` | fixed `SWEET SCOOPS` | front-card phrase 2 lines, floor 40 | — |
| `meditation32` | fixed `STILLNESS` | 1 line, floor 50 | — |
| `strongweak32` | lead-in only | 1 line | expecting to set STRONGEST/WEAKEST |
| `funkyfashion32` | fixed `FUNKY / FASHION` | 2 independently measured lines, floor 40 | — |

## 2.4 Colour latitude and intensity

- **Flexible panels** take the theme's ground and accent as-is; you do not pick
  hex values for supports at all. The `palette` block in `visual-plan.json` is for
  the **two thumbnails only** and is not read by the support renderer.
- Intensity is set by the world's `pool` value (light-pool alpha: 0.10 on `sage`,
  0.18 on `midnight`) and by `tooth` (speckle count). Panels then scale it —
  `contour32` paints at `pool*0.7, tooth*0.6`, `neon32` at `pool=0.03`,
  `feature32`/`crest32`/`echo32` at `pool=0.0`–`0.05` because a flat field is the
  design.
- The remakes mostly **declare their own grounds and let the theme be a rim**: a
  `t30332` `_backdrop` mixes a fixed top/bottom pair, adds one `P["accent"]`
  `light_pool` and seeds its grain from the theme; `poster.py` mixes its reference
  ink 3–8% toward a palette key; `fashion.py` mixes exactly 7% of `accent` into the
  house red at a 3.0 floor; `photo.py` uses `theme_ink` on **one element per panel**.
  A world therefore nudges these panels rather than re-skinning them.
- **Locked panels** carry their own palette and will look the same whatever you
  argue for — all 14 `objects.py` slots plus `phonegarden32`, `contactlist32`,
  `pixelquote32` never read `ctx["pal"]` at all. Their fixed colours are quoted in
  Part 3 so you can caption accurately.
- Never describe a support image's palette as chosen for this font. It is either
  the rolled world or the reference's own ink.

---

# Part 3 — Template reference

Format per panel: **Draws · Copy · Budget · Sizing · Colour · Guards · Caption ·
Alt text.** "Copy: none" means the panel is hard-coded and authoring anything for
it is wasted effort.

## Flexible panels

### `line32` — the letterpress broadside
- **Draws:** theme ground and device; the phrase set as up to 2 full-measure
  letterpress lines; the initial of the last drawable letter ghosted bottom-right
  at ink alpha 0.10 with an accent wireframe at 0.24; line one echoed as an accent
  wireframe (alpha 0.30, stroke 2.0*scale); eyebrow with an accent tick rule
  (alpha 0.90); edge type; footer `DISPLAY SPECIMEN`.
- **Copy:** `line` then `word` (fallback `"LETTERS THAT MATTER"`); `over` → eyebrow,
  default `"New Release"`.
- **Budget:** 2–4 words. `pack_lines` caps at 2 lines.
- **Sizing:** `hi 560*scale`, `min_read 46*scale`, `fill=True`, `lead_frac 0.08`,
  centred; each row grown edge-to-edge and tone-lifted per row against the measured
  ground at 4.5.
- **Colour:** flexible ground and ink; accent only on the tick rule and echo.
- **Guards:** `"line32: the face draws no word of this line"` when nothing is
  spellable. The echo is **suppressed** for `FLOWING` families and when
  `contour_density(line one) >= 0.5` — a dense face's outline echo reads as mud.
  Expect no echo on a script; that is correct, not a fault.
- **Caption:** the large echoed phrase. **Alt text:** oversized letterpress wording
  and paper texture.

### `duo32` — the summer sign poster
- **Draws:** the source's cobalt print field, coral sun at 0.775w/0.375h
  (radius 0.24h), two near-black palm silhouettes over a mound, and an ivory
  oversized initial at 0.055h; the rest of the word crosses the initial and sun
  on its own 0.52h baseline. A restrained dark keyline protects the crossing
  word over the palm silhouettes; the tagline sits below it.
- **Copy:** `word` then `line` (fallback `"SUNSHINE"`); tag = `sub`, then `over`,
  then the source phrase `"knows how to party"`.
- **Budget:** one word of 3–9 characters; tag 2–3 words.
- **Sizing:** tail `fit_measure hi 470*scale`; word slot `hi=lo=tsize`,
  `min_read 40*scale`, `min_contrast 2.2`; tag `hi 158*scale lo 20`,
  `min_read 20*scale`.
- **Colour:** cobalt ground, coral sun, warm-ivory type, and near-black palms;
  explicit CLI palette/mode overrides remain available.
- **Guards:** `"duo32: the face draws no word long enough to split"` under 3
  characters. The 2.2 floor is deliberate — type crosses palm and sun edges — so
  the low floor is not a licence to use a pale ink. The tail is capped so its
  height stays under ~48% of the initial.
- **Caption:** the title. **Alt text:** the sun disc and palm shapes.

### `card32` — the stacked paper cards
- **Draws:** bench ground and device; a caption eyebrow; a full-height word column
  on the left (0.34w); two tipped paper cards on the right (0.50w x 0.62h at
  0.655w/0.485h) — back card blank at 0.84 scale tipped +2.8°, front at -2.2° with
  drop shadows at alpha 0.26/0.38 and two tape strips at alpha 0.34 rotated ±38°;
  the phrase lettered across the front card with cap and foot in the companion
  face; a hairline border mixed 0.35 toward the accent at alpha 0.55; edge type;
  footer.
- **Copy:** four slots, all through `_nm_free`, all title-cased.
  `word` pool `("Always","Steady","Brightly","By heart","Onward")`;
  `line` pool `("Made to be read","Set in good faith","Worth reading twice",
  "Cut for the long run","Printed to be kept")`;
  `over` pool `("In hand","Fresh off the press","On the bench","Proof for the buyer")`
  fallback `"In Hand"`;
  `sub` pool `("Invitations and vows","Mastheads and margins","Posters and patches",
  "Banners and tickets","Marquees and sleeves")` fallback `"Fresh From The Bench"`.
- **Budget:** word 1–2, phrase 3–5, cap 2–4, foot 2–4. Column caps at 2 lines; card
  phrase at 2–3 rows.
- **Sizing:** column `hi 520*scale min_read 48*scale`; card `hi 380 min_read 44`
  (card-space pixels); cap `hi 32 lo 14`; foot `hi 34 lo 15`.
- **Colour:** the paper is *chosen* — the renderer picks whichever of six candidate
  grounds has the highest contrast against the measured bench, then repairs every
  ink with `readable(...,4.5)` and the tape at 1.6. Maintain clear card edges.
- **Guards:** `"card32: the face draws neither a word nor a phrase that is not the
  name — there is nothing to letter"`. Dropped entirely for `sports`, `pixel`, `mono`.
- **Caption:** the phrase. **Alt text:** the layered paper specimen.

### `feature32` — the scalloped call card
- **Draws:** warm paper stock; a scalloped frame with concave corner bites,
  radius 92*scale, stroke `max(3.0, 5.2*scale)` at alpha 0.96; one large specimen
  word centered across the card; two compact feature labels on opposite shoulders,
  each ruled and dotted to the word like the source's patent-drawing callouts.
- **Copy:** `word`, then the widest usable token in `line` (fallback
  `"Crystal"`, matching the source specimen). The heading is `"OpenType Features"`; labels report supported
  GSUB features or neutral copy when no tags are present.
- **Budget:** one word; the font name is never used.
- **Sizing:** hero `hi 720*scale`, one line, centered; labels `hi 48*scale lo 14`;
  heading `hi 64*scale lo 20`.
- **Colour:** warm-paper and oxblood source palette by default; explicit CLI
  palette/mode overrides remain available. Frame uses
  `readable(ground, ink, 5.5)`, callout ink `readable(ground, accent, 5.0)`,
  text slots at 2.6.
- **Guards:** `"feature32: the face draws no usable specimen word"`.
- **Caption:** the headline. **Alt text:** the ruled feature callouts.

### `sticker32` — the die-cut
- **Draws:** a speckled wall (`pool 0.13, tooth 1`); one phrase as up to 2 fat
  slabs centred in a stage, each drawn three times — a flat offset shadow cutout,
  the die-cut stock band, then the ink fill, with a round-joined stroke of
  `2*band` as the cut edge; the whole block tilted `((seed%9)-4)*0.75` degrees.
  No rules, no footer, nothing else on the sheet.
- **Copy:** `word`, then `line` **only if 3 words or fewer**, else the pool
  `("Hand set","Fresh ink","Read me","Made to last","Say it loud")`. Never the name.
- **Budget:** 1–2 words.
- **Sizing:** two words make two lines; one word of 6+ characters splits at the
  most even ink seam when its band would be under 0.30 of the stage height.
  `fit_measure hi 820*scale`.
- **Colour:** a three-ink settle in strict order — stock
  `readable(ground, mix(white, paper1, 0.14) on a dark ground else deep1, 2.6)`,
  then ink `readable(lum(stock), accent, 3.2)`, then shadow
  `readable(ground, mix(deep1, paper1, 0.35), 1.7)`. All alpha 1.0.
- **Guards:** `"sticker32: the face draws no usable word that is not the name"`;
  `"sticker32: the phrase is too long to sticker"` when the smaller line drops
  under 40*scale. Registers `sh.mark`, not `sh.text`, so contrast is pre-resolved
  and `_enforce` never runs here.
- **Caption:** the exact phrase. **Alt text:** the offset sticker lettering.

### `neon32` — the marquee
- **Draws:** a dark ground forced regardless of theme (`invert` when the world is
  paper); two columns of seven rounded-rect perforations, each with a warm halo at
  alpha 0.10 and a solid fill at 0.95; film-gate hairlines at 0.108w and 0.892w;
  up to 2 marquee lines centred; one small tag line under them.
- **Copy:** `word`, else `line` **only if 4 words or fewer**, else the pool
  `("opening night","last call","one night only","live on stage","the main event")`
  rotated by name and tried both as written and uppercased, requiring every
  character to be drawable. Tag = `over` else `sub` else `"Coming Soon"`.
- **Budget:** 1–4 words; 2 lines maximum.
- **Sizing:** the measure narrows with the face's own density —
  `wall = clamp(1.05 - 0.45*contour_density, 0.62, 1.0)`, so a fat display gets
  0.62 of the width and a light face gets all of it. `fit_measure hi 760*scale`;
  one shared factor shrinks lines and tag together past 0.86h.
  `min_read 40*scale` lines, `20*scale` tag.
- **Colour:** dark ground is mandatory; the neon hue may adapt. Warm ink is
  `mix(glow, white, 0.35)`, glow halo `mix(warm, accent, 0.30)`.
- **Guards:** `"neon32: the face draws no usable word to light up"`.
  `min_contrast 3.0` — a tube is not body text, and the halo is doing the work.
- **Caption:** the marquee phrase. **Alt text:** the glowing tube and edge perforations.
- **Source-led HTML/CSS design:** `support-html/templates/neon32/` follows T30173_07 with two fitted script rows, the small centered `Coming Soon` line, a soft amber bloom, a dark door seam and grain, and seven glowing windows down each edge. The editor starts with the photographed warm palette and exposes the light and copy as separate controls; Skia remains the default renderer.

### `quote32` — the sign-writer's showpiece
- **Draws:** a quiet ground (`pool 0.04`); up to 3 staggered display lines in one
  ink, each with its own thin bloom; the face's own quote marks hung outside the
  first and last line.
- **Copy:** `line` then `word`, fallback `"MADE TO MATTER"`. No `over`/`sub`.
- **Budget:** 3–6 words. This is the panel where over-long copy passes validation
  and still ruins the design — see the fracs below.
- **Sizing:** line-count and stagger are a fixed table: 3 lines use widths
  (0.98, 0.62, 1.0) anchored left/right/left; 2 lines (0.86, 1.0) right/left; 1 line
  full width. Short lines are height-capped to `min(full)*(0.35+0.65*frac)`, and
  the block shrinks by `k = min(1, stage.h/total)`. `fit_measure hi 640*scale`,
  `min_read 44*scale`.
- **Colour:** flexible single-ink; each line's accent is resolved against **its own
  measured strip** at 4.5, and the bloom mixes the line ink with `glow` (dark) or
  `paper1` (light) at 0.45.
- **Guards:** `"quote32: the face draws no usable word of this line"`. Quote marks
  are dropped entirely unless the face draws `"` — a quote with no marks is a
  different, still-valid design.
- **Caption:** the quote. **Alt text:** the staggered sign-writer lettering.

### `crest32` — the open crest
- **Draws:** a flat field (`pool 0.0`); four crossed corner brackets (long arm
  0.205w / 0.30h, cross offset 46*scale, weight `max(3.0, 5.4*scale)`); a
  three-part lockup — a phrase arched up over one dominant word, a second arched
  under it. One ink.
- **Copy:** word `word`|`line` fallback `"GOOD THINGS"`; upper arch
  `line`|`over` fallback `"NEW RELEASE"`; lower arch `sub` fallback
  `"{glyphs} GLYPHS"` — **a real fact from the binary**. Arches are uppercased.
- **Budget:** one dominant word of 4–9 characters; two arches of 2–4 words.
- **Sizing:** arches are laid on a fixed 1.12 rad sweep with a chord floor forced at
  0.60w when the computed size drops under 30*scale, capped at 132*scale, tracking
  0.13*size. Word `fit_measure hi 760*scale` at 0.74w; whole stack shrinks past 0.90h.
- **Colour:** flexible flat field and ink; everything uses one `readable(ground,
  field_ink, 4.5)` resolution. Preserve the open crossed-corner frame.
- **Guards:** arches are set in the **companion face** when the family is `FLOWING`
  (script, brush, blackletter, swashy) — a swashed arch is unreadable. Errors:
  `"crest32: the face draws no dominant word"`,
  `"crest32: the face draws no usable arch phrase"`,
  `"crest32: an arch phrase is too long to stay legible"` (under 24*scale),
  and `"N.NN rad of arc will not read as lettering"`. Dropped for `sports`,
  `pixel`, `mono`.
- **Caption:** the central phrase. **Alt text:** the open crest and curved lines.

### `echo32` — the double print
- **Draws:** the same lockup twice — the whole wordmark grown to as much as 3.6x
  and bled off the sides as a flat ghost, the real lettering centred full-ink on
  top; an arched eyebrow dotted either side; two tracked small-caps lines below.
- **Copy:** wordmark `word`|`line` fallback `"TYPE IN MOTION"`; eyebrow `over`
  fallback `"JUST SET TYPE"`; first footer `sub` fallback `"DISPLAY STUDY"`;
  second footer is **hard-coded `"TYPE SPECIMEN"`**.
- **Budget:** one word, or two short ones. Five-plus words collapses the ghost.
- **Sizing:** wordmark grown to 0.92w at up to `900*scale`; the panel bails below
  `44*scale`. Eyebrow arc at 0.62 rad capped at `112*scale`, refused under
  `22*scale`. Footers `hi 34*scale lo 18` and `hi 31*scale lo 16`, tracking 0.22.
- **Colour:** the ghost is **not an alpha** — it is a flat tone mixing the
  mid-ground with ink at 0.17, which is why it stays distinct from the solid.
  The real lettering's contrast is measured *after* the ghost is painted, at 4.5;
  footers resolve the muted tone at 5.0. Keep ghost and solid wordmark distinct.
- **Guards:** `"echo32: the face draws no wordmark big enough to echo"`,
  `"echo32: the eyebrow phrase will not fit its arch"`,
  `"echo32: the lockup cannot be stood up on the sheet"`.
- **Caption:** the phrase. **Alt text:** the layered echo and small framing text.

### `contour32` — retired; historical design: the glyph as terrain
- **Draws:** one glyph dilated into 8–13 concentric stepped-tone contour bands
  (even-odd clip, so counters fill like basins), a hairline shoreline in full ink,
  a graticule of cross-rules every 168*scale, clipped at a ruled margin of 0.155h
  above the foot where two captions sit.
- **Copy:** the character comes from `word`, else the font name's initial, else the
  pool `("terrain","ridgeline","summit","elevation","highland","baseline")` — only
  its **first alphabetic drawable letter** is used. Captions are grammar-locked:
  `"{ch} surveyed — contour study"` and
  `"CONTOUR INTERVAL {step} · {n} RINGS · {EDGE(ctx)}"`.
- **Budget:** effectively one glyph; the word you supply only picks it.
- **Sizing:** `fit_measure hi 1500*scale` at 0.52w, height clamped to 0.58h; ring
  pitch scales with the face's measured stem, `(0.030 + 1.25*stem)` clamped
  0.032–0.072, ring count clamped 8–13.
- **Colour:** flexible survey-sheet palette; bands run `mix(ink, ground, 0.14)` to
  `0.84` with index contours deepened 0.13 and faded on `t**1.25`; the accent rule
  sits at alpha 0.95. Keep contours distinct from the ground.
- **Guards:** the ruled margin exists specifically so the contrast guard
  "never bites" on the terrain; captions resolve at 4.5 against measured pixels.
  Errors: `"contour32: the face draws no letter to survey"`,
  `"{ch!r} cannot be cut at any size"`,
  `"{ch!r} is too wide to stand at reading size"` (under 40*scale).
- **Caption:** the glyph. **Alt text:** the outline bands and measurement grid.

- **Source-led HTML/CSS design:** the opt-in port in
  `support-html/templates/contour32/` follows `T30930_03`: its orange frame and
  three cropped ribbons, seven cyan arrows, `9 LIGATURES` caption, and the
  source's `ADCAQO` / `STSZTTZS` glyph rows. It exposes scale, width, tracking,
  and source-palette controls. This is the source-fidelity layout; the Skia
  terrain study above remains the default until the renderer migration is
  reviewed.

### `hand32` — the thumbs-up line art
- **Draws:** a full-bleed solid ground; the supplied T33144 line-art hand at the
  source's left-edge proportions (`Box(-0.005w, 0.13h, 0.41w, 0.61h)`), beside
  three oversized words and the small note.
- **Copy: none.** The words are hard-coded `NICE / BIG / FONT` with the note
  `"Sometimes you just need a..."`.
- **Sizing:** words `hi 415*scale lo 86`, `min_read 74*scale`, tracking -0.045;
  note `hi 37 lo 24`, 2 lines, `min_read 20`.
- **Colour:** the supplied transparent hand is tinted to the **theme accent**, so
  pink is one possible colour, not a rule; ground and type ink follow the world at
  4.5.
- **Guards:** words pass `min_contrast 1.6` because they sit over linework; the
  note keeps 4.5. Errors are asset failures only:
  `"hand32: missing reference illustration …"` / `"could not decode …"`.
- **Caption:** the words. **Alt text:** the oversized outlined thumbs-up and type.

---

## Locked panels — reference-rebuilt artwork

These rebuild a specific seller reference. Preserve composition and imagery;
nothing here is theme-adaptable. Their fixed RGB is quoted so your caption is
accurate.

### `mountain32` — six numbered specimens
- **Draws:** left cream illustration panel (0.052w, 0.08h, 0.30w, 0.81h) holding the
  supplied T33631 artwork aspect-fit; right column of six numbered specimen rows at
  `y = 0.065 + i*0.145` with hairline rules between them.
- **Copy: none.** Words are hard-coded — `Diabolically, Equalizing, Revaluation,
  Pandemic, Submachine, Challenger`, numbered 01–06.
- **Sizing:** numbers `hi 23*scale lo 12`; words `hi 124*scale lo 42`,
  `min_read 35*scale`.
- **Colour: LOCKED** and it overrides the roll — deep1 `(19,20,21)`, deep2
  `(27,28,29)`, paper1 `(244,239,224)`, paper2 `(229,222,204)`, ink `(19,20,21)`,
  glow `(244,239,224)`, accent and accent2 `(181,37,45)`, mode dark. A `theme`
  authored for this panel does nothing.
- **Guards:** `"mountain32: missing reference illustration …"` /
  `"could not decode …"`. Each row's ink is resolved against the pixels behind it
  at 4.5.
- **Caption:** one visible specimen. **Alt text:** the mountain illustration and
  numbered type rows.

### `zebra32` — the paired panels
- **Draws:** a pale paper page carrying two square black poster cards built from
  halves of the plastic texture, darkened under a black veil at alpha 0.20; an
  arched zebra cutout with `LOVE` and a white rule on the left card; a rose strip
  and eight right-aligned poem lines on the right.
- **Copy: none.** `LOVE` and the poem `ROSES / ARE RED / CHOCOLATES / ARE BROWN /
  VALENTINE / IS BORED / IF YOU ARE / ALONE`, all through `clean()`.
- **Sizing:** `LOVE hi 275*scale lo 82`, `min_read 64`; poem `hi 76 lo 23`,
  `min_read 22`, leading 0.82.
- **Colour: LOCKED** paper `(239,239,237)`, black `(9,10,11)`, white `(246,243,236)`.
- **Guards:** three asset errors. The real trap is the silent one: `clean()` strips
  `€`-class characters and the poem's punctuation, and an emptied slot renders
  nothing **without an error**.
- **Caption:** `LOVE` or the poem opening. **Alt text:** both panels and their
  supplied imagery.

### `soldier32` — the archival plate
- **Draws:** a dark field with a stroked clipped-corner frame
  `(0.05w, 0.202h, 0.90w, 0.594h)` at white alpha 0.68 and interior split lines at
  x 0.47w / y 0.614h; the OpenCV-reviewed source crop in the left cell; `"1935"`
  beneath it; three centred headline lines in the right-top cell; digits and
  symbols in the right-bottom.
- **Copy: none.** The Skia composition sets `1935`; `THIS / WAR IS / USELESS`;
  `1234567890`; and `!?$€£&` through `clean()`. The HTML/CSS prototype restores
  the source's `!?$¢€£&` strip and keeps every specimen character visible with
  browser fallback glyphs when the selected face lacks coverage.
- **Sizing:** year `hi 285 lo 85`, `min_read 62`; headline `hi 164 lo 46`,
  `min_read 42`; digits `hi 86 lo 28`; symbols `hi 82 lo 27`.
- **Colour: LOCKED** dark `(7,8,9)`, white `(245,243,237)`.
- **Guards:** asset errors only; same silent-strip caveat as `zebra32`.
- **Caption:** the headline. **Alt text:** the archival group photo and centered
  type specimen.

### `mirror32` — the overprinted portrait
- **Draws:** a flat black field matching the source;
  the transparent mirror portrait at the left, 0.67h tall with its aspect
  preserved; six quotation lines right-aligned marching over the portrait at
  `y = 0.158 + i*0.116`.
- **Copy: none.** `PEOPLE HASTEN / TO JUDGE / IN ORDER / NOT TO BE / JUDGED /
  THEMSELVES`.
- **Sizing:** `hi 142*scale lo 40`, `min_read 36`, tracking -0.026.
- **Colour: LOCKED** dark `(5,6,7)`, white `(246,244,239)`.
- **Guards:** asset errors; preserve text legibility over the portrait.
- **Caption:** the quote opening. **Alt text:** the portrait and overprinted
  quotation.
- **Source-led HTML/CSS design:** `support-html/templates/mirror32/` retains the approved natural-ratio portrait, moves the shared quote edge back to the source column, and lets each line be fitted independently; the image and text stay separate so the overprint can be refined without flattening the composition.

### `brutal32` — the photo book spread
- **Draws:** a black canvas with a two-page spread inset 8.2%/8.5%, left page
  `(43,44,45)` and right `(27,28,30)`, a border stroke and centre spine; four photo
  panels cropped at hard-coded source rectangles from the contact-sheet plate, each
  stroked; four centred display lines.
- **Copy: none.** `BRUTALISM / A PLAY BETWEEN / CRUDITY / AND FINESSE`.
- **Sizing:** `hi 252*scale lo 38`, `min_read 34*scale`, tracking -0.026, 1 line
  each.
- **Colour: LOCKED** black `(5,6,7)`, white `(246,244,239)`, border `(225,225,222)`.
- **Guards:** `"brutal32: missing/decode failure for photo plate …"`.
- **Caption:** the statement. **Alt text:** the four concrete-building photos and
  overlaid lines.

### `brutalpack32` — the identity board
- **Draws:** two tall vertical paper labels (pointed-peak and arched) carrying
  rotated `BRUTALISM`; a centre arched photo card on paper with `BRUTA` / rule /
  `LISM`; a hexagonal header with a giant `B` over the transparent Potrace-extracted
  folded carton from `T13692_07-folded-package-lines.png`.
- **Copy: none.** `BRUTALISM`, `BRUTA`, `LISM`, `B`.
- **Sizing:** vertical labels `hi 175*scale lo 42`, `min_read 34`, tracking -0.035;
  `BRUTA hi 155`, `LISM hi 150`, initial `hi 224*scale lo 62`, `min_read 48`.
- **Colour: LOCKED** black `(5,6,7)`, ink `(32,32,33)`, paper `(243,242,237)`,
  edge `(210,210,207)`.
- **Guards:** plate asset error. Note the rotated labels live in a sub-sheet whose
  `verify()` results are folded back prefixed with `card/` — an overlap there is
  reported against the card, not the panel.
- **Caption:** the identity-board typography. **Alt text:** the two labels, arched
  card and package mark.

### `rio32` — the dusk travel hero
- **Draws:** a full-bleed dusk panorama darkened by a `(22,18,16)` scrim at alpha
  0.23; faux landing-page furniture in cream — brand `TYPE/STUDY`, nav
  `HOME/CATALOG/CONTACT`, hero `The Janeiro`, subtitle
  `THE WEEKEND HOLIDAY TRIP`, an outlined `BOOK NOW` button, three footer lines.
- **Copy: none.** All strings hard-coded, including the footer's holiday quotation.
- **Sizing:** `Janeiro` anchors the sheet at `hi 286*scale lo 72`, `min_read 58`,
  tracking -0.035; `The hi 132`; nav `hi 42`; footer `hi 25 lo 14`, `min_read 12`.
- **Colour: LOCKED** cream `(246,239,220)` on ink `(22,18,16)`.
- **Guards:** the scrim is the only deliberate contrast aid; type still resolves at
  4.5 against the actual photo pixels, so a bright horizon band can force a lift.
  Preserve the Rio dusk image; cream type adapts only for contrast.
- **Caption:** `The Janeiro`. **Alt text:** the dusk city hero and booking/navigation
  details.

### `boots32` — the western poster
- **Draws:** a sage ground with paper grain (`seed 24507, cell 96`); the salt-flat
  portrait across the left 40%; three coral horseshoes with five inset stars each,
  procedural, at -14°/0°/+13°; a coral-tinted transparent engraved boot bottom-right;
  title and subtitle right of the photo.
- **Copy: none.** `Wild Boots` and the smaller `photography`.
- **Sizing:** title `hi 176*scale lo 50`, `min_read 42`, tracking -0.028; subtitle
  `hi 76 lo 30`, `min_read 28`.
- **Colour: LOCKED** sage `(214,222,190)`, deep green `(27,82,44)`, coral
  `(217,101,95)`.
- **Eligibility, stated precisely:** `boots32` is **offered only when the folder
  holds at least two real sibling styles**, but the panel itself renders only the
  primary face — the two-style rule is a gate on availability, not a rendering
  requirement. Do not caption it as a family proof; `weightfamily32` and
  `mangosboard32` are the family proofs.
- **Guards:** two asset errors.
- **Caption:** keep the third word as the smaller subline. **Alt text:** the seated
  figure and coral boot/horseshoe art.

### `plakat32` — retired; historical design: the poster specimen
- **Draws:** a navy ground with grain; a top fact rail counting real glyph coverage;
  a large two-line display headline; a three-cell band — a facts column, a cyan
  tile with five enlarged cream vector symbols (loop, eight-point star, flower,
  heart, reverse loop), and a cream cell with an oversized `FORM`; two lower axis
  rails, Thin↔Black and Upright↔Italic, with cyan diamond markers at measured
  positions.
- **Copy:** one authored slot — `word` then `line`, fallback `"Plakat"`.
- **Budget:** 2–4 words. More than one word splits into two lines at `(n+1)//2`; a
  single word becomes `"{word} / STUDY"` if it is `type`, else `"{word} / FORM"`.
- **Sizing:** headline `hi 445*scale lo 68`, `min_read 46*scale`, tracking -0.045;
  `FORM hi 116`, `min_read 24`; rails `hi 25–35*scale`.
- **Colour: LOCKED** navy `(4,20,39)`, cream `(247,242,229)`, cyan `(45,190,226)`.
- **Facts:** `"{caps}/26 CAPS · {lowers}/26 LOWER"` and `"{glyphs} GLYPHS"` are
  counted live with `usable()`; the weight marker sits at
  `(weight-100)/800` clamped 0.06–0.94 and the style marker flips on
  `slant > 0.01`. The display and symbol band use most of the canvas.
- **Guards:** no asset and no panel-specific problem — only the shared fit,
  legibility and contrast rails.
- **Caption:** the display phrase. **Alt text:** the large symbol band and paired
  weight/style rows, without inventing facts.

### `plakatart32` — the macro-art specimen
- **Draws:** a near-black ground; the red/cyan macro texture cropped to
  `height*1.2` into a right-side art window; seven left-rail metadata labels in the
  companion face; one oversized display word deliberately overlapping the art's
  lower-left (the image is non-colliding by design).
- **Copy:** `word` then `line`, fallback `"Plakat"`, **one line only**.
- **Budget:** 1–2 words. Three words must still fit a single line and will shrink
  hard.
- **Sizing:** `hi 505*scale lo 95`, `min_read 82*scale`, tracking -0.035, backed by
  a black glow; labels `hi 34*scale lo 18`, `min_read 16`, tracking 0.015.
- **Colour: LOCKED** black `(3,4,5)`, cream `(246,243,233)`, cyan `(47,190,224)`.
- **Guards:** macro-texture asset error.
- **Caption:** the title. **Alt text:** the macro-art panel and overlapping wordmark.

### `mangos32` — the botanical information poster
- **Draws:** a black ground; two wordmarks with a cyan double-headed arrow between;
  an orange→black gradient strip standing in as a "variable weight ramp"; a cyan
  infinity loop; a descriptor stack and a centred botanical binomial;
  nutrition-style figure rows; a cyan circle-and-leaf fruit icon; a bottom
  `TROPICAL / 1/2 / SUBTROPICAL` row.
- **Copy: none.** `BOTANICAL`, `FIELD NOTES`, `Mangifera indica L.`, `100g`,
  `(3.53oz)`, `Energy provided`, `~ 272 kJ`, `TROPICAL`, `1/2`, `SUBTROPICAL`.
- **Sizing:** title `hi 170*scale lo 68`; botanical `hi 162 lo 49`; weight
  `hi 158 lo 65`; `min_read` from 58 down to 29; tracking -0.015 to -0.04.
- **Colour: LOCKED** black `(13,15,15)`, white `(244,244,239)`, cyan `(35,201,229)`,
  orange `(247,112,28)`.
- **The claim trap, stated plainly:** the ramp, the infinity loop and every figure
  on this panel are **decorative stock text styled after the Mangos poster. They
  are not derived from the font binary.** Never caption or alt-text this as
  evidence of a variable axis, a weight range, or any measured value.
- **Guards:** shared rails only.
- **Caption:** the large display specimen. **Alt text:** the ramp and compact data
  rows — described as artwork, not as facts.

### `alphabet32` — the character-set specimen
- **Draws:** a paper ground with two fine rules at y 0.345 and 0.695; two uppercase
  rows `ABCDEFGHIJKLM` / `NOPQRSTUVWXYZ`; a lowercase descriptor column plus two
  lowercase rows; a figures row `#0123456789`; right-hand `UPPERCASE / LOWERCASE /
  FIGURES` labels; footers `LETTERFORM STUDY` and `GLYPH SPECIMEN`. Selected glyphs
  are re-stroked in orange over the same outlines at measured advances — indices
  0 and 12 of the first upper row, 8 of the second, 0 and 11 of the lowercase rows,
  and 3 of the figures.
- **Copy: none.** Rows are the real alphabet; labels use the companion face.
- **Sizing:** upper `hi 246*scale`, lower `hi 178`, figures `hi 190`, all with `lo`
  fixed at `52*scale` and `min_read 39`; descriptors `hi 42 lo 20`; footers
  `hi 46 lo 22` and `hi 28 lo 16`.
- **Colour: LOCKED** paper `(250,249,239)`, ink `(20,20,20)`, burnt orange
  `(231,101,27)`, muted `(112,109,100)`.
- **Guards:** `clean()` drops characters the face lacks, so a face without a full
  lowercase set returns **short rows and no error**. If the coverage is thin, say
  so in the alt text rather than describing three complete groups.
- **Caption:** the alphabet specimen. **Alt text:** the three character groups and
  highlighted glyphs — as actually rendered.

### `birvase32` — the screenprint word
- **Draws:** the red/cyan print plate full-bleed, with one centred oversized
  specimen word carrying a cream halo.
- **Copy:** `word` then `line`, fallback `"Birvase"`, **hard-clipped to 2 words**
  in the panel body.
- **Sizing:** `hi 440*scale lo 90`, `min_read 72*scale`, tracking -0.04, 1 line.
- **Colour: LOCKED** to the plate; ink `(5,5,7)`, halo `(250,245,231)` at sigma
  0.035 of ink height, alpha 0.2.
- **Guards:** print-texture asset error. Preserve dark-word contrast.
- **Caption:** the visible word. **Alt text:** the single word and screenprint ground.

### `weightfamily32` — the family proof (guaranteed when eligible)
- **Draws:** a black ground divided into `len(rows)` equal rows; each row is an
  orange style label on the left, an orange rule beneath it, and two uppercase
  alphabet rows set **in that sibling's own font file**.
- **Copy: none.** The alphabet strings are fixed; the labels are the font's own
  metadata.
- **Family mechanics:** rows come from `ctx["family_samples"]`, built by
  `family_profile()` scanning the folder for real siblings matching OpenType family
  name ID 16/1, deduping format twins, and preferring a Light/Regular/Bold triplet
  when present, otherwise up to 3 real styles with upright first. Labels are
  `clean(ctx, sample["label"]).upper()` where the label is the sibling's **real
  name ID 17 style string** — never synthesised.
- **Sizing:** labels `hi 42*scale lo 18`, `min_read 17`, tracking 0.02, 2 lines;
  alphabets `hi 145*scale lo 45`, `min_read 35`, tracking -0.018.
- **Colour: LOCKED** black `(18,20,20)`, paper `(245,244,239)`, orange `(235,105,27)`.
- **Guards:** `"weightfamily32: needs at least two real styles from this family"`,
  and the panel is not offered at all below two styles. **Use it to claim a range
  only because it is real evidence — and never describe weights it does not show.**
- **Caption:** the family comparison. **Alt text:** the real style names.

### `mangosboard32` — the modular family board (guaranteed when eligible)
- **Draws:** a black ground; a top-left orange block of per-style rows (label plus
  the specimen word `TYPE` in that sibling's face); a top-right white block with an
  orange `Family` wordmark; a central dark strip carrying a glyph string; three
  bottom tiles — a cyan `Aa`, a white tile rotated -7° repeating
  `OPEN / LETTER / FORM`, and an orange tile carrying `@` or `A`.
- **Copy: none.** All strings fixed.
- **Family mechanics:** identical to `weightfamily32` — real siblings, real style
  labels, same two-style floor and the same bail message.
- **Sizing:** style labels `hi 28 lo 14`; specimen `hi 72 lo 28`, `min_read 26`;
  `Family hi 190 lo 50`, `min_read 42`; glyph strip `hi 214 lo 48`, `min_read 36`;
  `Aa hi 245 lo 62`, `min_read 44`; repeats `hi 95 lo 32`; symbol `hi 235 lo 58`.
- **Colour: LOCKED** black `(13,15,15)`, white `(245,245,239)`, orange `(247,111,26)`,
  cyan `(24,190,224)`; strip `(31,33,33)` bordered `(174,178,176)` at alpha 0.8.
- **Guards:** the central strip is `C€Ω½?†qTTD0123456789` filtered **per character**
  through `usable()`, falling back to plain A–Z. Specials legitimately vanish on a
  sparse face — the strip is then honest but shorter. Preserve the modular blocks.
- **Caption:** the family comparison. **Alt text:** the central glyph strip and lower
  specimens.

## Reference-remake slots (44)

Slots **27–70**, with **43 active remakes** and slot 43 reserved for the withdrawn
`bondibeach32`. Their stable IDs remain in `SUPPORT_ORDER`; the renderer filters
retired names before listing or selecting layouts. Active layouts live in five
modules under `bin/pin-studio/support_templates/`. Per-reference
source mapping is in [REMAKE-MAP.md](REMAKE-MAP.md) and material provenance in
`SOURCES.md` — this section is the *operating* reference: what each panel draws, how
much copy it can wear, what size it ends up at, and what it forbids.

**None of the 43 active remakes is a type claim.** A remake panel is a composition that happens
to be set in the buyer's face. The only things that vary between fonts are (a) the
letterforms, (b) the palette where the module reads `ctx["pal"]`, and (c) the theme
grain seed. Everything else — ground colours, block positions, alphas, rules — is
fixed by the module. "Premium" here means *the composition never adapts; the type
fits into it*, so a face that cannot fit is a bad derivation, not a layout problem.

### The machinery the 26 originals do not share

| module | slots | local helper | default `lo` | default `min_read` | default `min_contrast` | palette use |
|---|---|---|---|---|---|---|
| `t30332.py` | 27–35 | `_text(…, hi, …)` | `max(14, hi*0.28)` | `hi*0.24` | 4.5 | flexible ground, fixed scene |
| `fashion.py` | 36–43 | `text(…, hi=120, lo=22, …)` | `22` | `18` | 4.5 | house red nudged 7% to `accent` |
| `poster.py` | 44–49 | `text(…, size, …)` | `max(8, 12)` | `18` | 4.5 | grounds mixed 3–8% toward palette |
| `photo.py` | 50–56 | calls `sh.text` directly | given per call | given per call | renderer default | photo ground + one `theme_ink` element |
| `objects.py` | 57–70 | `type(…, size=120, …)` | `max(8, 12)` | `18` | **3.2** | **LOCKED — never reads `ctx["pal"]`** |

All numbers are pre-`sh.scale`. Do not read one module's defaults as another's: an
`t30332` label with `min_read 13` and a `photo` label with `min_read=13 * sh.scale`
are the same floor, but `objects` will let 12px ink through on a busy ground where
`poster` would not, because its contrast contract is 3.2 not 4.5.

Three facts that apply to every active remake:

* **Every visible string is scrubbed centrally.** `render()` sets `sh._support_ctx`
  for any name in `SUPPORT_ORDER`, and `Sheet.text` then runs *every* string —
  including fixed furniture — through `support_render_copy()`: `clean()` first, then
  if the whitespace-normalised result equals the font's name (token run, case- and
  punctuation-insensitive) or a `SUPPORT_STOCK_COPY` phrase, it is replaced by the
  first usable of `TYPE / FORM / PRINT / GLYPH / LETTERS`. So `focusposter32`'s
  `FOCUS`, `wideclaim32`'s `WIDE`/`SERIF`, `voguecover32`'s `STYLE`,
  `strongweak32`'s `STRONGEST`/`WEAKEST`, `blossom32`'s `BLOOM INTO CALM` and
  `greetingsgrid32`'s six tiles are all replaceable in that rare collision. The box
  stays alive; the word changes. **Caption the file, not the panel spec.**
* **`t30332` scrubs twice**, once per line inside `_text()` and again in `Sheet.text`.
  Its reason is line breaks: `Sheet.text` normalises whitespace across the whole
  string, so a stacked fixed label (`OPEN\nAIR\nBLOOMS`) is checked as three lines
  *and* as one phrase.
* **Material-led panels need supplied artwork**, and the failure mode differs by
  module. Every one of them appends to `sh.problems` first (`_load_image()` in
  `t30332`, `image()` in `fashion`/`objects`, `image()`/`image_background()` in
  `photo`), which means a non-zero exit and no shipped set. **Seven** of them then draw
  *nothing* and `return` at once: `amberdawn32`, `skinbadge32`, `latestlook32`,
  `gelatocards32`, `meditation32`, `ovalword32` and `cliffpostcard32`. The rest degrade
  into a half-composition that still passes the geometry checks — `stardust32` silently
  substitutes a grey `_backdrop`, `lemonade32` loses its glass, `ravencover32` the whole
  tailoring photograph behind its cover type. Never "rescue" such a panel by re-drawing it
  without the material; fix the folder. The renderer currently references **30** materials
  under `support-references/materials/`, and all are present.

  Every count in this section is re-derivable, so do not trust the prose over the code:

  ```bash
  python3 bin/check_support_catalogue_facts.py
  ```

  It prints, per remake panel, whether it reads authored copy, whether it bails on a
  missing material, and whether it reads the theme palette, plus the catalogue counts
  and any missing material. Run it before you report a guide number as a defect.

**Eligibility audit.** The previous broad class gate was replaced by the six-style
matrix in `SUPPORT_STYLE_EXCLUDE`. The complete per-class pairings and the exact
hard-exclusion lists are maintained with the dated paired sheets at
[`class-audit-2026-10-14/README.md`](class-audit-2026-10-14/README.md). Do not add
another class exclusion from a single representative font: keep the test evidence
and conditional pool available for seller review.

### One measured sweep of the catalogue (script class, 2400×1600, `sh.scale = 1.6`)

`bin/pin-studio/.venv/bin/python bin/pin-studio/pin_studio.py --supports
--support-count 999 --json …` on a wide script face: **67 panels**, because the three
multi-style proofs (`boots32`, `weightfamily32`, `mangosboard32`) decline a
single-style face exactly as `SUPPORT_MIN_STYLES` says they should. Read these numbers
as *the catalogue's behaviour at a moment in time* — they are the cheapest way to tell
whether a later change moved it:

* A previous full-catalogue sweep reported `OFF-CANVAS` on marks registered
  `collide=False` **without** `bleed=True`: `typewall32` (its rows intentionally start
  at `x −0.04w`) and `blossom32`. `ravencover32` and `blossom32` now mark their
  intentional full-bleed artwork correctly; only `typewall32` remains on that old list.
  Rerun the catalogue before treating the old error count as current. The panels that
  failed this class earlier — `cliffpostcard32`,
  `ovalword32` — have since been rebuilt on supplied clean plates marked `bleed=True`,
  which is the fix, not a re-tuned box. Rerun the catalogue before treating its
  historical error count as current. Judge a delivery by its 12 selected designs,
  not by that historical sweep.
* **`hi` is reached, not assumed, and a wide face spends it unevenly.** Short fixed
  strings land on `hi × 1.6`: `yearposter32` 784, `signalclock32` 624, `glyphsheet32`
  208 ×3, `greetingsgrid32` 165 in all six tiles. Longer ones do not: `wideclaim32`
  570/497, `stardust32` 330 under `hi 300`, `colosseum32` 229/229/171 (the third word is
  the longest), `ovalword32` 356 for its one-word medallion. The split-lockup panels
  are the cautionary ones — `stadiumposter32` came out **258 / 397** and `strongweak32`
  **317 / 422**, so the two halves of a "matched pair" are set at visibly different
  sizes. `phonegarden32` has three independent source lockups (four-line, rotated
  two-word, and editorial phrase); compare all three screens against the source.
* **28 `ink lifted` notes**, and they are not scattered: 25 in the remakes against 3 in
  the originals, and `objects.py` alone accounts for 10 of the 25 (6 of them in
  `greetingsgrid32`) — the densest cluster in the catalogue, which is what a 3.2 contract
  on flat saturated grounds looks like. The worst starting points are
  `sunkiss32` title and badge `1.3:1 → 3.2:1`, and `brutalpack32`'s two vertical
  cards `1.3:1 → 4.6:1`. Those are
  **the guard working as designed**, not a fault — but a lift that starts near 1:1 is
  also the signal that a locked ground/ink pair was never high-contrast, so look at
  those files.
* **A slot's `size` is not proof that its string rendered.** `greet4` (`Привет!`)
  reports `165` on one line for a face that draws only the `!`. `--json` tells you how
  big, never how much; only the PNG or
  `bin/check_support_glyph_coverage.py` tells you whether the tile is whole.

### `t30332.py` — slots 27–35

Most grounds come from `_backdrop()`: fixed top/bottom colours, an optional `light_pool`
of `P["accent"]` at `(0.73w, 0.18h)` radius `0.82h`, and `speckle` seeded from
`ctx["th"]["seed"]` at alpha `0.065`. So the *world* shows up as a faint rim glow and
grain colour only — never as the panel's declared colour. `ovalword32`,
`kindersea32` and `messageframe32` instead use cleaned source plates to retain
their distinct reference stock textures; `kindersea32` also overlays its
source-extracted image and sparkles as separate layers.

* **`ovalword32` (27)** — **Draws:** cleaned reference background, source-matched
  white oval with a near-black `4*scale` outline, and a generic single-word specimen.
  **Copy:** `oval_word` = `panel_text` from
  `daydream / sunbeam / harmony / tender`; `oval_meta` "TYPE STUDY" and
  `oval_caption` "DISPLAY / LETTERFORMS" are fixed. **Budget:** 1 word, **1 line**.
  **Sizing:** `hi 430`, `min_read 100`, track −0.025; labels `hi 36/42`,
  `min_read 21/24`. **Colour:**
  labels use `P["ink"]`, centre is fixed `(16,17,21)`. **Caption:** the centred
  phrase in an oval medallion; do not call the ground "clay" or "sage".
* **`stardust32` (28)** — **Draws:** full-bleed monochrome portrait with a 24%
  near-black veil, the reference's `STARDUST / AND STORIES / STUDIO` stack, four
  pixel-cross sparkles, and a 12×2 checker strip. **Copy:** eyebrow = `lead_in`
  uppercased; the fixed phrase is generic and never repeats the font name. **Sizing:**
  headline `hi 300`, `min_read 82`, track −0.015; eyebrow/footer `hi 33/26`.
  **Colour:** white typography with fixed source-yellow sparkles on the grayscale
  plate. **Alt text:** oversized three-line white display over a dark portrait.
* **`cliffpostcard32` (29)** — **Draws:** the supplied
  `T30332_02-clean-postcard-background.png` plate full-bleed (marked `bleed=True`, so it
  is allowed to reach the edge), the headline split into two single-line locks, and two
  fixed footers. **Copy: none** — `cliff_headline_1` `Wander where` and
  `cliff_headline_2` `your soul feels wild.` are literals; authored `line`/`word` never
  reach this panel. **Budget:** 3 words + 3 words, one line each. **Sizing:** both lines
  `hi 235`, `min_read 68`, track −0.02; footers `hi 24`, `min_read 15`. **Colour:**
  headline ink fixed at `(12,15,18)`, footers at `(24,31,33)` — the theme cannot move
  them, so describe the ink. **Guard:** the panel `return`s when the plate is missing, so
  a broken `materials/` folder costs it entirely.
* **`kindersea32` (30)** — **Draws:** the source-text-cleaned lavender plate,
  with its exact pixel sea crop and two original transparent sparkles overlaid.
  Generic `FIELD NOTES` and vertical `POSTCARD` replace source branding/name.
  **Copy:** two fixed one-line locks, `I WISH YOU` and `a KINDER SEA.` **Sizing:**
  both `hi 225`, `min_read 68`, track −0.012. **Colour:** source violet stock and
  white type; the contrast floor is intentionally 2.5 to preserve the reference's
  white-on-lavender treatment. **Guard:** returns if any of the three source
  materials is missing.
* **`messageframe32` (31)** — **Draws:** the source-text-cleaned lavender stock,
  retaining its exact white framed card, dot fields, pinheads, hearts, stars, corner
  blocks and globe. **Copy:** four fixed single-line messages — `You Will Look Back`,
  `On These Days And`, `Be So Grateful You`, `Made It Through`; generic `FIELD NOTES`
  and `A NOTE TO KEEP` replace the source brand/font name. **Sizing:** each line has
  its own box, `hi 138`, `min_read 58`; preserve the four-line stack and its even scale.
  **Colour:** near-black type on the source white panel. **Guard:** returns if the
  cleaned source plate is missing.
* **`contactlist32` (32)** — **Draws:** a text-free, image-model-cleaned backing
  plate composition-matched to the source: white board, navy frame, pastel gradient
  card, three tabs, seven pink nodes, and two footer plates. **Copy:** the eight source
  track titles (`01.Misread` through `the Westhill`) plus generic `TRACK LIST` / `NO. 07`
  footer labels; no font name. **Sizing:** each title is one line at `hi 82`,
  `min_read 36`, track −0.012. **Colour:** locked navy type over the source-matched
  pastel plate. **Caption:** describe a numbered track list, never imply eight styles
  or weights.
* **`sunsetpromise32` (33)** — **Draws:** the text-free generated lavender/floral
  reference plate, with the exact source pixel-sunset crop overlaid at upper left,
  plus the source globe, pixel marks, and corner stars. **Copy:** four fixed title-case
  lines — `Every`, `Sunset Brings`, `the Promise of`, `a New Day`; `FIELD NOTES` and
  `DUSK / 07` replace the source branding/font name. **Sizing:** each line is one
  outlined display slot, `hi 170`, `min_read 52`; white fill with a dark `1*scale`
  stroke. **Colour:** locked source lavender/pink with white outlined type. **Caption:**
  describe the four-line sunset message and framed pixel-art scene, not the font name.
* **`phonegarden32` (34)** — **Draws:** a text-free three-phone reference plate with
  the exact source peony overlaid on the lower-left screen; the plate retains the yellow
  field, black phone shells, cream screens, app chrome, other flowers, and sparkles.
  **Copy:** left `CON / VENT / GARD / EN` plus `CONVENT / GARDEN`; center `CONVENT` and
  `GARDEN` rotated bottom-to-top; right `CONVENT / GARDEN` and `Timeless / Charm, /
  Rooted in / Grace.`. `FIELD NOTES` and `FLORA / 08` replace the vertical foundry/font
  labels. **Sizing:** left display rows `hi 94` and `hi 57`; center columns fit a
  `0.69h` vertical run; right headings `hi 48`, message rows `hi 52`. **Colour: LOCKED**
  dark ink on yellow/cream. **Guard:** preserve the three distinct reference lockups;
  never repeat the font name.
* **`pixelquote32` (35)** — **Draws:** black field `(4,4,6)` with the source's exact
  transparent pink corner stitches, heart, and pixel mascot. **Copy:** five fixed
  lines, `A Little / Nonsense / Now & Then / is Relished by / the Wisest Man`; no
  font-name label. **Sizing:** `hi 250`, `min_read 52`, track −0.018. **Colour:
  LOCKED** `(244,76,157)` on black — **the theme is invisible here**; caption it as
  "hot pink on black", never as a world.

### `fashion.py` — slots 36–43

One shared house palette: `PAPER (249,247,241)`, `INK (17,17,18)`, `RED (222,9,28)`,
`WHITE`, `GREY (91,88,84)`. `colors(ctx)` returns
`readable(lum(PAPER), mix(RED, pal["accent"], .07), 3.0)` — i.e. **7% of the theme
accent folded into the house red, floored at 3.0 contrast against ivory**. That is the
whole extent of theme participation in this module. Every value also passes
`support_copy(ctx, (), value)`, so a fixed string that collides with the font name
rolls to `TYPE`/`FORM`/… before `text()` even sees it; an empty result returns `None`
and the slot silently disappears.

* **`ravencover32` (36)** — **Draws:** full-bleed clean red-tailoring photo under a
  subtle 20% `(16,10,12)` veil; fine ivory top/bottom rules, a small outlined oval
  kicker, and the large cream headline remain directly over the photograph, as in the
  source. **Copy:** all fixed (`CITY EDITION / NO. 06`, `AFTER HOURS`, `MODERN FORM /
  TIMELESS DETAIL`, `TAILORING / TEXTURE / NIGHT`); the font name is omitted.
  **Sizing:** title `hi 330`, one line, `min_read 68`; small oval labels at `hi 20/18`.
  **Colour:** ivory on the darkened photo; theme-independent. **Guard:** the full-bleed
  photo and veil register `bleed=True`; the headline sits over the figure intentionally.
* **`voguecover32` (37, retired)** — **Draws:** ivory paper, contained transparent face
  cutout right of centre, hairline at `0.075h`, a red keyline under the masthead.
  **Copy:** masthead `STYLE` fixed; headline `A STUDY IN SILHOUETTE` fixed;
  `cover_note` = `rolled` from three editorial phrases (the only rotating copy here).
  **Sizing:** masthead `hi 300 lo 120`, `min_read 88`, track −0.045 — a **very long
  ascenderless masthead word is what this panel wants**; a script face will shrink it
  and lose the cover. **Colour:** masthead in the nudged red, headline `INK`.
  The opt-in HTML/CSS editor restores the stacked issue label, three-line left story,
  lower editorial block, and right-hand feature deck as individually editable layers.
* **`confident32` (38, retired)** — **Draws:** paper, a transparent eye-illustration crop with
  the tiny source-font imprint removed, centre-covering the lower 46%, and three rules.
  **Copy:** `confident_word` = `panel_text` from `STAND TALL /
  LOOK AHEAD / OWN YOUR SPACE / KEEP YOUR LINE`; overline/sub/caption fixed.
  **Budget:** 2 words, **1 line** — a third word is what triggers the block shrink.
  **Sizing:** `hi 330 lo 85`, `min_read 68`, track −0.04. **Wears:** best on a bold
  display face with short words; weakest on ultra-condensed.
* **`storyteller32` (39)** — **Draws:** paper, artist illustration contained in a
  right column, a hands strip, a red vertical rule at `0.635w` dividing text from art.
  **Copy:** `story_body` = `support_copy(("line","sub"))` — **the only fashion panel
  that puts authored copy into a body slot**, `max_lines 3` at `hi 34 lo 18`,
  `min_read 16`, leading .92; kicker/headline/signature fixed
  (`TYPE TELLS\nA STORY`, 2 lines at `hi 190`). **Budget:** ~12–16 words of body,
  sentence-case; do not send an all-caps line here, it will not match the case of the
  fixed headline. **Colour:** kicker and signature in nudged red, body `INK`.
* **`focusposter32` (40)** — **Draws:** a high-key soft-focus monochrome portrait
  background, the exact red-framed eye-study crop at source proportions near the upper
  left-centre, and rules at `0.35h` and `0.89h`. **Copy:** `focus_title` =
  `support_copy(("word",), "FOCUSED")` — **a single word, set enormous**;
  `focus_phrase` = `support_copy(("line","sub"))` in up to 2 lines; three side labels
  are fixed. **Material:** the generated backdrop is text-free; the framed eye remains
  the exact source crop.
  **Sizing:** `hi 420 lo 105`, `min_read 84`, track −0.045 — the highest display
  ceiling in the fashion module. **Best use:** this is the panel to *sell the word-shape
  of one strong word*; it is also the panel most likely to be replaced by `TYPE` if the
  font is named "Focus".
* **`wideclaim32` (41)** — **Draws:** pure type on paper, one rule, no artwork.
  **Copy: fixed** — `WIDE` at `hi 650 lo 150`, `min_read 126`, track −0.055 and
  `SERIF` at `hi 520 lo 125`, `min_read 105`; kicker/footer fixed. **Guard:** the words
  are **never** true of the showcased face, and neither is the panel eligible to be
  described as a metric proof. `SERIF` on a sans face is a *composition* claim, not a
  font claim: caption "two oversized specimen words in red and black", and Part 4 rule 5
  forbids writing "a wide serif".
* **`blossom32` (42)** — **Draws:** the restored straight red field over the left 62%
  (white `light_pool` at strength .11), the contained blossom illustration on the
  right, and a stroked pill. **Copy:** fixed `BLOOM` and `INTO CALM` on two separately
  measured rows (`hi 180`, `min_read 40`); `blossom_body` =
  `support_copy(("line","sub"))`, up to 3 lines `hi 31`, `min_read 15`, leading .95;
  button fixed. **Colour:** white on red at `min_contrast 3.0`. **Guard:** the pill is
  `collide=False`; its label may not spill. Slot 43 remains reserved for the withdrawn
  `bondibeach32` and is not active.

### `poster.py` — slots 44–49

No local name scrub: `text()` takes `size` (not `hi`) and passes
`lo = max(8, 12*scale)`, `min_read*sh.scale`, `min_contrast 4.5`, `leading .84`.
Grounds are the reference colour **mixed 3–8% toward a palette key**
(`P["accent"]`, `P["accent2"]`, `P["deep1/2"]`), so the world is a whisper; glows in
`electromagnetic32`/`demolition32` take `mix(..., P["accent"], .06)` and
`P["accent2"]` outright. Empty `wording` returns without drawing (no `None` slot).

* **`neue32` (44)** — **Draws:** pink field, three translucent rounded rows, three
  signal pills (one `INK`, two coral), meta/footer rules absent. **Copy:** one word
  from `support_copy(("word",), "FRESH")`, **rendered six times** — 3 rows at
  `hi 235` (`min_read 82`, track −0.035) and 3 pills at `size 27` (`min_read 13`).
  **Budget:** 1 word, ≤7 characters before the pills start shrinking independently of
  the rows. **Colour:** black/pink/coral, coral is `mix((245,63,76), accent, .08)`.
* **`electromagnetic32` (45)** — **Draws:** dark ground `(14,15,21)`, a violet
  `light_pool` at `0.28w` and an acid-green one at `0.76w`, 1400 speckles, an orbiting
  beacon replacing the source's globe. **Copy:** `em_word` =
  `support_copy(("word","line"))`, default `ELECTRIC DREAMS`. **Budget:** 4 lines,
  left-aligned — **2–4 words is the sweet spot**; a single long word leaves the
  left-aligned field looking under-filled. **Sizing:** `size 156`, `min_read 42`,
  leading .92. **Wears:** midnight/graphite/asphalt; on `bone`/`vellum` the glows are
  the only theme signal.
* **`demolition32` (46)** — **Draws:** dark violet ground mixed with `deep1/2`, orange
  and violet pools, 1900 warm speckles, a 16-point vector impact star. **Copy:**
  `demo_title` = `support_copy(("word","line"))`, default `BREAK THE PATTERN`.
  **Budget:** 4 lines left-aligned, 2–5 words. **Sizing:** `size 172`, `min_read 40`,
  track −0.015, leading .91. **Guard:** the star marks `impact_burst`
  `collide=False` and sits at `0.83w/0.82h` — a 4-line block that reaches `0.75h` is
  the practical limit.
  The opt-in HTML/CSS editor uses T19827_06's supplied color-field texture and
  gives each source display row its own fitted box, avoiding the Skia line collisions.
* **`yearposter32` (47)** — **Draws:** red ground mixed 3.5% toward accent/accent2,
  6200 dark speckles for wear, one light rule at `0.83h`, two footer labels. **Copy:**
  `year_title` = `support_copy(("word",), "1982")` — **a single "word", set at
  `size 810` with `min_read 160` and track −0.055**, i.e. the largest request in the
  whole catalogue. **Budget:** 4–6 characters. A 12-character word still renders, at
  roughly a quarter of the intended scale, and the panel stops reading monumental —
  this is the panel to *not* choose when the incoming word is long. **Caption:** say
  what rendered; if the word is a text word rather than a date, do not call it a year.
  The opt-in HTML/CSS renderer preserves unavailable year digits in a readable
  browser fallback and reports the selected face's missing characters.
* **`stadiumposter32` (48)** — **Draws:** red ground, seven ghosted grandstand tiers
  (rules + 18 dots each), rules at `0.79h`. **Copy: the only self-reflowing remake.**
  `support_copy(("line","word"), "NORTH STAND")` is split
  `split_at = max(1, (len+1)//2)` into two lines, with `STAND` forced as the second
  line if the split leaves one word. **Budget:** exactly 2 lines, one word-ish block
  each; **3–4 words is ideal, 1 word produces a doubled layout, 7+ words crushes both
  blocks toward `min_read 80`**. **Sizing:** `size 410` each, track −0.06. **Wears:**
  sports/condensed display; the class `sports` gets this panel and it is the one
  built for it.
* **`signalclock32` (49)** — **Draws:** near-black ground `(9,10,12)`, 950 speckles,
  a chamfered red plaque, a rule at `0.84h`. **Copy:** `signal_value` =
  `support_copy(("word",), "$50.50")`, `size 390`, `min_read 74`, track −0.055, in a
  box only `0.66w` wide. **Budget:** a short numeric-ish token. **Guard:** the plaque
  is hard-labelled **`DOLLAR`** and the panel is composed as a price — with a
  non-numeric word the two stop agreeing. Caption the glyphs, not the currency.
  The HTML/CSS editor exposes source-width fitting and preserves unsupported price
  glyphs in a readable browser fallback instead of removing them.

### `photo.py` — slots 50–56

These call `sh.text` directly with `* sh.scale` on every number, so their contracts
are written out in full per slot. Shared helper `theme_ink(ctx, ground_rgb)` =
`readable(lum(ground_rgb), ctx["pal"]["accent"], 4.5)` and is used on **exactly one
element per panel** (a rule, a badge outline, a keyline) — the photographs stay the
photographs. All seven are full-bleed or inset photographs from `materials/`, and
**all seven return early with a recorded problem if the material is missing.** Every
`sh.text` string here is scrubbed by `Sheet.text`, but note that `glow=` and `grad=`
are used (no other remake module uses them).

* **`amberdawn32` (50)** — **Draws:** full-bleed amber glass-block fashion photo under
  a 4.5% dark veil, a partial lemon ring with curved lettering and an `Aa / GLYPHS`
  sample. **Copy:** fixed `Golden / Hour`; `amber_caption` =
  `support_copy(("sub",), "LETTERFORM / EDITORIAL STUDY")` — **one of only three
  panels that consume `sub`**. **Sizing:** headline `hi 400 lo 94`, 2 lines,
  `min_read 64`, track −0.035, leading .84; badge sample `hi 53`, caption `hi 35`.
  **Colour:** fixed lemon `(255,229,28)`; the theme appears in one rule under the
  headline.
* **`skinbadge32` (51)** — **Draws:** a text-free reconstruction of the source's warm
  hair-and-skin photo behind overlapping lavender `(184,155,249)` and brown `(96,42,24)`
  seals. The right seal clips five large `Tribe Tribe` rows; the left carries curved
  rim copy, two side stars, a `Skin / Tribe` headline, and a white hand-drawn underline.
  **Sizing:** repeat rows `hi 190 lo 72`; the headline words are separate one-line slots
  up to `hi 280`, so script faces keep their stack.
* **`latestlook32` (52)** — **Draws:** a one-pass text-free rebuild of the red-blazer
  photograph full-bleed, with the model at left and architecture open at right.
  **Copy:** three independently measured white rows, `Get The / Latest / Style`, plus
  a split footer (`DISPLAY LETTERING` / `AUTUMN LOOKBOOK`). **Sizing:** rows `hi 312`,
  one line each, `min_read 56`; a thin center rule separates the footer.
* **`gelatocards32` (53)** — **Draws:** dessert-shop photo under a 10% milky wash, a
  supplied blue ice-cream pattern clipped into the rear cobalt card and the supplied
  crimson pattern softened to pink in the foreground card (both `radius 24*scale`),
  plus offset shadow rects. **Copy:** fixed `SWEET SCOOPS` on both cards,
  stacked on the front card. **Sizing:** front headline `hi 198 lo 60`, up to 3 lines,
  `min_read 40`, leading .83; back phrase `hi 105 lo 34`. **Guard:** the back card's
  slots sit in the strip exposed to the
  right of the front card (`exposed_x = front.r + 18*scale`, `exposed_w` floored at
  120px) — a wide face shrinks `SCOOP / SHOP` there first.
* **`meditation32` (54)** — **Draws:** pink→mint `gradient_fill`, 86 wavy white
  strokes, a screen `light_pool`, a **cropped inset photo `(0,0,949,261)`** with a
  white keyline, a 17-point magenta `PAUSE / RESET` starburst badge, and a 72%-alpha
  `MINDFUL WORKSHOP` pill. **Copy:** fixed `STILLNESS` headline and fixed labels.
  **Sizing:** headline `hi 320 lo 76`, one line, `min_read 50`. **Wears:**
  sage/moss/bone/vellum; a violet or ember world still
  produces this pink-mint ground — **never caption it as the theme**.
* **`strongweak32` (55)** — **Draws:** orange field, a pink rounded mat with 19+11
  scalloped circles, a cobalt card, two 12-point sticker bursts. **Copy: hard-coded**
  `STRONGEST` (`hi 310 lo 88`) and `WEAKEST` (`hi 330 lo 88`), both 1 line,
  `min_read 52`, with `glow=((7,44,94), .018, .42)`; kicker = `lead_in`; two burst
  labels fixed. **Guard:** the two words sit in **one column, two boxes** — they are
  *not* two weights, and this is the panel most likely to be mis-captioned as a
  weight comparison. Part 4 rule 5 applies: it carries no type evidence.
  **Sizing:** both at ~300–330 pre-scale is the reference look; a very wide face will
  drop one of them toward 88 and the pair will visibly stop matching.
* **`funkyfashion32` (56)** — **Draws:** pink field, the source's 5×5 annotation dots
  and pointer, a **rounded-clipped transparent portrait** over an orange oval, and
  the source smiley sticker. **Copy:** fixed `FUNKY / FASHION` in two independently
  measured one-line display slots (`hi 260 lo 62`, `min_read 40`); `FASHION / WEEK`,
  the three-line body, caption, and rule are fixed. **Colour:** cream headline and
  labels over pink, with the source orange portrait surround.

### `objects.py` — slots 57–70

**The locked module.** No panel in it reads `ctx["pal"]` at all (verified file-wide),
so `theme` in a brief changes nothing on slots 57–70 and the caption must name the
actual inks. `type()`'s contrast contract is `min_contrast=3.2` — the loosest in the
codebase — because these are flat, saturated, self-lit grounds. Word counts are
hard-coded: **this module has no copy inlet whatsoever** (except `roadrunner32`/
`freakscene32` being checked below), so authored copy is silently ignored 14 times
over. It does have a real hazard: fixed strings with non-Latin letters and symbols
that most faces do not draw (see 1.6 and `bin/check_support_glyph_coverage.py`).

* **`dreamchalk32` (57)** — dark-green chalkboard, a mint chalk circle stroke, vector
  crown, dry chalk speckle (3600), four 4-point stars, a rule. `DARE TO` at `size 118`
  (`min_read 40`), `DREAM` at `size 260` (`min_read 82`) in fixed yellow `(250,217,90)`,
  footer `GIVE YOUR IDEAS ROOM TO GROW` at 23. **Budget:** two words + one word.
* **`lovecard32` (58)** — green ground, 16 quad-curve leaves, a `radius 16` ivory card,
  three 5-point hearts. `WE LOVE\nGOOD TYPE` at `size 148`, **2 lines**,
  `min_read 42`, leading .87, in fixed red `(215,44,60)`. **Budget:** 4 words in 2
  lines, hard-coded — a face with tall descenders will crowd the hearts.
* **`queens32` (59)** — near-black ground, double teal roundel, crown, rule, two
  4-point stars. `QUEENS` at `size 270` (`min_read 76`), kicker at 35, footer
  `OWN THE ROOM` at 37. **Best for** a high-contrast display face: the roundel is
  sized to a 6-letter word, and longer strings shrink toward 76.
* **`lemonade32` (60)** — cream ground, a `radius 18` speech bubble keyed in ink,
  **and the one supplied line-art glass** (`materials/T26003_01_lemonade-line-art.png`,
  contain-fit). `MADE WITH\nREAL LEMONS` at 62 in the bubble (2 lines),
  `SUNSHINE\nIN A GLASS` at 75 (2 lines, `min_read 32`), footer at 19. **Budget:** 3
  words in the title, 4 in the bubble; the title box is `0.51w` on the *left* half, so
  a long word collapses it to the floor while the glass stays large.
* **`sunkiss32` (61)** — marigold ground, ink card frame, concentric sun rings, a
  `FRESH PRESS` badge. `SUNKISS` is set **twice**: `size 280` cream at `.38h` over
  `size 268` ink at `.405h` — **the offset-outline echo**, one of only two panels that
  draw the same word twice for effect (the other is `neue32`'s six-up). A wide face
  breaks the registration between the two passes; check the pair visually.
* **`typewall32` (62)** — yellow ground, **7 rows of a 10-word Title Case list**
  (`Classic, Cult, Sunshine, Electric, Good Times, Sunday, Wonder, Forever, Louder,
  Lovely`) alternating `size 140`/`120`, boxes overhanging both edges
  (`x −0.04w`, `w 1.08w`) with a left/centre alignment flip, one fine side rule.
  **Budget:** nothing is authored; the row count is fixed. `min_read 35`. **Guard:**
  this is typographic *wallpaper*, not a specimen — `VERIFY` will not complain, but a
  very wide face makes rows 3 and 5 shrink unevenly and the rhythm reads broken.
* **`manualbrew32` (63)** — dark ground, six fixed chromatic chips as a colour key.
  `MANUAL` (`size 265`, pink) over `BREW` (`size 260`, cyan), both `min_read 66/68`,
  track ≈ −0.045/−0.04; note line at 21. **Budget:** 2 words total. **Wears:** rounded
  or quirky text faces; the two colours are fixed and *not* the theme's.
* **`pastpresent32` (64)** — pink **gingham** built from `cell = sh.w/16` squares,
  three cream frames with a second inner keyline and mirrored 8-point rosettes.
  `PAST / PRESENT / FUTURE` one per frame at `size 92` (`min_read 32`), footer 19.
  **Budget:** 3 fixed words. **Caption:** a three-step timeline; it is **not** a
  weight or style ramp and carries no family evidence.
* **`herbalproduct32` (65)** — vivid green ground around a double-keylined cream
  label; an orange twelve-ray `NEW` burst overlaps the top-left corner. Hand-drawn
  botanical sprigs flank the `1969` batch oval above the bold `HERBALS` title. The
  outlined `Arabica Whole Beans Coffee` line sits over three compact process, roast,
  and date columns. The source display word is `HERBALS` at `size 205` (`min_read
  64`); two fixed labels. **Budget:** 1 word. A wide face eats the card padding
  first — the box is `0.92` of the card width.
* **`colosseum32` (66)** — cream paper, three words in navy/red/navy at `size 143`
  (`min_read 42`, track −0.03), hairlines between them, a meta line at 18. **Fixed
  lowercase** `colosseum / circulation / antipodes`. **Coverage hazard:** the
  lowercase-only requirement plus the long words make this the panel most likely to
  render short on a caps-only or narrow-advance face — run the coverage validator, and
  caption the words that actually appear.
* **`glyphsheet32` (67)** — green ground, `FIGURES / SIGNS` head, three rule-separated
  rows at `size 130` (`min_read 36`, track −0.035) each with a 19px label:
  `0123456789`, `$&%!?@#`, `()[]{}+−=` (**U+2212 minus sign**). **Budget:** none, all
  fixed. **Coverage hazard:** measured **11/27** binaries in the current folder lose
  `−`, and the row silently shortens with a clean exit — this panel is the reason
  `bin/check_support_glyph_coverage.py` exists.
* **`freakscene32` (68)** — hot-pink ground with a 5px yellow stroke frame and two
  yellow ringed stars. `FREAK\nSCENE` at `size 340`, **2 lines**, `min_read 80`,
  track −0.055, leading .81; kicker 23, footer 20. **Budget:** 2 words. **Guard:** the
  stroke frame is `radius 0`, so a face with wide bolds will shrink toward 80 before
  it breaches the frame.
* **`greetingsgrid32` (69)** — six flat colour tiles in a 3×2 grid (gutter
  `0.012w`), each tile a word at `size 103` (`min_read 29`) with a rule and a 16px
  language label: `HELLO! / HOWDY! / HALLÅ! / BONJOUR! / Привет! / ¡HOLA!` against
  `ENGLISH/DIALECT/SWEDISH/FRENCH/RUSSIAN/SPANISH`. **Budget:** none.
  **Coverage hazard — the worst in the catalogue:** measured **27/27** binaries render the
  `Привет!` tile as a bare `!`, and `Å` fails on some, *all with zero layout errors and
  exit code 0*. `--json` will not warn you — a stripped tile still reports its full
  size — so run `bin/check_support_glyph_coverage.py` or read the PNG before captioning
  six languages.
* **`roadrunner32` (70)** — acid-lime ground, a pink rounded frame and inner lime
  panel, a 16-point pink star, a pink rule. `GO WHERE\nTHE ROAD\nOPENS UP` at
  `size 168`, **3 lines**, `min_read 40`, leading .83; kicker 22, footer 21. **Budget:**
  6 fixed words. **Guard:** the star sits at `0.15w/0.18h`, clear of the type box that
  starts at `0.25h`.

### HTML-only user-reference remakes — slots 71–84

These source-led remakes are available only with `--support-renderer html` or
`hybrid`; the default Skia run excludes them. Each editor shows the downloaded
source image beside the recreated artboard. Twelve use a generated text-free
plate under `support-references/materials/user-batch-2026-10-20/`; the green
T33329_00 and pink T16576_09 fields are recreated directly in CSS. Uploaded
display fonts are measured with `SupportLayout.fitLine()` inside reserved
boxes. The measurement inset is 10% horizontally and 24% vertically; text is
clipped at the editor box edge, and the editor reports a warning if the copy
still cannot fit at its minimum size. For production captions, name the visible
type treatment and source art, and describe the text that actually rendered.

* **`palmello32` (71)** — T33329_00, a quiet dark-green field with one centered
  muted-teal script word. **Copy:** one word; fallback `Palmello`. There is no
  caption or decoration. **Alt text:** one teal script word on a dark-green field.
* **`quietattempt32` (72)** — T32243_00, a pale two-line script phrase over a
  charcoal portrait silhouette and fine monochrome grain. **Copy:** up to two
  lines; fallback `Quiet Attempt`. A small widely tracked caption sits below.
  **Alt text:** two pale script lines over a dark profile silhouette.
* **`hushglow32` (73)** — T32243_06, pink script across a tightly cropped,
  glitter-shadowed eye photograph with a black lower band. **Copy:** one main
  line; fallback `Hush And Glow`. The secondary phrase sits in the lower band.
  **Alt text:** pink script over a close-up eye photograph and black caption band.
* **`italianhorror32` (74)** — T15503_08, a broad white brush title across a
  red-black horror still, with narrow spaced subtitle lettering. **Copy:** one
  line; fallback `Italian Horror`. **Alt text:** white brush lettering over a
  red-black horror scene.
* **`dreamwarriors32` (75)** — T15503_09, a stacked white brush title on a
  red-lit scene with a small dark figure at lower left. **Copy:** up to two
  lines; fallback `Dream Warriors`. A small lower caption is fixed. **Alt text:**
  two-line white brush lettering above a lone figure in a red-lit scene.
* **`nesting32` (76)** — T15503_11, a white brush title over a crimson textured
  backdrop with shadowed hands to the right. **Copy:** one main line; fallback
  `The Nesting`. A small centered credit sits below. **Alt text:** white brush
  lettering over a crimson background and shadowed hands.
* **`erotica32` (77)** — T15503_12, one red brush word over a near-black image
  with a diagonal red light streak and underline. **Copy:** one word; fallback
  `Erotica`. **Alt text:** red brush lettering with an underline on a dark,
  red-lit field.
* **`conspiracytheory32` (78)** — T15503_13, a large two-line white brush
  phrase with an angled underline over a red-black paper collage. **Copy:** up
  to two lines; fallback `Conspiracy Theory`. **Alt text:** stacked white brush
  lettering over a distressed red paper collage.
* **`overglow32` (79)** — T16576_00, a pink central script word with violet-blue
  and indigo offset shadows on a blue-violet star field. Small top and bottom
  captions remain separate. **Copy:** one word; fallback `Overglow`. **Alt text:**
  pink script over a blue-violet star field.
* **`pinkvice32` (80)** — T16576_01, blue script with a pink offset shadow above
  a centered pink sports car on cracked pale paper. **Copy:** one main line;
  fallback `Pink Vice`. A small bottom label is fixed. **Alt text:** blue script
  above a pink car on textured pale paper.
* **`attitude32` (81)** — T16576_04, pale script with pink and blue offset
  shadows across a teal fashion photograph. Small top and lower-right labels are
  separate. **Copy:** one word; fallback `Attitude`. **Alt text:** pale script
  across a teal fashion portrait.
* **`indieground32` (82)** — T16576_09, blue two-line script with a pink offset
  shadow on a vivid pink field. **Copy:** up to two lines; fallback
  `Indieground Font Foundry`. **Alt text:** a blue two-line script wordmark on
  a pink field.
* **`caramelsundae32` (83)** — T36099_00, two brown title lines inside a
  scalloped cream panel over coral stripes, with a coral banner below. **Copy:**
  up to two lines; fallback `Caramel Sundae`. **Alt text:** brown display text
  and a coral ribbon on a scalloped pastel candy poster.
* **`sweettreat32` (84)** — T36099_07, three right-aligned display rows beside
  a smiling ice-cream cone illustration, with waffle corners. **Copy:** up to
  three rows; fallback `Sweet Treat Dreams`. **Alt text:** three display rows
  beside a smiling ice-cream cone and waffle-pattern corners.

`T32243_06` has a source-black lower band; the caption belongs in that band.
`T16576_01` and `T16576_04` deliberately place lettering over their subjects as
flat graphic overlays. Preserve those overlaps while keeping every editable
text box within its measured area.

### October 2026 reference batch B — slots 85–105

These 21 additional source-led editors are HTML-only and use the same measured
fit and clipping contract. Nineteen have generated text-free background plates
and square scene extensions under
`support-references/materials/user-batch-2026-10-20-b/`. `beachclub32` uses the
preserved original photo under a turquoise cover panel because image cleanup
was rejected by the image tool. `splitampersand32` rebuilds its two-tone
specimen directly in CSS. Originals, URLs, material hashes, and cleanup notes
are in `support-references/originals/user-batch-2026-10-20-b/SOURCES.md`.

* **`saucystack32` (85)** — T34327_05, three chunky green/yellow lines above a
  snack photograph, with the middle line on a red banner.
* **`anteliascard32` (86)** — T33743_05, a tilted monochrome studio card with a
  large script wordmark and small letter-spaced details.
* **`peacebreath32` (87)** — T15926_01, a golden stacked quote inside a dark
  rounded screen over a quiet ocean image.
* **`nyccoffee32` (88)** — T15926_02, a centered white feature title over a
  warm café photograph and video-frame edge.
* **`afterhours32` (89)** — T15926_03, golden script and collection details over
  an outdoor fashion scene.
* **`outofoffice32` (90)** — T15926_06, a warm orange two-line title over a
  canyon image, with small greeting and vacation lines.
* **`skincareroutine32` (91)** — T15926_07, a low white routine title over a
  skincare portrait; the subject's face stays clear.
* **`youlookgood32` (92)** — T15926_08, a golden two-line script phrase over
  soft ocean texture inside a rounded screen frame.
* **`spiritadventure32` (93)** — T9403_01, a white vertical script quote over
  a blue glacier landscape.
* **`dreamfollow32` (94)** — T9403_02, a low white quote below a seated figure
  facing a night mountain sky.
* **`angelinastyle32` (95)** — T9403_03, pale script and a small uppercase
  subtitle at lower left beside a teal fashion portrait.
* **`comesnatural32` (96)** — T9403_04, black stacked script on the open left
  side, with a shoreline figure at right.
* **`calmafterstorm32` (97)** — T9403_05, centered white script over a muted
  botanical photograph.
* **`beachclub32` (98)** — T18889_00, yellow two-line script on a turquoise
  masking panel over the original editorial image; the panel covers the source
  title and stamp.
* **`splitampersand32` (99)** — T16351_04, a bold pangram on white paired with
  an oversized ampersand on black.
* **`setrum32` (100)** — T16351_08, a white geometric title and red outlined
  date framing a narrow blue corridor image.
* **`nectarambience32` (101)** — T18612_01, a fine mint two-line title over a
  dark magenta science-fiction composition.
* **`fluorescentduo32` (102)** — T19863_07, two bright portrait cards with
  separate yellow headings.
* **`sacharon32` (103)** — T19863_00, a heavy yellow title across a vivid
  pop-art portrait.
* **`lastnightsweden32` (104)** — T7553_01, a rough yellow title on blue beside
  a vertical yellow stripe.
* **`crywolf32` (105)** — T7553_00, a white brush title over dark forest texture.

### October 2026 reference batch C — sequential build, slot 106 onward

Batch C has 21 user-supplied references preserved in
`support-references/originals/user-batch-2026-10-26-c/`. Each is developed and
visually checked in both 3:2 and 1:1 before the next source is started. The first
editor is `welcomemorning32` (106), based on T31141_04: two left-aligned display
rows and an eight-point star over a vivid pink field, above a shallow storefront
photo strip. Built-in ImageGen removed the source title and storefront lettering
to create separate 3:2 and square plates in
`support-references/materials/user-batch-2026-10-26-c/`. Its source comparison,
rendered outputs, and sequential status table are kept with the batch benchmark
and `originals/.../SOURCES.md`.

The second editor is `esens32` (107), based on T31141_05: one centered pink
display word over a monochrome portrait with the tracked `LOTION BEAUTY SKINCARE`
caption beneath it. Its 3:2 plate is copied unchanged from the user-provided
Downloads image; the square plate is cropped from that same image. The original
T31141_05 reference remains unchanged. No wardrobe changes or photo retouching
are applied. Both live text layers are separately editable and fitted to their
ratio-specific layouts. Its source comparison and ratio renders are stored with
the batch benchmark.

The third editor is `asbon32` (108), based on T31141_02: a near-black display
word sits above a wide lagoon photograph inside a vivid pink card with a dark
outer frame. The 3:2 photograph is cropped from the unchanged source reference;
the square editor uses a generated square reframe of that same scene. Both
ratios retain editable, font-fitted headline type and source-matched card and
photo spacing. Its source comparison, square render, and renderer reports are
stored with the batch benchmark.

The fourth editor is `italicregular32` (109), based on T30392_12: a centered,
two-line style label sits above oversized `A` and `a` letterforms. The support
script offers it only when the selected font has another real style in the same
family. It chooses the closest opposite italic/upright sibling when available,
otherwise the nearest distinct style, and uses that face's actual style name in
the label. The generated clean plate preserves the reference's warm, lightly
speckled paper; the square editor crops the same texture to fit its board. The
standalone editor has a sibling-font upload. Its source comparison and ratio
renders are stored with the batch benchmark.

The fifth editor is `smokeletters32` (110), based on T30392_16: tall curly
braces enclose two oversized italic letters over a monochrome smoky-paper
texture. The four corner labels use neutral copy in the source's small tracked
typewriter style. The 3:2 and square versions use separately cleaned background
plates; the letters and braces remain independent live layers. Its source
comparison, ratio renders, and renderer reports are stored with the batch
benchmark.

The sixth editor is `blackerwear32` (111), based on T26301_02: a grayscale seated
fashion portrait fills the left side, with two white display lines over the
photo. The pale gray right panel carries a roman and italic headline plus compact
body copy. User-supplied clean 3:2 and square plates are stored beside the
unchanged original and preserve its model, outfit, pose, cap, sunglasses, crop,
split, and monochrome lighting. All five copy layers are editable, and the
display lines fit the uploaded font independently. Its source comparison, ratio
renders, and normal catalogue render checks are under the batch benchmark.

The seventh editor is `silentnight32` (112), based on T0420_02: two large white
words sit on one centered line across a solid black field, surrounded by small
white and gray star glints. The typography remains live HTML/CSS; each word fits
to the source width, and the vector star positions are independent layout
elements. Both ratios retain the reference's open margins and sparse night-sky
balance. Its source comparison, ratio renders, and normal catalogue outputs are
stored with the batch benchmark.

The eighth editor is `playgrid32` (113), based on T29045_05: two charcoal panels
sit on black, with small cyan corner labels and a large editable `Pickle` title
and `2037` on the left. The right panel has a live `PLAY` heading and a violet
and cream 3-by-3 grid with editable numerals, four SVG arrows, and a geometric
center mark. All displayed words and numerals remain HTML text; no image model
created the lettering. The same paired-panel proportions adapt to square. Its
source comparison, two ratio exports, and normal catalogue renders are under
`support-html/benchmarks/user-reference-batch-c-2026-10-26/`.

The ninth editor is `fridayrunning32` (114), based on T29045_06: a black poster
with cyan corner labels and a large cyan `RUNNING` line, plus a white `FRIDAY`
title between geometric marks and a lower `20 CLUB 25` lockup. The footer copy
remains editable, and every word and number is live HTML/CSS text. No image
plate or AI-generated lettering is used. The square adaptation preserves the
same stacked hierarchy and fits `RUNNING` within the board. Its source
comparison, two ratio exports, and normal catalogue renders are under
`support-html/benchmarks/user-reference-batch-c-2026-10-26/`.

The tenth editor was `greatness32` (115), based on T29045_11. It is withdrawn
from the active catalogue, and slot 115 remains reserved. The archived remake
used the original tree-lined billboard photo, outer frame, horizontal divider,
and lower panels, with editable headline and labels over the baked-in header
copy. The original comparison and ratio exports remain under
`support-html/benchmarks/user-reference-batch-c-2026-10-26/`.

The eleventh editor is `medievalcreatures32` (116), based on T33443_05: the
original red-on-black specimen is rebuilt from three editable HTML/CSS text
layers, with `medieval creatures` above oversized `{1348}` and `manuscript and
bestiaries` below. Both ratios retain the centered hierarchy and source red;
the square layout expands the caption width while keeping the year dominant.
Its source comparison, two ratio exports, and normal catalogue renders are
under `support-html/benchmarks/user-reference-batch-c-2026-10-26/`.

The twelfth editor is `littlemadquote32` (117), based on T33443_07: three
editable crimson italic quote lines sit over a purple radial glow that fades to
black, with a `Psycho (1960)` attribution and small corner credits. The source
wording is live HTML/CSS and the gradient is native CSS. Both ratios preserve the
quote hierarchy and source palette; the original and comparison exports remain
under `support-html/benchmarks/user-reference-batch-c-2026-10-26/`.

The thirteenth editor is `soulrevenge32` (118), based on T33443_11: the paired
black posters retain the source's three monochrome photo bands, crimson cast
poster, and red circled 1987 Dragon Knight card over a violet radial field. All
copy is editable HTML/CSS; the photos are exact crops from the unchanged source.
The square version keeps both portrait panels side by side at a larger relative
scale. Its comparison, two-ratio exports, responsive previews, and catalogue
renders are under `support-html/benchmarks/user-reference-batch-c-2026-10-26/`.

The fourteenth editor is `allworkplay32` (119), based on T18053_05: four lines
of the source quote are live editable italic HTML/CSS text over a text-free,
ice-blue texture plate. The downloaded reference remains unchanged. Both the
3:2 and square layouts preserve the four-line rhythm, with each row fitted to
the uploaded font. Its comparison, two-ratio exports, responsive previews, and
catalogue renders are under
`support-html/benchmarks/user-reference-batch-c-2026-10-26/`.

The fifteenth editor is `sociato32` (120), based on T16618_06: a large live
white `R` overlays the vivid portrait while an editable gold `Quirky.` lead-in
and serif article fill the white right panel. The text-free portrait crop is a
separate material; the downloaded source remains unchanged, and no image-model
lettering is used. The square version independently reframes the portrait and
fits the copy. Its source comparison, two-ratio exports, responsive previews,
and catalogue renders are under
`support-html/benchmarks/user-reference-batch-c-2026-10-26/`.

The sixteenth editor is `owlstory32` (121), based on T18880_08: `The` and `Owl`
form two large editable indigo display lines beside the hand-engraved owl, with
the three-line `WHO COULDN’T SLEEP` subhead below. Separate text-free 3:2 and
square parchment plates retain the source's paper and illustration style; the
original remains unchanged, and no image-model lettering is used. The square
version gives the owl a larger upper-right position and keeps the editable copy
in the left paper area. Its source comparison, two-ratio exports, responsive
previews, and catalogue renders are under
`support-html/benchmarks/user-reference-batch-c-2026-10-26/`.

The seventeenth editor is `hazysky32` (122), based on T18880_11: the lowercase
`hazy` and `sky` display lines use editable type with a muted-gold edge, followed
by an editable `SESSION IPA` caption. Separate text-free 3:2 and square plates
preserve the source's warm paper grain and pink, cream, seafoam, and gold brush
bands. The downloaded original remains unchanged, and no image-model lettering
was used. Its source comparison, two-ratio exports, responsive previews, and
catalogue renders are under
`support-html/benchmarks/user-reference-batch-c-2026-10-26/`.

The eighteenth editor is `itsokay32` (123), based on T18880_15: the live cream
`it's` and `Okay!` title rows sit over a stippled violet rose, with editable
violet `Fenotype Studios` lettering and the tracked `POSTRE - TASTY DISPLAY
TYPE` footer. Separate text-free 3:2 and square plates preserve the floral
poster treatment; the original reference remains unchanged, and no model
generated lettering. Its comparison, two-ratio exports, responsive previews,
and normal catalogue renders are under
`support-html/benchmarks/user-reference-batch-c-2026-10-26/`.

The nineteenth editor is `nightonearth32` (124), based on T18021_05: the two
left-aligned lines `Night on` and `earth.` remain editable in the electric
indigo used by the source. Its black field is CSS, so there is no generated
background image or lettering. The original remains unchanged; its comparison,
two-ratio exports, responsive previews, and normal catalogue renders are under
`support-html/benchmarks/user-reference-batch-c-2026-10-26/`.

The twentieth editor is `goodthingstothose32` (125), based on T17804_02: the
three source-case quote rows and five checkbox labels stay editable, with a
CSS-sampled electric blue-purple field and vector underline and checkbox marks.
The original wording is preserved; no raster material or generated lettering
is used. The square layout keeps the same hierarchy with independently fitted
text. Its source comparison, two-ratio exports, responsive previews, and normal
catalogue renders are under
`support-html/benchmarks/user-reference-batch-c-2026-10-26/`.

The twenty-first editor is `rudybrownie32` (126), based on T17997_03: centered
cream `Rudy` and `Brownie` lines are live editable HTML/CSS over separate
text-free sunset-photo plates. The 3:2 plate is a photo-only text-removal
cleanup; its square adaptation is an exact center crop. The downloaded original
is unchanged, and no AI-generated lettering is used. Its source comparison,
two-ratio exports, responsive previews, and normal catalogue renders are under
`support-html/benchmarks/user-reference-batch-c-2026-10-26/`.

## Reference batch D — October 2026

The first editor is `spaceprint32` (127), based on E9653_03: the source's
retro science-fiction screen-print collage is rebuilt with separate text-free
3:2 and square plates. `HOLO` and `2023` remain live editable type over the
orange and two-colour panels; the numeral glyphs use the currently selected
font. The second editor, `scriptgrid32` (128), rebuilds T28885_02 as eight live
words in a two-column grid. Its family and designer labels come from the selected
font's metadata, with neutral type and format labels. The source responses are
kept unchanged as WebP under
`support-references/originals/reference-batch-2026-10-26-d/`; both ratio exports
are in the full catalogue review folder. The third editor, `smashcourt32` (129),
rebuilds T28885_05 as a selected-font three-line quote with both source captions
editable. Its original court photo stays unchanged; a separate text-free plate
removes only the original lettering, and the square adaptation uses a centered
crop of that plate. All wording is live HTML/CSS, not generated into the image.
The fourth editor, `scriptpattern32` (130), rebuilds T19363_09 as oversized
selected-font words scattered over text-free cream paper. The fifth,
`brushpanel32` (131), rebuilds T8461_02 as four pink, mint, white, and charcoal
CSS panels; Orchid North Design, #FRESH, Believe to Achieve, and Vivid Boutique
are live selected-font text. Its original is preserved unchanged, and no raster
material or generated lettering is used.
The sixth editor, `avalonbrush32` (132), rebuilds T8461_00 with a live selected-
font Avalon word, repeated edge type, and a green “Font Specimen” badge. Its
format-neutral badge keeps the design useful for fonts that are not SVG fonts;
all lettering is live HTML/CSS, and its source remains unchanged.
The seventh editor, `ssrange32` (133), rebuilds T32952_09 over the seller's
unchanged clean fashion photo in landscape and square ratios. Both yellow
source lines, `S/S_RANGE` and `NEW_vogue`, are editable selected-font lettering.
The downloaded reference remains untouched, and the seller-supplied background
plates are stored separately from the original. The eighth editor,
`allsummerlong32` (134), adapts T35520_06 with three large hot-pink live
selected-font lines over a text-free triptych plate; the model, clothing, pose,
and image framing are retained. The ninth editor, `boldcampaign32` (135),
rebuilds T35520_03 as four color blocks with the source's campaign phrases live
in the selected font; the original paper texture remains beneath CSS panels
that fully cover the source lettering. The tenth editor, `goodtimeroll32`
(136), rebuilds T20482_01 with “Let the Good / Times Roll!” in two editable
selected-font lines over a separate text-clean plate. The original stays
unchanged, the fully clothed skater and roller skates remain visible, and the
square adapts by centered cover cropping. The eleventh editor,
`childhoodbook32` (137), rebuilds T22014_02 as four large live rows with its
black and orange emphasis over a white field; every word is editable in the
selected font, and the square layout preserves the four-row rhythm. The
twelfth editor, `playerglyph32` (138), rebuilds T21126_11 with a selected-font
P glyph and the source words “Player / your game / manifestation” on a charcoal
field, using pink CSS blocks instead of added raster artwork.
The thirteenth editor, `alicebadge32` (139), rebuilds T21126_03 as a circular
sunset badge. “RABBITS · GO ASK ALICE” follows the upper SVG arc and “FOLLOW
THE WHITE RABBIT” follows the lower arc; both strings stay editable in the
selected font. The two blue stars sit in the side gaps, and the sunset scene is
drawn with SVG geometry, so no extra raster material is needed.
The fourteenth editor, `notallroads32` (140), rebuilds T16168_01 with four
editable lines over a text-clean aerial photograph of an autumn road. “NOT”
and “ARE” stay gold; “all roads” and “simple,” stay white. The two white lines
use a detected real Italic family member when present, and remain upright in
the selected face when no Italic member exists; the renderer never synthesizes
an italic style.

The fifteenth editor, `practicehard32` (141), rebuilds T16168_07 as four
paired white verbs and gold emphasis words over a text-clean basketball
photograph. Each pair and the display scale are editable. The square layout
repositions all four rows over its own centered crop. Verbs use a detected
actual Italic family member when one exists; without one they stay upright in
the selected face, with no synthetic italic.

The sixteenth editor, `rainbowstack32` (142), rebuilds T19310_08 with four
editable uppercase rows that alternate a thin white outline and a solid white
fill over the source's dark photograph. The square version keeps all four rows
within the frame over a centered cover crop, and every word remains live text.

The seventeenth editor, `wakefamous32` (143), rebuilds T19310_10 as three
editable uppercase selected-font lines inside a thin white rectangular frame.
The text and frame are live HTML/CSS over a separate text-free dark plate; the
square layout independently positions both within its safer inset.

## Registered but not selectable

`blush32`, `sign32` and `wash32` are registered by `@support` and appear in
`--template` choices, but they are **not in `SUPPORT_ORDER`**, so the catalogue
never samples them and passing them on a support run fails the stray check. Do not
plan around them. `SUPPORT_ORDER` is the only thing that makes a panel selectable.
Legacy names may remain in `SUPPORT_RETIRED` without registered renderers;
active-slot retirements stay in `SUPPORT_ORDER` as numbering tombstones and are
filtered by `SUPPORT_RETIRED`. Old renderer-owned PNGs are withdrawn from
shipping output folders when a support run finds them.

---

# Part 4 — Caption and alt-text rules

1. Describe **the rendered file**, not the template's intention. If a slot came
   out empty, or a row came out short, or the echo was suppressed, the caption
   follows the file.
2. Alt text is one concise sentence naming the actual type treatment, the readable
   phrase, and one or two prominent visual elements.
3. Never repeat the font name in a support caption — it is not on the panel.
4. Name the type treatment you can see (`letterpress broadside`, `die-cut`,
   `arched lockup`, `contour bands`), not a technique you cannot see.
5. Do not claim a style, weight, axis, glyph, or use case the font does not have.
   The only panels that carry type evidence are `weightfamily32`,
   `mangosboard32`, `plakat32`, `alphabet32` and `contour32`. On `mangos32` the
  ramp is artwork. **None of the 43 active remakes carries a family claim**, and on the 18
   whose every visible string is a fixed literal (all 14 of `objects.py`, plus
   `ravencover32`, `wideclaim32`, `contactlist32` and `phonegarden32`) not one word is
   about the buyer's copy either.
6. For locked panels, describe the fixed imagery accurately — the mountain
   illustration, the paired black panels, the archival group photo, the dusk city
   hero, the salt-flat portrait, the concrete-building photos, the chalkboard
   crown, the pixel sea card and dolphin, the botanical carton, the gingham
   timeline — because that imagery is supplied artwork or generic vector
   furniture, not a photograph of the buyer's product.
7. Palette wording: a flexible panel's ground may be described in world terms
   (`clay`, `midnight`); a locked panel's must be described by what it actually is
   (`navy, cream and cyan`). The `t30332` violet grounds, `meditation32`'s
   pink-mint gradient and `typewall32`'s marigold are **fixed inks that only
   nominally belong to a world** — describe the ink.
8. **Composition furniture is not a specimen claim.** These fixed words describe
   the layout, never the face: `WIDE` / `SERIF` (`wideclaim32`), `STRONGEST` /
   `WEAKEST` (`strongweak32`), `PAST` / `PRESENT` / `FUTURE` (`pastpresent32`),
   `DOLLAR` and the price framing (`signalclock32`), the six language labels
   (`greetingsgrid32`), `TRACK LIST` / `NO. 07` (`contactlist32`), and the eight
   fixed track titles (`contactlist32` rows). Writing "a wide serif" or "three
   weights" from any of them is the single most common bad derivation available.

---

# Part 5 — Spotting a bad derivation before you ship

The renderer stops hard failures. These are the soft ones that pass validation and
still look wrong. Check the 12 selected designs at both ratios against this list
once, then move on. A normal Agent 27 handoff contains 24 support images; a
full-catalogue review is a separate, explicit run.

| Symptom | Cause | Fix |
|---|---|---|
| Companion type nearly as large as the display line | Copy too long triggered a whole-block shrink `k` | Shorten to the panel's budget |
| A row of letters noticeably shorter than its neighbours in a legacy Skia render | `clean()` stripped undrawable glyphs | Caption what rendered; do not fill the gap |
| A glyph fallback appears in an HTML support render | The selected face lacks that character | Review the displayed fallback and `contentWarnings`; the legacy glyph checker does not audit HTML |
| A tile shows one glyph but `--json` reports a normal size in legacy Skia | Stripping happens before `fit()`, so size proves nothing | Run `bin/check_support_glyph_coverage.py`; it applies only to Skia literals |
| `ink lifted X:1 -> Y:1` notes on several slots | Palette fighting the ground | Leave it — the guard is working; only an *unreachable* floor is an error |
| A lift that starts below 2:1 (`sunkiss32` 1.3, `greetingsgrid32` 1.9) | A locked ground/ink pair that was never high-contrast; `objects.py` only asks 3.2 | Look at the file; do not change the module to chase it |
| No echo line on `line32` | `FLOWING` family or density ≥ 0.5 | Correct behaviour, not a fault |
| Arches set in a plain sans on `crest32` | `FLOWING` family routed to the companion face | Correct behaviour |
| No quote marks on `quote32` | Face does not draw `"` | Correct behaviour |
| A wordmark crossing artwork | Marks register `collide=False` by design | Only fix if it is genuinely unreadable |
| `OFF-CANVAS` on `typewall32` | Deliberately overhanging rows not marked `bleed=True` | Historical catalogue finding; selected templates `ravencover32` and `blossom32` mark intentional bleed correctly |
| A fixed headline came out `TYPE` / `FORM` / `PRINT` | The font's name collides with the panel's own word (`FOCUS`, `WIDE`, `SERIF`, `STYLE`, `BLOOM INTO CALM`) and `support_render_copy` replaced it | Caption the replacement; never restore the original word by hand |
| The year panel shows a word, or a long word shrank `1982`'s box | `yearposter32` takes `word` with no length check | Do not select it for a long word; caption what set |
| Theme `bone` and the panel is still hot pink / marigold / black | The module never read `ctx["pal"]` for that ground | Describe the ink (Part 4 rule 7) |
| A count or fixed string in this guide disagrees with the render | The remake modules are under active edit | `python3 bin/check_support_catalogue_facts.py` — the code wins; update this file |
| Your authored copy never appeared | Panel is hard-coded, or the copy was stock/name-bearing, or the panel wasn't selected | Check Part 3 "Copy:" and the `supports:` selection line |
| `support-11_…` with no `support-2…10` | Numbering is catalogue slot, not ordinal | Nothing to fix |

## Editing the remake modules safely

The 43 active remakes occupy 44 stable slots in five modules under `bin/pin-studio/support_templates/`
(`t30332.py`, `fashion.py`, `photo.py`, `poster.py`, `objects.py`); `SUPPORT_ORDER`
still owns their numbering, so a slot keeps its folder name whatever else changes.
All visible type goes through `Sheet.text`, and artwork uses generic specimen
language rather than the font name. Crop-safe image inserts live under
`support-references/materials/` and one-pass generation prompts in
`IMAGEGEN-PROMPTS.md`.

When changing these layouts, preserve each reference's dominant hierarchy,
placement, and palette before polishing decorative details. If the source image
has baked-in text, use only its clean crop or the matching generated material;
do not place a full product reference image behind new type. Transparent source
cutouts must retain alpha, and fashion illustrations must remain fully clothed
and non-suggestive. Mark a shape that is *meant* to reach the canvas edge with
`bleed=True` — every full-bleed photo, ground and overhanging row that omits it
fails `VERIFY`. See [REMAKE-MAP.md](REMAKE-MAP.md) for the per-reference template
map and `SOURCES.md` for material provenance.

---

# Part 6 — Authoring per-panel copy (exception path)

## Creative Market reference remakes — slots 181–182

`numeralfolio32` is a restrained paper-toned 0–9 sheet with two rows of live
selected-font numerals. `timechange32` is a black poster with pale-blue live
“Time”, “Change”, and “(380)” display lines. Both have separate 3:2 and square
placements. Keep the secondary labels neutral and omit source foundry or font
names. The small category caption is generated from the selected font's
classifier so it reflects the actual font being shown.

## November 2026 image-backed additions — slots 173–180

These HTML/CSS layouts use the clean plates in
`materials/user-batch-2026-11-03-a/`. Display wording is live text in the
selected font. Keep the supplied neutral label face for secondary captions.
Do not use source names, studio credits, or font-category claims.
Slots 174 (`statueframe32`), 177 (`fashioncard32`), and 179
(`parkstatement32`) have since been retired;
their rows below are retained as source history.

| Template | Composition and safe copy area | Caption / alt focus |
|---|---|---|
| `crimsonportrait32` | Red fashion portrait; white title in the lower-left field. | Red portrait and large lower headline. |
| `statueframe32` · retired | Classical figures at the sides; compact dark title stays on the central cream panel. | Sculptural side panels and centered message. |
| `portraitcard32` | Small portrait above/alongside open ivory card; dark copy remains inside the card. | Portrait and airy editorial card. |
| `warmportrait32` | Warm close-up; pale title sits left of the face and uses a quiet shaded edge. | Close-up portrait and pale display line. |
| `fashioncard32` · retired | Fashion image on the right; editable dark copy stays inside the left cream card. | Fashion photograph and inset quote card. |
| `cinemaportrait32` | Low-light portrait; pale title stays low over the shaded image area. | Cinematic portrait and lower title. |
| `parkstatement32` · retired | Monochrome park photo at left; cream copy sits in the open dark field at right. | Bench-side silhouettes and split composition. |
| `amberquote32` | Defocused amber image; five-line editable quote and two-line credit placeholder. | Soft amber photograph and large centered quote. |

All eight original entries have independent square placements. The five active
templates keep their copy editable. Amber Quote retains the five-line reference
quote in its editable slot rather than replacing it with a short generic phrase;
the font and studio credit remain placeholders.

Standard runs author nothing for supports (1.3). Pass a brief only when the seller
has asked for a specific adjustment to a delivered set.

The mechanism exists and works: `render(name, per.get(name, ctx))` takes per-panel
copy and theme from a brief's `supports` block, keyed by template name, with the
four keys `line`, `sub`, `over`, `word` plus `theme` and `tone`.

```json
{
  "name": "Exact Font Name",
  "class": "elegant",
  "about": "structural description of the face",
  "supports": {
    "line32":  {"line": "Quiet mornings slow hours", "over": "Set by hand", "theme": "clay"},
    "quote32": {"line": "Keep the letters honest", "theme": "bone"}
  }
}
```

Rules that will bite, all verified live:

1. **Author only for the 13 actually selected.** Selection is deterministic from
   `sha256("{name}|{class}|support-catalogue")`, so run once and read the
   `supports: selected …` line, then author for those names. Copy for an
   unselected panel is silently wasted; a panel this face cannot wear is reported
   as "not shipped".
2. **Themes must be unique across the panels you author.** Reusing one is rejected
   before rendering: `"support theme clay on line32, sticker32 — four panels want
   four different worlds"`, exit code 2.
3. **A supports-only brief is legal** and skips the five-pin contract, but `about`
   is still required and the class must be one of the four.
4. **Word budgets still apply** and are enforced by `panel_text`'s 4-word cap on
   `line`, the legibility floor, and each panel's own refusals.
5. **`check_brief` does not run on the standard Agent 27 path** (no `--brief` is
   passed), so the anti-samey overlap test (`>= 0.5` shared tokens) and the
   historical reuse scan only apply once you introduce a brief. Do not author a
   support line that repeats a Pinterest headline for the same font.
6. **Never author copy for a locked panel.** It reads no copy at all, and its
   palette override means a `theme` value changes nothing.
