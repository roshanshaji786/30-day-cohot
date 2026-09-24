# Content pack — the 6 things that make the page convert

The theme is complete. These are the assets and words that go into it. Everything here maps to a slot that
already exists in the theme editor, so there is nothing to code.

Work top to bottom: 1 and 2 unlock the most, 6 the least.

---

## 1. Testimonials — replace the 3 placeholders

**Where:** Theme editor → Home page → *Testimonials* section → each *Testimonial* block.
**Why it matters most:** for a ₹2,999 live course, proof outweighs every other element on the page.

### Ask past workshop attendees this (copy-paste)

> WhatsApp / Email template

```
Hi [NAME]! I'm putting together the page for the next cohort of the AI × Shopify
Bootcamp and I'd love to feature you.

Three quick questions — one or two lines each is plenty:
1. What were you stuck on before the workshop?
2. What changed after it — what did you actually build or launch?
3. Would you recommend it to someone starting from zero?

If you're comfortable, send a photo I can use, and tell me how you'd like to be
credited: "Full name · City" or just a first name. Also happy to link your store.

No pressure at all if you'd rather not — and thank you either way.
```

### How to write the block once you have answers

| Field | Guidance |
|---|---|
| Quote | Keep the student's own words. 20–35 words. One specific outcome beats three adjectives. |
| Name | Full name if permitted. "Student name" is worse than nothing — never ship it. |
| Role or city | `Kochi · First cohort` builds more trust than a job title. |
| Photo | Square headshot, 200×200 minimum, face fills the frame. No photo? Use a first initial — the theme handles it. |
| Rating | Only if the student actually rated it. |

**Third-party placements:** the *Testimonials* section also accepts app blocks, so if you later install a
reviews app (Judge.me, Loox, Junip) you can drop it in without touching code.

### Screenshot row (the strongest proof you can show)

**Where:** same section → *Student stores* → 4 image slots.
Ask 4 students to send a screenshot of their **live store homepage on a phone**.

- Take the screenshot at phone width so it looks like a phone, not a stretched desktop page.
- Blur or crop any customer name, order number, email or revenue figure.
- Crop to roughly **16:10**; the theme scales whatever you give it.
- Name the file `student-store-1.jpg` … `student-store-4.jpg` before uploading.
- Add real alt text in the image alt field, e.g. `Student Shopify store selling handmade soaps`.

---

## 2. Instructor photo and hero image

**Where:** Theme editor → *Instructor* section → Photo; *Hero* section → Hero image.

| Slot | Size to upload | Notes |
|---|---|---|
| Instructor photo | **800 × 1000** (portrait 4:5) | Face in the upper third. Shot at chest height or closer. Plain or softly blurred background. The theme crops around the face using the *Photo crop* setting — set it to Top if your head sits high in the frame. |
| Hero image | **1200 × 1500** (portrait 4:5) | You teaching, at a desk, or beside a screen showing a store. Avoid stock photos and screenshots with unreadable text. |
| Social share image | **1200 × 630** | Used for the WhatsApp/LinkedIn/X link preview. Heading text large enough to read on a phone. |
| Logo | PNG with transparent background, ~400px wide | The header displays it at up to 130px wide; the footer shows it in white space, so make sure a dark logo works on a light background — or leave the logo empty and keep the built-in monogram + wordmark. |
| Favicon | **32 × 32** PNG | The small icon in the browser tab. |

Leave any of these empty and the theme shows a designed placeholder — never a broken or empty box.

---

## 3. The 90-second demo video

**Where:** *Video / walkthrough* section. Upload to Shopify (best: automatic poster and correct aspect
ratio) or paste a YouTube/Vimeo link.

Upload a **landscape 16:9** recording. The theme letterboxes instead of cropping, so a screen-share stays
readable on a phone. External videos load only when tapped, so mobile visitors pay no data cost up front.

### Shot list (record your screen with Loom, OBS, or QuickTime)

| # | Seconds | On screen | Say |
|---|---|---|---|
| 1 | 0–8 | Your face, or a title card | "Here's exactly what you'll build in the bootcamp — in two minutes." |
| 2 | 8–25 | ChatGPT: niche research prompt | "Class 1: I paste one prompt and we narrow 50 niches down to 3 worth testing." |
| 3 | 25–45 | Shopify admin → theme editor | "Then we build. Your store, not a demo store — I stay on the call while you do it." |
| 4 | 45–62 | Product page being written with AI | "This product page took four minutes. Copy, images and SEO fields included." |
| 5 | 62–75 | Storefront on a phone | "And we check it the way your customers will: on a phone, on mobile data." |
| 6 | 75–90 | Pricing card on screen + your face | "15 live classes, small group, recordings you keep. If the first two classes aren't right, ask for a refund within 7 days." |

Rules: no music louder than your voice, no unreadable text, no claiming income. Re-record the intro after
you have a real student store to show — screenshots of a live student store beat any animation.

**Poster image:** for external videos, upload a 1280×720 frame with your face and a big readable title.

---

## 4. Copy you can paste straight in

These are already in the theme's defaults — edit them in the editor rather than re-typing:

- **Hero heading:** `Learn AI, build a Shopify store,` + accent `launch in 30 days.`
- **Eyebrow:** `Founding cohort · First 25 students only` — keep "First 25" only while it's true; the
  theme shows a live seats-left chip from real inventory, so the two must agree.
- **Product description:** already written, ~500 words, in `product-import.csv`. Importing the CSV fills the
  product page, the schema markup and the search result preview in one step.
- **Meta description:** set the SEO title and description on the product (they're in the CSV) and in
  Theme settings → SEO & sharing for the homepage.

---

## 5. Cohort facts to fill in

| Setting | Where | Example |
|---|---|---|
| Cohort start date | Theme settings → Course product | `2026-10-01T21:00:00+05:30` — drives the countdown and the structured data |
| Enrolment closes | Theme settings → Course product | Optional. If blank, the countdown uses the start date |
| WhatsApp number | Theme settings → Contact & social | `919876543210` (digits with country code, no `+` or spaces) |
| Support email | Theme settings → Contact & social | A real inbox you check daily |
| Instagram / YouTube / LinkedIn | Theme settings → Contact & social | Footer icons + `sameAs` in structured data |
| Policies | Settings → Policies | Paste from `setup/policies/` in this repo |
| Seats left | Product → Inventory → Track quantity | The site prints "Only N seats left" under 12, so set the real number |

---

## 6. Launch-week checklist

**Day −3**
- [ ] Product imported (`setup/product-import.csv`), price ₹2,999 / compare-at ₹5,000 verified
- [ ] Track quantity ON, real seat count entered
- [ ] Payment gateway live in test mode, then a real ₹1 test order
- [ ] Policies published, footer links verified by clicking them
- [ ] WhatsApp number and support email set; send yourself a test message from the site

**Day −1**
- [ ] Real testimonial content in (or placeholders removed — never ship "Student name")
- [ ] Instructor photo and hero image uploaded, alt text written
- [ ] Demo video uploaded or linked, poster set
- [ ] Open the site on a real phone on mobile data: buy bar appears, menu opens, video plays
- [ ] Place a real test order end to end, refund it, confirm the refund email arrives

**Day 0**
- [ ] Announcement bar text and countdown checked against the real deadline
- [ ] Social share image set — send the product link to yourself on WhatsApp and look at the preview
- [ ] Google Search Console: submit the sitemap (`/sitemap.xml`) and request indexing
- [ ] Post the launch message (below) on Instagram and WhatsApp status

**Launch caption, ready to paste**

```
The next cohort starts [DATE]. 15 live evening classes where you build your own
Shopify store with AI — not a demo store, yours.

· Small group, so your store gets reviewed live
· Every class recorded, recordings are yours for life
· Malayalam + English, Q&A in Hindi too
· 7-day refund if the first two classes aren't right for you

Seats are limited to keep the group small. Link in bio.
```

**After week 1**
- [ ] Ask every student for the testimonial in section 1 — ask while it's fresh
- [ ] Note the two questions you answered most; add them to the FAQ section as new blocks
- [ ] Add the best student store screenshot to the results row
