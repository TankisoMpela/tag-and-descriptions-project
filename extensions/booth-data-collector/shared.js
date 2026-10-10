/* ===========================================================
 * BOOTH Data Collector — shared.js
 * Pure functions shared by content script and background worker.
 * Loaded first in the content script and via importScripts() in
 * the service worker. Everything is attached to globalThis.
 * =========================================================== */

(function () {
  'use strict';

  const EXTRACTOR_VERSION = '1.0.0';

  /* ---------- small utilities ---------- */

  function absUrl(href, base) {
    try {
      return new URL(href, base).href;
    } catch (e) {
      return String(href || '');
    }
  }

  function cleanText(str) {
    return String(str == null ? '' : str).replace(/\s+/g, ' ').trim();
  }

  // Parse "0 JPY", "¥1,000", "1.200" etc into an int (null if failed)
  function parseMoney(text) {
    if (text == null) return null;
    const t = String(text).replace(/[^\d]/g, '');
    if (!t) return null;
    const v = parseInt(t, 10);
    return isNaN(v) ? null : v;
  }

  function parseLikes(text) {
    if (text == null) return 0;
    const s = String(text).replace(/,/g, '').replace(/[^\d]/g, '');
    const v = parseInt(s, 10);
    return isNaN(v) ? 0 : v;
  }

  function uniq(arr) {
    return Array.from(new Set(arr));
  }

  // BOOTH item pages often render tags lazily from embedded state, so the
  // DOM selectors may find nothing. The exact-tag route scheme (same one the
  // frozen tag bank uses) is `?tags%5B%5D={url-encoded-tag}`, and BOOTH embeds
  // those hrefs in <script>/meta/state even when the visible tag chips are
  // hydrated client-side. Recovering them from the raw HTML text is a reliable
  // last-resort tag source.
  function tagsFromRawHtml(text) {
    const seen = [];
    const patterns = [
      /tags%5B%5D=([^&"'\s<>]+)/gi,
      /tags%5B\d+%5D=([^&"'\s<>]+)/gi,
      /tags\[\]=([^&"'\s<>]+)/gi
    ];
    for (const re of patterns) {
      let m;
      while ((m = re.exec(text || '')) !== null) {
        let t;
        try {
          t = cleanText(decodeURIComponent(m[1]));
        } catch (e) {
          t = cleanText(m[1]);
        }
        if (!t || t.length > 60) continue;
        if (!seen.includes(t)) seen.push(t);
      }
    }
    return seen;
  }

  function todayStamp() {
    return new Date().toISOString().slice(0, 10);
  }

  function nowIso() {
    return new Date().toISOString();
  }

  /* ---------- context: parse tag/category/sort/page from a BOOTH URL ---------- */

  // Recognise BOOTH browse / search / tag URLs and return:
  // { contextTag, contextCategory, sortMode, page } + rawUrl
  function parseContext(rawUrl) {
    const ctx = {
      contextTag: '',
      contextCategory: '',
      categoryPath: '',
      sortMode: 'default',
      page: 1,
      rawUrl: String(rawUrl || '')
    };
    let url;
    try {
      url = new URL(rawUrl);
    } catch (e) {
      return ctx;
    }
    const sp = url.searchParams;
    const pageRaw = sp.get('page');
    const p = parseInt(pageRaw, 10);
    ctx.page = isNaN(p) || p < 1 ? 1 : p;

    const sort = sp.get('sort') || '';
    if (sort) ctx.sortMode = sort;
    else ctx.sortMode = 'default';

    const tags = sp.getAll('tags[]').length ? sp.getAll('tags[]') : sp.getAll('tags');
    if (tags.length) {
      ctx.contextTag = uniq(tags.filter(Boolean)).join(' | ');
    }

    // Browse path: /ja/browse/フォント・書体 or /en/browse/Fonts
    const m = url.pathname.match(/\/browse\/([^/]+)/);
    if (m) {
      const seg = decodeURIComponent(m[1]);
      ctx.categoryPath = seg;
      ctx.contextCategory = seg;
    } else {
      const cat = sp.get('category');
      if (cat) ctx.contextCategory = cat;
    }
    return ctx;
  }

  /* ---------- list page extraction ---------- */

  // Returns { products, nextUrl, context, cardCount, pagePerPage }
  function extractList(doc, rawUrl) {
    const context = parseContext(rawUrl);
    const cards = Array.from(doc.querySelectorAll('li.item-card'));

    const products = cards.map((el, idx) => {
      const d = el.dataset || {};
      const priceEl = el.querySelector('.price.text-primary400, .price');
      const likesEl = el.querySelector('.l-item-card-favorite .typography-14, .l-item-card-favorite [class*="typography"]');
      const titleEl = el.querySelector('.item-card__title a, a.item-card__title-anchor');
      const shopEl = el.querySelector('a.item-card__shop-name-anchor');
      const shopNameEl = el.querySelector('.item-card__shop-name');
      const imgEls = el.querySelectorAll('.item-card__thumbnail-images a, .item-card__thumbnail a');

      const page = context.page;
      const position = (() => {
        const pos = parseInt(d.productPosition, 10);
        return isNaN(pos) ? idx : pos;
      })();

      return {
        page: page,
        position: position,
        absolutePosition: (page - 1) * cards.length + idx + 1, // best-effort global rank within the crawl
        sortMode: context.sortMode,
        contextTag: context.contextTag,
        contextCategory: context.contextCategory,
        itemId: d.productId || '',
        title: cleanText(el.querySelector('.item-card__title') ? el.querySelector('.item-card__title').textContent : (titleEl ? titleEl.textContent : '')),
        priceJpy: (() => {
          const v = parseMoney(priceEl ? priceEl.textContent : null);
          return v == null ? (parseMoney(d.productPrice) || 0) : v;
        })(),
        rawPrice: d.productPrice || '',
        likes: parseLikes(likesEl ? likesEl.textContent : ''),
        brand: d.productBrand || '',
        shopName: cleanText(shopNameEl ? shopNameEl.textContent : ''),
        shopUrl: shopEl ? absUrl(shopEl.href, rawUrl) : '',
        itemUrl: titleEl ? absUrl(titleEl.href, rawUrl) : '',
        cardImageCount: imgEls.length,
        categoryId: d.productCategory || '',
        url: String(rawUrl || '')
      };
    });

    const next = doc.querySelector('a[rel="next"]');
    const nextUrl = next ? absUrl(next.href, rawUrl) : '';

    return {
      products: products,
      nextUrl: nextUrl,
      context: context,
      cardCount: cards.length
    };
  }

  /* ---------- item detail page extraction ---------- */

  function parseItemDetail(htmlText, meta) {
    // meta: { itemId, itemUrl, sourceContext }
    const doc = new DOMParser().parseFromString(htmlText, 'text/html');
    const base = (meta && meta.itemUrl) || 'https://booth.pm';

    // Title
    let title = '';
    const h1 = doc.querySelector('h1');
    if (h1) title = cleanText(h1.textContent);
    if (!title) title = cleanText((doc.querySelector('meta[property="og:title"]') || {}).content || '');
    if (!title) title = (meta && meta.title) || '';

    // Description
    let description = '';
    let descSource = '';
    const descSelectors = [
      '.item-description',
      '.js-item-description',
      '#item-description',
      '.box-description',
      '.item_description',
      '.item-description__body'
    ];
    for (const sel of descSelectors) {
      const el = doc.querySelector(sel);
      if (el && cleanText(el.textContent)) {
        description = cleanText(el.textContent);
        descSource = sel;
        break;
      }
    }
    if (!description) {
      const metaDesc = doc.querySelector('meta[name="description"]');
      if (metaDesc && (metaDesc.content || '').trim()) {
        description = cleanText(metaDesc.content);
        descSource = 'meta[name=description]';
      }
    }
    if (!description) {
      const ogDesc = doc.querySelector('meta[property="og:description"], meta[name="twitter:description"]');
      if (ogDesc && (ogDesc.content || '').trim()) {
        description = cleanText(ogDesc.content);
        descSource = (ogDesc.getAttribute('property') || ogDesc.getAttribute('name')) + '';
      }
    }

    // Tags
    let tags = [];
    let tagSource = '';
    const tagSelectors = [
      '.item-tag-list a',
      '.tags a',
      '.tag-list a',
      '.item-tag a',
      '.nav-tags a',
      'a[href*="tags%5B%5D"], a[href*="tags%5B0%5D"]'
    ];
    for (const sel of tagSelectors) {
      const els = Array.from(doc.querySelectorAll(sel));
      const found = uniq(els.map((a) => cleanText(a.textContent)).filter(Boolean));
      if (found.length) {
        tags = found;
        tagSource = sel;
        break;
      }
    }
    if (!tags.length) {
      const kw = doc.querySelector('meta[name="keywords"]');
      if (kw && (kw.content || '').trim()) {
        tags = uniq(kw.content.split(/[,、]/).map((s) => cleanText(s)).filter(Boolean));
        tagSource = 'meta[name=keywords]';
      }
    }
    if (!tags.length) {
      const rawTags = tagsFromRawHtml(htmlText);
      if (rawTags.length) {
        tags = rawTags;
        tagSource = 'embedded-href (tags[] route decode)';
      }
    }

    // Prices & variants
    const bodyText = doc.body ? doc.body.innerText : '';
    const priceMatches = Array.from(bodyText.matchAll(/[,¥￥]?\s*(\d[\d,.]*)\s*(?:円|jpy|yen)?/gi))
      .map((m) => parseMoney(m[0]))
      .filter((v) => v !== null && v > 0);

    const variants = [];
    const variantRe = /Variant\s*name\s*[:：]?\s*[`'"]?([^`'"\n]+)/g;
    let vm;
    let variantPrices = priceMatches.slice();
    while ((vm = variantRe.exec(bodyText)) !== null) {
      const name = cleanText(vm[1]);
      if (!name) continue;
      // look ahead for nearest price after this match
      const after = bodyText.slice(vm.index + vm[0].length, vm.index + vm[0].length + 240);
      const am = after.match(/[,¥￥]?\s*(\d[\d,.]*)\s*(?:円|jpy|yen)?/i);
      const price = am ? parseMoney(am[0]) : null;
      variants.push({ name: name, priceJpy: price });
    }
    if (!variants.length) {
      // fallback: single price product
      if (priceMatches.length && meta && meta.priceJpy != null) {
        variants.push({ name: 'single', priceJpy: meta.priceJpy });
      }
    }

    const prices = priceMatches.length ? priceMatches : (meta && meta.priceJpy != null ? [meta.priceJpy] : []);
    const priceMin = prices.length ? Math.min.apply(null, prices) : null;
    const priceMax = prices.length ? Math.max.apply(null, prices) : null;

    // Formats from description text
    const fmtPattern = /\b(OTF|TTF|WOFF2?|OPS?|ZIP)\b/g;
    const formats = uniq(Array.from((description + ' ' + bodyText).matchAll(fmtPattern)).map((m) => m[0].toUpperCase()));

    // Image count
    let imageCount = 0;
    const imgSelectors = [
      '.js-item-image-list img',
      '.item-image-list img',
      '.swiper-wrapper img',
      '.thumbnail-list img',
      '[class*="item-image"] img',
      '.images img'
    ];
    for (const sel of imgSelectors) {
      const n = doc.querySelectorAll(sel).length;
      if (n) { imageCount = n; break; }
    }
    if (!imageCount) imageCount = doc.querySelectorAll('img[data-original], .js-thumbnail-image').length;
    if (!imageCount) imageCount = doc.querySelectorAll('img').length;

    // Published date
    let published = '';
    const pubMeta = doc.querySelector('meta[property="article:published_time"]');
    if (pubMeta && pubMeta.content) published = pubMeta.content;
    if (!published) {
      const dm = bodyText.match(/(?:登録|公開|投稿)[：:]?\s*(\d{4})[年\/\-.](\d{1,2})[月\/\-.](\d{0,2})?/);
      if (dm) published = dm.slice(1).filter(Boolean).join('-');
    }
    if (!published) {
      const t = doc.querySelector('time[datetime]');
      if (t && t.getAttribute('datetime')) published = t.getAttribute('datetime');
    }

    // Item like count
    let likeCountItem = null;
    const likeEl = doc.querySelector('.js-item-like-count, .l-item-favorite .typography-14, [class*="like-count"]');
    if (likeEl) likeCountItem = parseLikes(likeEl.textContent);

    // Category breadcrumb
    const crumbs = Array.from(doc.querySelectorAll('ol.breadcrumb a[href*="/browse/"], .breadcrumb a[href*="/browse/"]'))
      .map((a) => cleanText(a.textContent)).filter(Boolean);

    return {
      detailFetched: true,
      detailFetchedAt: nowIso(),
      detailTitle: title,
      description: description,
      descriptionLength: description.length,
      tags: tags,
      tagCount: tags.length,
      tagSource: tagSource,
      variants: variants,
      variantString: variants.map((v) => `${v.name}:${v.priceJpy == null ? '?' : '¥' + v.priceJpy}`).join(' | '),
      priceMin: priceMin,
      priceMax: priceMax,
      formats: formats,
      formatString: formats.join(' '),
      published: published,
      likeCountItem: likeCountItem,
      imageCountItem: imageCount,
      categoryBreadcrumb: crumbs.join(' > ')
    };
  }

  /* ---------- exports ---------- */

  function flattenForCsv(rec) {
    // rec = list-card record merged with detail fields (rec.merged = true)
    const tags = Array.isArray(rec.tags) ? rec.tags : [];
    return {
      crawl_date: todayStamp(),
      sort_mode: rec.sortMode || '',
      context_tag: rec.contextTag || '',
      context_category: rec.contextCategory || '',
      page: rec.page,
      position: rec.position,
      absolute_position: rec.absolutePosition,
      item_id: rec.itemId,
      title: rec.title || rec.detailTitle || '',
      price_jpy: rec.priceJpy == null ? '' : rec.priceJpy,
      likes: rec.likes,
      brand: rec.brand,
      shop_name: rec.shopName,
      shop_url: rec.shopUrl,
      item_url: rec.itemUrl,
      card_image_count: rec.cardImageCount,
      detail_fetched: rec.detailFetched ? 'yes' : 'no',
      description: rec.description || '',
      description_length: rec.descriptionLength == null ? '' : rec.descriptionLength,
      tag_count: tags.length || (rec.tagCount == null ? '' : rec.tagCount),
      tags: tags.join(' | '),
      tag_source: rec.tagSource || '',
      variants: rec.variantString || '',
      price_min: rec.priceMin == null ? '' : rec.priceMin,
      price_max: rec.priceMax == null ? '' : rec.priceMax,
      formats: rec.formatString || '',
      published: rec.published || '',
      item_like_count: rec.likeCountItem == null ? '' : rec.likeCountItem,
      item_image_count: rec.imageCountItem == null ? '' : rec.imageCountItem,
      category_breadcrumb: rec.categoryBreadcrumb || '',
      extractor_version: EXTRACTOR_VERSION
    };
  }

  const CSV_HEADERS = [
    'crawl_date', 'sort_mode', 'context_tag', 'context_category', 'page', 'position',
    'absolute_position', 'item_id', 'title', 'price_jpy', 'likes', 'brand', 'shop_name',
    'shop_url', 'item_url', 'card_image_count', 'detail_fetched', 'description',
    'description_length', 'tag_count', 'tags', 'tag_source', 'variants', 'price_min',
    'price_max', 'formats', 'published', 'item_like_count', 'item_image_count',
    'category_breadcrumb', 'extractor_version'
  ];

  function csvEscape(v) {
    const s = String(v == null ? '' : v);
    return /[",\n\r]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
  }

  function buildCsv(records) {
    const rows = records.map((rec) => {
      const flat = flattenForCsv(rec);
      return CSV_HEADERS.map((h) => csvEscape(flat[h] == null ? '' : flat[h])).join(',');
    });
    return '\uFEFF' + CSV_HEADERS.join(',') + '\n' + rows.join('\n');
  }

  function buildJsonl(records) {
    return records.map((rec) => {
      const out = Object.assign({}, rec);
      out.extractor_version = EXTRACTOR_VERSION;
      return JSON.stringify(out);
    }).join('\n');
  }

  function suggestFileName(records, base) {
    const first = records[0] || {};
    const tag = (first.contextTag || first.contextCategory || 'browse').replace(/[\\/:*?"<>|]+/g, '-').slice(0, 40);
    return `${base || 'booth'}-${tag}-${todayStamp()}.${first.sortMode || 'default'}`;
  }

  globalThis.BOOTH_COLLECTOR = {
    EXTRACTOR_VERSION,
    absUrl,
    cleanText,
    parseMoney,
    parseLikes,
    uniq,
    todayStamp,
    nowIso,
    parseContext,
    extractList,
    parseItemDetail,
    tagsFromRawHtml,
    flattenForCsv,
    CSV_HEADERS,
    buildCsv,
    buildJsonl,
    suggestFileName
  };
})();