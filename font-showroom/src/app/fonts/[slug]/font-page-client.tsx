'use client'

import Link from 'next/link'
import { trackEvent } from '@/lib/track'
import type { PublicFont } from '@/lib/fonts'

export function FontPageClient({
  font,
  related,
}: {
  font: PublicFont
  related: PublicFont[]
}) {
  const onBooth = () => trackEvent('booth_click', font.slug)
  const onRelated = () => trackEvent('collection_click', font.slug)

  return (
    <>
      <div style={{ marginBottom: '3rem' }}>
        <h1 style={{ fontSize: '2.5rem', fontWeight: 'bold', marginBottom: '1rem' }}>
          {font.name}
        </h1>
        {font.boothThumbnail && (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={font.boothThumbnail}
            alt={font.name}
            style={{
              width: '100%',
              maxWidth: '480px',
              borderRadius: '8px',
              marginBottom: '1.5rem',
            }}
          />
        )}
        <p style={{ fontSize: '1.125rem', color: '#666', marginBottom: '1.5rem', maxWidth: '720px' }}>
          {font.shortDescription || font.boothDescription}
        </p>
        {font.boothUrl ? (
          <a
            href={font.boothUrl}
            target="_blank"
            rel="noopener noreferrer"
            onClick={onBooth}
            style={{
              background: '#000',
              color: '#fff',
              padding: '0.75rem 1.5rem',
              borderRadius: '4px',
              textDecoration: 'none',
              display: 'inline-block',
            }}
          >
            BOOTHで見る
          </a>
        ) : (
          <span style={{ color: '#999' }}>BOOTHリンクは準備中です</span>
        )}
      </div>

      {related.length > 0 && (
        <div aria-hidden style={{ display: 'none' }}>
          {related.map((r) => (
            <Link key={r.id} href={`/fonts/${r.slug}`} onClick={onRelated}>
              {r.name}
            </Link>
          ))}
        </div>
      )}
    </>
  )
}
