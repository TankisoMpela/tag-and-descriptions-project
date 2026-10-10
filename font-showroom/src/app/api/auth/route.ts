import { NextResponse } from 'next/server'

export async function POST(request: Request) {
  let body: { password?: string }
  try {
    body = await request.json()
  } catch {
    return NextResponse.json({ error: 'Invalid JSON' }, { status: 400 })
  }

  const expected = process.env.ADMIN_PASSWORD
  if (!expected) {
    return NextResponse.json({ error: 'ADMIN_PASSWORD is not configured' }, { status: 500 })
  }
  if (typeof body.password !== 'string' || body.password !== expected) {
    return NextResponse.json({ error: 'Incorrect password' }, { status: 401 })
  }
  return NextResponse.json({ ok: true })
}
