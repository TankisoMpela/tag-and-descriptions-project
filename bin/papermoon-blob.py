#!/usr/bin/env python3
"""PaperMoon Vercel Blob wrapper for Pinterest pin images.

Fills the gaps of `vercel blob`: deterministic pathname naming, public-URL
table output, and JSON results (`vercel blob list` has no --json).

Auth comes from ~/.config/papermoon/blob.env (BLOB_READ_WRITE_TOKEN +
BLOB_PUBLIC_BASE). BLOB_STORE_ID is deliberately never passed: the CLI rejects
it when combined with the read-write token.

Usage:
  python3 bin/papermoon-blob.py upload <file> --slug <slug> [--index N]
  python3 bin/papermoon-blob.py upload <file> --pathname fonts/x/y.png
  python3 bin/papermoon-blob.py list [--prefix fonts/]
  python3 bin/papermoon-blob.py url <pathname>
  python3 bin/papermoon-blob.py del <pathname> [<pathname> ...]
  Add --json to any command for machine-readable output.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ENV_FILE = Path.home() / ".config" / "papermoon" / "blob.env"
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".avif"}


def load_env() -> dict[str, str]:
    env: dict[str, str] = {}
    if not ENV_FILE.exists():
        sys.exit(f"error: {ENV_FILE} not found — create it with BLOB_READ_WRITE_TOKEN and BLOB_PUBLIC_BASE")
    for line in ENV_FILE.read_text().splitlines():
        m = re.match(r"^(BLOB_[A-Z_]+)=(.+)$", line.strip())
        if m:
            env[m.group(1)] = m.group(2).strip().strip('"')
    missing = {"BLOB_READ_WRITE_TOKEN", "BLOB_PUBLIC_BASE"} - env.keys()
    if missing:
        sys.exit(f"error: {ENV_FILE} missing {', '.join(sorted(missing))}")
    return env


def vercel_env(env: dict[str, str]) -> dict[str, str]:
    child = dict(__import__("os").environ)
    child["BLOB_READ_WRITE_TOKEN"] = env["BLOB_READ_WRITE_TOKEN"]
    child.pop("BLOB_STORE_ID", None)
    return child


def run_blob(args: list[str], env: dict[str, str]) -> str:
    if shutil.which("vercel") is None:
        sys.exit("error: vercel CLI not found on PATH")
    proc = subprocess.run(
        ["vercel", "blob", *args], capture_output=True, text=True, env=vercel_env(env)
    )
    out = proc.stdout + proc.stderr
    if proc.returncode != 0:
        sys.exit(f"error: vercel blob {' '.join(args[:1])} failed:\n{out.strip()}")
    return out


def parse_url(stdout: str) -> str:
    m = re.search(r"Success!\s+(https://\S+)", stdout)
    if not m:
        m = re.search(r"(https://\S+\.public\.blob\.vercel-storage\.com\S*)", stdout)
    if not m:
        sys.exit(f"error: could not find blob URL in output:\n{stdout.strip()}")
    return m.group(1).rstrip(".")


def parse_list(stdout: str) -> list[dict[str, str]]:
    rows = []
    for line in stdout.splitlines():
        m = re.match(r"\s*(\S+)\s+(\S+)\s+(\S+)\s+(https://\S+)\s*$", line)
        if m:
            rows.append({"uploaded_at": m.group(1), "size": m.group(2),
                         "pathname": m.group(3), "url": m.group(4)})
    return rows


def default_pathname(file: Path, slug: str, index: int | None) -> str:
    ext = file.suffix.lower()
    if ext not in IMAGE_EXTENSIONS:
        sys.exit(f"error: unsupported image extension {ext or '(none)'} for {file}")
    name = f"pinterest_{index}" if index is not None else file.stem
    return f"fonts/{slug}/{name}{ext}"


def cmd_upload(args, env) -> int:
    file = Path(args.file)
    if not file.is_file():
        sys.exit(f"error: file not found: {file}")
    pathname = args.pathname or default_pathname(file, args.slug, args.index)
    out = run_blob([
        "put", str(file), "--access", "public", "--pathname", pathname,
        "--allow-overwrite", "true",
    ], env)
    url = parse_url(out)
    result = {"pathname": pathname, "url": url, "source": str(file)}
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(url)
    return 0


def cmd_list(args, env) -> int:
    out = run_blob(["list", "--prefix", args.prefix, "--limit", "1000"], env)
    rows = parse_list(out)
    if args.json:
        print(json.dumps(rows, indent=2))
    elif not rows:
        print("(empty)")
    else:
        for r in rows:
            print(f"{r['pathname']}\t{r['url']}")
    return 0


def cmd_url(args, env) -> int:
    print(f"{env['BLOB_PUBLIC_BASE'].rstrip('/')}/{args.pathname.lstrip('/')}")
    return 0


def cmd_del(args, env) -> int:
    out = run_blob(["del", *args.pathnames], env)
    if args.json:
        print(json.dumps({"deleted": args.pathnames}, indent=2))
    else:
        print(out.strip().splitlines()[-1])
    return 0


def main(argv=None) -> int:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", help="machine-readable output")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="command", required=True)

    up = sub.add_parser("upload", parents=[common], help="upload one image and print its public URL")
    up.add_argument("file")
    up.add_argument("--slug", help="font slug for the default pathname fonts/{slug}/…")
    up.add_argument("--index", type=int, help="pinterest image number (1-4)")
    up.add_argument("--pathname", help="explicit target pathname (overrides --slug/--index)")
    up.set_defaults(func=cmd_upload)

    li = sub.add_parser("list", parents=[common], help="list stored files")
    li.add_argument("--prefix", default="fonts/")
    li.set_defaults(func=cmd_list)

    ur = sub.add_parser("url", parents=[common], help="public URL for a pathname")
    ur.add_argument("pathname")
    ur.set_defaults(func=cmd_url)

    de = sub.add_parser("del", parents=[common], help="delete pathnames")
    de.add_argument("pathnames", nargs="+")
    de.set_defaults(func=cmd_del)

    args = ap.parse_args(argv)
    if args.command == "upload" and not (args.pathname or (args.slug and args.index is not None)):
        ap.error("upload needs --pathname, or --slug with --index")
    return args.func(args, load_env())


if __name__ == "__main__":
    sys.exit(main())
