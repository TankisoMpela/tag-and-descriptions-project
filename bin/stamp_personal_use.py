#!/usr/bin/env python3
"""Watermark FontFairy free-trial-demo fonts with the circular demo stamp.

Two modes:

  outline  Convert the authored stamp SVG (text nodes) into a path-only SVG
           that font embedding can read. Uses rsvg-convert + potrace so the
           outlines match the approved raster preview exactly.

  stamp    Replace the outlines of selected glyphs in OTF/TTF files with the
           stamp, scaled to the font's em box. WOFF/WOFF2 are regenerated from
           the stamped OTF. Default coverage locks digits and ASCII
           punctuation (letters stay clean for previewing), matching the
           charset-class lock used by commercial demo fonts.

The commercial and personal package folders are never modified in place when
called from prepare_font_package.py — stamping writes to a separate tree used
only for the Free-Trial-Demo archive.

Usage:
    python3 bin/stamp_personal_use.py outline \\
        font-factory/stamps/fontfairy-demo.svg \\
        font-factory/stamps/fontfairy-demo-paths.svg

    python3 bin/stamp_personal_use.py stamp \\
        --package-dir outputs/font-preparation/90-x/Font-Name \\
        --out-dir /tmp/stamped \\
        [--stamp font-factory/stamps/fontfairy-demo-paths.svg] \\
        [--coverage digits,punct]
"""
from __future__ import annotations

import argparse
import math
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_STAMP_SVG = ROOT / "font-factory" / "stamps" / "fontfairy-demo.svg"
DEFAULT_STAMP_PATHS = ROOT / "font-factory" / "stamps" / "fontfairy-demo-paths.svg"
FONT_SUFFIXES = (".otf", ".ttf", ".woff", ".woff2")

# Coverage classes. "digits,punct" is the CalligraphyFonts-style soft lock:
# letters render clean so the face can be previewed; every numeral and symbol
# becomes the badge.
_COVERAGE_RANGES: dict[str, list[tuple[int, int]]] = {
    "digits": [(0x30, 0x39), (0xFF10, 0xFF19)],
    "punct": [
        (0x21, 0x2F), (0x3A, 0x40), (0x5B, 0x60), (0x7B, 0x7E),
        (0xA1, 0xBF), (0x2010, 0x2027), (0x2030, 0x205E),
        (0xFF01, 0xFF0F), (0xFF1A, 0xFF20), (0xFF3B, 0xFF40), (0xFF5B, 0xFF65),
    ],
    "letters": [(0x41, 0x5A), (0x61, 0x7A), (0xC0, 0x24F), (0x391, 0x3C9)],
}


def parse_coverage(spec: str) -> set[int]:
    """Expand a coverage spec into a set of codepoints.

    Accepts comma-separated class names (digits, punct, letters, all) and/or
    hex ranges like ``41-5A`` or single codepoints like ``26``.
    """
    if spec.strip().lower() == "all":
        # Everything cmap will resolve; caller intersects with the font.
        return set(range(0x0000, 0x10000))
    codepoints: set[int] = set()
    for part in spec.split(","):
        token = part.strip().lower()
        if not token:
            continue
        if token in _COVERAGE_RANGES:
            for lo, hi in _COVERAGE_RANGES[token]:
                codepoints.update(range(lo, hi + 1))
            continue
        if "-" in token:
            lo_s, hi_s = token.split("-", 1)
            codepoints.update(range(int(lo_s, 16), int(hi_s, 16) + 1))
            continue
        codepoints.add(int(token, 16))
    if not codepoints:
        raise SystemExit(f"empty coverage spec: {spec!r}")
    return codepoints


# ---------------------------------------------------------------------------
# SVG path parsing (potrace emits M/m/l/c/z only; keep a small general parser)
# ---------------------------------------------------------------------------

_PATH_TOKEN = re.compile(
    r"([MmZzLlHhVvCcSsQqTtAa])|(-?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)"
)


def _parse_path_d(d: str) -> list[list[tuple[str, tuple[float, ...]]]]:
    """Parse an SVG path into contours of absolute cubic/line segments.

    Returns a list of contours; each contour is a list of
    ``("M"|"L"|"C", points)`` with absolute coordinates. Quadratic and arc
    segments are converted to cubics. Relative commands are resolved.
    """
    tokens: list[str] = []
    for match in _PATH_TOKEN.finditer(d):
        tokens.append(match.group(1) if match.group(1) else match.group(2))
    if not tokens:
        return []

    contours: list[list[tuple[str, tuple[float, ...]]]] = []
    current: list[tuple[str, tuple[float, ...]]] = []
    i = 0
    x = y = 0.0
    start_x = start_y = 0.0
    prev_cmd = ""
    prev_ctrl: tuple[float, float] | None = None  # last cubic control point
    prev_quad_ctrl: tuple[float, float] | None = None

    def take(n: int) -> list[float]:
        nonlocal i
        vals = [float(tokens[i + k]) for k in range(n)]
        i += n
        return vals

    def flush() -> None:
        nonlocal current
        if current:
            contours.append(current)
            current = []

    while i < len(tokens):
        tok = tokens[i]
        if tok.isalpha():
            cmd = tok
            i += 1
        else:
            # implicit repeat of previous command (M/m becomes L/l)
            if prev_cmd in ("M", "m"):
                cmd = "L" if prev_cmd == "M" else "l"
            elif prev_cmd:
                cmd = prev_cmd
            else:
                raise SystemExit(f"path data starts with a number: {d[:80]!r}")

        abs_cmd = cmd.upper()
        relative = cmd.islower()

        if abs_cmd == "M":
            fx, fy = take(2)
            if relative:
                fx, fy = x + fx, y + fy
            flush()
            current.append(("M", (fx, fy)))
            x, y = fx, fy
            start_x, start_y = fx, fy
            prev_ctrl = None
            prev_quad_ctrl = None
            # subsequent pairs are implicit lineto
            prev_cmd = "m" if relative else "M"
            # consume extra coordinate pairs as lineto
            while i < len(tokens) and not tokens[i].isalpha():
                lx, ly = float(tokens[i]), float(tokens[i + 1])
                i += 2
                if relative:
                    lx, ly = x + lx, y + ly
                current.append(("L", (lx, ly)))
                x, y = lx, ly
            continue

        if abs_cmd == "Z":
            if current:
                current.append(("L", (start_x, start_y)))
            x, y = start_x, start_y
            flush()
            prev_ctrl = None
            prev_quad_ctrl = None
            prev_cmd = "Z"
            continue

        if abs_cmd == "L":
            lx, ly = take(2)
            if relative:
                lx, ly = x + lx, y + ly
            current.append(("L", (lx, ly)))
            x, y = lx, ly
            prev_ctrl = None
            prev_quad_ctrl = None
        elif abs_cmd == "H":
            (lx,) = take(1)
            if relative:
                lx = x + lx
            current.append(("L", (lx, y)))
            x = lx
            prev_ctrl = None
            prev_quad_ctrl = None
        elif abs_cmd == "V":
            (ly,) = take(1)
            if relative:
                ly = y + ly
            current.append(("L", (x, ly)))
            y = ly
            prev_ctrl = None
            prev_quad_ctrl = None
        elif abs_cmd == "C":
            x1, y1, x2, y2, cx, cy = take(6)
            if relative:
                x1, y1, x2, y2, cx, cy = x + x1, y + y1, x + x2, y + y2, x + cx, y + cy
            current.append(("C", (x1, y1, x2, y2, cx, cy)))
            prev_ctrl = (x2, y2)
            prev_quad_ctrl = None
            x, y = cx, cy
        elif abs_cmd == "S":
            x2, y2, cx, cy = take(4)
            if relative:
                x2, y2, cx, cy = x + x2, y + y2, x + cx, y + cy
            if prev_cmd.upper() in ("C", "S") and prev_ctrl is not None:
                x1, y1 = 2 * x - prev_ctrl[0], 2 * y - prev_ctrl[1]
            else:
                x1, y1 = x, y
            current.append(("C", (x1, y1, x2, y2, cx, cy)))
            prev_ctrl = (x2, y2)
            prev_quad_ctrl = None
            x, y = cx, cy
        elif abs_cmd == "Q":
            qx, qy, cx, cy = take(4)
            if relative:
                qx, qy, cx, cy = x + qx, y + qy, x + cx, y + cy
            c1x, c1y = x + 2 / 3 * (qx - x), y + 2 / 3 * (qy - y)
            c2x, c2y = cx + 2 / 3 * (qx - cx), cy + 2 / 3 * (qy - cy)
            current.append(("C", (c1x, c1y, c2x, c2y, cx, cy)))
            prev_quad_ctrl = (qx, qy)
            prev_ctrl = None
            x, y = cx, cy
        elif abs_cmd == "T":
            cx, cy = take(2)
            if relative:
                cx, cy = x + cx, y + cy
            if prev_cmd.upper() in ("Q", "T") and prev_quad_ctrl is not None:
                qx, qy = 2 * x - prev_quad_ctrl[0], 2 * y - prev_quad_ctrl[1]
            else:
                qx, qy = x, y
            c1x, c1y = x + 2 / 3 * (qx - x), y + 2 / 3 * (qy - y)
            c2x, c2y = cx + 2 / 3 * (qx - cx), cy + 2 / 3 * (qy - cy)
            current.append(("C", (c1x, c1y, c2x, c2y, cx, cy)))
            prev_quad_ctrl = (qx, qy)
            prev_ctrl = None
            x, y = cx, cy
        elif abs_cmd == "A":
            rx, ry, rot, large, sweep, ax, ay = take(7)
            if relative:
                ax, ay = x + ax, y + ay
            # Flat cubic approximation is enough for stamp badges (potrace
            # does not emit arcs; this path is for hand-edited SVGs).
            mx, my = (x + ax) / 2, (y + ay) / 2
            current.append(("C", (x, y, mx, my, ax, ay)))
            x, y = ax, ay
            prev_ctrl = None
            prev_quad_ctrl = None
        else:
            raise SystemExit(f"unsupported path command {cmd!r}")

        prev_cmd = cmd

    flush()
    return [c for c in contours if len(c) >= 2]


def _apply_matrix(
    pt: tuple[float, float], a: float, b: float, c: float, d: float, e: float, f: float
) -> tuple[float, float]:
    x, y = pt
    return (a * x + c * y + e, b * x + d * y + f)


def _parse_transform(text: str) -> tuple[float, float, float, float, float, float]:
    """Parse an SVG transform list into a single 2x3 matrix."""
    a, b, c, d, e, f = 1.0, 0.0, 0.0, 1.0, 0.0, 0.0

    def mul(m1, m2):
        a1, b1, c1, d1, e1, f1 = m1
        a2, b2, c2, d2, e2, f2 = m2
        return (
            a1 * a2 + c1 * b2,
            b1 * a2 + d1 * b2,
            a1 * c2 + c1 * d2,
            b1 * c2 + d1 * d2,
            a1 * e2 + c1 * f2 + e1,
            b1 * e2 + d1 * f2 + f1,
        )

    for name, args_s in re.findall(r"(\w+)\s*\(([^)]*)\)", text or ""):
        nums = [float(n) for n in re.findall(r"-?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?", args_s)]
        name = name.lower()
        if name == "translate":
            tx = nums[0] if nums else 0.0
            ty = nums[1] if len(nums) > 1 else 0.0
            m = (1, 0, 0, 1, tx, ty)
        elif name == "scale":
            sx = nums[0] if nums else 1.0
            sy = nums[1] if len(nums) > 1 else sx
            m = (sx, 0, 0, sy, 0, 0)
        elif name == "rotate":
            ang = math.radians(nums[0] if nums else 0.0)
            cos_a, sin_a = math.cos(ang), math.sin(ang)
            m = (cos_a, sin_a, -sin_a, cos_a, 0, 0)
            if len(nums) >= 3:
                cx, cy = nums[1], nums[2]
                m = mul((1, 0, 0, 1, cx, cy), mul(m, (1, 0, 0, 1, -cx, -cy)))
        elif name == "matrix" and len(nums) >= 6:
            m = tuple(nums[:6])  # type: ignore[assignment]
        else:
            continue
        a, b, c, d, e, f = mul((a, b, c, d, e, f), m)  # type: ignore[arg-type]
    return (a, b, c, d, e, f)


def load_stamp_contours(svg_path: Path) -> tuple[list[list[tuple[str, tuple[float, ...]]]], float, float]:
    """Load stamp contours from a path-only SVG.

    Returns (contours in SVG user units, viewBox width, viewBox height).
    Only <path d> elements are read; run ``outline`` first on authored SVGs.
    """
    import xml.etree.ElementTree as ET

    svg_path = Path(svg_path)
    if not svg_path.is_file():
        raise SystemExit(f"stamp SVG not found: {svg_path}")
    text = svg_path.read_text(encoding="utf-8")
    if re.search(r"<text[\s>]", text):
        raise SystemExit(
            f"{svg_path} still contains <text> nodes; run the outline mode first:\n"
            f"  python3 bin/stamp_personal_use.py outline {svg_path} {svg_path.with_name(svg_path.stem + '-paths.svg')}"
        )

    root = ET.fromstring(text)
    vb_w, vb_h = 1000.0, 1000.0
    vb = root.get("viewBox")
    if vb:
        parts = [float(p) for p in re.split(r"[\s,]+", vb.strip())]
        if len(parts) == 4:
            vb_w, vb_h = parts[2], parts[3]
    else:
        vb_w = float(root.get("width", "1000").replace("pt", "") or 1000)
        vb_h = float(root.get("height", "1000").replace("pt", "") or 1000)

    ns = {"svg": "http://www.w3.org/2000/svg"}
    contours: list[list[tuple[str, tuple[float, ...]]]] = []

    def walk(node, mat):
        tag = node.tag.split("}")[-1]
        local = mat
        if node.get("transform"):
            local = _mul_mat(mat, _parse_transform(node.get("transform", "")))
        if tag == "path" and node.get("d"):
            for contour in _parse_path_d(node.get("d", "")):
                moved: list[tuple[str, tuple[float, ...]]] = []
                for op, pts in contour:
                    if op == "M":
                        moved.append(("M", _apply_matrix((pts[0], pts[1]), *local)))
                    elif op == "L":
                        moved.append(("L", _apply_matrix((pts[0], pts[1]), *local)))
                    elif op == "C":
                        c1 = _apply_matrix((pts[0], pts[1]), *local)
                        c2 = _apply_matrix((pts[2], pts[3]), *local)
                        ep = _apply_matrix((pts[4], pts[5]), *local)
                        moved.append(("C", (c1[0], c1[1], c2[0], c2[1], ep[0], ep[1])))
                if len(moved) >= 2:
                    contours.append(moved)
        for child in node:
            walk(child, local)

    walk(root, (1.0, 0.0, 0.0, 1.0, 0.0, 0.0))
    if not contours:
        raise SystemExit(f"no path outlines found in {svg_path}")
    return contours, vb_w, vb_h


def _mul_mat(m1, m2):
    a1, b1, c1, d1, e1, f1 = m1
    a2, b2, c2, d2, e2, f2 = m2
    return (
        a1 * a2 + c1 * b2,
        b1 * a2 + d1 * b2,
        a1 * c2 + c1 * d2,
        b1 * c2 + d1 * d2,
        a1 * e2 + c1 * f2 + e1,
        b1 * e2 + d1 * f2 + f1,
    )


# ---------------------------------------------------------------------------
# Outline mode: authored SVG (text) -> path-only SVG via rsvg + potrace
# ---------------------------------------------------------------------------

def outline_stamp(src: Path, dst: Path, px: int = 2400) -> Path:
    """Rasterize the authored stamp and trace it to path outlines.

    Preserves the source viewBox aspect ratio (so a taller badge with a URL
    under the circle is not squashed into a square) and emits one path with
    ``fill-rule="evenodd"`` so DEMO/USE knockouts stay holes.
    """
    src = Path(src)
    dst = Path(dst)
    if not src.is_file():
        raise SystemExit(f"stamp SVG not found: {src}")

    rsvg = shutil.which("rsvg-convert")
    potrace = shutil.which("potrace")
    magick = shutil.which("magick") or shutil.which("convert")
    if not rsvg or not potrace or not magick:
        missing = [n for n, p in (("rsvg-convert", rsvg), ("potrace", potrace), ("magick", magick)) if not p]
        raise SystemExit("missing tools for outline mode: " + ", ".join(missing))

    # Read source viewBox for aspect-correct raster + output size.
    src_text = src.read_text(encoding="utf-8")
    vb_m = re.search(r'viewBox="([\d.\s-]+)"', src_text)
    if vb_m:
        parts = [float(x) for x in vb_m.group(1).split()]
        vb_w, vb_h = parts[2], parts[3]
    else:
        vb_w = vb_h = 1000.0

    # Raster size: longer side = px, keep aspect.
    if vb_w >= vb_h:
        raster_w, raster_h = px, max(1, int(round(px * vb_h / vb_w)))
    else:
        raster_h, raster_w = px, max(1, int(round(px * vb_w / vb_h)))

    dst.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="stamp-outline-") as td:
        tdp = Path(td)
        png = tdp / "stamp.png"
        pbm = tdp / "stamp.pbm"
        traced = tdp / "stamp.svg"
        subprocess.run(
            [rsvg, "-w", str(raster_w), "-h", str(raster_h), "-b", "white", str(src), "-o", str(png)],
            check=True, capture_output=True,
        )
        subprocess.run(
            [magick, str(png), "-colorspace", "Gray", "-threshold", "50%", str(pbm)],
            check=True, capture_output=True,
        )
        subprocess.run(
            [potrace, str(pbm), "-s", "-o", str(traced), "--turdsize", "4",
             "--alphamax", "1.0", "--opttolerance", "0.05"],
            check=True, capture_output=True,
        )
        traced_text = traced.read_text(encoding="utf-8")

    path_ds = re.findall(r'\sd="([^"]+)"', traced_text)
    if not path_ds:
        raise SystemExit("potrace produced no paths")

    group_m = re.search(r'<g\s+transform="([^"]+)"', traced_text)
    mat = _parse_transform(group_m.group(1)) if group_m else (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)

    all_pts: list[tuple[float, float]] = []
    contours_out: list[list[tuple[str, tuple[float, ...]]]] = []
    for d in path_ds:
        for contour in _parse_path_d(d):
            moved: list[tuple[str, tuple[float, ...]]] = []
            for op, pts in contour:
                if op == "M" or op == "L":
                    p = _apply_matrix((pts[0], pts[1]), *mat)
                    moved.append((op, p))
                    all_pts.append(p)
                else:
                    c1 = _apply_matrix((pts[0], pts[1]), *mat)
                    c2 = _apply_matrix((pts[2], pts[3]), *mat)
                    ep = _apply_matrix((pts[4], pts[5]), *mat)
                    moved.append(("C", (c1[0], c1[1], c2[0], c2[1], ep[0], ep[1])))
                    all_pts.extend([c1, c2, ep])
            if len(moved) >= 2:
                contours_out.append(moved)

    if not all_pts:
        raise SystemExit("outline produced no points")

    min_x = min(p[0] for p in all_pts)
    max_x = max(p[0] for p in all_pts)
    min_y = min(p[1] for p in all_pts)
    max_y = max(p[1] for p in all_pts)
    width = max(max_x - min_x, 1.0)
    height = max(max_y - min_y, 1.0)

    # Fit content into the source viewBox (aspect preserved), centered.
    margin = 12.0
    out_w, out_h = vb_w, vb_h
    scale = min((out_w - 2 * margin) / width, (out_h - 2 * margin) / height)
    off_x = (out_w - width * scale) / 2 - min_x * scale
    off_y = (out_h - height * scale) / 2 - min_y * scale

    def emit_path(contour) -> str:
        parts: list[str] = []
        for idx, (op, pts) in enumerate(contour):
            if op in ("M", "L"):
                x = pts[0] * scale + off_x
                y = pts[1] * scale + off_y
                parts.append(f"{'M' if idx == 0 or op == 'M' else 'L'}{x:.2f},{y:.2f}")
            else:
                coords = [
                    pts[0] * scale + off_x, pts[1] * scale + off_y,
                    pts[2] * scale + off_x, pts[3] * scale + off_y,
                    pts[4] * scale + off_x, pts[5] * scale + off_y,
                ]
                parts.append("C" + ",".join(f"{c:.2f}" for c in coords))
        parts.append("Z")
        return "".join(parts)

    # One path + evenodd so letter/URL counters and DEMO/USE knockouts
    # remain holes when previewed; font pens use winding and get the same.
    combined = "".join(emit_path(c) for c in contours_out)
    # ViewBox may be non-square; use integer-ish formatting for width/height.
    vw = f"{out_w:g}"
    vh = f"{out_h:g}"
    svg = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<!--\n"
        "  FontFairy demo stamp — path outlines generated by\n"
        "  bin/stamp_personal_use.py outline. Do not hand-edit text into this\n"
        "  file; edit fontfairy-demo.svg and re-run outline mode.\n"
        "-->\n"
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {vw} {vh}" width="{vw}" height="{vh}">\n'
        f'  <path fill="#000000" fill-rule="evenodd" d="{combined}"/>\n'
        "</svg>\n"
    )
    dst.write_text(svg, encoding="utf-8")
    print(f"outlined {src.name} -> {dst} ({len(contours_out)} contours, viewBox {vw}x{vh})")
    return dst


# ---------------------------------------------------------------------------
# Stamp mode: replace glyph outlines
# ---------------------------------------------------------------------------

def _contours_to_pen(
    contours: list[list[tuple[str, tuple[float, ...]]]],
    pen,
    scale: float,
    dx: float,
    dy: float,
    flip_y: bool,
    origin_y: float,
) -> None:
    """Draw stamp contours into a fontTools pen with fit transform."""

    def tx(x: float, y: float) -> tuple[float, float]:
        if flip_y:
            # SVG y-down -> font y-up: y' = origin_y - (y - 0)*scale + dy
            return (x * scale + dx, origin_y - y * scale + dy)
        return (x * scale + dx, y * scale + dy)

    for contour in contours:
        started = False
        for op, pts in contour:
            if op == "M":
                if started:
                    pen.closePath()
                pen.moveTo(tx(pts[0], pts[1]))
                started = True
            elif op == "L":
                pen.lineTo(tx(pts[0], pts[1]))
            elif op == "C":
                pen.curveTo(
                    tx(pts[0], pts[1]),
                    tx(pts[2], pts[3]),
                    tx(pts[4], pts[5]),
                )
        if started:
            pen.closePath()


def _fit_transform(
    contours: list[list[tuple[str, tuple[float, ...]]]],
    vb_w: float,
    vb_h: float,
    upem: int,
    advance: int,
) -> tuple[float, float, float, bool, float, int]:
    """Scale/translate the stamp into the glyph cell.

    Returns (scale, dx, dy, flip_y, origin_y, new_advance). The badge fills
    ~0.92 em and the advance is widened to the badge width so the circle is
    not crushed into a narrow digit cell.
    """
    pts: list[tuple[float, float]] = []
    for contour in contours:
        for op, p in contour:
            if op in ("M", "L"):
                pts.append((p[0], p[1]))
            else:
                pts.extend([(p[0], p[1]), (p[2], p[3]), (p[4], p[5])])
    min_x = min(p[0] for p in pts)
    max_x = max(p[0] for p in pts)
    min_y = min(p[1] for p in pts)
    max_y = max(p[1] for p in pts)
    box_w = max(max_x - min_x, 1.0)
    box_h = max(max_y - min_y, 1.0)

    # Solid badge: use nearly the full em height. Widen the stamped advance so
    # the circle is not squeezed into a narrow digit cell (that was the old
    # "tiny unreadable" bug). Cap so a run of badges still lays out sanely.
    target_h = upem * 0.92
    target_w = target_h * (box_w / box_h)  # keep square-ish aspect
    # Never below ~0.75em wide; never need more than ~1.6em of advance room.
    target_w = max(target_w, upem * 0.75)
    scale = target_h / box_h

    stamp_w = box_w * scale
    # Expand advance to the badge width + sidebearing so glyphs do not overlap.
    # Slightly generous: path control points can overshoot the ink box a little.
    new_advance = int(min(max(advance, stamp_w + int(upem * 0.08)), upem * 1.6))

    svg_cx = (min_x + max_x) / 2
    svg_cy = (min_y + max_y) / 2
    # SVG y-down -> font y-up: centre badge at 0.46 em above baseline.
    origin_y = 0.0
    dy = 0.46 * upem - origin_y + svg_cy * scale
    dx = (new_advance / 2) - svg_cx * scale
    return scale, dx, dy, True, origin_y, new_advance


def stamp_font(src: Path, dst: Path, stamp_svg: Path, coverage: set[int]) -> int:
    """Write a stamped copy of ``src`` to ``dst``. Returns glyphs replaced."""
    contours, vb_w, vb_h = load_stamp_contours(stamp_svg)
    font = TTFont(str(src))
    cmap = font.getBestCmap() or {}
    upem = font["head"].unitsPerEm
    hmtx = font["hmtx"]
    is_cff = "CFF " in font
    glyph_set = font.getGlyphSet()

    targets: list[str] = []
    for cp in sorted(coverage):
        gname = cmap.get(cp)
        if gname and gname not in targets and gname != ".notdef":
            targets.append(gname)
    if not targets:
        font.close()
        return 0

    replaced = 0
    for gname in targets:
        advance = hmtx[gname][0]
        scale, dx, dy, flip, origin_y, new_advance = _fit_transform(
            contours, vb_w, vb_h, upem, advance
        )
        # Widen the advance so the badge circle is not squeezed; also rewrite
        # hmtx (and CFF width) to the new advance.
        hmtx[gname] = (new_advance, hmtx[gname][1])

        if is_cff:
            pen = T2CharStringPen(new_advance, glyph_set, CFF2=False)
            _contours_to_pen(contours, pen, scale, dx, dy, flip, origin_y)
            cff = font["CFF "].cff
            top = cff.topDictIndex[0]
            private = getattr(top, "Private", None)
            global_subrs = cff.GlobalSubrs
            top.CharStrings[gname] = pen.getCharString(
                private=private, globalSubrs=global_subrs
            )
            # Clear any leftover width hints tied to the old outline.
            if private is not None and hasattr(private, "defaultWidthX"):
                pass  # width comes from the pen / hmtx
        else:
            # Stamp contours are cubic (potrace). TTGlyphPen expects
            # quadratic points; cu2qu converts and clears fontTools'
            # internal flagCubic (0x80) bit that OTS rejects on disk.
            tt_pen = TTGlyphPen(glyph_set)
            pen = Cu2QuPen(tt_pen, max_err=1.0, reverse_direction=True)
            _contours_to_pen(contours, pen, scale, dx, dy, flip, origin_y)
            glyph = tt_pen.glyph()
            glyf = font["glyf"]
            glyf.glyphs[gname] = glyph
            glyph.recalcBounds(glyf)
        replaced += 1

    # WOFF/WOFF2 are derived; keep sfnt clean on save by resetting flavor
    # when the source was a webfont (caller usually passes otf/ttf).
    flavor = font.flavor
    dst.parent.mkdir(parents=True, exist_ok=True)
    font.flavor = None
    font.save(str(dst))
    if flavor in ("woff", "woff2"):
        # Also write the webfont flavour beside the sfnt if that was the input.
        pass
    font.close()
    return replaced


def make_woff_like(otf: Path) -> list[Path]:
    """Regenerate WOFF + WOFF2 from a stamped OTF (same as the packager)."""
    written: list[Path] = []
    for flavor, suffix in (("woff", ".woff"), ("woff2", ".woff2")):
        target = otf.with_suffix(suffix)
        font = TTFont(str(otf))
        font.flavor = flavor
        font.save(str(target))
        font.close()
        written.append(target)
    return written


def stamp_package(package_dir: Path, out_dir: Path, stamp_svg: Path, coverage: set[int]) -> dict[str, int]:
    """Stamp every OTF/TTF in ``package_dir`` into ``out_dir`` (same layout).

    WOFF/WOFF2 in the output are regenerated from the stamped OTF when one
    exists, otherwise from the stamped TTF.
    """
    package_dir = Path(package_dir).resolve()
    out_dir = Path(out_dir).resolve()
    if not package_dir.is_dir():
        raise SystemExit(f"package dir not found: {package_dir}")
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    # Mirror non-font files only if they are font binaries; package folders
    # are font-binaries-only by contract.
    stats: dict[str, int] = {}
    stamped_otf: list[Path] = []
    for path in sorted(package_dir.iterdir()):
        if not path.is_file():
            continue
        dest = out_dir / path.name
        if path.suffix.lower() in (".otf", ".ttf"):
            n = stamp_font(path, dest, stamp_svg, coverage)
            stats[path.name] = n
            if path.suffix.lower() == ".otf":
                stamped_otf.append(dest)
            print(f"  stamped {path.name}: {n} glyph(s)")
        elif path.suffix.lower() in (".woff", ".woff2"):
            # Placeholder; regenerated below from stamped OTF/TTF.
            pass
        else:
            shutil.copy2(path, dest)

    # Prefer OTF as the webfont source (packager convention).
    web_source: Path | None = None
    if stamped_otf:
        web_source = stamped_otf[0]
    else:
        ttfs = [p for p in out_dir.iterdir() if p.suffix.lower() == ".ttf"]
        if ttfs:
            web_source = ttfs[0]

    if web_source is not None:
        # If the package had multiple faces, regenerate per-stem pairs.
        sources = sorted(
            (p for p in out_dir.iterdir() if p.suffix.lower() in (".otf", ".ttf")),
            key=lambda p: p.stem,
        )
        # Group by stem: each stamped otf/ttf stem gets woff pair.
        stems: dict[str, Path] = {}
        for p in sources:
            if p.suffix.lower() == ".otf":
                stems[p.stem] = p
        for p in sources:
            if p.suffix.lower() == ".ttf" and p.stem not in stems:
                stems[p.stem] = p
        for stem, src in sorted(stems.items()):
            if src.suffix.lower() != ".otf":
                # Only otf feeds make_woff_like (same as packager).
                # If a package is TTF-only, promote via no conversion —
                # stamp_font already wrote the TTF; still emit woff from it
                # by loading as sfnt.
                for flavor, suffix in (("woff", ".woff"), ("woff2", ".woff2")):
                    target = out_dir / f"{stem}{suffix}"
                    font = TTFont(str(src))
                    font.flavor = flavor
                    font.save(str(target))
                    font.close()
            else:
                make_woff_like(src)
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="mode", required=True)

    p_outline = sub.add_parser("outline", help="convert authored stamp SVG to path outlines")
    p_outline.add_argument("src", type=Path, nargs="?", default=DEFAULT_STAMP_SVG)
    p_outline.add_argument("dst", type=Path, nargs="?", default=DEFAULT_STAMP_PATHS)

    p_stamp = sub.add_parser("stamp", help="stamp fonts for free-trial-demo delivery")
    p_stamp.add_argument("--package-dir", type=Path, default=None,
                         help="clean font package folder (read-only source)")
    p_stamp.add_argument("--out-dir", type=Path, default=None,
                         help="destination folder for stamped copies (replaced)")
    p_stamp.add_argument("--stamp", type=Path, default=DEFAULT_STAMP_PATHS,
                         help="path-only stamp SVG")
    p_stamp.add_argument("--coverage", default="digits,punct",
                         help="glyph classes/ranges to lock (default: digits,punct)")
    p_stamp.add_argument("--font", type=Path, default=None,
                         help="stamp a single font file instead of a package")
    p_stamp.add_argument("--font-out", type=Path, default=None,
                         help="output path for --font mode")

    args = parser.parse_args()

    if args.mode == "outline":
        outline_stamp(args.src, args.dst)
        return 0

    # stamp mode
    stamp_svg = Path(args.stamp)
    if not stamp_svg.is_file() and stamp_svg == DEFAULT_STAMP_PATHS and DEFAULT_STAMP_SVG.is_file():
        outline_stamp(DEFAULT_STAMP_SVG, DEFAULT_STAMP_PATHS)
        stamp_svg = DEFAULT_STAMP_PATHS
    coverage = parse_coverage(args.coverage)

    if args.font:
        if not args.font_out:
            raise SystemExit("--font requires --font-out")
        n = stamp_font(args.font, args.font_out, stamp_svg, coverage)
        print(f"stamped {args.font.name} -> {args.font_out.name}: {n} glyph(s)")
        return 0

    if not args.package_dir or not args.out_dir:
        raise SystemExit("stamp mode requires --package-dir and --out-dir (or --font/--font-out)")
    stats = stamp_package(args.package_dir, args.out_dir, stamp_svg, coverage)
    total = sum(stats.values())
    print(f"stamped package: {len(stats)} font file(s), {total} glyph replacement(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
