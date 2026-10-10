import Link from 'next/link'

const BOOTH_SHOP = process.env.NEXT_PUBLIC_BOOTH_URL || 'https://booth.pm'

export default function AboutPage() {
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

      <main style={{ maxWidth: '720px', margin: '0 auto', padding: '3rem 2rem' }}>
        <h1 style={{ fontSize: '2.25rem', fontWeight: 'bold', marginBottom: '1.5rem' }}>
          このショップについて
        </h1>
        <p style={{ fontSize: '1.125rem', color: '#555', lineHeight: 1.7, marginBottom: '1.25rem' }}>
          変な・かわいい・ノスタルジック・遊び心・実験的なプロジェクトのための、インディペンデント書体をお届けしています。すべて手づくりで、BOOTHショップから公開しています。ご購入前に試せる個人利用向けお試しもご用意しています。
        </p>
        <p style={{ fontSize: '1.125rem', color: '#555', lineHeight: 1.7, marginBottom: '2rem' }}>
          このサイトはショールームです。コレクションや見本を眺めて、ライセンスとフルリリースはBOOTHからどうぞ。
        </p>
        <a
          href={BOOTH_SHOP}
          target="_blank"
          rel="noopener noreferrer"
          style={{
            display: 'inline-block',
            background: '#000',
            color: '#fff',
            padding: '0.75rem 1.5rem',
            borderRadius: '4px',
            textDecoration: 'none',
          }}
        >
          BOOTHショップを見る
        </a>
      </main>

      <footer
        style={{
          borderTop: '1px solid #ddd',
          padding: '2rem',
          textAlign: 'center',
          color: '#666',
        }}
      >
        <p>© {new Date().getFullYear()} Font Studio</p>
      </footer>
    </div>
  )
}
