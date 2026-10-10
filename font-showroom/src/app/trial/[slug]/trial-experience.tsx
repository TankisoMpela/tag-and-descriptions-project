'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import { trackEvent } from '@/lib/track'
import {
  abStorageKey,
  getCtaCopyForVariant,
  isAbMode,
  pickAbVariant,
  resolveCtaVariant,
} from '@/lib/cta-messages'
import type { PublicFont } from '@/lib/fonts'

type Phase = 'idle' | 'starting' | 'post' | 'error'

const BOOTH_SHOP = process.env.NEXT_PUBLIC_BOOTH_URL || 'https://booth.pm'

function storageKey(slug: string) {
  return `trial_downloaded_${slug}`
}

function readStored(key: string) {
  try {
    return localStorage.getItem(key)
  } catch {
    return null
  }
}

function writeStored(key: string, value: string) {
  try {
    localStorage.setItem(key, value)
  } catch {
    // ignore
  }
}

function ensureAbVariant(slug: string): string {
  const stored = readStored(abStorageKey(slug))
  const pick = pickAbVariant(slug, stored)
  if (stored !== pick) writeStored(abStorageKey(slug), pick)
  return pick
}

export function TrialExperience({
  font,
  hasTrial,
  relatedCount = 0,
}: {
  font: PublicFont
  hasTrial: boolean
  relatedCount?: number
}) {
  const [phase, setPhase] = useState<Phase>('idle')
  // SSR-safe default; sticky AB pick is locked in the lockVariant effect below.
  const [activeVariant, setActiveVariant] = useState<string>(() =>
    font.ctaVariant === 'custom' ? 'custom' : resolveCtaVariant(font.ctaVariant)
  )
  const supportTracked = useRef(false)
  const viewTracked = useRef(false)

  const cta = getCtaCopyForVariant(
    activeVariant,
    font.ctaVariant === 'custom' ? font : undefined
  )

  const lockVariant = useCallback(() => {
    if (font.ctaVariant === 'custom') {
      setActiveVariant('custom')
      return 'custom'
    }
    if (isAbMode(font.ctaVariant)) {
      const pick = ensureAbVariant(font.slug)
      setActiveVariant(pick)
      return pick
    }
    const pinned = resolveCtaVariant(font.ctaVariant)
    setActiveVariant(pinned)
    return pinned
  }, [font.ctaVariant, font.slug])

  const markSupportView = useCallback(() => {
    if (supportTracked.current) return
    supportTracked.current = true
    trackEvent('support_cta_view', font.slug, activeVariant)
  }, [font.slug, activeVariant])

  useEffect(() => {
    lockVariant()
  }, [lockVariant])

  useEffect(() => {
    if (!viewTracked.current) {
      viewTracked.current = true
      trackEvent('trial_view', font.slug)
      trackEvent('trial_page_view', font.slug)
    }
    try {
      if (localStorage.getItem(storageKey(font.slug)) === '1') {
        setPhase('post')
      }
    } catch {
      // ignore storage errors
    }
  }, [font.slug])

  useEffect(() => {
    if (phase === 'post') markSupportView()
  }, [phase, markSupportView])

  const startDownload = async () => {
    if (!hasTrial || phase === 'starting') return
    setPhase('starting')
    const variant = lockVariant()
    trackEvent('trial_download_started', font.slug, variant)

    try {
      const res = await fetch(`/api/download/${font.slug}`, { cache: 'no-store' })
      if (!res.ok) throw new Error('download failed')

      const blob = await res.blob()
      const objectUrl = URL.createObjectURL(blob)
      const anchor = document.createElement('a')
      anchor.href = objectUrl
      anchor.download = `${font.slug}-trial.zip`
      document.body.appendChild(anchor)
      anchor.click()
      anchor.remove()
      window.setTimeout(() => URL.revokeObjectURL(objectUrl), 15_000)

      writeStored(storageKey(font.slug), '1')
      setPhase('post')
    } catch {
      setPhase('error')
    }
  }

  const onBoothLike = () => {
    trackEvent('booth_like_cta_click', font.slug, activeVariant)
    trackEvent('cta_click', font.slug, activeVariant)
  }

  const onCollection = () => {
    trackEvent('collection_click', font.slug, activeVariant)
    trackEvent('cta_click', font.slug, activeVariant)
  }

  const onShop = () => {
    trackEvent('booth_shop_click', font.slug, activeVariant)
  }

  const specimenLine = `${font.name} ${font.name} ${font.name}`

  if (phase === 'idle' || phase === 'starting') {
    return (
      <div className="w-full text-center">
        <div className="mb-8">
          {font.boothThumbnail && (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={font.boothThumbnail}
              alt=""
              className="w-full max-w-sm mx-auto rounded-xl mb-6 shadow-md"
            />
          )}
          <p className="text-xs tracking-widest text-gray-400 mb-2">個人利用 無料お試し</p>
          <h1 className="text-4xl font-bold mb-3">{font.name}</h1>
          <p className="text-gray-600 mb-6 max-w-md mx-auto">
            {font.shortDescription ||
              font.boothDescription?.slice(0, 180) ||
              'このフォントを試していただき、ありがとうございます。'}
          </p>
          <div className="bg-gray-50 rounded-xl p-5 text-left text-sm sm:text-base text-gray-800 leading-relaxed border border-gray-100">
            <p className="mb-1">ABCDEFGHIJKLMNOPQRSTUVWXYZ</p>
            <p className="mb-1">abcdefghijklmnopqrstuvwxyz</p>
            <p>0123456789</p>
          </div>
        </div>

        <p className="text-lg font-semibold mb-1">お試しファイルの準備ができました。</p>
        <p className="text-sm text-gray-500 mb-5">アカウント不要。すぐにダウンロードできます。</p>

        {hasTrial ? (
          <button
            type="button"
            onClick={() => void startDownload()}
            disabled={phase === 'starting'}
            className="w-full bg-black text-white py-4 rounded-xl text-lg font-semibold hover:bg-gray-800 transition disabled:opacity-60"
          >
            {phase === 'starting' ? 'ダウンロード中…' : 'フォントをダウンロード'}
          </button>
        ) : (
          <p className="text-gray-500 text-sm py-4">
            このフォントのお試しファイルはまだありません。
          </p>
        )}
      </div>
    )
  }

  if (phase === 'error') {
    return (
      <div className="w-full text-center">
        <div className="rounded-xl border border-red-100 bg-red-50 p-6 mb-6">
          <p className="font-semibold text-red-800 mb-1">ダウンロードを開始できませんでした。</p>
          <p className="text-sm text-red-700">もう一度お試しください。</p>
        </div>
        <button
          type="button"
          onClick={() => void startDownload()}
          className="w-full bg-black text-white py-4 rounded-xl text-lg font-semibold hover:bg-gray-800 transition"
        >
          もう一度試す
        </button>
      </div>
    )
  }

  return (
    <div className="w-full text-center">
      <div className="mb-5 inline-flex items-center gap-2 rounded-full bg-green-50 text-green-800 px-4 py-2 text-sm font-semibold">
        <span aria-hidden>✓</span>
        ダウンロードを開始しました
      </div>

      {/* Mini product poster: what they just downloaded, then the ask */}
      <section
        aria-label="ダウンロードした商品"
        className="rounded-3xl border border-gray-200 bg-white shadow-lg overflow-hidden mb-6 text-left"
      >
        {font.boothThumbnail && (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={font.boothThumbnail} alt="" className="w-full h-52 sm:h-64 object-cover" />
        )}

        <div className="px-5 pt-5 pb-6 sm:px-7 sm:pt-6 text-center border-b border-gray-100">
          <p className="inline-block text-[11px] tracking-[0.2em] uppercase text-gray-500 border border-gray-300 rounded-full px-3 py-1 mb-4">
            Free Trial
          </p>
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight mb-2">{font.name}</h2>
          <p
            className="text-lg sm:text-xl text-gray-700 mb-3 break-words"
            style={{ fontFamily: 'ui-monospace, monospace' }}
          >
            {specimenLine}
          </p>
          <p className="text-sm text-gray-600 max-w-sm mx-auto leading-relaxed">
            {font.shortDescription ||
              font.styles ||
              font.boothDescription?.slice(0, 120) ||
              'コレクションから届いた個人利用向けお試しです。'}
          </p>
          {font.boothPrice && (
            <p className="text-xs text-gray-500 mt-3">BOOTH · {font.boothPrice}</p>
          )}
        </div>

        <div className="bg-black text-white px-5 py-7 sm:px-7 sm:py-8 text-center">
          <h3 className="text-lg sm:text-xl font-bold mb-3 leading-snug">{cta.headline}</h3>
          <p className="text-sm sm:text-base text-gray-200 leading-relaxed mb-5 max-w-sm mx-auto">
            {cta.message}
          </p>
          <p className="text-xs text-gray-400 mb-4">
            BOOTHは新しいタブで開きます。このページはそのまま残ります。
          </p>
          {font.boothUrl ? (
            <a
              href={font.boothUrl}
              target="_blank"
              rel="noopener noreferrer"
              onClick={onBoothLike}
              className="block w-full max-w-xs mx-auto bg-white text-black py-4 rounded-xl text-base font-bold tracking-wide hover:bg-gray-100 transition"
            >
              {cta.button}
            </a>
          ) : (
            <p className="text-sm text-gray-300">BOOTHのリンクがまだ設定されていません。</p>
          )}
        </div>
      </section>

      <p className="text-sm mb-5 text-gray-600">
        <Link
          href="/"
          onClick={onCollection}
          className="font-medium text-gray-800 hover:text-black underline underline-offset-4"
        >
          Explore more fonts →
        </Link>
        {relatedCount > 0 && (
          <span className="block text-xs text-gray-400 mt-1">
            ほかに {relatedCount} 書体があります
          </span>
        )}
      </p>

      <p className="text-sm mb-8">
        <a
          href={BOOTH_SHOP}
          target="_blank"
          rel="noopener noreferrer"
          onClick={onShop}
          className="text-gray-500 hover:text-gray-800 underline underline-offset-4"
        >
          BOOTHショップを見る →
        </a>
      </p>
    </div>
  )
}
