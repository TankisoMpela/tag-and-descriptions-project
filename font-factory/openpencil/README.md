# OpenPencil setup

> **Capabilities & foundation audit:** see `font-factory/openpencil/CAPABILITIES.md`
> for the verified JSX design surface, handoff contract, CLI/lint behavior, and
> the headless infrastructure audit (including why the desktop app is not
> required for this pipeline).

OpenPencil is installed locally as `@open-pencil/cli` and is available through
the repository's `openpencil` binary:

```sh
npx --no-install openpencil --help
npx --no-install openpencil --version
```

The Troska text study is generated without the desktop editor:

```sh
npm run openpencil:text-studies
```

The generator uses OpenPencil's JSX scene-graph renderer, registers the two
local Troska font files for the headless render, writes an editable `.fig` and
the JSX source, and exports the gallery plus individual 3:2/1:1 PNGs. This is
a capability study, not a production art direction or a claim that every
sample is finished marketplace artwork.

The generated files are under:

```text
font-factory/openpencil/examples/troska-text-studies/
```

OpenPencil's stock CLI can inspect the document and run structural checks:

```sh
npx --no-install openpencil info font-factory/openpencil/examples/troska-text-studies/troska-text-studies.fig --json
npx --no-install openpencil tree font-factory/openpencil/examples/troska-text-studies/troska-text-studies.fig --page 'Text Studies' --depth 2 --json
npx --no-install openpencil analyze typography font-factory/openpencil/examples/troska-text-studies/troska-text-studies.fig --json
npx --no-install openpencil lint font-factory/openpencil/examples/troska-text-studies/troska-text-studies.fig --preset strict
```

The stock CLI's separate headless export process does not currently receive
project-local OTF/TTF files. The generator therefore registers the real font
data in the OpenPencil core before rendering. This is an explicit setup step,
not a fallback to another drawing system.

## Font handoff path

Agent 27 authors each creative image as its own OpenPencil JSX and `.fig`
source. The repository supplies two mechanical bridges:

```sh
node bin/compile_openpencil_jsx.mjs \
  --source font-factory/fonts/{slug}/visual-direction/openpencil/3x2/thumbnail_main.jsx \
  --output font-factory/fonts/{slug}/visual-direction/openpencil/3x2/thumbnail_main.fig

python3 bin/rasterize_font_visual_handoff.py \
  --plan font-factory/fonts/{slug}/visual-direction/visual-plan.json \
  --output font-factory/fonts/{slug}/prepared_visuals
```

The second command renders every separately-authored source to separate PNGs,
copies the `.fig`/JSX sources, registers the project's actual font files, and
writes `openpencil-render-report.json`. It also runs the factual specimen
renderer. It never chooses a template, changes copy, recolors, crops, or
repairs an image. Old SVG handoffs remain a compatibility path only.
