# AI × Shopify Business Bootcamp — theme v13

Rebuilt from the audit in `THEME_AUDIT.md`. Everything the audit flagged as P0 is fixed, the P1 conversion
work is built in, and the theme now follows Shopify's current architecture requirements (section groups,
JSON templates, blocks + presets, locales, structured data).

**Install file:** `ai-shopify-business-bootcamp-v13.zip`
**Source:** `theme-v13/`
**Design preview:** run a server in `preview/` and open `index.html`

---

## 1. Install

1. Shopify admin → **Online Store → Themes → Add theme → Upload zip**
2. Upload `ai-shopify-business-bootcamp-v13.zip`
3. **Customize** to check it, then **Publish** when ready.

The theme is safe to publish immediately. The buy buttons only work after step 2 below.

## 2. Create the product (required)

**Fastest path:** Shopify admin → **Products → Import** → `setup/product-import.csv`.
Every field below is already filled in that file, including a ~500-word description. Import, check the
handle, and set the real seat count.

The whole theme points at **one** product.

| Field | Value |
|---|---|
| Title | AI × Shopify Business Bootcamp |
| Handle | `ai-shopify-business-bootcamp` |
| Price | 2999 |
| Compare-at price | 5000 |
| Track quantity | **On** — set the real number of seats left |
| Status | Active |

- The handle is configured in **Theme settings → Course product → Course product handle**. Change it there, not in code.
- **Track quantity matters:** the "Only N seats left" chip and the sticky-bar seat count read
  `variant.inventory_quantity`. Turn it off and those claims disappear instead of lying.
- If you later sell more than one product, the pricing section has its own product picker and the store
  still works normally for collections/search.

## 3. Store settings that unlock theme features

| Where | Setting | Effect |
|---|---|---|
| Settings → Policies | Refund, Privacy, Terms, Shipping — **drafts in `setup/policies/`** | Footer + contact page legal links (auto). Required for ad approval and gateway KYC. |
| Theme settings → Contact & social | WhatsApp number | Announcement bar, FAQ, pricing, footer, contact page CTAs |
| Theme settings → Contact & social | Instagram / YouTube / LinkedIn | Footer icon row + `sameAs` in structured data |
| Theme settings → Course product | Cohort start date | Countdown timer in the announcement bar and `Course.startDate` |
| Theme settings → SEO & sharing | Social share image (1200×630) | WhatsApp/LinkedIn/X link previews + Organization logo |
| Theme settings → Logo & icons | Logo, favicon | Header, footer, gift card, browser tab |
| Online Store → Navigation | Add menu links | Header nav (optional — the theme falls back to in-page anchors) |

Without a WhatsApp number or support email, contact links fall back to `mailto:shop-email` so nothing is ever dead.

## 4. Content to add (the sections already look finished without it)

1. **Testimonials** — replace the 3 placeholders with real quotes, names, roles, photos. Add student-store
   screenshots to the results row.
2. **Video** — upload a Shopify-hosted video (best) or paste a YouTube/Vimeo URL + poster. External videos only
   load when tapped, so mobile users pay no data cost up front.
3. **Instructor photo** — portrait, ≥800×1000. There's a monogram placeholder until then.
4. **Curriculum / FAQ / What's included** — all are *blocks* now: add, reorder or delete rows in the editor
   without touching code.
5. **Hero copy** — heading, accent word, bullets, stats and CTAs are all editable; the price in the CTA button is live.

## 5. What changed vs. the old theme

**Blocking bugs fixed**

- Desktop layout: the old CSS targeted `.bootcamp-v10` while the markup used `.bootcamp-v12`, so sections had
  **zero padding and no max-width** above 750px. The rebuilt theme uses one container + one spacing scale.
- `.eyebrow` had no base rule at all (micro-labels rendered as plain body text). Now a real component.
- 9 of 14 links rendered `href=""`, including the header CTA. The rebuilt theme audit renders **59 anchors, 0 empty**.
- Navigation vanished below 900px with no replacement; there is now a `dialog`-based mobile menu.
- Empty default state (black video box, blank photo square) → designed fallbacks.
- Video `aspect-ratio:9/16` + `object-fit:cover` cropped landscape recordings into an unreadable slice.
  Now letterboxed (`object-fit:contain`) with a per-section shape setting.
- `routes.contact_url` — **this route does not exist in Shopify.** The old footer/CTA usage silently rendered
  empty links; replaced with a `contact-link` snippet (WhatsApp → email → shop email).
- A parenthesised Liquid expression in the JSON-LD block, unsupported by Shopify's Liquid, was caught by the
  parser test and rewritten.

**Buy path**

- `templates/product.json` + `main-product` section with a real `{% form 'product' %}`, variant selects,
  quantity input, express checkout (`form | payment_button`) and stock-aware button states.
- Cart drawer (`sections/cart-drawer.liquid`) refreshed through the Section Rendering API, plus a full cart page.
- Sticky mobile buy bar that submits the product form via `form="course-buy-form"`.
- AJAX add-to-cart with a `<noscript>`-safe fallback (without JS the forms still post to `/cart/add`).

**Editor experience**

- 29 sections, every one with `presets`; blocks for FAQ, curriculum phases, bento cards, testimonials, stats, tools, credentials.
- Header/footer moved into **section groups** (`header-group.json`, `footer-group.json`) as required for new themes.
- Full template coverage incl. 404, search, page, contact, blog, article, password, gift card and 7 customer templates.
- `config/settings_schema.json` + `settings_data.json` + `locales/en.default.json`: colours, fonts, page width,
  radius, course product, contact, SEO and performance toggles.

**Accessibility (WCAG 2.2 AA targets)**

- Visible `:focus-visible` rings on every interactive element; skip link; landmark roles; `aria-current` on nav.
- Menus and the cart drawer use native `<dialog>` (free focus trap, Esc to close, inert background).
- Minimum body text 14px; tap targets ≥44px; no text below 4.5:1 contrast (the old `.hero-price s{opacity:.55}` fail is gone).
- Cart updates and form errors announce through a polite live region; `prefers-reduced-motion` disables animation.

**SEO**

- JSON-LD graph: `Organization`, `WebSite` + `SearchAction`, `Product`/`Offer`, `Course` + `CourseInstance` with
  instructor, availability and currency read live from the product.
- `FAQPage` generated from the FAQ blocks (only the questions you actually show).
- Dynamic `{{ page_description }}`, `canonical_url`, OpenGraph + Twitter cards with `og:image:width/height`, breadcrumbs.

**Performance**

- 54 KB CSS (unminified, one file) and 19 KB JS (unminified, no dependencies, one `defer` script).
- Zero third-party requests, no webfonts loaded from external CDNs (Shopify's font CDN only, `font-display:swap`).
- Responsive `srcset` + `sizes` on every image, `width`/`height` or `aspect-ratio` everywhere to avoid CLS,
  hero image preload, `loading="lazy"` below the fold, click-to-load video embeds, `content-visibility`-friendly
  section structure.

## 6. Verification performed on this build

| Check | Result |
|---|---|
| Liquid parse (real Liquid engine) | 46 / 46 files, 0 errors |
| Section schemas (JSON) | 29 / 29 valid, all named |
| Template JSON + section references | 19 / 19 valid, no dangling references |
| Snippet references | 12 snippets, no missing includes |
| Locale keys | Every `t`-filter key resolves |
| Rendered anchor audit (all sections) | 57 anchors, **0 dead links** |
| CSS coverage | 419 classes, **0 dead rules** (old theme: 73 dead of 119) |
| `theme.js` | `node --check` clean |

Run it yourself: `python3 theme-v13/tools/verify.py`.

## 7. What was added after the first build

**Instant search.** A ⌘K / `/` overlay that queries Shopify's predictive search endpoint and renders products,
pages and guides with images and prices. Requests are debounced and abortable, results announce through a live
region, Enter falls through to the full search page, and the whole thing works without JavaScript (the form is a
plain GET to `/search`). Turn it off in Header → *Instant search overlay*.

**One-tap add to cart.** Collection and search cards show an Add button for single-variant, in-stock products
(`snippets/quick-add.liquid`); anything with options shows *View details* instead, so nobody adds the wrong
variant. It posts to `/cart/add`, so it degrades to the cart page without JavaScript.

**Review-app slots.** The testimonials section accepts `@app` blocks, so a reviews app can be placed from the
editor rather than hard-coded.

**A test suite.** `theme-v13/tools/verify.py` runs eight checks (Liquid parse, schema JSON, template references,
snippet references, locale keys, rendered-link audit, CSS dead-rule detection, JS syntax). `tools/build.py`
refuses to package a theme that fails them, then zips only the folders Shopify expects and prints the SHA-256.

```bash
pip install python-liquid            # required for the parse + link checks
python3 theme-v13/tools/verify.py    # check only
python3 theme-v13/tools/build.py     # check, then package the zip
```

**The `setup/` folder** — everything that lives in Shopify admin rather than the theme:

| File | Purpose |
|---|---|
| `setup/product-import.csv` | Import-ready product: handle, ₹2,999 / ₹5,000, 25 tracked seats, digital (no shipping), SEO fields, full description |
| `setup/make_product_csv.py` | Regenerates the CSV if the copy or price changes |
| `setup/policies/refund-policy.md` | 7-day refund policy matching the on-page promise, plus the grievance officer block |
| `setup/policies/privacy-policy.md` | Data handling written for the DPDP Act, 2023 |
| `setup/policies/terms-of-service.md` | Licence, payment, conduct, IP, **no earnings guarantee**, liability cap |
| `setup/policies/delivery-policy.md` | Digital delivery timings and the "no physical shipping" statement |
| `setup/content-pack.md` | Testimonial outreach scripts, image sizes, a 90-second video script, launch checklist |
| `setup/README.md` | Order of operations |

Policy drafts are drafts. Have them reviewed, and delete any processor listed in the privacy policy that you do
not actually use.

## 8. Files

```
theme-v13/
├── assets/           theme.css (54 KB), theme.js (19 KB)
├── config/           settings_schema.json, settings_data.json
├── layout/           theme.liquid, password.liquid, gift_card.liquid
├── locales/          en.default.json
├── sections/         29 sections + header-group.json + footer-group.json
├── snippets/         11 snippets (icon, price, product-form, contact-link, jsonld, …)
└── templates/        19 templates incl. customers/*
```

## 9. Known limits (honest list)

- **Testimonials, photos and video are placeholders** until you add real ones — that's a content task, not a code task.
- **No reviews app bundled.** Testimonials are merchant-authored blocks, and the section accepts `@app` blocks, so
  installing Judge.me/Loox/Junip is an editor action rather than a code change.
- **Single-product by default.** Collections/search/cart all work, but the landing page is built around one hero product.
- The customer account templates use Shopify's **legacy** customer accounts (`customers/*.json`). New Customer
  Accounts (the hosted version) renders its own UI and ignores these files — both work.
- The theme is **not** submitted to the Shopify Theme Store, so some of its formal requirements (e.g. per-block
  app-block coverage on every section) are partially implemented rather than fully certified.
