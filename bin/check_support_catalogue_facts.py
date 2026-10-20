#!/usr/bin/env python3
"""Print the facts TEMPLATE-GUIDE.md quotes about the support catalogue.

Reads the renderer and the five remake modules as text, so it runs on plain
python3 (no skia needed). Use it whenever a guide number and a render disagree:

    python3 bin/check_support_catalogue_facts.py

Exit code is 0 unless a referenced material is missing or a panel's facts cannot
be parsed, which is what tells you the modules moved.
"""
import ast
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
STUDIO = ROOT / "bin/pin-studio/pin_studio.py"
TEMPLATES = ROOT / "bin/pin-studio/support_templates"
MATERIALS = ROOT / "font-factory/support-references"

# `inlet` = a call that can put authored copy on the panel. panel_text and
# lead_in always read; support_copy only when its key tuple is non-empty.
INLET = re.compile(
    r'(?:g\["(?:panel_text|_support_copy|lead_in|rolled)"\]'
    r'|(?<![\w.])(?:panel_text|_support_copy|support_copy|lead_in|rolled))'
    r'\s*\(\s*ctx\s*,\s*(\([^)]*\))?')
PANEL = re.compile(r'@support\("([a-z0-9]+32)"|'
                   r'^\s*def _?(?:t_)?([a-z0-9]+32)\(', re.M)
NEXT_DEF = re.compile(r'^\s*(?:def |@support\()', re.M)
MATERIAL = re.compile(r'"materials/([A-Za-z0-9_.\- ]+\.png)"')


def const(name):
    """Read one module-level literal, whatever it wraps itself in."""
    src = STUDIO.read_text()
    m = re.search(rf'^{name}\s*=\s*', src, re.M)
    if not m:
        sys.exit(f"cannot find {name} in {STUDIO}")
    depth, end = 0, None
    for i in range(m.end(), len(src)):
        ch = src[i]
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
        elif ch == "\n" and depth == 0:
            end = i
            break
    if end is None:
        sys.exit(f"cannot read the value of {name}")
    expr = re.sub(r'frozenset\((.*)\)', r'\1', src[m.end():end].strip(),
                  flags=re.S)
    return ast.literal_eval(expr)


def panels():
    """Yield (module, panel, body) for every remake panel.

    A panel may be marked by its `@support` decorator, by its `def`, or by both;
    the decorator wins, so the pair collapses to one boundary.
    """
    for path in sorted(TEMPLATES.glob("*.py")):
        src = path.read_text()
        hits = []
        for m in PANEL.finditer(src):
            name = m.group(1) or m.group(2)
            if hits and hits[-1][1] == name:
                continue
            hits.append((m.start(), name))
        for i, (pos, name) in enumerate(hits):
            end = hits[i + 1][0] if i + 1 < len(hits) else len(src)
            yield path.stem, name, src[pos:end]


def authored(body):
    for m in INLET.finditer(body):
        keys = m.group(1)
        if keys is None or keys.strip(" ()"):
            return True
    return False


def hard_fails(body):
    """True when a missing material makes the panel draw nothing at all."""
    return bool(re.search(r'is None:\s*\n\s*return\b', body))


def palette_direct(body):
    """A palette read inside this panel's own code.

    The only honest static answer to "does the theme move this panel", because
    shared module helpers can inherit the theme too (see `shared_palette_reads`)
    and a render is the only proof of what they were passed.
    """
    return bool(re.search(r'ctx\["pal"\]|pal\[|theme_ink\(', body))


def shared_palette_reads():
    """Helpers outside any panel body that read the theme, by module."""
    out = []
    for path in sorted(TEMPLATES.glob("*.py")):
        src = path.read_text()
        spans = [(m.start(), m.end()) for m in PANEL.finditer(src)]
        for m in re.finditer(r'^\s*def (\w+)\(', src, re.M):
            if any(a <= m.start() < b for a, b in spans):
                continue
            rest = NEXT_DEF.search(src, m.end())
            body = src[m.end():rest.start()] if rest else src[m.end():]
            if re.search(r'ctx\["pal"\]|pal\[|theme_ink\(', body):
                out.append(f"{path.stem}.{m.group(1)}()")
    return out


def main():
    order = const("SUPPORT_ORDER")
    retired = const("SUPPORT_RETIRED")
    print(f"SUPPORT_ORDER: {len(order)} selectable, "
          f"SUPPORT_RETIRED: {len(retired)}")
    rows, problems = [], []
    for module, name, body in panels():
        rows.append((module, name, authored(body), hard_fails(body),
                     palette_direct(body)))
    print(f"{'panel':22s} {'module':8s} copy material palette")
    for module, name, cp, hf, pal in rows:
        print(f"  {name:20s} {module:8s} "
              f"{'reads ' if cp else 'fixed '} "
              f"{'BAILS ' if hf else '      '} "
              f"{'theme' if pal else 'no-direct'}")
    print(f"summary: {sum(r[2] for r in rows)} read copy, "
          f"{sum(not r[2] for r in rows)} fixed; "
          f"{sum(r[3] for r in rows)} bail out on missing material; "
          f"{sum(r[4] for r in rows)} read the theme palette in their own body")
    shared = shared_palette_reads()
    if shared:
        print("shared helpers that read the theme (panels calling these can "
              "move with the palette even when listed no-direct; prove it with "
              "bin/check_support_theme_lock.py): " + ", ".join(shared))

    refs = set()
    for path in list(TEMPLATES.glob("*.py")) + [STUDIO]:
        refs.update(MATERIAL.findall(path.read_text()))
    missing = sorted(r for r in refs
                     if not (MATERIALS / "materials" / r).is_file())
    print(f"materials referenced: {len(refs)}, missing: {len(missing)}")
    for m in missing:
        problems.append(f"MISSING material {m}")
        print(f"  missing: {m}")

    # Full-bleed marks that omit bleed=True are the known OFF-CANVAS class; the
    # render's own VERIFY is the authority, so this tool only counts what it can
    # see statically: the marks whose box is the whole canvas.
    edge = sorted({name for _, name, body in panels()
                   for mk in re.finditer(r'(?:mark|_safe_mark)\((.*?)\)\n',
                                         body, re.S)
                   if re.search(r'0, 0, sh\.w, sh\.h', mk.group(1))
                   and 'bleed=True' not in mk.group(1)})
    if edge:
        print("full-canvas marks without bleed=True: " + ", ".join(edge))
    if problems:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
