# Behance Workflow Stress Test

Date: 2026-08-16  
Scope: static/dry-run validation of the sequential font listing workflow; no Behance upload, publication, checkout, or marketplace mutation was performed.

## Contract tested

The intended sequence is:

`Creative Market (Agent 2) -> MasterBundles (Agent 8) -> Cubebrush (Agent 9) -> BOOTH (Agent 20) -> Behance (Agent 21) -> Pinterest (Agent 10)`

Behance is a final project-package stage. It prepares a paste-ready project, not a claim that a project was published.

## Passed checks

- Agent 21 specification exists and defines the Behance publish fields, research method, output contract, and completion gates.
- Both OpenCode registries parse as JSON and expose the Behance specialist, `behance-font` command, and sequential `all-fonts` route.
- Native Codex registration parses and points at the Agent 21 specification.
- The workflow orchestrator places Agent 21 after Agent 20 and does not allow it to run in parallel with marketplace agents.
- The font-workflow and creative-market-workflow skills include the BOOTH-to-Behance handoff.
- Behance output path is `outputs/behance/{NUM}-{product-slug}-behance.md`.
- The Behance validator passes the three-image fixture at `tests/fixtures/behance-valid.md`.
- Validator checks cover frontmatter, required sections, Typography field, 1–10 project tags, per-image tag limits, alt text, research URLs, image ordering, and CTA status.
- The default sale mode is `EXTERNAL_LINK`; native Behance asset-sale fields are optional and are not implied by a listing package.
- The agent does not perform raw product/package/image QA and does not claim to upload or publish.

## Issues found and fixed during the stress test

- The nested OpenCode registry contained a duplicate `all-fonts` command and an invalid trailing comma after the Behance additions. The duplicate was removed and the JSON now parses.
- The initial validator fixture parser did not reliably associate source filenames with image blocks. It was corrected to parse the filename from each image heading, then the fixture was rerun successfully.

## Live-research evidence used

The agent specification records the official Behance rules that matter to this workflow: required cover/title/Creative Fields, up to 10 project tags, up to 10 image tags, alt text, image ordering, and manual publish steps. It also records the current cover and image guidance, including the recommended cover source size and project-image limits.

Official sources used for the implementation:

- [Create and publish a project](https://help.behance.net/hc/en-us/articles/204483684-Guide-Create-Publish-A-Project)
- [Cover image and project title](https://help.behance.net/hc/en-us/articles/204483484-Guide-Cover-Image-Project-Title)
- [Creative Fields](https://help.behance.net/hc/en-us/articles/204483944-Guide-Creative-Fields)
- [Project Tags](https://help.behance.net/hc/en-us/articles/204483954-Guide-Project-Tags)
- [Image Tags and Alt Text](https://help.behance.net/hc/en-us/articles/360042819254-Guide-Image-Tags-Alt-Text)
- [Formatting images for display](https://help.behance.net/hc/en-us/articles/204484614-Guide-Formatting-Images-For-Display-On-Behance)
- [Behance best practices](https://help.behance.net/hc/en-us/articles/1260800494029-Guide-Best-Practices)

## Runtime caveats

- `opencode debug config` and `opencode models` could not complete in this environment because OpenCode attempted to open `/home/tankisompela/.local/share/opencode/log/opencode.log`, which is unavailable. Static registry and native-registration checks passed independently.
- Firecrawl and Exa requests for Behance pages were refused by the current tool safety boundary. Direct official Behance Help Center and Behance pages were used instead; the Agent 21 research protocol records provider failure rather than fabricating search-volume evidence.
- A signed-in Behance editor was not automated. The deliverable therefore remains a manual publishing package with explicit paste/upload steps.

## Result

The Behance stage is structurally ready for a real product run. A live run still requires the seller to provide the product facts, approved image filenames/notes, and the destination Creative Market/BOOTH URL, then manually publish the generated package.
