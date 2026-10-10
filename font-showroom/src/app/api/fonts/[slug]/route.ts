import { NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'
import { isAdmin, unauthorized } from '@/lib/auth'
import { publicFontSelect } from '@/lib/fonts'

type Params = { params: { slug: string } }

export async function GET(request: Request, { params }: Params) {
  const { slug } = await params
  const admin = isAdmin(request)

  if (admin) {
    const font = await prisma.font.findUnique({
      where: { slug },
      include: {
        events: {
          orderBy: { createdAt: 'desc' },
          take: 200,
          select: { id: true, eventType: true, variant: true, country: true, createdAt: true },
        },
      },
    })
    if (!font) return NextResponse.json({ error: 'Font not found' }, { status: 404 })
    return NextResponse.json({ ...font, hasTrial: Boolean(font.trialFile) })
  }

  const font = await prisma.font.findUnique({
    where: { slug },
    select: { ...publicFontSelect, status: true, trialFile: true },
  })
  if (!font || font.status !== 'published') {
    return NextResponse.json({ error: 'Font not found' }, { status: 404 })
  }
  const { trialFile, ...rest } = font
  return NextResponse.json({ ...rest, hasTrial: Boolean(trialFile) })
}

export async function PATCH(request: Request, { params }: Params) {
  if (!isAdmin(request)) return unauthorized()

  const { slug } = await params
  const existing = await prisma.font.findUnique({ where: { slug } })
  if (!existing) return NextResponse.json({ error: 'Font not found' }, { status: 404 })

  let body: Record<string, unknown>
  try {
    body = await request.json()
  } catch {
    return NextResponse.json({ error: 'Invalid JSON' }, { status: 400 })
  }

  const data: Record<string, unknown> = {}
  const assignable = [
    'name',
    'status',
    'shortDescription',
    'styles',
    'characterSet',
    'license',
    'featured',
    'ctaVariant',
    'ctaHeadline',
    'ctaMessage',
    'ctaButton',
    'boothUrl',
    'boothProductId',
    'boothName',
    'boothThumbnail',
    'boothDescription',
    'boothPrice',
  ] as const

  for (const key of assignable) {
    if (key in body) {
      data[key] = body[key] === undefined ? null : body[key]
    }
  }

  if (typeof data.status === 'string' && !['draft', 'published'].includes(data.status)) {
    return NextResponse.json({ error: 'Invalid status' }, { status: 400 })
  }

  const nextStatus = typeof data.status === 'string' ? data.status : existing.status
  const nextBooth = 'boothUrl' in data ? (data.boothUrl as string | null) : existing.boothUrl
  if (nextStatus === 'published' && (!existing.trialFile || !nextBooth)) {
    return NextResponse.json(
      { error: 'A font needs a trial ZIP and a BOOTH URL before it can be published.' },
      { status: 400 }
    )
  }

  if (typeof data.ctaVariant === 'string') {
    const allowed = [
      'ab',
      'auto',
      'direct_support',
      'concise',
      'small_shop',
      'just_downloaded',
      'new_release',
      'discovery',
      'creator',
      'community',
      'very_direct',
      'premium',
      'shop_growth',
      'product_discovery',
      'independent_creator',
      'custom',
    ]
    if (!allowed.includes(data.ctaVariant)) {
      return NextResponse.json({ error: 'Invalid CTA variant' }, { status: 400 })
    }
    if (data.ctaVariant === 'custom' && !data.ctaMessage && !existing.ctaMessage) {
      return NextResponse.json({ error: 'Custom CTA requires a message.' }, { status: 400 })
    }
  }

  try {
    const font = await prisma.font.update({ where: { slug }, data })
    return NextResponse.json(font)
  } catch {
    return NextResponse.json({ error: 'Update failed' }, { status: 400 })
  }
}

export async function DELETE(request: Request, { params }: Params) {
  if (!isAdmin(request)) return unauthorized()

  const { slug } = await params
  try {
    await prisma.font.delete({ where: { slug } })
    return NextResponse.json({ success: true })
  } catch {
    return NextResponse.json({ error: 'Font not found' }, { status: 404 })
  }
}
