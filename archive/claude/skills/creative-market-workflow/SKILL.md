---
name: creative-market-workflow
description: Multi-marketplace product optimization workflow for Creative Market, Etsy, MasterBundles, Cubebrush, and DaFont & FontSpace. Runs sequential font delegation across marketplaces to preserve API rate limits.
---

# Multi-Marketplace Product Optimization Workflow

## 9 Agents — Multi-marketplace specialists & simultaneous font delegation

| # | Agent | Command | Marketplace | For |
|---|-------|---------|-------------|-----|
| 1 | **PowerPoint Specialist** | `/cm-powerpoint` | Creative Market | PowerPoint, Google Slides, Keynote presentation templates |
| 2 | **CM Fonts Specialist** | `/cm-font` | Creative Market | Font products for Creative Market (script, serif, sans, display, etc.) |
| 3 | **Mockups Specialist** | `/cm-mockup` | Creative Market | Mockup products (device, apparel, packaging, scene creators) |
| 4 | **General Specialist** | `/cm-general` | Creative Market | Everything else on CM (graphics, templates, brushes, photos, 3D) |
| 5 | **Etsy General Specialist** | `/etsy` | Etsy | Any digital/physical product listing optimized for Etsy SEO |
| 6 | **Etsy Fonts Specialist** | `/etsy-font` | Etsy | Font products for Etsy (digital downloads, Cricut, OTF/TTF) |
| 7 | **MasterBundles Fonts Specialist** | `/mb-font` | MasterBundles | Font products for MasterBundles (deals, subcategories, SEO meta) |
| 8 | **Cubebrush Fonts Specialist** | `/cb-font` | Cubebrush | Font products for Cubebrush (no approval, Basic/Commercial licenses, AI-content tagging check, centered-thumbnail covers) |
| 9 | **DaFont & FontSpace Freemium Specialist** | `/freemium-font` | DaFont & FontSpace | Free/Demo font freemium conversion funnel metadata and zip license text file |
| 10 | **Multi-Marketplace Font Delegator** | `/all-fonts` | ALL Platforms | Sequentially runs Agents 2, 8, and 9 (CM -> MasterBundles -> Cubebrush), then optional standalone agents one by one |

## How to use

### Sequential Multi-Marketplace Font Delegation (Recommended for Fonts):
When given any font product or when `/all-fonts` is invoked:
```
/all-fonts "Modern handwritten script font with 4 weights, opentype ligatures, swashes, OTF TTF WOFF"
```
Or pass the font details to the main orchestrator agent. The sequential pipeline runs 3 agents (Creative Market -> MasterBundles -> Cubebrush) to respect search & Firecrawl rate limits:
1. **Agent 2 (`agent-2-fonts-specialist.md`)** -> Creative Market PDP Listing & 30 Tags
2. **Agent 8 (`agent-8-masterbundles-fonts-specialist.md`)** -> MasterBundles Listing & Fixed-Keyword-List Tags (SEO meta)
3. **Agent 9 (`agent-9-cubebrush-fonts-specialist.md`)** -> Cubebrush Listing & 20 Tags (300+ word description, Basic/Commercial license, AI-content tagging check)

Optional standalone agents (NOT in the sequential run — invoke only when explicitly requested):
- **Etsy** (`agent-6-etsy-fonts-specialist.md`) -> Etsy Listing & 13 Tags (Plain text, max 20 char tags)
- **DaFont/FontSpace** (`agent-11-dafont-fontspace-specialist.md`) -> Freemium Metadata & Zip License Readme Text File

### Single-Platform Commands:
```
/cm-font "Hand-drawn script font with 4 weights..."
/etsy-font "Cricut modern calligraphy font OTF TTF..."
/mb-font "Vintage serif font for branding & packaging..."
/cb-font "Futuristic serif font for logos & branding..."
/freemium-font "Modern script font demo for DaFont & FontSpace..."
```

## Multi-Marketplace Font Delegation Protocol

When a user provides a font product description, execute subagents sequentially in order (Creative Market -> MasterBundles -> Cubebrush) to avoid concurrent rate limits on search APIs. Etsy and DaFont/FontSpace are NOT part of the sequential run — execute them only when the user explicitly requests that platform:
```javascript
// Step 1: Creative Market
task(context: "Font optimization Step 1/3: Creative Market", tasks: [
  { name: "CM_Font_Specialist", agent: "task", task: "Execute agent-2-fonts-specialist.md instructions for product: [User Font Input]" }
]);

// Step 2: MasterBundles
task(context: "Font optimization Step 2/3: MasterBundles", tasks: [
  { name: "MasterBundles_Font_Specialist", agent: "task", task: "Execute agent-8-masterbundles-fonts-specialist.md instructions for product: [User Font Input]" }
]);

// Step 3: Cubebrush
task(context: "Font optimization Step 3/3: Cubebrush", tasks: [
  { name: "Cubebrush_Font_Specialist", agent: "task", task: "Execute agent-9-cubebrush-fonts-specialist.md instructions for product: [User Font Input]" }
]);

// Optional standalone (only on explicit request): Etsy, DaFont/FontSpace
task(context: "Font optimization (optional): Etsy / DaFont", tasks: [
  { name: "Optional_Platform_Specialist", agent: "task", task: "Execute the requested agent file (agent-6-etsy-fonts-specialist.md or agent-11-dafont-fontspace-specialist.md) instructions for product: [User Font Input]" }
]);
```

## Data Enrichment & Tooling Pipeline
- **Firecrawl** is the primary scraper for CM, Etsy, MasterBundles, Cubebrush, DaFont, and FontSpace pages.
- **Serper/Exa/Tavily** provide search intent and competitor discovery across all marketplaces.
- **Google Suggestqueries** (`bin/search.js`) validates search volume for tag selection.
- **CacheRepository** (`lib/`) caches search responses with per-source TTLs.
