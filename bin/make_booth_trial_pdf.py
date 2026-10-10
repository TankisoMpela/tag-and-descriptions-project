#!/usr/bin/env python3
"""Build a one-page branded BOOTH trial-insert PDF (Japanese customer copy).

Inputs: BOOTH item URL, local font directory, public trial URL.
Image: thumbnail from {font-dir}/visuals/New-Images/squares/ (mechanical pick).
Render: temporary HTML + headless Chromium print-to-pdf (clickable links).

Exit 0 on success; fail closed on missing inputs/assets/chromium/PDF.
"""

from __future__ import annotations

import argparse
import html
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
FONT_EXTS = {".otf", ".ttf", ".woff", ".woff2"}
PAGES = {
    "a5": {"w": "148mm", "h": "210mm", "css": "@page { size: A5 portrait; margin: 0; }"},
    "letter": {"w": "8.5in", "h": "11in", "css": "@page { size: letter portrait; margin: 0; }"},
}

# Fail closed — these are not optional marketing strings.
REQUIRED = (
    "BOOTH商品URL (--booth-url) が必要です。",
    "トライアルURL (--trial-url) が必要です。",
    "フォントディレクトリ (--font-dir) が必要です。",
)


def die(msg: str, code: int = 1) -> None:
    print(f"[FAIL] {msg}", file=sys.stderr)
    sys.exit(code)


def norm_url(raw: str) -> str:
    u = raw.strip()
    if not u:
        return ""
    if not re.match(r"^https?://", u, re.I):
        u = "https://" + u
    return u


def slugify(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", name.strip()).strip("-").lower()
    return s or "font"


def is_http_url(raw: str) -> bool:
    try:
        p = urlparse(norm_url(raw))
        return p.scheme in ("http", "https") and bool(p.netloc)
    except Exception:
        return False


def find_font(font_dir: Path) -> Path:
    candidates: list[Path] = []
    for p in sorted(font_dir.rglob("*")):
        if not p.is_file():
            continue
        if p.suffix.lower() not in FONT_EXTS:
            continue
        if "__MACOSX" in p.parts or p.name.startswith("._"):
            continue
        candidates.append(p)
    if not candidates:
        die(f"font binary not found under {font_dir}")

    scored: list[tuple[int, Path]] = []
    for p in candidates:
        name = p.name.lower()
        score = 0
        if "italic" in name or "oblique" in name:
            score += 40
        if "bold" in name and "regular" not in name:
            score += 10
        if "regular" in name:
            score -= 5
        score += len(p.relative_to(font_dir).parts) * 3
        if p.suffix.lower() in (".woff", ".woff2"):
            score += 5
        scored.append((score, p))
    scored.sort(key=lambda t: (t[0], str(t[1])))
    return scored[0][1]


def _first_image(directory: Path) -> Path | None:
    if not directory.is_dir():
        return None
    files = [
        p
        for p in sorted(directory.iterdir())
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS and not p.name.startswith("._")
    ]
    if not files:
        return None
    preferred = [
        p
        for p in files
        if p.stem.lower() in ("thumbnail_main", "thumbnail", "main", "thumb")
    ]
    return preferred[0] if preferred else files[0]


def find_thumbnail(font_dir: Path, explicit: str | None) -> Path:
    if explicit:
        p = Path(explicit).expanduser()
        if not p.is_file():
            die(f"image not found: {p}")
        if p.suffix.lower() not in IMAGE_EXTS:
            die(f"unsupported image type: {p}")
        return p.resolve()

    rels = (
        Path("visuals") / "New-Images" / "squares",
        Path("visuals") / "squares",
        Path("New-Images") / "squares",
    )
    for rel in rels:
        hit = _first_image(font_dir / rel)
        if hit:
            return hit.resolve()

    # Bounded search: visual/New-Images/squares or visual/squares under font_dir.
    hits: list[Path] = []
    for p in font_dir.rglob("squares"):
        if not p.is_dir():
            continue
        if p.parent.name not in ("New-Images", "visuals"):
            continue
        if "__MACOSX" in p.parts:
            continue
        img = _first_image(p)
        if img:
            hits.append(img)
    if hits:
        hits.sort(key=lambda x: (len(x.parts), str(x)))
        return hits[0].resolve()

    die(
        "thumbnail not found — expected "
        f"{font_dir}/visuals/New-Images/squares/ (or pass --image)"
    )
    raise AssertionError


def derive_font_name(font_dir: Path, font_file: Path) -> str:
    stem = font_file.stem
    # Strip common style suffixes.
    stem = re.sub(
        r"[\s_-]+(regular|bold|italic|oblique|light|medium|black|thin|book|display)$",
        "",
        stem,
        flags=re.I,
    )
    if stem and stem.lower() not in ("font", "untitled"):
        return stem.strip()
    for part in (font_dir.name,):
        cleaned = re.sub(r"^\d+[-_\s]+", "", part).strip()
        if cleaned:
            return cleaned
    return font_file.stem


def build_html(
    *,
    font_name: str,
    font_file: Path,
    image_file: Path,
    booth_url: str,
    trial_url: str,
    shop_name: str,
    tagline: str,
    specimen: str,
    accent: str,
    page_key: str,
    trial_display: str,
) -> str:
    page = PAGES[page_key]
    font_uri = font_file.resolve().as_uri()
    image_uri = image_file.resolve().as_uri()
    font_face = "TrialFont"
    # Chromium resolves file: URIs from a file: document.
    esc = html.escape
    specimen_esc = esc(specimen)
    name_esc = esc(font_name)
    trial_display_esc = esc(trial_display)

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8" />
<title>{name_esc} — Trial Insert</title>
<style>
{page['css']}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{
  width: {page['w']};
  height: {page['h']};
  background: #F7F4EF;
  color: {accent};
  font-family: "Noto Sans CJK JP", "Noto Sans JP", "Hiragino Sans", "Yu Gothic", sans-serif;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}}
@font-face {{
  font-family: "{font_face}";
  src: url("{font_uri}") format("opentype"),
       url("{font_uri}") format("truetype");
  font-weight: normal;
  font-style: normal;
}}
.page {{
  width: {page['w']};
  height: {page['h']};
  padding: 11mm 12mm 9mm;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}}
.brand {{
  text-align: center;
  margin-bottom: 2.5mm;
  flex-shrink: 0;
}}
.brand .shop {{
  font-size: 10pt;
  letter-spacing: 0.28em;
  text-transform: uppercase;
  font-weight: 700;
}}
.brand .tag {{
  margin-top: 1mm;
  font-size: 6pt;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: #6b6560;
}}
.hero-name {{
  font-family: "{font_face}", serif;
  text-align: center;
  font-size: 34pt;
  line-height: 1.05;
  letter-spacing: -0.02em;
  margin: 1mm 0 2.5mm;
  word-break: break-word;
  flex-shrink: 0;
}}
.art {{
  width: 100%;
  height: 38mm;
  object-fit: cover;
  border-radius: 2.5mm;
  display: block;
  background: #ece7e0;
  margin-bottom: 2.5mm;
  flex-shrink: 0;
}}
.specimen {{
  text-align: center;
  font-family: "{font_face}", serif;
  font-size: 11pt;
  line-height: 1.3;
  margin-bottom: 1mm;
  flex-shrink: 0;
}}
.alphabet {{
  text-align: center;
  font-family: "{font_face}", serif;
  font-size: 7.5pt;
  line-height: 1.4;
  letter-spacing: 0.04em;
  color: #3a3632;
  margin-bottom: 3mm;
  flex-shrink: 0;
}}
.rule {{
  height: 1px;
  background: #d9d2c8;
  margin: 0 6mm 3mm;
  flex-shrink: 0;
}}
.trial-block {{
  text-align: center;
  margin-bottom: 2mm;
  flex-shrink: 0;
}}
.eyebrow {{
  font-size: 7pt;
  letter-spacing: 0.28em;
  text-transform: uppercase;
  color: #6b6560;
  margin-bottom: 1.5mm;
}}
.thanks {{
  font-size: 9pt;
  line-height: 1.5;
  max-width: 92mm;
  margin: 0 auto;
}}
.thanks strong {{
  font-family: "{font_face}", serif;
  font-weight: 700;
}}
.cta {{
  display: block;
  width: 74mm;
  margin: 3mm auto 1.5mm;
  padding: 3.2mm 4mm;
  background: {accent};
  color: #F7F4EF;
  text-align: center;
  text-decoration: none;
  font-size: 10pt;
  font-weight: 700;
  letter-spacing: 0.08em;
  border-radius: 1.5mm;
}}
.trial-url {{
  display: block;
  text-align: center;
  font-size: 6.5pt;
  color: #55504b;
  word-break: break-all;
  max-width: 100mm;
  margin: 0 auto 3mm;
  font-family: "SFMono-Regular", "Liberation Mono", "Noto Sans Mono", monospace;
}}
.about {{
  text-align: center;
  margin-bottom: 1.5mm;
  flex-shrink: 0;
}}
.about p {{
  font-size: 7.5pt;
  line-height: 1.5;
  max-width: 96mm;
  margin: 0 auto 1.2mm;
  color: #3a3632;
}}
.booth-cta {{
  display: inline-block;
  margin-top: 0.5mm;
  padding: 2mm 4.5mm;
  border: 1.2px solid {accent};
  color: {accent};
  text-decoration: none;
  font-size: 7.5pt;
  font-weight: 700;
  letter-spacing: 0.06em;
  border-radius: 1.2mm;
}}
.footer {{
  margin-top: auto;
  text-align: center;
  padding-top: 2mm;
  flex-shrink: 0;
}}
.footer .line {{
  height: 1px;
  background: #d9d2c8;
  margin: 0 5mm 2.5mm;
}}
.footer .shop {{
  font-size: 8pt;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}}
.footer .note {{
  font-size: 6.5pt;
  color: #6b6560;
  margin-top: 0.8mm;
  letter-spacing: 0.04em;
}}
.footer .links {{
  margin-top: 1.2mm;
  font-size: 6pt;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #55504b;
}}
.footer a {{
  color: inherit;
  text-decoration: none;
}}
</style>
</head>
<body>
  <div class="page">
    <header class="brand">
      <div class="shop">{esc(shop_name)}</div>
      <div class="tag">{esc(tagline)}</div>
    </header>

    <div class="hero-name">{name_esc}</div>

    <img class="art" src="{image_uri}" alt="" />

    <div class="specimen">{specimen_esc}</div>
    <div class="alphabet">
      ABCDEFGHIJKLMNOPQRSTUVWXYZ<br />
      abcdefghijklmnopqrstuvwxyz<br />
      0123456789
    </div>

    <div class="rule"></div>

    <section class="trial-block">
      <div class="eyebrow">Personal Use Trial</div>
      <p class="thanks">
        <strong>{name_esc}</strong> をダウンロードいただき、ありがとうございます。<br />
        これは無料の Personal Use（個人利用）版です。
      </p>
      <a class="cta" href="{esc(trial_url)}">フォントを入手する →</a>
      <span class="trial-url">{trial_display_esc}</span>
    </section>

    <section class="about">
      <div class="eyebrow">About this trial</div>
      <p>
        このバージョンは個人利用のみにライセンスされています。<br />
        商用プロジェクトには、BOOTH のフル版とライセンスをご確認ください。
      </p>
      <a class="booth-cta" href="{esc(booth_url)}">フル版を見る →</a>
    </section>

    <footer class="footer">
      <div class="line"></div>
      <div class="shop">{esc(shop_name)}</div>
      <div class="note">Independent fonts, made with care.</div>
      <div class="links">
        <a href="{esc(booth_url)}">BOOTH</a>
        &nbsp;·&nbsp;
        <a href="{esc(trial_url)}">Trial</a>
        &nbsp;·&nbsp;
        More fonts
      </div>
    </footer>
  </div>
</body>
</html>
"""


def find_chromium() -> str:
    for name in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable"):
        path = shutil.which(name)
        if path:
            return path
    for path in ("/usr/bin/chromium", "/usr/bin/chromium-browser"):
        if Path(path).is_file():
            return path
    die("chromium not found on PATH (need headless print-to-pdf)")
    raise AssertionError


def print_pdf(chromium: str, html_path: Path, pdf_path: Path) -> None:
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    if pdf_path.exists():
        pdf_path.unlink()
    cmd = [
        chromium,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path}",
        html_path.resolve().as_uri(),
    ]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            env={**os.environ, "HOME": tempfile.mkdtemp(prefix="booth-pdf-")},
        )
    except subprocess.TimeoutExpired:
        die("chromium print-to-pdf timed out")
    if proc.returncode != 0 or not pdf_path.is_file() or pdf_path.stat().st_size < 200:
        err = (proc.stderr or proc.stdout or "").strip()[-800:]
        die(f"chromium failed to write PDF (exit {proc.returncode}): {err}")


def validate_pdf(pdf_path: Path) -> None:
    data = pdf_path.read_bytes()
    if not data.startswith(b"%PDF"):
        die("output is not a PDF")
    if b"/Type /Page" not in data and b"/Type/Page" not in data:
        # Very small PDFs still contain page objects; be strict but allow compressed.
        if b"/Page" not in data:
            die("PDF has no page objects")
    size = pdf_path.stat().st_size
    if size > 8_000_000:
        die(f"PDF unexpectedly large ({size} bytes)")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Build a one-page Japanese BOOTH trial-insert PDF."
    )
    ap.add_argument("--booth-url", required=True, help="BOOTH item URL")
    ap.add_argument("--trial-url", required=True, help="Public trial page URL")
    ap.add_argument("--font-dir", required=True, help="Local font directory")
    ap.add_argument("--font-name", default="", help="Display font name")
    ap.add_argument("--specimen", default="", help="Personality specimen line")
    ap.add_argument("--shop-name", default="Font Studio")
    ap.add_argument("--tagline", default="INDEPENDENT TYPE / FONT STUDIO")
    ap.add_argument("--accent", default="#111111", help="Accent color (hex)")
    ap.add_argument("--page", choices=sorted(PAGES), default="a5")
    ap.add_argument("--image", default="", help="Explicit product image path")
    ap.add_argument("--output", default="", help="Output PDF path")
    ap.add_argument(
        "--keep-html",
        action="store_true",
        help="Keep generated HTML beside the PDF",
    )
    args = ap.parse_args(argv)

    if not is_http_url(args.booth_url):
        die(REQUIRED[0])
    if not is_http_url(args.trial_url):
        die(REQUIRED[1])

    font_dir = Path(args.font_dir).expanduser()
    if not font_dir.is_dir():
        die(REQUIRED[2] + f" (missing directory: {font_dir})")
    font_dir = font_dir.resolve()

    booth_url = norm_url(args.booth_url)
    trial_url = norm_url(args.trial_url)

    font_file = find_font(font_dir)
    image_file = find_thumbnail(font_dir, args.image or None)
    font_name = (args.font_name or "").strip() or derive_font_name(font_dir, font_file)
    if not font_name:
        die("could not derive --font-name")

    specimen = (args.specimen or "").strip() or f"{font_name} {font_name} {font_name}"
    accent = args.accent.strip() or "#111111"
    if not re.match(r"^#[0-9A-Fa-f]{3,8}$", accent):
        die(f"invalid --accent hex color: {accent}")

    slug = slugify(font_name)
    out = (
        Path(args.output).expanduser()
        if args.output
        else Path("outputs") / "booth-pdfs" / f"{slug}-trial-insert.pdf"
    )
    if out.suffix.lower() != ".pdf":
        out = out.with_suffix(".pdf")
    out = out.resolve()

    # Prefer a pretty host-only path under the trial URL for the printed fallback.
    try:
        tp = urlparse(trial_url)
        trial_display = f"{tp.netloc}{tp.path}".rstrip("/")
    except Exception:
        trial_display = trial_url

    content = build_html(
        font_name=font_name,
        font_file=font_file,
        image_file=image_file,
        booth_url=booth_url,
        trial_url=trial_url,
        shop_name=args.shop_name,
        tagline=args.tagline,
        specimen=specimen,
        accent=accent,
        page_key=args.page,
        trial_display=trial_display,
    )

    out.parent.mkdir(parents=True, exist_ok=True)
    html_path = out.with_suffix(".html")
    html_path.write_text(content, encoding="utf-8")

    chromium = find_chromium()
    print_pdf(chromium, html_path, out)
    validate_pdf(out)

    if not args.keep_html:
        try:
            html_path.unlink()
        except OSError:
            pass

    print("[PASS] pdf written")
    print(f"pdf={out}")
    print(f"font={font_file}")
    print(f"image={image_file}")
    print(f"font_name={font_name}")
    print(f"booth_url={booth_url}")
    print(f"trial_url={trial_url}")
    print(f"page={args.page}")
    print("No upload or publication claim")
    return 0


if __name__ == "__main__":
    sys.exit(main())
