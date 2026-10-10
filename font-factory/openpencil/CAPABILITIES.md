# OpenPencil capabilities & image-generation foundation — audit reference

This document is the authoritative reference for **what Agent 27 can reliably
produce with OpenPencil**, what the headless render bridge actually does, and
the verified capabilities/infrastructure audit that underpins both. Every claim
here was validated against the installed `@open-pencil` packages (v0.14.0) and,
where marked, by a live headless render test.

Read this together with `README.md` (setup + handoff path) and the two visual
skills (`font-thumbnail-design`, `font-supporting-image-design`). This page is
about the *design surface* and the *foundation*; the skills are about *how to
art-direct*.

---

## 1. The foundation in one paragraph

Agent 27 authors every creative image as **OpenPencil JSX** (a readable source
of truth) plus an **editable `.fig`** compiled from that JSX. A mechanical
bridge (`bin/render_openpencil_font_handoff.mjs`) loads the real project fonts,
loads the authored `.fig` **headlessly** with `@open-pencil/core`, verifies
that each asset contains a declared product font family, and exports the root
frame to a PNG. The compiler is the only helper that executes the authored JSX
to create the `.fig`. No desktop app, no SVG/raster template path, no image
model. The renderer is mechanical: it never chooses a layout, edits copy,
recolors, or repairs an image.

OpenPencil is installed locally as `@open-pencil/cli` + the `@open-pencil/*`
packages under `node_modules`; the headless rendering path uses the **same
pure-JS engine** (`@open-pencil/core`, `@open-pencil/scene-graph`) that the
desktop app uses, so there is no separation between "what the agent authors"
and "what renders."

**Official docs** are the authority for the JSX renderer, MCP server, CLI, and
`eval` scripting: `openpencil.dev/programmable/jsx-renderer.md`,
`.../mcp-server.md`, `.../cli/scripting.md`, `reference/cli.md`, plus the
ecosystem comparison in `openpencil.dev/overview/comparison.md` (see §5A).
This page adds what we **verified against the installed packages** (v0.14.0)
and with live headless renders, on top of those docs.

---

## 2. Reliable JSX design surface (verified to render headlessly)

These construct classes were exercised through the installed renderer and
produced valid output PNGs (600×600 RGBA) with no errors. They are safe for
Agent 27 to use. The full supported prop list lives in
`node_modules/@open-pencil/core/dist/design-jsx/render.js` (`SUPPORTED_PROPS`).

### 2.1 Elements (from `design-jsx/components`)
`Frame`, `Text`, `Rectangle`/`Rect`, `Ellipse`, `Line`, `Star`, `Polygon`,
`Vector`, `Group`, `Section`, `Component`, `ComponentSet`, `Instance`, `Page`.
`View` ∥ `Frame`, `Rect` ∥ `Rectangle`.

### 2.2 Layout & sizing
- **Flex/flow**: `flex="row|col|column"`, `flow/dir="auto|ltr|rtl"`, `gap`,
  `rowGap`, `columnGap`, `wrap`, `justify/justifyContent="start|end|center|between"`,
  `items/align/alignItems`, `grow`.
- **Box model**: `x`, `y`, `top`, `left`, `position`, `w/h` (`'fill'`/`'hug'`
  or number), `minW/maxW/minH/maxH`, `p/px/py/pt/pr/pb/pl`, `rounded`/
  `borderRadius` (+ `roundedTL/TR/BL/BR`), `cornerSmoothing`.
- **Overflow/clip**: `overflow="hidden"` clips children to the frame bounds —
  this is the reliable clip/mask primitive.

### 2.3 Paint (fills / strokes / gradients)
- `bg`, `fill`, `fills` (array), `background`/`backgroundColor`.
- **Gradients** from `design-jsx/paints`: `linearGradient`, `radialGradient`,
  `angularGradient`, `diamondGradient`, and generic `gradient(type, stops)`.
  Stops are `[color, position]` tuples or `{color, position}` objects.
- **Strokes**: `stroke`, `strokeWidth`, `strokeAlign="inside|outside|center"`,
  `strokeDash` (array), `strokeCap`, `strokeJoin`.
- Solid: `solid(color, {opacity, blendMode})`.

### 2.4 Effects (from `design-jsx/effects`)
`dropShadow({color,x,y,offset,radius,spread,visible,blendMode})`,
`innerShadow(...)`, `layerBlur(radius)`, `backgroundBlur(...)`,
`foregroundBlur(...)`. Apply via `effects={[dropShadow({...})]}`.
`opacity`, `blendMode`, `rotation`/`rotate` are also supported.

### 2.5 Text
- `fontFamily`, `fontWeight`/`weight`, `fontSize`, `lineHeight`, `letterSpacing`,
  `textAlign`, `textCase` (e.g. `"UPPER"`), `maxLines`, `truncate="END"`,
  `textAutoResize`, `textDecoration`, `color` (text fill), `stroke` (unicode
  outline effect), per-run style overrides.
- **Real fonts**: the bridge registers the project's actual OTF/TTF before
  rendering (`fontManager.markLoaded`), so `fontFamily="<The Font>"` renders
  with the true glyphs — not a fallback. This is the typography-led edge.

### 2.6 Shapes
`Ellipse`, `Line`, `Star({points, innerRadius})`, `Polygon({pointCount})`,
and `Vector`/paths (inline SVG `<svg viewBox="..." size={n}><path d="..."/></svg>`
is supported inside JSX by `render`). Boolean/path tools exist in the MCP
registry for interactive editing but are not needed for JSX authoring.

### 2.7 Truth about masks
There is a `mask`-style hint in some docs, but the **reliable** masking primitive
headlessly is `overflow="hidden"` on a Frame (clip) — verified. Frames with
`rounded` + `overflow="hidden"` give rounded-clip panels. Do not rely on
alpha-mask semantics that are not exercised by the render bridge.

---

## 3. Verified handoff contract (what the bridge produces)

`bin/render_openpencil_font_handoff.mjs` consumes a **visual plan** and,
per asset, loads the `.fig`, registers real fonts, exports the named root frame
to PNG, and copies source `.fig`/`.jsx`. It writes `openpencil-render-report.json`
(per-asset: `asset`, `ratio`, `source`, `jsx`, `output`, `page`, `root` id/name/
w/h, `nodeCount`, `textNodes` with `fontFamily`, `fontSize`, bounds,
`fontFamilies`, `featuredFontFamilies`, and mechanical checks including
`featuredFontPresent`). It never edits nodes.

The handoff must contain:
- `prepared_visuals/3x2/thumbnail_main.png` + `promo_N.png`
- `prepared_visuals/1x1/thumbnail_main.png`, `thumbnail_japanese.png`, `promo_N.png`
- four factual specimen PNGs (two families × two ratios)
- matching `openpencil/3x2/*.{fig,jsx}` and `openpencil/1x1/*.{fig,jsx}` sources
- `visual-handoff-manifest.md`, `VISUAL-HANDOFF-READY.md`

Validation: `bin/validate_font_visual_handoff.py` + the `openpencil` CLI
(`info`, `tree`, `analyze`, `lint`).

---

## 4. CLI inspection & lint behavior (verified)

These work headlessly on a generated `.fig`:
```sh
npx --no-install openpencil info <file>.fig --json
npx --no-install openpencil tree <file>.fig --page '<Page>' --depth N        # note: --json shape differs; use plain for readability
npx --no-install openpencil analyze typography <file>.fig --json
npx --no-install openpencil lint <file>.fig --preset strict
```

`lint --preset strict` on fresh art emits **warnings** (`no-hardcoded-colors`,
`text-style-required`, `font-weight-not-found`), **not errors**. These warnings
are expected and acceptable for art-directed poster work; they do not block a
handoff. (If the agent wants clean lint, it can bind palette colors to design
variables via `defineVars`/`designVar` — optional, cosmetic.)

---

## 5. Infrastructure audit — findings & the headless-MCP story

> **Official docs** (fetched `openpencil.dev`, v0.14.0): `programmable/mcp-server.md`,
> `programmable/jsx-renderer.md`, `programmable/cli/scripting.md`,
> `reference/cli.md` are the authoritative references. This section reconciles
> those docs with what we verified empirically in `node_modules`.

We audited whether the **desktop app** is required, because the app crashed on
this machine with `Could not create default EGL display: EGL_BAD_PARAMETER`
(Tauri/WebKitGTK GPU issue). Findings:

1. **The MCP tool surface is documented at 90–91 tools.** `@open-pencil/mcp`
   ships two binaries:
   - `openpencil-mcp` → `stdio.mjs` — a stdio **bridge** that forwards JSON-RPC
     to a running server socket. Official docs: "The stdio server discovers the
     running OpenPencil app automatically… Make sure the desktop app is open
     with a document loaded."
   - `openpencil-mcp-http` → `index.mjs` — the actual **MCP server** (stdio
     clients spawn it, or run standalone). It listens on a Unix socket (+
     optional TCP via `PORT`), writes the `mcp.json` discovery file, and
     registers the tool surface. **Documented at 90–91 tools**; our live bridge
     measured **110** (the extra are document-lifecycle + `eval` +
     gap/query/export tools the doc's curated list omits). The doc group:
     Document, Read, Create, Modify, Structure, Vector Path, Export,
     Viewport, Variables, Analyze, Diff, Navigation, and `eval`.

2. **The server has no document engine of its own.** It registers tool *schemas*
   and routes commands over a WebSocket to a **registered "browser" backend**.
   In the normal flow that backend is the running desktop app (its `figma`
   facade over an in-memory `SceneGraph`). Without any backend, document work
   returns `"OpenPencil app is not connected"` (we reproduced this).

3. **Headless paths exist that don't need the desktop GUI.**
   - **Documented, cleanest:** the **CLI `eval` command** runs JavaScript with a
     Figma-compatible `figma` global **against a `.fig` file directly** —
     `openpencil eval assets.fig -c "return figma.currentPage.children.length"`,
     with `--write`/`--output` to persist. No app, no MCP server, no custom
     engine. This is the official headless scripting surface and is the
     recommended foundation for any headless document work (batch edits,
     inspection, fixture setup). The repo wraps it in `bin/openpencil_eval.sh`
     (verified: `return figma.currentPage.name` → `"Page 1"` on the Troska
     text-study document). **Version pinning:** `@open-pencil/cli` is pinned to
     **exact `0.14.0`** in `package.json` (no caret) so this verified contract
     cannot silently drift; bump the pin and re-run the
     `npm run openpencil:text-studies` smoke test when upgrading.
   - **MCP stdio over RPC** requires an attached backend; the documented client
     for that backend is the desktop app.
   - **MCP `eval` tool** is available over **stdio** but **disabled in HTTP
     mode** (per official docs), and requires `OPENPENCIL_MCP_EVAL=1` on the
     bridge process.

4. **We proved the desktop app's engine is replaceable — but the CLI `eval`
   path makes a custom engine unnecessary.** We connected a small headless
   WebSocket engine (registered as the backend) to `openpencil-mcp-http`, and
   `new_document`/`list_documents` **succeeded** through
   `bridge → server → headless engine`, confirming the app's document engine is
   just a `figma` facade over the same pure-JS `SceneGraph` we use. However,
   because the CLI `eval` command already provides official headless document
   scripting against a file, **building a custom engine is not worth it**; the
   CLI `eval` path covers the same need more simply.

5. **Decision (current): keep the proven render-bridge foundation.** Agent 27
   authors JSX; the bridge renders to PNG with real fonts. This is
   deterministic, already validated end-to-end (gradients, masks/clip, flex,
   effects, text all render), and needs no server, app, or engine process. The
   MCP interactive loop, the CLI `eval` scripting path, and a headless engine
   all remain **documented future options** — not required for Agent 27's
   font-image work.

### Capability test reference
A live diagnostic harness rendered five construct classes (gradients, masks/
clip, flex layout, shapes+effects, text features) headlessly:
`gradients`, `masks-clip`, `flex-layout`, `shapes-effects`, `text-features` —
each produced a valid 600×600 PNG. The rendered outputs landed under
`/tmp/opencode/capability-check/` and a project copy under
`outputs/image-review/capability-check/`. These are **diagnostic proofs**, not
marketplace artwork.

---

## 5A. OpenPencil vs. Penpot / Figma / "pencil.dev"

The official docs include a dedicated architecture comparison —
`openpencil.dev/overview/comparison.md` — but it is **OpenPencil vs Penpot**
(not "pencil.dev"). Clarifying the naming:

- **There is no notable "pencil.dev" design tool.** The open-source design tool
  people mean is **Penpot** (`penpot.app`). There are also legacy, largely
  unmaintained tools named "Pencil" (e.g. the old Evolus "Pencil Project" UX
  prototyping tool, pencil.evolus.vn) — unrelated to OpenPencil and to Penpot.
- **OpenPencil** is a single-process, local-first, open-source (MIT) editor:
  ~26K LOC TypeScript/Vue, Tauri desktop + browser, native Figma `.fig`/Kiwi
  codec read, Figma-compatible scene graph, headless CLI/MCP/JSX/eval automation,
  P2P collaboration. Optimized for **instant local performance and scriptability**.
- **Penpot** is a full-stack, **server-hosted** platform: ~299K LOC across
  Clojure/ClojureScript/Rust/SCSS, Docker + Postgres + Valkey + MinIO +
  JVM + headless-Chromium exporter, its own `.penpot` ZIP/JSON format (no
  native `.fig` import), a plugin ecosystem, and **no headless scripting/MCP
  surface**. Optimized for **multi-user team deployments**.
- **Figma** is the closed, commercial baseline OpenPencil is compatible with.
  OpenPencil reuses Figma's Kiwi binary format, GUIDs, and clip/protocol, so it
  can open `.fig` files and paste Figma clipboard data — but Figma's own MCP
  server is read-only and its design format is proprietary/cloud-hosted, whereas
  OpenPencil is fully open, local, and writable/scriptable.

**Why this matters for the font-image pipeline:** OpenPencil's headless
automation (JSX + CLI `eval` + MCP) is exactly what Agent 27 relies on; Penpot
has no equivalent headless scripting or MCP surface, and its file format isn't
`.fig`, so it is **not** a drop-in substitute for this project.

---

## 6. What Agent 27 should and shouldn't reach for

**Use freely (verified):**
- Real-font typography (`fontFamily` bound to the registered project font).
- Flat premium-font fields: solid fills, high-contrast ink on paper tones.
- Frames + `overflow="hidden"` clipping, rounded panels.
- Linear/radial/angular gradients for subtle depth (use sparingly — premium
  font listings lean on clean flat fields, per the YouWorkForThem audit).
- Drop/inner shadows, layer blur, rotation for composition, letter-spacing /
  tracking, uppercase forcing.
- Fine size/positioning via absolute `x`/`y`/`w`/`h` for precise typography-led
  layouts.

**Use carefully / sparingly:**
- Heavy photo-scene or complex-mask compositing — premium font listings are
  typography-led on clean fields; this is a style constraint, not a cap.
- Near-synonym duplicate text nodes or redundant swatches (keep it clean).
- Brand renames: `font_name` may be the public name, but
  `font_files[].family` and `featured_font_families` must match the
  OpenPencil text node family that the bridge registers and verifies.
  Optional non-product label faces belong in `auxiliary_font_files`; they are
  rendered if supplied but do not satisfy the product-font check.

**Do NOT do (agent scope):**
- Do not call image-generation models for these deliverables.
- Do not invent a fallback composition or template; each ratio is authored
  independently (see `font-factory/AGENTS.md`).
- Do not modify font binaries or run marketplace agents.

---

## 7. Quick command reference

```sh
# author → compile JSX to editable .fig
node bin/compile_openpencil_jsx.mjs --source <file>.jsx --output <file>.fig

# render a full handoff with real fonts (mechanical bridge)
python3 bin/rasterize_font_visual_handoff.py \
  --plan <visual-plan.json> --output <prepared_visuals>

# headless document scripting against a .fig file (official CLI `eval`, no app)
npx --no-install openpencil eval <file>.fig -c "return figma.currentPage.children.length"
npx --no-install openpencil eval <file>.fig -c "...mutations..." --write   # -o for new file
bin/openpencil_eval.sh <file>.fig "return figma.currentPage.children.length"   # repo wrapper

# inspect / lint
npx --no-install openpencil info <file>.fig --json
npx --no-install openpencil tree <file>.fig --page '<Page>' --depth 4
npx --no-install openpencil analyze typography <file>.fig --json
npx --no-install openpencil lint <file>.fig --preset strict
```

> Future (documented, not built): an interactive MCP tool-call design loop via
> `openpencil-mcp-http` + a headless `figma`-facade engine. Per §5, the official
> **CLI `eval`** command already covers headless document scripting against a
> file, so a custom MCP engine is unnecessary for Agent 27. Either surface is a
> future option; the current bridge-based foundation remains the default.
