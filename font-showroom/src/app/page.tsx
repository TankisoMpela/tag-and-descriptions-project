import Link from 'next/link'
import { prisma } from '@/lib/prisma'
import { publicFontSelect } from '@/lib/fonts'

export const dynamic = 'force-dynamic'

const BOOTH_SHOP = process.env.NEXT_PUBLIC_BOOTH_URL || 'https://booth.pm'

export default async function Home() {
  const published = await prisma.font.findMany({
    where: { status: 'published' },
    select: publicFontSelect,
    orderBy: { createdAt: 'desc' },
  })

  const featured = published.find((f) => f.featured) || published[0] || null

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

      <main>
        <section style={{ padding: '5rem 2rem', textAlign: 'center' }}>
          <h2
            style={{
              fontSize: '2.5rem',
              fontWeight: 'bold',
              marginBottom: '1rem',
              maxWidth: '900px',
              marginLeft: 'auto',
              marginRight: 'auto',
            }}
          >
            変な・かわいい・ノスタルジック・遊び心のあるプロジェクトのための書体
          </h2>
          <p style={{ fontSize: '1.25rem', color: '#666' }}>
            手づくりのタイプフェイス・コレクション
          </p>
        </section>

        {featured && (
          <section style={{ maxWidth: '1200px', margin: '0 auto', padding: '2rem' }}>
            <h3 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '1.5rem' }}>
              おすすめ
            </h3>
            <article
              style={{
                border: '1px solid #ddd',
                borderRadius: '12px',
                padding: '2rem',
                display: 'grid',
                gridTemplateColumns: 'minmax(0, 1fr) minmax(0, 1fr)',
                gap: '2rem',
                alignItems: 'center',
              }}
            >
              <div>
                {featured.boothThumbnail && (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={featured.boothThumbnail}
                    alt={featured.name}
                    style={{
                      width: '100%',
                      borderRadius: '8px',
                      objectFit: 'cover',
                      maxHeight: '360px',
                    }}
                  />
                )}
              </div>
              <div>
                <p style={{ color: '#666', fontSize: '0.875rem', marginBottom: '0.5rem' }}>
                  注目のフォント
                </p>
                <h4 style={{ fontSize: '2rem', fontWeight: 'bold', marginBottom: '0.75rem' }}>
                  {featured.name}
                </h4>
                <p style={{ color: '#555', marginBottom: '1.5rem', lineHeight: 1.6 }}>
                  {featured.shortDescription ||
                    featured.boothDescription?.slice(0, 220) ||
                    'コレクションから届く、手づくりのタイプフェイス。'}
                </p>
                <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                  <Link
                    href={`/fonts/${featured.slug}`}
                    style={{
                      background: '#000',
                      color: '#fff',
                      padding: '0.75rem 1.5rem',
                      borderRadius: '4px',
                      textDecoration: 'none',
                    }}
                  >
                    フォントを見る
                  </Link>
                  {featured.boothUrl && (
                    <a
                      href={featured.boothUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{
                        border: '1px solid #000',
                        padding: '0.75rem 1.5rem',
                        borderRadius: '4px',
                        textDecoration: 'none',
                      }}
                    >
                      BOOTHで見る
                    </a>
                  )}
                </div>
              </div>
            </article>
          </section>
        )}

        {published.length > 0 && (
          <section style={{ maxWidth: '1200px', margin: '0 auto', padding: '2rem' }}>
            <h3 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '2rem' }}>
              フォントコレクション
            </h3>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
                gap: '2rem',
              }}
            >
              {published.map((font) => (
                <article
                  key={font.id}
                  style={{
                    border: '1px solid #ddd',
                    borderRadius: '8px',
                    padding: '1.5rem',
                    display: 'flex',
                    flexDirection: 'column',
                  }}
                >
                  {font.boothThumbnail && (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={font.boothThumbnail}
                      alt={font.name}
                      style={{
                        width: '100%',
                        height: '180px',
                        objectFit: 'cover',
                        borderRadius: '4px',
                        marginBottom: '1rem',
                      }}
                    />
                  )}
                  <h4 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '0.5rem' }}>
                    {font.name}
                  </h4>
                  <p style={{ color: '#666', marginBottom: '1rem', flexGrow: 1 }}>
                    {(font.shortDescription || font.boothDescription || '').slice(0, 100)}
                    {(font.shortDescription || font.boothDescription || '').length > 100
                      ? '…'
                      : ''}
                  </p>
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                    }}
                  >
                    <span style={{ fontSize: '1.125rem', fontWeight: 500 }}>
                      {font.boothPrice || ''}
                    </span>
                    <Link
                      href={`/fonts/${font.slug}`}
                      style={{
                        background: '#000',
                        color: '#fff',
                        padding: '0.5rem 1rem',
                        borderRadius: '4px',
                        textDecoration: 'none',
                      }}
                    >
                      見る
                    </Link>
                  </div>
                </article>
              ))}
            </div>
          </section>
        )}

        {published.length === 0 && (
          <section
            style={{
              maxWidth: '1200px',
              margin: '0 auto',
              padding: '2rem',
              textAlign: 'center',
              color: '#666',
            }}
          >
            <p>公開中のフォントはまだありません。</p>
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
