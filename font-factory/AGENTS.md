# Font source, visual, and preparation workspace

This workspace holds selected source fonts, Agent 27 visual drafts, and optional source references. Generated font packages and preparation materials belong under `outputs/font-preparation/{NUM}-{slug}/`.

## Active Codex roles

Before Agent 27 acts, read `../AGENTS.md`, `support-references/TEMPLATE-GUIDE.md`, and `../agents/agent-27-font-image-generator.md`. Before Agent 13 acts, read `../AGENTS.md`, `../agents/agent-13-font-prep-specialist.md`, and `.codex/agents/font-preparer.toml`. The Codex registrations and their canonical specs define the current process; do not follow OpenCode commands or archived workflow directions.

Agent 27 owns the visual handoff in the selected source workspace:

- inspect source metadata, a family-wide preflight, the fact sheet, and every page of the Unicode-mapped atlas for each distinct family style before naming or writing copy;
- save the selected name, visual profile, and source-verified product facts for
  the listing stages in `visual-direction/visual-plan.json`;
- make three white-background font-name specimens and three complete prompts in `visual-direction/theme.txt` for the 3:2 main image, the independent square main image, and the storefront square;
- use a font-seeded random selection of 13 eligible support designs from the
  active HTML/CSS catalogue and render each at 3:2 and 1:1; include every
  family showcase when the source has real sibling styles;
- render the four factual specimen previews and all 23 active Pinterest templates with the supplied font;
- write the manifests, visual QA notes, and ready marker; stop if mechanical validation fails.

Agent 13 owns preparation output, not the creative review drafts:

- prepare branded font files and metadata in a font-named folder under `outputs/font-preparation/{NUM}-{slug}/`;
- create the Commercial-Use and Personal-Use archives with byte-identical font binaries; no demo watermark archive is part of the current preparation pass;
- copy the schema-2 product description to the preparation root's `description.txt` and include its audit reports;
- install Agent 27's 23 checksummed Pinterest template pins and render the final factual specimen sheets;
- leave Agent 27's thumbnails and support designs in `font-factory/fonts/{input-slug}/prepared_visuals/`.

## Source selection and retention

`/full-workflow` requires one exact user-selected folder from `font-factory/Saved/`. List available folders and root-level OTF/TTF files with:

```bash
python3 bin/stage_saved_font.py --list
```

Move only the selected folder's original root-level OTF/TTF files:

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

Agent 13 writes package binaries, the two archives, `description.txt`, audit reports, factual specimens, and `visuals/New-Images/pinterest/` to the numbered preparation output. It does not copy the 26 support renders or thumbnail specimens there, generate final artwork, compress seller images, or make videos.

After preparation, the seller generates and approves the 3:2 and square main thumbnails from the matching specimens and prompts, then places them in the preparation output's image drop directory. Agent 30 final-image processing and Pinterest preparation are separate follow-up stages outside `/full-workflow`. They do not run until invoked as their own workflow.
