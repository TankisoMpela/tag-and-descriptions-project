#!/usr/bin/env python3
"""
collect_dlsite_category.py — DLsite Tools/Accessories collector (mirrors collect_booth_category.py).

Walks the TOL category pagination (page 1..55, per_page=30, order=trend) at
https://www.dlsite.com/home/fsr/=/work_type/TOL and extracts every list card
(product_id, title, maker, price).
Enriches products with exact sales/downloads (dl_count), favorites (wishlist_count),
ratings, and official pricing via the batch AJAX API (/home/product/info/ajax).
Fetches detail pages (https://www.dlsite.com/home/work/=/product_id/{ID}.html)
for #work_outline (genre, file format, file size, release date, author) and
descriptions to identify true font items.

Outputs (into --out):
  tools-accessories-items.csv    UTF-8 BOM CSV
  tools-accessories-items.jsonl  one record per item
  crawl-state.json               resumable checkpoint (use --resume)
  collector-manifest.md          run facts, page map, errors

Example:
  python3 bin/collect_dlsite_category.py --start "https://www.dlsite.com/home/fsr/=/work_type/TOL" --detail-limit 300
  python3 bin/collect_dlsite_category.py --max-pages 2 --detail-limit 10  # quick probe

Stdlib + httpx + lxml.
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

import signal
import httpx
from lxml import html as lhtml

_sig_received = None

def _sig_handler(signum, frame):
    global _sig_received
    _sig_received = signum
    raise KeyboardInterrupt(f"Process received signal {signum}")

try:
    signal.signal(signal.SIGINT, _sig_handler)
    signal.signal(signal.SIGTERM, _sig_handler)
except Exception:
    pass

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)

CSV_HEADERS = [
    "crawl_date", "work_type", "context_category", "page", "position",
    "absolute_position", "product_id", "title", "title_jp", "price_jpy",
    "official_price", "price_display", "maker_id", "maker_name", "maker_url", "item_url",
    "thumb_url", "detail_fetched", "description", "description_length",
    "genre", "file_format", "file_size", "published", "sales_count",
    "favorites_count", "rating_count", "rate_average", "review_count",
    "language", "is_font", "custom_genres", "extractor_version",
]

EXTRACTOR_VERSION = "cli-dlsite-1.1.0"
DEFAULT_START = "https://www.dlsite.com/home/fsr/=/work_type/TOL/work_type_name/%E3%83%84%E3%83%BC%E3%83%AB%2F%E3%82%A2%E3%82%AF%E3%82%BB%E3%82%B5%E3%83%AA/language/jp/age_category/general/order/trend/per_page/30/page/1/show_type/3"

def clean_text(s):
    return re.sub(r"\s+", " ", s or "").strip()

def jp_text(el):
    return clean_text("".join(el.xpath(".//text()")))

def to_int(v):
    try:
        return int(float(str(v).replace(",", "").replace("¥", "").replace("$", "")))
    except (TypeError, ValueError):
        return None

def parse_money(text):
    t = re.sub(r"[^\d]", "", text or "")
    return to_int(t)

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def sleep_ms(ms):
    time.sleep(ms / 1000.0)

def parse_context(raw_url):
    ctx = {"context_category": "Tools / Accessories", "work_type": "TOL", "page": 1, "raw_url": str(raw_url or "")}
    try:
        from urllib.parse import urlparse
        u = urlparse(raw_url)
        m = re.search(r"/page/(\d+)", raw_url)
        if m:
            ctx["page"] = int(m.group(1))
        m2 = re.search(r"work_type/([^/]+)", raw_url)
        if m2:
            ctx["work_type"] = unquote(m2.group(1))
    except Exception:
        pass
    return ctx

# ------------------------------------------------------------------
# list page extraction & batch ajax
# ------------------------------------------------------------------

def parse_list_page(html_bytes, page_url):
    """Returns (products, next_url, card_count)."""
    try:
        doc = lhtml.fromstring(html_bytes)
        doc.make_links_absolute(page_url)
    except Exception as e:
        raise ValueError(f"lxml parse failed: {e}") from e

    context = parse_context(page_url)
    cards = doc.xpath("//li[contains(@class,'search_result_img_box_inner') and @data-list_item_product_id]")
    if not cards:
        cards = doc.xpath("//*[@data-list_item_product_id]")
    products = []
    page_size = len(cards) or 30

    for idx, card in enumerate(cards):
        pid = (card.get("data-list_item_product_id") or "").strip()
        if not pid:
            hid = card.xpath(".//input[contains(@id,'_')]/@id")
            if hid:
                pid = hid[0].lstrip("_")
        
        title_el = next(iter(card.xpath(".//dd[contains(@class,'work_name')]//a")), None)
        if title_el is None:
            title_el = next(iter(card.xpath(".//a[contains(@href,'/product_id/')]")), None)
        title = clean_text(title_el.get("title") or jp_text(title_el)) if title_el is not None else ""
        
        jp_title = ""
        ga = card.xpath(".//div[contains(@class,'ga4_event_item')]/@data-work_name")
        if ga:
            jp_title = clean_text(ga[0])
        
        item_url = title_el.get("href", "") if title_el is not None else ""
        if item_url and not item_url.startswith("http"):
            item_url = urljoin(page_url, item_url)
        
        maker_el = next(iter(card.xpath(".//dd[contains(@class,'maker_name')]//a")), None)
        maker_name = jp_text(maker_el) if maker_el is not None else ""
        maker_url = maker_el.get("href", "") if maker_el is not None else ""
        maker_id = ""
        if maker_url:
            m = re.search(r"maker_id/([^/\.]+)", maker_url)
            if m:
                maker_id = m.group(1)
        if not maker_id:
            hid2 = card.xpath(".//input[@class='__product_attributes']/@value")
            if hid2:
                maker_id = hid2[0].split(",")[0] if hid2[0] else ""
        
        price_jpy = None
        ga_price = card.xpath(".//div[contains(@class,'ga4_event_item')]/@data-price")
        if ga_price:
            price_jpy = to_int(ga_price[0])
        if price_jpy is None:
            price_el = next(iter(card.xpath(".//*[contains(@class,'work_price_base')]")), None)
            if price_el is not None:
                price_jpy = parse_money(jp_text(price_el))
        price_display = jp_text(next(iter(card.xpath(".//*[contains(@class,'work_price')]")), None)) if card.xpath(".//*[contains(@class,'work_price')]") else ""
        
        thumb_el = next(iter(card.xpath(".//dt[contains(@class,'work_thumb')]//img/@src | .//dt[contains(@class,'work_thumb')]//source/@srcset")), None)
        thumb_url = thumb_el if isinstance(thumb_el, str) else ""
        if thumb_url and thumb_url.startswith("//"):
            thumb_url = "https:" + thumb_url
        
        rating_el = next(iter(card.xpath(".//*[contains(@class,'star_rating')]")), None)
        rating_count = to_int(jp_text(rating_el).replace("(","").replace(")","")) if rating_el is not None else None
        
        wt = "TOL"
        wt_el = card.xpath(".//div[contains(@class,'work_category')]//a/text()")
        if wt_el and "Tools" in wt_el[0]:
            wt = "TOL"
        ga_wt = card.xpath(".//div[contains(@class,'ga4_event_item')]/@data-work_type")
        if ga_wt:
            wt = ga_wt[0]
        
        position = idx

        # Heuristic font check on list card
        hay_check = (title + " " + jp_title).lower()
        is_font_candidate = any(k in hay_check for k in ["フォント", "書体", "font", "typeface", "文字"])
        if any(k in hay_check for k in ["synthesizer", "voiceroid", "voicepeak", "cevio", "a.i.voice", "歌声"]):
            is_font_candidate = False

        products.append({
            "page": context["page"],
            "position": position,
            "absolute_position": (context["page"] - 1) * page_size + idx + 1,
            "work_type": wt,
            "context_category": context["context_category"],
            "product_id": pid,
            "title": title,
            "title_jp": jp_title or title,
            "price_jpy": price_jpy if price_jpy is not None else 0,
            "official_price": price_jpy if price_jpy is not None else 0,
            "price_display": price_display,
            "maker_id": maker_id,
            "maker_name": maker_name,
            "maker_url": maker_url,
            "item_url": item_url,
            "thumb_url": thumb_url,
            "rating_count": rating_count,
            "rate_average": None,
            "review_count": None,
            "sales_count": None,
            "favorites_count": None,
            "custom_genres": [],
            "published": "",
            "is_font": is_font_candidate,
            "url": page_url,
        })

    next_url = ""
    cur_page = context["page"]
    next_el = next(iter(doc.xpath(f"//td[contains(@class,'page_no')]//a[@data-value='{cur_page+1}']")), None)
    if next_el is not None:
        next_url = next_el.get("href", "")
    else:
        cand = doc.xpath("//td[contains(@class,'page_no')]//a[contains(text(),'Next')]/@href")
        if cand:
            next_url = cand[0]
        else:
            all_links = doc.xpath("//td[contains(@class,'page_no')]//a/@href")
            for href in all_links:
                if f"/page/{cur_page+1}/" in href or f"/page/{cur_page+1}?" in href:
                    next_url = href
                    break
    if next_url and not next_url.startswith("http"):
        next_url = urljoin(page_url, next_url)

    return products, next_url, len(cards)


def fetch_product_info_batch(client, product_ids, retries=3):
    """Fetch product/info/ajax for a list of product IDs (DLsite official frontend API)."""
    if not product_ids:
        return {}
    pid_str = ",".join(product_ids)
    url = f"https://www.dlsite.com/home/product/info/ajax?product_id={pid_str}&cdn_cache=3"
    resp, err = fetch_page(client, url, retries=retries)
    if resp is None:
        return {}
    try:
        return resp.json() or {}
    except Exception:
        return {}


def apply_ajax_info(product, info):
    """Enrich product dict with AJAX API return fields."""
    if not info:
        return
    if info.get("dl_count") is not None:
        product["sales_count"] = info["dl_count"]
    if info.get("wishlist_count") is not None:
        product["favorites_count"] = info["wishlist_count"]
    if info.get("rate_count") is not None:
        product["rating_count"] = info["rate_count"]
    if info.get("rate_average_2dp") is not None:
        product["rate_average"] = info["rate_average_2dp"]
    elif info.get("rate_average") is not None:
        product["rate_average"] = info["rate_average"]
    if info.get("review_count") is not None:
        product["review_count"] = info["review_count"]
    if info.get("price") is not None:
        product["price_jpy"] = info["price"]
    if info.get("official_price") is not None:
        product["official_price"] = info["official_price"]
    if info.get("custom_genres"):
        product["custom_genres"] = info["custom_genres"]
    if info.get("regist_date") and not product.get("published"):
        product["published"] = info["regist_date"][:10]
    if info.get("work_name"):
        product["title_jp"] = info["work_name"]
        if not product.get("title"):
            product["title"] = info["work_name"]

# ------------------------------------------------------------------
# detail page extraction (HTML work_outline + description)
# ------------------------------------------------------------------

def parse_detail(html_bytes, html_text, meta):
    base = (meta or {}).get("item_url") or "https://www.dlsite.com"
    try:
        doc = lhtml.fromstring(html_bytes)
        doc.make_links_absolute(base)
    except Exception:
        doc = None

    body_text = ""
    if doc is not None:
        try:
            body_text = "\n".join(doc.xpath("//body//text()"))
        except Exception:
            body_text = html_text or ""

    title = ""
    if doc is not None:
        h1 = doc.xpath("//h1[@id='work_name' or contains(@class,'work_name')]")
        if h1:
            title = jp_text(h1[0])
        if not title:
            h1_any = doc.xpath("//h1")
            if h1_any:
                title = jp_text(h1_any[0])
        if not title:
            og = doc.xpath("//meta[@property='og:title']/@content")
            if og:
                title = clean_text(og[0])
    if not title:
        title = (meta or {}).get("title", "")

    description = ""
    if doc is not None:
        wp = doc.xpath("//*[contains(@class,'work_parts_container')]")
        if wp:
            description = clean_text("".join(wp[0].xpath(".//text()")))
        if not description:
            for sel in ("#work_outline", ".work_outline", "#main_inner"):
                els = doc.xpath(f"//*[@id='{sel.strip('#.')}' or contains(@class,'{sel.strip('#.')}')]")
                if els:
                    description = clean_text("".join(els[0].xpath(".//text()")))
                    break
        if not description:
            m = doc.xpath("//meta[@name='description']/@content | //meta[@property='og:description']/@content")
            if m:
                description = clean_text(m[0])

    outline = {}
    if doc is not None:
        rows = doc.xpath("//table[@id='work_outline']//tr")
        for tr in rows:
            th = jp_text(next(iter(tr.xpath("./th")), None))
            td_el = next(iter(tr.xpath("./td")), None)
            if not th or td_el is None:
                continue
            td_text = jp_text(td_el)
            td_html = lhtml.tostring(td_el, encoding="unicode") if td_el is not None else ""
            outline[th] = {"text": td_text, "html": td_html, "el": td_el}

    def _get_outline(keys):
        for k in keys:
            if k in outline:
                return outline[k]
        return None

    rel_date_info = _get_outline(["販売日", "発売日", "Release date"])
    published = ""
    if rel_date_info:
        txt = rel_date_info["text"]
        m = re.search(r"(\d{4})[年\/\-.](\d{1,2})[月\/\-.](\d{1,2})", txt)
        if m:
            y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
            published = f"{y:04d}-{mo:02d}-{d:02d}"
        else:
            m2 = re.search(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[\/\s]+(\d{1,2})[\/,\s]+(\d{4})", txt, re.I)
            if m2:
                mon_map = {k:i for i,k in enumerate(["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"],1)}
                mon = mon_map[m2.group(1)[:3].title()]
                d = int(m2.group(2)); y = int(m2.group(3))
                published = f"{y:04d}-{mon:02d}-{d:02d}"
    if not published and meta and meta.get("published"):
        published = meta["published"]

    genre = ""
    genre_info = _get_outline(["ジャンル", "Genre"])
    if genre_info:
        el = genre_info["el"]
        links = el.xpath(".//a/text()") if el is not None else []
        if links:
            genre = clean_text(" ".join(links))
        else:
            genre = clean_text(genre_info["text"])

    file_format = ""
    fmt_info = _get_outline(["ファイル形式", "File format"])
    if fmt_info:
        file_format = clean_text(fmt_info["text"])
        add = fmt_info["html"]
        if "トゥルータイプ" in add or "フォント" in add or "ET1" in add or "OTF" in add or "TTF" in add:
            extra = clean_text(re.sub(r"<[^>]+>", " ", add))
            if extra not in file_format:
                file_format += " / " + extra

    size_info = _get_outline(["ファイル容量", "File size"])
    file_size = clean_text(size_info["text"]) if size_info else ""

    prod_fmt_info = _get_outline(["作品形式", "Product format"])
    product_format = clean_text(prod_fmt_info["text"]) if prod_fmt_info else ""

    lang_info = _get_outline(["対応言語", "Supported languages"])
    language = clean_text(lang_info["text"]) if lang_info else ""

    maker_info = _get_outline(["作者", "サークル名", "ブランド名", "Author", "Circle", "Maker"])
    maker_from_outline = clean_text(maker_info["text"]) if maker_info else ""

    # Price fallback
    price_jpy = (meta or {}).get("price_jpy")
    if price_jpy is None and doc is not None:
        price_els = doc.xpath("//*[contains(@class,'price') or contains(@class,'work_price')]//text()")
        for t in price_els:
            if "JPY" in t or "円" in t or "¥" in t:
                v = parse_money(t)
                if v and 0 < v < 5000000:
                    price_jpy = v
                    break

    # Font determination rule
    is_font = False
    fmt_lower = (file_format or "").lower()
    title_lower = (title or "").lower()
    desc_lower = (description or "").lower()

    # Positive font signals:
    # 1. File format explicitly contains TrueType / OpenType / Font / ET1 font mention
    has_font_format = any(k in fmt_lower for k in ["トゥルータイプ", "フォント", "書体", "ttf", "otf", "ttc"])
    # 2. Title explicitly contains font / typeface / typeface keywords
    has_font_title = any(k in title_lower for k in ["フォント", "書体", "font", "typeface"])

    if has_font_format or has_font_title:
        is_font = True
    elif any(k in desc_lower for k in ["フォント", "書体", "ttf", "otf", "ttc"]):
        # Description mention is only a font if format is NOT an application or plugin
        if not any(k in fmt_lower for k in ["アプリケーション", "プラグイン", "ゲーム", "exe", "apk"]):
            is_font = True

    # Negative exclusion signals (voice synths, game engines, development tools):
    if any(k in (product_format + " " + title).lower() for k in [
        "synthesizer", "voicepeak", "voiceroid", "cevio", "a.i.voice", "歌声",
        "ティラノビルダー", "tyranobuilder", "srpg studio", "エンジン", "制作ツール"
    ]):
        if not has_font_format:
            is_font = False

    return {
        "detailFetched": True,
        "detailFetchedAt": now_iso(),
        "detailTitle": title,
        "description": description,
        "descriptionLength": len(description),
        "genre": genre,
        "file_format": file_format,
        "file_size": file_size,
        "product_format": product_format,
        "published": published,
        "language": language,
        "maker_from_outline": maker_from_outline,
        "price_jpy_detail": price_jpy,
        "is_font": is_font,
    }

# ------------------------------------------------------------------
# CSV / JSONL serialization
# ------------------------------------------------------------------

def flatten(rec):
    cg = rec.get("custom_genres", [])
    cg_str = "|".join(cg) if isinstance(cg, list) else str(cg or "")
    return {
        "crawl_date": rec.get("crawl_date", date.today().isoformat()),
        "work_type": rec.get("work_type", "TOL"),
        "context_category": rec.get("context_category", "Tools / Accessories"),
        "page": rec.get("page", ""),
        "position": rec.get("position", ""),
        "absolute_position": rec.get("absolute_position", ""),
        "product_id": rec.get("product_id", ""),
        "title": rec.get("detailTitle") or rec.get("title", ""),
        "title_jp": rec.get("title_jp", ""),
        "price_jpy": rec.get("price_jpy") if rec.get("price_jpy") is not None else rec.get("price_jpy_detail", ""),
        "official_price": rec.get("official_price", ""),
        "price_display": rec.get("price_display", ""),
        "maker_id": rec.get("maker_id", ""),
        "maker_name": rec.get("maker_from_outline") or rec.get("maker_name", ""),
        "maker_url": rec.get("maker_url", ""),
        "item_url": rec.get("item_url", ""),
        "thumb_url": rec.get("thumb_url", ""),
        "detail_fetched": "yes" if rec.get("detailFetched") else "no",
        "description": rec.get("description", ""),
        "description_length": rec.get("descriptionLength", ""),
        "genre": rec.get("genre", ""),
        "file_format": rec.get("file_format", ""),
        "file_size": rec.get("file_size", ""),
        "published": rec.get("published", ""),
        "sales_count": rec.get("sales_count", "") if rec.get("sales_count") is not None else "",
        "favorites_count": rec.get("favorites_count", "") if rec.get("favorites_count") is not None else "",
        "rating_count": rec.get("rating_count", "") if rec.get("rating_count") is not None else "",
        "rate_average": rec.get("rate_average", "") if rec.get("rate_average") is not None else "",
        "review_count": rec.get("review_count", "") if rec.get("review_count") is not None else "",
        "language": rec.get("language", ""),
        "is_font": "yes" if rec.get("is_font") else "no",
        "custom_genres": cg_str,
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
    return "\n".join(json.dumps({**rec, "extractor_version": EXTRACTOR_VERSION}, ensure_ascii=False) for rec in records)

# ------------------------------------------------------------------
# HTTP client & helpers
# ------------------------------------------------------------------

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

# ------------------------------------------------------------------
# Crawl Orchestration
# ------------------------------------------------------------------

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
        "ajax_phase_done": False,
        "errors": [],
        "log": [],
        "stop": False,
    }

def save_state(out_dir, state):
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp = out_dir / "crawl-state.json.tmp"
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(out_dir / "crawl-state.json")

def run(client, args, state, out_dir):
    log = state["log"]
    def add_log(msg):
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {msg}"
        log.append(line)
        print(line, flush=True)

    # 1. LIST PHASE
    should_run_list = not state.get("list_phase_done") or (bool(state.get("next_url")) and not args.max_pages)
    if should_run_list:
        state["list_phase_done"] = False
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
            add_log(f"page {state['pages_done'] + 1}: {url[:120]}")
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
            
            # Fetch batch AJAX for this page's cards immediately
            page_pids = [p["product_id"] for p in products if p.get("product_id")]
            if page_pids:
                ajax_map = fetch_product_info_batch(client, page_pids, retries=args.retries)
                for p in products:
                    if p["product_id"] in ajax_map:
                        apply_ajax_info(p, ajax_map[p["product_id"]])

            seen = {p["product_id"] + "|" + p["item_url"] for p in state["products"]}
            added = 0
            for p in products:
                key = p["product_id"] + "|" + p["item_url"]
                if key in seen:
                    continue
                seen.add(key)
                p["crawl_date"] = date.today().isoformat()
                state["products"].append(p)
                added += 1
            state["pages_done"] += 1
            state["next_url"] = next_url
            state["last_url"] = url
            add_log(f"  {card_count} cards, +{added} new (total {len(state['products'])})")
            save_state(out_dir, state)
            try:
                write_outputs(out_dir, state, args)
            except Exception:
                pass
            if not next_url:
                add_log("no more pages; list phase complete")
                break
            url = next_url
            sleep_ms(args.list_delay + random.randint(0, 300))
        state["list_phase_done"] = True
        save_state(out_dir, state)

    # 2. AJAX BACKFILL PHASE (if any products still lack dl_count/wishlist_count)
    pending_ajax = [p for p in state["products"] if p.get("sales_count") is None and p.get("product_id")]
    if pending_ajax:
        add_log(f"ajax backfill phase: {len(pending_ajax)} items")
        chunk_size = 30
        for i in range(0, len(pending_ajax), chunk_size):
            chunk = pending_ajax[i:i + chunk_size]
            pids = [p["product_id"] for p in chunk]
            ajax_map = fetch_product_info_batch(client, pids, retries=args.retries)
            for p in chunk:
                if p["product_id"] in ajax_map:
                    apply_ajax_info(p, ajax_map[p["product_id"]])
            add_log(f"  ajax progress: {min(i + chunk_size, len(pending_ajax))}/{len(pending_ajax)}")
            sleep_ms(400 + random.randint(0, 200))
        save_state(out_dir, state)

    # 3. DETAIL PHASE (HTML work_outline + descriptions)
    detail_limit = args.detail_limit if args.detail_limit is not None else 300
    if detail_limit != 0:
        products = state["products"]
        def priority_key(p):
            is_f = 1 if p.get("is_font") else 0
            sales = p.get("sales_count") or 0
            favs = p.get("favorites_count") or 0
            pos = p.get("absolute_position") or 9999
            return (-is_f, -sales, -favs, pos)

        queue = sorted([p for p in products if p.get("item_url")], key=priority_key)[:detail_limit]
        pending = [p for p in queue if p["product_id"] not in state["details"]]
        add_log(f"detail phase: {len(pending)} items to fetch (limit {detail_limit}, already {len(state['details'])})")
        if not pending:
            add_log("nothing left to fetch")
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
                    if job["product_id"] in state["details"]:
                        continue
                    detail, err = fetch_item_detail(client, job, retries=args.retries)
                    with lock:
                        if detail is not None:
                            state["details"][job["product_id"]] = detail
                            fresh = next((p for p in state["products"] if p["product_id"] == job["product_id"]), None)
                            if fresh is not None:
                                fresh.update(detail)
                        else:
                            state["errors"].append({"at": now_iso(), "product_id": job["product_id"], "msg": "detail fetch failed: " + (err or "unknown")})
                        done = len(state["details"])
                        if done and (done % 10 == 0 or done == len(queue)):
                            save_state(out_dir, state)
                            try:
                                write_outputs(out_dir, state, args)
                            except Exception:
                                pass
                            add_log(f"  details: {done}/{len(queue)} (checkpoint saved to disk)")
                    sleep_ms(args.detail_delay + random.randint(0, 400))

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
        detail = parse_detail(
            resp.content, resp.text,
            {
                "product_id": job["product_id"],
                "item_url": job["item_url"],
                "title": job.get("title"),
                "price_jpy": job.get("price_jpy"),
                "published": job.get("published"),
            }
        )
        return detail, None
    except Exception as e:
        return None, f"parse: {e}"

MANIFEST_FILE = "collector-manifest.md"

def write_outputs(out_dir, state, args):
    records = []
    for p in state["products"]:
        d = state["details"].get(p["product_id"])
        merged = {**p, **(d or {})}
        merged.setdefault("detailFetched", False)
        if d:
            merged["detailFetched"] = True
        records.append(merged)
    base = "tools-accessories-items"
    
    csv_tmp = out_dir / f"{base}.csv.tmp"
    csv_tmp.write_text(build_csv(records), encoding="utf-8")
    csv_tmp.replace(out_dir / f"{base}.csv")

    jsonl_tmp = out_dir / f"{base}.jsonl.tmp"
    jsonl_tmp.write_text(build_jsonl(records), encoding="utf-8")
    jsonl_tmp.replace(out_dir / f"{base}.jsonl")

    lines = []
    def out(s=""):
        lines.append(s)
    out(f"# DLsite Tools/Accessories Collector Manifest — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    out()
    out(f"- Start URL: `{args.start}`")
    out(f"- Collector: {EXTRACTOR_VERSION}")
    out(f"- Status: {state['status']}")
    out(f"- Pages walked: {state['pages_done']}")
    out(f"- Unique products: {len(state['products'])}")
    out(f"- Products with sales metrics (dl_count): {sum(1 for r in records if r.get('sales_count') is not None)}")
    out(f"- Detail pages fetched: {len(state['details'])} (limit: {args.detail_limit if args.detail_limit is not None else 300})")
    out(f"- Fonts filtered (is_font=yes): {sum(1 for r in records if r.get('is_font'))}")
    out(f"- Started: {state.get('started_at')}  Finished: {state.get('finished_at', '-')}")
    out()
    out("## Errors")
    out()
    if state["errors"]:
        for e in state["errors"][-40:]:
            out(f"- {e.get('at')} {e.get('product_id') or e.get('url')}: {e['msg']}")
    else:
        out("- none")
    out()
    out("## Page map")
    out()
    for i in range(1, state["pages_done"] + 1):
        out(f"- page {i}: recorded")
    out()
    out("## Notes")
    out("- Category is ツール/アクセサリ (TOL), 55 pages x30 at crawl. Voice synth + game engines + fonts mixed; is_font flag marks true fonts via File format / description.")
    out("- Sales (dl_count) and Favorites (wishlist_count) fetched from official DLsite AJAX API (/home/product/info/ajax).")
    out("- Join with font research and analyze with bin/build_dlsite_db.py then bin/analyze_dlsite_collection.py")
    manifest_tmp = out_dir / f"{MANIFEST_FILE}.tmp"
    manifest_tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    manifest_tmp.replace(out_dir / MANIFEST_FILE)

def main():
    ap = argparse.ArgumentParser(description="DLsite Tools/Accessories collector")
    ap.add_argument("--start", default=DEFAULT_START, help="DLsite TOL list URL")
    ap.add_argument("--out", default=None, help="Output dir (default: outputs/research/dlsite-live-collector/{date}/tools-accessories)")
    ap.add_argument("--max-pages", type=int, default=0, help="0 = unlimited (55)")
    ap.add_argument("--max-items", type=int, default=0, help="0 = unlimited")
    ap.add_argument("--detail-limit", type=int, default=300, help="Fetch detail pages for top-N (0 = none)")
    ap.add_argument("--concurrency", type=int, default=2, help="Detail fetch concurrency (1-3, DLsite soft-blocks burst)")
    ap.add_argument("--list-delay", type=int, default=800, help="Delay ms between list pages")
    ap.add_argument("--detail-delay", type=int, default=1200, help="Delay ms between detail fetches (per worker)")
    ap.add_argument("--retries", type=int, default=3, help="Fetch retries")
    ap.add_argument("--timeout", type=float, default=25.0, help="HTTP timeout seconds")
    ap.add_argument("--resume", action="store_true", help="Resume a stopped run in --out")
    args = ap.parse_args()
    if args.detail_limit is not None and args.detail_limit < 0:
        ap.error("--detail-limit must be >= 0 (0 = all)")
    out_dir = Path(args.out) if args.out else Path(f"outputs/research/dlsite-live-collector/{date.today().isoformat()}/tools-accessories")
    out_dir.mkdir(parents=True, exist_ok=True)
    state_file = out_dir / "crawl-state.json"
    if state_file.exists():
        if args.resume:
            state = json.loads(state_file.read_text(encoding="utf-8"))
            print(f"Resuming run at {out_dir} ({state['pages_done']} pages done, {len(state['products'])} products, {len(state['details'])} details)")
        else:
            import time as _t
            bak = out_dir / f"crawl-state-{int(_t.time())}.json.bak"
            state_file.rename(bak)
            print(f"Existing run moved aside: {bak.name}. Starting fresh.")
            state = fresh_state(args.start)
    else:
        if args.resume:
            print("No existing run to resume; starting fresh.")
        state = fresh_state(args.start)
    client = make_client(args.timeout)
    exit_code = 0
    try:
        run(client, args, state, out_dir)
    except KeyboardInterrupt:
        state.setdefault("status", "stopped")
        state["stop"] = True
        state["finished_at"] = now_iso()
        save_state(out_dir, state)
        try:
            write_outputs(out_dir, state, args)
        except Exception:
            pass
        sig_label = "SIGTERM" if _sig_received == signal.SIGTERM else "SIGINT (Ctrl+C)"
        print(f"\nInterrupted via {sig_label}. Progress safely saved — run with --resume to continue.")
        exit_code = 143 if _sig_received == signal.SIGTERM else 130
    except Exception as e:
        state.setdefault("status", "error")
        state["stop"] = True
        state["finished_at"] = now_iso()
        state["errors"].append({"at": now_iso(), "msg": f"Unhandled error: {e}"})
        save_state(out_dir, state)
        try:
            write_outputs(out_dir, state, args)
        except Exception:
            pass
        print(f"\nError encountered: {e}. Progress safely saved — run with --resume to continue.")
        exit_code = 1
    finally:
        try:
            write_outputs(out_dir, state, args)
            print(f"Outputs saved to {out_dir}")
        except Exception as e:
            print(f"Warning: could not write outputs: {e}")
        client.close()

    if state.get("status") != "done" and exit_code == 0:
        exit_code = 1

    return exit_code

if __name__ == "__main__":
    raise SystemExit(main())
