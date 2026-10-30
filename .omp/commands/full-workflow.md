---
description: Run the shared five-stage sequential font launch workflow through preparation, BOOTH, Creative Market, and Creative Fabrica. Pixiv and other marketplace stages are paused.
---

Dispatch the registered `full-workflow` task agent. It reads the shared
contract in `agents/agent-28-full-workflow.md` and runs these five active
stages strictly sequentially: `font-image-generator` (Agent 27),
`font-prep-specialist` (Agent 13), `booth-fonts-specialist` (Agent 20),
`cm-fonts-specialist` (Agent 2), then `creative-fabrica-fonts-specialist`
(Agent 29). It selects/stages only the user-chosen
Saved family when a new source is required. It does not run Pixiv or any other
paused marketplace, and makes no upload or publication claim.

User request / constraints:

$@
