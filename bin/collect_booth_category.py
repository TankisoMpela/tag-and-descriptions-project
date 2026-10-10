#!/usr/bin/env python3
"""
collect_booth_category.py — headless, full-category BOOTH data collector.

For a BOOTH browse/tag/search URL this tool walks EVERY page (until no
a[rel="next"] exists or you cap it), extracting every list card (id, name,
price, likes, shop, position) — the full ranking/buffet of the category — and
then optionally fetches detail pages (description, tags, variants, prices)
for the strongest items.

Use the Chrome extension (extensions/booth-data-collector/) for
interactive browsing-session collection; use THIS tool for bulk collection of
the whole category without a browser.

Outputs (written into --out):
  {context}-items.csv    UTF-8 BOM CSV, same schema as the extension
  {context}-items.jsonl  one record per item (nested tags / variants)
  crawl-state.json       resumable checkpoint (use --resume)
  collector-manifest.md  run facts, page map, errors

Example (all pages of the Fonts category, popularity sort, detail pages for
the top 200 by likes):
  python3 bin/collect_booth_category.py \
    --start "https://booth.pm/ja/browse/%E3%83%95%E3%82%A9%E3%83%B3%E3%83%88%E3%83%BB%E6%9B%B8%E4%BD%93?sort=popular" \
    --detail-limit 200

Resume a stopped run:
  python3 bin/collect_booth_category.py --start "<same URL>" --resume

Get real per-item tags + likes (BOOTH hydrates them client-side, so they need a
real browser):
  uv pip install playwright
  python3 bin/collect_booth_category.py --start "..." --browser --detail-limit 200

Stdlib + httpx + lxml (optionally playwright for the --browser detail phase).
"""

import argparse
import json
import random
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import quote, unquote, urljoin

import httpx
from lxml import html as lhtml

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)

# --- same CSV schema as the Chrome extension (extensions/booth-data-collector) ---
CSV_HEADERS = [
    "crawl_date", "sort_mode", "context_tag", "context_category", "page", "position",
    "absolute_position", "item_id", "title", "price_jpy", "likes", "brand", "shop_name",
    "shop_url", "item_url", "card_image_count", "detail_fetched", "description",
    "description_length", "tag_count", "tags", "tag_source", "variants", "price_min",
    "price_max", "formats", "published", "item_like_count", "item_image_count",
    "category_breadcrumb", "extractor_version",
]

EXTRACTOR_VERSION = "cli-1.0.0"


# ----------------------------------------------------------------------------
# tiny helpers
# ----------------------------------------------------------------------------

def clean_text(s):
    return re.sub(r"\s+", " ", s or "").strip()


def jp_text(el):
    return clean_text("".join(el.xpath(".//text()")))


def to_int(v):
    try:
        return int(float(str(v).replace(",", "")))
    except (TypeError, ValueError):
        return None


def parse_money(text):
    t = re.sub(r"[^\d]", "", text or "")
    v = to_int(t)
    return v


def parse_likes(text):
    t = re.sub(r"[^\d]", "", text or "")
    v = to_int(t)
    return v or 0


def parse_context(raw_url):
    ctx = {"context_tag": "", "context_category": "", "category_path": "",
           "sort_mode": "default", "page": 1, "raw_url": str(raw_url or "")}
    from urllib.parse import parse_qs, urlparse
    try:
        u = urlparse(raw_url)
    except Exception:
        return ctx
    qs = parse_qs(u.query)
    p = to_int((qs.get("page") or ["1"])[0])
    ctx["page"] = p if p and p >= 1 else 1
    sort = (qs.get("sort") or [""])[0]
    ctx["sort_mode"] = sort or "default"
    tags = qs.get("tags[]") or qs.get("tags") or []
    if tags:
        ctx["context_tag"] = " | ".join(t for t in tags if t)
    m = re.search(r"/browse/([^/]+)", u.path)
    if m:
        seg = unquote(m.group(1))
        ctx["category_path"] = seg
        ctx["context_category"] = seg
    else:
        cat = (qs.get("category") or [""])[0]
        if cat:
            ctx["context_category"] = cat
    return ctx


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def sleep_ms(ms):
    time.sleep(ms / 1000.0)


# ----------------------------------------------------------------------------
# list page extraction (port of the extension's extractList)
# ----------------------------------------------------------------------------

def parse_list_page(html_bytes, page_url):
    """Returns (products, next_url, card_count)."""
    try:
        doc = lhtml.fromstring(html_bytes)
        doc.make_links_absolute(page_url)
    except Exception as e:
        raise ValueError(f"lxml parse failed: {e}") from e

    context = parse_context(page_url)
    cards = doc.xpath("//li[contains(concat(' ', normalize-space(@class), ' '), ' item-card ')]")
    products = []
    page_size = len(cards) or 60

    for idx, card in enumerate(cards):
        def attr(name):
            return (card.get(name) or "").strip()

        pos_attr = to_int(attr("data-product-position"))
        position = pos_attr if pos_attr is not None else idx

        # title anchor (multiline) + href
        title_el = next(iter(card.xpath(
            ".//a[contains(@class,'item-card__title-anchor')]"
        )), None)
        title = jp_text(title_el) if title_el is not None else jp_text(card)
        item_url = title_el.get("href", "") if title_el is not None else ""

        # shop
        shop_el = next(iter(card.xpath(".//a[contains(@class,'item-card__shop-name-anchor')]")), None)
        shop_url = shop_el.get("href", "") if shop_el is not None else ""
        shop_name = clean_text(
            "".join(card.xpath(".//*[contains(@class,'item-card__shop-name')]//text()"))
        )

        # price: prefer the data attribute (server-rendered), fall back to text
        price_data = attr("data-product-price")
        price_els = card.xpath(".//*[contains(concat(' ', normalize-space(@class), ' '), ' price ')]")
        price_text = jp_text(price_els[0]) if price_els else ""
        price = parse_money(price_data) if price_data not in ("", None) else None
        if price is None:
            price = parse_money(price_text)

        # likes: the wish-list count inside .l-item-card-favorite
        likes = 0
        fav = next(iter(card.xpath(".//*[contains(@class,'l-item-card-favorite')]")), None)
        if fav is not None:
            txt = "".join(fav.xpath(".//text()"))
            likes = parse_likes(txt)

        thumb_count = len(card.xpath(".//a[contains(@class,'item-card__thumbnail-image')]"))

        products.append({
            "page": context["page"],
            "position": position,
            "absolute_position": (context["page"] - 1) * page_size + idx + 1,
            "sort_mode": context["sort_mode"],
            "context_tag": context["context_tag"],
            "context_category": context["context_category"],
            "item_id": attr("data-product-id"),
            "title": title,
            "price_jpy": price if price is not None else 0,
            "raw_price": price_data,
            "likes": likes,
            "brand": attr("data-product-brand"),
            "shop_name": shop_name,
            "shop_url": shop_url,
            "item_url": item_url,
            "card_image_count": thumb_count,
            "category_id": attr("data-product-category"),
            "url": page_url,
        })

    next_els = doc.xpath("//a[@rel='next']")
    next_url = next_els[0].get("href", "") if next_els else ""

    return products, next_url, len(cards)


# ----------------------------------------------------------------------------
# item detail page extraction (port of the extension's parseItemDetail)
# ----------------------------------------------------------------------------

def tags_from_raw_html(text):
    seen = []
    patterns = [
        r"tags%5B%5D=([^&\"'\s<>]+)",
        r"tags%5B\d+%5D=([^&\"'\s<>]+)",
        r"tags\[\]=([^&\"'\s<>]+)",
    ]
    for pat in patterns:
        for m in re.finditer(pat, text or "", re.I):
            try:
                t = clean_text(unquote(m.group(1)))
            except Exception:
                t = clean_text(m.group(1))
            if t and len(t) <= 60 and t not in seen:
                seen.append(t)
    return seen


def css_to_xpath(sel):
    """Minimal CSS-to-XPath for the selectors used here (.class, #id, and
    '.class img' descendant chains). Avoids the cssselect dependency."""
    out = []
    for part in sel.split():
        if part.startswith("#"):
            out.append(f"*[@id='{part[1:]}']")
        elif part.startswith("."):
            out.append(f"*[contains(concat(' ', normalize-space(@class), ' '), ' {part[1:]} ')]")
        else:
            out.append(part)
    return "//" + "//".join(out)


def parse_item_detail(html_bytes, html_text, meta):
    base = (meta or {}).get("item_url") or "https://booth.pm"
    try:
        doc = lhtml.fromstring(html_bytes)
        doc.make_links_absolute(base)
    except Exception:
        doc = None

    body_text = ""
    if doc is not None:
        body_text = "\n".join(doc.xpath("//body//text()"))

    # title
    title = ""
    if doc is not None:
        h1 = doc.xpath("//h1")
        if h1:
            title = jp_text(h1[0])
    if not title and doc is not None:
        og = doc.xpath("//meta[@property='og:title']")
        if og:
            title = clean_text(og[0].get("content"))
    if title:
        # og:title includes " - {shop} - BOOTH" / " - BOOTH"; keep the clean product title
        title = re.sub(r"\s+-\s+[^-]+-\s+BOOTH\s*$", "", title)
        title = re.sub(r"\s+-\s+BOOTH\s*$", "", title)
    if not title:
        title = (meta or {}).get("title", "")

    # description
    description, desc_source = "", ""
    if doc is not None:
        for sel in (".item-description", ".js-item-description", "#item-description",
                    ".box-description", ".item_description", ".item-description__body"):
            els = doc.xpath(css_to_xpath(sel))
            if els and clean_text("".join(els[0].xpath(".//text()"))):
                description = clean_text("".join(els[0].xpath(".//text()")))
                desc_source = sel
                break
    if not description and doc is not None:
        for xp in ("//meta[@name='description']", "//meta[@property='og:description']",
                   "//meta[@name='twitter:description']"):
            els = doc.xpath(xp)
            if els and (els[0].get("content") or "").strip():
                description = clean_text(els[0].get("content"))
                desc_source = xp
                break

    # tags
    tags, tag_source = [], ""
    if doc is not None:
        tag_xpaths = [
            "//*[@id='js-item-tag-list']//a",
            ".//*[contains(@class,'item-tag-list')]//a",
            ".//*[contains(concat(' ', normalize-space(@class), ' '), ' tags ')]//a",
            ".//*[contains(@class,'tag-list')]//a",
            ".//*[contains(@class,'item-tag')]//a",
            ".//*[contains(@class,'nav-tags')]//a",
            ".//a[contains(@href,'tags%5B%5D')]",
        ]
        for xp in tag_xpaths:
            found = [t for t in (jp_text(a) for a in doc.xpath(xp))
                     if t and "で検索" not in t and " x " not in t]
            found = list(dict.fromkeys(found))
            if found:
                tags, tag_source = found, xp
                break
    if not tags:
        # NOTE: BOOTH renders tags client-side into #js-item-tag-list; the server
        # HTML carries no per-item tags, and the site-wide meta[name=keywords] is
        # boilerplate, not item tags. We try the embedded-route decode (inert when
        # BOOTH stops embedding routes), then record an honest empty set.
        raw_tags = tags_from_raw_html(html_text)
        if raw_tags:
            tags, tag_source = raw_tags, "embedded-href (tags[] route decode)"
        else:
            tags, tag_source = [], "NOT-AVAILABLE (server HTML hides tags)"

    # prices / variants — read the purchase-box DOM. Each priced option is a
    # .variation-item block carrying .variation-name + .variation-price.
    variants = []
    main_prices = []
    if doc is not None:
        price_els = doc.xpath(
            ".//*[contains(concat(' ', normalize-space(@class), ' '), ' variation-price ')]")
        for pel in price_els:
            p = parse_money("".join(pel.xpath(".//text()")))
            if p is None or p >= 50_000_000:
                continue
            main_prices.append(p)
            name = ""
            node = pel
            for _ in range(6):
                node = node.getparent()
                if node is None:
                    break
                names = node.xpath(
                    ".//*[contains(concat(' ', normalize-space(@class), ' '), ' variation-name ')]")
                if names:
                    t = clean_text("".join(names[0].xpath(".//text()")))
                    t = re.sub(r"^Variant\s*name\s*[:：]?\s*[`'\"]?", "", t).strip()
                    t = re.sub(r"[`'\"]+\s*$", "", t).strip()
                    name = clean_text(t)
                    break
            variants.append({"name": name or f"variant-{len(variants) + 1}", "priceJpy": p})

    # Fallback for layouts without .variation-price: only ¥/￥-prefixed numbers
    # inside the main region (up to the first add-to-cart button — related item
    # prices further down would pollute min/max).
    if not main_prices:
        region = body_text
        ci = body_text.find("カートに入れる")
        if ci >= 0:
            region = body_text[: ci + len("カートに入れる")]
        price_hits = re.findall(r"[¥￥]\s*(\d[\d,]*)", region)
        price_hits += [m[1] for m in re.finditer(r"(\d{1,3}(?:,\d{3})+)\s*円", region)]
        main_prices = [v for v in (parse_money(p) for p in price_hits)
                       if v is not None and 0 <= v < 50_000_000]
    if not variants and main_prices:
        variants.append({"name": "single", "priceJpy": main_prices[0]})
    if not variants and meta is not None and meta.get("price_jpy") is not None:
        variants.append({"name": "single", "priceJpy": meta["price_jpy"]})

    # A purchase box with no .variation-name at all is a single-price item —
    # label it "single" instead of leaving generic variant-1/2 names.
    if doc is not None and len(variants) > 0:
        has_names = bool(doc.xpath(
            ".//*[contains(concat(' ', normalize-space(@class), ' '), ' variation-name ')]"))
        if not has_names:
            for _v in variants:
                _v["name"] = "single"

    positive = [v for v in main_prices if v > 0]
    price_min = min(positive) if positive else (min(main_prices) if main_prices else None)
    price_max = max(main_prices) if main_prices else None
    if price_min is None:
        price_min = price_max
    variant_string = " | ".join(
        f"{v['name']}:{('¥' + str(v['priceJpy'])) if v['priceJpy'] is not None else '?'}"
        for v in variants)

    # formats
    hay = (description or "") + " " + body_text
    formats = list(dict.fromkeys(
        m.group(0).upper() for m in re.finditer(r"\b(OTF|TTF|WOFF2?|OPS?|ZIP)\b", hay, re.I)))

    # image count
    image_count = 0
    if doc is not None:
        for sel in (".js-item-image-list img", ".item-image-list img", ".swiper-wrapper img",
                    ".thumbnail-list img", ".images img"):
            els = doc.xpath(css_to_xpath(sel))
            if els:
                image_count = len(els)
                break
    if not image_count and doc is not None:
        image_count = len(doc.xpath("//img[@data-original]"))
    if not image_count and doc is not None:
        image_count = len(doc.xpath("//img"))

    # published — server HTML carries <meta property="article:published_time">;
    # on hydrated pages (--browser) the item page shows 商品公開日時：YYYY年M月D日.
    published = ""
    if doc is not None:
        pub = doc.xpath("//meta[@property='article:published_time']")
        if pub and pub[0].get("content"):
            published = pub[0].get("content")
    if not published and doc is not None:
        m = None
        for el in doc.xpath("//*[contains(normalize-space(.), '商品公開日時')][1]"):
            m = re.search(r"(20\d{2})[年\/\-.](\d{1,2})(?:[月\/\-.](\d{1,2}))?",
                          "".join(el.itertext()))
        if m:
            published = "-".join(x for x in m.groups() if x)
    if not published:
        dm = re.search(r"(?:登録|公開|投稿)[日時]?[：:]?\s*(\d{4})[年\/\-.](\d{1,2})(?:[月\/\-.](\d{1,2}))?", body_text)
        if dm:
            published = "-".join(x for x in dm.groups() if x)

    # item like count
    like_count_item = None
    if doc is not None:
        # On hydrated item pages the wish-list (like) count renders in a
        # typography-14 element beside the wish-list button.  The main item's
        # count lives under #js-item-wishlist-button; the related-item cards
        # have their own with a different id.
        like_count_item = None
        if doc is not None:
            for xp in ("//*[@id='js-item-wishlist-button']//div[contains(@class,'typography-14')]",
                       ".//*[contains(concat(' ', normalize-space(@class), ' '), ' like-count ')]",
                       ".//*[contains(@class,'js-item-like-count')]",
                       ".//*[contains(concat(' ', normalize-space(@class), ' '), ' wish-list ')]",
                       ".//*[contains(@class,'js-item-wish-list-button')]//*[contains(@class,'typography-14')]"):
                els = doc.xpath(xp)
                if els:
                    v = parse_likes("".join(els[0].xpath(".//text()")))
                    if v is not None:
                        like_count_item = v
                        break

    # breadcrumb
    crumbs = []
    if doc is not None:
        crumbs = [clean_text(a) for a in doc.xpath(
            "//*[contains(@class,'breadcrumb')]//a[contains(@href,'/browse/')]")]

    return {
        "detailFetched": True,
        "detailFetchedAt": now_iso(),
        "detailTitle": title,
        "description": description,
        "descriptionLength": len(description),
        "tags": tags,
        "tagCount": len(tags),
        "tagSource": tag_source,
        "variants": variants,
        "variantString": variant_string,
        "priceMin": price_min,
        "priceMax": price_max,
        "formats": formats,
        "formatString": " ".join(formats),
        "published": published,
        "likeCountItem": like_count_item,
        "imageCountItem": image_count,
        "categoryBreadcrumb": " > ".join(crumbs),
    }


# ----------------------------------------------------------------------------
# CSV / JSONL / manifest writers
# ----------------------------------------------------------------------------

def flatten(rec):
    tags = rec.get("tags") if isinstance(rec.get("tags"), list) else []
    return {
        "crawl_date": date.today().isoformat(),
        "sort_mode": rec.get("sort_mode", ""),
        "context_tag": rec.get("context_tag", ""),
        "context_category": rec.get("context_category", ""),
        "page": rec.get("page", ""),
        "position": rec.get("position", ""),
        "absolute_position": rec.get("absolute_position", ""),
        "item_id": rec.get("item_id", ""),
        "title": rec.get("title") or rec.get("detailTitle", ""),
        "price_jpy": rec.get("price_jpy", ""),
        "likes": rec.get("likes", 0),
        "brand": rec.get("brand", ""),
        "shop_name": rec.get("shop_name", ""),
        "shop_url": rec.get("shop_url", ""),
        "item_url": rec.get("item_url", ""),
        "card_image_count": rec.get("card_image_count", ""),
        "detail_fetched": "yes" if rec.get("detailFetched") else "no",
        "description": rec.get("description", ""),
        "description_length": rec.get("descriptionLength", ""),
        "tag_count": len(tags) if tags else rec.get("tagCount", ""),
        "tags": " | ".join(tags),
        "tag_source": rec.get("tagSource", ""),
        "variants": rec.get("variantString", ""),
        "price_min": rec.get("priceMin", ""),
        "price_max": rec.get("priceMax", ""),
        "formats": rec.get("formatString", ""),
        "published": rec.get("published", ""),
        "item_like_count": rec.get("likeCountItem", ""),
        "item_image_count": rec.get("imageCountItem", ""),
        "category_breadcrumb": rec.get("categoryBreadcrumb", ""),
        "extractor_version": EXTRACTOR_VERSION,
    }


def csv_escape(v):
    s = str("" if v is None else v)
    if re.search(r'[",\n\r]', s):
        return '"' + s.replace('"', '""') + '"'
    return s


def build_csv(records):
    rows = [",".join(csv_escape(flatten(r)[h]) for h in CSV_HEADERS) for r in records]
    return "\ufeff" + ",".join(CSV_HEADERS) + "\n" + "\n".join(rows)


def build_jsonl(records):
    return "\n".join(
        json.dumps({**rec, "extractor_version": EXTRACTOR_VERSION}, ensure_ascii=False)
        for rec in records
    )


# ----------------------------------------------------------------------------
# HTTP
# ----------------------------------------------------------------------------

def make_client(timeout):
    return httpx.Client(
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ja-JP,ja;q=0.9,en;q=0.8",
        },
        follow_redirects=True,
        timeout=timeout,
    )


def fetch_page(client, url, retries=3, base_delay=1.0):
    last = None
    for attempt in range(retries):
        try:
            r = client.get(url)
            if r.status_code in (429, 500, 502, 503, 504):
                last = f"HTTP {r.status_code}"
                sleep_ms(int(base_delay * 1000 * (attempt + 1)) + random.randint(0, 500))
                continue
            if r.status_code >= 400:
                return None, f"HTTP {r.status_code}"
            return r, None
        except Exception as e:
            last = str(e)
            sleep_ms(int(base_delay * 1000 * (attempt + 1)) + random.randint(0, 500))
    return None, f"failed: {last}"


# ----------------------------------------------------------------------------
# crawl orchestration
# ----------------------------------------------------------------------------

def slug_for(context, start_url):
    name = context.get("context_tag") or context.get("context_category") or "browse"
    slug = re.sub(r"[^A-Za-z0-9\u3040-\u30ff\u4e00-\u9fff]+", "-", name).strip("-")[:40]
    return slug or "booth"


def run(client, args, state, out_dir):
    context = parse_context(args.start)
    log = state["log"]
    def add_log(msg):
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {msg}"
        log.append(line)
        print(line, flush=True)

    # ---------- LIST PHASE ----------
    if not state.get("list_phase_done"):
        url = state.get("next_url") or args.start
        while True:
            if state.get("stop"):
                break
            if args.max_pages and state["pages_done"] >= args.max_pages:
                add_log(f"max-pages reached ({args.max_pages}); stopping list phase")
                break
            if args.max_items and len(state["products"]) >= args.max_items:
                add_log(f"max-items reached ({args.max_items}); stopping list phase")
                break

            add_log(f"page {state['pages_done'] + 1}: {url}")
            resp, err = fetch_page(client, url, retries=args.retries)
            if err:
                state["errors"].append({"at": now_iso(), "url": url, "msg": err})
                add_log(f"  ERROR {err}")
                break
            try:
                products, next_url, card_count = parse_list_page(resp.content, url)
            except Exception as e:
                state["errors"].append({"at": now_iso(), "url": url, "msg": f"parse: {e}"})
                add_log(f"  PARSE ERROR {e}")
                break

            seen = {p["item_id"] + "|" + p["item_url"] for p in state["products"]}
            added = 0
            for p in products:
                key = p["item_id"] + "|" + p["item_url"]
                if key in seen:
                    continue
                seen.add(key)
                state["products"].append(p)
                added += 1

            state["pages_done"] += 1
            state["next_url"] = next_url
            state["last_url"] = url
            add_log(f"  {card_count} cards, +{added} new  (total {len(state['products'])})")
            save_state(out_dir, state)

            if not next_url:
                add_log("no more pages; list phase complete")
                break
            url = next_url
            sleep_ms(args.list_delay + random.randint(0, 300))

        state["list_phase_done"] = True
        save_state(out_dir, state)

    # ---------- DETAIL PHASE ----------
    detail_limit = args.detail_limit if args.detail_limit is not None else 200
    if detail_limit != 0:
        products = state["products"]
        # Server HTML carries no like counts (likes hydrate client-side), so the
        # ordering signal is the crawl position. On a sort=popular crawl that IS
        # the popularity ranking: the first N items are the top-N by popularity.
        # --browser mode reloads each detail item in Chromium and reads the
        # hydrated tags + real like count from the live DOM.
        queue = sorted(
            [p for p in products if p.get("item_url")],
            key=lambda p: (p.get("absolute_position") or 0),
        )[:detail_limit]

        pending = [p for p in queue if p["item_id"] not in state["details"]]
        add_log(f"detail phase: {len(pending)} items to fetch (limit {detail_limit}, "
                f"already fetched {len(state['details'])})")

        if args.browser:
            if not pending:
                add_log("nothing left to fetch; skipping browser detail phase")
            else:
                run_browser_details(args, state, pending, add_log, save_state, out_dir)
        else:
            lock = threading.Lock()
            idx = 0

            def worker():
                nonlocal idx
                while True:
                    with lock:
                        i = idx
                        idx += 1
                    if i >= len(pending):
                        return
                    job = pending[i]
                    if job["item_id"] in state["details"]:
                        return
                    detail, err = fetch_item_detail(client, job, retries=args.retries)
                    with lock:
                        if detail is not None:
                            state["details"][job["item_id"]] = detail
                            # merge into product record
                            fresh = next((p for p in state["products"] if p["item_id"] == job["item_id"]), None)
                            if fresh is not None:
                                fresh.update(detail)
                        else:
                            state["errors"].append({"at": now_iso(), "item_id": job["item_id"],
                                                    "msg": "detail fetch failed: " + (err or "unknown")})
                        done = len(state["details"])
                        if done and (done % 10 == 0 or done == len(pending)):
                            save_state(out_dir, state)
                            add_log(f"  details: {done}/{len(pending)}")
                    sleep_ms(args.detail_delay + random.randint(0, 500))

            with ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as pool:
                list(pool.map(lambda _: worker(), range(min(args.concurrency, len(pending)))))
            save_state(out_dir, state)
            add_log(f"detail phase complete: {len(state['details'])} fetched")

    state["status"] = "done"
    state["finished_at"] = now_iso()
    save_state(out_dir, state)


def fetch_item_detail(client, job, retries=3):
    resp, err = fetch_page(client, job["item_url"], retries=retries)
    if resp is None:
        return None, err
    try:
        detail = parse_item_detail(resp.content, resp.text, {
            "item_id": job["item_id"],
            "item_url": job["item_url"],
            "title": job.get("title"),
            "price_jpy": job.get("price_jpy"),
        })
        return detail, None
    except Exception as e:
        return None, f"parse: {e}"


def run_browser_details(args, state, pending, add_log, save_state, out_dir):
    """Detail phase run through headless Chromium: BOOTH hydrates tags and like
    counts client-side, so the hydrated DOM (page.content()) must be collected in
    a real browser. Sequential per-item (politeness + one playright browser)."""
    import os
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

    # Auto-locate the Playwright browser cache: PLAYWRIGHT_BROWSERS_PATH may point
    # at a dead path (e.g. a sandbox .opencode2-cache), while the actual download
    # lives in ~/.cache/ms-playwright. Pick the first candidate that exists.
    cache_candidates = [
        os.environ.get("PLAYWRIGHT_BROWSERS_PATH", ""),
        os.path.expanduser("~/.cache/ms-playwright"),
        os.path.expanduser("~/Library/Caches/ms-playwright"),
        os.path.expanduser("~/Projects/.opencode2-cache/ms-playwright"),
    ]
    for cand in cache_candidates:
        if not cand:
            continue
        try:
            has_chromium = any(
                os.path.isdir(os.path.join(cand, d)) and d.startswith("chromium")
                for d in os.listdir(cand)
            )
        except OSError:
            has_chromium = False
        if has_chromium:
            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = cand
            break

    _transport_kw = (
        "connection closed", "connection reset", "target closed",
        "browser has been closed", "browser has disconnected",
        "browser was disconnected", "context was destroyed",
        "execution context was destroyed", "disconnected",
        "connection lost", "broken pipe", "epipe", "eof",
        "i/o error", "the browser may have crashed",
    )

    def _is_transport_failure(exc):
        if isinstance(exc, (BrokenPipeError, ConnectionResetError, EOFError, OSError)):
            return True
        msg = str(exc).lower()
        return any(k in msg for k in _transport_kw)

    def _quiet_close(obj):
        if obj is None:
            return
        try:
            obj.close()
        except Exception:
            pass

    with sync_playwright() as p:
        browser = None
        context = None
        idx = 0
        while idx < len(pending):
            job = pending[idx]
            if job["item_id"] in state["details"]:
                idx += 1
                continue

            # Per-item: up to 2 page-processing attempts. A transport-level
            # failure (driver/browser death, broken pipe, disconnect) tears the
            # session down and retries the same item once in a fresh browser
            # instead of killing the whole run.
            detail = None
            page_tries = 0
            while page_tries < 2:
                page_tries += 1

                # (Re)launch the browser if we don't have a live session.
                if browser is None:
                    launch_tries = 0
                    while browser is None:
                        launch_tries += 1
                        if launch_tries > 6:
                            raise RuntimeError(
                                f"could not (re)launch Chromium after 6 attempts "
                                f"(item {job['item_id']})")
                        try:
                            browser = p.chromium.launch(headless=True)
                            context = browser.new_context(
                                user_agent=USER_AGENT,
                                viewport={"width": 1280, "height": 900},
                                extra_http_headers={"Accept-Language": "ja-JP,ja;q=0.9,en;q=0.8"},
                            )
                        except Exception as e:
                            add_log(f"browser launch attempt {launch_tries} failed for "
                                    f"{job['item_id']}: {e}")
                            _quiet_close(browser)
                            browser = None
                            context = None
                            sleep_ms(5000 + random.randint(0, 3000))

                try:
                    page = context.new_page()
                except Exception as e:
                    # Session died between items: relaunch next iteration.
                    state["errors"].append({"at": now_iso(), "item_id": job["item_id"],
                                            "msg": "browser session died between items: " + str(e)})
                    _quiet_close(browser)
                    browser = None
                    context = None
                    continue

                try:
                    page.goto(job["item_url"], wait_until="domcontentloaded",
                              timeout=args.browser_timeout * 1000)
                    try:
                        page.wait_for_selector("#js-item-tag-list a",
                                               timeout=args.browser_timeout * 1000)
                    except PWTimeout:
                        pass  # hydration slower than usual — use whatever is there
                    html = page.content()
                    detail = parse_item_detail(html.encode("utf-8"), html, {
                        "item_id": job["item_id"],
                        "item_url": job["item_url"],
                        "title": job.get("title"),
                        "price_jpy": job.get("price_jpy"),
                    })
                except Exception as e:
                    if _is_transport_failure(e):
                        state["errors"].append({"at": now_iso(), "item_id": job["item_id"],
                                                "msg": "browser transport failure (relaunching): " + str(e)})
                        _quiet_close(browser)
                        browser = None
                        context = None
                        continue  # retry this item in a fresh browser
                    state["errors"].append({"at": now_iso(), "item_id": job["item_id"],
                                            "msg": "browser detail failed: " + str(e)})
                finally:
                    _quiet_close(page)
                break  # success or non-transport failure -> move to next item

            if detail is not None:
                state["details"][job["item_id"]] = detail
                fresh = next((pp for pp in state["products"]
                              if pp["item_id"] == job["item_id"]), None)
                if fresh is not None:
                    fresh.update(detail)
                done = len(state["details"])
                if done and (done % 10 == 0 or done == len(pending)):
                    save_state(out_dir, state)
                    add_log(f"  browser details: {done}/{len(pending)}")
            idx += 1
            sleep_ms(args.detail_delay + random.randint(0, 300))
        _quiet_close(browser)
    save_state(out_dir, state)
    add_log(f"browser detail phase complete: {len(state['details'])} fetched")


# ----------------------------------------------------------------------------
# state / outputs
# ----------------------------------------------------------------------------

STATE_FILE = "crawl-state.json"
MANIFEST_FILE = "collector-manifest.md"


def fresh_state(start_url):
    return {
        "status": "running",
        "started_at": now_iso(),
        "start_url": start_url,
        "pages_done": 0,
        "products": [],
        "details": {},
        "next_url": "",
        "last_url": "",
        "list_phase_done": False,
        "errors": [],
        "log": [],
        "stop": False,
    }


def save_state(out_dir, state):
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp = out_dir / (STATE_FILE + ".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(out_dir / STATE_FILE)


def slugified_name(context):
    name = context.get("context_tag") or context.get("context_category") or "browse"
    return re.sub(r"[^A-Za-z0-9\u3040-\u30ff\u4e00-\u9fff]+", "-", unquote(name)).strip("-")[:40]


def write_outputs(out_dir, state, context, args):
    records = []
    for p in state["products"]:
        d = state["details"].get(p["item_id"])
        merged = {**p, **(d or {})}
        merged.setdefault("detailFetched", False)
        if d:
            merged["detailFetched"] = True
        records.append(merged)

    base = f"{slugified_name(context)}-items"
    (out_dir / f"{base}.csv").write_text(build_csv(records), encoding="utf-8")
    (out_dir / f"{base}.jsonl").write_text(build_jsonl(records), encoding="utf-8")

    lines = []
    def out(s=""):
        lines.append(s)
    out(f"# BOOTH Category Collector Manifest — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    out()
    out(f"- Start URL: `{args.start}`")
    out(f"- Collector: {EXTRACTOR_VERSION}")
    out(f"- Status: {state['status']}")
    out(f"- Sort mode recorded: `{context['sort_mode']}`")
    out(f"- Context tag: `{context['context_tag'] or '-'}`")
    out(f"- Context category: `{context['context_category'] or '-'}`")
    out(f"- Pages walked: {state['pages_done']}")
    out(f"- Unique products: {len(state['products'])}")
    out(f"- Detail pages fetched: {len(state['details'])} (limit: {args.detail_limit if args.detail_limit is not None else 200})")
    out(f"- Started: {state.get('started_at')}  Finished: {state.get('finished_at', '-')}")
    out()
    out("## Errors")
    out()
    if state["errors"]:
        for e in state["errors"][-40:]:
            out(f"- {e.get('at')} {e.get('url') or e.get('item_id')}: {e['msg']}")
    else:
        out("- none")
    out()
    out("## Page map")
    out()
    for i in range(1, state["pages_done"] + 1):
        out(f"- page {i}: recorded")
    out()
    out("## Notes")
    out()
    out("- **Ranking semantics**: `absolute_position` is the order items appeared in")
    out("  the crawl (page*60 + on-page position), so under the recorded sort it IS the")
    out("  ranking. With `?sort=popular` this is popularity descending — the 'highest to")
    out("  lowest in popularity' view. Do not treat the card-level `likes` column as data:")
    out("  BOOTH server HTML renders like counts client-side, so it records 0.")
    if args.browser:
        out(f"- Detail extraction mode: Chromium browser hydration (--browser). Each detail")
        out("  page was loaded in headless Chromium and parsed after hydration, so the")
        out("  `item_like_count` column holds the REAL wish-list count and `tags` holds the")
        out("  item's real tags (tag_source carries the DOM selector).")
    else:
        out("- Detail extraction mode: raw HTTP (server HTML). Tags and like counts are")
        out("  client-side, so raw-HTTP detail rows have tag_source NOT-AVAILABLE and are")
        out("  the reason `item_like_count` is empty. Re-run with --browser to capture them.")
    out("- This dataset is raw collected data (catalog/popularity signals). Nothing here")
    out("  was refreshed from the frozen `outputs/research/booth-font-tag-bank.md`, which")
    out("  stays the paid-listing baseline.")
    out("- Join with the FontFairy rank CSV and analyze with:")
    out("  `python3 bin/analyze_booth_collection.py --collection <this csv> --rank <rank csv> --bank outputs/research/booth-font-tag-bank.md`")
    (out_dir / MANIFEST_FILE).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="Headless full-category BOOTH collector")
    ap.add_argument("--start", required=True, help="BOOTH browse/tag/search URL (set ?sort=popular for popularity order)")
    ap.add_argument("--out", default=None, help="Output dir (default: outputs/research/booth-live-collector/{date}/{slug})")
    ap.add_argument("--max-pages", type=int, default=0, help="0 = unlimited (walk until no next page)")
    ap.add_argument("--max-items", type=int, default=0, help="0 = unlimited product rows")
    ap.add_argument("--detail-limit", type=int, default=200,
                    help="Fetch detail pages for the top-N items by likes (0 = every item)")
    ap.add_argument("--concurrency", type=int, default=3, help="Detail fetch concurrency (1-8)")
    ap.add_argument("--list-delay", type=int, default=600, help="Delay ms between list pages")
    ap.add_argument("--detail-delay", type=int, default=900, help="Delay ms between detail fetches (per worker)")
    ap.add_argument("--retries", type=int, default=3, help="Fetch retries with backoff")
    ap.add_argument("--timeout", type=float, default=25.0, help="HTTP timeout seconds")
    ap.add_argument("--browser", action="store_true",
                    help="Fetch detail pages in headless Chromium so BOOTH's client-side "
                         "tags and like counts hydrate (needs: uv pip install playwright). "
                         "Slower (sequential), but gives real tags + likes per item.")
    ap.add_argument("--browser-timeout", type=int, default=25,
                    help="Seconds to wait for tag hydration in --browser mode (default 25)")
    ap.add_argument("--resume", action="store_true", help="Resume a stopped run in --out")
    ap.add_argument("--tags-file", default=None,
                    help="File with one tag page URL (or bare tag name) per line — runs a short "
                         "list-only crawl per tag into outdir/tag-{tag}/ for tag-level popularity "
                         "rankings (this is the headless path to tag science, since item pages "
                         "hide tags server-side)")
    ap.add_argument("--tag-pages", type=int, default=1,
                    help="Max list pages per tag when using --tags-file (default 1 = top page)")
    args = ap.parse_args()

    if args.detail_limit is not None and args.detail_limit < 0:
        ap.error("--detail-limit must be >= 0 (0 = all)")

    context = parse_context(args.start)
    out_dir = Path(args.out) if args.out else Path(
        f"outputs/research/booth-live-collector/{date.today().isoformat()}/{slugified_name(context)}")
    out_dir.mkdir(parents=True, exist_ok=True)

    state_file = out_dir / STATE_FILE
    if state_file.exists():
        if args.resume:
            state = json.loads(state_file.read_text(encoding="utf-8"))
            print(f"Resuming run at {out_dir} ({state['pages_done']} pages done, "
                  f"{len(state['products'])} products, {len(state['details'])} details)")
        else:
            bak = out_dir / f"crawl-state-{int(time.time())}.json.bak"
            state_file.rename(bak)
            print(f"Existing run moved aside: {bak.name}. Starting fresh.")
            state = fresh_state(args.start)
    else:
        if args.resume:
            print("No existing run to resume; starting fresh.")
        state = fresh_state(args.start)

    client = make_client(args.timeout)

    # ---- --tags-file mode: one list-only crawl per tag ----
    if args.tags_file:
        import types as _types
        with open(args.tags_file, "r", encoding="utf-8") as f:
            lines = [ln.strip() for ln in f if ln.strip() and not ln.lstrip().startswith("#")]
        for line in lines:
            if line.lower().startswith("http"):
                target = line
            else:
                target = f"https://booth.pm/ja/items?tags%5B%5D={quote(line)}&sort=popular"
            tctx = parse_context(target)
            tag_dir = out_dir / f"tag-{slugified_name(tctx)}"
            tag_dir.mkdir(parents=True, exist_ok=True)
            targs = _types.SimpleNamespace(**vars(args))
            targs.start = target
            targs.max_pages = args.tag_pages
            targs.detail_limit = 0  # list-only for tag ranking
            targs.max_items = args.max_items
            tstate = fresh_state(target)
            tstate_file = tag_dir / STATE_FILE
            if tstate_file.exists() and args.resume:
                tstate = json.loads(tstate_file.read_text(encoding="utf-8"))
            print(f"\n=== tag crawl: {target} -> {tag_dir}")
            try:
                run(client, targs, tstate, tag_dir)
            except KeyboardInterrupt:
                tstate["status"] = "stopped"
                tstate["stop"] = True
                save_state(tag_dir, tstate)
                raise
            write_outputs(tag_dir, tstate, tctx, targs)
            print(f"   tag outputs: {tag_dir}")
        return 0

    try:
        run(client, args, state, out_dir)
    except KeyboardInterrupt:
        state.setdefault("status", "stopped")
        state["stop"] = True
        state["finished_at"] = now_iso()
        save_state(out_dir, state)
        print("\nInterrupted. State saved — re-run with --resume to continue.")
    finally:
        try:
            write_outputs(out_dir, state, context, args)
            print(f"Outputs written to {out_dir}")
        except Exception as e:
            print(f"Warning: could not write outputs: {e}")
        client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())