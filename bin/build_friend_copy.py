#!/usr/bin/env python3
"""Build a clean, portable source copy without touching the source workspace.

Callable API::

    from build_friend_copy import build_friend_copy
    build_friend_copy("/path/to/tag-and-description-project-friend")

CLI::

    python3 bin/build_friend_copy.py --destination ../tag-and-description-project-friend

The destination must be outside the source repository and absent or empty.
The builder never removes or overwrites destination contents.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Iterable


POLICY_VERSION = 1
PROJECT_FILES = (
    ".gitignore",
    "AGENTS.md",
    "opencode.json",
    "package.json",
    "package-lock.json",
    "bun.lock",
    "pyproject.toml",
    "requirements.txt",
    "requirements-deterministic-visuals.txt",
    "uv.lock",
)
TEXT_SUFFIXES = {
    ".md", ".txt", ".py", ".js", ".mjs", ".sh", ".json", ".toml",
    ".yml", ".yaml", ".html", ".css", ".xml", ".jsx", ".svg", ".lock",
}
CODE_SUFFIXES = {".py", ".js", ".mjs", ".sh", ".md", ".txt"}
REFERENCE_IMAGE_RE = re.compile(
    r"(?:\.\./)+support-references/(?!materials/)[A-Za-z0-9_.\-/]+\.(?:png|jpe?g|webp|gif)",
    re.IGNORECASE,
)
PLACEHOLDER_IMAGE = "data:image/gif;base64,R0lGODlhAQABAAAAACwAAAAAAQABAAACAkQBADs="
PROJECT_ROOT_PATTERN = re.compile(
    r"/home/[^/\s]+/Projects/Business-and-Tools/tag-and-description-project/?"
)
MCP_ROOT_PATTERN = re.compile(r"/home/[^/\s]+/Projects/MCP-and-Integrations/gemini-proxy")
MATERIAL_NAME_RE = re.compile(
    r"[A-Za-z0-9_.-]+\.(?:png|jpe?g|webp|svg|ttf|woff2?)", re.IGNORECASE
)


class BuildError(RuntimeError):
    pass


def _is_file(path: Path) -> bool:
    return path.exists() and path.is_file() and not path.is_symlink()


def _add_file(root: Path, selected: dict[str, Path], relative: str | Path) -> None:
    rel = Path(relative).as_posix()
    source = root / rel
    if not _is_file(source):
        raise BuildError(f"required source file is missing or is a symlink: {rel}")
    selected[rel] = source


def _add_tree(
    root: Path,
    selected: dict[str, Path],
    relative: str | Path,
    *,
    suffixes: set[str],
    excluded_parts: set[str] | None = None,
    include_names: set[str] | None = None,
    exclude_names: set[str] | None = None,
) -> None:
    base = root / relative
    if not base.is_dir():
        return
    excluded_parts = excluded_parts or set()
    include_names = include_names or set()
    exclude_names = exclude_names or set()
    for source in sorted(base.rglob("*")):
        if not _is_file(source):
            continue
        rel_path = source.relative_to(root)
        if any(part in excluded_parts for part in rel_path.parts):
            continue
        if source.name in exclude_names:
            continue
        if include_names and source.name not in include_names:
            continue
        if source.suffix.lower() not in suffixes:
            continue
        selected[rel_path.as_posix()] = source


def _active_support_sources(root: Path) -> tuple[dict, list[Path]]:
    catalog_path = root / "font-factory/support-html/catalog.json"
    try:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BuildError(f"cannot read active support catalogue: {exc}") from exc
    templates = catalog.get("templates")
    if not isinstance(templates, list) or not templates:
        raise BuildError("support catalogue has no active templates")
    return catalog, templates


def _active_pin_ids(root: Path) -> list[str]:
    renderer = root / "font-factory/pin-html/render_gallery.mjs"
    try:
        text = renderer.read_text(encoding="utf-8")
    except OSError as exc:
        raise BuildError(f"cannot read active Pinterest template renderer: {exc}") from exc
    match = re.search(r"const ids = \[(.*?)\];", text, re.S)
    if not match:
        raise BuildError("cannot find active Pinterest template IDs in render_gallery.mjs")
    try:
        ids = json.loads("[" + match.group(1) + "]")
    except json.JSONDecodeError as exc:
        raise BuildError(f"cannot parse active Pinterest template IDs: {exc}") from exc
    if not isinstance(ids, list) or not ids or any(not isinstance(item, str) for item in ids):
        raise BuildError("active Pinterest template IDs are invalid")
    if len(ids) != len(set(ids)):
        raise BuildError("active Pinterest template IDs are not unique")
    return ids


def _selected_render_materials(root: Path, templates: list[dict]) -> list[Path]:
    support_root = root / "font-factory/support-html"
    scan_sources: set[Path] = set()
    for template in templates:
        entry = template.get("htmlEntry")
        if entry:
            entry_path = root / "font-factory" / entry
            if not entry_path.is_file():
                raise BuildError(f"active catalogue entry is missing: {entry}")
            template_dir = entry_path.parent
            scan_sources.update(p for p in template_dir.iterdir() if _is_file(p))
        module = template.get("module")
        if module:
            module_path = root / module if module.startswith("bin/") else root / "font-factory" / module
            if module_path.is_file():
                scan_sources.add(module_path)
    scan_sources.update(
        p for p in (support_root / "shared").glob("*")
        if _is_file(p) and p.suffix.lower() in {".js", ".css"}
    )
    benchmark_editor = support_root / "benchmarks/T26074-12/layout-editor.html"
    if benchmark_editor.is_file():
        scan_sources.add(benchmark_editor)

    names: set[str] = set()
    for source in scan_sources:
        try:
            names.update(MATERIAL_NAME_RE.findall(source.read_text(encoding="utf-8")))
        except (OSError, UnicodeDecodeError):
            continue

    # Several template modules form square filenames mechanically from their
    # 3:2 background names. Include only those computed sibling ingredients.
    for name in tuple(names):
        if name.endswith("-clean-bg.png"):
            names.add(name.removesuffix("-clean-bg.png") + "-clean-bg-square.png")
        if name.endswith("-background-3x2.png"):
            names.add(name.removesuffix("-background-3x2.png") + "-background-square.png")
        if name.endswith("-3x2.png"):
            names.add(name.removesuffix("-3x2.png") + "-square.png")

    materials = root / "font-factory/support-references/materials"
    return sorted(
        path for path in materials.rglob("*")
        if _is_file(path) and path.name in names
    )


def _select_files(root: Path) -> tuple[dict[str, Path], list[str]]:
    selected: dict[str, Path] = {}
    for relative in PROJECT_FILES:
        _add_file(root, selected, relative)

    _add_tree(root, selected, ".github", suffixes={".yml", ".yaml", ".md"})
    _add_tree(root, selected, "agents", suffixes={".md"})
    _add_tree(
        root, selected, "archive", suffixes=CODE_SUFFIXES | {".html", ".css"},
        excluded_parts={
            "research", "claude", "opencode", "omp-agents", "omp-agents-legacy",
            "kilo", "commands", "skills-legacy",
        },
    )
    _add_tree(
        root, selected, "bin", suffixes=CODE_SUFFIXES,
        excluded_parts={"archive", "__pycache__", ".venv", "node_modules"},
        exclude_names={"magick7", "sec-scan", "gen_claude_registration.py"},
    )
    _add_tree(root, selected, "docs", suffixes={".md"}, include_names={
        "AGENT-27-CREATIVE-PROCESS.md", "FULL-WORKFLOW-REFERENCE.md",
        "TOKEN-EFFICIENCY.md", "PASTE5-FINDINGS.md", "OPTIMIZATION-RESULTS.md",
        "SKIA-PIN-RENDERER.md", "PIN-ART-DIRECTION.md",
        "FONT-PACKAGE-METADATA-INVESTIGATION.md", "LISTING-TOKEN-PLAN.md",
        "SEARCH-DATA-ACCESS.md",
    })
    _add_tree(root, selected, "lib", suffixes={".js", ".md"})
    _add_tree(root, selected, "templates", suffixes={".md", ".txt"})

    # Runtime registrations only: local MCP settings, permissions, caches,
    # runtime package installs, and unrelated user-level skills stay out.
    _add_file(root, selected, ".codex/config.toml")
    _add_tree(root, selected, ".codex/agents", suffixes={".toml"}, include_names={
        "full-workflow.toml", "font-image-generator.toml", "font-preparer.toml",
        "booth-fonts-specialist.toml", "cm-fonts-specialist.toml",
        "creative-fabrica-fonts-specialist.toml", "font-final-visual-processor.toml",
        "font-rights-researcher.toml", "pinterest-font-preparer.toml",
        "daily-pinterest-run.toml",
    })
    _add_file(root, selected, ".omp/config.yml")
    _add_tree(root, selected, ".omp/agents", suffixes={".md"}, exclude_names={"pixiv-fonts-specialist.md"})
    _add_tree(root, selected, ".omp/commands", suffixes={".md"}, exclude_names={"pixiv-font.md"})
    _add_tree(root, selected, ".qwen/agents", suffixes={".md"})
    _add_tree(root, selected, ".opencode/skills", suffixes={".md"})

    _add_file(root, selected, "font-factory/AGENTS.md")
    _add_file(root, selected, "font-factory/README.md")
    # Pinterest renderer and only its active 23 templates. Reference photos,
    # retired layouts, and font-review screenshots are not part of the handoff.
    pin_root = "font-factory/pin-html"
    for relative in (
        f"{pin_root}/README.md",
        f"{pin_root}/editor.html",
        f"{pin_root}/render_gallery.mjs",
        f"{pin_root}/render_template.mjs",
    ):
        _add_file(root, selected, relative)
    _add_tree(root, selected, f"{pin_root}/shared", suffixes=TEXT_SUFFIXES | {".svg"})
    _add_tree(root, selected, f"{pin_root}/assets", suffixes={".svg", ".txt"})
    pin_ids = _active_pin_ids(root)
    for template_id in pin_ids:
        _add_tree(
            root, selected, f"{pin_root}/templates/{template_id}",
            suffixes=TEXT_SUFFIXES | {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"},
        )

    catalog, templates = _active_support_sources(root)
    for relative in (
        "font-factory/support-html/AUDIT.md",
        "font-factory/support-html/README.md",
        "font-factory/support-html/catalog.json",
        "font-factory/support-html/render_template.mjs",
    ):
        _add_file(root, selected, relative)
    _add_tree(root, selected, "font-factory/support-html/shared",
              suffixes={".js", ".css", ".md"})
    active_ids: list[str] = []
    for template in templates:
        template_id = template.get("id")
        entry = template.get("htmlEntry")
        if not template_id or not entry:
            raise BuildError("active support template is missing its id or htmlEntry")
        active_ids.append(template_id)
        entry_path = root / "font-factory" / entry
        for source in sorted(entry_path.parent.iterdir()):
            if _is_file(source) and source.suffix.lower() in TEXT_SUFFIXES | {
                ".png", ".jpg", ".jpeg", ".webp", ".gif"
            }:
                selected[source.relative_to(root).as_posix()] = source
    _add_tree(root, selected, "font-factory/support-html/assets",
              suffixes={".ttf", ".otf", ".woff", ".woff2", ".txt", ".png", ".svg"})

    # One catalogue entry uses this source-backed layout bench. Keep its source
    # and label/material assets, but never copy its historical output folder.
    benchmark = "font-factory/support-html/benchmarks/T26074-12"
    for relative in (
        f"{benchmark}/layout-editor.html",
        f"{benchmark}/render_roadrunner.mjs",
    ):
        _add_file(root, selected, relative)
    _add_tree(root, selected, f"{benchmark}/assets",
              suffixes={".ttf", ".otf", ".txt", ".jpg", ".png", ".svg"})

    for relative in (
        "font-factory/support-references/README.md",
        "font-factory/support-references/TEMPLATE-GUIDE.md",
        "font-factory/support-references/REMAKE-MAP.md",
        "font-factory/support-references/IMAGEGEN-PROMPTS.md",
    ):
        _add_file(root, selected, relative)
    material_paths = _selected_render_materials(root, templates)
    for source in material_paths:
        selected[source.relative_to(root).as_posix()] = source

    return selected, active_ids


def _portable_text(text: str, source_root: Path) -> str:
    text = text.replace(str(source_root) + "/", "./").replace(str(source_root), ".")
    text = PROJECT_ROOT_PATTERN.sub(".", text)
    text = MCP_ROOT_PATTERN.sub("${PAPERMOON_MCP_DIR}", text)
    text = REFERENCE_IMAGE_RE.sub(PLACEHOLDER_IMAGE, text)
    return text


def _readme(active_template_count: int) -> str:
    return f"""# Tag & Description Project — Friend Copy

This is a source-only copy of the reusable workflow system. It contains the
agents and workflow definitions, validators and helper code, HTML/CSS
templates, and the selected render ingredients used by active support designs
({active_template_count} support templates). It has no Git history, user font
collections, staged input families, previous preparation packages, generated
renders, source-reference image archive, research databases, or prior runs.
Small open-licensed fonts used inside active support-template layouts remain as
render dependencies; the seller's font collections and product packages do not.

## Install dependencies

- Python 3.10 or newer. Use `uv sync` from the included `pyproject.toml` and
  `uv.lock`, or create a virtual environment and install `requirements.txt`.
- Node.js and npm. Run `npm ci`, then `npx playwright install chromium` for the
  HTML/CSS renderers. Set `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH` only when using
  a Chromium binary outside Playwright's managed browser folder.
- The Skia support-template renderer is optional; install its extra packages
  with `python3 -m pip install -r bin/pin-studio/requirements.txt`. The
  deterministic-visual dependency set is also optional and listed in
  `requirements-deterministic-visuals.txt`.
- Font preparation uses the `ots-sanitize` executable for its independent
  OpenType audit. SVG conversion helpers can use `rsvg-convert`. Image
  conversion/optimization helpers can use ImageMagick (`magick`) and
  `pngquant`; these are system tools and are not bundled. The BOOTH PDF helper
  needs Chromium or Google Chrome on `PATH` (or `CHROMIUM_EXECUTABLE_PATH`).
- Pinterest Blob upload is optional and needs the Vercel CLI plus the user's
  own credentials. Do not commit credentials.

## Agent runtimes

Project registrations are included for Codex, Qwen Code, OMP, and OpenCode.
Install and authenticate whichever runtime you use separately.
Configure your own search/browser MCP services and credentials in that
runtime's local configuration. Machine-specific MCP files and local runtime
settings were deliberately omitted. The shared `/full-workflow` contract is
`agents/agent-28-full-workflow.md`; check registrations with
`python3 bin/check_full_workflow_sync.py`.

The empty `font-factory/` and `outputs/` folders are workflow shells. Add only
the font family you have rights to process, then follow the selected runtime's
native full-workflow entry point. The package does not contain a font or
prepared product.
"""


def _shell_directories() -> tuple[str, ...]:
    return (
        "font-factory/Fonts",
        "font-factory/Saved",
        "font-factory/fonts",
        "font-factory/input",
        "font-factory/font-preparation",
        "font-factory/visuals",
        "outputs/booth",
        "outputs/booth-pdfs",
        "outputs/creative-fabrica",
        "outputs/creativemarket",
        "outputs/dlsite",
        "outputs/font-preparation",
        "outputs/marketore",
        "outputs/pinterest",
        "outputs/pixiv",
        "outputs/research",
        "outputs/yellowimages",
    )


def build_friend_copy(destination: str | Path, source: str | Path | None = None) -> Path:
    """Build and return a separate friend copy; existing data is never removed."""
    source_root = Path(source or Path(__file__).resolve().parents[1]).expanduser().resolve()
    if not (source_root / "AGENTS.md").is_file():
        raise BuildError(f"source is not the project root: {source_root}")
    destination_path = Path(destination).expanduser()
    if not destination_path.is_absolute():
        destination_path = Path.cwd() / destination_path
    destination_path = destination_path.resolve()
    if destination_path == source_root or source_root in destination_path.parents:
        raise BuildError("destination must be outside the source repository")
    if destination_path in source_root.parents:
        raise BuildError("destination cannot contain the source repository")
    if destination_path.is_symlink():
        raise BuildError("destination cannot be a symlink")
    if destination_path.exists():
        if not destination_path.is_dir() or any(destination_path.iterdir()):
            raise BuildError(f"destination already contains data; nothing was changed: {destination_path}")
    else:
        destination_path.mkdir(parents=True)

    selected, active_ids = _select_files(source_root)
    for relative, source_file in sorted(selected.items()):
        target = destination_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if source_file.suffix.lower() in TEXT_SUFFIXES:
            try:
                content = source_file.read_text(encoding="utf-8")
                target.write_text(_portable_text(content, source_root), encoding="utf-8")
                shutil.copystat(source_file, target, follow_symlinks=False)
                continue
            except UnicodeDecodeError:
                pass
        shutil.copy2(source_file, target, follow_symlinks=False)

    for relative in _shell_directories():
        (destination_path / relative).mkdir(parents=True, exist_ok=True)

    readme_path = destination_path / "FRIEND-COPY-README.md"
    readme_path.write_text(_readme(len(active_ids)), encoding="utf-8")
    records = []
    total_bytes = 0
    for path in sorted(p for p in destination_path.rglob("*") if p.is_file()):
        if path.name == "FRIEND-COPY-MANIFEST.json":
            continue
        raw = path.read_bytes()
        total_bytes += len(raw)
        records.append({
            "path": path.relative_to(destination_path).as_posix(),
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        })
    manifest = {
        "policy_version": POLICY_VERSION,
        "generated_by": "bin/build_friend_copy.py",
        "included_file_count": len(records),
        "included_bytes": total_bytes,
        "active_support_template_count": len(active_ids),
        "active_support_template_ids": active_ids,
        "empty_workflow_directories": list(_shell_directories()),
        "excluded_categories": [
            "Git history and runtime dependency installations",
            "font collections, Saved/Input families, and prepared packages",
            "generated renders, prior runs, databases, and research ledgers",
            "source reference originals and reference galleries",
            "machine-local credentials, MCP configs, and runtime settings",
            "font-vault, showroom, video, brush, and other personal applications",
        ],
        "files": records,
    }
    (destination_path / "FRIEND-COPY-MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return destination_path


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", required=True, help="new folder outside the source repository")
    parser.add_argument("--source", help="source project root; defaults to this script's repository")
    args = parser.parse_args(argv)
    try:
        destination = build_friend_copy(args.destination, args.source)
    except (BuildError, OSError, ValueError) as exc:
        print(f"[FAIL] friend copy: {exc}", file=sys.stderr)
        return 1

    manifest = json.loads((destination / "FRIEND-COPY-MANIFEST.json").read_text(encoding="utf-8"))
    print(f"[PASS] friend copy: {destination}")
    print(f"[PASS] files copied: {manifest['included_file_count']}")
    print(f"[PASS] copied source/media size: {manifest['included_bytes'] / 1024 / 1024:.1f} MiB")
    print(f"[PASS] active 3:2/square support templates: {manifest['active_support_template_count']}")
    print("[PASS] Git history, installed dependencies, user font collections, previous outputs/runs, and local credentials excluded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
