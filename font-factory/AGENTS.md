# Font source, visual, and preparation workspace

This workspace holds selected source fonts, Agent 27 visual drafts, and optional source references. Generated font packages and preparation materials belong under `outputs/font-preparation/{NUM}-{slug}/`.

## Active Codex roles

Before Agent 27 acts, read `../AGENTS.md`, `support-references/TEMPLATE-GUIDE.md`, and `../agents/agent-27-font-image-generator.md`. Before Agent 13 acts, read `../AGENTS.md`, `../agents/agent-13-font-prep-specialist.md`, and `.codex/agents/font-preparer.toml`. The Codex registrations and their canonical specs define the current process; do not follow OpenCode commands or archived workflow directions.

Agent 27 owns the visual handoff in the selected source workspace:

- inspect source metadata, a family-wide preflight, the fact sheet, and every page of the Unicode-mapped atlas for each distinct family style before naming or writing copy;
- save the selected name, visual profile, and source-verified product facts for
  the listing stages in `visual-direction/visual-plan.json`;
- make two white-background font-name lettering references and four complete prompts in `visual-direction/theme.txt`: a primary and a distinctly different alternate direction, each composed separately for 3:2 and 1:1;
- use a font-seeded random selection of 12 eligible support designs from the
  active HTML/CSS catalogue and render each at 3:2 and 1:1; eligible family
  showcases share the pool and are not guaranteed selections;
- do not render Pinterest pins; the old Pinterest template catalogue is retired;
  factual specimen sheets remain Agent 13's deliverable;
- write the manifests, visual QA notes, and ready marker; stop if mechanical validation fails.

Agent 13 owns preparation output, not the creative review drafts:

- keep each source's outline format as its native master: for glyf/TTF input, prepare TTF directly and derive CFF/OTF; for CFF/OTF input, keep OTF and derive TTF; create WOFF from the native master. Store them in separate `OTF/`, `TTF/`, and `WOFF/` folders under a font-named folder in `outputs/font-preparation/{NUM}-{slug}/`;
- create one `{FontName}.zip` containing that folder and all validated format files; do not create WOFF2 or separate Commercial-Use/Personal-Use archives;
- require Agent 13's source-to-output audit for cmap mappings, GSUB/GPOS inventory, HarfBuzz shaping, legacy `kern` pair preservation, and source-format hint preservation; review the reported 9–24 px and 96/200 px raster deltas in `audit-report.md`;
- copy the schema-2 product description to the preparation root's `description.txt` and include its audit reports;
- install all 24 supporting images from Agent 27's handoff for Agent 30, skip
  retired Pinterest templates, and render the final factual specimen sheets;
- leave Agent 27's thumbnails and support designs in `font-factory/fonts/{input-slug}/prepared_visuals/`.

## Source selection and retention

`/full-workflow` uses an exact Saved folder or staged workspace supplied by the user. Stage an exact Saved folder with `--source`. If none is supplied, Agent 27 chooses one eligible `font-factory/Saved/` family at random with `python3 bin/stage_saved_font.py --random`. The helper serializes concurrent selection and moves only root-level OTF/TTF source files into a fresh workspace. Agent 27 may proceed only when its own call reports `RANDOM_SOURCE_CLAIMED`; otherwise it stops rather than adopting another run's workspace.

List available folders and root-level OTF/TTF files when an explicit source choice is needed:

```bash
python3 bin/stage_saved_font.py --list
```

Move only an explicitly selected folder's original root-level OTF/TTF files:

```bash
python3 bin/stage_saved_font.py --source "{saved-folder}"
```

The helper moves the font files unchanged into a fresh `font-factory/fonts/{input-slug}/`, records SHA-256 hashes in `source-import.json`, and refuses to overwrite an unrelated destination. Keep these files in `fonts/` as the durable source of record for checking completed work. Nested repair/output folders and non-font files stay in Saved.

The source workspace is distinct from the preparation output:

```text
font-factory/fonts/{input-slug}/       # original source and Agent 27 review assets
outputs/font-preparation/{NUM}-{slug}/ # newly prepared package and seller handoff
```

## Preparation output and seller image handoff

Agent 13 writes package binaries, one archive, `description.txt`, audit reports, factual specimens, and the 24 support renders plus four Agent-27 thumbnails into `visuals/New-Images/`. It does not alter the artwork, compress seller images, or make videos.

After listings, `/full-workflow` runs Agent 30 to process the prepared image pool when its readiness check passes. The standalone `/font-final-images` command remains available for previously prepared products. Pinterest upload preparation is a separate follow-up stage.
