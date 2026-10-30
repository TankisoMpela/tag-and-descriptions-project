#!/usr/bin/env python3
"""Audit glyph coverage in the legacy Python/Skia support renderers.

This utility reads Python panel literals only. It does not audit the active
HTML/CSS catalogue: Chromium preserves unsupported characters and renders them
with a browser fallback. Do not use this report as an HTML coverage result.

    bin/check_support_glyph_coverage.py font-factory/fonts/{input-slug}/{Primary}.{ext}
    bin/check_support_glyph_coverage.py --json a.otf b.otf
"""

import argparse
import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUDIO = ROOT / "bin" / "pin-studio"
RENDERER = STUDIO / "pin_studio.py"
PACKAGE = STUDIO / "support_templates"

# A slot that keeps fewer than this share of its letters is a broken image, not
# a reduced one: "Привет!" -> "!" scores 0.14.
EMPTY_AT = 0.55
# Lowercase single words are slot names, palette keys and file stems, never art.
NOT_COPY = re.compile(r"^[a-z][a-z0-9_]*$|^[.#/]|[\\n]\Z|\.(png|otf|ttf|json)\Z")


def catalogue():
    """The selectable support panel names, in catalogue order."""
    block = re.search(r"SUPPORT_ORDER\s*=\s*\((.*?)\n\)", RENDERER.read_text(), re.S)
    return set(re.findall(r'"([a-z0-9_]+)"', block.group(1)))


def literals(path, wanted):
    """{panel: [string, ...]} for every literal inside a panel body."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = {}

    def walk(node):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.FunctionDef) and child.name in wanted:
                bucket = found.setdefault(child.name, [])
                for inner in ast.walk(child):
                    if (isinstance(inner, ast.Constant) and inner.value
                            and isinstance(inner.value, str)):
                        bucket.append(inner.value)
            walk(child)

    walk(tree)
    return found


def codepoints(font_path):
    from fontTools.ttLib import TTFont
    tt = TTFont(str(font_path), fontNumber=0, lazy=True)
    try:
        return {chr(c) for c in tt.getBestCmap()}
    finally:
        tt.close()


def audit(font_path, wanted):
    have = codepoints(font_path)
    strings = {}
    for path in [RENDERER, *sorted(PACKAGE.glob("*.py"))]:
        for panel, found in literals(path, wanted).items():
            strings.setdefault(panel, []).extend(found)
    rows = []
    for panel, words in sorted(strings.items()):
        missing, worst = set(), 1.0
        for text in words:
            if NOT_COPY.search(text) or not any(c.isalpha() or ord(c) > 127
                                                for c in text):
                continue
            letters = [c for c in text if not c.isspace()]
            gaps = [c for c in letters if c not in have]
            if not gaps:
                continue
            missing.update(gaps)
            worst = min(worst, 1 - len(gaps) / len(letters))
        if missing:
            rows.append({"panel": panel, "kept": round(worst, 2),
                         "missing": "".join(sorted(missing))})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("fonts", nargs="+")
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()
    wanted = catalogue()
    import json
    report, broken = {}, 0
    for raw in args.fonts:
        path = Path(raw)
        rows = audit(path, wanted)
        dead = [r for r in rows if r["kept"] < EMPTY_AT]
        report[str(path)] = {"empty_slots": dead, "thinned": rows}
        if not args.as_json:
            print(f"\n== {path.name}")
            if not rows:
                print("   every support panel keeps its full wording")
            for r in rows:
                flag = "EMPTY" if r["kept"] < EMPTY_AT else "thin "
                print(f"   [{flag}] {r['panel']:16s} keeps {r['kept']:.0%} "
                      f"— missing {r['missing']!r}")
        broken += len(dead)
    if args.as_json:
        print(json.dumps(report, indent=2))
    print(f"\n{broken} panel(s) would render an effectively empty slot "
          f"across {len(args.fonts)} font(s)")
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
