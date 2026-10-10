# Getting real traffic data for FontFairy

Your shop is `https://fontfairy.booth.pm/`. Two facts decide everything here:

1. **BOOTH has no item-views panel.** There is no analytics screen in the
   seller dashboard. My earlier note saying to look for one there was wrong.
2. **BOOTH lets you attach your own Google Analytics 4 property** to your shop
   and product pages. That is the only way to see views, and it works.

---

## 1. The actual mechanism: BOOTH's Measurement ID field

From BOOTH's own help article
([ショップや商品のウェブ解析がしたいです](https://booth.pixiv.help/hc/ja/articles/900003694886)):

> `ショップ情報編集` にてGoogle アナリティクスの測定IDを設定することで、
> ショップや商品の**詳細なウェブ解析**が行えます。
>
> *(By setting your Google Analytics measurement ID in Shop Info Edit, you get
> detailed web analytics for your shop **and your products**.)*

So the field you found is not a substitute for an analytics view — **it is the
analytics view.** You supply the GA4 ID; BOOTH fires the tracking on your shop
and item pages; Google Analytics shows you the data.

Two constraints BOOTH states explicitly:

- **GA4 only.** Universal Analytics is dead; a `UA-` tracking ID cannot be set.
- The ID must start with **`G-`**.

**One Measurement ID per shop**, so all your items report into one property.

---

## 2. Step-by-step

### A. Create the GA4 property

1. Go to **https://analytics.google.com** and sign in with the Google account
   you want to own this data.
2. **Admin** (gear, bottom left) → **Create** → **Property**.
3. Name it (e.g. `FontFairy BOOTH`) → set timezone to **Japan** and currency to
   **JPY** → **Next**.
4. Business details: pick Industry = *Arts & Entertainment* (or similar) and
   your size → **Next** → choose your objectives → **Create**.
5. **Create a Data Stream** → choose **Web**.
6. Website URL: `https://fontfairy.booth.pm` — Stream name: `FontFairy BOOTH`
   → **Create stream**.
7. The stream page now shows a **Measurement ID** that looks like
   `G-XXXXXXXXXX`. **Copy it.**

> Google's own instructions for finding the ID, if you get lost:
> https://support.google.com/analytics/answer/12270356

### B. Paste it into BOOTH

1. Go to **https://manage.booth.pm/settings** (ショップ情報編集).
2. Find the **「Google アナリティクス」** section.
3. Paste the `G-XXXXXXXXXX` ID into the **Measurement ID** field.
4. **Save / update the shop settings.**

### C. Wait, then read the data

GA4 starts collecting from the moment the ID is saved. Data appears within a
few hours; **24–48 hours** before reports are complete.

Then in GA4, these are the reports that matter to you:

| question | GA4 report | what to look at |
|---|---|---|
| **how many views did each font get?** | **Reports → Engagement → Pages and screens** | filter path contains `/items/`, sort by Views |
| **how many people saw my shop at all?** | Reports → Acquisition → Traffic acquisition | Sessions by channel |
| **where did they come from?** | Reports → Acquisition → Traffic acquisition | Session source / medium |
| **what did they search before finding me?** | Reports → Acquisition → Traffic acquisition | Secondary dimension → **Session source** — BOOTH search referrals carry the query |
| **did anyone buy?** | Reports → Monetization → Ecommerce purchases | BOOTH supports GA4 **enhanced ecommerce** |

**The first row is the number you have been missing.** `Pages and screens`
filtered to `/items/` gives you **views per font**. That is what separates the
two opposite problems:

    font A: 300 views,  6 likes   -> thumbnail/title is losing people
    font B:  30 views,  6 likes   -> the listing is fine; it needs exposure

Public like counts alone cannot tell those apart. Views can.

### On the "what did they search" row

BOOTH's own site search puts the query in the URL. If a visitor searches on
BOOTH and then lands on your item, the **referrer** carries that query, and GA4
records it. Check **Acquisition → Traffic acquisition** with **Session source**
as the secondary dimension — look for `booth.pm` referrals carrying `?q=`.
This is the closest thing to real typed-query data that exists for your shop,
and it comes free with the same integration.

Set **Admin → Data Streams → your stream → Enhanced measurement → Site search**
to ON, so GA4 parses query parameters properly.

---

## 3. Why Search Console still cannot help

This is unchanged by the GA4 integration, and it is worth being blunt about it.

GSC only reports on a property you have **proven you own** — via a root HTML
file, a DNS TXT record, a `<meta>` tag, or a Google Analytics /
Tag Manager container you own. For `https://fontfairy.booth.pm/`:

| method | why it fails |
|---|---|
| HTML file at `booth.pm/` root | no write access to pixiv's server |
| DNS TXT on `booth.pm` | you do not own the domain |
| `<meta>` tag in the pages | you cannot edit BOOTH's listing HTML |
| Google Analytics | **GA4 is not a GSC verification method** |

That last row matters because it is the obvious thing to try next. GSC's
"Google Analytics" verification method required **Universal Analytics** with
edit rights on the matching property, and Google retired it alongside UA in
2023. A GA4 Measurement ID does not verify anything. And even if it did, the
tag sits on pixiv's domain, not yours.

**So: attaching GA4 gives you traffic data about your shop. It does not, and
cannot, give you a Search Console property.** Those are two different things
and only the first one is available to you.

GSC would only ever cover a domain you own. If FontFairy gets its own site —
even a one-page `fontfairy.com` landing that links to the BOOTH shop — that
domain verifies normally and its GSC reports real typed queries. Until then,
skip GCP entirely. Do not open a project or enable the Search Console API.

---

## 4. What each source gives you

| source | gives you | available now? |
|---|---|---|
| **BOOTH + GA4** | **views per item**, channels, referrals, search queries | **yes — free, ~30 min setup** |
| BOOTH's public route counts | how many items compete per tag | yes — `bin/booth_tag_route_count.py` |
| `--top-lanes` discovery | which tags win in the young cohort | yes — `bin/booth_tag_evidence.py` |
| Own domain + GSC | typed queries, impressions, CTR | needs a domain |
| BOOTH's internal query log | — | does not exist; no public API |

---

## 5. Do this today

1. **Create the GA4 property** (§2A) — free, ~10 minutes.
2. **Paste the `G-` ID into `manage.booth.pm/settings`** (§2B).
3. **Wait 48 hours**, then open **Engagement → Pages and screens**, filter to
   `/items/`, and sort by Views.

That gives you the per-font view counts that no amount of tag analysis could
produce. **Check views before changing another tag** — the numbers may show
your listings are converting fine and simply lack exposure, which is a
different fix from a weak title or thumbnail.

Do not touch GCP or the Search Console API. With no verifiable property there
is nothing to query.

---

## 6. Can this be automated with gcloud? (tested — no)

Short answer: **no, not usefully.** Verified on this machine, not assumed.

| attempt | result |
|---|---|
| `gcloud auth login --scopes=…` | `unrecognized arguments` — `--scopes` was removed from this command |
| `gcloud auth application-default login --scopes=…analytics.edit` | **scope blocked**, see below |
| Admin API call with a plain gcloud token | `403 PERMISSION_DENIED — insufficient authentication scopes` |

The ADC attempt printed this, which is the whole story:

```
WARNING:
The following scopes will be blocked soon for the default client ID:
https://www.googleapis.com/auth/analytics.edit.
To use these scopes, you must provide your own client ID or use service
account impersonation.
```

**gcloud's built-in OAuth client cannot request Analytics scopes.** The
Analytics Admin API lives under Google Marketing Platform, outside GCP, and
Google restricts Google-Cloud-owned clients from requesting those scopes. To
get one you must create your **own** OAuth Client ID (Desktop app) in a GCP
project and pass it with `--client-id-file`. That is several minutes of Console
clicking before any script runs.

**And it would not finish the job anyway.** The final step — pasting the `G-`
ID into `manage.booth.pm/settings` — happens behind your BOOTH login. No API
token touches it.

So the automated route is *strictly more work* than the manual one:

| step | automated | manual |
|---|---|---|
| GCP Console: create an OAuth client | ~10 clicks | — |
| Enable the Analytics Admin API | yes | — |
| Login config + browser consent | yes | — |
| Create property + data stream | script | ~10 clicks |
| **Paste the ID into BOOTH** | **you** | **you** |

The browser path at `analytics.google.com` wins. The Admin API is worth it only
if you are provisioning many properties; you need one.

Your gcloud account (`tankisompela010@gmail.com`) and its projects are
irrelevant here — GA4 properties are not GCP resources. Nothing was changed:
the aborted login left no ADC file and the active account is intact.

---

## 7. Confirming the tag is live (and how long to wait)

### Verified on this shop, 2026-09-22

The shop now carries **two** GA4 IDs, and it matters which is which:

| ID | whose |
|---|---|
| `G-RWT2QKJLDC` | **BOOTH's own** — present on every BOOTH page, ignore it |
| `G-KBT1DE139L` | **this shop's** — the ID added in shop settings |

`G-RWT2QKJLDC` is the platform's own property (BOOTH's pages carry it as
`<meta name="ga">`). Do not confuse it for the shop's, and do not expect data
from it.

Both pages were checked and both carry the shop ID:

| page | result |
|---|---|
| shop top (`fontfairy.booth.pm/`) | shop ID **present** |
| item page (`fontfairy.booth.pm/items/8880826`) | shop ID **present** |

That second row is the one that matters — item pages reporting into the shop
property is what produces per-font view counts.

### Check it yourself, any time

Fetch the page and look for the ID. No login needed:

```bash
curl -sL https://fontfairy.booth.pm/items/8880826 | grep -o 'G-[A-Z0-9]\{6,14\}' | sort -u
```

Expect `G-KBT1DE139L`. If it is missing, the shop settings did not save.

Or use `bin/booth_tag_route_count.py`-style Firecrawl access if BOOTH challenges
the plain request — `firecrawl /v1/scrape` with `formats: ["rawHtml"]` renders
past Cloudflare.

### Timing

| what | when |
|---|---|
| tag visible in page source | **immediately** (confirmed) |
| **Realtime** report shows your own visit | **~1 minute** |
| first rows in **Pages and screens** | ~24 hours |
| reports trustworthy / fully processed | **24–48 hours** |
| any data from before you saved the setting | **never** — GA4 does not backfill |

### The 2-minute confirmation

1. In GA4: **Reports → Realtime**.
2. In a second tab, open `https://fontfairy.booth.pm/` and click into two or
   three item pages.
3. Watch Realtime. You should see yourself within about a minute.

If Realtime shows your visit, the whole chain works: BOOTH injected the tag,
the tag fires, and the property receives it. If it stays empty, the tag is
present but not firing — re-check that the ID was saved in shop settings and
matches the data stream exactly.

### Reading item views

**Reports → Engagement → Pages and screens** → search the path for `/items/` →
sort by **Views**. Item pages are served on the shop subdomain as
`/items/<id>`, so the path filter works directly.
