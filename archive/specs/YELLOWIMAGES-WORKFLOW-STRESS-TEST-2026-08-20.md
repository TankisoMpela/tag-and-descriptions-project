# YellowImages Agent Stress Test - 2026-08-20

## Scope

Stress-tested the new `agent-23-yellowimages-fonts-specialist` against the
current Creative Market font-agent pattern and live YellowImages font pages.
The test covered registration, exact 30-tag formatting, canonical-first tag
ordering, evidence-row requirements, Creative Store categorization,
research-provider allocation, and failure handling. Image production and
dimension QA were deliberately excluded because they belong to Font Prep.

## Implementation under test

- Role specification: `agents/agent-23-yellowimages-fonts-specialist.md`
- OpenCode native registration: `.codex/agents/yellowimages-fonts-specialist.toml`
- OpenCode JSON agent and command: `yellowimages-fonts-specialist` and
  `yellowimages-font`
- Validator: `bin/validate_yellowimages_listing.py`
- Output target: `outputs/yellowimages/{NUM}-{slug}-yellowimages.md`

## Live evidence batch

The unique URL batch was assigned according to the shared 60/40 policy:

| URL | Assigned provider | Actual provider | Result |
|---|---|---|---|
| `https://yellowimages.com/tags` | Firecrawl | Firecrawl | PASS; public store tag directory and font vocabulary returned |
| `https://yellowimages.com/graphic-design/category/fonts` | Firecrawl | Firecrawl | PASS; live font category returned current catalog and filters |
| `https://yellowimages.com/stock/nebula-sci-fi-font-54870` | Firecrawl | Firecrawl | PASS; PDP title, description, category, previews, and licensing fields returned |
| `https://yellowimages.com/stock/uncode-pixel-modern-font-71289` | Crawl4AI | Crawl4AI failed at browser launch | Web fallback retrieved the page and current product evidence |
| `https://yellowimages.com/stock/glitten-ligature-serif-font-68054` | Crawl4AI | Crawl4AI failed at browser launch | Web fallback retrieved the page and current product evidence |

Crawl4AI's failure was `BrowserType.launch: Target page, context or browser has
been closed` while starting the local Playwright Chromium headless shell. The
agent specification treats this as an assigned-provider failure and allows one
webfetch fallback; it does not reassign the full batch to Firecrawl.

Independent discovery checks also succeeded:

- Serper returned relevant YellowImages products including Space Rocks,
  Cosmico, Aerospace, and Rickgat.
- Exa returned relevant Creative Store PDPs including Newro Space, Robocops,
  Futury, NCL Nexiom, and BERGAN.
- Neither result set was treated as YellowImages search volume or sales data.

## Copy/tag stress result

A Vexora-style fixture containing five relevant exact YellowImages terms first
and 25 researched supplemental terms passed:

`python3 bin/validate_yellowimages_listing.py /tmp/yellowimages-valid.md`

Result: **PASS**

The validator confirmed:

- exactly 30 tags;
- comma-separated single-line format;
- no duplicates;
- at least two words per tag;
- no leading-word repetition above three;
- 30 tag-evidence rows;
- `Creative Store > Fonts` category;
- no em dash formatting issue.

A Creative Market listing was intentionally run through the YellowImages
validator as a negative control. It failed for missing YellowImages-specific
sections, tag evidence, and category, confirming that the new
validator is not merely accepting an existing CM listing unchanged.

## Registration result

- `opencode.json` parses successfully.
- Native YellowImages TOML parses successfully.
- The new files exist at their required paths.
- `opencode --version` returned `1.18.15`.
- `opencode debug config` and `opencode models` could not complete because this
  environment cannot open `/home/tankisompela/.local/share/opencode/log/opencode.log`.
  This is an OpenCode runtime/log-path limitation, not a static registration
  or validator failure.

## Conclusions

The YellowImages agent is structurally ready for an explicit product run. It
copies Creative Market's useful research discipline and exact-count validation,
but changes the marketplace assumptions: YellowImages Tags/category terms are
frontloaded as canonical vocabulary, supplemental terms are separately
evidenced, no public tag cap is claimed, Creative Store > Fonts is required,
and image creation/derivative work remains upstream in Font Prep rather than
being duplicated by the listing agent.
