#!/usr/bin/env python3
"""Legacy local Crawl4AI helper retained for diagnostics only.

Usage: python3 bin/crawl4ai_fetch.py https://example.com
Current marketplace agents must not call this helper. They use Firecrawl first,
then Serper/Exa for discovery and WebFetch once after a Firecrawl rate limit or
failure. This helper remains only for explicit diagnostics or future user-
requested experiments.
"""

import argparse
import asyncio
import os
import site
import sys
from pathlib import Path
from tempfile import gettempdir


USER_ENV = Path.home() / ".local/share/crawl4ai-venv"
if USER_ENV.exists():
    sys.path.insert(0, str(USER_ENV / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"))
# OpenCode's sandbox may expose the home directory read-only. Crawl4AI's
# robots/config cache is disposable for this one-URL fallback, so keep it in
# a writable temporary location unless the caller explicitly overrides it.
os.environ.setdefault("CRAWL4_AI_BASE_DIRECTORY", str(Path(gettempdir()) / "crawl4ai-runtime"))


async def fetch(url: str) -> int:
    try:
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig
    except ImportError:
        print("Crawl4AI is not installed in the configured environment", file=sys.stderr)
        return 2

    browser = BrowserConfig(headless=True, verbose=False)
    # Avoid Crawl4AI's default on-disk cache: marketplace agents use this as a
    # bounded fallback and should not fail because a cache directory is absent
    # or not writable in the caller's environment.
    config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, page_timeout=30000)
    try:
        async with AsyncWebCrawler(config=browser) as crawler:
            result = await asyncio.wait_for(crawler.arun(url=url, config=config), timeout=40)
    except Exception as exc:
        print(f"Crawl4AI fetch failed: {exc}", file=sys.stderr)
        return 1

    if not result.success:
        print(f"Crawl4AI fetch failed: {result.error_message or 'unknown error'}", file=sys.stderr)
        return 1
    print(result.markdown or result.cleaned_html or "")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    args = parser.parse_args()
    return asyncio.run(fetch(args.url))


if __name__ == "__main__":
    raise SystemExit(main())
