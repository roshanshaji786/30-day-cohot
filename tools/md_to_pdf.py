#!/usr/bin/env python3
"""
Render a Markdown report to print-ready HTML, then PDF.

Why the fonts are embedded: this machine has no fontconfig fonts registered
(`fc-list` is empty), so Chromium would render blank boxes. The TTFs are inlined
as data URLs instead, and the font stack relies on Chromium's per-glyph
fallback (Open Sans for text, DejaVu Sans for arrows/check/rupee, DejaVu Mono
for code).

Emoji have no available font, so the three status emoji in the report are
replaced with styled marks that use characters present in DejaVu Sans.

Usage:  python3 tools/md_to_pdf.py <input.md> <output.html>
"""
import base64
import html
import pathlib
import re
import sys

import markdown

FONTS = {
    "Open Sans": {
        "normal": "/tmp/fx/fonts/Open_Sans/OpenSans-Regular.ttf",
        "bold": "/tmp/fx/fonts/Open_Sans/OpenSans-Bold.ttf",
        "italic": "/tmp/fx/fonts/Open_Sans/OpenSans-Italic.ttf",
    },
    "DejaVu Sans": {
        "normal": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "bold": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    },
    "DejaVu Sans Mono": {
        "normal": "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "bold": "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    },
}


def font_face_css() -> str:
    rules = []
    for family, variants in FONTS.items():
        for style, path in variants.items():
            data = pathlib.Path(path).read_bytes()
            b64 = base64.b64encode(data).decode()
            rules.append(
                "@font-face{font-family:'%s';font-style:%s;font-weight:normal;"
                "font-display:block;src:url(data:font/ttf;base64,%s) format('truetype')}"
                % (family, style, b64)
            )
    return "\n".join(rules)


CSS = """.body-font{font-family:'Open Sans','DejaVu Sans',sans-serif}
html{-webkit-print-color-adjust:exact;print-color-adjust:exact}
body{font-family:'Open Sans','DejaVu Sans',sans-serif;font-size:9.5pt;line-height:1.5;color:#1b1b23;margin:0}
h1,h2,h3,h4{font-family:'Open Sans','DejaVu Sans',sans-serif;line-height:1.25;color:#111119}

/* ---- report masthead ---- */
.masthead{border:1px solid #e2def7;border-radius:10px;padding:16px 18px;margin:0 0 18px;background:#faf9fe}
.masthead .kicker{font-size:7.5pt;letter-spacing:.16em;text-transform:uppercase;font-weight:700;color:#4f2fd6;margin:0 0 6px}
.masthead h1{font-size:21pt;margin:0 0 4px;letter-spacing:-.01em}
.masthead .sub{font-size:10pt;color:#4a4a58;margin:0 0 12px;font-weight:700}
.meta{display:flex;flex-wrap:wrap;gap:6px 0;font-size:8.4pt;border-top:1px solid #e2def7;padding-top:10px}
.meta div{width:50%;color:#3a3a48}
.meta b{color:#111119}

h2{font-size:14pt;margin:22px 0 8px;padding-bottom:5px;border-bottom:2px solid #e2def7;color:#2f1a94;break-after:avoid}
h3{font-size:11pt;margin:16px 0 6px;color:#22222c;break-after:avoid}
h4{font-size:9.8pt;margin:12px 0 5px;color:#33333f;break-after:avoid}
p{margin:0 0 8px}
ul,ol{margin:0 0 9px;padding-left:18px}
li{margin:0 0 3px}
a{color:#4f2fd6;text-decoration:none;word-break:break-word}
strong{color:#0f0f16}
hr{border:none;border-top:1px solid #e6e4f0;margin:16px 0}

/* ---- tables ---- */
table{width:100%;border-collapse:collapse;font-size:8.1pt;margin:8px 0 14px;table-layout:fixed}
thead{display:table-header-group}
tr{break-inside:avoid}
th{background:#f0eefb;text-align:left;font-weight:700;color:#241a54}
th,td{border:1px solid #d9d6e8;padding:4px 6px;vertical-align:top;word-break:break-word;overflow-wrap:anywhere}
tbody tr:nth-child(even){background:#faf9fe}
table.t-wide{font-size:7.3pt}
table.t-wide th,table.t-wide td{padding:3px 4px}
table.t-compact{font-size:8.4pt}

/* ---- code + quotes ---- */
code{font-family:'DejaVu Sans Mono',monospace;font-size:7.9pt;background:#f4f2fb;padding:0 3px;border-radius:3px;color:#2a2050}
pre{background:#f6f5fb;border:1px solid #e6e4f0;border-left:3px solid #4f2fd6;border-radius:4px;
    padding:8px 10px;margin:8px 0 12px;break-inside:avoid;overflow-wrap:anywhere}
pre code{font-size:7.3pt;background:none;padding:0;line-height:1.45;white-space:pre-wrap;display:block;color:#20203a}
blockquote{margin:10px 0 12px;padding:8px 12px;background:#f6f5fb;border-left:4px solid #b9aef0;border-radius:0 4px 4px 0}
blockquote p{margin:0 0 5px;font-size:9pt;color:#33333f}
blockquote p:last-child{margin-bottom:0}
blockquote strong{color:#2f1a94}

/* ---- issue register, rendered as cards ---- */
.reg{margin:10px 0 4px}
.issue{break-inside:avoid;border:1px solid #dedbf0;border-radius:8px;margin:0 0 9px;overflow:hidden}
.issue__head{display:flex;align-items:baseline;gap:9px;background:#f6f4fe;
             border-bottom:1px solid #e6e3f6;padding:6px 10px}
.issue__id{font-family:'DejaVu Sans Mono',monospace;font-size:8.3pt;font-weight:700;color:#2f1a94;white-space:nowrap}
.issue__title{flex:1;font-size:8.9pt;font-weight:700;color:#17171f}
.issue__body{display:grid;grid-template-columns:1fr 1fr}
.cell{padding:6px 10px;font-size:8.1pt;border-top:1px solid #f0edf9}
.cell:nth-child(1),.cell:nth-child(2){border-top:none}
.cell--full{grid-column:1 / -1}
.cell--fix{background:#fbfaff}
.cell__k{display:block;font-size:6.7pt;letter-spacing:.13em;text-transform:uppercase;
         font-weight:700;color:#71718a;margin-bottom:3px}
.cell code{font-size:7.4pt}

/* ---- status marks + severity pills ---- */
.st{font-weight:700;font-family:'DejaVu Sans',sans-serif}
.st--ok{color:#0a7d3c}
.st--no{color:#c02222}
.st--warn{color:#b26a00}
.sev{display:inline-block;padding:1px 5px;border-radius:8px;font-size:7.2pt;font-weight:700;
     white-space:nowrap;color:#fff;letter-spacing:.02em}
.sev--blocker{background:#a31414}
.sev--critical{background:#c02222}
.sev--high{background:#b26a00}
.sev--medium{background:#7a6a00}
.sev--low{background:#3f7a3f}
.sev--info{background:#5a5a6e}
.pagebreak{break-before:page}
@media print{h2{orphans:3;widows:3}}
"""


def build(md_text: str) -> str:
    # -- pull the title + metadata out of the markdown so we can render a masthead
    title = "Website Quality Audit"
    for line in md_text.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            break

    body = md_text
    # drop the leading H1 and the metadata block lines (they go in the masthead)
    body = re.sub(r"^# .*\n", "", body, count=1)
    meta = {}
    for key in ("Site", "Audit date", "Auditor method", "Deployed build identified"):
        m = re.search(r"^\*\*%s:\*\*\s*(.+)$" % re.escape(key), body, re.M)
        if m:
            meta[key] = m.group(1).strip()
            body = body.replace(m.group(0), "", 1)

    html_body = markdown.markdown(
        body,
        extensions=["tables", "fenced_code", "sane_lists", "attr_list"],
        output_format="html5",
    )

    SEVERITIES = ("Blocker", "Critical", "High", "Medium", "Low", "Info")

    def pill(word):
        return '<span class="sev sev--%s">%s</span>' % (word.lower(), word)

    def clean(cell):
        """Strip the outer <td>/<p> wrapper so a cell can live in the card grid."""
        cell = re.sub(r"</?td[^>]*>", "", cell).strip()
        cell = re.sub(r"^<p>|</p>$", "", cell).strip()
        # a severity cell becomes its pill
        stripped = re.sub(r"</?(?:strong|p)>", "", cell).strip()
        if stripped in SEVERITIES:
            return pill(stripped)
        return cell

    def to_cards(table):
        """The 7-column issue register reads far better as stacked cards."""
        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", table, flags=re.S)
        cells = [re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", r, flags=re.S) for r in rows]
        cells = [c for c in cells if c]
        if not cells or len(cells[0]) != 7:
            return None

        out = ['<div class="reg">']
        for row in cells[1:]:  # row 0 is the header
            ident, sev, issue, repro, expected, actual, fix = [clean(c) for c in row]
            out.append(
                '<div class="issue">'
                '<div class="issue__head"><span class="issue__id">%s</span>%s'
                '<span class="issue__title">%s</span></div>'
                '<div class="issue__body">'
                '<div class="cell"><span class="cell__k">Reproduction</span>%s</div>'
                '<div class="cell"><span class="cell__k">Expected</span>%s</div>'
                '<div class="cell"><span class="cell__k">Actual</span>%s</div>'
                '<div class="cell cell--full cell--fix"><span class="cell__k">Fix</span>%s</div>'
                "</div></div>" % (ident, sev, issue, repro, expected, actual, fix)
            )
        out.append("</div>")
        return "".join(out)

    def table_dispatch(match):
        table = match.group(0)
        cards = to_cards(table)
        if cards is not None:
            return cards
        cols = table.count("<th")
        cls = "t-wide" if cols >= 6 else ("t-compact" if cols <= 3 else "")
        if cls:
            table = table.replace("<table>", '<table class="%s">' % cls, 1)
        return table

    html_body = re.sub(r"<table>.*?</table>", table_dispatch, html_body, flags=re.S)

    # -- severity pills anywhere else they appear as a whole cell
    html_body = re.sub(
        r"<td([^>]*)>\s*(?:<strong>)?(Blocker|Critical|High|Medium|Low|Info)(?:</strong>)?\s*</td>",
        lambda m: '<td%s><span class="sev sev--%s">%s</span></td>'
        % (m.group(1), m.group(2).lower(), m.group(2)),
        html_body,
    )

    # -- emoji have no font on this machine: swap them for glyphs DejaVu Sans has
    html_body = html_body.replace("\u2705", '<span class="st st--ok">\u2713</span>')
    html_body = html_body.replace("\u274c", '<span class="st st--no">\u00d7</span>')
    html_body = html_body.replace("\u26a0\ufe0f", '<span class="st st--warn">!</span>')
    html_body = html_body.replace("\u26a0", '<span class="st st--warn">!</span>')

    masthead_meta = "".join(
        "<div><b>%s:</b> %s</div>"
        % (
            html.escape(k),
            html.escape(meta.get(k, "").replace("`", "")),
        )
        for k in ("Site", "Audit date", "Deployed build identified", "Auditor method")
        if meta.get(k)
    )

    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Test Report \u2014 learn.dartsai.in</title>
<style>%s
%s</style></head>
<body>
<div class="masthead">
  <p class="kicker">Test Report</p>
  <h1>%s</h1>
  <p class="sub">Production-readiness audit \u00b7 Darts Ai Academy \u00b7 learn.dartsai.in</p>
  <div class="meta">%s</div>
</div>
%s
</body></html>""" % (
        font_face_css(),
        CSS,
        html.escape(title),
        masthead_meta,
        html_body,
    )


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    out = build(pathlib.Path(src).read_text(encoding="utf-8"))
    pathlib.Path(dst).write_text(out, encoding="utf-8")
    print("wrote %s (%.1f KB)" % (dst, len(out) / 1024))
