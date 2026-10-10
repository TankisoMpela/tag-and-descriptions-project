import { NextResponse } from 'next/server'

export function isAdmin(request: Request): boolean {
  const password = process.env.ADMIN_PASSWORD
  if (!password) return false
  const auth = request.headers.get('authorization')
  return auth === `Bearer ${password}`
}

export function unauthorized(): NextResponse {
  return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
}
