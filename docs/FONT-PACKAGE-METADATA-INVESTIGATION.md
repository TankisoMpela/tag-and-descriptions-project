# Font Package Metadata Investigation

**Date:** 2026-10-23
**Scope:** Agent 13 preparation, CFF names, font timestamps, Name ID 10, GSUB/GPOS replacement, and archive outputs.

## Findings

`bin/prepare_font_package.py:set_metadata` previously rewrote the OpenType
`name` table and OS/2 fields but did not rewrite the names duplicated in a CFF
table. That left the visible branded name table beside the source font's CFF
TopDict `FamilyName` and `FullName`, plus its CFF Name INDEX `FontName`. The
packager copied those values into WOFF and WOFF2 as well. This is the confirmed
original-name leak.

The issue was reproduced in three existing Commercial-Use OTFs:

| Product | CFF names before fix | Branded name IDs 1 / 4 / 6 |
|---|---|---|
| Big Riff | `Chunko Bold` / `Chunko Bold` / `ChunkoBold` | `Big Riff` / `Big Riff Regular` / `BigRiff-Regular` |
| FieldStory | `Hitherto` / `Hitherto` / `FieldStory-Regular` | `FieldStory` / `FieldStory Regular` / `FieldStory-Regular` |
| Moonletter | `Maniefa` / `Maniefa Regular` / `Moonletter-Regular` | `Moonletter` / `Moonletter Regular` / `Moonletter-Regular` |

### Timestamps and Name ID 10

- `head.created` carries the source creation date and can expose source history,
  even though it does not contain the old family name. The rebranding pass now
  resets it to the packaging time.
- `head.modified` is recalculated by fontTools when the prepared font is saved.
  `apply_metadata` enables `recalcTimestamp` explicitly, and `set_metadata`
  initializes both timestamps to the rebranding time. One inspected input,
  PT Footlocker, stores low Unix-style timestamp values; fontTools warns and
  normalizes those while reading. Resetting both fields avoids carrying that
  source encoding into the branded package.
- Name ID 10 is not a hidden copy of the family name in these samples. It
  contains upstream description/credit material and is intentionally preserved
  by the current project policy. Examples include `Hatf Type`, `Created using
  Fontlab 8`, and a designer/manufacturer credit. It may disclose provenance,
  but it is not treated as an accidental naming leak and is not obfuscated.

## Fix Implemented

After writing the branded name records, `set_metadata` now synchronizes the CFF
fields before saving:

```python
if "CFF " in font:
    cff = font["CFF "].cff
    top_dict = cff.topDictIndex[0]
    top_dict.FamilyName, top_dict.FullName = (
        records.getDebugName(1), records.getDebugName(4)
    )
    cff.fontNames[0] = records.getDebugName(6)
```

`FamilyName` and `FullName` are TopDict operators. `FontName` is stored in the
CFF Name INDEX, so it must be set through `cff.fontNames[0]`. The package audit
now checks all three against name IDs 1, 4, and 6 in OTF, WOFF, and WOFF2 files.
It also reports the layout feature inventory, Name ID 10, and `head` timestamps.

## GSUB/GPOS Preparation Path

The packager now accepts an explicit `--layout-features <file.fea>` option.
When supplied, fontTools `feaLib` replaces GSUB and GPOS from that reviewed
Adobe Feature File before conversion. Without it, the source tables are
preserved. Agent 13 is instructed not to invent feature rules and to verify
requested substitutions and positioning by shaping sample text with HarfBuzz.

The existing PT Footlocker feature file was exercised as an integration sample.
It built a `liga` GSUB feature and a `kern` GPOS feature. HarfBuzz shaped `fi fl`
to the `fi` and `fl` ligature glyphs; the `AT` pair advanced 1847 units with
kerning enabled versus 1864 with kerning disabled. The original TTF and the
pre-existing `layout-repaired/` proof artifacts were not overwritten.

## Watermark Workflow Removed

New preparation runs create only Commercial-Use and Personal-Use archives.
The packager verifies that the archives contain the same font paths and
byte-identical font binaries; Personal-Use may additionally include the
like-request note. The Free-Trial-Demo stamping pass and archive were removed
from both active archive builders, Agent 13's instructions, and the active
helper index. `stamp_personal_use.py` remains documented as a legacy standalone
utility and is no longer called by the preparation workflow.

On a successful `--force` rebuild, the packager removes that product's obsolete
local Free-Trial-Demo ZIP after the replacement fonts pass their audits. No
existing package archive was rewritten or deleted during this investigation.

## Tests Run

- Re-saved and reopened three shipped CFF OTF samples (Big Riff, FieldStory,
  Moonletter). In every file, the CFF triple matched name IDs 1 / 4 / 6 after
  the fix.
- Ran Big Riff through the complete CFF-source packaging branch. The OTF,
  WOFF, and WOFF2 CFF names matched the branded name table; its derived TTF,
  package audit, OTS pass, and two-archive payload check passed.
- Verified the same samples retained Name ID 10, reset `head.created` to the
  rebranding time, and refreshed `head.modified` at save time.
- Ran the complete `prepare_font_package.py` path in a temporary output folder
  with the PT Footlocker `.fea` input. All four formats passed
  `font_package_audit.py` and `ots-sanitize`; the output contained exactly the
  two paid archives and their four font payloads matched byte-for-byte.
- Verified HarfBuzz `liga` and `kern` behavior as described above.
- Started from the repaired PT Footlocker font that already had both tables,
  then applied a liga-only `.fea` file. The test confirmed the old GPOS table
  was removed and only the declared GSUB `liga` feature remained.
- Verified a successful forced rebuild removes an obsolete local trial ZIP;
  the failure path retains it.
- Ran `python3 -m py_compile` for the modified Python scripts and
  `git diff --check`.

## Existing Package Rebuild Recommendation

An archive scan across prepared outputs found 19 product folders with at least
one CFF naming mismatch:

`052-big-riff`, `053-ivoryglass`, `057-fieldstory`, `058-moonletter`,
`064-funk-drop`, `068-lucky-chrome`, `070-stone-ledger`, `074-circuit-sprint`,
`076-cameo-journal`, `077-kuro-ripper`, `078-story-wisp`, `080-cosette-marque`,
`082-restrained-flourish`, `92-ember-bracket`, `93-blazher`, `995-final-check`,
`997-timing-font`, `999-qegor-test`, and `aureus-clare`.

Across Commercial-Use archives, 69 of 106 CFF OTF/WOFF/WOFF2 members failed the
name comparison; across Personal-Use archives, 71 of 106 failed. These are
archive-member counts, so OTF/WOFF/WOFF2 representations and license-copy
archives repeat some source faces. The focused OTF scan found 26 mismatches in
40 CFF OTF members across 30 Commercial-Use archives containing CFF OTF files.

Recommendation: rebuild each affected product from its original staged source
with the patched `prepare_font_package.py`, reusing its existing product number
and branded name. Validate the generated package and matching archive payloads
before replacing any marketplace delivery. Run this only where the original
source workspace is available; the rebuild has not been started here.

```bash
python3 bin/prepare_font_package.py \
  --workspace "font-factory/fonts/{input-slug}" \
  --name "{existing-branded-name}" \
  --number {existing-product-number} \
  --force
```

The rebuild overwrites the local prepared font files and two paid archives; the
obsolete local trial ZIP is removed only after all replacement audits pass.

## Follow-up Metadata Hardening (2026-10-26)

This pass supersedes the earlier timestamp and Name ID 10 decisions above.
OpenType Name ID 10 means Description; it is removed from delivered fonts.
The input preflight report now captures source Name IDs 9 (Designer) and 10
across platforms for review. Managed name IDs are collapsed to a single
Windows Unicode English record, style labels come from OS/2 weight/width/slant
fields, and unused custom name IDs are dropped while names referenced by
variable-font, palette, and layout-feature tables are retained.

The CFF TopDict family, full name, weight, copyright and notice now match the
branded records. Orphaned String INDEX entries for those rewritten fields are
neutralized in place, while glyph-name strings remain unchanged. CFF
UniqueID/XUID, stale DSIG signatures, FFTM timestamp/application data, legacy
PCLT and optional meta tables are removed. head.created stays at the source value while
head.modified changes on save. Glyph outlines, CFF charstrings, private hint
data, cmap, metrics, layout tables, and the other OS/2 behavior fields remain
intact in the native source-format output. The alternate outline format is
converted and can lose the source hint program; the preparation audit names
which outputs retain original hinting.

The package audit enforces platform/language normalization, absence of removed
records and tables, CFF identifier cleanup, branded values, PostScript-name
format, and empty WOFF metadata/private-data blocks. WOFF/WOFF2 are generated
from the cleaned OTF master; compression carries its cleaned font tables.
