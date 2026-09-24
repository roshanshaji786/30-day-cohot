#!/usr/bin/env python3
"""
render_check.py -- MANDATORY pre-delivery gate.

Why this exists
---------------
Static checks are not enough. A theme can parse cleanly, have zero dead links and
100% CSS-class coverage and still render as unstyled Times New Roman in a merchant's
real store. That is exactly what happened once: a Liquid syntax error in the <head>
aborted the render chain, the :root token block never reached the page
block, and every var() in the stylesheet collapsed to its fallback.

So this tool does what a merchant actually does:

  1. renders layout/theme.liquid behaviour -- tokens, jsonld, header group,
     JSON template sections, footer group -- through a real Liquid engine,
  2. writes the page next to the real assets/theme.css and theme.js,
  3. loads every page in a REAL headless Chromium at 1280px AND 390px,
  4. screenshots each page full height,
  5. asserts the things that were actually broken: theme fonts applied (not a serif
     fallback), buttons opaque, cards and accordions visible, theme custom
     properties present and none undefined, valid JSON-LD, no Liquid error text,
     no console errors, no mobile horizontal overflow.

Exit code is non-zero on any failure, and tools/build.py refuses to package a zip.

Run:  PYTHONPATH=/home/user/pylibs python3 theme-v16/tools/render_check.py
"""

import glob
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
THEME = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from verify import (  # noqa: E402
    LINKLIST_STUB, STUB_PRODUCT, STUB_VARIANT, preprocess_liquid, read,
    schema_of, section_defaults, preset_blocks, shopify_settings,
)

OUT = os.environ.get("RENDER_OUT", "/tmp/theme-render")
NODE_DIR = os.environ.get("RENDER_NODE_DIR", "/tmp/btest")
CHROMIUM = os.environ.get("RENDER_CHROMIUM", "/tmp/chromium-bin")
LIBDIR = os.environ.get("RENDER_LIBDIR", "/tmp/al2023x/lib")

problems = []
notes = []

MONEY = "\u20b9{{ amount_no_decimals }}"


def fail(message):
    problems.append(message)


def ok(message):
    print(f"  \u2713 {message}")


# --------------------------------------------------------------------------
# Shopify filter emulation
# --------------------------------------------------------------------------
def make_filters(locale):
    def t(value, *args, **kwargs):
        node = locale
        for part in str(value).split("."):
            if isinstance(node, dict) and part in node:
                node = node[part]
            else:
                return "\u26a0missing:" + str(value)
        if isinstance(node, dict):
            node = node.get("one") or node.get("other") or next(iter(node.values()), "")
        text = str(node)
        for i, arg in enumerate(args):
            text = text.replace("%{" + str(i) + "}", str(arg))
        return text

    def money(value, *a, **k):
        # Shopify money filters receive the price in minor units (paise/cents)
        # and divide by 100 for display.
        try:
            return "\u20b9" + f"{float(value) / 100:,.0f}"
        except (TypeError, ValueError):
            return "\u20b9" + str(value)

    def image_url(img, *a, **k):
        if img in (None, ""):
            return ""
        width = k.get("width") or 1200
        return "assets/course-hero.jpg"

    def image_tag(img, *a, **k):
        if img in (None, ""):
            return ""
        w = int(k.get("width") or 1200)
        h = int(k.get("height") or round(w * 0.66))
        return (f'<img src="assets/course-hero.jpg" alt="{k.get("alt", "")}" '
                f'class="{k.get("class", "")}" width="{w}" height="{h}" '
                f'sizes="{k.get("sizes", "100vw")}" loading="{k.get("loading", "lazy")}" '
                f'decoding="async">')

    return {
        # python-liquid has no `json` filter registered by default and silently
        # passes the value through instead, which emits unquoted JSON-LD and a
        # broken window.themeStrings script. Register the real thing.
        "json": lambda v, *a, **k: json.dumps(v, ensure_ascii=False)
        if not isinstance(v, str) else json.dumps(v, ensure_ascii=False),
        "asset_url": lambda n, *a, **k: "assets/" + str(n),
        "stylesheet_tag": lambda u, *a, **k: f'<link rel="stylesheet" href="{u}">',
        "script_tag": lambda u, *a, **k: f'<script src="{u}" defer></script>',
        "image_url": image_url,
        "image_tag": image_tag,
        "img_url": lambda i, *a, **k: image_url(i, **k),
        "file_url": lambda n, *a, **k: "assets/" + str(n),
        "file_img_url": lambda n, *a, **k: "assets/" + str(n),
        "shopify_asset_url": lambda n, *a, **k: "https://cdn.shopify.com/s/assets/" + str(n),
        "global_asset_url": lambda n, *a, **k: "https://cdn.shopify.com/s/assets/" + str(n),
        "t": t,
        "money": money,
        "money_with_currency": money,
        "money_without_currency": lambda v, *a, **k: f"{float(v) / 100:,.2f}",
        "money_without_trailing_zeros": money,
        "weight_with_unit": lambda v, *a, **k: f"{v} kg",
        "placeholder_svg_tag": lambda *a, **k: (
            '<svg class="placeholder-svg" viewBox="0 0 100 100" width="100" height="100" '
            'role="img" aria-label="Placeholder"><rect width="100" height="100" fill="#e9e3ff"/></svg>'),
        "payment_button": lambda *a, **k: '<button type="button" class="shopify-payment-button__button">Buy now</button>',
        "payment_type_svg_tag": lambda *a, **k: '<svg class="payment-icon" width="38" height="24" role="img" aria-label="card"><rect width="38" height="24" rx="3" fill="#ddd"/></svg>',
        "external_video_tag": lambda *a, **k: '<div class="video-embed"><iframe title="video"></iframe></div>',
        "video_tag": lambda *a, **k: '<video class="video" controls playsinline></video>',
        "media_tag": lambda *a, **k: '<img class="media" src="assets/course-hero.jpg" alt="" width="1200" height="800">',
        "format_address": lambda *a, **k: "",
        "customer_login_link": lambda *a, **k: '<a href="/account/login">Log in</a>',
        "default_pagination": lambda *a, **k: "",
        "time_tag": lambda *a, **k: "",
        "link_to": lambda *a, **k: f'<a href="#">{a[0] if a else ""}</a>',
        "url_encode": lambda v, *a, **k: str(v).replace(" ", "%20"),
        "url_escape": lambda v, *a, **k: str(v).replace(" ", "%20"),
        "strip_html": lambda v, *a, **k: re.sub(r"<[^>]+>", "", str(v)),
        "handleize": lambda v, *a, **k: re.sub(r"[^a-z0-9]+", "-", str(v).lower()).strip("-"),
        "handle": lambda v, *a, **k: re.sub(r"[^a-z0-9]+", "-", str(v).lower()).strip("-"),
        "color_to_rgb": lambda v, *a, **k: "rgb(0,0,0)",
        "color_modify": lambda v, *a, **k: str(v),
        "color_lighten": lambda v, *a, **k: str(v),
        "color_darken": lambda v, *a, **k: str(v),
        "font_face": lambda *a, **k: "",
        "font_url": lambda *a, **k: "",
        "pluralize": lambda count, single, plural=None, **k: (
            plural or single + "s") if abs(int(count or 0)) != 1 else single,
        "date": lambda v, *a, **k: "1 Sep 2026",
    }


# --------------------------------------------------------------------------
# Render the theme
# --------------------------------------------------------------------------
def as_font_object(handle):
    """Shopify's font_picker returns an object, not a string. Modelling this
    matters: {{ font.family }} is what feeds --font-body, and a harness that
    supplies a bare string renders the whole theme in Times New Roman and hides
    real regressions behind a false alarm."""
    if isinstance(handle, dict):
        return handle
    if not isinstance(handle, str) or not handle:
        return {"family": "Assistant", "fallback_families": "sans-serif",
                "weight": 400, "style": "normal", "system": False}
    parts = handle.split("_")
    style, weight = "normal", 400
    if len(parts) > 1 and parts[-1][:1] in ("n", "i", "b"):
        flag = parts[-1]
        style = "italic" if flag.startswith("i") else "normal"
        digits = re.sub(r"[^0-9]", "", flag)
        weight = int(digits) * 100 if digits else 400
        parts = parts[:-1]
    family = " ".join(word.capitalize() for word in "_".join(parts).split("_") if word)
    return {"family": family or "Assistant", "fallback_families": "sans-serif",
            "weight": weight, "style": style, "system": False}


def nil_as_blank(mapping):
    """Shopify treats nil as blank, so `{% if image != blank %}` is false when a
    picker is empty. python-liquid evaluates `None != blank` as TRUE, which
    silently renders the wrong branch (preload link with an empty href instead of
    the section's fallback art). Normalise nils to match the storefront."""
    if not isinstance(mapping, dict):
        return mapping
    return {key: ("" if value is None else value) for key, value in mapping.items()}


def coerce_fonts(theme, settings):
    """Turn every font_picker default into a font object."""
    schema = json.load(open(os.path.join(theme, "config/settings_schema.json"),
                            encoding="utf-8"))
    font_ids = set()
    for group in schema:
        for setting in group.get("settings", []):
            if setting.get("type") == "font_picker" and setting.get("id"):
                font_ids.add(setting["id"])
    for key in list(settings):
        if key in font_ids:
            settings[key] = as_font_object(settings[key])
    return settings


def stage_theme():
    """python-liquid's FileSystemLoader resolves {% render 'x' %} to x.liquid, so
    every snippet and section goes into one flat directory."""
    staging = os.path.join(OUT, "_liquid")
    shutil.rmtree(staging, ignore_errors=True)
    os.makedirs(staging, exist_ok=True)
    for folder in ("snippets", "sections"):
        for path in glob.glob(os.path.join(THEME, folder, "*.liquid")):
            # converted, not copied: snippets pulled in by {% render %} would
            # otherwise hit Shopify-only tags the generic engine cannot parse.
            with open(os.path.join(staging, os.path.basename(path)), "w",
                      encoding="utf-8") as fh:
                fh.write(render_source(read(path)))
    return staging


def render_source(src):
    """Convert Shopify-only tags into something a generic engine can run, without
    losing the markup they wrap."""
    src = re.sub(r"{%-?\s*schema\s*-?%}.*?{%-?\s*endschema\s*-?%}", "", src, flags=re.S)
    src = re.sub(r"{%-?\s*style\s*-?%}", "<style>", src)
    src = re.sub(r"{%-?\s*endstyle\s*-?%}", "</style>", src)
    for tag in ("form", "paginate", "capture", "layout", "javascript"):
        src = re.sub(r"{%-?\s*" + tag + r"\b[^%]*?-?%}", "", src)
        src = re.sub(r"{%-?\s*end" + tag + r"\s*-?%}", "", src)
    src = re.sub(r"{%-?\s*endjavascript\s*-?%}", "", src)
    return src


def snippet_source(name):
    path = os.path.join(THEME, "snippets", name + ".liquid")
    return render_source(read(path)) if os.path.exists(path) else None


def section_ctx(section_id, name, settings, blocks):
    return {
        "id": section_id,
        "settings": settings,
        "blocks": blocks,
        "type": name,
        "shopify_attributes": "",
    }


def render_template(env, template_name, settings, dropped):
    """Render a JSON template + header/footer groups into one HTML page."""
    product = dict(STUB_PRODUCT)
    product.update({
        "title": "AI Shopify Business Bootcamp",
        "handle": "ai-shopify-business-bootcamp",
        "url": "/products/ai-shopify-business-bootcamp",
        "description": "<p>A 15-class live cohort that takes you from zero to a launched, "
                       "profitable Shopify store. Includes templates, ad scripts and "
                       "1:1 reviews.</p>",
        "content": "<p>Course details and curriculum.</p>",
        "featured_image": "course-hero.jpg",
        "images": ["course-hero.jpg"],
        "price": 299900, "compare_at_price": 500000,
        "price_min": 299900, "price_max": 299900, "compare_at_price_max": 500000,
        "available": True, "vendor": "Darts AI Academy", "type": "Course",
        "tags": ["bootcamp", "shopify", "course"],
        "metafields": {},
        "collections": [],
    })

    month_names = {}
    collection = {
        "title": "Catalog", "handle": "all", "url": "/collections/all",
        "description": "<p>Every course and kit we sell.</p>",
        "products": [product], "products_count": 1, "all_products_count": 1,
        "filters": [], "sort_by": "manual", "default_sort_by": "manual",
        "sort_options": [], "image": None, "featured_image": None,
        "current_type": None, "current_vendor": None, "metafields": {},
        "all_tags": [],
    }
    article = {
        "title": "How to pick your first product", "content": "<p>Body of the post.</p>",
        "excerpt_or_content": "<p>Body of the post.</p>", "author": "Roshan Shaji",
        "published_at": "2026-09-01", "image": "course-hero.jpg", "url": "/blogs/news/post",
        "tags": ["guides"], "comments_count": 0, "comments": [],
        "comment_post_url": "/blogs/news/post/comments", "metafields": {},
    }

    context = {
        "request": {"origin": "https://demo.myshopify.com", "path": "/",
                    "page_type": template_name, "locale": {"iso_code": "en"},
                    "design_mode": False, "host": "demo.myshopify.com"},
        "template": {"name": template_name, "suffix": None, "directory": None},
        "canonical_url": "https://demo.myshopify.com/",
        "page_title": "AI Shopify Business Bootcamp",
        "page_description": "Build and launch your Shopify store in 30 days.",
        "current_page": 1, "current_tags": [],
        "settings": settings,
        "all_products": {"ai-shopify-business-bootcamp": product},
        "product": product,
        "collection": collection,
        "collections": [collection],
        "search": {"performed": False, "terms": "", "results": [], "results_count": 0,
                   "results_count_string": "0 results", "types": [], "sort_by": "relevance"},
        "blog": {"title": "Journal", "handle": "news", "url": "/blogs/news",
                 "articles": [article], "articles_count": 1, "all_tags": [{"title": "guides"}],
                 "metafields": {}},
        "article": article,
        "page": {"title": "Contact", "content": "<p>Get in touch with the team.</p>",
                 "handle": "contact", "url": "/pages/contact", "metafields": {}},
        "pages": [],
        "page_title_str": "AI Shopify Business Bootcamp",
        "cart": {"item_count": 2, "total_price": 599800, "original_total_price": 599800,
                 "total_discount": 0, "note": None, "empty?": False,
                 "currency": {"iso_code": "INR"}, "items": [{
                     "key": "k1", "title": product["title"], "quantity": 1,
                     "price": 299900, "final_price": 299900, "line_price": 299900,
                     "original_line_price": 299900, "url": product["url"],
                     "image": "course-hero.jpg", "product": product,
                     "variant": STUB_VARIANT, "options_with_values": [],
                     "discounted_price": 299900, "product_title": product["title"],
                     "line_level_discount_allocations": [],
                 }]},
        "customer": {"orders": [], "email": "student@example.com", "first_name": "Student",
                     "last_name": "", "default_address": None, "addresses": [],
                     "new_address": {}, "accepts_marketing": False, "metafields": {}},
        "order": {"name": "#1001", "line_items": [], "discounts": [], "subtotal_price": 299900,
                  "total_price": 299900, "created_at": "2026-09-01",
                  "financial_status_label": "Paid", "fulfillment_status_label": "Fulfilled",
                  "shipping_address": None, "customer_url": "/account/orders/1"},
        "gift_card": None,
        "linklists": LINKLIST_STUB,
        "routes": ROUTES,
        "shop": SHOP,
        "form": {"errors": None, "posted_successfully": False},
        "predictive_search": {"performed": False, "terms": ""},
        "recommendations": {"products": [], "products_count": 0},
        "paginate": {"pages": 1, "parts": [], "previous": None, "next": None,
                     "current_page": 1, "items": 1},
        "localization": {"available_countries": [], "available_languages": [],
                         "country": {"iso_code": "IN"}, "language": {"iso_code": "en"}},
        "country_option_tags": "",
        "shop_locale": {"iso_code": "en", "endonym_name": "English"},
        "handle": template_name, "keywords": "", "scripts": "",
        "additional_checkout_buttons": "", "powered_by_link": "",
        "content_for_header": "", "content_for_layout": "",
        "theme": {"role": "main", "name": "Bootcamp"},
        "block": None, "section": None, "forloop": None,
    }

    def render_section(name, section_id, raw_settings, raw_blocks, block_order=None):
        path = os.path.join(THEME, "sections", name + ".liquid")
        if not os.path.exists(path):
            dropped.append(f"{name}: section file missing")
            return ""
        try:
            schema = schema_of(path) or {}
        except json.JSONDecodeError as error:
            dropped.append(f"{name}: bad schema JSON ({error})")
            schema = {}
        defaults = nil_as_blank(section_defaults(schema))
        defaults.update(raw_settings or {})
        # Shopify stores blocks as an id-keyed object with a parallel block_order;
        # normalise to a list before rendering.
        if isinstance(raw_blocks, dict):
            order = [k for k in (block_order or []) if k in raw_blocks] \
                or list(raw_blocks.keys())
            normalised = []
            for key in order:
                if key in raw_blocks:
                    entry = dict(raw_blocks[key])
                    entry.setdefault("id", key)
                    normalised.append(entry)
            for key, value in raw_blocks.items():
                if key not in order:
                    entry = dict(value)
                    entry.setdefault("id", key)
                    normalised.append(entry)
            raw_blocks = normalised

        blocks = []
        for index, block in enumerate(raw_blocks or []):
            block_type = block.get("type")
            block_defaults = {}
            for candidate in schema.get("blocks") or []:
                if isinstance(candidate, dict) and candidate.get("type") == block_type:
                    block_defaults = section_defaults(candidate)
                    break
            block_defaults = nil_as_blank(block_defaults)
            block_defaults.update(block.get("settings") or {})
            blocks.append({"id": block.get("id") or f"b{index}", "type": block_type,
                           "settings": block_defaults, "shopify_attributes": ""})
        # NOTE: no preset fallback here, deliberately. Shopify only applies presets
        # when a merchant adds a section through the editor; a JSON template that
        # omits `blocks` renders with none. Substituting presets here once hid a
        # live-site bug where half the homepage was empty.
        section = section_ctx(section_id, name, defaults, blocks)

        body = render_source(read(path))
        scope = dict(context)
        scope.update({"section": section,
                      "block": blocks[0] if blocks else None,
                      "forloop": None})
        try:
            html = env.from_string(body).render(**scope)
        except Exception as error:  # noqa: BLE001
            dropped.append(f"{name}: {type(error).__name__}: {str(error)[:220]}")
            return ""
        return (f'<div id="shopify-section-{section_id}" '
                f'class="shopify-section shopify-section--{name}">{html}</div>')

    def render_group(group_file):
        path = os.path.join(THEME, "sections", group_file)
        if not os.path.exists(path):
            dropped.append(f"{group_file} missing")
            return ""
        html = []
        for sid, section in json.load(open(path, encoding="utf-8")) \
                .get("sections", {}).items():
            html.append(render_section(section["type"], sid, section.get("settings"),
                                       section.get("blocks"), section.get("block_order")))
        return "\n".join(html)

    header_html = render_group("header-group.json")
    footer_html = render_group("footer-group.json")

    content = []
    template_json = os.path.join(THEME, "templates", template_name + ".json")
    if os.path.exists(template_json):
        data = json.load(open(template_json, encoding="utf-8"))
        order = data.get("order") or list(data.get("sections", {}).keys())
        for sid in order:
            section = data["sections"].get(sid)
            if not section:
                continue
            if section.get("type") == "predictive-search":
                continue
            content.append(render_section(section["type"], sid,
                                          section.get("settings"), section.get("blocks"),
                                          section.get("block_order")))
    else:
        dropped.append(f"templates/{template_name}.json missing")

    layout_file = "password.liquid" if template_name == "password" else "theme.liquid"
    layout = read(os.path.join(THEME, "layout", layout_file))

    # Keep the header/footer groups in their real layout position -- putting them
    # inside <main> renders the whole footer above the hero.
    layout = re.sub(r"{%-?\s*sections\s+'header-group'\s*-?%}", header_html, layout)
    layout = re.sub(r"{%-?\s*sections\s+'footer-group'\s*-?%}", footer_html, layout)

    for name, setting in (("sticky-buy-bar", "sticky_buy_bar"),
                          ("cart-drawer", "cart_drawer_enabled")):
        html = render_section(name, name.replace("-", "_"), {}, None, None) \
            if settings.get(setting) else ""
        layout = re.sub(r"{%-?\s*section\s+'" + name + r"'\s*-?%}", html, layout)
    layout = re.sub(r"{%-?\s*section\s+'[^']*'[^%]*?-?%}", "", layout)

    layout = layout.replace("{{ content_for_layout }}", "\n".join(content))
    layout = layout.replace("{{ content_for_header }}", "")
    body = render_source(layout)

    page = env.from_string(body).render(**context)
    return page


SHOP = {
    "name": "Roshan Shaji \u00b7 Darts AI Academy", "email": "hello@dartsaiacademy.com",
    "domain": "demo.myshopify.com", "permanent_domain": "demo.myshopify.com",
    "url": "https://demo.myshopify.com", "secure_url": "https://demo.myshopify.com",
    "currency": "INR", "money_format": MONEY, "money_with_currency_format": MONEY,
    "enabled_payment_types": ["visa", "master", "upi"],
    "address": {"city": "Thiruvananthapuram", "country": "India", "province": "Kerala"},
    "refund_policy": {"url": "/policies/refund-policy", "title": "Refund policy"},
    "privacy_policy": {"url": "/policies/privacy-policy", "title": "Privacy policy"},
    "terms_of_service": {"url": "/policies/terms-of-service", "title": "Terms of service"},
    "shipping_policy": {"url": "/policies/shipping-policy", "title": "Shipping policy"},
    "subscription_policy": {"url": ""},
    "metafields": {}, "description": "Live Shopify cohort",
}

ROUTES = {
    "root_url": "/", "cart_url": "/cart", "search_url": "/search",
    "collections_url": "/collections", "all_products_collection_url": "/collections/all",
    "predictive_search_url": "/search/suggest",
    "account_url": "/account", "account_login_url": "/account/login",
    "account_logout_url": "/account/logout", "account_register_url": "/account/register",
    "account_recover_url": "/account/login#recover", "account_profile_url": "/account",
    "account_addresses_url": "/account/addresses",
    "cart_add_url": "/cart/add", "cart_change_url": "/cart/change",
    "cart_update_url": "/cart/update", "cart_clear_url": "/cart/clear",
    "product_recommendations_url": "/recommendations/products",
    "storefront_login_url": "/account/login",
}


# --------------------------------------------------------------------------
# Browser
# --------------------------------------------------------------------------
BROWSER_JS = r"""
const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');
const cfg = JSON.parse(process.argv[2]);

(async () => {
  const browser = await puppeteer.launch({
    executablePath: cfg.chromium,
    headless: 'shell',
    args: ['--no-sandbox','--disable-setuid-sandbox','--disable-dev-shm-usage',
           '--disable-gpu','--use-gl=swiftshader','--font-render-hinting=none',
           '--hide-scrollbars','--allow-file-access-from-files'],
    env: { ...process.env, LD_LIBRARY_PATH: cfg.libdir },
  });
  const report = { pages: [], problems: [] };

  for (const pageCfg of cfg.pages) {
    for (const vp of cfg.viewports) {
      const page = await browser.newPage();
      const consoleErrors = [];
      page.on('console', m => { if (m.type() === 'error') consoleErrors.push(m.text().slice(0,180)); });
      page.on('pageerror', e => consoleErrors.push('pageerror: ' + String(e.message).slice(0,180)));
      await page.setViewport({ width: vp.width, height: vp.height, deviceScaleFactor: 1 });
      await page.goto('file://' + pageCfg.file, { waitUntil: 'load', timeout: 30000 });
      await new Promise(r => setTimeout(r, 400));

      const probe = await page.evaluate(() => {
        const cs = getComputedStyle;
        const rootCS = cs(document.documentElement);
        const varDef = new Set();
        const rootDef = new Set();
        const varUse = new Set();
        for (const sheet of Array.from(document.styleSheets)) {
          let rules; try { rules = sheet.cssRules; } catch (e) { continue; }
          const walk = list => {
            for (const r of Array.from(list || [])) {
              // skip @media blocks that do not match this viewport, and @supports
              // that do not apply -- otherwise their :root rules are counted as
              // "defined but empty" when they simply never applied.
              if (r.conditionText !== undefined) {
                if (r.constructor.name === 'CSSMediaRule'
                    && !window.matchMedia(r.conditionText).matches) continue;
                if (r.constructor.name === 'CSSSupportsRule'
                    && !CSS.supports(r.conditionText)) continue;
              }
              if (r.style && r.selectorText !== undefined) {
                for (const prop of Array.from(r.style)) {
                  if (!prop.startsWith('--')) continue;
                  varDef.add(prop);
                  if (/:root|^html\b/.test(r.selectorText)) rootDef.add(prop);
                }
                // only usages WITHOUT a fallback are unsafe when undefined
                for (const m of (r.cssText || '').matchAll(/var\((--[a-z0-9-]+)\s*\)/gi)) varUse.add(m[1]);
              }
              if (r.cssRules && r.cssRules.length) walk(r.cssRules);
            }
          };
          walk(rules);
        }
        const alphaOf = colour => {
          const m = String(colour).match(/rgba?\(([^)]+)\)/);
          if (!m) return 1;
          const parts = m[1].split(',').map(parseFloat);
          return parts.length > 3 ? parts[3] : 1;
        };
        const body = cs(document.body);
        const buttons = Array.from(document.querySelectorAll('.btn, button.btn, a.btn, input[type=submit]'));
        const opaque = buttons.filter(b => alphaOf(cs(b).backgroundColor) > 0.05
                                        || cs(b).backgroundImage !== 'none'
                                        || parseFloat(cs(b).borderTopWidth) > 0);
        const invisible = [];
        for (const sel of ['.card', '.faq-item', '.faq__item', '.testimonial',
                           '.pricing-card', '.value-card', '.step-card', '.curriculum-item',
                           '.trust-item', '.bonus-card', '.module-card']) {
          for (const el of Array.from(document.querySelectorAll(sel)).slice(0, 60)) {
            const c = cs(el);
            if (alphaOf(c.backgroundColor) < 0.05 && c.backgroundImage === 'none'
                && parseFloat(c.borderTopWidth) === 0 && parseFloat(c.boxShadow.replace(/^none$/, '0')) === 0) {
              invisible.push(sel);
            }
          }
        }
        const serif = [];
        for (const sel of ['h1','h2','.btn','button','.card','.price','nav a','p']) {
          const el = document.querySelector(sel);
          if (!el) continue;
          const f = cs(el).fontFamily.toLowerCase();
          if (/(times|georgia|"serif"|,\s*serif)/.test(f) && !/sans-serif/.test(f)) {
            serif.push(sel + ' -> ' + cs(el).fontFamily.slice(0,70));
          }
        }
        // A custom property that is DEFINED but EMPTY is the silent killer: var()
        // never uses its fallback, the declaration is dropped, and the theme
        // reverts to browser defaults. Catch it explicitly.
        const emptyVars = [];
        // only variables defined on :root/html are inherited globally -- a var
        // scoped to .btn is legitimately empty when read from the root element
        for (const name of rootDef) {
          const value = rootCS.getPropertyValue(name).trim();
          if (value === '' || /^[\s,;]*$/.test(value) || value === 'none') emptyVars.push(name);
        }
        // A native <dialog> that is NOT open must not render. Declaring `display`
        // on the dialog class overrides the UA hide rule and shows the closed
        // overlay on every page (this shipped once: the mobile menu bar).
        const strayDialogs = [];
        for (const d of Array.from(document.querySelectorAll('dialog'))) {
          const c = cs(d);
          const r = d.getBoundingClientRect();
          if (!d.hasAttribute('open') && c.display !== 'none'
              && c.visibility !== 'hidden' && r.width > 4 && r.height > 4) {
            strayDialogs.push((d.id || d.className) + ' ' + Math.round(r.width) + 'x' + Math.round(r.height));
          }
        }
        // A section that renders its blocks but received none shows up as a big
        // blank band. Catch it structurally: any element that declares a
        // block-rendering hook must contain content.
        const emptySections = [];
        for (const sec of Array.from(document.querySelectorAll('main > .shopify-section'))) {
          const cls = sec.className;
          if (!/curriculum|faq|includes|stats|pricing|testimonials|tools|video|instructor/.test(cls)) continue;
          const r = sec.getBoundingClientRect();
          const txt = (sec.innerText || '').trim();
          const media = sec.querySelectorAll('img, svg, video, iframe').length;
          const listItems = sec.querySelectorAll('li, article, details').length;
          if (r.height > 120 && txt.length < 40 && media < 2 && listItems < 2) {
            emptySections.push(cls.replace('shopify-section shopify-section--', '').trim()
                               + ' (' + Math.round(r.height) + 'px tall, ' + txt.length + ' chars)');
          }
        }
        const text = document.body.innerText || '';
        const h1 = document.querySelector('h1');
        return {
          title: document.title,
          bodyFont: body.fontFamily.slice(0, 90),
          varDefined: varDef.size,
          varUsed: varUse.size,
          varUndefined: Array.from(varUse).filter(v => !varDef.has(v)).slice(0, 12),
          primary: (rootCS.getPropertyValue('--c-accent') || rootCS.getPropertyValue('--color-primary')).trim() || null,
          fontBody: (rootCS.getPropertyValue('--font-body') || '').trim().slice(0, 70) || null,
          emptyVars: emptyVars.slice(0, 12),
          strayDialogs,
          emptySections,
          buttonCount: buttons.length,
          opaqueButtons: opaque.length,
          invisibleBoxes: Array.from(new Set(invisible)),
          liquidError: /Liquid (syntax )?error|was not properly terminated|Liquid error/i.test(text),
          missingStrings: (text.match(/\u26a0missing:[a-z0-9._]+/gi) || []).slice(0, 8),
          serifHits: serif,
          overflow: document.documentElement.scrollWidth > window.innerWidth + 2,
          scrollWidth: document.documentElement.scrollWidth,
          innerWidth: window.innerWidth,
          docHeight: document.documentElement.scrollHeight,
          h1: h1 ? h1.textContent.trim().slice(0,90) : null,
          sectionCount: document.querySelectorAll('main > .shopify-section, main > *').length,
          anchorCount: document.querySelectorAll('a[href]').length,
          jsonldBlocks: document.querySelectorAll('script[type="application/ld+json"]').length,
        };
      });

      // Walk the page like a human so IntersectionObserver reveal animations
      // fire; a naive fullPage capture freezes every below-the-fold section at
      // opacity:0 and reports a blank page.
      const total = await page.evaluate(() => document.documentElement.scrollHeight);
      for (let y = 0; y < total; y += Math.round(vp.height * 0.6)) {
        await page.evaluate(v => window.scrollTo(0, v), y);
        await new Promise(r => setTimeout(r, 60));
      }
      await page.evaluate(() => window.scrollTo(0, 0));
      await new Promise(r => setTimeout(r, 450));

      const hidden = await page.evaluate(() => {
        const out = [];
        for (const el of Array.from(document.querySelectorAll('.reveal'))) {
          if (parseFloat(getComputedStyle(el).opacity) < 0.05) {
            out.push(el.className.slice(0, 60));
          }
        }
        return out;
      });

      const shot = path.join(cfg.shotdir, pageCfg.name + '-' + vp.width + '.png');
      await page.screenshot({ path: shot, fullPage: true });
      report.pages.push({ name: pageCfg.name, width: vp.width,
                          probe: Object.assign({}, probe, { stillHidden: hidden }),
                          shot, consoleErrors });
      await page.close();
    }
  }
  await browser.close();
  fs.writeFileSync(cfg.report, JSON.stringify(report, null, 2));
  console.log('RENDER_REPORT_OK');
})().catch(e => { console.error('RENDER_FAIL: ' + e.message); process.exit(1); });
"""


def run_browser(pages, shotdir, report_path):
    os.makedirs(NODE_DIR, exist_ok=True)
    with open(os.path.join(NODE_DIR, "render_browser.js"), "w", encoding="utf-8") as fh:
        fh.write(BROWSER_JS)
    config = {"chromium": CHROMIUM, "libdir": LIBDIR, "report": report_path,
              "shotdir": shotdir, "pages": pages,
              "viewports": [{"width": 1280, "height": 900},
                            {"width": 390, "height": 844}]}
    result = subprocess.run(["node", "render_browser.js", json.dumps(config)],
                            cwd=NODE_DIR, capture_output=True, text=True, timeout=1200)
    combined = result.stdout + result.stderr
    if "RENDER_REPORT_OK" not in combined:
        return None, combined[-2000:]
    return json.load(open(report_path, encoding="utf-8")), None


PAGES = ["index", "product", "collection", "cart", "page", "search", "list-collections",
         "blog", "article", "404", "password"]

# Simulate the live-store outage: the storefront rendered as unstyled Times New
# Roman because the :root token block never reached the page. --no-vars strips it
# from the rendered HTML so the stylesheet has to stand on its own fallbacks.
# If the theme can survive that, this class of outage can never take the store down.
STRIP_THEME_VARS = "--no-vars" in sys.argv


def main():
    print("Rendering the theme in a real browser\n")
    if not os.path.exists(CHROMIUM):
        fail(f"headless chromium not found at {CHROMIUM} -- see tools/README-render.md")
        return 1

    import liquid
    from liquid import Environment, FileSystemLoader

    os.makedirs(OUT, exist_ok=True)
    # In resilience mode write elsewhere BEFORE wiping anything, otherwise the
    # --no-vars run deletes the normal run's screenshots.
    shotdir = os.path.join(OUT, "shots-no-vars" if STRIP_THEME_VARS else "shots")
    shutil.rmtree(shotdir, ignore_errors=True)
    os.makedirs(shotdir, exist_ok=True)

    staging = stage_theme()
    locale = json.load(open(os.path.join(THEME, "locales", "en.default.json"),
                            encoding="utf-8"))
    env = Environment(loader=FileSystemLoader(staging, ext=".liquid"),
                      strict_filters=False)
    for name, fn in make_filters(locale).items():
        env.add_filter(name, fn)

    settings = coerce_fonts(THEME, nil_as_blank(shopify_settings(THEME)))

    # assets the rendered page asks for
    assets_out = os.path.join(OUT, "assets")
    shutil.rmtree(assets_out, ignore_errors=True)
    shutil.copytree(os.path.join(THEME, "assets"), assets_out)
    # stand-in imagery so <img> tags resolve instead of showing broken icons
    try:
        from PIL import Image, ImageDraw
        hero = Image.new("RGB", (1200, 800))
        draw = ImageDraw.Draw(hero)
        for y in range(800):
            t = y / 800
            draw.line([(0, y), (1200, y)],
                      fill=(int(79 + 120 * t), int(47 + 60 * t), int(214 - 40 * t)))
        hero.save(os.path.join(assets_out, "course-hero.jpg"), quality=88)
        hero.resize((600, 400)).save(os.path.join(assets_out, "course-square.jpg"), quality=88)
    except ImportError:
        notes.append("Pillow not installed - placeholder imagery skipped")

    pages = []
    render_failures = []
    for name in PAGES:
        dropped = []
        page = render_template(env, name, settings, dropped)
        for item in dropped:
            render_failures.append(f"{name}: {item}")
        path = os.path.join(OUT, name + ".html")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(page)
        pages.append({"name": name, "file": path})

    if render_failures:
        for item in render_failures:
            fail(f"liquid render: {item}")
        return 1
    ok(f"Liquid render: {len(pages)} page types rendered with no exceptions")

    # JSON-LD must be valid JSON, or Google silently drops the rich result
    for name in ("index", "product"):
        html = read(os.path.join(OUT, name + ".html"))
        for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>',
                                html, re.S):
            try:
                json.loads(block)
            except json.JSONDecodeError as error:
                fail(f"jsonld on {name}: invalid JSON -- {error}")
    ok("JSON-LD: parses as valid JSON on index + product")

    if STRIP_THEME_VARS:
        print("  · --no-vars: stripping the :root token block to test fallback resilience")
        for entry in pages:
            html = read(entry["file"])
            stripped = re.sub(r"<style>.*?</style>",
                              "<style>/* tokens removed for the resilience run */</style>",
                              html, count=1, flags=re.S)
            with open(entry["file"], "w", encoding="utf-8") as fh:
                fh.write(stripped)
    report, error = run_browser(pages, shotdir, os.path.join(OUT, "report.json"))
    if error:
        fail(f"browser run failed -- {error}")
        return 1

    desktop = 0
    for entry in report["pages"]:
        p = entry["probe"]
        tag = f"{entry['name']}@{entry['width']}"
        if p["liquidError"]:
            fail(f"{tag}: a Liquid error is visible on the rendered page")
        if p["missingStrings"]:
            fail(f"{tag}: missing translations rendered: {p['missingStrings']}")
        if p["varDefined"] == 0 and not STRIP_THEME_VARS:
            fail(f"{tag}: no theme custom properties were emitted -- "
                 "the token block did not reach the page")
        visual_only = STRIP_THEME_VARS  # in resilience mode, missing tokens are the setup, not the bug
        if visual_only and p["varDefined"] == 0:
            pass  # expected
        if p.get("stillHidden"):
            fail(f"{tag}: scroll-reveal content never became visible "
                 f"({len(p['stillHidden'])} element(s)): {p['stillHidden'][:3]}")
        if p["emptySections"]:
            fail(f"{tag}: section rendered with no content -- its blocks were probably "
                 f"never written into the JSON template: {p['emptySections']}")
        if p["strayDialogs"]:
            fail(f"{tag}: closed <dialog> is still rendered (missing a "
                 f":not([open]){{display:none}} guard): {p['strayDialogs']}")
        if p["emptyVars"] and not STRIP_THEME_VARS:
            fail(f"{tag}: custom properties defined but EMPTY (var() fallbacks will not "
                 f"apply and the theme reverts to browser defaults): {p['emptyVars']}")
        if not p["fontBody"] and not STRIP_THEME_VARS:
            fail(f"{tag}: --font-body is missing -- the theme font stack did not reach the page")
        if p["varUndefined"]:
            fail(f"{tag}: stylesheet uses undefined custom properties: {p['varUndefined']}")
        if p["serifHits"]:
            fail(f"{tag}: serif fallback font in use (theme fonts not applied): {p['serifHits']}")
        if p["invisibleBoxes"]:
            fail(f"{tag}: cards render with no background, border or shadow: {p['invisibleBoxes']}")
        if p["buttonCount"] and p["opaqueButtons"] != p["buttonCount"]:
            fail(f"{tag}: {p['buttonCount'] - p['opaqueButtons']} of {p['buttonCount']} "
                 "buttons render transparent")
        if entry["width"] == 390 and p["overflow"]:
            fail(f"{tag}: horizontal overflow ({p['scrollWidth']}px content in "
                 f"{p['innerWidth']}px viewport)")
        if p["jsonldBlocks"] == 0 and entry["name"] in ("index", "product"):
            fail(f"{tag}: no JSON-LD block present in the head")
        hard_console = [c for c in entry["consoleErrors"]
                        if "favicon" not in c.lower()]
        if hard_console:
            fail(f"{tag}: console errors: {hard_console[:3]}")
        if entry["width"] == 1280:
            desktop += 1

    heights = {e["name"]: e["probe"]["docHeight"] for e in report["pages"]
               if e["width"] == 1280}
    empty = [n for n, h in heights.items() if h < 500 and n != "password"]
    if empty:
        fail(f"pages rendered suspiciously short (likely nothing rendered): {empty}")

    if not problems:
        mode = " (tokens stripped)" if STRIP_THEME_VARS else ""
        ok(f"Browser: {desktop} page types \u00d7 2 viewports rendered clean{mode}")
        ok("Visual assertions: fonts, custom properties, buttons, card surfaces, overflow")
        total_vars = report["pages"][0]["probe"]["varDefined"]
        ok(f"Theme custom properties live on the page: {total_vars}")
        print(f"\n  screenshots -> {shotdir}")

    shutil.rmtree(staging, ignore_errors=True)

    for note in notes:
        print(f"  \u00b7 {note}")
    if problems:
        print(f"\n{len(problems)} problem(s):")
        for item in problems:
            print(f"  \u2717 {item}")
        return 1
    print("\nRender check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
