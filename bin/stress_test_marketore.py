#!/usr/bin/env python3
"""Deterministic stress test for the Marketore agent contract.

This does not pretend to run an LLM. It stress-tests the evidence cache,
taxonomy/tag invariants, positive validator fixture, and representative
failure fixture so changes to the agent cannot silently relax the hard gates.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALID = ROOT / "tests" / "fixtures" / "marketore-valid.md"
INVALID = ROOT / "tests" / "fixtures" / "marketore-invalid.md"
VOCAB = ROOT / "outputs" / "research" / "marketore-tags-vocabulary.json"
RESEARCH = ROOT / "outputs" / "research" / "marketore-font-seo-research.md"
TOP48 = ROOT / "outputs" / "research" / "raw" / "marketore-fonts-page-top48.json"


def fail(message: str) -> None:
    raise AssertionError(message)


def check(condition: bool, message: str) -> None:
    if not condition:
        fail(message)
    print(f"[PASS] {message}")


def validate(path: Path, should_pass: bool) -> str:
    result = subprocess.run(
        [sys.executable, str(ROOT / "bin" / "validate_marketore_listing.py"), str(path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    passed = result.returncode == 0
    check(passed is should_pass, f"validator {'accepts' if should_pass else 'rejects'} {path.name}")
    return (result.stdout + result.stderr).strip()


def band(vocabulary_count: int, search_count: int | None = None) -> str:
    if vocabulary_count >= 500 or (search_count is not None and search_count >= 1000):
        return "saturated"
    if vocabulary_count >= 100 or (search_count is not None and search_count >= 100):
        return "established"
    if vocabulary_count >= 17 or (search_count is not None and search_count >= 20):
        return "opportunity"
    return "ultra-niche"


def main() -> int:
    try:
        vocabulary = json.loads(VOCAB.read_text(encoding="utf-8"))
        research = RESEARCH.read_text(encoding="utf-8")
        top48 = json.loads(TOP48.read_text(encoding="utf-8"))
        check(len(vocabulary) == 4353, "captured Marketore vocabulary has 4,353 entries")
        check(len({row["tag"].casefold() for row in vocabulary}) == 4353, "vocabulary has no duplicate folded tag entries")
        check(len(top48["products"]) == 48, "top browse capture contains 48 font listings")
        check("exactly 10 tags" in research.casefold(), "research records the ten-tag top-seller pattern")
        check("first sentence" in research.casefold(), "research records first-sentence metadata extraction")
        check(
            "Commercial ≈ Personal × 2" in research or "Personal ≈ Commercial ÷ 2" in research,
            "research records the Personal/Commercial pricing ratio",
        )
        check("Extended ≈ Commercial × 40" in research, "research records the Extended pricing ratio")

        by_tag = {row["tag"].casefold(): row for row in vocabulary}
        for tag in ("modern", "elegant", "branding font", "font", "magazine"):
            check(tag in by_tag, f"recurring core tag is present in vocabulary: {tag}")
        check(band(by_tag["modern"]["count"]) == "saturated", "Modern is classified as saturated, not as demand proof")
        check(band(by_tag["font duo"]["count"]) == "ultra-niche", "Font Duo is classified as ultra-niche from exact tag adoption")
        check(band(by_tag["blackletter"]["count"]) == "ultra-niche", "blackletter is classified as ultra-niche from exact tag adoption")

        valid_output = validate(VALID, True)
        check("hard gates passed" in valid_output, "valid fixture reports hard-gate success")
        invalid_output = validate(INVALID, False)
        check("absent from captured Marketore vocabulary" in invalid_output, "invalid fixture rejects an invented custom tag")
        check("Main category must be exactly Fonts" in invalid_output, "invalid fixture rejects Creative Market taxonomy")
        check("product description is" in invalid_output, "invalid fixture rejects a description below the live minimum")
    except (OSError, json.JSONDecodeError, KeyError, AssertionError) as exc:
        print(f"[FAIL] Marketore stress test: {exc}")
        return 1
    print("[PASS] Marketore stress test completed: research cache, saturation bands, validator acceptance, and validator rejection are covered")
    return 0


if __name__ == "__main__":
    sys.exit(main())
