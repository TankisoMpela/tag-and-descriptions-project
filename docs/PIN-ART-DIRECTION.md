# Pinterest pin art direction — the workflow

How a font becomes five pins that a stranger would save. Companion to
`docs/SKIA-PIN-RENDERER.md`, which says what the renderer *can* do; this document says
what it should *choose* to do, and in what order.

**This replaces the image-mashup approach.** Compositing specimen PNGs is a
forward-looking statement about nothing. A pin is a small poster whose subject is
letterforms.

**Status (locked 2026-10).** The five templates are the design and the design phase is
closed: production is Agent 13 STEP 2 (`/font-prep`, inside `/full-workflow`), which
authors `pins.brief.json` and runs one `bin/render-pins --brief` command. No template
work happens without a new user instruction, and the other font classes are
note-only: brush (Kuro Ripper), handwritten (FineLetter), tech/sports (IronRush),
blackletter/celtic (Braewick) each earned the label "not designed yet" — today's
five are **the elegant set templates** and carry every font until told otherwise.

---

## 0. What is decided here and what is decided in code

The templates are the spec now. `bin/pin-studio/pin_studio.py` ships five tested
compositions — `hero`, `set`, `wall`, `phrase`, `full_stack`, rendered and numbered
`pinterest_1..5` in that order — evolved from the `out/v6-black` series, and `--stress`
proves them across faces and copy lengths.

Everything below that is a *mechanical* rule has moved into that code and is no longer
a thing to remember:

| Rule | Now enforced by |
|---|---|
| nothing overlaps, nothing runs off the canvas | `Sheet.verify()` |
| type always fits its column, at any face | `fit()` / `layout()` bisection, `fit_measure()` |
| contrast ≥ 4.5:1 against the ground actually painted | `Sheet._enforce()`, measured not assumed |
| body copy readable in a 200 px thumbnail | the `min_read` legibility floor |
| no tofu, no placeholder digits | `audit()` + `clean()` |
| ≤ 200 000 bytes | `MAX_BYTES`, with a PIL 4:2:0 JPEG re-encode at q90/85/80 that says so in the notes |
| copy that repeats itself | `check_brief()` — no canned headline, ≥50% token overlap between two pins refused, a repeated theme refused, and any line already shipped for another font hard-fails the batch scan |
| glyph integrity, word budget, dedupe | `--json` errors, and the tag ledger |

What is left in this document is the part code cannot do: **what to write on the pin**,
and knowing a good composition from a safe one. §4's concept menu and §9's element menu
describe improvisation that the template library has now replaced — read them as the
backlog for templates not yet built, not as instructions for a run.

---

## 1. What the pin is for


Nobody on Pinterest is looking for a font. They are collecting *looks*: a mood, a
layout idea, a phrase they want to remember, an aesthetic for a board. So:

* The success metric is **save / like**, not click-through. A pin that is admired and
  never clicked still feeds the algorithm and still builds recognition.
* **The font must be a pleasure first and a product second.** The hook is a phrase, a
  word, a quote, a letterform — something worth staring at with zero purchase intent.
* The name of the font is **subtext**. It lives in the colophon rail at ~10–14% of the
  focal scale, or hides inside the specimen as a cameo. It is never the headline, never
  an eyebrow screaming "NEW", never a price, never "available now".
* Technical facts (glyph counts, weight ranges, OpenType features) are **not pin
  content**. They belong in the description text that Buffer/Pinterest carries, not on
  the canvas. A pin that looks like a spec sheet is invisible in the feed.
* The link and the marketplace are handled by the CSV row, not the artwork. The image
  never says where to buy.

Read that as: design for the person who will pin this to a board called "type
inspiration" and never visit the shop. That person is the whole point.

---

## 2. The unit of work

**One font → five pins, each a different design decision.** Not five palettes on one
layout: Pinterest dedupes near-identical images, and a board owner who sees five
siblings skips all of them.

Differentiation is structural and runs on two axes:

| | Constant across the five | Variable across the five |
|---|---|---|
| field | 1000×1500, one dominant focal phrase | — |
| voice | the font's own character | copy register, and the phrase |
| grammar | the colophon rail syntax (§7) | ground polarity (light/dark), palette |
| craft | glyph-integrity gate, contrast ≥ 4.5:1 | **the template** (all five, one each), the theme, the tone rung, the copy |

The constants make the set read as one font's family. The variables make each pin a
separate object. The shipped five, in render order: `hero` (the name edge to edge over
the font's own giant initial, in two colours), `set` (the alphabet as upper/lower
pairs, funnelled and coloured row by row), `wall` (phrase, digits and punctuation,
every row to measure, filling the frame), `phrase` (a short line of copy with drawn
ornaments around it), and `full_stack` (the specimen sheet: name, purpose, and the
alphabet filling the page). Grounds mix dark and paper *within* a set — that contrast
is part of why the series reads as designed rather than generated.

---

## 3. Read the font before you design anything

Collect facts, then form an opinion. Both are required: facts alone produce a
specimen, opinion alone produces decoration that fights the letterforms.

**Facts** — from the binary, mechanically (the existing `audit()` in
`bin/pin-studio/pin_studio.py` already extracts upem/glyphs/cap/x-height/features
and flags placeholder glyphs; keep using it):

* what the font *is*: contrast (stress, thick/thin ratio), x-height vs cap, terminal
  shape (blunt / tapered / sheared / ball / swash), slant, aperture, spacing looseness;
* character set reality: which glyphs exist, which are stubs, whether lowercase or
  uppercase or figures carry the personality;
* features present (`liga`, `dlig`, `salt`, `ss01…`, `calt`, `kern`) — an alternate-set
  font is asking to be shown;
* family name's own phonetics and length (it may be the phrase, or may fight it).

**Opinion** — write one sentence answering: *what does this font already want to be
about?* Not "it is a script", but "it wants to look like a hand-written note left on a
kitchen table" / "it wants to be a 1970s national-park sign" / "it wants to be a
film-title card at 2 a.m.". Everything downstream follows from that sentence, and it is
the reason two fonts get different designs even when the same concept is drawn.

**The description** (`outputs/font-preparation/{NUM}-{slug}/description.txt`, or the
`description` field in `outputs/pinterest/registry.json`) is the seed source for both
vocabulary and subject matter. Read it for: the named place/era/craft, the verbs, the
language or culture it gestures at, any anecdote. Pull candidate words from it, then
reject most of them — the description was written for a marketplace, and its language
is selling language.

The three **tensions** to name explicitly, because a good pin dramatises one of them:

* geometric vs hand (does it want a rule or a smudge?);
* loud vs quiet (high contrast rewards scale and dark grounds; even textures reward
  flat colour and typographic rigour);
* readable vs sculptural (does the personality live at word size or only at display size?).

---

## 4. Choose a concept per pin

A concept is **the reason the viewer's eye stops**, stated as one clause. In a
from-scratch run draw five different concepts for the five pins (in the locked run the
templates already do this); the same concept never repeats across two fonts
inside the 14-day ledger window.

Each is achievable with calls that are probe-verified in `docs/SKIA-PIN-RENDERER.md`
(section references are to that file).

| # | Concept | The move | Renderer backing |
|---|---|---|---|
| 1 | **The quote as specimen** | 3–9 words of real prose set at editorial size, justified block, one word blown up | Tier C paragraph, `kJustify`, mixed-size runs, one paragraph per line for rhythm (§4) |
| 2 | **One word, enormous** | a single word cropped so close the counters break the field; nothing else but the rail | `fit()` scale + clip paths (§8) |
| 3 | **Letterform as object** | a single glyph at poster scale, printed in flat colour, treated as sculpture not as text | `Font.getPath` → fill + `skia.Op` inline (§5) |
| 4 | **The alternate showcase** | one root word restated 4–6 times, each with a different `salt`/`ss01`/`dlig` applied | shaping per run via uharfbuzz features (§1) |
| 5 | **Type as texture** | the same short syllable tiled so densely it stops reading and becomes a pattern, one gap holds the phrase | `drawAtlas` / `Path2DPathEffect` (§6) |
| 6 | **A route for the letters** | the phrase walks a curve or a spiral, rotating per glyph | `Path1DPathEffect` with a glyph marker, `drawTextOnPath`, `allocRunRSXform` (§5, §4-B) |
| 7 | **Two voices arguing** | a high-contrast display word against a small tracked-out caption in the *same* family — the font talking to itself | Tier C two runs, `setLetterSpacing`, `ColorFilters.Matrix` for a tonal shift (§4, §3) |
| 8 | **Overprint / misregistration** | two colour plates, slightly offset, the overlap a third colour | `ImageFilters.Arithmetic` or `BlendMode.kMultiply` (§3, §7) |
| 9 | **Paper and ink** | a warm ground with real tooth, letterpress-ish, no gradients at all | SkSL hash/value noise as ground (§7), PNG ship (fine at 1000×1500) |
| 10 | **The wash** | a soft mesh-gradient field with the phrase floating on it, atmospheric, minimal structure | `drawPatch`/`drawVertices` with `kModulate` + white paint (§6), linear surface (§3) |
| 11 | **Cut and restate** | the word printed once, then a horizontally sliced second copy offset — a collage move | clip rects + two draws of one `Picture` (§8) |
| 12 | **The cameo** | a normal editorial layout in a *workhorse* face, and the display font appears only for one word — the viewer has to notice | Tier C with `setForegroundPaint`/distinct typeface on one run (§4) |
| 13 | **Figure study** | numerals or punctuation as a graphic grid — a phone number, coordinates, a time, a decimal | `Font.getPaths` stamping or monospace-ish tracking (§5) |
| 14 | **Language hook** | a word/short line in the language or culture the font gestures at, plus its romanisation | Tier C, verify coverage before setting (§3) |

Deliberately excluded: the technical diagram, the contour/wireframe "craft" pin, the
full-alphabet grid, the weight-range ladder, the letter-spacing ruler. Those are
foundry-marketing artifacts that read as homework in a feed of pictures. Wireframes are
allowed only as a subordinate texture under a phrase (concept 5/9 variants), never as
the subject. If a concept cannot be described without the word "glyph", reconsider.

**Rolling the concepts.** Pick 5 non-repeating rows, weighted by the §3 opinion:
a high-contrast serif earns 1/3/10; a chunky display earns 2/8/11; a script earns
1/6/14; a geometric sans earns 4/7/13. Never let a random draw produce two
single-word-hero layouts in one set — slot 2 is reserved once.

---

## 5. Copy: the hook comes first, the name comes last

### The register menu

Choose one register per pin, and let the font's character pick it. The register decides
the *voice*, so five pins of one font can feel like five different authors — which is
the point.

| Register | What it sounds like | Suits |
|---|---|---|
| **Aphorism** | a short true-sounding observation, no attribution | quiet textures, editorial serifs |
| **Definition** | `word — a made-up second meaning`, a fake dictionary entry | high-contrast display, wit |
| **Place + era** | a street name, a coordinate, a year, a hotel | retro, continental, stencil faces |
| **Craft line** | one step from a real process: "fold twice, then press" | hand, workwear, utilitarian faces |
| **Sensory fragment** | not a sentence — "cold tile, 6 a.m." | atmospheric, washed, soft |
| **Address / label** | a name-and-place like a return address or a crate stencil | condensed, industrial, grotesque |
| **Line of verse** | 2–4 words of rhythmic language, original, no quotation marks | scripts, calligraphic |
| **List** | three nouns on one line, comma-separated, ending without a period | playful, wide, loose-tracked |
| **Field note** | an observation with a measurement, a date, a species name | scientific, botanical, technical |
| **Name** | a person's name, set as if on a place card | anything with a strong italic or swash |

### Rules for the phrase

* **≤ 10–12 words on the canvas total**, including the colophon. At 200 px thumbnail
  width, more than that is texture, not message.
* Never reuse a phrase across fonts within the ledger window (§11). Never use a famous
  quote — it will be searched, matched, and read as filler; and attribution drag
  makes the pin feel like merchandise. Write the line.
* No "font", "typeface", "new", "available", "shop", "%", or price on the canvas.
* No call to action, no arrow, no "save this". The save happens because it's nice.
* Say something the letterforms can deliver: a word whose ascenders/descenders/figures
  exercise the font's actual personality. For a font with a wild `Q`, the phrase
  contains a `Q`. This is the single strongest link between copy and design — prefer
  copy that *demonstrates* over copy that *describes*.
* Prefer concrete nouns and verbs. Abstractions ("creativity", "elegant") photograph as
  nothing.
* **Split the copy into a hook word and a body line.** Take the phrase's strongest noun
  or verb, draw it alone at the focal rung, and let the rest of the sentence continue
  beneath at 36–44 px. The eye gets one thing to read at thumbnail size and a second
  thing to find when it stops. Both are the font; neither is the product name.
  (`Harbour` / "Every harbour keeps one light…" in the worked proof.)
* Test the phrase aloud at the intended scale: if the eye has to work, it is too long.
* Language: match the font's own gesture. A font described as Iberian can carry Spanish;
  **only if every codepoint exists in the binary** — check coverage first, missing
  glyphs render as tofu and are the fastest way to look amateur.

### The font name as subtext

Three legitimate treatments, and the set should use more than one across its five pins:

1. **Colophon rail** (always available): bottom-left or right, 20–26 px, tracked out,
   in the neutral workhorse face. `{Font Name}` on one line, an optional
   `{foundry-ish descriptor}` or year beneath it. Small, dry, part of the grid.
2. **In-specimen cameo**: the font's own name set *in the font*, as a tiny secondary
   line inside the phrase block. For name puns (a name that is already a word).
3. **Absent.** The name appears only in the pin's title/description CSV fields. Legit
   for concepts 3/10/11 where any text would break the image.

The title text that goes in the CSV is a separate piece of writing and *is* allowed to
name the font and the marketplace — that is where the product information lives. The
canvas stays clean.

---

## 6. Composition

Constants: the field is 1000×1500; margins are a modular unit (start from
`M = 84`, then derive all other gaps as `M/2`, `M`, `M*1.5`, `M*2`); one focal element;
the colophon rail grammar is fixed.

Variables, deliberately rolled or chosen:

* **scale rung** — the focal size drawn from a small set (e.g. 96 / 140 / 220 / 300 /
  460 px) rather than always "fit to width". "Fit to width" is why generated pins look
  machine-made: it removes the choice of how big. Mechanically: walk a fixed rung list
  from the top and take the first whose natural advance (`Font.getWidths` + the rolled
  tracking) clears `2*M` — then drop a rung rather than shrink. The proof uses
  `[340, 288, 240, 196, 156, 124]`.
* **anchor** — optical, not geometric: baseline placement from `FontMetrics.fCapHeight`
  / `fXHeight`, phrase block sitting above or below the centre line, off-centre by a
  margin unit.
* **ground polarity** — light field / dark field / mid tonal wash. Exactly one dark pin
  per set.
* **axis** — upright, or the whole composition rotated 90° (vertical rail type), or a
  slight tilt on a single element.
* **element count** — 1 to 4; if a fifth element appears, delete something.
* **texture presence** — grain/mesh/none.
* **palette** — from the ink/paper sets, seeded (§8).

Two compositional habits that separate designed from generated:

* **Tension over balance.** Elements that share an edge or a baseline read as a grid;
  elements that *nearly* touch, or crop through the field, read as a decision. Crop at
  least one thing in one pin of every set.
* **One thing is loudest.** If the palette, the scale, and the texture are all shouting,
  nothing is. Choose the loud channel per pin and keep the other two quiet.

---

## 7. Series coherence and the colophon rail

The rail is the family resemblance: same corner, same workhorse face, same tracking,
same two-line structure, across all five pins. It is the quiet promise that these
belong to one font, and it frees everything else to vary.

```
{Font Name}                       ← 22–26 px, +10% tracking, workhorse face
{descriptor · year}               ← optional second line, 60% of the first's value
```

Nothing else lives in the rail. No URLs (a bare domain in the artwork is read as an ad
and de-ranks), no marketplace logos, no hashtags.

---

## 8. Non-determinism: the roll vs the call

The user-facing requirement is that design must **not** be fully deterministic. Do not
solve that by making every choice random — that produces noise, not variety. Split the
decisions:

**The call (agent judgement, unseeded, reasoned from §3).**
Concept selection, the phrase, the register, the loud channel, which glyph to showcase,
whether the crop happens. These are written down in the direction block (§10) as
decisions with a stated reason. A model that picks these from the font's character is
what makes two runs on two different fonts look genuinely different.

**The roll (seeded, mechanical, reproducible per date+slug).**
Palette index, ground polarity within the allowed set, texture parameters, rotation
angle, margin multiple, scale rung, element offsets. Seeded so a re-run of the same day
produces the same files (`outputs/pinterest/{YYYY-MM-DD}/` is re-uploadable) but a
different day produces a different design.

```python
seed = int(hashlib.md5(f"{slug}|{date}".encode()).hexdigest()[:8], 16)
rng  = random.Random(seed)
palette = rng.choice(PALETTES)          # after §3 ruled out any that fight the font
grain   = rng.choice(["none", "hash", "value"])
tilt    = rng.uniform(-2.5, 2.5) if rng.random() < 0.35 else 0.0
```

Guardrails on the roll — randomness is only allowed inside a coherent envelope:
contrast stays ≥ 4.5:1; at most one dark ground per set; no palette that clashes with
the §3 opinion (a soft textural serif is not neon); the rail is always legible; and the
focal phrase always fits its rung — if the drawn size doesn't fit, **drop a rung**,
never auto-shrink-to-fit.

Where the harness is a model rather than a script, the equivalent split holds: the
model writes the direction block, and a small `--seed` in the renderer rolls the
numeric parameters so the same brief re-renders identically.

---

## 9. Element menu, keyed to what the renderer actually does

Pick 1–4 elements per pin, each justifiable by the concept. "Renderer" references point
into `docs/SKIA-PIN-RENDERER.md`.

| Element | Renderer backing | Use it when |
|---|---|---|
| Rule / hairline rail | `drawLine`, dash or discrete path effect | the composition needs a spine; never decorative-only |
| Mesh wash (Coons patch) | `drawPatch` 12 cubics + 4 colours, `kModulate`+white paint **into its own surface**, composited with `drawImage(snap, 0, 0, SamplingOptions(), Paint(Alphaf=0.45))` | atmospheric, quiet, sensory registers. At 100% it measured 3.33:1 contrast — a wash is a *tint*, not a ground |
| Soft lens / halo | `ImageFilters.Magnifier`, radial gradient shader | a second look at one word |
| Halftone or stamp field | `drawAtlas` with `RSXform.MakeFromRadians` | texture-as-subject, figure studies |
| Type-tiled pattern | `Path2DPathEffect(Matrix, glyph tile)` | the font's shape is the interesting thing |
| Glyph used as ornament | `Font.getPath(gid)` stamped as a mark (not as reading) | a distinctive ampersand, swash, or `Q` tail |
| Inline / stencil letterform | `skia.Op(a, b, kDifference)` after `AsWinding` | bold, poster, overprint concepts |
| Curve-routed phrase | `drawTextOnPath(text, path, matrix, font, paint)` or `Path1DPathEffect` | hand-made, poetic, vintage registers |
| Per-glyph kinetic run | `allocRunRSXform` / `allocRunPos` | one word only; a whole sentence becomes unreadable |
| Gradient inside wrapped text | Tier C `setForegroundPaint` with a linear shader | dark fields, single-word heroes |
| Justified or ragged body block | Tier C; rhythm from explicit line breaks, **not** `StrutStyle.setLeading` (broken — renderer doc §4.1). Use `kLeft` on a display face; `kJustify` opens rivers in it | the quote-as-specimen concept |
| Wavy / dashed underlining | `setDecoration` + `setDecorationStyle` | accent without a new shape |
| Duotone or desaturated grade | `ColorFilters.Matrix` luma rows; `HSLAMatrix` | unify an overprint pair |
| Grain / paper tooth | SkSL **interpolated** value noise, one octave, `u_scale ≥ 200`, quantised to 3–5 levels, near-white return, `kMultiply` | craft, field-note, letterpress registers. Continuous tone is the cap killer (measured 257–978 KB for a ground alone); blocky `floor()` hash is cheap but reads as a quilt — renderer doc §10 |
| Ghost word | Tier B `allocRunPosH` at a mid rung, tint one step off the ground, `kMultiply`, inside `cv.clipRect(band)`, bleeding off an edge | the composition has a dead middle band; gives the face a second size without a second voice |
| Offset overprint plates | `ImageFilters.Arithmetic`, `BlendMode.kMultiply` | riso/screen-print gestures |
| Cropped/sliced restatement | clip rects, two draws of one `Picture` | collage, cut-and-paste concepts |
| 9-s patch ground | `Canvas.Lattice` | a border or frame that must stretch |
| Depth without a drop shadow | `ImageFilters.DropShadow` / `saveLayer` blur | card or plate treatments |
| Vertical rail type | `concat(Matrix)` rotation on a run | labels, addresses, placards |

Not on the menu: anything requiring `Canvas.drawShadow`, `skia.Blender`, custom blend
modes, or `maxLines` — all absent from this wheel (§12 of the renderer doc).

---

## 10. The direction block

Before rendering, write this. It is short by design — it is a decision record, not an
essay, and it is what a later run reads instead of re-reasoning. In the locked run this
block is carried by `pins.brief.json`: per pin a fresh `line` (plus the template's own
word/sub/over slots), a distinct `theme`, and a `tone` rung — the renderer's
`check_brief()` refuses repetition, so what used to be a checklist is now a gate.

```markdown
Font: {Font-Name}  slug: {slug}  date: {YYYY-MM-DD}
Character: <one sentence — what the font already wants to be about>
Tension:   <geometric|hand> vs <loud|quiet>, <readable|sculptural> — which one the set dramatises

Pin 1  concept: #<n> <name>       register: <Aphorism|…>
       phrase: "<exact canvas copy>"        name treatment: rail|cameo|absent
       loud channel: <scale|colour|texture> others quiet
       elements: <2 from §9>                ground: light|dark|wash  palette: <name>
       why: <one clause tying it to Character>
… ×5
Set: exactly one pure hero, exactly one dark ground, no repeated concept row.
```

Five `why` lines that don't reference `Character` mean the direction was not actually
derived from the font — redo it.

---

## 11. Anti-repeat ledger

`outputs/research/pinterest-tags.sqlite` already holds `tag_uses`, `pinned_runs` and
`pins` (full shipped text, via `python3 bin/pinterest_tag_ledger.py history --slug
<slug> --full`), and `brief.md` prints it before copy is written. Extend the same idea
to design:

* record per shipped pin: `(slug, date, concept_row, palette, ground, register,
  phrase)`.
* reject a new plan that repeats a **concept row** within 14 days across fonts, or a
  `(concept, ground, palette)` tuple within the same set.
* phrases are checked against the `pins` table for near-duplicates before rendering —
  the same dedupe logic Pinterest applies to images should be applied by us first.

The point of the ledger is not enforcement for its own sake: three consecutive fonts
rendered as "one word, enormous, on a dark ground" makes the account look like a
template, and templates are scrolled past.

---

## 12. Checks before the image is kept

| Check | How |
|---|---|
| the face loaded | `Typeface.MakeFromFile` returns `None` for a bad path and `Font(None, size)` then silently renders **Noto Sans** — assert the typeface and its family name before drawing anything |
| glyph integrity | every drawn codepoint exists and is not a placeholder — `Font.textToGlyphs` → gid `0` is `.notdef`, and `audit()`'s flagged set is never drawn from |
| thumbnail legibility | `drawImageRect` the finished pin into a 200×300 **RGBA** surface and count dark pixels in the focal band: want **15–60%**. Below, the hook can't be read in the grid; above, it's a black slab. Reference run: 17% |
| contrast | **WCAG 2.x relative luminance** (sRGB-linearised), darkest 5th percentile of the focal band vs the median of a ground box containing no ink — renderer doc §2 has the exact array code. The naive 8-bit luma shortcut understates a light-ground pin by 2.3× (5.39 vs 12.23 on identical pixels) and will make you reject good work. Floor 4.5:1; reference run: 12.48:1 |
| word budget | ≤ 10–12 words on canvas |
| no selling language | grep the copy for `font`, `new`, `buy`, `shop`, `free`, `link`, `%` |
| file size | ≤ 200 KB, measured from `stat().st_size` on the actual file — not inferred from the design. Keep ~50 KB of headroom (reference pin: 153.1 KB PNG). If it's over, cut in this order: tooth levels 5→3, drop the ghost word, **never** shrink the type |
| dedupe | concept row and phrase not used in the last 14 days (§11) |
| set integrity | exactly one hero, exactly one dark, five distinct themes and five distinct headlines — `check_brief()` refuses anything less |

Failing any check: change the design decision, not the threshold. A check that passes
too easily is a suspect check — verify the checker before trusting the pin.

---

## 13. Failure modes, named so they're recognisable

1. **The spec sheet.** Wireframes, glyph counts, feature tables. Correct information,
   wrong medium.
2. **The shrug composition.** Everything centred, everything evenly spaced, nothing
   cropped, nothing loudest. Reads as generated.
3. **Fit-to-width hero.** The phrase is scaled until it touches both margins, so every
   pin of every font has the same silhouette.
4. **The pitch.** Font name at 300 px with an "available now" — this is an ad, and ads
   are the least-saved content on the platform.
5. **Palette-only variety.** Five colour swaps of one layout: deduped by Pinterest,
   ignored by boards.
6. **Decorative mismatch.** A soft letterpress grain under a brutal geometric sans; a
   neon overprint on a bookish serif. The texture must follow §3's `Character` line.
7. **Tofu.** A beautiful phrase containing a glyph the binary doesn't have.
8. **Word-count creep.** A paragraph that "needs" 30 px to fit and becomes texture.
9. **The name as a product tile.** A 300 px font name *with sales language around it* is
   an ad. A 300 px font name alone, set in the thing being admired, is a specimen — and
   it is what `hero` does. The distinction is the pitch, not the size. The name may hold
   the focal rung; the price, the marketplace and "available now" may not appear.
10. **Camouflage ground.** Blocky hash noise, or smooth noise at too small a scale: the
    texture becomes the loudest thing on the canvas and the type has to fight it. Tooth
    should be *found*, not seen — if you can point at a cell, the scale is wrong.
11. **The blob edge.** A mesh wash whose patch anchors sit inside the canvas draws a
    visible organic boundary. Put every anchor and control point outside the frame.
12. **Rivers.** `kJustify` on a display or script face stretches the word spaces into
    channels. Left-align, or set the copy as discrete lines.

---

## 14. What a run looks like, end to end

The locked production run — Agent 13 STEP 2, inside `/full-workflow`:

1. Read the font binary + `description.txt`; write the `Character` line into the
   brief's required `about` (the seller's own words decide the family — the classifier
   mislabels FineLetter, IronRush and Braewick).
2. Write five fresh headlines (§5 rules) — none from `COPIES`, no overlap between
   pins, none already shipped by another font — and assign one distinct theme plus a
   tone rung per pin. Author it all once as `pins.brief.json`.
3. One command renders: `bin/render-pins --brief …` validates the brief, renders
   `hero`, `set`, `wall`, `phrase`, `full_stack` into `pinterest_1..5`, and enforces
   the checks (§12) as it goes.
4. `visuals/New-Images/pinterest/` (with `pins.brief.json`) is then picked up by
   `/pinterest-prepare`, and `/pinterest-daily` pairs each pin with one of the two
   product links in `buffer.csv` / `pins.csv`. **Uploading to Buffer/Pinterest stays
   the human step; no run claims publication.**

A worked proof that the documented renderer techniques are executable lives in
`vendor/typography-labs/py/verify_doc_recipes.py` (one complete pin, every documented
technique, all checks green) — §13 of the renderer doc carries its last measured
output. It stays in the capability lab; the production path is `bin/pin-studio/`
behind `bin/render-pins`.
