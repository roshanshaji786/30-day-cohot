#!/usr/bin/env python3
"""Generate the Shopify product import CSV for the bootcamp."""
import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))

description = """<p><strong>Fifteen live evening classes where you use AI to research a niche, build a real Shopify store, and get it ready to sell — with personal feedback from your instructor.</strong></p>
<p>This is not a recorded video library you watch alone. It is a small live cohort that meets at 9:00 PM IST on Google Meet, and every class is a screen-share build you follow on your own store. You finish with a live, mobile-ready store and a launch checklist, not a folder of notes.</p>

<h3>Who this is for</h3>
<ul>
  <li>Complete beginners — no coding, no design skills, no prior business experience</li>
  <li>Anyone who has a store sitting half-finished and wants to finally launch it</li>
  <li>Freelancers, students and shop owners across India who want an AI-powered workflow</li>
  <li>Anyone who prefers learning in Malayalam or English with room to ask questions</li>
</ul>

<h3>What you build, phase by phase</h3>
<p><strong>Phase 1 — Find a niche that actually sells (4 classes).</strong> Use AI to map trending niches and buyer intent, validate demand before spending a rupee, choose products with healthy margins, and design a brand angle that stands out. Outcome: a validated niche and a product shortlist.</p>
<p><strong>Phase 2 — Build the store with AI (7 classes).</strong> Shopify setup, domains and payments; theme structure, sections and mobile layout; product pages, copy and descriptions written with AI; product photography and image generation; apps, email capture and abandoned-cart flows; SEO basics; speed, trust and legal pages. Outcome: a live, mobile-ready Shopify store.</p>
<p><strong>Phase 3 — Launch, traffic and first orders (4 classes).</strong> Meta and Google ad foundations, UGC and creative testing with AI tools, an organic content playbook for Instagram, reading analytics and fixing leaks, and scaling what works. Outcome: a launch checklist and your first campaign ready to run.</p>

<h3>What is included</h3>
<ul>
  <li>15 live classes on Google Meet, 9:00 PM IST, with live Q&amp;A in every session</li>
  <li>Lifetime access to every recording, posted within 24 hours</li>
  <li>The AI prompt library used in class — niche research, copy, product pages and ads</li>
  <li>Personal feedback: the cohort is small, so your store gets reviewed live</li>
  <li>Pre-launch and first-orders checklist</li>
  <li>Private community for questions and accountability after the course</li>
  <li>Certificate of completion</li>
</ul>

<h3>How it works</h3>
<ul>
  <li><strong>Format:</strong> live online classes, 60–90 minutes each, plus recordings</li>
  <li><strong>Language:</strong> Malayalam and English, with Hindi support in Q&amp;A</li>
  <li><strong>Time needed:</strong> about 6–8 hours a week, including practice</li>
  <li><strong>What you need:</strong> a laptop, a stable internet connection, and a domain when you are ready to launch</li>
  <li><strong>Access:</strong> course links are emailed within minutes of payment</li>
</ul>

<h3>Honest expectations</h3>
<p>You will be taught a repeatable process and you will build a real store. What you earn depends on your product, your effort and the market — this course does not promise or guarantee any specific income, revenue or profit. If the first two classes are not right for you, ask within 7 days for a full refund.</p>"""

HEADERS = [
    "Handle", "Title", "Body (HTML)", "Vendor", "Type", "Tags", "Published",
    "Option1 Name", "Option1 Value", "Variant SKU", "Variant Inventory Tracker",
    "Variant Inventory Qty", "Variant Inventory Policy", "Variant Fulfillment Service",
    "Variant Price", "Variant Compare At Price", "Variant Requires Shipping",
    "Variant Taxable", "Gift Card", "SEO Title", "SEO Description",
    "Variant Weight Unit", "Cost per item", "Status",
]

ROW = [
    "ai-shopify-business-bootcamp",
    "AI \u00d7 Shopify Business Bootcamp",
    description,
    "DARTS AI Academy",
    "Course",
    "shopify, ai, course, live cohort, ecommerce, dropshipping, online course, malayalam, kerala, bootcamp",
    "TRUE",
    "Title",
    "Default Title",
    "BOOTCAMP-COHORT",
    "shopify",
    "25",
    "deny",
    "manual",
    "2999",
    "5000",
    "FALSE",
    "TRUE",
    "FALSE",
    "AI \u00d7 Shopify Business Bootcamp \u2014 Live Online Course (15 Classes)",
    "Live 15-class cohort: use AI to research a niche and build a real Shopify store, step by step. "
    "Small group, personal feedback, recordings you keep.",
    "kg",
    "",
    "active",
]


def main():
    out = os.path.join(HERE, "product-import.csv")
    with open(out, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, quoting=csv.QUOTE_ALL)
        writer.writerow(HEADERS)
        writer.writerow(ROW)

    with open(out, encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1, "expected a single product row"
    assert rows[0]["Handle"] == "ai-shopify-business-bootcamp"
    assert rows[0]["Variant Price"] == "2999"
    assert rows[0]["Variant Requires Shipping"] == "FALSE"
    assert rows[0]["Published"] == "TRUE"

    print("product-import.csv written")
    print("  columns :", len(HEADERS))
    print("  title   :", rows[0]["Title"])
    print("  price   :", rows[0]["Variant Price"], "| compare-at:", rows[0]["Variant Compare At Price"])
    print("  stock   :", rows[0]["Variant Inventory Tracker"], rows[0]["Variant Inventory Qty"],
          "| policy:", rows[0]["Variant Inventory Policy"])
    print("  shipping:", rows[0]["Variant Requires Shipping"], "(digital product)")
    print("  body    :", len(rows[0]["Body (HTML)"]), "chars of HTML")


if __name__ == "__main__":
    main()
