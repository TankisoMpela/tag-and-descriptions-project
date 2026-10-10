#!/usr/bin/env python3
"""Generate the Claude Code registration for the tag-and-description-project.

Reads opencode.json (source of truth) and produces:
  - .claude/agents/{key}.md                 for every registered agent
  - .claude/commands/{name}.md              for every registered command
  - .claude/skills/                         mirror of .opencode/skills
  - .claude/settings.json                   permissions.allow for the Agent tool + validators
"""
import json
import os
import re
import shutil
import sys

ROOT = "/home/tankiso/Projects/Business-and-Tools/tag-and-description-project"
OUT = os.path.join(ROOT, ".claude")

TOOL_MAP = {
    "serper_serper_search": "serper_search",
    "firecrawl_firecrawl_scrape": "firecrawl_scrape",
    "firecrawl_firecrawl_search": "firecrawl_search",
    "exa_exa_search": "exa_search",
    "tavily_tavily_search": "tavily_search",
    "context7_query_docs": "context7_query-docs",
    "agent_browser": "WebFetch",
}

WORKFLOW_DELEGATION = {
    "all-fonts-workflow": [
        ("booth-fonts-specialist", "BOOTH (Japanese-first paid-only listing + validator)"),
        ("marketore-fonts-specialist", "Marketore (Fonts taxonomy, exactly 10 vocabulary tags)"),
        ("yellowimages-fonts-specialist", "YellowImages (Creative Store font listing, exactly 30 canonical-first tags)"),
    ],
    "full-workflow": [
        ("font-image-generator", "Agent 27 — OpenPencil visual handoff; decides final name when not supplied (no uniqueness research)"),
        ("font-prep-specialist", "Agent 13 — continuous metadata/package/audit, both videos, factual-specimen copy, visual handoff"),
        ("booth-fonts-specialist", "Agent 20 — BOOTH paid-only listing"),
        ("marketore-fonts-specialist", "Agent 24 — Marketore listing"),
        ("yellowimages-fonts-specialist", "Agent 23 — YellowImages listing"),
    ],
    "ivoryglass-marketplace-workflow": [
        ("booth-fonts-specialist", "BOOTH listing"),
        ("cubebrush-fonts-specialist", "Cubebrush listing"),
        ("yellowimages-fonts-specialist", "YellowImages listing"),
        ("dlsite-fonts-specialist", "DLsite listing"),
    ],
    "all-brushes-workflow": [
        ("brush-visual-prep-specialist", "Agent 18 — visual validation/derivatives/manifest"),
        ("cm-procreate-brushes-specialist", "Agent 15 — Creative Market brush listing"),
        ("cubebrush-procreate-brushes-specialist", "Agent 16 — Cubebrush brush listing"),
        ("masterbundles-general-specialist", "Agent 17 — MasterBundles listing"),
    ],
}


def spec_file_for(agent_cfg):
    m = re.search(r"\{file:\./agents/([^}]+)\}", agent_cfg.get("prompt", ""))
    return m.group(1) if m else None


def yaml_str(value):
    return json.dumps(str(value), ensure_ascii=False)


def titleize(key):
    return key.replace("-", " ").title()


def build_agent(key, agent_cfg, spec):
    perms = ["    permissionMode: acceptEdits", ""]
    is_workflow = key in WORKFLOW_DELEGATION
    lines = []
    lines.append("---")
    lines.append(f"name: {key}")
    lines.append(f"description: {yaml_str(agent_cfg['description'])}")
    lines.append("permissionMode: acceptEdits")
    lines.append("---")
    lines.append("")
    lines.append(f"# {titleize(key)}")
    lines.append("")
    lines.append(
        f"You are the Claude Code registration of the **`{key}`** specialist in the "
        "tag-and-description-project workspace. You run inside Claude Code. The "
        "canonical agent spec lives in `agents/{spec}` and the master workspace guide "
        "is `AGENTS.md`; the OpenCode (`opencode.json`) and omp (`.omp/`) registries "
        "belong to other runtimes and are **not** delegation targets here."
        .replace("{spec}", spec)
    )
    lines.append("")
    lines.append("## Startup (do this first, every run)")
    lines.append("")
    lines.append("1. Read `AGENTS.md` from the project root and follow its rules that apply to your role: listing-agent scope, platform constraint matrix, unified product numbering, tag-tracking rules, research checkpoints and web-research fetch policy, pricing/seller-entry doctrine, and the relevant workflow/doctrine section for your stage.")
    lines.append(f"2. Read `agents/{spec}` — it is your authoritative system prompt. Follow its execution modes, evidence rules, output paths, and validators exactly. Treat any OpenCode/omp/Codex runtime references inside it as translated by the mapping below.")
    lines.append("3. Only then execute the task from your delegation prompt.")
    lines.append("")

    lines.append("## Claude Code runtime mapping (translate; never call the other runtimes' names)")
    lines.append("")
    lines.append("- Research MCP servers come from the project `.mcp.json` and appear as Claude Code tools: `firecrawl_scrape`, `firecrawl_search`, `serper_search`, `exa_search`, `tavily_search`, `context7_query-docs`. The OpenCode/omp spellings (`firecrawl_firecrawl_scrape`, `serper_serper_search`, `exa_exa_search`, `tavily_tavily_search`, `context7_query_docs`, `mcp__firecrawl_scrape`) do not exist here — call the Claude Code names.")
    lines.append("- `webfetch` in the specs maps to Claude Code's `WebFetch`, used only as the allowed one-time fallback when Firecrawl fails or rate-limits (record the substitution).")
    lines.append("- `agent_browser` is NOT available in this runtime. Record it as a limitation in your research notes; do not invent a substitute browse step.")
    lines.append("- Local tooling runs through the `Bash` tool: `node bin/search.js ...`, `python3 bin/*.py` collectors/validators, etc.")
    lines.append("- Write outputs to the exact paths the spec requires, run the required validator from the project root, and report PASS/FAIL honestly. Never claim publication, upload, or an account action.")
    lines.append("")

    if is_workflow:
        lines.append("## Delegation map (Claude Code)")
        lines.append("")
        lines.append("Use the Claude Code `Agent` tool for every stage, strictly one at a time, in this exact order. Wait for each child's final result before starting the next stage. Never dispatch concurrently, in a task array, or in the background.")
        lines.append("")
        for i, (name, purpose) in enumerate(WORKFLOW_DELEGATION[key], 1):
            lines.append(f"{i}. `{name}` — {purpose}")
        lines.append("")
        lines.append("Pass each child the full handoff text your canonical spec requires, translating any OpenCode/Codex runtime agent IDs to the `.claude/agents/` subagent names listed above. Do not do a child's listing/preparation work in this parent.")
        lines.append("")

    lines.append("## Crossover guard (hard rule)")
    lines.append("")
    lines.append("You are a Claude Code subagent. You MUST NOT:")
    lines.append("- spawn, invoke, or delegate to the `opencode`, `omp`, `claude`, or `codex` CLIs/daemons through Bash or any subprocess;")
    lines.append("- treat `opencode.json` agent entries, `.omp/agents/*.md`, Codex agents, or an external session as delegation targets;")
    lines.append("- describe a stage as delegated unless a Claude Code `Agent` tool call against a `.claude/agents/` subagent returned the child's final result;")
    lines.append("- claim completion from a partial file, a started child, or a plausible-but-unverified output.")
    lines.append("")
    lines.append("## Report back")
    lines.append("")
    lines.append("Return: the output file path(s) you wrote, validator status (PASS/FAIL), evidence/tag decisions in brief, research limitations, and any blocked facts. State clearly that no upload or publication occurred.")
    return "\n".join(lines)


def build_command(name, cmd_cfg):
    agent = cmd_cfg.get("agent")
    template = cmd_cfg.get("template", "") or ""
    template = template.replace("{input}", "$ARGUMENTS").strip()
    lines = []
    lines.append("---")
    lines.append(f"description: {yaml_str(cmd_cfg['description'])}")
    if agent:
        lines.append('argument-hint: "product facts or workspace path"')
    lines.append("---")
    lines.append("")
    lines.append(f"# /{name}")
    lines.append("")
    if agent:
        lines.append(f"Delegate the task below to the **`{agent}`** subagent defined in `.claude/agents/{agent}.md`. Use the Claude Code `Agent` tool, run it in the foreground, and wait for its final result before continuing. Do not delegate this to OpenCode, omp, or Codex, and do not attempt the specialist's work in the main session.")
        lines.append("")
        lines.append("Task:")
        lines.append("")
        lines.append(f"```")
        lines.append(template)
        lines.append(f"```")
        lines.append("")
        lines.append("After the subagent returns, report its output paths, validator status, evidence, and any blocked facts. Never claim publication or an upload.")
    else:
        lines.append(template)
        lines.append("")
    return "\n".join(lines)


def normalize_tool_names(text):
    for src, dst in TOOL_MAP.items():
        text = text.replace(src, dst)
    return text


def copy_skills():
    src_dir = os.path.join(ROOT, ".opencode", "skills")
    dst_dir = os.path.join(OUT, "skills")
    if not os.path.isdir(src_dir):
        return
    for name in sorted(os.listdir(src_dir)):
        src = os.path.join(src_dir, name)
        if not os.path.isdir(src):
            continue
        dst = os.path.join(dst_dir, name)
        shutil.copytree(src, dst, dirs_exist_ok=True)
        sk = os.path.join(dst, "SKILL.md")
        if os.path.isfile(sk):
            with open(sk, "r", encoding="utf-8") as f:
                content = f.read()
            # normalize frontmatter allowed-tools and inline tool-name references
            content = content.replace(
                'allowed-tools: ["read", "write", "bash", "serper_serper_search", "firecrawl_firecrawl_scrape", "agent_browser"]',
                'allowed-tools: ["Read", "Write", "Edit", "Bash", "serper_search", "firecrawl_scrape", "WebFetch"]',
            )
            content = normalize_tool_names(content)
            with open(sk, "w", encoding="utf-8") as f:
                f.write(content)
        # copy any other files as-is (supporting materials)
        for item in os.listdir(dst):
            if item == "SKILL.md":
                continue
            sp = os.path.join(dst, item)
            if os.path.isfile(sp) and os.path.isdir(src):
                # files already copied by copytree; nothing extra needed
                pass


def main():
    with open(os.path.join(ROOT, "opencode.json"), encoding="utf-8") as f:
        cfg = json.load(f)

    agents_dir = os.path.join(OUT, "agents")
    cmds_dir = os.path.join(OUT, "commands")
    os.makedirs(agents_dir, exist_ok=True)
    os.makedirs(cmds_dir, exist_ok=True)

    agent_keys = sorted(cfg.get("agent", {}).keys())
    for key in agent_keys:
        agent_cfg = cfg["agent"][key]
        spec = spec_file_for(agent_cfg) or "AGENTS.md"
        # spec must exist
        spec_path = os.path.join(ROOT, "agents", spec)
        if not os.path.isfile(spec_path):
            print(f"WARN: spec not found for {key}: {spec_path}")
        body = build_agent(key, agent_cfg, spec)
        with open(os.path.join(agents_dir, f"{key}.md"), "w", encoding="utf-8") as f:
            f.write(body)
        print(f"agent: {key} -> .claude/agents/{key}.md ({spec})")

    cmd_names = sorted(cfg.get("command", {}).keys())
    for name in cmd_names:
        cmd_cfg = cfg["command"][name]
        body = build_command(name, cmd_cfg)
        with open(os.path.join(cmds_dir, f"{name}.md"), "w", encoding="utf-8") as f:
            f.write(body)
        print(f"command: {name} -> .claude/commands/{name}.md")

    copy_skills()
    print("skills: mirrored .opencode/skills -> .claude/skills (normalized tool names)")

    settings = {
        "permissions": {
            "allow": [
                "Agent",
                "Task",
                "Bash(python3 bin/validate_booth_listing.py *)",
                "Bash(python3 bin/validate_x_campaign.py *)",
                "Bash(python3 bin/validate_marketore_listing.py *)",
                "Bash(node bin/search.js *)",
            ]
        }
    }
    with open(os.path.join(OUT, "settings.json"), "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
        f.write("\n")
    print("settings: .claude/settings.json (delegation + validator permissions)")

    print(f"\nDone. {len(agent_keys)} agents, {len(cmd_names)} commands.")


if __name__ == "__main__":
    main()