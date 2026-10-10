import { NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'
import { isAdmin, unauthorized } from '@/lib/auth'
import { publicFontSelect } from '@/lib/fonts'

export async function GET(request: Request) {
  const admin = isAdmin(request)

  if (admin) {
    const fonts = await prisma.font.findMany({ orderBy: { createdAt: 'desc' } })
    return NextResponse.json(fonts)
  }

  const fonts = await prisma.font.findMany({
    where: { status: 'published' },
    select: publicFontSelect,
    orderBy: { createdAt: 'desc' },
  })
  return NextResponse.json(fonts)
}

export async function POST(request: Request) {
  if (!isAdmin(request)) return unauthorized()

  const body = await request.json()
  if (!body.slug || !body.name) {
    return NextResponse.json({ error: 'slug and name are required' }, { status: 400 })
  }

  try {
    const status = body.status === 'published' ? 'published' : 'draft'
    if (status === 'published') {
      return NextResponse.json(
        { error: 'Create as draft first, then add a trial ZIP and BOOTH URL before publishing.' },
        { status: 400 }
      )
    }
    const font = await prisma.font.create({
      data: {
        slug: String(body.slug).trim().toLowerCase(),
        name: String(body.name).trim(),
        status: 'draft',
        shortDescription: body.shortDescription ?? null,
      },
    })
    return NextResponse.json(font)
  } catch {
    return NextResponse.json({ error: 'That slug is already in use' }, { status: 409 })
  }
}
