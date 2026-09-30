# Website Quality Audit — learn.dartsai.in

**Site:** https://learn.dartsai.in/ ("Darts Ai Academy" / AI × Shopify Business Bootcamp)
**Audit date:** 30 September 2026
**Auditor method:** read-only reconnaissance (no orders placed, no forms submitted, no data or settings modified)
**Deployed build identified:** `Bootcamp theme v17.0.0` (identity comment present in the live rendered `<head>`; theme asset path `/cdn/shop/t/10/`)

---

## 1. Executive summary

The store is **functionally sellable today** — but it has **one systemic defect that silently disables every design setting**, and **two trust/legal gaps that should be fixed before any paid traffic**.

### What is genuinely good (verified on the live site)

| Verified | Evidence |
|---|---|
| v17 is really deployed | Live HTML line 8: `<!-- Bootcamp theme v17.0.0 … express checkout, library-upload video with autoplay, VideoObject + BreadcrumbList schema … -->` |
| Express checkout + quick-checkout panel live | PDP renders express button, "Instant access after payment", payment chips, 7-day refund block |
| Buy path plumbing intact | Product JSON: `price 2999.00`, `compare_at_price 7500.00`, `available`, `requires_shipping: false` (correct for a course) |
| Countdown is accurate | At 2026-09-30 ~08:27 IST it read `01d 12h 33m` → target 2026-10-01 21:00 IST ✓ (±1 min) |
| Search works both ways | `/search?q=bootcamp` → "1 result"; `/search?q=zzzzzzz` → "No results found for "zzzzzzz"." with a back-to-home CTA |
| Cart + cart drawer work | `/cart` renders the empty state with a recovery CTA; drawer renders "Your cart (0 items)" on every page |
| Collection renders | `/collections/all` grid + sale tag + price + one-tap add |
| SEO plumbing present | Canonical, og:*, twitter:*, 1200×630 og:image with `og:image:alt`, 5-part sitemap, correct `robots.txt` incl. agent/UCP directives |
| Lean theme assets | `theme.css` 75,370 B, `theme.js` 36,307 B, single files, no external font/CSS dependencies (653 KB / 78 files total) |
| No dead theme links in the header | Header CTA + "Ask a question" resolve to `wa.me/917012045854` |

### What blocks a confident launch

| # | Issue | Severity |
|---|---|---|
| AUD-01 | **Every design token is discarded in real browsers** — two Liquid errors are printed *inside* the `<style>` block, so all `--c-*`, `--page-width`, `--radius*`, `--shadow*`, `--font-*` variables are empty and the storefront falls back to hard-coded values. **Theme Editor colour/typography/layout settings currently do nothing.** | Blocker |
| AUD-02 | **The refund policy 404s** while the PDP promises "7-day refund" (terms + shipping policies also 404). Consumer-law and payment-provider exposure. | Critical |
| AUD-03 | **PDP testimonials render the placeholder text "Student name" three times.** | High |
| AUD-04 | **Broken button:** "Contact us" on `/pages/data-sharing-opt-out` points at `/pages/https%3A%2F%2Fwa.me%2F…` → 404. | High |
| AUD-05 | **Homepage instructor photo has no `alt`** — confirmed theme bug (`section.settings.name` does not exist in that section's schema). | High |

### Score

| Dimension | Score | Basis |
|---|---|---|
| Overall **6.5 / 10** | — | Weighted; sellable core, fixable blockers |
| Functional | 8.0 | Buy/search/cart/collection verified; checkout entry and forms not executed (read-only mandate) |
| UI / UX | 7.5 | Text-level only; placeholder testimonials + name mismatch cost points |
| Responsive | **Not tested** | No viewport control from the audit environment (v17 build was verified at 390 px + 1440 px in the local build gate) |
| Accessibility (WCAG 2.2 AA) | 6.5 | 3 confirmed markup failures + several unverifiable criteria (keyboard, focus, contrast, screen reader) |
| Security | **Partial / 7.0** | HTTPS, no mixed content, no exposed secrets; headers, CSP, TLS config not measurable from here |
| Performance | **Not measured** | Lighthouse/PSI/CrUX unavailable (API quota 0); only static asset weights verified |
| SEO | 7.0 | Strong plumbing; title/branding inconsistency, empty blog indexed, no H1 gap (see note) |
| Browser compatibility | **Not tested** | No cross-browser execution possible; browser-safe markup confirmed by validator + Chromium 153 |

### Release recommendation

> **CONDITIONAL GO — ship after P0/P1 (est. 2–3 hours of work).**
> Do not start paid traffic until AUD-01 and AUD-02 are closed. AUD-03/04/05 are 15-minute fixes that materially change how the page reads to a buyer.

---

## 2. Coverage, method and confidence

### How each page was tested

| Method | What it proves | Limits |
|---|---|---|
| `fetch_page` text extraction | Page content, copy, links, pricing, states | Strips `<header>`/`<footer>` chrome (see §2.2) — no layout, colour or interaction |
| **W3C Nu HTML Checker (validator.w3.org)** | Raw markup, real parse errors, exact line/column + source dump | Markup only, not behaviour |
| **Shopify product JSON API** | Ground-truth product data (`compare_at_price`, `requires_shipping`, media `alt`) | Shopify throws a 404 on `/products/*.json` on some stores (worked here); **not tested for PDP mobile image gallery** |
| **Chromium 153 (local, headless)** | Real CSS parsing behaviour for the AUD-01 reproduction | Local reproduction of the live condition, not the live page itself |
| Local theme source (`theme-v17/`) | Root cause of every theme-side finding | Source ≠ deployed file for *content*, but v17 identity marker + matching markup confirm the file set |
| Shopify `theme-check-node` (v17 build gate) | Liquid/schema correctness | Reported 0 errors / 0 warnings — it did **not** catch AUD-01/AUD-05 (see §2.3) |

### 2.1 Page coverage

| Page | Fetched | Validated (Nu) | Notes |
|---|---|---|---|
| `/` homepage | ✅ | ✅ 7 errors | full content read |
| `/products/ai-shopify-business-bootcamp` | ✅ | ✅ 2 errors | + product JSON |
| `/collections/all` | ✅ | ✅ 2 errors | + section API probe |
| `/cart` | ✅ | ✅ 5 errors | empty state; + full rendered source |
| `/search?q=bootcamp` | ✅ | — | 1 result |
| `/search?q=zzzzzzz` | ✅ | — | 0-result state |
| `/pages/contact` | ✅ | ✅ 2 errors | contact form inspected, **not submitted** |
| `/policies/privacy-policy` | ✅ | — | exists |
| `/policies/refund-policy` | ✅ **404** | — | AUD-02 |
| `/policies/terms-of-service` | ✅ **404** | — | AUD-02 |
| `/policies/shipping-policy` | ✅ **404** | — | AUD-02 |
| `/pages/data-sharing-opt-out` | ✅ | ✅ 8 errors | AUD-04, AUD-08 |
| `/blogs/news` | ✅ | ✅ 2 errors | "No articles yet." |
| `/robots.txt`, `/sitemap.xml` + 4 sub-maps | ✅ | — | 2 pages, 1 product, 1 collection, 1 empty blog |
| `/checkout`, `/account/*`, `/collections/*/product`, `/gift_cards/*` | ❌ | ❌ | **Not tested** — see §2.4 |

### 2.2 A tool limitation you must know about (not a site bug)

The extraction tool **drops `<header>` and `<footer>` content**. Evidence: Nu's raw markup shows the collection header exists — `</header><ul class="product-grid" role="list">` — while the text extraction showed no heading. **Consequence:** my first pass appeared to show a missing H1 on `/collections/all` and `/blogs/news`; that is a **tool artefact, not a defect** (the shipped `main-collection.liquid:6` and `main-blog.liquid:5` do render `<h1>`, and the raw markup confirms the header is present). It also means **site navigation, footer content, footer policy links and the announcement-bar links were not auditable from here** and must be checked visually.

### 2.3 Why the local build gates missed AUD-01 and AUD-05 (process finding)

* The build harness renders with a Liquid implementation that returns **empty output** for `font_face` and does not validate setting references, so the failing filter produced no visible symptom locally.
* `theme-check` reported 0/0 on the exact zip that throws Liquid errors live.
* **Recommended gate change:** fail the build if the rendered HTML contains the string `Liquid error`, and re-enable/explicitly configure Shopify's `UndefinedObject` check (it is the check that targets AUD-05's `section.settings.name`).

### 2.4 What could **not** be tested here (requires external tools or a person)

| Area | Why | Required tool |
|---|---|---|
| Core Web Vitals / Lighthouse | PageSpeed Insights API returned **429 (daily quota 0)** for this project | PageSpeed Insights UI, Lighthouse, WebPageTest, CrUX |
| Responsive/breakpoints | No viewport or device control from the audit environment | Real devices + Chrome DevTools device mode |
| Keyboard, focus order, screen reader | Needs interaction | axe DevTools, NVDA/VoiceOver, manual tab runs |
| Colour contrast ratios | Needs computed styles | axe / Colour Contrast Analyser |
| Actual font rendering (Assistant) | Needs a browser | Browser devtools → Computed → Rendered fonts |
| Checkout screens | Read-only mandate — no orders may be placed | Staging checkout with a test gateway |
| Contact form + opt-out form submission | Submitting would send real messages/captures | Manual test with an agreed inbox |
| Add-to-cart → cart → checkout handoff | Would create a cart session | Manual test on the live site |
| Security headers, CSP, TLS grade | Not reachable from here | securityheaders.com, SSL Labs, Mozilla Observatory |
| Cross-browser rendering | No other engines available | BrowserStack / real Safari + Firefox |

**Nothing in this report is guessed.** Every "confirmed" item has tool output or source lines behind it; anything unverifiable is labelled *Not tested* or *Potential*.

---

## 3. Critical issues (P0 blockers)

### AUD-01 — The entire design-token block is discarded by the browser; theme settings have no effect

**Severity:** Blocker · **Confidence:** Confirmed (validator + real-browser reproduction)

**What happens:** `layout/theme.liquid` wraps its token declarations in `{% style %}` and pipes `font_modify` results into the `font_face` filter. On the live store two of those filters fail, and Shopify prints the error *as CSS*:

```
<style data-shopify>
    Liquid error (layout/theme line 44): font_face can only be used with a font drop

    Liquid error (layout/theme line 47): font_face can only be used with a font drop

    :root{
      --font-heading: Assistant, sans-serif;
      …
      --shadow-lg: 0 24px 64px rgba(16, 16, 32, .14);
    }
  </style>
```
*(verbatim, W3C Nu "source" view of https://learn.dartsai.in/cart, lines 30–66)*

The CSS parser reads `Liquid error (…) : font_face …` as a **selector** and then swallows the whole `:root{…}` block as that selector's declaration block. The rule is invalid and is dropped.

**Reproduced in Chromium 153** with the exact live text:

| Case | `--c-accent` | `--page-width` | `--shadow-lg` | Computed `background: var(--c-accent, #4f2fd6)` |
|---|---|---|---|---|
| A — live condition (errors present, `#4f2fd6`) | **EMPTY** | **EMPTY** | **EMPTY** | `rgb(79, 47, 214)` (fallback) |
| B — errors removed | `#4f2fd6` | `1200px` | `0 24px 64px …` | `rgb(79, 47, 214)` |
| C — merchant sets accent to `#ff0000`, errors present | **EMPTY** | **EMPTY** | **EMPTY** | `rgb(79, 47, 214)` ← **should be red** |

**Impact:** every Theme Editor design setting is silently ignored — accent/ink/surface colours, heading + body fonts, type scale, corner radius, page width, section spacing, shadows. The storefront still *looks* correct only because `theme.css` carries identical fallbacks in every `var()` (352 of 352 `var()` calls have fallbacks, 0 bare). The moment you change a colour or a font, nothing happens. Secondary impact: the intended `@font-face` for the failed variants is missing, so some bold/italic text renders with a substituted face.

**Root cause (source):** `layout/theme.liquid` lines 46–51 pass unguarded values to `font_face`. `font_modify` returns **nil** when the chosen font has no such variant (Assistant has no true "bolder" and no italic in Shopify's family), and `nil | font_face` raises exactly this error. Exactly two errors appear, which rules out a bad font handle (that would fail all six calls).

**Fix (4 lines, v18):**
```liquid
assign heading_font_bold  = heading_font | font_modify: 'weight', 'bold'   | default: heading_font
assign heading_font_black = heading_font | font_modify: 'weight', 'bolder' | default: heading_font_bold
assign body_font_bold     = body_font  | font_modify: 'weight', 'bold'    | default: body_font
assign body_font_italic   = body_font  | font_modify: 'style', 'italic'   | default: body_font
```
**Acceptance test after deploy:** (1) Nu validator → the `CSS: Parse Error` must disappear from all pages; (2) DevTools console → set a colour in the Theme Editor and confirm the computed value changes; (3) `getComputedStyle(document.documentElement).getPropertyValue('--c-accent')` must return a value, not `""`.

---

## 4. Functional issue register

> Severity scale: **Blocker** (must fix before traffic) · **Critical** (legal/trust or revenue) · **High** · **Medium** · **Low**

| ID | Sev | Issue | Reproduction | Expected | Actual | Fix |
|---|---|---|---|---|---|---|
| AUD-01 | Blocker | Design tokens dropped; settings dead (details §3) | Open any page → DevTools → `getComputedStyle(document.documentElement).getPropertyValue('--c-accent')` | `#4f2fd6` | `""` (empty) | Guard `font_modify` with `default:` (§3) |
| AUD-02 | Critical | Refund policy missing while "7-day refund" is promised | `GET /policies/refund-policy` | Refund policy page | `404 Not Found` | Shopify admin → Settings → Policies → fill **Refund**, **Terms of service**, **Shipping** (or change the PDP claim) |
| AUD-02b | Critical | Terms of service 404 | `GET /policies/terms-of-service` | Terms page | `404` | Same as above |
| AUD-02c | High | Shipping/fulfilment policy 404 | `GET /policies/shipping-policy` | Policy page | `404` | Same (for a course, "instant access, no shipping" is the right content) |
| AUD-03 | High | PDP testimonials show placeholder authors | Open the PDP → "What students say" | Three real names | All three read **"Student name"** (initial "S") | Theme Editor → product template → Testimonials → enter real names, or hide the section until quotes exist. *(Source: `templates/product.json` blocks ship `"author": "Student name"`; the homepage blocks were filled in, the PDP ones were not.)* |
| AUD-04 | High | "Contact us" button 404s | Open `/pages/data-sharing-opt-out` → click "Contact us" | Contact page or WhatsApp | `…/pages/https%3A%2F%2Fwa.me%2F917012045854%3Ftext%3D…` → **404** | Clear the Main-page section's "Contact page" setting (the snippet then falls back to WhatsApp automatically) or point it at `/pages/contact`. Harden `snippets/contact-link.liquid` to reject values that are not `http(s)://`, `mailto:`, `tel:` or a leading `/` |
| AUD-05 | High | Instructor photo has no `alt` | Homepage → view source → search `instructor__img` | Descriptive alt | `<img … class="instructor__img" …>` — **no alt attribute** (Nu error, line 689) | In `sections/instructor.liquid:25` replace `section.settings.name` with `section.settings.heading` (the section has **no** `name` setting — that is the bug), and add media alt text in the theme editor |
| AUD-06 | Medium | Invalid boolean attribute on the hero video | Homepage → view source → search `playsinline` | `playsinline` | `playsinline="true"` (Nu: *Bad value "true" for attribute "playsinline"*) | In `sections/video.liquid:76` pass `playsinline: 'playsinline'` or drop the key (browsers accept all three forms, but only empty/`playsinline` is valid) |
| AUD-07 | Medium | `aria-label` on a role-less `div` (site-wide) | View source → `site-footer__pay` | A role on the element, or visually-hidden text | `The "aria-label" attribute must not be specified on any "div" element unless the element has a "role" value…` (Nu, every page) | In `sections/footer.liquid:109` add `role="group"` (keeps the accessible name "Secure payment methods") |
| AUD-08 | Medium | Malformed third-party snippet in the privacy-choices page body | `GET /pages/data-sharing-opt-out` → view source | Valid absolute URLs, one charset | `href="https:////cdn.shopify.com/…/data-sale-opt-out.css"`, `src="https:////cdn.shopify.com/…/data-sale-opt-out.js"`, plus a **second `<meta charset>` inside the body** (4 Nu errors) | Remove the pasted snippet from the page content and use Shopify's built-in "Privacy choices" page feature instead; if Shopify auto-injects it, raise it with Shopify support |
| AUD-09 | Medium | Product description hygiene | `GET /products/ai-shopify-business-bootcamp.json` → `body_html` | Clean HTML | Google-Docs paste artefacts (`data-start`, `data-end`, `class="PDq2pG_selectionAnchorContainer"`, empty `<span>`), a bare **`<h3>`** in a page whose only H1 is the product title (heading-level skip H1→H3), and **no images at all** in a 15-class course description | Re-type or clean the description; add 2–3 real images; keep headings at H2 under the product title |
| AUD-09b | Low | Product media have no alt text | Product JSON → `"alt": null` | Descriptive alt | Theme falls back to the product title, so markup stays valid, but the image vocabulary is wasted | Set alt text on the product media in Shopify admin |
| AUD-10 | Medium | Product/brand naming is inconsistent | Compare `<title>`/H1/heros across pages | One name | Homepage + ads + WhatsApp CTA say **"AI × Shopify Business Bootcamp"**; the PDP `<title>`, H1 and the sticky bar say **"AI Shopify Launch Masterclass"** | Rename the product to "AI × Shopify Business Bootcamp (Launch Masterclass)" or align the hero/CTAs. Ad-to-landing-page mismatch costs conversion |
| AUD-11 | Low | Homepage `<title>` is 79 chars with three brands | `GET /` → `<title>` | ~50–60 chars | `AI × Shopify Business Bootcamp \| DARTS AI Academy \| Roshanshaji.com – Darts Ai Academy` | Shorten to `AI × Shopify Business Bootcamp — DARTS AI Academy`; remove the duplicated store-name suffix (the theme appends `– shop.name` unless the title already contains it) |
| AUD-12 | Low | `og:image` served over `http://` while `og:image:secure_url` is `https://` | Homepage → `<meta property="og:image">` | `https://` | `http://learn.dartsai.in/cdn/…` | Emit the `https://` form in `snippets/meta-tags.liquid` |
| AUD-13 | Low | Empty blog is in the sitemap | `/blogs/news` → "No articles yet."; listed in `sitemap_blogs_1.xml` | Either content or noindex | Indexable empty page | Publish 1–2 posts (best: "How the 15 classes work", "What you'll launch in 30 days") or unpublish the blog |
| AUD-14 | Info | Platform-injected markup errors (not theme, not merchant-actionable) | Nu on `/cart`, `/` | — | `<link rel="ucp" … version="2026-08-25">` (invalid attribute), `<script type="module" defer>` (both Shopify-injected), `charset` after byte 1024 (Shopify's event-observer script is injected above your `<meta charset>`), and Shopify's `video_tag` poster `<img>` without alt | Document; raise with Shopify if it matters to you. Nothing to change in the theme |

### Verified working (so you know what *not* to touch)

* Express "Buy it now" + quick-checkout panel + payment chips + "Instant access after payment" — present on the PDP.
* `requires_shipping: false` on the selling variant — correct for a digital course (no shipping options will be requested at checkout).
* Sale pricing renders correctly everywhere (`Rs. 2,999.00` vs `Rs. 7,500.00`, "Sale" tag on cards).
* Countdown, "Founding cohort · First 25 students only", WhatsApp CTA, announcement bar: all live on every page.
* Zero-result and one-result search states both render with a recovery CTA.
* Cart page + drawer empty states render; recovery links point to `/products/…`.
* Built-in 404 page is branded ("Page not found" + back-to-home + browse-the-course).

---

## 5. Per-page UX assessment

*Text-level assessment only — no visual, hover, animation or touch testing was possible from this environment.* Scores are relative, not absolute.

| Page | Score | What works | What drags it down |
|---|---|---|---|
| `/` Homepage | 8.5 | Clear hero promise, countdown, pricing anchor, curriculum, instructor, real testimonials, FAQ, sticky CTA | Instructor photo has no alt; title/branding muddle (AUD-11) |
| PDP | **7.0** | Strong structure: price/urgency, express checkout, assurance panel, refund line, curriculum | **"Student name" ×3** (AUD-03); name mismatch (AUD-10); description has no images and a heading skip (AUD-09); refund promise without a policy (AUD-02) |
| `/collections/all` | 8.0 | Clean single-product grid, sale tag, one-tap add | Collection called "Products" while the store sells one course |
| `/cart` | 8.0 | Calm empty state, obvious recovery CTA | Nothing material |
| Search (1 result / 0 results) | 8.5 | Correct counts, product cards, recovery CTA on empty | No search suggestions on the empty state |
| `/pages/contact` | 8.5 | WhatsApp + email + studio address, labelled form, topic dropdown, privacy note | No phone number; form submission untested |
| `/policies/privacy-policy` | 8.0 | Complete, dated, links the opt-out page | Its sibling policies are missing (AUD-02) |
| `/pages/data-sharing-opt-out` | **5.5** | Correct content and hCaptcha protection | **Broken "Contact us"** (AUD-04) + malformed injected snippet (AUD-08) |
| `/blogs/news` | n/a | Renders an empty state | Empty blog indexed (AUD-13) |
| 404 | 8.0 | Branded, two clear exits, search available | None |

---

## 6. Responsive design

**Status: Not tested on the live site.** The audit environment cannot resize a viewport or emulate a device, so any claim about breakpoints, tap-target size, overflow or mobile navigation would be invented.

What can be said with evidence:
* The v17 build was verified locally at **390 px and 1440 px across 11 page types** in the build gate (clean screenshots, no horizontal overflow, no console errors).
* Markup is mobile-first (`viewport-fit=cover`, `clamp()` spacing throughout `theme.css`).
* WCAG 2.2 "Target Size (Minimum) 24×24" could not be measured — needs a browser.

**Manual check to run (10 minutes):** iPhone SE (375×667), iPhone 15 (393×852), Pixel 7, iPad mini, 1280 px and 1920 px laptops — verify: no horizontal scroll, sticky bar doesn't cover the buy button, video doesn't overflow, tap targets ≥ 24×24 px, drawers and menus close correctly, and text stays readable at 200 % zoom.

---

## 7. Accessibility (WCAG 2.2 AA)

**Status: Partial.** Only markup-level criteria could be checked; everything requiring interaction or computed styles is marked untested.

### Confirmed failures

| WCAG | Finding | Evidence |
|---|---|---|
| 1.1.1 Non-text Content | Instructor photo has no `alt` (AUD-05) | Nu: *An "img" element must have an "alt" attribute* — homepage line 689 |
| 4.1.2 / 1.3.1 | `aria-label` on a role-less `div` in the footer (site-wide) (AUD-07) | Nu on every page: *The "aria-label" attribute must not be specified on any "div" element unless the element has a "role" value…* |
| 1.3.1 Info & Relationships | 1 heading-level skip on the PDP (H1 → H3 inside the description) (AUD-09) | Product JSON `body_html` contains `<h3 …>` with no H2 before it |

### Positive markup findings

* `<html lang="en">` set; `<main id="MainContent" role="main" tabindex="-1">` present with a "Skip to content" link on every page.
* Forms on the contact page use real `<label for>` elements (verified in page text).
* The cart page has a single H1; the homepage hero H1 is unique.
* The `role="list"` attributes Nu flags as "unnecessary" are a **deliberate Safari/VoiceOver workaround** (a `list-style:none` list loses its list semantics there) — keep them; they are not a defect.
* Nu's "Section lacks heading" warnings (tools strip, stats strip) are decorative bands — informational only.

### Not tested (must be run with axe + a screen reader)

Keyboard reachability and focus order · visible focus indicators · colour contrast of every token pair (the theme targets 4.5:1 but this was not measured) · screen-reader announcement of the video, drawer, and quick-checkout panel · 200 % zoom/reflow · reduced-motion behaviour · form error messaging · `Target Size (Minimum) 24×24`.

**Recommended acceptance run:** axe DevTools (0 critical/serious) + a 15-minute NVDA or VoiceOver pass on the homepage, PDP and cart.

---

## 8. Security (partial — configuration not measurable from here)

| Check | Result | Evidence |
|---|---|---|
| HTTPS everywhere | ✅ | All canonical/og/twitter URLs are `https://`; one `og:image` is `http://` (AUD-12) |
| Mixed content | ✅ | No `http://` sub-resources found in the rendered head |
| Secrets in markup | ✅ | Only the expected public storefront token (`shopify-features` accessToken) — platform-standard; no API keys, no admin tokens, no credentials |
| Customer data exposure | ✅ | No customer data in any fetched page; cart/checkout require their own session |
| Form spam protection | ✅ | hCaptcha is loaded by Shopify for the contact/opt-out forms (verified in the opt-out page markup) |
| Privacy posture | ⚠️ | Privacy policy + opt-out page exist, but the opt-out widget's injected CSS/JS URLs are malformed (AUD-08) and the refund/terms policies are missing (AUD-02) |
| **Not tested** | — | HTTP security headers (HSTS, CSP, `X-Frame-Options`, `Referrer-Policy`, Permissions-Policy), TLS grade, cookie flags, rate limiting, admin/API exposure, Shopify account hardening (2FA, staff roles) |

**Actions:** run securityheaders.com + SSL Labs on `learn.dartsai.in`; enable 2FA on the Shopify owner account; keep checkout settings on Shopify-managed payments; do not paste third-party snippets into page bodies (AUD-08 is exactly that failure mode).

---

## 9. Performance

**Status: Not measured — no field or lab metric was obtainable.**
PageSpeed Insights API returned **HTTP 429, `quota_limit_value: 0`** (daily quota exhausted for the consumer project), and the audit environment cannot run a browser against the live site. **No LCP/CLS/INP/TBT number in this report is estimated** — do not publish numbers from this audit.

What *was* measured:

| Asset | Size (uncompressed) |
|---|---|
| `assets/theme.css` | 75,370 B (single file, no CSS imports) |
| `assets/theme.js` | 36,307 B (single file, no framework) |
| Theme total | 653 KB / 78 files |
| External CSS/JS from the theme | **none** (no jQuery, no analytics SDK of your own, no font CDN) |

Structural observations from the rendered head (lines 3–133 of the live source):
* Shopify injects ~15 script blocks before your content (event-observer bootstrap, `load_feature`, shop-js module loaders, origin trials, MCP adapter, `preloads.js`) — this is platform overhead shared by every Shopify store and is not theme-tunable.
* The hero video uses `preload="auto"` + `autoplay` and is served from Shopify's CDN; the poster is a 1400 px JPEG. This is the most likely LCP/bandwidth cost on the homepage — consider `preload="metadata"` if LCP proves slow (measure first).
* No render-blocking third-party CSS was found.

**Required to close this section:** PageSpeed Insights (mobile + desktop), Lighthouse in an incognito Chrome, and CrUX field data for the URL. Then decide about video preload.

---

## 10. SEO

### Working well

* Canonical tag on every page; `og:*` + `twitter:*` with a 1200×630 image and `og:image:alt`.
* `robots.txt` = Shopify defaults + explicit **agent/UCP directives** (`/agents.md`, `/.well-known/ucp`, `/api/ucp/mcp`), with a correct `Sitemap:` line and the standard crawl-trap disallows (filters, sorts, `?ls=`).
* `sitemap.xml` is a valid **sitemap index** → products / pages / collections / blogs / agentic-discovery.
* Product **and** breadcrumb structured data are shipped by the theme (v17: `Product`, `VideoObject`, `BreadcrumbList`, `Organization`, `WebSite`) and were verified in the local render gate.
* Every template renders exactly one H1 by construction; the collection/blog headers are present in the live markup (`</header><ul class="product-grid">` proves the header block renders).

### Issues

| Sev | Issue | Fix |
|---|---|---|
| Medium | 79-character, triple-brand homepage title (AUD-11) | Shorten; keep one brand token |
| Medium | Product name ≠ campaign name (AUD-10) — search users and ad clickers see two different products | Rename the product |
| Low | Empty `/blogs/news` is indexable and in the sitemap (AUD-13) | Publish or unpublish |
| Low | `og:image` over `http://` (AUD-12) | Emit the `https://` URL |
| Low | Product description has no internal links, no images, weak keyword coverage for "Shopify course Kerala / Malayalam" | Rewrite the description with 2–3 images and one internal link to the contact page |

**Not tested:** keyword rankings, backlinks, indexation status (Search Console is not available to this audit), rich-result eligibility (Google's Rich Results Test requires a POST + browser), hreflang/international targeting (this is a single-locale `en` store — no hreflang needed).

---

## 11. Browser compatibility

**Status: Not tested across engines.** No Safari/Firefox/Edge runtime was available, and the live site could not be driven from a browser here.

Evidence that *should* translate well:

| Signal | Value |
|---|---|
| Markup validation | Valid HTML5 except 4 theme-side issues (§4) — no deprecated elements, no quirks-mode triggers (`<!doctype html>`, `<meta charset>`, `X-UA-Compatible`) |
| CSS approach | Custom properties + `clamp()` + flex/grid; **every** `var()` has a fallback (352/352) → graceful degradation |
| Feature usage | `content-visibility`/`IntersectionObserver`/`aspect-ratio` are all baseline-modern (2020+); no proprietary prefixes required |
| JS | Vanilla ES2015+, no framework, no polyfill dependence; `no-js` class swap is progressive |
| Known risk | Safari's `list-style:none` list semantics workaround is already applied (`role="list"`); `backdrop-filter`/`mix-blend-mode` on the aurora and blur effects can be expensive on older iOS — worth a visual check |

**Matrix to run before launch:** Chrome + Safari (iOS 17+) + Firefox + Edge, at 390 px and 1440 px — homepage, PDP, cart, search, contact form.

---

## 12. Action plan (P0 → P3)

### P0 — before paid traffic (same day, ~2 hours)

1. **AUD-01** — Patch `layout/theme.liquid` (4 `default:` guards, §3), re-run the build gates, ship as v18, then confirm with the Nu validator that the `CSS: Parse Error` is gone **and** that `--c-accent` resolves in DevTools. *(Blocker)*
2. **AUD-02 / 02b / 02c** — Fill Refund, Terms and Shipping policies in Shopify admin (or remove the "7-day refund" promise from the PDP and the assurance panel). *(Critical)*

### P1 — trust and conversion (same week, ~1 hour)

3. **AUD-03** — Replace the three "Student name" testimonials on the PDP with real names, or hide the section.
4. **AUD-04** — Fix/clear the "Contact page" setting on the data-sharing-opt-out page; harden `contact-link.liquid`.
5. **AUD-05** — Fix the instructor `alt` (`section.settings.heading`) and set real image alt text. *(Ships in the same v18 patch.)*

### P2 — quality and validity (this month)

6. **AUD-06 / AUD-07** — `playsinline` + footer `role="group"`. *(Same v18 patch — both are one line.)*
7. **AUD-08** — Remove the malformed injected snippet from the opt-out page body.
8. **AUD-09 / 09b** — Clean the product description (Google-Docs artefacts, H1→H3 skip) and add images + media alt text.
9. **AUD-10** — Align the product name with the campaign name.
10. Run the accessibility acceptance pass (axe + screen reader) and the responsive matrix (§6, §11).

### P3 — polish and measurement

11. **AUD-11** — Shorten the homepage title.
12. **AUD-12** — `https://` og:image.
13. **AUD-13** — Publish or unpublish the blog.
14. Run PageSpeed Insights + Lighthouse and record real Core Web Vitals; revisit the hero video's `preload`.
15. Add two build gates: fail on the string `Liquid error` in rendered output; enable Shopify's `UndefinedObject` check (§2.3).
16. Rename the live theme from `darts-ai-shopify-bootcamp-v25-reverted` to a release name that matches the deployed version (v17.0.0 today) so deployments stay auditable.

---

## 13. Release checklist

| # | Gate | Status |
|---|---|---|
| 1 | Homepage, PDP, collection, cart, search, contact, 404 all return 200 and render their core content | ✅ Verified |
| 2 | Pricing, sale price and "Add to cart"/express checkout render correctly | ✅ Verified (variant `49228679119031`, `requires_shipping: false`) |
| 3 | Countdown matches the announced start time | ✅ Verified (01d 12h 33m → 2026-10-01 21:00 IST) |
| 4 | Design tokens resolve in a real browser (theme settings work) | ❌ **AUD-01** |
| 5 | Refund / Terms / Shipping policies exist and are linked | ❌ **AUD-02** |
| 6 | No placeholder content anywhere a buyer can see | ❌ **AUD-03** (PDP testimonials) |
| 7 | No dead links or buttons | ❌ **AUD-04** (one confirmed 404 button); ⚠️ nav + footer links unverified from here |
| 8 | All images have appropriate alt text | ❌ **AUD-05**; ⚠️ product media alt empty |
| 9 | W3C validation: theme-side errors = 0 | ❌ 4 theme-side errors (AUD-05/06/07 + CSS) |
| 10 | Shopify `theme-check` clean on the shipped zip | ✅ 0 errors / 0 warnings on v17 (**but it did not catch AUD-01/AUD-05** — see §2.3) |
| 11 | Search works with results and without | ✅ Verified |
| 12 | Cart add → cart page → checkout handoff | ⚠️ **Not tested** (read-only mandate) |
| 13 | Contact + opt-out forms submit and reach you | ⚠️ **Not tested** (would send real messages) |
| 14 | Checkout completes with a real payment method | ⚠️ **Not tested** (no order may be placed) |
| 15 | Mobile/tablet/desktop layout, no horizontal scroll | ⚠️ **Not tested live** (v17 verified locally at 390/1440 px) |
| 16 | Keyboard + screen-reader pass, contrast, zoom 200 % | ⚠️ **Not tested** |
| 17 | Core Web Vitals within budget | ⚠️ **Not measured** (PSI quota 0) |
| 18 | Security headers + TLS grade | ⚠️ **Not tested** |
| 19 | Cross-browser smoke test | ⚠️ **Not tested** |
| 20 | Live theme name/version matches the audited release | ❌ Live theme is named `darts-ai-shopify-bootcamp-v25-reverted` while the code marker says v17.0.0 |

---

## Appendix A — Inputs I still need from you

The audit template fields were left blank. These change the conclusions, so please fill them in:

1. **Technology stack** — confirmed as Shopify + Liquid theme v17; is anything else in play (apps, custom checkout extensions, email/automation tools)?
2. **Target users** — Indian students? Malayalam/English/Hindi speakers? Complete beginners? (Affects whether the missing Malayalam content and the WhatsApp-first support model are right.)
3. **Primary purpose / conversion goal** — one-time ₹2,999 enrolment for the October cohort, or a funnel into a higher-priced programme?
4. **Key user flows to certify** — I inspected: home → PDP → express checkout entry, collection → PDP, search, cart, contact. Are there others (coupon flows, EMI, WhatsApp follow-up, refund requests)?
5. **Languages** — store is `en` only; the footer promises "Support in Malayalam, English & Hindi". Should the storefront itself be translated?
6. **Authentication** — is a customer account required? (The theme ships Dawn-style customer templates, but the store currently sells guest checkout.)
7. **Test account** — **none was provided.** Provide one (plus a test payment method or a Shopify Payments test mode) if you want the checkout, account and order-email flows verified.
8. **Environment** — is `learn.dartsai.in` the production environment? Is there a theme preview/staging URL I may inspect?

With a test account and a staging URL I can convert checklist items 12–14 from "not tested" into verified results.
