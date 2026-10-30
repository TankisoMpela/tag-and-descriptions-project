# Pinterest Pin Layout Studio

This is the portrait HTML/CSS layout iteration port for the Pinterest pin templates. Every active design has its own editor page under `templates/<template>/editor.html`; shared drawing, fitted text, controls, and layout reporting live in `shared/`. The artboard is 1000 × 1500 CSS pixels and exports at that size through Chromium.

Open `templates/<template>/editor.html` in Chromium to edit the copy and upload a local font. The active reference-led layouts are `coffee_roaster`, `punk_manifesto`, and `neon_overprint`. Their layouts study composition, palette, hierarchy, and decorative shapes from the supplied pins. Watermarks and source artwork are not carried into the new templates. `green_starburst` and `phrase` are retired from the render set at the user's request; their editor sources are retained for reference.

Render all active designs into one individual-image review folder:

```sh
node font-factory/pin-html/render_gallery.mjs
```

By default this creates a date-stamped folder under `outputs/`. The renderer
refuses to replace existing renderer outputs unless `--overwrite` is supplied;
when overwriting it removes only its named gallery files (or numbered pin
renders in production mode), leaving contact sheets and other files in place.
The gallery includes a manifest with dimensions, source lineage, layout
reports, and links to the individual editors. Retired variants remain out of
production pins.

The local specimen fonts mirror the families used in the prior review set. Upload any other font through an editor's font picker to compare the layouts against it.

## Font workflow production render

Agent 27 renders the 23 active templates individually with the actual primary
font and final font name, rather than using the local specimen defaults:

```sh
node font-factory/pin-html/render_gallery.mjs \
  --mode pins \
  --font "font-factory/fonts/{slug}/{Primary}.otf" \
  --font-name "{Font Name}" \
  --out "font-factory/fonts/{slug}/prepared_visuals/pinterest"
```

This writes `pinterest_1.jpg` through `pinterest_23.jpg` (1000×1500, at most
200 KB each) and `pinterest-template-manifest.json`, including the ordered
template IDs and hashes. Agent 13 copies that verified set to
`outputs/font-preparation/{NUM}-{slug}/visuals/New-Images/pinterest/`. Agent 30
then appends ten image composites and writes the final pin-set manifest for the
Pinterest preparer.
