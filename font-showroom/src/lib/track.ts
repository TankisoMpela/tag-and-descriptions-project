'use client'

export type AnalyticsEventType =
  | 'trial_view'
  | 'trial_page_view'
  | 'trial_download_started'
  | 'support_cta_view'
  | 'booth_like_cta_click'
  | 'collection_click'
  | 'booth_shop_click'
  | 'booth_click'
  | 'cta_click'

export function trackEvent(
  eventType: AnalyticsEventType,
  slug: string,
  variant?: string | null
) {
  if (typeof window === 'undefined') return
  try {
    void fetch('/api/events', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        slug,
        eventType,
        variant: variant || null,
        referrer: document.referrer || null,
      }),
      keepalive: true,
    })
  } catch {
    // analytics must never break the UI
  }
}
