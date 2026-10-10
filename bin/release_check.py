#!/usr/bin/env python3
"""Run the local release gate for the OpenCode font pipeline.

This checks the active registry, runtime tools, and Python dependencies. A
product handoff can be added with ``--prepared-visuals``; raw font binaries can
be checked with ``--font-workspace``.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIGS = ("opencode.json", ".opencode/opencode.json", ".mcp.json", "package.json")
REQUIRED_COMMANDS = ("node", "opencode", "ots-sanitize", "rsvg-convert", "ffprobe")
FONT_SUFFIXES = {".otf", ".ttf", ".woff", ".woff2"}


def run(label: str, command: list[str], failures: list[str], timeout: int = 60) -> None:
    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        failures.append(f"{label}: {error}")
        return
    if result.returncode:
        output = result.stdout.strip().splitlines()
        detail = output[-1] if output else f"exit {result.returncode}"
        failures.append(f"{label}: {detail}")
    else:
        print(f"[PASS] {label}")


def check_registry(failures: list[str]) -> None:
    path = ROOT / "opencode.json"
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        failures.append(f"OpenCode registry: {error}")
        return

    agents = config.get("agent", {})
    commands = config.get("command", {})
    for name, agent in agents.items():
        prompt = agent.get("prompt")
        if not isinstance(prompt, str) or not prompt.startswith("{file:") or not prompt.endswith("}"):
            failures.append(f"agent {name!r} has no file-backed prompt")
            continue
        prompt_path = ROOT / prompt[6:-1]
        if not prompt_path.is_file():
            failures.append(f"agent {name!r} prompt is missing: {prompt_path}")
    for name, command in commands.items():
        target = command.get("agent")
        if target and target not in agents:
            failures.append(f"command {name!r} references missing agent {target!r}")
    if not failures:
        print(f"[PASS] OpenCode registry: {len(agents)} agents, {len(commands)} commands")


def check_configs(failures: list[str]) -> None:
    for relative in CONFIGS:
        path = ROOT / relative
        try:
            json.loads(path.read_text(encoding="utf-8"))
            print(f"[PASS] JSON: {relative}")
        except (OSError, json.JSONDecodeError) as error:
            failures.append(f"JSON {relative}: {error}")


def check_font_workspace(path: Path, failures: list[str]) -> None:
    files = sorted(file for file in path.rglob("*") if file.is_file() and file.suffix.casefold() in FONT_SUFFIXES)
    if not files:
        failures.append(f"font workspace contains no OTF/TTF/WOFF/WOFF2 files: {path}")
        return
    sanitizer = shutil.which("ots-sanitize")
    assert sanitizer is not None
    for file in files:
        run(f"OTS {file.relative_to(path)}", [sanitizer, str(file)], failures, timeout=30)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepared-visuals", type=Path,
                        help="also run strict Agent-27 handoff validation")
    parser.add_argument("--font-workspace", type=Path,
                        help="also run ots-sanitize on every font binary below this folder")
    args = parser.parse_args()
    failures: list[str] = []

    check_configs(failures)
    check_registry(failures)
    for command in REQUIRED_COMMANDS:
        if shutil.which(command):
            print(f"[PASS] tool available: {command}")
        else:
            failures.append(f"required tool missing: {command}")

    python_bin = os.environ.get("PYTHON_BIN")
    if not python_bin:
        venv_python = ROOT / ".venv" / "bin" / "python"
        python_bin = str(venv_python if venv_python.is_file() else Path(sys.executable))
    run("Python dependencies", [python_bin, "-c", "import fontTools, PIL, uharfbuzz"], failures)
    run("Python byte compilation", [python_bin, "-m", "compileall", "-q", "bin"], failures)
    run("OpenCode config", ["opencode", "debug", "config"], failures)
    run("OpenCode full-workflow agent", ["opencode", "debug", "agent", "full-workflow"], failures)

    if args.prepared_visuals:
        visual_path = args.prepared_visuals.resolve()
        run(
            "strict visual handoff",
            [python_bin, "bin/validate_font_visual_handoff.py", str(visual_path), "--strict-art-direction"],
            failures,
            timeout=90,
        )
    if args.font_workspace:
        workspace = args.font_workspace.resolve()
        if not workspace.is_dir():
            failures.append(f"font workspace does not exist: {workspace}")
        else:
            check_font_workspace(workspace, failures)

    if failures:
        for failure in failures:
            print(f"[FAIL] {failure}")
        print(f"\n[FAIL] release check: {len(failures)} failure(s)")
        return 1
    print("\n[PASS] release check complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
