# Font Showroom

A font trial & BOOTH storefront system: public showroom, private-ish trial pages linked from BOOTH PDFs, and an admin dashboard.

## Getting Started

1. Install dependencies:
   ```bash
   npm install
   ```

2. Configure environment (see `SECRETS.md` — never commit real secrets):
   ```bash
   vercel env pull
   # or set in .env.local:
   # DATABASE_URL=postgresql://...
   # ADMIN_PASSWORD=...
   # BLOB_READ_WRITE_TOKEN=...
   # NEXT_PUBLIC_BOOTH_URL=https://yourshop.booth.pm
   ```

3. Push the database schema:
   ```bash
   npx prisma migrate deploy
   # first time / local: npx prisma migrate dev
   ```

4. Run the development server:
   ```bash
   npm run dev
   ```

5. Open http://localhost:3000/admin

## Features

- Public font showroom (`/`, `/fonts/[slug]`, `/about`) — Japanese-first for BOOTH customers
- Trial pages (`/trial/[slug]`, `noindex`): download starts immediately, page stays open, then a mini product poster + **GO LIKE ON BOOTH** CTA (opens in a new tab)
- CTA library: **Auto A/B** (sticky per browser across 3 headline+body flavors) + pin/custom; leaderboard in admin
- Admin dashboard: create/edit/publish fonts, upload trial ZIPs, fetch/sync BOOTH metadata, pick CTA mode, analytics
- First-party analytics: trial views, download starts, CTA views, BOOTH CTA clicks (with `variant`), collection clicks, shop clicks

## Add a font (workflow)

1. Admin → Create Font (slug + name)
2. Upload trial ZIP
3. Paste BOOTH URL → Fetch Product → Save / Sync
4. Fill style / character set / license + optional post-download CTA
5. Set status to **Published** (requires trial ZIP + BOOTH URL; optionally Featured)
6. Preview `/fonts/…` and `/trial/…`

## Stack

- Next.js 14 (App Router)
- Prisma + PostgreSQL (Neon)
- Vercel Blob for trial ZIPs
- Tailwind CSS 3

## Deploy to Vercel

1. Push to GitHub (ensure `.env*` and `SECRETS.md` stay ignored)
2. Import project in Vercel dashboard
3. Add environment variables
4. Deploy
