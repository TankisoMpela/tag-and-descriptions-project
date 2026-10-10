import Link from 'next/link'
import { prisma } from '@/lib/prisma'
import { publicFontSelect } from '@/lib/fonts'
import { FontPageClient } from './font-page-client'

export const dynamic = 'force-dynamic'

const BOOTH_SHOP = process.env.NEXT_PUBLIC_BOOTH_URL || 'https://booth.pm'

export default async function FontPage({ params }: { params: { slug: string } }) {
  const { slug } = params

  const font = await prisma.font.findUnique({
    where: { slug },
    select: { ...publicFontSelect, status: true },
  })

  if (!font || font.status !== 'published') {
    return (
      <div style={{ padding: '3rem', textAlign: 'center' }}>
        <p>フォントが見つかりません</p>
        <p style={{ marginTop: '1rem' }}>
          <Link href="/">フォント一覧へ戻る</Link>
        </p>
      </div>
    )
  }

  const related = await prisma.font.findMany({
    where: { status: 'published', slug: { not: slug } },
    select: publicFontSelect,
    take: 3,
    orderBy: { createdAt: 'desc' },
  })

  const infoRows: Array<[string, string]> = []
  if (font.styles) infoRows.push(['スタイル', font.styles])
  if (font.characterSet) infoRows.push(['文字セット', font.characterSet])
  if (font.license) infoRows.push(['ライセンス', font.license])
  if (font.boothPrice) infoRows.push(['価格', font.boothPrice])
  infoRows.push(['状態', 'BOOTHにて公開中'])

  return (
    <div>
      <header
        style={{
          borderBottom: '1px solid #ddd',
          padding: '1rem 2rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          maxWidth: '1200px',
          margin: '0 auto',
        }}
      >
        <Link href="/" style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#000' }}>
          Font Studio
        </Link>
        <nav style={{ display: 'flex', gap: '1.5rem' }}>
          <Link href="/">フォント</Link>
          <Link href="/about">このショップについて</Link>
          <a href={BOOTH_SHOP} target="_blank" rel="noopener noreferrer">
            BOOTH
          </a>
        </nav>
      </header>

      <main style={{ maxWidth: '1200px', margin: '0 auto', padding: '2rem' }}>
        <FontPageClient font={font} related={related} />

        <section>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '1.5rem' }}>
            見本
          </h2>
          <div
            style={{
              background: '#f9f9f9',
              padding: '2rem',
              borderRadius: '8px',
              fontSize: '1.5rem',
              lineHeight: 1.8,
              overflowX: 'auto',
            }}
          >
            <p style={{ marginBottom: '1rem' }}>ABCDEFGHIJKLMNOPQRSTUVWXYZ</p>
            <p style={{ marginBottom: '1rem' }}>abcdefghijklmnopqrstuvwxyz</p>
            <p style={{ marginBottom: '1rem' }}>0123456789</p>
            <p style={{ marginBottom: 0 }}>!@#$%&amp;*()[]{'{}'}</p>
          </div>
        </section>

        <section style={{ marginTop: '3rem' }}>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '1.5rem' }}>
            情報
          </h2>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
              gap: '1rem',
            }}
          >
            {infoRows.map(([label, value]) => (
              <div key={label}>
                <span style={{ color: '#666' }}>{label}:</span>{' '}
                <span style={{ fontWeight: 500 }}>{value}</span>
              </div>
            ))}
          </div>
        </section>

        {related.length > 0 && (
          <section style={{ marginTop: '3rem' }}>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '1.5rem' }}>
              関連フォント
            </h2>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                gap: '1.5rem',
              }}
            >
              {related.map((r) => (
                <article
                  key={r.id}
                  style={{
                    border: '1px solid #ddd',
                    borderRadius: '8px',
                    padding: '1.25rem',
                  }}
                >
                  <h3 style={{ fontWeight: 600, marginBottom: '0.5rem' }}>{r.name}</h3>
                  <p
                    style={{
                      color: '#666',
                      fontSize: '0.95rem',
                      marginBottom: '1rem',
                      minHeight: '2.5em',
                    }}
                  >
                    {(r.shortDescription || r.boothDescription || '').slice(0, 90)}
                  </p>
                  <Link
                    href={`/fonts/${r.slug}`}
                    style={{
                      display: 'inline-block',
                      background: '#000',
                      color: '#fff',
                      padding: '0.4rem 0.9rem',
                      borderRadius: '4px',
                      textDecoration: 'none',
                      fontSize: '0.9rem',
                    }}
                  >
                    見る
                  </Link>
                </article>
              ))}
            </div>
          </section>
        )}
      </main>

      <footer
        style={{
          borderTop: '1px solid #ddd',
          padding: '2rem',
          textAlign: 'center',
          color: '#666',
          marginTop: '3rem',
        }}
      >
        <p style={{ marginBottom: '0.5rem' }}>
          <Link href="/">フォント</Link>
          {' · '}
          <Link href="/about">このショップについて</Link>
          {' · '}
          <a href={BOOTH_SHOP} target="_blank" rel="noopener noreferrer">
            BOOTHショップ
          </a>
        </p>
        <p>© {new Date().getFullYear()} Font Studio</p>
      </footer>
    </div>
  )
}
