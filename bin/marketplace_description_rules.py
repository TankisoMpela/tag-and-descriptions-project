"""Shared copy gates for Creative Market and Creative Fabrica font descriptions."""

from __future__ import annotations

import re


MAX_DESCRIPTION_WORDS = 230
MIN_DESCRIPTION_PARAGRAPHS = 2
MAX_DESCRIPTION_PARAGRAPHS = 4
MAX_MARKETPLACE_PROSE_PARAGRAPHS = 3
MAX_BOOTH_DESCRIPTION_CHARS = 700

PROHIBITED_DESCRIPTION_PATTERNS = (
    (re.compile(r"\blicen[cs](?:e|es|ing|ed)?\b", re.IGNORECASE), "license or licensing discussion"),
    (re.compile(r"\b(?:personal|commercial|extended)[- ]use\b", re.IGNORECASE), "license/package-use wording"),
    (re.compile(r"\b\d+\s+(?:mapped\s+)?(?:glyphs?|characters?)\b", re.IGNORECASE), "glyph or character count"),
    (re.compile(r"\b(?:unicode|basic\s+latin|latin[- ]?1|latin\s+extended|private\s+use\s+area|codepoints?)\b", re.IGNORECASE), "Unicode coverage detail"),
    (re.compile(r"\b(?:gsub|gpos)\b", re.IGNORECASE), "OpenType table name"),
    (re.compile(r"\b(?:legacy\s+)?kern(?:ing)?(?:\s+table)?\b", re.IGNORECASE), "kerning implementation detail"),
    (re.compile(r"\b(?:no|without|missing|lacks?|does\s+not\s+include|doesn't\s+include|not\s+included|not\s+supported)\b.{0,70}\b(?:alternates?|ligatures?|kerning|kern|coverage|support|feature|compatibility)\b", re.IGNORECASE), "missing-feature or limitation disclosure"),
)

BOOTH_PROHIBITED_DESCRIPTION_PATTERNS = (
    (re.compile(r"(?:ライセンス|ライセンシー|利用許諾|許諾|商用利用|商用可|商用可能|非商用|個人利用|ロイヤリティフリー|再配布|二次配布|再販|埋め込み|利用規約|利用条件|使用許可)", re.IGNORECASE), "license or permission discussion"),
    (re.compile(r"\b(?:licen[cs](?:e|es|ing|ed)?|personal use|commercial use|royalty[- ]free|redistribution|resale rights?)\b", re.IGNORECASE), "license or permission discussion"),
    (re.compile(r"\b(?:otf|ttf|woff2?|opentype|truetype|unicode|gsub|gpos|pua|glyphs?|ligatures?|alternates?|kerning)\b", re.IGNORECASE), "technical feature or format detail"),
    (re.compile(r"(?:グリフ|字形|文字コード|文字数|収録文字|対応文字|対応環境|対応ソフト|フォント形式|ファイル形式|フォント形式|収録内容|リガチャ|オルタネイト|カーニング|合字|互換性|インストール|ソフトウェア|アプリケーション)", re.IGNORECASE), "technical specification"),
    (re.compile(r"(?:非対応|未収録|未対応|非搭載|収録されていません|含まれていません|含まれません|含まれていない|利用できません|使用できません|対応していません|対応していない|含まない|未実装|対象外|不向き|向きません|制限|注意が必要|使えません|使えない)", re.IGNORECASE), "limitation or detraction"),
    (re.compile(r"\b(?:missing|lacks?|without|not supported|not included|does not include|doesn't include|does not support|doesn't support|unsupported|limitation|incompatible|not compatible)\b", re.IGNORECASE), "limitation or detraction"),
)


def validate_marketplace_description(description: str) -> list[str]:
    """Validate concise prose plus explicit included-files/features/software blocks."""
    blocks = {}
    current = "PROSE"
    blocks[current] = []
    for line in description.splitlines():
        heading = line.strip().strip("*_ `#").casefold().rstrip(":")
        if heading in {"what's included", "what’s included", "included files", "features", "software compatibility", "works with"}:
            current = heading
            blocks.setdefault(current, [])
        else:
            blocks.setdefault(current, []).append(line)
    prose = "\n".join(blocks.get("PROSE", [])).strip()
    prose_paragraphs = [part.strip() for part in re.split(r"\n\s*\n", prose) if part.strip()]
    all_text = "\n".join(description.splitlines())
    format_sections = " ".join(
        line for key in ("what's included", "what’s included", "included files")
        for line in blocks.get(key, [])
    )
    software_sections = " ".join(
        line for key in ("software compatibility", "works with")
        for line in blocks.get(key, [])
    )
    words = re.findall(r"\b[\w'-]+\b", all_text)
    issues: list[str] = []

    if len(words) > MAX_DESCRIPTION_WORDS:
        issues.append(f"product description is {len(words)} words; maximum is {MAX_DESCRIPTION_WORDS}")
    if not MIN_DESCRIPTION_PARAGRAPHS <= len(prose_paragraphs) <= MAX_MARKETPLACE_PROSE_PARAGRAPHS:
        issues.append(
            f"product description has {len(prose_paragraphs)} prose paragraphs; expected {MIN_DESCRIPTION_PARAGRAPHS}-{MAX_MARKETPLACE_PROSE_PARAGRAPHS}"
        )
    if not format_sections.strip():
        issues.append("product description is missing a What's Included file list")
    if not any(line.strip().startswith(("-", "•", "*")) for line in format_sections.splitlines()):
        issues.append("What's Included must use bullet points")
    for format_name in ("OTF", "TTF", "WOFF"):
        if not re.search(rf"\b{format_name}\b", format_sections, re.IGNORECASE):
            issues.append(f"What's Included must list the delivered {format_name} format")
    if not any(line.strip().startswith(("-", "•", "*")) for line in blocks.get("features", [])):
        issues.append("Features must use bullet points")
    if not software_sections.strip():
        issues.append("product description is missing a software compatibility note")
    if not any(
        line.strip().startswith(("-", "•", "*"))
        for key in ("software compatibility", "works with")
        for line in blocks.get(key, [])
    ):
        issues.append("Software Compatibility must use bullet points")
    if re.search(r"\b(?:otf|ttf|woff2?|opentype|truetype)\b", prose, re.IGNORECASE):
        issues.append("file formats belong in What's Included, not the prose")
    if re.search(r"\b(?:compatible\s+with|compatibility|software|canva|illustrator|photoshop|indesign|affinity|microsoft\s+office)\b", prose, re.IGNORECASE):
        issues.append("software compatibility belongs in its own section, not the prose")
    for pattern, label in PROHIBITED_DESCRIPTION_PATTERNS:
        if pattern.search(all_text):
            issues.append(f"product description contains prohibited {label}")
    return issues


def validate_booth_description(description: str) -> list[str]:
    """Return the concise, buyer-focused BOOTH copy-contract violations."""
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", description.strip()) if part.strip()]
    text = " ".join(paragraphs)
    issues: list[str] = []

    if len(text) > MAX_BOOTH_DESCRIPTION_CHARS:
        issues.append(
            f"paste-ready description is {len(text)} characters; maximum is {MAX_BOOTH_DESCRIPTION_CHARS}"
        )
    if not MIN_DESCRIPTION_PARAGRAPHS <= len(paragraphs) <= MAX_DESCRIPTION_PARAGRAPHS:
        issues.append(
            f"paste-ready description has {len(paragraphs)} paragraphs; expected 2-4 concise paragraphs"
        )
    for pattern, label in BOOTH_PROHIBITED_DESCRIPTION_PATTERNS:
        if pattern.search(text):
            issues.append(f"paste-ready description contains prohibited {label}")
    return issues
