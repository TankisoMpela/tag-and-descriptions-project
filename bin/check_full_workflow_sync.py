#!/usr/bin/env python3
"""Check that the active runtime registrations agree on full-workflow order."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


STAGES = (
    "font-image-generator",
    "font-prep-specialist",
    "cm-fonts-specialist",
    "creative-fabrica-fonts-specialist",
    "font-final-visual-processor",
)
CODEX_STAGES = (
    "font_image_generator",
    "font_preparer",
    "cm_fonts_specialist",
    "creative_fabrica_fonts_specialist",
    "font_final_visual_processor",
)
SPEC_FILES = (
    "agents/agent-27-font-image-generator.md",
    "agents/agent-13-font-prep-specialist.md",
    "agents/agent-2-fonts-specialist.md",
    "agents/agent-29-creative-fabrica-fonts-specialist.md",
    "agents/agent-30-font-final-visual-processor.md",
)


class SyncError(Exception):
    pass


def read(root: Path, relative: str) -> str:
    path = root / relative
    if not path.is_file():
        raise SyncError(f"missing file: {relative}")
    return path.read_text(encoding="utf-8")


def require_order(text: str, expected: tuple[str, ...], label: str) -> None:
    positions = [text.find(item) for item in expected]
    missing = [item for item, pos in zip(expected, positions) if pos < 0]
    if missing:
        raise SyncError(f"{label} is missing stage IDs: {', '.join(missing)}")
    if positions != sorted(positions):
        raise SyncError(f"{label} stage IDs are out of order: {', '.join(expected)}")


def frontmatter_name(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not match:
        return None
    name = re.search(r"^name:\s*['\"]?([^'\"\n]+)", match.group(1), re.M)
    return name.group(1).strip() if name else None


def check_children(root: Path, runtime: str, directory: str) -> None:
    for agent, spec in zip(STAGES, SPEC_FILES):
        path = root / directory / f"{agent}.md"
        if not path.is_file():
            raise SyncError(f"{runtime} is missing child agent: {path.relative_to(root)}")
        name = frontmatter_name(path)
        if name != agent:
            raise SyncError(
                f"{runtime} child {path.relative_to(root)} has name {name!r}; expected {agent!r}"
            )
        if spec not in path.read_text(encoding="utf-8"):
            raise SyncError(f"{runtime} child {agent} does not reference {spec}")


def check_agent27_sync(root: Path, opencode_agents: dict) -> None:
    canonical = read(root, SPEC_FILES[0])
    if "12 eligible layouts" not in canonical or "none is" not in canonical:
        raise SyncError("canonical Agent 27 spec is missing the 12-design randomized family showcase rule")

    registrations = {
        "Codex": read(root, ".codex/agents/font-image-generator.toml"),
        "OMP": read(root, ".omp/agents/font-image-generator.md"),
        "Qwen": read(root, ".qwen/agents/font-image-generator.md"),
        "OpenCode": str(opencode_agents.get("font-image-generator", {}).get("prompt", ""))
        + "\n"
        + str(opencode_agents.get("font-image-generator", {}).get("description", "")),
    }
    for runtime, text in registrations.items():
        if SPEC_FILES[0] not in text:
            raise SyncError(f"{runtime} Agent 27 registration does not reference {SPEC_FILES[0]}")
        if "12" not in text or "family" not in text.lower():
            raise SyncError(
                f"{runtime} Agent 27 registration is missing the 12-design family showcase handoff"
            )


def check(root: Path) -> list[str]:
    messages: list[str] = []

    canonical = read(root, "agents/agent-28-full-workflow.md")
    sequence_section = canonical.split("## Required sequence", 1)[1].split(
        "## Stage handoffs", 1
    )[0]
    if not all(label in sequence_section for label in ("Agent 27", "Agent 13", "Agent 2", "Agent 29", "Agent 30")):
        raise SyncError("canonical contract does not list the five active stages")
    if sequence_section.find("Agent 27") > sequence_section.find("Agent 13"):
        raise SyncError("canonical Agent 27/13 stages are out of order")
    for stage in STAGES[2:]:
        if stage not in sequence_section:
            raise SyncError(f"canonical stage ID missing: {stage}")
    if (
        "Saved" not in canonical
        or "stage_saved_font.py --random" not in canonical
        or "auto-random source mode" not in canonical
    ):
        raise SyncError("canonical contract is missing Agent-27 random Saved-source selection")
    messages.append("canonical contract: five active stages present")

    codex = read(root, ".codex/agents/full-workflow.toml")
    require_order(codex, CODEX_STAGES, "Codex orchestrator")
    if "stage_saved_font.py --random" not in codex:
        raise SyncError("Codex full-workflow must use Agent-27 random Saved-source selection")
    for filename in (
        "font-image-generator.toml",
        "font-preparer.toml",
        "cm-fonts-specialist.toml",
        "creative-fabrica-fonts-specialist.toml",
        "font-final-visual-processor.toml",
    ):
        if not (root / ".codex/agents" / filename).is_file():
            raise SyncError(f"Codex is missing child agent: .codex/agents/{filename}")
    messages.append("Codex: order and five child profiles present")

    omp = read(root, ".omp/agents/full-workflow.md")
    require_order(omp, STAGES, "OMP orchestrator")
    omp_command = read(root, ".omp/commands/full-workflow.md")
    require_order(omp_command, STAGES, "OMP /full-workflow command")
    if "stage_saved_font.py --random" not in omp or "stage_saved_font.py --random" not in omp_command:
        raise SyncError("OMP full-workflow must use Agent-27 random Saved-source selection")
    check_children(root, "OMP", ".omp/agents")
    messages.append("OMP: order, command, and five child profiles present")

    opencode_config = json.loads(read(root, "opencode.json"))
    agents = opencode_config.get("agent", {})
    for agent, spec in zip(STAGES, SPEC_FILES):
        if agent not in agents:
            raise SyncError(f"OpenCode is missing child agent: {agent}")
        if spec not in agents[agent].get("prompt", ""):
            raise SyncError(f"OpenCode child {agent} does not reference {spec}")
    check_agent27_sync(root, agents)
    opencode_command = opencode_config.get("command", {}).get("full-workflow", {})
    require_order(opencode_command.get("template", ""), STAGES, "OpenCode /full-workflow command")
    if "stage_saved_font.py --random" not in opencode_command.get("template", ""):
        raise SyncError("OpenCode full-workflow must use Agent-27 random Saved-source selection")
    if "Pixiv" not in opencode_command.get("description", "") and "paused" not in opencode_command.get("description", ""):
        raise SyncError("OpenCode full-workflow command should identify paused scope")
    messages.append("Agent 27: 12-design randomized family showcase handoff aligned across runtimes")
    messages.append("OpenCode: order, command, and six child registrations present")

    qwen_parent = read(root, ".qwen/agents/full-workflow.md")
    require_order(qwen_parent, STAGES, "Qwen orchestrator")
    if "stage_saved_font.py --random" not in qwen_parent:
        raise SyncError("Qwen full-workflow must use Agent-27 random Saved-source selection")
    check_children(root, "Qwen", ".qwen/agents")
    if "run_in_background: false" not in qwen_parent:
        raise SyncError("Qwen orchestrator must require foreground sequential children")
    messages.append("Qwen: order, foreground delegation, and five child profiles present")

    return messages


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    try:
        messages = check(root)
    except (OSError, ValueError, IndexError, SyncError) as exc:
        print(f"[FAIL] full-workflow sync: {exc}", file=sys.stderr)
        return 1
    for message in messages:
        print(f"[PASS] {message}")
    print("[PASS] Codex, OMP, OpenCode, and Qwen full-workflow registrations are aligned")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
