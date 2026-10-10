'use client'

import { useCallback, useEffect, useState } from 'react'

type FontRow = {
  id: string
  slug: string
  name: string
  status: string
  shortDescription?: string | null
  styles?: string | null
  characterSet?: string | null
  license?: string | null
  featured?: boolean
  ctaVariant?: string
  ctaHeadline?: string | null
  ctaMessage?: string | null
  ctaButton?: string | null
  trialFile?: string | null
  boothUrl?: string | null
  boothProductId?: string | null
  boothName?: string | null
  boothThumbnail?: string | null
  boothDescription?: string | null
  boothPrice?: string | null
  events?: Array<{ id: string; eventType: string; createdAt: string }>
}

type BoothPreview = {
  boothProductId: string
  boothName: string
  boothThumbnail: string | null
  boothPrice: string | null
  boothDescription: string | null
  boothUrl: string
}

type EventRow = {
  id: string
  eventType: string
  variant?: string | null
  createdAt: string
  font: { id: string; slug: string; name: string }
}

const CTA_VARIANT_LABELS: Record<string, string> = {
  ab: 'Auto A/B',
  direct_support: 'Direct shop support',
  concise: 'Concise',
  small_shop: 'Small shop',
  just_downloaded: 'Just downloaded',
  new_release: 'New release',
  discovery: 'Discovery',
  creator: 'Creator',
  community: 'Community',
  very_direct: 'Very direct',
  premium: 'Premium',
  custom: 'Custom',
  shop_growth: 'Direct shop support (legacy)',
  product_discovery: 'Discovery (legacy)',
  independent_creator: 'Creator (legacy)',
}

const EMPTY_FORM = {
  slug: '',
  name: '',
  shortDescription: '',
  styles: '',
  characterSet: '',
  license: '',
}

const CTA_VARIANT_CHOICES = [
  { id: 'ab', label: 'Auto A/B — rotate 3 (recommended)' },
  { id: 'direct_support', label: 'Pin A/B · Direct shop support' },
  { id: 'discovery', label: 'Pin A/B · Discovery' },
  { id: 'new_release', label: 'Pin A/B · New release' },
  { id: 'concise', label: 'Pin · Very concise' },
  { id: 'small_shop', label: 'Pin · Small independent shop' },
  { id: 'just_downloaded', label: 'Pin · You just downloaded it' },
  { id: 'creator', label: 'Pin · Creator / type foundry' },
  { id: 'community', label: 'Pin · Community feeling' },
  { id: 'very_direct', label: 'Pin · Very direct' },
  { id: 'premium', label: 'Pin · Polished / premium' },
  { id: 'shop_growth', label: 'Legacy · Shop Growth → Direct' },
  { id: 'product_discovery', label: 'Legacy · Product Discovery → Discovery' },
  { id: 'independent_creator', label: 'Legacy · Independent Creator → Creator' },
  { id: 'custom', label: 'Custom (日本語可)' },
] as const

export default function Admin() {
  const [password, setPassword] = useState('')
  const [authenticated, setAuthenticated] = useState(false)
  const [authError, setAuthError] = useState('')
  const [authLoading, setAuthLoading] = useState(false)

  const [fonts, setFonts] = useState<FontRow[]>([])
  const [events, setEvents] = useState<EventRow[]>([])
  const [selected, setSelected] = useState<string | null>(null)
  const [form, setForm] = useState(EMPTY_FORM)
  const [status, setStatus] = useState('draft')
  const [featured, setFeatured] = useState(false)
  const [boothUrl, setBoothUrl] = useState('')
  const [boothPreview, setBoothPreview] = useState<BoothPreview | null>(null)
  const [ctaVariant, setCtaVariant] = useState('ab')
  const [ctaHeadline, setCtaHeadline] = useState('')
  const [ctaMessage, setCtaMessage] = useState('')
  const [ctaButton, setCtaButton] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [file, setFile] = useState<File | null>(null)

  const authHeaders = useCallback(
    (): HeadersInit => ({
      Authorization: `Bearer ${password}`,
      'Content-Type': 'application/json',
    }),
    [password]
  )

  const loadAll = useCallback(async () => {
    const [fontsRes, eventsRes] = await Promise.all([
      fetch('/api/fonts', { headers: { Authorization: `Bearer ${password}` } }),
      fetch('/api/events', { headers: { Authorization: `Bearer ${password}` } }),
    ])
    if (fontsRes.ok) setFonts(await fontsRes.json())
    if (eventsRes.ok) setEvents(await eventsRes.json())
  }, [password])

  useEffect(() => {
    if (authenticated) void loadAll()
  }, [authenticated, loadAll])

  const flash = (msg: string) => {
    setError('')
    setMessage(msg)
    setTimeout(() => setMessage(''), 4000)
  }

  const fail = (msg: string) => {
    setMessage('')
    setError(msg)
  }

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault()
    setAuthLoading(true)
    setAuthError('')
    try {
      const res = await fetch('/api/auth', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password }),
      })
      if (res.ok) {
        setAuthenticated(true)
      } else {
        setAuthError('Incorrect password')
      }
    } catch {
      setAuthError('Could not reach the server')
    } finally {
      setAuthLoading(false)
    }
  }

  const selectFont = (font: FontRow) => {
    setSelected(font.slug)
    setForm({
      slug: font.slug,
      name: font.name,
      shortDescription: font.shortDescription || '',
      styles: font.styles || '',
      characterSet: font.characterSet || '',
      license: font.license || '',
    })
    setStatus(font.status)
    setFeatured(Boolean(font.featured))
    setCtaVariant(font.ctaVariant || 'ab')
    setCtaHeadline(font.ctaHeadline || '')
    setCtaMessage(font.ctaMessage || '')
    setCtaButton(font.ctaButton || '')
    setBoothUrl(font.boothUrl || '')
    setBoothPreview(
      font.boothProductId || font.boothUrl
        ? {
            boothProductId: font.boothProductId || '',
            boothName: font.boothName || '',
            boothThumbnail: font.boothThumbnail || null,
            boothPrice: font.boothPrice || null,
            boothDescription: font.boothDescription || null,
            boothUrl: font.boothUrl || '',
          }
        : null
    )
    setFile(null)
    setMessage('')
    setError('')
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setBusy(true)
    try {
      const res = await fetch('/api/fonts', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({
          slug: form.slug,
          name: form.name,
          status: 'draft',
          shortDescription: form.shortDescription || null,
        }),
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        fail(data.error || 'Could not create font')
        return
      }
      const created = await res.json()
      flash(`Created ${created.name}`)
      setForm(EMPTY_FORM)
      await loadAll()
      selectFont(created)
    } finally {
      setBusy(false)
    }
  }

  const handleSave = async () => {
    if (!selected) return
    setBusy(true)
    try {
      const res = await fetch(`/api/fonts/${selected}`, {
        method: 'PATCH',
        headers: authHeaders(),
        body: JSON.stringify({
          name: form.name,
          status,
          featured,
          shortDescription: form.shortDescription || null,
          styles: form.styles || null,
          characterSet: form.characterSet || null,
          license: form.license || null,
          ctaVariant,
          ctaHeadline: ctaHeadline || null,
          ctaMessage: ctaMessage || null,
          ctaButton: ctaButton || null,
          boothUrl: boothPreview?.boothUrl || boothUrl || null,
          boothProductId: boothPreview?.boothProductId || null,
          boothName: boothPreview?.boothName || null,
          boothThumbnail: boothPreview?.boothThumbnail || null,
          boothDescription: boothPreview?.boothDescription || null,
          boothPrice: boothPreview?.boothPrice || null,
        }),
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        fail(data.error || 'Save failed')
        return
      }
      flash('Saved')
      await loadAll()
    } finally {
      setBusy(false)
    }
  }

  const fetchBooth = async () => {
    if (!boothUrl.trim()) {
      fail('Paste a BOOTH product URL first')
      return
    }
    setBusy(true)
    try {
      const res = await fetch('/api/booth', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ url: boothUrl.trim() }),
      })
      const data = await res.json()
      if (!res.ok) {
        fail(data.error || 'BOOTH fetch failed')
        return
      }
      setBoothPreview(data)
      flash('BOOTH product loaded — review and save')
    } finally {
      setBusy(false)
    }
  }

  const syncBooth = async () => {
    if (!selected) return
    const url = boothPreview?.boothUrl || boothUrl
    if (!url) {
      fail('No BOOTH URL to sync')
      return
    }
    setBoothUrl(url)
    setBusy(true)
    try {
      const res = await fetch('/api/booth', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ url }),
      })
      const data = await res.json()
      if (!res.ok) {
        fail(data.error || 'Sync failed')
        return
      }
      setBoothPreview(data)
      const saveRes = await fetch(`/api/fonts/${selected}`, {
        method: 'PATCH',
        headers: authHeaders(),
        body: JSON.stringify({
          boothUrl: data.boothUrl,
          boothProductId: data.boothProductId,
          boothName: data.boothName,
          boothThumbnail: data.boothThumbnail,
          boothDescription: data.boothDescription,
          boothPrice: data.boothPrice,
        }),
      })
      if (!saveRes.ok) {
        fail('Fetched BOOTH data but could not save it')
        return
      }
      flash('Synced with BOOTH')
      await loadAll()
    } finally {
      setBusy(false)
    }
  }

  const handleUpload = async () => {
    if (!selected || !file) return
    setUploading(true)
    try {
      const fd = new FormData()
      fd.append('file', file)
      const res = await fetch(`/api/download/${selected}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${password}` },
        body: fd,
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) {
        fail(data.error || 'Upload failed')
        return
      }
      flash('Trial ZIP uploaded')
      setFile(null)
      await loadAll()
    } finally {
      setUploading(false)
    }
  }

  const handleDelete = async (slug: string) => {
    if (!confirm(`Delete ${slug}? This also removes its analytics.`)) return
    setBusy(true)
    try {
      const res = await fetch(`/api/fonts/${slug}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${password}` },
      })
      if (!res.ok) {
        fail('Delete failed')
        return
      }
      if (selected === slug) {
        setSelected(null)
        setForm(EMPTY_FORM)
        setBoothPreview(null)
      }
      flash('Deleted')
      await loadAll()
    } finally {
      setBusy(false)
    }
  }

  const eventCounts = (slug: string) => {
    const rows = events.filter((e) => e.font.slug === slug)
    const count = (t: string) => rows.filter((e) => e.eventType === t).length
    return {
      trial_view: count('trial_view') + count('trial_page_view'),
      trial_download: rows.filter(
        (e) =>
          e.eventType === 'trial_download' ||
          e.eventType === 'download' ||
          e.eventType === 'trial_download_started'
      ).length,
      support_cta_view: count('support_cta_view'),
      booth_like: count('booth_like_cta_click') + count('booth_click'),
      collection_click: count('collection_click'),
      booth_shop_click: count('booth_shop_click'),
    }
  }

  const totals = (() => {
    const count = (t: string) => events.filter((e) => e.eventType === t).length
    return {
      trial_view: count('trial_view') + count('trial_page_view'),
      trial_download: events.filter(
        (e) =>
          e.eventType === 'trial_download' ||
          e.eventType === 'download' ||
          e.eventType === 'trial_download_started'
      ).length,
      support_cta_view: count('support_cta_view'),
      booth_like: count('booth_like_cta_click') + count('booth_click'),
      collection_click: count('collection_click'),
      booth_shop_click: count('booth_shop_click'),
    }
  })()

  const abLeaderboard = (() => {
    const ids = new Set<string>()
    for (const e of events) {
      if (
        e.variant &&
        (e.eventType === 'support_cta_view' || e.eventType === 'booth_like_cta_click')
      ) {
        ids.add(e.variant)
      }
    }
    return [...ids]
      .map((variant) => {
      const views = events.filter(
        (e) => e.eventType === 'support_cta_view' && e.variant === variant
      ).length
      const clicks = events.filter(
        (e) => e.eventType === 'booth_like_cta_click' && e.variant === variant
      ).length
      const rate = views > 0 ? Math.round((clicks / views) * 1000) / 10 : 0
      return {
        variant,
        label: CTA_VARIANT_LABELS[variant] || variant,
        views,
        clicks,
        rate,
      }
    })
    .sort((a, b) => b.rate - a.rate || b.clicks - a.clicks || b.views - a.views)
  })()

  const selectedFont = fonts.find((f) => f.slug === selected) || null
  const inputStyle: React.CSSProperties = {
    padding: '0.5rem',
    border: '1px solid #ddd',
    borderRadius: '4px',
    width: '100%',
  }

  if (!authenticated) {
    return (
      <div
        style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: '#f5f5f5',
        }}
      >
        <form
          onSubmit={handleAuth}
          style={{
            background: '#fff',
            padding: '2rem',
            borderRadius: '8px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            width: '100%',
            maxWidth: '320px',
          }}
        >
          <h1 style={{ fontSize: '1.25rem', fontWeight: 'bold', marginBottom: '1rem' }}>
            Admin Login
          </h1>
          <input
            type="password"
            placeholder="Enter password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={{ ...inputStyle, marginBottom: '1rem' }}
            autoFocus
          />
          {authError && (
            <p style={{ color: '#dc3545', fontSize: '0.875rem', marginBottom: '0.75rem' }}>
              {authError}
            </p>
          )}
          <button
            type="submit"
            disabled={authLoading}
            style={{
              width: '100%',
              background: '#000',
              color: '#fff',
              padding: '0.5rem',
              borderRadius: '4px',
              border: 'none',
              cursor: 'pointer',
            }}
          >
            {authLoading ? 'Checking…' : 'Login'}
          </button>
        </form>
      </div>
    )
  }

  return (
    <div style={{ minHeight: '100vh', background: '#f5f5f5', padding: '2rem' }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '2rem',
          }}
        >
          <h1 style={{ fontSize: '2rem', fontWeight: 'bold' }}>Admin Dashboard</h1>
          <button
            onClick={() => {
              setAuthenticated(false)
              setPassword('')
            }}
            style={{
              background: 'none',
              border: '1px solid #ccc',
              padding: '0.4rem 0.8rem',
              borderRadius: '4px',
              cursor: 'pointer',
            }}
          >
            Log out
          </button>
        </div>

        {message && (
          <div
            style={{
              background: '#d4edda',
              color: '#155724',
              padding: '0.75rem 1rem',
              borderRadius: '4px',
              marginBottom: '1.5rem',
            }}
          >
            {message}
          </div>
        )}
        {error && (
          <div
            style={{
              background: '#f8d7da',
              color: '#721c24',
              padding: '0.75rem 1rem',
              borderRadius: '4px',
              marginBottom: '1.5rem',
            }}
          >
            {error}
          </div>
        )}

        <section
          style={{
            background: '#fff',
            padding: '1.5rem',
            borderRadius: '8px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            marginBottom: '1.5rem',
          }}
        >
          <h2 style={{ fontSize: '1.15rem', fontWeight: 'bold', marginBottom: '1rem' }}>
            Analytics overview
          </h2>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
              gap: '1rem',
            }}
          >
            {(
              [
                ['Trial views', totals.trial_view],
                ['Downloads', totals.trial_download],
                ['CTA views', totals.support_cta_view],
                ['BOOTH CTA clicks', totals.booth_like],
                ['Collection clicks', totals.collection_click],
                ['Shop clicks', totals.booth_shop_click],
              ] as Array<[string, number]>
            ).map(([label, value]) => (
              <div
                key={label}
                style={{ background: '#f9f9f9', padding: '1rem', borderRadius: '6px' }}
              >
                <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>{value}</div>
                <div style={{ color: '#666', fontSize: '0.85rem' }}>{label}</div>
              </div>
            ))}
          </div>

          <h3 style={{ fontSize: '0.95rem', fontWeight: 600, margin: '1.25rem 0 0.75rem' }}>
            CTA A/B leaderboard (BOOTH CTA click rate by message)
          </h3>
          {abLeaderboard.length === 0 ? (
            <p style={{ color: '#888', fontSize: '0.875rem', margin: 0 }}>
              No variant-tagged CTA events yet. Leave fonts on Auto A/B to collect data.
            </p>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #ddd', textAlign: 'left' }}>
                    <th style={{ padding: '0.4rem' }}>Message</th>
                    <th style={{ padding: '0.4rem' }}>CTA views</th>
                    <th style={{ padding: '0.4rem' }}>BOOTH CTA clicks</th>
                    <th style={{ padding: '0.4rem' }}>Click rate</th>
                  </tr>
                </thead>
                <tbody>
                  {abLeaderboard.map((row) => (
                    <tr key={row.variant} style={{ borderBottom: '1px solid #eee' }}>
                      <td style={{ padding: '0.4rem' }}>{row.label}</td>
                      <td style={{ padding: '0.4rem' }}>{row.views}</td>
                      <td style={{ padding: '0.4rem' }}>{row.clicks}</td>
                      <td style={{ padding: '0.4rem', fontWeight: 600 }}>{row.rate}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <section
          style={{
            background: '#fff',
            padding: '1.5rem',
            borderRadius: '8px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            marginBottom: '1.5rem',
          }}
        >
          <h2 style={{ fontSize: '1.15rem', fontWeight: 'bold', marginBottom: '1rem' }}>
            Add New Font
          </h2>
          <form
            onSubmit={handleCreate}
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
              gap: '1rem',
              marginBottom: '1rem',
            }}
          >
            <input
              placeholder="Slug (e.g. mochi)"
              value={form.slug}
              onChange={(e) => setForm({ ...form, slug: e.target.value })}
              style={inputStyle}
              required
            />
            <input
              placeholder="Name (e.g. Mochi)"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              style={inputStyle}
              required
            />
            <input
              placeholder="Short description"
              value={form.shortDescription}
              onChange={(e) => setForm({ ...form, shortDescription: e.target.value })}
              style={inputStyle}
            />
            <button
              type="submit"
              disabled={busy}
              style={{
                background: '#000',
                color: '#fff',
                padding: '0.5rem 1rem',
                borderRadius: '4px',
                border: 'none',
                cursor: 'pointer',
              }}
            >
              Create Font
            </button>
          </form>
        </section>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'minmax(0, 1.2fr) minmax(0, 1fr)',
            gap: '1.5rem',
            alignItems: 'start',
          }}
        >
          <section
            style={{
              background: '#fff',
              padding: '1.5rem',
              borderRadius: '8px',
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            }}
          >
            <h2 style={{ fontSize: '1.15rem', fontWeight: 'bold', marginBottom: '1rem' }}>
              Fonts
            </h2>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #ddd' }}>
                    <th style={{ textAlign: 'left', padding: '0.5rem' }}>Name</th>
                    <th style={{ textAlign: 'left', padding: '0.5rem' }}>BOOTH</th>
                    <th style={{ textAlign: 'left', padding: '0.5rem' }}>Trial</th>
                    <th style={{ textAlign: 'left', padding: '0.5rem' }}>Status</th>
                    <th style={{ textAlign: 'left', padding: '0.5rem' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {fonts.map((font) => {
                    const c = eventCounts(font.slug)
                    return (
                      <tr
                        key={font.id}
                        style={{
                          borderBottom: '1px solid #eee',
                          background: selected === font.slug ? '#f0f7ff' : undefined,
                          cursor: 'pointer',
                        }}
                        onClick={() => selectFont(font)}
                      >
                        <td style={{ padding: '0.5rem' }}>
                          {font.name}
                          {font.featured ? ' ★' : ''}
                          <div
                            style={{
                              fontSize: '0.75rem',
                              color: '#888',
                              fontWeight: 400,
                            }}
                          >
                            {font.slug} · 👁 {c.trial_view} · ⬇ {c.trial_download} ·{' '}
                            {c.booth_like} CTA
                          </div>
                        </td>
                        <td style={{ padding: '0.5rem' }}>
                          {font.boothProductId || font.boothUrl ? 'Connected' : '—'}
                        </td>
                        <td style={{ padding: '0.5rem' }}>{font.trialFile ? '✓' : '—'}</td>
                        <td style={{ padding: '0.5rem' }}>
                          <span
                            style={{
                              padding: '0.25rem 0.5rem',
                              borderRadius: '4px',
                              fontSize: '0.8rem',
                              background:
                                font.status === 'published' ? '#d4edda' : '#fff3cd',
                              color: font.status === 'published' ? '#155724' : '#856404',
                            }}
                          >
                            {font.status}
                          </span>
                        </td>
                        <td style={{ padding: '0.5rem', whiteSpace: 'nowrap' }}>
                          <a
                            href={`/fonts/${font.slug}`}
                            target="_blank"
                            rel="noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            style={{ marginRight: '0.5rem', fontSize: '0.85rem' }}
                          >
                            Preview
                          </a>
                          <a
                            href={`/trial/${font.slug}`}
                            target="_blank"
                            rel="noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            style={{ marginRight: '0.5rem', fontSize: '0.85rem' }}
                          >
                            Trial
                          </a>
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              void handleDelete(font.slug)
                            }}
                            style={{
                              color: '#dc3545',
                              background: 'none',
                              border: 'none',
                              cursor: 'pointer',
                              fontSize: '0.85rem',
                            }}
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    )
                  })}
                  {fonts.length === 0 && (
                    <tr>
                      <td colSpan={5} style={{ padding: '1rem', color: '#666' }}>
                        No fonts yet — create one above.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>

          <section
            style={{
              background: '#fff',
              padding: '1.5rem',
              borderRadius: '8px',
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
              position: 'sticky',
              top: '1rem',
            }}
          >
            <h2 style={{ fontSize: '1.15rem', fontWeight: 'bold', marginBottom: '1rem' }}>
              {selected ? `Edit: ${selectedFont?.name || selected}` : 'Edit Font'}
            </h2>

            {!selected && (
              <p style={{ color: '#666' }}>Select a font from the list to edit it.</p>
            )}

            {selected && (
              <div className="space-y-4" style={{ display: 'grid', gap: '1rem' }}>
                <label style={{ display: 'block' }}>
                  <span style={{ fontSize: '0.85rem', color: '#666' }}>Name</span>
                  <input
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    style={inputStyle}
                  />
                </label>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                  <label>
                    <span style={{ fontSize: '0.85rem', color: '#666' }}>Status</span>
                    <select
                      value={status}
                      onChange={(e) => setStatus(e.target.value)}
                      style={inputStyle}
                    >
                      <option value="draft">Draft</option>
                      <option value="published">Published</option>
                    </select>
                  </label>
                  <label>
                    <span style={{ fontSize: '0.85rem', color: '#666' }}>Featured</span>
                    <select
                      value={featured ? 'yes' : 'no'}
                      onChange={(e) => setFeatured(e.target.value === 'yes')}
                      style={inputStyle}
                    >
                      <option value="no">No</option>
                      <option value="yes">Yes</option>
                    </select>
                  </label>
                </div>

                <label>
                  <span style={{ fontSize: '0.85rem', color: '#666' }}>Short description</span>
                  <textarea
                    value={form.shortDescription}
                    onChange={(e) => setForm({ ...form, shortDescription: e.target.value })}
                    rows={2}
                    style={inputStyle}
                  />
                </label>

                <div style={{ display: 'grid', gap: '0.5rem' }}>
                  <span style={{ fontSize: '0.85rem', color: '#666', fontWeight: 600 }}>
                    Trial ZIP
                  </span>
                  <div style={{ fontSize: '0.85rem' }}>
                    {selectedFont?.trialFile ? '✓ Uploaded' : 'No trial file yet'}
                  </div>
                  <input
                    type="file"
                    accept=".zip"
                    onChange={(e) => setFile(e.target.files?.[0] || null)}
                  />
                  <button
                    onClick={() => void handleUpload()}
                    disabled={!file || uploading}
                    style={{
                      background: '#333',
                      color: '#fff',
                      padding: '0.5rem 1rem',
                      borderRadius: '4px',
                      border: 'none',
                      cursor: 'pointer',
                      opacity: !file || uploading ? 0.6 : 1,
                    }}
                  >
                    {uploading ? 'Uploading…' : 'Upload trial ZIP'}
                  </button>
                </div>

                <div style={{ borderTop: '1px solid #eee', paddingTop: '1rem' }}>
                  <span style={{ fontSize: '0.85rem', color: '#666', fontWeight: 600 }}>
                    BOOTH
                  </span>
                  <input
                    placeholder="https://shop.booth.pm/items/…"
                    value={boothUrl}
                    onChange={(e) => setBoothUrl(e.target.value)}
                    style={{ ...inputStyle, marginTop: '0.5rem' }}
                  />
                  <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
                    <button
                      onClick={() => void fetchBooth()}
                      disabled={busy}
                      style={{
                        background: '#333',
                        color: '#fff',
                        padding: '0.45rem 0.8rem',
                        borderRadius: '4px',
                        border: 'none',
                        cursor: 'pointer',
                      }}
                    >
                      Fetch Product
                    </button>
                    <button
                      onClick={() => void syncBooth()}
                      disabled={busy || !(boothPreview?.boothUrl || boothUrl)}
                      style={{
                        background: '#555',
                        color: '#fff',
                        padding: '0.45rem 0.8rem',
                        borderRadius: '4px',
                        border: 'none',
                        cursor: 'pointer',
                      }}
                    >
                      Sync with BOOTH
                    </button>
                  </div>

                  {boothPreview && (
                    <div
                      style={{
                        marginTop: '0.75rem',
                        padding: '0.75rem',
                        border: '1px solid #ddd',
                        borderRadius: '4px',
                        background: '#f9f9f9',
                      }}
                    >
                      <div style={{ display: 'flex', gap: '0.75rem' }}>
                        {boothPreview.boothThumbnail && (
                          // eslint-disable-next-line @next/next/no-img-element
                          <img
                            src={boothPreview.boothThumbnail}
                            alt=""
                            style={{
                              width: '72px',
                              height: '72px',
                              objectFit: 'cover',
                              borderRadius: '4px',
                            }}
                          />
                        )}
                        <div>
                          <div style={{ fontWeight: 600 }}>{boothPreview.boothName}</div>
                          <div style={{ fontSize: '0.9rem' }}>
                            {boothPreview.boothPrice || 'Price n/a'}
                          </div>
                          <div style={{ fontSize: '0.8rem', color: '#666' }}>
                            #{boothPreview.boothProductId}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                <div
                  style={{
                    borderTop: '1px solid #eee',
                    paddingTop: '1rem',
                    display: 'grid',
                    gap: '0.75rem',
                  }}
                >
                  <span style={{ fontSize: '0.85rem', color: '#666', fontWeight: 600 }}>
                    Font details
                  </span>
                      <input
                        placeholder="Styles (Regular, Bold…)"
                        value={form.styles}
                        onChange={(e) => setForm({ ...form, styles: e.target.value })}
                        style={inputStyle}
                      />
                      <input
                        placeholder="文字セット Character set (Latin, kana…)"
                        value={form.characterSet}
                        onChange={(e) => setForm({ ...form, characterSet: e.target.value })}
                        style={inputStyle}
                      />
                      <input
                        placeholder="ライセンスメモ License note"
                        value={form.license}
                        onChange={(e) => setForm({ ...form, license: e.target.value })}
                        style={inputStyle}
                      />
                </div>

                <div
                  style={{
                    borderTop: '1px solid #eee',
                    paddingTop: '1rem',
                    display: 'grid',
                    gap: '0.75rem',
                  }}
                >
                  <span style={{ fontSize: '0.85rem', color: '#666', fontWeight: 600 }}>
                    Post-download CTA (日本語で顧客に表示)
                  </span>
                  <label>
                    <span style={{ fontSize: '0.8rem', color: '#888' }}>
                      Message variant (見出し＋本文の組み合わせ)
                    </span>
                    <select
                      value={ctaVariant}
                      onChange={(e) => setCtaVariant(e.target.value)}
                      style={inputStyle}
                    >
                      {CTA_VARIANT_CHOICES.map((v) => (
                        <option key={v.id} value={v.id}>
                          {v.label}
                        </option>
                      ))}
                    </select>
                  </label>
                  {ctaVariant === 'custom' ? (
                    <>
                      <input
                        placeholder="見出し Headline（任意）"
                        value={ctaHeadline}
                        onChange={(e) => setCtaHeadline(e.target.value)}
                        style={inputStyle}
                      />
                      <textarea
                        placeholder="本文 Body（必須）— ダウンロード後に表示"
                        value={ctaMessage}
                        onChange={(e) => setCtaMessage(e.target.value)}
                        rows={3}
                        style={inputStyle}
                      />
                      <input
                        placeholder="ボタン Button（既定: GO LIKE ON BOOTH）"
                        value={ctaButton}
                        onChange={(e) => setCtaButton(e.target.value)}
                        style={inputStyle}
                      />
                    </>
                  ) : ctaVariant === 'ab' ? (
                    <p style={{ fontSize: '0.8rem', color: '#888', margin: 0 }}>
                      各訪問者に3種の見出し＋本文を自動で割り当て（ブラウザごとに固定）。
                      リーダーボードで勝ち負けを確認できます。キャンペーン時は個別に Pin できます。
                    </p>
                  ) : (
                    <p style={{ fontSize: '0.8rem', color: '#888', margin: 0 }}>
                      この見出し＋本文に固定表示します（A/Bを止めます）。
                    </p>
                  )}
                </div>

                <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
                  <button
                    onClick={() => void handleSave()}
                    disabled={busy}
                    style={{
                      background: '#000',
                      color: '#fff',
                      padding: '0.6rem 1.2rem',
                      borderRadius: '4px',
                      border: 'none',
                      cursor: 'pointer',
                    }}
                  >
                    Save Changes
                  </button>
                  <a
                    href={`/fonts/${selected}`}
                    target="_blank"
                    rel="noreferrer"
                    style={{
                      padding: '0.6rem 1rem',
                      borderRadius: '4px',
                      border: '1px solid #ccc',
                      textDecoration: 'none',
                      color: '#000',
                    }}
                  >
                    Preview page
                  </a>
                  <a
                    href={`/trial/${selected}`}
                    target="_blank"
                    rel="noreferrer"
                    style={{
                      padding: '0.6rem 1rem',
                      borderRadius: '4px',
                      border: '1px solid #ccc',
                      textDecoration: 'none',
                      color: '#000',
                    }}
                  >
                    Preview trial
                  </a>
                </div>

                {selectedFont && (
                  <div style={{ fontSize: '0.85rem', color: '#666' }}>
                    Trial URL: <code>/trial/{selected}</code>
                  </div>
                )}
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  )
}
