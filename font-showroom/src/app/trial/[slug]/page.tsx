import type { Metadata } from 'next'
import Link from 'next/link'
import { prisma } from '@/lib/prisma'
import { publicFontSelect } from '@/lib/fonts'
import { TrialExperience } from './trial-experience'

export const dynamic = 'force-dynamic'

export const metadata: Metadata = {
  title: 'フォントのお試し',
  robots: { index: false, follow: false },
}

export default async function TrialPage({ params }: { params: { slug: string } }) {
  const { slug } = params

  const font = await prisma.font.findUnique({
    where: { slug },
    select: { ...publicFontSelect, trialFile: true },
  })

  if (!font) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
        <div className="max-w-lg w-full bg-white rounded-2xl shadow-xl p-12 text-center">
          <h1 className="text-2xl font-bold mb-2">お試しを利用できません</h1>
          <p className="text-gray-600 mb-6">
            このお試しリンクは期限切れか、フォントが削除された可能性があります。
          </p>
          <Link
            href="/"
            className="inline-block border border-gray-300 px-6 py-3 rounded-lg hover:bg-gray-50"
          >
            コレクションを見る
          </Link>
        </div>
      </div>
    )
  }

  const hasTrial = Boolean(font.trialFile)
  const relatedCount = await prisma.font.count({
    where: { status: 'published', slug: { not: font.slug } },
  })

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-100 flex items-center justify-center p-4 sm:p-6">
      <div className="max-w-lg w-full bg-white rounded-3xl shadow-xl p-6 sm:p-10">
        <TrialExperience font={font} hasTrial={hasTrial} relatedCount={relatedCount} />
        <p className="text-sm text-gray-400 text-center mt-2">Font Studio</p>
      </div>
    </div>
  )
}
