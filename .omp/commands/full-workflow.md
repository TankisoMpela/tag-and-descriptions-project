---
description: Run the shared five-stage sequential font launch, including final image processing when the image readiness check passes. Pixiv and other marketplace stages are paused.
---

Dispatch the registered `full-workflow` task agent. It reads the shared
contract in `agents/agent-28-full-workflow.md` and runs these five stages
strictly sequentially: `font-image-generator` (Agent 27),
`font-prep-specialist` (Agent 13), `cm-fonts-specialist` (Agent 2), then `creative-fabrica-fonts-specialist`
(Agent 29), then `font-final-visual-processor` (Agent 30) when its mechanical
image-readiness check passes. Agent 27 generates all four thumbnails from the
exact theme prompts and paired specimens; Agent 13 installs them with the 34
support images. It preserves an exact user-supplied source; if none is supplied,
Agent 27 selects and stages one Saved family with
`python3 bin/stage_saved_font.py --random` before reviewing metadata and the
full character atlas. It does not ask the user to choose. The selected source
continues through all stages. It does not run Pixiv or any other
paused marketplace, and makes no upload or publication claim. Agent 30 also
remains independently available for older prepared products.

User request / constraints:

$@
