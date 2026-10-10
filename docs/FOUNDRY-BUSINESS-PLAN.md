# PaperMoon / Font Foundry Business Plan

Status: working plan — decisions intentionally open
Last updated: 2026-10-08

This document captures the current direction for building a sustainable font
business around the PaperMoon catalogue and `tmpela.store`. It is a working
brief for future planning sessions, not a final technical specification.

## North-star funnel

```text
Font production
    -> product pages and specimens
    -> discovery (search, Pinterest, free-font platforms, communities)
    -> own website catalogue and account
    -> paid font purchase or time-limited catalogue trial
    -> subscription / repeat purchase
```

The website should become the long-term hub: catalogue, licensing education,
SEO landing pages, customer support, and eventually checkout and downloads.
Third-party marketplaces and free-font platforms are distribution channels,
not the permanent centre of the business.

## Free access and discovery: current direction

The own website is not currently intended to distribute a free Personal-Use
version of every font. The preferred model is:

1. **Paid individual font** — the normal purchase path, with pricing still to
   be tested. Roughly $9–$12 is only a starting hypothesis.
2. **Seven-day catalogue trial** — registered users can temporarily access the
   trial area for seven days. The current idea is to collect a card during
   signup but not automatically charge it when the seven days end.
3. **Subscription** — after the trial ends, users subscribe if they want to
   continue accessing the catalogue's free-download benefits.
4. **Third-party discovery files** — selected free-font platforms may receive
   limited or watermarked versions, if their upload rules permit them. These
   are acquisition assets, not the complete products sold on the own website.

The existing project workflow supports a stamped Free-Trial-Demo archive. That
can be used for third-party discovery, but it should not be assumed that every
platform accepts watermarked glyphs, promotional website marks, or restricted
font archives. Platform policy must be checked per site before uploading.

### Trial-design questions

- Does the seven-day access include full font files, limited demos, or only a
  defined number of downloads?
- Is the trial for personal use only, or does it provide a temporary commercial
  licence? These are very different promises and must be explicit.
- What exactly becomes unavailable when the trial ends?
- Does requiring a card improve conversion enough to justify the extra trust and
  payment-compliance friction?
- Can the payment system verify a card without automatic renewal, and can users
  clearly leave without being charged?
- Should the first test compare a no-card trial with a card-required version?

The main risk is that a card-required trial can feel like a disguised
subscription even when it does not auto-charge. Checkout copy should say
plainly: trial length, what is included, whether any charge will occur, and
what happens afterward. A no-card trial may be a better first experiment, but
that remains open.

Watermarking is a promotional mechanism, not a license. Any third-party file
still needs an explicit license and a plain explanation of what commercial
users must purchase. A platform may reject files whose glyphs are deliberately
altered, whose download is mainly an advertisement, or whose licensing is
unclear; this must be validated site by site.

## Website and store direction

`tmpela.store` is currently the public PaperMoon catalogue. The long-term site
should include:

- searchable font catalogue and categories;
- individual font pages with live previews, glyph/specimen images, features,
  formats, and related fonts;
- clear Commercial and future extended-license explanations;
- paid product download path and a clearly bounded trial path;
- commercial purchase path;
- About, FAQ, licensing, support, and contact pages;
- blog/resource pages built around real font-use searches;
- customer downloads and licenses once the sales system warrants it.

Creative Market is a useful reference for product presentation and licensing
choices. Creative Fabrica is a useful reference for membership packaging and
trial concepts, but the exact access rules, pricing, and entitlement model need
to be designed for PaperMoon rather than copied blindly.

## Live font-preview plan

Font previews do not require a special preview package. The browser already
supports downloadable webfonts through CSS `@font-face`.

Each product page can provide:

- editable preview text;
- font-size controls;
- colour and background controls;
- uppercase/lowercase or specimen presets;
- glyph and character-set previews;
- related font suggestions;
- license options and a purchase button.

The technical flow is:

```text
font source
    -> optimized preview WOFF2
    -> @font-face
    -> editable React specimen component
```

Use WOFF2 preview files for browser delivery. Keep them separate from the
commercial OTF/TTF packages. Any font loaded in a browser can technically be
downloaded, so the website should expose only a preview/demo webfont, never the
full commercial package. Purchased files remain protected behind Lemon Squeezy
entitlements and the R2 download flow.

The storefront can implement this directly with CSS and React state. A font
parsing library such as `fontkit` is optional and may later help with metadata,
glyph coverage, previews, or server-side subsetting; it is not required for the
basic live preview.

## Subscription hypothesis

The subscription is part of the intended model, but its price and scope are not
decided. Roughly $5–$9/month and $9–$12 for individual fonts are starting
hypotheses, not commitments.

Possible later offer:

- individual commercial licenses remain available;
- a membership unlocks a defined set of downloads or catalogue access while
  active;
- the seven-day trial ends without an automatic charge;
- existing customers should not be forced into a subscription.

The first evidence to collect is trial activation, trial-to-paid conversion,
download behaviour, individual-purchase behaviour, cancellation reasons,
catalogue size, and support burden. The subscription must not make individual
purchases look irrational or undermine commercial licensing.

## Initial technical direction

The likely low-cost stack is:

- Next.js/Vercel for the public site and SEO pages;
- Supabase for Postgres data and authentication;
- object storage such as Cloudflare R2 for ZIPs, PDFs, and large assets;
- Lemon Squeezy or another merchant-of-record checkout for early sales;
- server-side order/license entitlement handling;
- Search Console and privacy-conscious analytics for measurement.

Important constraint: a Next.js Commerce starter is a frontend/application
starting point, not a complete font-commerce business. Before building a custom
store, confirm the payment, fulfilment, licensing, authentication, storage,
refund, and customer-download requirements. A simple hosted checkout plus the
existing catalogue may be the best first implementation.

## Discovery channels

Use multiple channels, with the website as the canonical destination:

- search and useful typography articles;
- Pinterest specimen and use-case content;
- selected free-font platforms;
- Telegram/email for release announcements and repeat contact;
- relevant design communities where sharing is allowed;
- existing marketplaces for paid-marketplace discovery.

Each font should produce several useful discovery assets, but quality and
measurement matter more than hitting a fixed publishing number.

## Measurement loop

For each trial, product, and discovery channel, record:

```text
source -> landing page -> font view -> signup -> trial access -> checkout -> purchase
```

Review the evidence before expanding a channel. Traffic alone is not enough;
the useful question is which sources produce people who later need commercial
rights or join the owned audience.

## Decisions to make together later

- PaperMoon name and whether a future rebrand is likely;
- trial access rules, card requirement, and exact limits;
- whether third-party platforms permit watermarked discovery files;
- which third-party free-font sites are worth using;
- whether the own-site download requires email signup;
- license wording and commercial-use tiers;
- Lemon Squeezy first versus custom checkout first;
- when a subscription becomes justified;
- which catalogue categories and SEO topics to prioritize;
- the minimum analytics and customer-support workflow.

## Immediate posture

Keep producing and packaging fonts, keep the website as the brand hub, and
avoid implementing a complicated subscription before the trial rules,
entitlements, and payment behaviour are clear. The next planning session should
choose one small, reversible trial/discovery test and define its success
metrics.
