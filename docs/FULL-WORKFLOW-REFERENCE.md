# Font workflow — current reference

This page summarizes the current font launch and thumbnail handoff. Detailed
role rules live in the linked agent instructions; read those before changing a
stage.

## Thumbnail source and handoff

Agent 27 renders the exact font name in the actual font on a plain white field.
The resulting images are raw lettering specimens for the image model. They are
not final thumbnail artwork. Agent 27 also writes three complete, bespoke
prompts in `visual-direction/theme.txt`, each paired with its specimen:

- 3:2 main marketplace thumbnail;
- independently composed 1:1 main thumbnail;
- separate 1:1 storefront thumbnail.

The image model receives the matching specimen and its prompt. The old
marketplace thumbnail is not an input. The prompts describe the font-specific
subject, composition, letter/image relationship, palette, material, lighting,
exposure, focus, blur, and texture as the concept needs. Final art is reviewed
for exact spelling and capitalization, glyph fidelity, crop, contrast,
small-size legibility, coherence, and prompt fidelity.

## Stages

1. **Agent 27 — font image generator.** Authors the visual plan, raw lettering
   specimens, three complete thumbnail prompts, seven shared HTML/CSS support
   designs at 3:2 and 1:1, factual specimen previews, and all active Pinterest
   template pins. The review drafts remain in `font-factory/`.
2. **Agent 13 — font preparation.** Performs font QA, packages the binaries,
   prepares metadata and listing assets, and installs the verified Pinterest
   template pins in the preparation output. It does not make final thumbnail
   artwork.
3. **Marketplace listing agents.** Prepare their listing copy and research from
   the completed font package.
4. **Image handoff.** Pair each white-background specimen with its matching
   prompt, generate and inspect final thumbnail artwork, and put approved files
   in the output path named by Agent 13.
5. **Agent 30 — final visual processor.** Classifies the approved raw images,
   writes delivery copies and the manifest, and appends its ten composite
   Pinterest panels after the template pins.
6. **Pinterest preparer.** Validates and uploads the complete Pinterest set and
   records the resulting links.

## Authoritative instructions

- Agent 27: `agents/agent-27-font-image-generator.md`
- Agent 13: `agents/agent-13-font-prep-specialist.md`
- Agent 30: `agents/agent-30-font-final-visual-processor.md`
- Shared support layouts: `font-factory/support-references/TEMPLATE-GUIDE.md`
- Thumbnail research and detailed captions:
  `font-factory/Style-References/thumbnail-prompt-research-2026-10-20/`
