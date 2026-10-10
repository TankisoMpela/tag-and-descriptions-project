import { NextResponse } from 'next/server'
import { put } from '@vercel/blob'
import { prisma } from '@/lib/prisma'
import { isAdmin, unauthorized } from '@/lib/auth'

type Params = { params: { slug: string } }

export async function POST(request: Request, { params }: Params) {
  if (!isAdmin(request)) return unauthorized()

  const { slug } = params
  const font = await prisma.font.findUnique({ where: { slug } })
  if (!font) return NextResponse.json({ error: 'Font not found' }, { status: 404 })

  const formData = await request.formData()
  const file = formData.get('file')
  if (!(file instanceof File)) {
    return NextResponse.json({ error: 'No file provided' }, { status: 400 })
  }
  if (!file.name.toLowerCase().endsWith('.zip')) {
    return NextResponse.json({ error: 'Trial package must be a .zip file' }, { status: 400 })
  }

  const blob = await put(`trials/${slug}-${Date.now()}.zip`, file, {
    access: 'public',
  })
  await prisma.font.update({ where: { slug }, data: { trialFile: blob.url } })
  return NextResponse.json({ success: true, downloadUrl: blob.url })
}

export async function GET(request: Request, { params }: Params) {
  const { slug } = params
  const font = await prisma.font.findUnique({ where: { slug } })
  if (!font || !font.trialFile) {
    return NextResponse.json({ error: 'Trial not available' }, { status: 404 })
  }

  try {
    const geo = (request as Request & { geo?: { country?: string } }).geo
    await prisma.event.create({
      data: {
        fontId: font.id,
        eventType: 'trial_download',
        country: geo?.country ?? null,
        referrer: request.headers.get('referer'),
      },
    })
  } catch {
    // never block the download on analytics
  }

  let upstream: Response
  try {
    upstream = await fetch(font.trialFile, { cache: 'no-store' })
  } catch {
    return NextResponse.json({ error: 'Could not fetch trial file' }, { status: 502 })
  }
  if (!upstream.ok || !upstream.body) {
    return NextResponse.json({ error: 'Trial file unavailable' }, { status: 502 })
  }

  const headers = new Headers({
    'Content-Type': upstream.headers.get('content-type') || 'application/zip',
    'Content-Disposition': `attachment; filename="${slug}-trial.zip"`,
    'Cache-Control': 'no-store',
  })
  const length = upstream.headers.get('content-length')
  if (length) headers.set('Content-Length', length)

  return new NextResponse(upstream.body, { status: 200, headers })
}
