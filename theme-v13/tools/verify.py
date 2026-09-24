#!/usr/bin/env python3
"""
Theme verification suite — run before packaging a release.

Usage:  python3 tools/verify.py [theme_dir]

Checks performed
  1. Every .liquid file parses with a real Liquid engine (python-liquid).
  2. Every {% schema %} block is valid JSON and has a name.
  3. Every JSON template is valid and references a section that exists.
  4. Every {% render %} / {% section %} reference resolves to a real file.
  5. Every locale key used with the `t` filter exists in locales/en.default.json.
  6. Sections render with their schema defaults (Shopify nil-as-blank semantics)
     and produce no empty `href=""` links.
  7. CSS coverage: no rule targets a class that is never used in markup.
  8. theme.js passes `node --check` when node is available.

Exit code is non-zero if any check fails, so it can gate a build.
"""

import glob
import json
import os
import re
import shutil
import subprocess
import sys

problems = []
notes = []


def fail(check, message):
    problems.append(f"[{check}] {message}")


def ok(message):
    notes.append(message)


# ---------------------------------------------------------------- utilities
def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def strip_schema(src):
    return re.sub(r"{%-?\s*schema\s*-?%}.*?{%-?\s*endschema\s*-?%}", "", src, flags=re.S)


def preprocess_liquid(src):
    """Remove Shopify-only tags that a generic Liquid engine cannot parse."""
    src = strip_schema(src)
    for tag in ("form", "paginate", "style", "javascript", "capture", "layout"):
        src = re.sub(r"{%-?\s*" + tag + r"\b[^%]*?-?%}", "", src)
        src = re.sub(r"{%-?\s*end" + tag + r"\s*-?%}", "", src)
    return re.sub(r"{%-?\s*sections?\s+'[^']*'[^%]*?-?%}", "", src)


def schema_of(path):
    match = re.search(r"{%\s*schema\s*%}(.*?){%\s*endschema\s*%}", read(path), re.S)
    return json.loads(match.group(1)) if match else None


EMPTY_BY_TYPE = {
    "text": "", "textarea": "", "richtext": "", "html": "", "url": "", "image_picker": None,
    "video": None, "video_url": None, "link_list": {"links": []}, "checkbox": False,
    "number": 0, "range": 0, "select": None, "color": "#000000", "product": None,
    "collection": None, "blog": None, "page": None, "font_picker": "assistant_n4",
    "article": None, "metaobject": None, "liquid": "",
}

LINKLIST_STUB = {
    "main-menu": {"links": [
        {"title": "Curriculum", "url": "/#curriculum", "links": [], "active": False,
         "child_active": False, "current": False},
        {"title": "Instructor", "url": "/#instructor", "links": [], "active": False,
         "child_active": False, "current": False},
        {"title": "FAQ", "url": "/#faq", "links": [], "active": False,
         "child_active": False, "current": False},
    ]}
}


def shopify_settings(theme):
    """Global settings exactly as Shopify exposes them (missing id -> nil)."""
    schema = json.load(open(os.path.join(theme, "config/settings_schema.json"), encoding="utf-8"))
    out = {}
    for group in schema:
        for setting in group.get("settings", []):
            if "id" not in setting:
                continue
            if "default" in setting:
                default = setting["default"]
                if setting.get("type") == "link_list":
                    out[setting["id"]] = LINKLIST_STUB.get(default, {"links": []})
                else:
                    out[setting["id"]] = default
            else:
                out[setting["id"]] = EMPTY_BY_TYPE.get(setting.get("type"), "")
    return out


def section_defaults(schema):
    out = {}
    for setting in schema.get("settings", []):
        if "id" not in setting:
            continue
        if "default" in setting:
            if setting.get("type") == "link_list":
                out[setting["id"]] = LINKLIST_STUB.get(setting["default"], {"links": []})
            else:
                out[setting["id"]] = setting["default"]
        else:
            out[setting["id"]] = EMPTY_BY_TYPE.get(setting.get("type"), "")
    return out


def preset_blocks(schema):
    """Mirror what the theme editor does when a merchant adds a preset section."""
    types = {b["type"]: b for b in schema.get("blocks", []) if isinstance(b, dict) and "type" in b}
    presets = schema.get("presets") or []
    blocks = []
    if presets and "blocks" in presets[0]:
        for index, block in enumerate(presets[0]["blocks"]):
            defaults = section_defaults(types.get(block.get("type"), {}))
            defaults.update(block.get("settings", {}))
            blocks.append({
                "id": f"b{index}", "type": block.get("type"),
                "settings": defaults, "shopify_attributes": "",
            })
    return blocks


# ------------------------------------------------------------- check 1: parse
def check_parse(theme):
    try:
        import liquid
        from liquid.exceptions import LiquidError
    except ImportError:
        notes.append("Liquid parse skipped (pip install python-liquid to enable)")
        return

    env = liquid.Environment()
    preprocess = preprocess_liquid

    files = sorted(glob.glob(os.path.join(theme, "**/*.liquid"), recursive=True))
    failed = 0
    for path in files:
        try:
            env.parse(preprocess(read(path)))
        except LiquidError as error:
            failed += 1
            fail("parse", f"{os.path.relpath(path, theme)}: {str(error)[:160]}")
        except Exception as error:  # noqa: BLE001
            failed += 1
            fail("parse", f"{os.path.relpath(path, theme)}: {type(error).__name__}: {str(error)[:160]}")
    if not failed:
        ok(f"Liquid parse: {len(files)}/{len(files)} files clean")


# ------------------------------------------- check 2/3/4: schemas + references
def check_schemas_and_refs(theme):
    section_files = sorted(glob.glob(os.path.join(theme, "sections/*.liquid")))
    templates = sorted(glob.glob(os.path.join(theme, "templates/**/*.json"), recursive=True))
    groups = [os.path.join(theme, "sections/header-group.json"),
              os.path.join(theme, "sections/footer-group.json")]

    sections = {os.path.basename(p)[:-7] for p in section_files}
    snippets = {os.path.basename(p)[:-7] for p in glob.glob(os.path.join(theme, "snippets/*.liquid"))}

    with_schema = 0
    for path in section_files:
        try:
            schema = schema_of(path)
        except json.JSONDecodeError as error:
            fail("schema", f"{os.path.basename(path)}: invalid JSON — {error}")
            continue
        if schema is None:
            continue  # sections rendered only through section_id (e.g. predictive-search)
        with_schema += 1
        if not schema.get("name"):
            fail("schema", f"{os.path.basename(path)}: missing \"name\"")

    referenced = set()
    for path in templates + [g for g in groups if os.path.exists(g)]:
        try:
            data = json.load(open(path, encoding="utf-8"))
        except json.JSONDecodeError as error:
            fail("template", f"{os.path.relpath(path, theme)}: invalid JSON — {error}")
            continue
        for section in data.get("sections", {}).values():
            referenced.add(section["type"])
            if section["type"] not in sections:
                fail("template", f"{os.path.relpath(path, theme)}: references missing section '{section['type']}'")

    layout = os.path.join(theme, "layout/theme.liquid")
    if os.path.exists(layout):
        referenced |= set(re.findall(r"{%-?\s*section\s+'([^']+)'", read(layout)))
        for name in referenced:
            if name not in sections:
                fail("layout", f"theme.liquid references missing section '{name}'")

    missing = set()
    for path in glob.glob(os.path.join(theme, "**/*.liquid"), recursive=True):
        for name in re.findall(r"{%-?\s*render\s+'([^']+)'", read(path)):
            if name not in snippets:
                missing.add(f"{os.path.relpath(path, theme)} -> render '{name}'")
    for item in sorted(missing):
        fail("render", item)

    if section_files and with_schema:
        ok(f"Schemas: {with_schema} valid, templates: {len(templates)} valid, "
           f"missing references: {len(missing)}")
    unused = sections - referenced
    if unused:
        notes.append(f"unused sections (fine if rendered by a template suffix): {sorted(unused)}")


# ------------------------------------------------------------- check 5: locale
def check_locales(theme):
    path = os.path.join(theme, "locales/en.default.json")
    if not os.path.exists(path):
        fail("locale", "locales/en.default.json is missing")
        return
    locale = json.load(open(path, encoding="utf-8"))

    def has_key(dotted):
        cursor = locale
        for part in dotted.split("."):
            if not isinstance(cursor, dict) or part not in cursor:
                return False
            cursor = cursor[part]
        return True

    missing = set()
    for file_path in glob.glob(os.path.join(theme, "**/*.liquid"), recursive=True):
        src = read(file_path)
        for key in re.findall(r"'([a-z0-9_]+\.[a-z0-9_]+\.[a-z0-9_.]+)'\s*\|\s*t", src):
            if not has_key(key):
                missing.add(key)
    for key in sorted(missing):
        fail("locale", f"'{key}' used in a template but not defined")
    if not missing:
        ok("Locale: every t-filter key resolves")


# ------------------------------------------------------- check 6: link audit
STUB_VARIANT = {
    "id": 111, "title": "Default Title", "available": True, "price": 299900,
    "inventory_quantity": 7, "inventory_management": "shopify", "compare_at_price": 500000,
    "options": ["Default Title"], "requires_shipping": False, "selling_plan_allocation": None,
}
STUB_PRODUCT = {
    "id": 1, "title": "AI x Shopify Business Bootcamp",
    "handle": "ai-shopify-business-bootcamp", "url": "/products/ai-shopify-business-bootcamp",
    "description": "<p>Build a real store.</p>", "price": 299900, "compare_at_price": 500000,
    "available": True, "featured_image": None, "featured_media": None, "images": [], "media": [],
    "variants": [STUB_VARIANT], "options_with_values": [], "has_only_default_variant": True,
    "vendor": "DARTS AI Academy", "tags": [], "selected_or_first_available_variant": STUB_VARIANT,
}


def check_links(theme):
    try:
        import liquid
        from liquid import Environment, FileSystemLoader
    except ImportError:
        notes.append("Link audit skipped (python-liquid not installed)")
        return

    staging = os.path.join(theme, ".verify-staging")
    if os.path.isdir(staging):
        shutil.rmtree(staging)
    os.makedirs(staging)
    for folder in ("snippets", "sections"):
        for path in glob.glob(os.path.join(theme, folder, "*.liquid")):
            shutil.copy(path, staging)

    env = Environment(loader=FileSystemLoader(staging, ext=".liquid"), strict_filters=False)
    settings = shopify_settings(theme)
    routes = {"root_url": "/"}
    for key in ("cart", "cart_add", "cart_change", "cart_clear", "cart_update", "search",
                "account", "account_login", "account_logout", "account_register",
                "account_addresses", "account_recover", "account_profile",
                "all_products_collection", "collections", "predictive_search",
                "product_recommendations", "storefront_login"):
        routes[key + "_url"] = "/" + key

    shop = {
        "name": "DARTS AI Academy", "url": "https://d.example", "money_format": "Rs. {{amount}}",
        "enabled_payment_types": [], "email": "hi@example.com", "address": {"summary": ""},
        "customer_accounts_enabled": False,
        "refund_policy": {"title": "Refund policy", "url": "/policies/refund-policy"},
        "privacy_policy": {"title": "Privacy policy", "url": "/policies/privacy-policy"},
        "terms_of_service": {"title": "Terms of service", "url": "/policies/terms-of-service"},
        "shipping_policy": {"title": "Shipping policy", "url": "/policies/shipping-policy"},
        "subscription_policy": None,
    }
    env.globals.update({
        "settings": settings, "shop": shop, "routes": routes,
        "cart": {"item_count": 0, "total_price": 0, "items": [], "note": None,
                 "currency": {"iso_code": "INR"}},
        "request": {"origin": "https://d.example", "page_type": "index",
                    "locale": {"iso_code": "en"}},
        "template": {"name": "index", "suffix": None},
        "canonical_url": "https://d.example/", "page_title": "Bootcamp",
        "page_description": "Live cohort",
        "all_products": {"ai-shopify-business-bootcamp": STUB_PRODUCT},
        "product": STUB_PRODUCT, "current_tags": [], "current_page": 1,
        "shop_url": "https://d.example", "linklists": LINKLIST_STUB, "form": None,
        "search": {"performed": False, "terms": "", "results": [], "results_count": 0},
        "paginate": {"pages": 1, "parts": [], "previous": None, "next": None},
        "country_option_tags": "", "predictive_search": {"performed": False, "terms": ""},
        "blog": {"title": "Journal", "articles": [], "url": "/blogs/journal"},
        "article": {"title": "Post", "content": "<p>Body</p>", "author": "Roshan",
                    "published_at": "2026-09-01", "image": None, "excerpt_or_content": "Body",
                    "url": "/blogs/journal/post"},
        "collection": {"title": "Store", "description": "", "products": [], "featured_image": None,
                       "all_products_count": 1, "url": "/collections/all"},
        "customer": {"orders": [], "email": "student@example.com", "default_address": None,
                     "addresses": [], "new_address": {}},
        "order": {"name": "#1001", "line_items": [], "discounts": [], "subtotal_price": 299900,
                  "total_price": 299900, "created_at": "2026-09-01",
                  "financial_status_label": "Paid", "fulfillment_status_label": "Fulfilled",
                  "shipping_address": None, "customer_url": "/account/orders/1"},
        "page": {"title": "Page", "content": "<p>Content</p>"}, "gift_card": None,
    })

    total_anchors = 0
    dead = []
    failures = []
    for path in sorted(glob.glob(os.path.join(staging, "*.liquid"))):
        name = os.path.basename(path)[:-7]
        if name.endswith("-group"):
            continue
        try:
            schema = schema_of(path)
        except json.JSONDecodeError:
            continue
        schema = schema or {}
        section = {
            "id": "sec1", "settings": section_defaults(schema), "type": name,
            "blocks": preset_blocks(schema),
        }
        body = preprocess_liquid(read(path))
        body = re.sub(r"{%-?\s*render 'product-form'[^%]*?-?%}", "[PRODUCT_FORM]", body)
        body = re.sub(r"{%-?\s*render 'quick-add'[^%]*?-?%}", "[QUICK_ADD]", body)
        try:
            rendered = env.from_string(body).render(
                section=section, product=STUB_PRODUCT,
                block=section["blocks"][0] if section["blocks"] else None)
        except Exception as error:  # noqa: BLE001
            failures.append(f"{name}: {type(error).__name__}: {str(error)[:120]}")
            continue
        for href in re.findall(r'<a\b[^>]*href="([^"]*)"', rendered):
            total_anchors += 1
            if href.strip() in ("", "#"):
                dead.append(f"{name} -> {href!r}")

    shutil.rmtree(staging, ignore_errors=True)

    for item in dead:
        fail("links", f"empty href: {item}")
    for item in failures:
        fail("render", item)
    if not dead and not failures:
        ok(f"Link audit: {total_anchors} anchors rendered, 0 dead links")


# --------------------------------------------------------- check 7: CSS usage
def check_css(theme):
    css_path = os.path.join(theme, "assets/theme.css")
    if not os.path.exists(css_path):
        fail("css", "assets/theme.css is missing")
        return
    defined = set(re.findall(r"\.([a-zA-Z][\w-]*)", read(css_path)))

    used = set()
    for path in glob.glob(os.path.join(theme, "**/*.liquid"), recursive=True):
        raw = read(path)
        stripped = re.sub(r"{%-?.*?-?%}", " ", raw, flags=re.S)
        stripped = re.sub(r"{{-?.*?-?}}", " ", stripped, flags=re.S)
        for attr in re.findall(r'class="([^"]*)"', stripped):
            used.update(c for c in attr.split() if c)
        for value in re.findall(r"class:\s*'([^']*)'", raw):
            used.update(c for c in value.split() if c)
    # class names built with Liquid interpolation, e.g. class="price--{{ size }}"
    prefixes = set()
    for path in glob.glob(os.path.join(theme, "**/*.liquid"), recursive=True):
        raw = read(path)
        for attr in re.findall(r'class="([^"]*)"', raw):
            if "{{" in attr or "{%" in attr:
                for token in re.split(r"[\s{}%]+", attr):
                    if token.endswith("--") or token.endswith("-"):
                        prefixes.add(token)
    for prefix in prefixes:
        used |= {c for c in defined if c.startswith(prefix)}

    # classes toggled from any script, including inline ones in layouts
    toggled_pattern = re.compile(r"""classList\.(?:add|toggle|remove)\(\s*['"]([\w-]+)["']""")
    for path in glob.glob(os.path.join(theme, "assets/*.js")) + glob.glob(
            os.path.join(theme, "layout/*.liquid")):
        raw = read(path)
        for attr in re.findall(r"""className\s*=\s*['"]([^'"]*)['"]""", raw):
            used.update(c for c in attr.split() if c)
        used.update(toggled_pattern.findall(raw))

    dead = sorted(c for c in defined if c not in used)
    if dead:
        fail("css", f"{len(dead)} rule(s) target classes never used in markup: {dead[:12]}")
    else:
        ok(f"CSS: {len(defined)} classes defined, no dead rules")


# ----------------------------------------------------------- check 8: JS lint
def check_js(theme):
    if not shutil.which("node"):
        notes.append("JS lint skipped (node not installed)")
        return
    for path in sorted(glob.glob(os.path.join(theme, "assets/*.js"))):
        result = subprocess.run(["node", "--check", path], capture_output=True, text=True)
        if result.returncode != 0:
            fail("js", f"{os.path.basename(path)}: {result.stderr.strip()[:160]}")
    ok("JS: node --check passed")


def default_theme():
    """Use the parent of tools/ when it looks like a theme, else look for theme-v13."""
    here = os.path.dirname(os.path.abspath(__file__))
    for candidate in (os.path.dirname(here),
                      os.path.join(os.path.dirname(here), "theme-v13")):
        if os.path.exists(os.path.join(candidate, "config", "settings_schema.json")):
            return candidate
    return "."


def main():
    theme = (sys.argv[1] if len(sys.argv) > 1 else default_theme()).rstrip("/")

    print(f"Verifying {theme}\n")
    check_parse(theme)
    check_schemas_and_refs(theme)
    check_locales(theme)
    check_links(theme)
    check_css(theme)
    check_js(theme)

    for note in notes:
        print(f"  · {note}")
    if problems:
        print(f"\n{len(problems)} problem(s):")
        for item in problems:
            print(f"  ✗ {item}")
        return 1
    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
