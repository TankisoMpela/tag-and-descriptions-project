import { NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'
import { isAdmin, unauthorized } from '@/lib/auth'
import { CTA_VARIANT_IDS } from '@/lib/cta-messages'

const PUBLIC_EVENT_TYPES = new Set([
  'trial_view',
  'trial_page_view',
  'trial_download_started',
  'support_cta_view',
  'booth_like_cta_click',
  'collection_click',
  'booth_shop_click',
  'booth_click',
  'cta_click',
])

function cleanVariant(body: Record<string, unknown>): string | null {
  if (typeof body.variant !== 'string') return null
  const v = body.variant.trim()
  if (!v || v.length > 64) return null
  if (v !== 'ab' && v !== 'custom' && !CTA_VARIANT_IDS.includes(v)) return null
  return v
}

export async function POST(request: Request) {
  let body: Record<string, unknown>
  try {
    body = await request.json()
  } catch {
    return NextResponse.json({ error: 'Invalid JSON' }, { status: 400 })
  }

  const eventType = typeof body.eventType === 'string' ? body.eventType : ''
  const variant = cleanVariant(body)

  if (isAdmin(request)) {
    if (!body.fontId || !eventType) {
      return NextResponse.json({ error: 'fontId and eventType required' }, { status: 400 })
    }
    try {
      const event = await prisma.event.create({
        data: {
          fontId: String(body.fontId),
          eventType,
          variant,
          country: typeof body.country === 'string' ? body.country : null,
          referrer: typeof body.referrer === 'string' ? body.referrer.slice(0, 500) : null,
        },
      })
      return NextResponse.json(event)
    } catch {
      return NextResponse.json({ error: 'Invalid fontId' }, { status: 400 })
    }
  }

  const slug = typeof body.slug === 'string' ? body.slug : ''
  if (!slug || !PUBLIC_EVENT_TYPES.has(eventType)) {
    return NextResponse.json({ error: 'Invalid event' }, { status: 400 })
  }
  const font = await prisma.font.findUnique({ where: { slug } })
  if (!font) return NextResponse.json({ error: 'Font not found' }, { status: 404 })

  try {
    const event = await prisma.event.create({
      data: {
        fontId: font.id,
        eventType,
        variant,
        referrer: typeof body.referrer === 'string' ? body.referrer.slice(0, 500) : null,
      },
    })
    return NextResponse.json({ ok: true, id: event.id })
  } catch {
    return NextResponse.json({ ok: true })
  }
}

export async function GET(request: Request) {
  if (!isAdmin(request)) return unauthorized()

  const events = await prisma.event.findMany({
    select: {
      id: true,
      fontId: true,
      eventType: true,
      variant: true,
      country: true,
      createdAt: true,
      font: { select: { id: true, slug: true, name: true } },
    },
    orderBy: { createdAt: 'desc' },
    take: 500,
  })
  return NextResponse.json(events)
}
