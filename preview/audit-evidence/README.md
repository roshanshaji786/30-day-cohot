# Evidence for AUD-01 (design tokens dropped in real browsers)

## 1. Live condition (captured from https://learn.dartsai.in/cart, W3C Nu "source" view, lines 30-66)

    <style data-shopify>
        Liquid error (layout/theme line 44): font_face can only be used with a font drop

        Liquid error (layout/theme line 47): font_face can only be used with a font drop

        :root{
          --font-heading: Assistant, sans-serif;
          ...
          --shadow-lg: 0 24px 64px rgba(16, 16, 32, .14);
        }
      </style>

The Nu checker reports on that region, on every page tested:
`CSS: Parse Error.` — "From line 61, column 6; to line 62, column 2" — extract: `14);↩    }↩  </styl`

## 2. Reproduction (Chromium 153)

    LD_LIBRARY_PATH=/tmp/al2023x/lib node probe.cjs

| case | contents | --c-accent | probe background |
|------|----------|-----------|------------------|
| A | Liquid error lines + shipped tokens (#4f2fd6) | (EMPTY) | rgb(79, 47, 214) |
| B | tokens only, no Liquid errors | #4f2fd6 | rgb(79, 47, 214) |
| C | Liquid error lines + merchant sets #ff0000 | (EMPTY) | rgb(79, 47, 214)  <-- should be RED |

Case C is the bug: a merchant colour change is silently ignored because the whole
`:root{...}` block is consumed by the invalid selector created by the error text.

## 3. Root cause and fix

`layout/theme.liquid` lines 46-51 pass `font_modify` results straight into `font_face`.
`font_modify` returns nil when the chosen font family has no such variant, and
`nil | font_face` emits the error string above into the stylesheet.

    assign heading_font_bold  = heading_font | font_modify: 'weight', 'bold'   | default: heading_font
    assign heading_font_black = heading_font | font_modify: 'weight', 'bolder' | default: heading_font_bold
    assign body_font_bold     = body_font  | font_modify: 'weight', 'bold'    | default: body_font
    assign body_font_italic   = body_font  | font_modify: 'style', 'italic'   | default: body_font

Acceptance test after deploy: the Nu "CSS: Parse Error" must disappear, and
`getComputedStyle(document.documentElement).getPropertyValue('--c-accent')` must
return a value in DevTools.
