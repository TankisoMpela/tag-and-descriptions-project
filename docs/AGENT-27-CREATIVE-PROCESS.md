# Agent 27 — the creative process

How the font image generator gets from "here is a font" to a finished set of
image briefs: the placeholder images and the theme paragraphs that describe them.

This is the **creative** account, not the technical one. It covers how concepts
are found, how each image's world is invented, how the words are chosen, and what
separates a brief from a layout description. The rendering mechanics, the plan
schema and the validation belong in `docs/FULL-WORKFLOW-REFERENCE.md`.

---

## 1. What this agent actually authors

Worth stating plainly, because it shapes everything else.

Agent 27 does **not draw the placeholder PNGs**. The renderer draws them: heavy
white-screen typography with the exact copy placed where the brief says, so the
seller has something readable to hand a later image model.

What the agent authors is the **concept**:

| It authors | It does not author |
|---|---|
| the complete creative brief for every image (which becomes `theme.txt`) | the pixels |
| the phrase/concept ledger — copy, buyer job, visual event, crop | `art-direction.md` (derived) |
| the plan's structured fields — copy, layouts, placements, palette | `image-notes/` (derived) |
| `candidate-review.md`, when a real decision was uncertain | the manifest or marker (renderer) |

The boundary the spec draws: *"Agent 27 conceptualizes the finished image in
theme.txt, the phrase/concept ledger, and the image notes. The PNG renderer does
not draw that artwork; it creates a clean typography-only placeholder… Never
judge the white placeholder as the final visual design, and never let the
placeholder renderer invent the concept."*

So the placeholder is a **stand-in for the composition**, not the composition.
The brief is what carries the idea forward.

**It also cannot see.** There is no vision or OCR in this runtime. The agent
never inspects a glyph, a reference image, or the PNG it caused to exist. That
constraint is not a limitation to route around — it is the reason the process is
built the way it is. It cannot look at the font, so it must *reason* about the
font from verified facts, then invent a world the font could live in.

---

## 2. The one rule everything else serves

> **The composition is an event, not a grid. The font is the protagonist.**

Every insistence below — action verbs, physical events, proving statements,
"if the phrase changes the image must stop making sense" — is a way of enforcing
that single idea.

The failure mode this exists to prevent is *background-only design*: a tasteful
colour field, a decorative rule, a circle, "premium editorial warmth", with text
sitting on top. The spec calls this out as the cardinal sin and names a real
example: the old `8-Retrofest` theme, with its centred name-only thumbnail and
interchangeable neon shapes, is documented as a **negative example** — *"the
exact background-only/template failure this workflow must prevent."*

The test that separates a concept from decoration:

> If you can swap the shape for any other shape and the composition still works,
> the shape is confetti. If you can swap the phrase for another phrase and the
> composition still makes sense, the concept has failed.

---

## 3. Stage A — Intake

The agent works from four things, and no others:

1. **The font name** — supplied, or decided under the naming policy.
2. **The description** — the seller's own language about the font.
3. **Verified facts from the fact sheet** — metrics, coverage, OpenType features,
   and the exact shaping of proposed phrases.
4. **Buyer use** — what someone is actually trying to make.

Two things it must resist here.

**It must not turn facts into inspiration.** The fact sheet tells it that a font
has swashes, a high x-height, no Japanese coverage, a `salt` feature. Those facts
*constrain* what may be claimed. They do not suggest an image. *"Machine font
inspection can prevent unsupported claims, but cannot tell the agent what the
font looks like and must not be treated as a visual art director."*

**It must not invent.** No photography, no illustration style it cannot deliver,
no language support, no OpenType feature, no buyer use case that was not
supplied or verified. If the fact sheet shows no Japanese coverage, no image may
imply it.

The fact sheet's shaping check earns its place here: if shaping a headline
returns a different glyph count than characters — a ligature, a substitution —
the agent knows before it trusts that headline. A word that silently changes
under shaping is a word it cannot put in a brief blind.

---

## 4. Stage B — Identity to intention

Before writing anything about any image, the agent privately answers six
questions. This is the decision system that stops the work from starting at
colour.

1. **Identity.** What personality, world, attitude or cultural feeling does the
   name and description establish? In the seller's language, not a category
   label — not "elegant serif" but whatever the description actually says.
2. **Intention.** What should a buyer feel or understand *immediately*? One
   primary impression. Not a list of benefits.
3. **Visual question.** What could the image make *happen* so that identity and
   intention become visible without extra explanatory text?
4. **Thesis.** One decisive answer, stated as an event or a relationship between
   the lettering and the graphic world. It must be usable even though the agent
   cannot see the glyphs.
5. **Composition.** Only now: medium, scale, lockup, spatial tension, palette.
6. **Payoff.** What does the finished image prove about the font? **If the same
   thesis would work for another font name and description, discard it.**

Then it generates **three private theses** — genuinely different intentions or
kinds of visual event, *not* three colour variations or three prop swaps — and
selects the clearest one. Not recorded, not compared across sessions: the
decision is self-contained, taking direction only from this product.

The order matters. Composition comes fifth, after the thesis. If composition
comes first, you get a layout looking for a meaning.

---

## 5. Stage C — The generative grammar

This is the engine. Six steps, in order, never skipped.

### Step 1 — Meaning first

> *Ask: what is this phrase actually about visually?*

Not "what style should it have?" The phrase has semantic, emotional or physical
content. Extract **that** before touching colour, layout or shape. State the
phrase's meaning in your own words — do not reach for a familiar category.

### Step 2 — Extract a visual metaphor or small illustrated world

Turn the meaning into a **physical, renderable event**. Not a mood, not a
stock-scene category — an event invented for this phrase. Ask what changes, what
causes the change, and how the font's verified construction makes that change
visually necessary.

### Step 3 — Find a font-specific behaviour

> *What characteristic of this typeface makes that metaphor work?*

Serif terminals, contrast, swashes, italic angle, ligatures, unusual counters,
capitals, proportions, ball terminals, bracketed curves — whatever the font
genuinely has. The metaphor must be *enacted through the font's own
construction*, not through generic graphics laid beside it.

### Step 4 — Turn that into a physical event

Not:

> "use elegant geometric accents"

But:

> "a narrow crimson stroke enters from the upper-right, crosses the S,
> disappears behind its lower bowl, then exits the frame"

Now there is something to render. The graphic element **participates** in the
concept. It is not decoration near text.

### Step 5 — Only then choose supporting graphics

> *If removing the rectangle makes the concept stronger, remove it.*

Shapes earn their existence by participating in the phrase's idea or
demonstrating a typographic property. Anything else is confetti.

### Step 6 — Compose around the event

Typography and image must be inseparable. Replace the phrase and the composition
should stop making conceptual sense. That is the proof the concept is tied to the
phrase rather than to a template.

---

## 6. Stage D — Phrase and copy decisions

The copy is chosen with the concept, not after it. The spec is explicit:

> *"Do not invent a phrase first and attach a generic theme later."*

**Thumbnails.** The only text is the **font name**, stacked as two lines — first
letter or word on top, second below. No subtext, tagline, supporting phrase or
label. The name is the entire typographic subject.

**Promos.** Each has **exactly one** dominant readable phrase. No secondary
blocks, no taglines, no supporting copy. And the phrase must not be the font name
— the name belongs only in the thumbnails.

Each promo phrase must be a **realistic use-case headline**: something a buyer
would commission. A magazine masthead, a book cover line, a poster heading, an
editorial subtitle, a brand tagline, a quote. Each promo shows the font
performing a **different job**, and the agent invents these phrases fresh for
every font — they are not fixed strings.

**Length.** 1–4 words is the working range. Five words only when the phrase
genuinely needs it. Six to eight once in the whole set, only as a deliberate
long-phrase legibility proof. At least five of eight promos must be 1–3 words,
and no more than one may exceed four. A phrase is not a sentence.

**Words are indivisible.** Never author a phrase that requires splitting,
clipping or pushing a word outside the safe area. If the renderer cannot honour
the placement at a safe size, **shorten the phrase or redesign the placement** —
never accept a shrunken or clipped placeholder.

Explicitly banned as headline filler: `Brand Identity`, `Create Beautifully`,
`Your Story Matters`, `The Art of Elegant Lettering`, `Handcrafted with Care`,
`Forever Begins Here`, and close variants. A buyer job like "packaging" or
"wedding" belongs in the private ledger; it is not sufficient as a visible
headline.

**Placement is a creative decision, not a default.** Centring everything makes
the campaign look like a template. The spec lists the moves worth rotating:
cropped into the upper-left leaving the lower-right open for action; pushed to
the lower-right with the upper space dominated by an event; split across two
lines with a shape sliding between them; stretched across the full width at
baseline; isolated as one oversized cropped letter; stacked in changing scales
so the last line slips sideways into a colour field; placed slightly off-centre
for asymmetric tension with a graphic element.

Placement exists to make room for the event: a line threading through terminals
needs space, a shape pushing into a letter needs the letter positioned where the
collision is visible. **Both thumbnails stay centred** — strategic placement is a
promo move, where moving the phrase creates room for the artwork.

---

## 7. Stage E — Writing the brief

The brief is written as a scene happening now, not a specification.

> *Describe a scene that is happening right now, as if you are looking at the
> finished image and telling someone what you see.*

One continuous paragraph. No bullets, no sub-headings, no metadata prefix. It
opens with a **newly chosen format or medium** belonging to this concept — never
a canned opener like "Flat graphic type poster" or "editorial panel" — and then
drops immediately into the present-tense scene.

Every entry must layer **four to six** of these:

1. the format or medium, newly chosen for this concept;
2. a dynamic action or event involving the typography;
3. a colour-role relationship — what the colours *do*: interrupt, thread,
   contrast, anchor, collide, frame;
4. a crop, spatial disruption or text effect necessary to this concept;
5. a type-treatment observation — what the construction or personality *does* at
   this scale: serifs surviving contrast, entry strokes becoming focal points,
   rhythm exposed through repetition;
6. a closing proving statement;
7. a concrete contextual motif that belongs to the phrase, not a generic
   geometric accent.

### Verb energy

Every sentence needs at least one active verb. The composition should feel like
something is *happening*.

**Banned as static:** sits, fills, breathes, is centred, is positioned, is
placed, set on, occupies, located.

**Preferred:** threads, snaps, cuts, interrupts, loops, drifts, restores, slips,
pushes, balances, traces, exits, slides, continues, anchors, collides, reveals,
exposes, frames, extends, crops, overlaps, weaves, punches, punctures, strikes.

At most one static verb per entry.

### Colour language

Named colours only — **never hex codes**, which read as CSS rather than
creativity. And colour is described by what it *does*.

> **Bad:** "a deep navy (#0D1B2A) background with a thin gold (#D4A853) rule"
> **Good:** "a vermilion diagonal cuts through the word and a cobalt rectangle
> interrupts the lower edge"

A cobalt panel is *cutting across*. A vermilion stroke *traces* a terminal. A
blush-to-ivory gradient *sits behind* the lettering.

### Spatial language

Write composition as something that *happens to* the typography, not as a grid.

> **Bad:** "the hero word dominates the upper two-thirds, the rule sits in the
> lower third, negative space breathes on the right"
> **Good:** "crop the title across a near-black field with one warm-white
> counterfield so the serif contrast becomes the visual event"

The space is a stage where events occur.

### Text effects

One deliberate effect is allowed and encouraged, where the font's construction
earns it: a letterform cropped at the frame edge revealing counter detail, a
colour field cutting through the baseline, a rule passing through the ascenders,
a repeated glyph pattern breaking at a focal point, a watermark showing serif
survival at low contrast. The effect must be specific to verified traits and must
not obscure legibility.

### The closing

Every entry **ends with a proving statement** — what the composition achieves for
the font's market positioning. This is what separates a brief from a layout
description.

> "…proving the font can [buyer job]", "…showing how the [feature] survives
> [context]", "…demonstrating the font's [quality] at [scale]", or an em-dash
> clause: "— a [composition type] that proves [positioning]"

---

## 8. Stage F — The thumbnail quality gate

The thumbnails are **not** treated like the promos. They are the first product
impression, so they carry the strictest rules in the document.

Each thumbnail brief must explicitly author all five of these:

1. one **concept hook** tied to the identity, description, era or naming anchor;
2. one visible thing **happening or changing**, invented for this font;
3. the exact **hero lettering treatment** — what the name is doing, its scale,
   crop, placement, and its relationship to the action;
4. one deliberate **contrast or framing device** that makes the lettering pop at
   thumbnail size;
5. a restrained **supporting detail** that makes the concept feel authored rather
   than like a generic backdrop.

**Rejected:** adjective stacks ("premium, editorial, textured, warm"), anything
that merely repeats the global theme sentence, and anything that could advertise
any font. The action must **frame or activate** the lettering, never cover it.

### The name is not a scene

A font name is not a phrase with a literal scene. `Silken Flourish` must not
become a desk, a pen, paper, an ink bottle, or a luxury tabletop photograph. The
name's association is **translated into a flat visual subject or typographic
event** — graphic art, not an object staged in a room.

Before accepting either thumbnail, the agent privately answers: *what is the
concrete illustrated subject or typographic event, what is changing, and which
verified identity makes it necessary?* If the answer is only a surface, material,
palette or atmosphere, the direction is rejected and derived again.

### The thumbnail medium rule

Both thumbnails must be **flat, straight-on 2D graphic or illustrated
compositions**. Photography and real-life scenes are forbidden.

Explicitly rejected: rooms, desks, landscapes, tabletops, lifestyle scenes,
product photography, photographic texture, marble, wood, fabric, leather, foil,
plaster, concrete, glass, acrylic, realistic paper, realistic ink splashes,
photographic grain, cast shadows, lens blur, depth of field, reflections, and
pseudo-real premium material treatments.

The words `paper`, `ink`, `silk`, `copper`, `velvet` may describe a **flat graphic
colour or a drawn motif only** — they never authorise a realistic surface or
object. The test: *if the prompt could be photographed as a tabletop product
shot, it has failed, even when it says "flat graphic" elsewhere.*

The background must be a **designed image field** — an illustrated world, a
pattern, a diagram, a collage, a typographic construction — not a physical
surface for the name to sit on.

This is a thumbnail-only constraint. It does not force the promos into the same
medium.

### The example of the failure

The spec gives a bad/good pair to show the difference structurally:

- **Bad:** "[Colour] on [colour] — the stacked font name fills the landscape
  frame at display scale, with a fine [colour] rule beneath." — a layout
  specification with no action and no event; it could describe any font.
- **Good:** name a newly chosen medium, describe one specific action that changes
  the relationship between the lettering and its surroundings, identify the
  supplied identity involved, state what the image proves.

And a standing warning not to drift back into the comfortable defaults: cream
paper, charcoal-and-gold, cardboard, foil, stationery, packaging, marble, fabric,
or a tasteful still life. These are not concepts. And do **not** force every font
into a poster — an oversized crop, a colour-field collision, repeated glyph
structure, a letterform-shaped frame, directional movement, an ornamental
composition, or a quiet specimen space may all be right when the evidence
supports it.

---

## 9. Stage G — Variety

Every image must feel substantially different from every other. Two kinds of
variety are named, and the spec ranks them:

> **Semantic differentiation matters more than colour differentiation.**

Changing the ground from charcoal to navy while keeping "text + one shape" is
not variety. Each promo must derive its mechanism from a **different aspect of
the phrase's meaning**, a different intention, or a different buyer job.

The concrete targets:

- Every promo uses a **distinctly different dominant hue family**. The thumbnail
  palette does not repeat in any promo.
- Each variant introduces **at least two materially new visual decisions**.
- Across the eight promos, **at least six materially distinct visual strategies**,
  measured by changes in spatial logic, density, scale relationship, movement,
  surface treatment and type/art interaction — *not* by swapping decorative
  motifs. And explicitly: do not fill a checklist of named strategies.
- No repeated concept, palette emphasis or composition layout.

Coherence does **not** come from repeating a setting. It comes from
*"the font's letterforms, typography, authored copy, and brand quality."* The
`supporting_image_theme` sentence is a **loose inspiration anchor**, not a rigid
art bible — it may set mood, but it does not require every image to repeat the
same world, palette or motif.

The result should read as a thoughtfully art-directed campaign, not ten
near-identical prompts.

**Safety floor across every variant:** flat-2D always; no live 3D environment,
photograph, room/landscape/tabletop, staged product shot, realistic face, hand
holding a tool, stock-photo composite, AI raster imagery, clipart, watermark or
badge overlay; no text below 16 pt at render scale; and no colour pair failing
4.5:1 contrast at the dominant text area.

---

## 10. Stage H — The private ledger

Before writing any theme paragraph, the agent records each image privately with:

> the exact phrase, word count, buyer job, identity intention, semantic idea,
> visual event, artwork/world, placement, and ratio-specific crop.

This is the spine of the whole process. The theme paragraph and the matching plan
entry must describe **that same phrase and that same event**. The ledger is what
makes it impossible to write a phrase and then attach an unrelated theme — the
event was already decided before the writing began.

The agent also keeps **roles distinct** across the set — a concise font-specific
`role` or buyer question per promo — so no two images are doing the same job.

One ledger, then one plan. Both ratios are designed **independently**: 3:2 may
exploit horizontal reading, long wordforms, side-by-side relationships or
directional movement; 1:1 may exploit a centred monogram, a stacked lockup, a
crop into a decisive letter, or a compact typographic system. *"These are
separate compositions, not one master artboard cropped or padded twice."*

---

## 11. Stage I — Banned patterns

Eleven prohibitions, each closing a specific failure the workflow has seen:

1. **No metadata prefix.** The paragraph *is* the brief.
2. **No `shared constants:` lines.** The format constraint is stated once in the
   opening phrase, not repeated per entry.
3. **No hex codes.** Named colours only.
4. **No layout-ratio language in the brief.** "3:2 landscape", "1:1 square" belong
   in the plan's ratio layouts.
5. **No specification closings.** Never end with "Clean, authoritative, no
   decoration" or "The composition is a centred vertical lockup." End with what it
   proves.
6. **No repeating the same colour scheme.** Every promo needs a different dominant
   hue family.
7. **No more than one static verb per entry.**
8. **No generic shapes as decoration.** If swapping the shape for any other shape
   leaves the composition working, it is confetti.
9. **No template compositions.** If two different phrases produce the same layout,
   the concept has failed.
10. **No "editorial panel" or "luxury brand" defaults.** Do not fall back to
    tasteful premium aesthetics when the grammar produced something more specific.
11. **No background-only concept.** A different colour field, paper grain,
    gradient or abstract shape is not artwork.

---

## 12. How `theme.txt` comes into being

The agent **does not write `theme.txt`**. It writes each image's brief into that
image's `theme_variant` field in the plan, one single paragraph per image. The
renderer derives `theme.txt` from those fields — one `##` block per image, in
order — and a hand-written `theme.txt` is overwritten on the next render.

That is deliberate. Before it, the agent hand-wrote `theme.txt`, `image-notes/`
and `art-direction.md` alongside the plan they restated: roughly 5,900 output
tokens per product, and they had **drifted apart** — one product's `theme.txt`
and its design note described *different copy for the same promo*.

So the creative writing happens **once**, in `theme_variant`, and everything else
is a view of it. The brief you see in `theme.txt` is exactly the paragraph the
agent composed under the rules above.

The consequence for editing: if a derived document reads wrong, **fix the plan
field that produced it**, never the rendered file.

Worked shape of one entry, as the agent authors it:

```text
## promo_1
[one continuous paragraph: a newly chosen medium, a present-tense event, the
lettering's role in it, colour as actor, a type-treatment observation, and a
closing proving statement]
```

And the whole set:

```text
## thumbnail_main        ## promo_1   …  ## promo_8
## thumbnail_japanese
```

Thumbnails stay centred and name-only; promos carry one use-case phrase each and
may use strategic placement.

---

## 13. The examples, and how to use them

The spec carries worked examples — a modern serif, a brush/grunge script, a
blackletter — and a bad/good pair. Their status is stated three times in
different words, because it is the easiest thing to get wrong:

> **Structure only — never copy the font type, colours, or style from these.
> Extract the writing pattern, then invent your own concept from the actual
> font's traits, name, and buyer.**

And more forcefully:

> **Do not use prior campaigns or the examples in this document as a motif
> library. They are evidence of a quality bar only, not ingredients to
> recombine… Invent a relationship that could not have been predicted from this
> document.**

The banned-default list exists for the same reason: botanical, storybook,
celestial, stationery, ticket, label, map, panel, ribbon, foliage, border,
flourish-line, repeated-glyph. These are the shapes a model reaches for when it
is not actually thinking about the font.

The good example shows the pattern in action, on a modern serif:

> "Flat identity poster built from an oversized 'Brand Identity' lockup: the tall
> B and d act as structural uprights while a [colour] rectangle pushes in from the
> left edge and interrupts the negative space between the two words; a single
> [colour] dot sits inside the A's counter — the same ball-terminal mark from the
> thumbnail — so the identity system feels authored and repeatable across
> contexts."

Why it works: the phrase drives the concept; the B and d are *doing a job*
(structural uprights); the rectangle *interrupts specific space*; the dot
*references the thumbnail's identity mark*. Swap the phrase and it stops making
sense.

The extractable pattern is the chain, not the content:

> **format tag + dynamic action + colour-as-actor + spatial disruption +
> type-treatment observation + proving statement**

Then the content comes from the font in front of you.

---

## 14. The self-check before handoff

The agent's own review, in its own terms:

- Would this thesis work for a different font? → discard it.
- Is the concrete subject nameable without borrowing one from the document? →
  if not, discard and derive again.
- Does the phrase change the image? If another phrase fits the same composition,
  the concept has failed.
- Is every element establishing hierarchy or concept? Anything that only
  decorates gets removed.
- Does it survive being read at thumbnail size?
- Would it photograph as a tabletop product shot? → it has failed.
- Is it a different hue family and a different mechanism from every other image?
- Does every entry end in what it proves?

Only then does the writing get committed to the plan.

---

## 15. The whole process, in one line

Name and description → what the font *is* → what a buyer wants from it → a
metaphor → the font's own construction enacting that metaphor → a physical event
→ copy that could belong to no other font → placement that gives the event room →
a paragraph describing it as a scene happening now → a closing that says what it
proves. Ten times, in ten different worlds, then handed to the renderer.
