---
name: namemaker
description: Font Naming & Marketplace Uniqueness Validation Specialist for omp, opencode, and codex. Takes font description, old name, and font specimen image, generates 10 evocative names, and searches DaFont and FontSpace for name uniqueness to select the #1 winning unique font name.
allowed-tools: ["Read", "Write", "Edit", "Bash", "serper_search", "firecrawl_scrape", "WebFetch"]
---

# NameMaker — Font Naming & Marketplace Uniqueness Validator Skill

`namemaker` is an automated font naming & uniqueness verification skill for **omp**, **opencode**, and **codex**. It takes a font description, an old/previous font name, and an optional font specimen image, generates 10 evocative, genre-aligned name candidates, and performs live search validation against **DaFont** and **FontSpace** to select the single best **#1 winning unique font name**.

---

## 🎯 Workflow Overview

1. **Input Ingestion**:
   - Font description (aesthetic, genre, weights, target audience).
   - Old / previous font name (if any).
   - Font specimen image path or URL (analyzes visual letterforms: contrast, serifs, swashes, script flow, vintage rough edges).

2. **Visual & Aesthetic Analysis**:
   - Inspect font sample image / read description.
   - Extract core brand personality traits (e.g. *Chic French Serif*, *70s Groovy Display*, *Cyberpunk Monospace*, *Romantic Calligraphy Script*, *Minimalist Swiss Grotesque*).

3. **Name Candidate Generation (10 Candidates)**:
   - Generate 10 evocative, short (1–2 words), memorable, and easily pronounceable candidate font names tailored to the visual genre.

4. **Marketplace Uniqueness Search & Validation (DaFont & FontSpace)**:
   - For every candidate name, run live searches across **DaFont** and **FontSpace**:
     ```bash
     # DaFont Check
     serper_search with query: site:dafont.com "[Candidate Name]"
     
     # FontSpace Check
     serper_search with query: site:fontspace.com "[Candidate Name]"
     ```
   - **Rejection Rule**: If any search returns an existing font listing matching `"[Candidate Name]"`, mark as **TAKEN** and discard immediately.

5. **Winning Selection & Report Generation**:
   - Select the **#1 Winning Unique Font Name** + 2 verified fallback unique names.
   - Save the comprehensive analysis report to `outputs/font-names/{product-slug}-name-report.md`.

---

## 📝 Output Report Schema (`outputs/font-names/{slug}-name-report.md`)

```markdown
---
date: [YYYY-MM-DD]
tool: namemaker
old_name: [Old Font Name]
winning_name: [Winning Unique Name]
status: Verified Unique on DaFont & FontSpace
---

# FONT NAMING REPORT: [WINNING FONT NAME]

## 🏆 WINNING FONT NAME
**[WINNING FONT NAME]**

### Why This Name Wins:
[2-3 sentences explaining visual alignment with the font letterforms, genre fit, and emotional appeal.]

---

## 🔍 MARKETPLACE UNIQUENESS VERIFICATION

| Candidate Name | DaFont Status | FontSpace Status | Overall Verdict |
|---|---|---|---|
| **[Winning Name]** | ✅ Available | ✅ Available | **WINNER** |
| [Fallback Name 1] | ✅ Available | ✅ Available | Backup 1 |
| [Fallback Name 2] | ✅ Available | ✅ Available | Backup 2 |
| [Rejected Name 1] | ❌ TAKEN | ✅ Available | Discarded |

---

## 🎨 VISUAL AESTHETIC & BRAND ALIGNMENT
- **Visual Style:** [e.g. Modern High-Contrast Serif]
- **Mood & Vibe:** [e.g. Elegant, Luxurious, Editorial]
- **Target Audience:** [e.g. Branding Agencies, Wedding Designers, Magazine Editors]
- **Recommended Seed Image File:** `seed.png` with text "[WINNING FONT NAME]"
```
