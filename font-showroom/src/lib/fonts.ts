export const publicFontSelect = {
  id: true,
  slug: true,
  name: true,
  status: true,
  shortDescription: true,
  styles: true,
  characterSet: true,
  license: true,
  featured: true,
  ctaVariant: true,
  ctaHeadline: true,
  ctaMessage: true,
  ctaButton: true,
  boothUrl: true,
  boothProductId: true,
  boothName: true,
  boothThumbnail: true,
  boothDescription: true,
  boothPrice: true,
  createdAt: true,
  updatedAt: true,
} as const

export type PublicFont = {
  id: string
  slug: string
  name: string
  status: string
  shortDescription: string | null
  styles: string | null
  characterSet: string | null
  license: string | null
  featured: boolean
  ctaVariant: string
  ctaHeadline: string | null
  ctaMessage: string | null
  ctaButton: string | null
  boothUrl: string | null
  boothProductId: string | null
  boothName: string | null
  boothThumbnail: string | null
  boothDescription: string | null
  boothPrice: string | null
  createdAt: Date
  updatedAt: Date
}
