# Setup folder — everything that lives in Shopify admin, not in the theme

The theme is code. These files are the store-side setup that code can't do for you.

| File | What it is | Where it goes |
|---|---|---|
| `product-import.csv` | Complete product record: title, handle, price ₹2,999, compare-at ₹5,000, 25 in tracked inventory, digital (no shipping), SEO title + description, and a ~500-word product description | Shopify admin → **Products → Import** |
| `make_product_csv.py` | Regenerates the CSV if you change the copy or price | Run `python3 make_product_csv.py` |
| `policies/refund-policy.md` | 7-day refund policy matching what the theme promises, plus the grievance officer block required by the Consumer Protection (E-Commerce) Rules, 2020 | Settings → Policies → **Refund policy** |
| `policies/privacy-policy.md` | What data you collect, why, who you share it with, retention, and the rights buyers have under the DPDP Act, 2023 | Settings → Policies → **Privacy policy** |
| `policies/terms-of-service.md` | Licence, payment, conduct, IP, **no earnings guarantee**, liability cap, Kerala jurisdiction | Settings → Policies → **Terms of service** |
| `policies/delivery-policy.md` | Digital delivery timings, "no physical shipping", what to do if access doesn't arrive | Settings → Policies → **Shipping policy** |
| `content-pack.md` | Testimonial outreach scripts, image sizes and shot list, a 90-second video script, cohort facts table, launch-week checklist | Work through it manually |

## Order of operations

1. **Import the product** — Products → Import → `product-import.csv`. Check the handle landed as
   `ai-shopify-business-bootcamp` (the theme points at it by default).
2. **Turn on inventory tracking** for the variant and set the real seat count. The "Only N seats left" chip
   and the sticky buy bar read this number; with tracking off, the claims simply don't render.
3. **Publish the four policies** — copy the text out of each `.md` file, replace every `[BRACKET]`, paste
   into the matching policy editor, save. The footer, contact page and structured data link to them
   automatically once they exist.
4. **Theme settings** → Course product, Contact & social, SEO & sharing, Logo & icons.
5. **Content** → work through `content-pack.md` (testimonials first).
6. **Test** → place a real order, then refund it, and confirm both emails arrive.

## About the policy drafts

They are written to match this specific business — a digital course sold in India, delivered over Google
Meet and WhatsApp, with a 7-day refund promise the theme repeats on-page. Placeholders look like
`[EMAIL]`, `[GSTIN]`, `[FULL POSTAL ADDRESS]`, `[GRIEVANCE OFFICER NAME]`.

Two cautions worth taking seriously:

- **They are drafts, not legal advice.** Have a lawyer or CA review them before launch, especially the
  liability cap and governing-law clauses.
- **Delete what you don't use.** The privacy policy lists common processors (Shopify, payment gateway,
  Google Meet, email tool, WhatsApp, analytics). Listing a processor you don't use is as misleading as
  omitting one you do — trim each list to match reality.

## Why a CSV instead of a checklist

Because "create a product with these 24 fields" is a task you can get subtly wrong — a typo in the handle
breaks every buy button on the site, and forgetting *Track quantity* silently removes the urgency chips.
Importing the CSV makes the handle, price, compare-at, inventory tracking, digital-product flag and SEO
fields exact on the first try.
