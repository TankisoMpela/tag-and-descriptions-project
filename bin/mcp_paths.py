"""Resolve optional local MCP proxy scripts without machine-specific paths."""

from __future__ import annotations

import os
from pathlib import Path


def configured_mcp_script(filename: str) -> Path | None:
    """Return a configured proxy script, or None when no local proxy is set.

    A per-server override such as ``PAPERMOON_FIRECRAWL_MCP`` takes precedence
    over ``PAPERMOON_MCP_DIR``. Secrets and connector configuration stay in the
    user's runtime environment and are never stored in this repository.
    """
    server = filename.removesuffix("_mcp.py").upper()
    direct = os.environ.get(f"PAPERMOON_{server}_MCP")
    if direct:
        return Path(direct).expanduser()
    directory = os.environ.get("PAPERMOON_MCP_DIR")
    if directory:
        return Path(directory).expanduser() / filename
    return None


def require_mcp_script(filename: str) -> Path:
    path = configured_mcp_script(filename)
    if path is None:
        raise RuntimeError(
            f"No local MCP proxy configured for {filename}; set PAPERMOON_MCP_DIR "
            f"or PAPERMOON_{filename.removesuffix('_mcp.py').upper()}_MCP"
        )
    if not path.is_file():
        raise FileNotFoundError(f"configured MCP proxy script does not exist: {path}")
    return path
