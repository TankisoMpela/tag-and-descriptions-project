import { NextResponse } from 'next/server'
import { isAdmin, unauthorized } from '@/lib/auth'

const USER_AGENT =
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ' +
  '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'

function decodeEntities(str: string): string {
  const txt = String(str).replace(/\+/g, ' ')
  const map: Record<string, string> = {
    '&amp;': '&',
    '&lt;': '<',
    '&gt;': '>',
    '&quot;': '"',
    '&#39;': "'",
    '&apos;': "'",
    '&nbsp;': ' ',
    '&#x2F;': '/',
    '&#47;': '/',
    '&yen;': '¥',
  }
  let out = txt.replace(
    /&(?:amp|lt|gt|quot|#39|apos|nbsp|#x2F|#47|yen);/gi,
    (m) => map[m.toLowerCase()] ?? m
  )
  out = out.replace(/&#(\d+);/g, (_, n) => String.fromCodePoint(Number(n)))
  out = out.replace(/&#x([0-9a-f]+);/gi, (_, h) => String.fromCodePoint(parseInt(h, 16)))
  return out
}

function escapeRegExp(str: string): string {
  return String(str).replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function extractMeta(html: string, key: string): string | null {
  const re = new RegExp(
    `<meta[^>]+(?:property=["']${key}["']|name=["']${key}["']|itemprop=["']${key}["'])[^>]*>`,
    'i'
  )
  const tag = html.match(re)
  if (!tag) return null
  const content = tag[0].match(/content=["']([^"']*)["']/i)
  return content ? content[1] : null
}

function extractTitleTag(html: string): string | null {
  const m = html.match(/<title[^>]*>([\s\S]*?)<\/title>/i)
  return m ? m[1].trim() : null
}

function extractJsonLdProduct(html: string): Record<string, unknown> | null {
  const blocks = html.matchAll(
    /<script[^>]*type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi
  )
  for (const block of blocks) {
    let data: unknown
    try {
      data = JSON.parse(block[1])
    } catch {
      continue
    }
    const items = Array.isArray(data) ? data : [data]
    for (const item of items) {
      if (!item || typeof item !== 'object') continue
      const obj = item as Record<string, unknown>
      const type = String(obj['@type'] || '')
      if (type.toLowerCase().includes('product') && obj.name) return obj
      const main = obj.mainEntity as Record<string, unknown> | undefined
      if (main && main.name && String(main['@type'] || '').toLowerCase().includes('product')) {
        return main
      }
    }
  }
  return null
}

function toAbsolute(url: string | null | undefined, base: string): string | null {
  if (!url) return null
  if (url.startsWith('//')) return `https:${url}`
  if (url.startsWith('http://') || url.startsWith('https://')) return url
  try {
    return new URL(url, base).toString()
  } catch {
    return null
  }
}

function cleanName(raw: string | null, brandSuffix: string | null): string | null {
  if (!raw) return null
  let name = decodeEntities(raw).trim()
  name = name.replace(/\s*-\s*BOOTH\s*$/i, '').trim()
  if (brandSuffix) {
    name = name
      .replace(new RegExp(`\\s*-\\s*${escapeRegExp(brandSuffix)}\\s*$`, 'i'), '')
      .trim()
  }
  if (!name) return null
  return name.slice(0, 140)
}

function stripHtml(html: string): string {
  return decodeEntities(html.replace(/<[^>]*>/g, ' '))
    .replace(/\s+/g, ' ')
    .trim()
}

function extractPrice(
  ld: Record<string, unknown> | null,
  html: string
): string | null {
  if (ld) {
    const offers = ld.offers
    const list = Array.isArray(offers) ? offers : offers ? [offers] : []
    for (const offer of list) {
      if (!offer || typeof offer !== 'object') continue
      const o = offer as Record<string, unknown>
      const price = o.price ?? o.lowPrice
      if (price !== undefined && price !== null && String(price).length > 0) {
        const currency = String(o.priceCurrency || 'JPY')
        const amount = String(price)
        if (currency === 'JPY' || currency === '') return `¥${amount}`
        return `${amount} ${currency}`
      }
    }
  }
  const amount =
    extractMeta(html, 'product:price:amount') ||
    html.match(/itemprop=["']price["'][^>]*content=["']([^"']+)["']/i)?.[1] ||
    html.match(/"price"\s*:\s*"?([0-9]+(?:\.[0-9]+)?)"?/)?.[1]
  if (!amount) return null
  const currency = extractMeta(html, 'product:price:currency') || 'JPY'
  if (currency === 'JPY') return `¥${amount}`
  return `${amount} ${currency}`
}

function extractDescription(
  ld: Record<string, unknown> | null,
  html: string
): string | null {
  if (ld && typeof ld.description === 'string' && ld.description.trim()) {
    return stripHtml(ld.description).slice(0, 600)
  }
  const og = extractMeta(html, 'og:description') || extractMeta(html, 'description')
  if (og) return decodeEntities(og).replace(/\s+/g, ' ').trim().slice(0, 600)
  return null
}

export const dynamic = 'force-dynamic'

export async function POST(request: Request) {
  if (!isAdmin(request)) return unauthorized()

  let body: { url?: string }
  try {
    body = await request.json()
  } catch {
    return NextResponse.json({ error: 'Send JSON with a BOOTH url' }, { status: 400 })
  }

  const rawUrl = typeof body.url === 'string' ? body.url.trim() : ''
  if (!rawUrl) {
    return NextResponse.json({ error: 'Paste a BOOTH product URL' }, { status: 400 })
  }

  let parsed: URL
  try {
    parsed = new URL(rawUrl)
  } catch {
    return NextResponse.json({ error: 'That is not a valid URL' }, { status: 400 })
  }

  const host = parsed.hostname.toLowerCase()
  if (host !== 'booth.pm' && !host.endsWith('.booth.pm')) {
    return NextResponse.json({ error: 'That is not a BOOTH URL' }, { status: 400 })
  }

  const itemMatch = parsed.pathname.match(/\/(?:[a-z]{2}\/)?items\/(\d+)/i)
  if (!itemMatch) {
    return NextResponse.json(
      { error: 'Use a product link like https://shop.booth.pm/items/123456' },
      { status: 400 }
    )
  }
  const itemId = itemMatch[1]

  let html: string
  try {
    const res = await fetch(parsed.toString(), {
      headers: {
        'User-Agent': USER_AGENT,
        Accept: 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
      },
      cache: 'no-store',
      redirect: 'follow',
    })
    if (!res.ok) {
      return NextResponse.json(
        { error: `BOOTH returned HTTP ${res.status}. The product may be private or deleted.` },
        { status: 502 }
      )
    }
    html = await res.text()
  } catch {
    return NextResponse.json(
      { error: 'Could not reach BOOTH right now. Try again or enter details manually.' },
      { status: 502 }
    )
  }

  if (!html || html.length < 500) {
    return NextResponse.json(
      { error: 'BOOTH returned an empty page (possible bot check). Enter details manually.' },
      { status: 502 }
    )
  }

  const ld = extractJsonLdProduct(html)
  const brandSuffix =
    ld && ld.brand && typeof ld.brand === 'object'
      ? ((ld.brand as Record<string, unknown>).name as string | undefined) || null
      : null

  let name: string | null = null
  if (ld && typeof ld.name === 'string') name = cleanName(ld.name, null)
  if (!name) {
    const ogTitle = extractMeta(html, 'og:title')
    if (ogTitle) name = cleanName(ogTitle, brandSuffix)
  }
  if (!name) name = cleanName(extractTitleTag(html), brandSuffix)

  let thumb =
    extractMeta(html, 'og:image') || extractMeta(html, 'twitter:image')
  if (!thumb && ld) {
    const img = ld.image
    if (Array.isArray(img) && typeof img[0] === 'string') thumb = img[0]
    else if (typeof img === 'string') thumb = img
  }
  thumb = toAbsolute(thumb, parsed.toString())

  const price = extractPrice(ld, html)
  const description = extractDescription(ld, html)

  if (!name && !thumb) {
    return NextResponse.json(
      { error: 'Could not read product metadata from BOOTH. Enter details manually.' },
      { status: 502 }
    )
  }

  return NextResponse.json({
    ok: true,
    boothProductId: itemId,
    boothName: name || 'Unknown product',
    boothThumbnail: thumb,
    boothPrice: price,
    boothDescription: description,
    boothUrl: parsed.toString(),
  })
}
