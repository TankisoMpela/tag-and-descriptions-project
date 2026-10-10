export type CtaVariantId =
  | 'ab'
  | 'direct_support'
  | 'concise'
  | 'small_shop'
  | 'just_downloaded'
  | 'new_release'
  | 'discovery'
  | 'creator'
  | 'community'
  | 'very_direct'
  | 'premium'
  | 'custom'

export type CtaCopy = {
  headline: string
  message: string
  button: string
}

type VariantDef = {
  label: string
  copy: CtaCopy
  en: CtaCopy
}

const BUTTON = 'GO LIKE ON BOOTH'

export const CTA_VARIANTS: Record<Exclude<CtaVariantId, 'custom' | 'ab'>, VariantDef> = {
  direct_support: {
    label: 'Direct shop support',
    copy: {
      headline: '私たちのショップの成長を、応援してください。',
      message:
        'このフォントが気に入ったら、BOOTHの商品にいいねをお願いします。ご支援が、新しいフォント制作の励みになります。',
      button: BUTTON,
    },
    en: {
      headline: 'Please help support and grow our shop.',
      message:
        'If you enjoyed this font, please consider leaving the product a like on BOOTH. Your support helps us continue creating and releasing new fonts.',
      button: BUTTON,
    },
  },
  concise: {
    label: '2 · Very concise',
    copy: {
      headline: '好きになりましたか？',
      message: 'ショップ応援のため、この商品にいいねをお願いします。',
      button: BUTTON,
    },
    en: {
      headline: 'Enjoying the font?',
      message: 'Please help support our shop by liking this product on BOOTH.',
      button: BUTTON,
    },
  },
  small_shop: {
    label: '3 · Small independent shop',
    copy: {
      headline: '小さなフォントショップを応援 ♡',
      message:
        '気に入ったら、BOOTHでのいいねが作品を見つけやすくなるだけでなく、ショップの力になります。',
      button: BUTTON,
    },
    en: {
      headline: 'Support our little font shop ♡',
      message:
        'If you enjoyed this font, a like on BOOTH helps more people discover our work and supports the shop.',
      button: BUTTON,
    },
  },
  just_downloaded: {
    label: '4 · You just downloaded it',
    copy: {
      headline: '今ダウンロードしたフォント、お気に入りですか？',
      message:
        'BOOTHの商品にいいねをお願いします。ショップの成長と、次のようなフォント作りの励みになります。',
      button: BUTTON,
    },
    en: {
      headline: 'Enjoying the font you just downloaded?',
      message:
        'Please consider giving the BOOTH product a like. Your support helps us grow the shop and make more fonts like this.',
      button: BUTTON,
    },
  },
  new_release: {
    label: 'New release',
    copy: {
      headline: '新作に、ちょっとした応援をお願いします。',
      message: '気に入ったら、BOOTHの商品にいいねを。新作を出し続ける励みになります。',
      button: BUTTON,
    },
    en: {
      headline: 'Help us give this new release a little support.',
      message:
        'If you enjoyed the font, please leave the product a like on BOOTH. It helps support the shop as we continue releasing new work.',
      button: BUTTON,
    },
  },
  discovery: {
    label: 'Discovery',
    copy: {
      headline: '気に入ったら、ほかの方にも見つけてもらえます。',
      message:
        'BOOTHのいいねは、ショップへの応援と、このフォントの見える化につながります。',
      button: BUTTON,
    },
    en: {
      headline: 'Enjoying this font? Help others discover it too.',
      message:
        'A like on BOOTH helps support our shop and gives this font a little more visibility.',
      button: BUTTON,
    },
  },
  creator: {
    label: '7 · Creator / type foundry',
    copy: {
      headline: 'インディペンデントな書体デザインを応援する。',
      message:
        '役に立ったと思ったら、BOOTHでこの商品にいいねをお願いします。新しいフォントを作り続ける力になります。',
      button: BUTTON,
    },
    en: {
      headline: 'Support independent type design.',
      message:
        'If this font was useful to you, please consider liking the product on BOOTH. Your support helps us continue making new fonts.',
      button: BUTTON,
    },
  },
  community: {
    label: '8 · Community feeling',
    copy: {
      headline: 'このフォント、楽しめましたか？',
      message:
        'BOOTHの商品にいいねをお願いします。フォントづくりを続けられる応援になります。ありがとうございます。',
      button: BUTTON,
    },
    en: {
      headline: 'Enjoyed trying this font?',
      message:
        'Please help support and grow our shop by leaving the product a like on BOOTH. Thank you for helping us keep making fonts.',
      button: BUTTON,
    },
  },
  very_direct: {
    label: '9 · Very direct',
    copy: {
      headline: 'このフォントを応援してください ♡',
      message: '今ダウンロードしたBOOTHの商品にいいねいただけると嬉しいです。',
      button: BUTTON,
    },
    en: {
      headline: 'Please support this font ♡',
      message: 'You can help our shop by liking the BOOTH product you just downloaded.',
      button: BUTTON,
    },
  },
  premium: {
    label: '10 · Polished / premium',
    copy: {
      headline: 'タイポグラフィの裏側の仕事を、応援する。',
      message:
        'お試しを気に入ったら、BOOTHでいいねをお願いします。インディペンデントなショップが新作を出し続ける力になります。',
      button: BUTTON,
    },
    en: {
      headline: 'Support the work behind the type.',
      message:
        'If you enjoyed this trial, please consider liking the font on BOOTH. Your support helps our independent shop continue creating new releases.',
      button: BUTTON,
    },
  },
}

export type AbPoolId = Exclude<CtaVariantId, 'custom' | 'ab'>

/**
 * Auto A/B starts with 3 strong approaches only — low traffic splits into
 * statistical soup across 10 messages. Other presets stay available to pin.
 */
export const AB_POOL: AbPoolId[] = ['direct_support', 'discovery', 'new_release']

export const PINNABLE_IDS = Object.keys(CTA_VARIANTS) as AbPoolId[]

const LEGACY_ALIASES: Record<string, AbPoolId> = {
  shop_growth: 'direct_support',
  product_discovery: 'discovery',
  independent_creator: 'creator',
  default: 'direct_support',
}

export const CTA_VARIANT_OPTIONS: Array<{ id: string; label: string }> = [
  { id: 'ab', label: `Auto A/B — rotate ${AB_POOL.length} (recommended)` },
  ...AB_POOL.map((id) => ({ id, label: `Pin A/B · ${CTA_VARIANTS[id].label}` })),
  ...PINNABLE_IDS.filter((id) => !(AB_POOL as string[]).includes(id)).map((id) => ({
    id,
    label: `Pin · ${CTA_VARIANTS[id].label}`,
  })),
  { id: 'custom', label: 'Custom (日本語可)' },
]

export const CTA_VARIANT_IDS = ['ab', ...PINNABLE_IDS, 'custom']

export function isAbMode(raw?: string | null) {
  const id = (raw || 'ab').trim()
  return id === 'ab' || id === '' || id === 'auto'
}

export function isPresetId(id: string): id is AbPoolId {
  return id in CTA_VARIANTS
}

export function resolveCtaVariant(raw?: string | null): AbPoolId {
  const id = (raw || 'direct_support').trim()
  if (id in CTA_VARIANTS) return id as AbPoolId
  if (id in LEGACY_ALIASES) return LEGACY_ALIASES[id]
  return 'direct_support'
}

export function abStorageKey(slug: string) {
  return `cta_ab_${slug}`
}

/** Sticky per-browser, per-font pick so a visitor always sees the same message. */
export function pickAbVariant(slug: string, stored?: string | null): AbPoolId {
  if (stored && (AB_POOL as string[]).includes(stored)) return stored as AbPoolId
  const pool = AB_POOL
  if (typeof crypto !== 'undefined' && 'getRandomValues' in crypto) {
    const buf = new Uint32Array(1)
    crypto.getRandomValues(buf)
    return pool[buf[0] % pool.length]
  }
  return pool[Math.floor(Math.random() * pool.length)]
}

export function getCtaCopyForVariant(variantId: string, font?: {
  ctaHeadline?: string | null
  ctaMessage?: string | null
  ctaButton?: string | null
}): CtaCopy {
  if (variantId === 'custom' && font?.ctaMessage?.trim()) {
    return {
      headline: font.ctaHeadline?.trim() || '私たちのショップの成長を、応援してください。',
      message: font.ctaMessage.trim(),
      button: font.ctaButton?.trim() || BUTTON,
    }
  }
  if (variantId === 'ab') {
    return CTA_VARIANTS.direct_support.copy
  }
  return CTA_VARIANTS[resolveCtaVariant(variantId)].copy
}

export function getCtaCopy(font: {
  ctaVariant?: string | null
  ctaHeadline?: string | null
  ctaMessage?: string | null
  ctaButton?: string | null
}): CtaCopy {
  const raw = (font.ctaVariant || 'ab').trim()

  if (raw === 'custom' && font.ctaMessage?.trim()) {
    return getCtaCopyForVariant('custom', font)
  }

  // Server/SSR default for AB mode; client locks a sticky pick in the trial UI.
  if (isAbMode(raw)) {
    return CTA_VARIANTS.direct_support.copy
  }

  return CTA_VARIANTS[resolveCtaVariant(raw)].copy
}
