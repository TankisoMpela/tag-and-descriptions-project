#!/usr/bin/env python3
"""Build a linked review gallery for individually rendered square templates."""

from __future__ import annotations

import argparse
import html
import json
import os
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = ROOT / "font-factory/support-html/catalog.json"
DEFAULT_DIR = ROOT / "font-factory/support-html/benchmarks/square-adaptations-2026-10-17"
DEFAULT_BLACKLETTER_MANIFEST = ROOT / "font-factory/support-html/benchmarks/titlecase-rerender-2026-10-15/render-manifest.json"
DEFAULT_BLACKLETTER_REFERENCE_MANIFEST = ROOT / "font-factory/support-html/benchmarks/blackletter-reference-templates-2026-10-15/render-manifest.json"

# These are deliberate edge-to-edge specimen patterns; the repeated words are
# clipped by the pattern mask or artboard, while the focal headline has its own
# separate fit check.
INTENTIONAL_PATTERN_CROPS = {
    "skinbadge32": "Repeated seal lettering is intentionally masked at the oval edges.",
    "typewall32": "Repeated typewall lettering intentionally runs beyond the square edges.",
}


def relative_link(folder: Path, target: Path) -> str:
    return Path(os.path.relpath(target.resolve(), folder.resolve())).as_posix()


def contrast_values(layout: dict) -> list[float]:
    values = []
    for key, value in layout.items():
        if "contrast" not in key.lower() or isinstance(value, bool):
            continue
        try:
            values.append(float(value))
        except (TypeError, ValueError):
            continue
    return values


def review_status(template: str, layout: dict) -> tuple[str, list[str], str | None]:
    problems: list[str] = []
    intentional: str | None = None
    if layout.get("outOfBounds"):
        problems.append("elements extend beyond the square artboard")
    if layout.get("stackOverlaps"):
        problems.append("declared text rows overlap")

    fit_failures = layout.get("fitFailures") or []
    if fit_failures:
        allowed = template in INTENTIONAL_PATTERN_CROPS and all(
            str(item.get("name", "")) == "text" for item in fit_failures
        )
        if allowed:
            intentional = INTENTIONAL_PATTERN_CROPS[template]
        else:
            problems.append(f"{len(fit_failures)} text fit warning(s) need review")

    values = contrast_values(layout)
    if values:
        exception = layout.get("contrastException") or {}
        try:
            minimum = float(exception.get("minimum", 4.5))
        except (TypeError, ValueError):
            minimum = 4.5
        rationale = str(exception.get("rationale", "")).strip()
        if exception and (minimum < 1 or len(rationale) < 24):
            problems.append("contrast exception is missing a supported rationale")
        elif min(values) < minimum:
            problems.append(f"contrast {min(values):.2f}:1 is below its {minimum:.2f}:1 floor")

    return ("REVIEW" if problems else "PASS"), problems, intentional


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folder", type=Path, default=DEFAULT_DIR)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--blackletter-manifest", type=Path, default=DEFAULT_BLACKLETTER_MANIFEST)
    parser.add_argument("--blackletter-reference-manifest", type=Path,
                        default=DEFAULT_BLACKLETTER_REFERENCE_MANIFEST)
    args = parser.parse_args()
    folder = args.folder.expanduser().resolve()
    catalog_path = args.catalog.expanduser().resolve()
    blackletter_manifest_path = args.blackletter_manifest.expanduser().resolve()
    blackletter_reference_manifest_path = args.blackletter_reference_manifest.expanduser().resolve()
    if not folder.is_dir() or not catalog_path.is_file():
        parser.error("review folder and support catalogue must both exist")

    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    source_rows = catalog.get("templates", [])
    if len(source_rows) != catalog.get("activeCount"):
        raise SystemExit("support catalogue activeCount does not match its template records")
    by_id = {row["id"]: row for row in source_rows}
    if len(by_id) != len(source_rows):
        raise SystemExit("support catalogue contains duplicate template IDs")
    if not blackletter_manifest_path.is_file():
        parser.error(f"blackletter variant manifest does not exist: {blackletter_manifest_path}")
    blackletter_source = json.loads(blackletter_manifest_path.read_text(encoding="utf-8"))
    blackletter_variants = [row for row in blackletter_source.get("rendered", [])
                            if row.get("class") == "blackletter"]
    if not blackletter_reference_manifest_path.is_file():
        parser.error(f"blackletter reference manifest does not exist: {blackletter_reference_manifest_path}")
    blackletter_reference_source = json.loads(blackletter_reference_manifest_path.read_text(encoding="utf-8"))
    blackletter_reference_templates = blackletter_reference_source.get("templates", [])
    if len({row.get("id") for row in blackletter_reference_templates}) != len(blackletter_reference_templates):
        raise SystemExit("blackletter reference manifest contains duplicate template IDs")

    rows = []
    for template in sorted(by_id):
        image_path = folder / f"{template}.png"
        report_path = folder / f"{template}.json"
        if not image_path.is_file() or not report_path.is_file():
            raise SystemExit(f"missing square render or report for {template}")
        report = json.loads(report_path.read_text(encoding="utf-8"))
        layout = report.get("layoutReport") or {}
        if report.get("template") != template or report.get("ratio") != "1x1":
            raise SystemExit(f"square report identity/ratio mismatch for {template}")
        with Image.open(image_path) as image:
            image.load()
            dimensions = list(image.size)
        if dimensions != [1600, 1600]:
            raise SystemExit(f"{template} is {dimensions}, expected 1600 x 1600")

        status, problems, intentional = review_status(template, layout)
        template_record = by_id[template]
        editor_entry = Path(template_record["htmlEntry"])
        editor_candidates = (
            ROOT / editor_entry,
            catalog_path.parent / editor_entry,
            catalog_path.parent.parent / editor_entry,
        )
        editor_path = next((candidate for candidate in editor_candidates
                            if candidate.is_file()), editor_candidates[0])
        if not editor_path.is_file():
            raise SystemExit(f"missing editable base template for {template}: {editor_path}")
        rows.append({
            "template": template,
            "image": image_path.name,
            "dimensions": dimensions,
            "bytes": image_path.stat().st_size,
            "ratio": "1x1",
            "renderer": report.get("renderer", "HTML/CSS + headless Chromium"),
            "font": Path(report.get("font", "")).name,
            "status": status,
            "issues": problems,
            "intentional_pattern_crop": intentional,
            "editor": relative_link(folder, editor_path),
            "source_id": template_record.get("sourceId"),
            "source_kind": template_record.get("sourceKind"),
            "report": report_path.name,
        })

    for variant in blackletter_variants:
        template = variant["template"]
        template_record = by_id.get(template)
        if not template_record:
            raise SystemExit(f"blackletter variant has no active template record: {template}")
        image_path = folder / variant["png"]
        report_path = image_path.with_suffix(".json")
        if not image_path.is_file() or not report_path.is_file():
            raise SystemExit(f"missing blackletter square render or report for {template}")
        report = json.loads(report_path.read_text(encoding="utf-8"))
        layout = report.get("layoutReport") or {}
        if report.get("template") != template or report.get("ratio") != "1x1":
            raise SystemExit(f"blackletter square report identity/ratio mismatch for {template}")
        with Image.open(image_path) as image:
            image.load()
            dimensions = list(image.size)
        if dimensions != [1600, 1600]:
            raise SystemExit(f"{image_path.name} is {dimensions}, expected 1600 x 1600")

        status, problems, intentional = review_status(template, layout)
        editor_entry = Path(template_record["htmlEntry"])
        editor_candidates = (
            ROOT / editor_entry,
            catalog_path.parent / editor_entry,
            catalog_path.parent.parent / editor_entry,
        )
        editor_path = next((candidate for candidate in editor_candidates
                            if candidate.is_file()), editor_candidates[0])
        if not editor_path.is_file():
            raise SystemExit(f"missing editable base template for {template}: {editor_path}")
        rows.append({
            "template": template,
            "variant": "Blackletter",
            "image": image_path.name,
            "dimensions": dimensions,
            "bytes": image_path.stat().st_size,
            "ratio": "1x1",
            "renderer": report.get("renderer", "HTML/CSS + headless Chromium"),
            "font": Path(report.get("font", "")).name,
            "status": status,
            "issues": problems,
            "intentional_pattern_crop": intentional,
            "editor": relative_link(folder, editor_path),
            "source_id": template_record.get("sourceId"),
            "source_kind": template_record.get("sourceKind"),
            "report": report_path.name,
        })

    for reference in blackletter_reference_templates:
        template = reference["id"]
        image_path = folder / f"blackletter-reference-{template}.png"
        report_path = image_path.with_suffix(".json")
        if not image_path.is_file() or not report_path.is_file():
            raise SystemExit(f"missing blackletter reference square render or report for {template}")
        report = json.loads(report_path.read_text(encoding="utf-8"))
        layout = report.get("layoutReport") or {}
        if report.get("template") != template or report.get("ratio") != "1x1":
            raise SystemExit(f"blackletter reference square report identity/ratio mismatch for {template}")
        with Image.open(image_path) as image:
            image.load()
            dimensions = list(image.size)
        if dimensions != [1600, 1600]:
            raise SystemExit(f"{image_path.name} is {dimensions}, expected 1600 x 1600")

        status, problems, intentional = review_status(template, layout)
        editor_path = ROOT / "font-factory/support-html" / "templates" / template / "editor.html"
        if not editor_path.is_file():
            raise SystemExit(f"missing blackletter reference template editor: {editor_path}")
        rows.append({
            "template": template,
            "title": reference.get("title", template),
            "variant": "Blackletter Reference",
            "image": image_path.name,
            "dimensions": dimensions,
            "bytes": image_path.stat().st_size,
            "ratio": "1x1",
            "renderer": report.get("renderer", "HTML/CSS + headless Chromium"),
            "font": Path(report.get("font", "")).name,
            "status": status,
            "issues": problems,
            "intentional_pattern_crop": intentional,
            "editor": relative_link(folder, editor_path),
            "source_id": reference.get("source"),
            "source_kind": "blackletter-reference",
            "report": report_path.name,
        })

    expected = {f"{template}.png" for template in by_id}
    expected.update(row["png"] for row in blackletter_variants)
    expected.update(f"blackletter-reference-{row['id']}.png" for row in blackletter_reference_templates)
    actual = {path.name for path in folder.glob("*.png")}
    if actual != expected:
        raise SystemExit(
            f"square PNG set differs from active catalogue; missing={sorted(expected-actual)}, "
            f"extra={sorted(actual-expected)}"
        )

    font_names = sorted({row["font"] for row in rows})
    manifest = {
        "title": "Support Template Square Adaptation Review",
        "date": "2026-10-18",
        "render_count": len(rows),
        "standard_template_count": len(by_id),
        "blackletter_variant_count": len(blackletter_variants),
        "blackletter_reference_template_count": len(blackletter_reference_templates),
        "canvas": [1600, 1600],
        "font_used": ", ".join(font_names),
        "base": (f"The review contains {len(by_id)} standard square templates, "
                 f"{len(blackletter_variants)} blackletter font swaps on standard templates, and "
                 f"{len(blackletter_reference_templates)} separate blackletter reference templates. "
                 "Every image is rendered from its matching HTML/CSS template; no 3:2 render is padded or cropped."),
        "review_rule": "PASS requires matching template and ratio, exact 1600x1600 output, no off-canvas elements or declared stack overlaps, text fit except documented decorative pattern crops, and contrast at or above the documented source exception floor (4.5:1 otherwise).",
        "images": rows,
    }
    (folder / "review-index.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    cards_by_group = {"Standard Templates": [], "Blackletter Font Swaps": [], "Blackletter Reference Templates": []}
    for row in rows:
        variant = row.get("variant")
        group = ("Blackletter Reference Templates" if variant == "Blackletter Reference" else
                 "Blackletter Font Swaps" if variant == "Blackletter" else "Standard Templates")
        name = html.escape(row.get("title", row["template"]) + (f" · {variant}" if variant else ""))
        template_id = html.escape(row["template"])
        img = html.escape(row["image"])
        editor = html.escape(row["editor"], quote=True)
        status = html.escape(row["status"])
        note = row["intentional_pattern_crop"] or "; ".join(row["issues"])
        note_html = f"<p class=\"note\">{html.escape(note)}</p>" if note else ""
        card = (
            f'<article class="card"><a class="preview" href="{img}" target="_blank" '
            f'rel="noreferrer"><img loading="lazy" src="{img}" alt="{name} square support design"></a>'
            f'<div class="caption"><div class="title"><h2>{name}</h2><span class="{status.lower()}">{status}</span></div>'
            f'<p>{template_id} · 1600 × 1600 · {row["bytes"]:,} bytes · 1:1</p>{note_html}'
            f'<a class="editor" href="{editor}" target="_blank" rel="noreferrer">Open 3:2-base template editor ↗</a></div></article>'
        )
        cards_by_group[group].append(card)
    sections = []
    for group, group_cards in cards_by_group.items():
        if group_cards:
            sections.append(f'<section class="gallery-section"><h2>{html.escape(group)} <span>{len(group_cards)}</span></h2>'
                            f'<div class="cards">{"".join(group_cards)}</div></section>')
    html_doc = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Support Template Square Adaptation Review</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;background:#151719;color:#f3f0e8;font:15px/1.45 system-ui,"Segoe UI",sans-serif}}
header{{padding:28px clamp(18px,4vw,58px) 22px;border-bottom:1px solid #34383c}}h1{{margin:0;font-size:clamp(24px,3vw,38px);letter-spacing:-.035em}}
header p{{margin:8px 0 0;color:#adb2b6;max-width:900px}}main{{display:grid;gap:30px;padding:24px clamp(18px,4vw,58px) 56px}}
.gallery-section>h2{{margin:0 0 13px;font-size:20px;letter-spacing:-.02em}}.gallery-section>h2 span{{color:#adb2b6;font-size:13px;font-weight:500;margin-left:5px}}.cards{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:18px}}
.card{{overflow:hidden;background:#1c1f22;border:1px solid #35393d}}.preview{{display:block;background:#25282b}}img{{display:block;width:100%;height:auto;aspect-ratio:1;object-fit:contain}}
.caption{{padding:11px 13px 14px}}.title{{display:flex;justify-content:space-between;align-items:center;gap:8px}}h2{{margin:0 0 4px;font-size:15px;font-weight:600}}.caption p{{margin:0;color:#afb3b6;font-size:12px}}
.pass,.review{{font-size:10px;letter-spacing:.08em;padding:2px 6px;border-radius:999px}}.pass{{background:#153d30;color:#a5e7c9}}.review{{background:#594015;color:#f2d18d}}
.note{{margin-top:5px!important;color:#e5c88f!important}}.editor{{display:inline-block;margin-top:8px;color:#e4b987;text-decoration:none;font-size:12px}}.editor:hover{{text-decoration:underline}}
@media(max-width:520px){{main{{gap:22px;padding-inline:12px}}.cards{{grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}}.caption{{padding:9px}}.caption p{{font-size:11px}}}}
</style></head><body><header><h1>Support Template Square Adaptation Review</h1>
<p>{len(rows)} individual 1600 × 1600 browser renders: {len(by_id)} standard templates, {len(blackletter_variants)} blackletter font swaps, and {len(blackletter_reference_templates)} blackletter reference templates. Each square is built from its matching HTML/CSS template; no landscape image was padded or cropped. Click an image for full resolution or open its editable template.</p>
</header><main>{''.join(sections)}</main></body></html>'''
    (folder / "index.html").write_text(html_doc, encoding="utf-8")
    print(f"[PASS] indexed {len(rows)} individual square renders in {folder}")
    print(f"[PASS] render review: {sum(row['status'] == 'PASS' for row in rows)} PASS, "
          f"{sum(row['status'] == 'REVIEW' for row in rows)} REVIEW")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
