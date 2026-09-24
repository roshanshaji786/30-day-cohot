"""Mini-Liquid renderer: approximates how this theme renders OUT OF THE BOX
(templates/index.json settings = {} -> schema defaults) for visual auditing."""
import re, json, html, os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'theme')
TAG = re.compile(r'\{%-?\s*(if|elsif|else|endif|unless|endunless)\b(.*?)-?%\}', re.S)

def schema_split(path):
    txt = open(path).read()
    m = re.search(r'\{%\s*schema\s*%\}(.*?)\{%\s*endschema\s*%\}', txt, re.S)
    body = txt[:m.start()] if m else txt
    s = json.loads(m.group(1)) if m else {}
    return body, {st['id']: st['default'] for st in s.get('settings', []) if 'default' in st}

def make_truthy(settings):
    def truthy(cond):
        cond = cond.strip()
        m = re.match(r"section\.settings\.(\w+)\s*!=\s*blank", cond)
        if m: return settings.get(m.group(1), '') not in ('', None)
        m = re.match(r"section\.settings\.(\w+)\s*==\s*blank", cond)
        if m: return settings.get(m.group(1), '') in ('', None)
        m = re.match(r"section\.settings\.(\w+)$", cond)
        if m: return bool(settings.get(m.group(1)))
        m = re.match(r"page_title\s+contains\s+shop\.name", cond)
        if m: return True
        return False
    return truthy

def tokenize(tpl):
    parts, idx = [], 0
    for m in TAG.finditer(tpl):
        parts.append(('txt', tpl[idx:m.start()]))
        parts.append(('tag', m.group(1), m.group(2)))
        idx = m.end()
    parts.append(('txt', tpl[idx:]))
    return parts

def render_conditionals(tpl, settings):
    parts = tokenize(tpl)
    truthy = make_truthy(settings)

    def parse(i, end):
        buf = []
        while i < end:
            p = parts[i]
            if p[0] == 'txt':
                buf.append(p[1]); i += 1; continue
            tag = p[1]
            if tag in ('endif', 'endunless', 'elsif', 'else'):
                return ''.join(buf), i          # let the caller consume it
            if tag in ('if', 'unless'):
                branches = [(tag, p[2])]
                depth, j = 0, i + 1
                while j < end:
                    if parts[j][0] == 'tag':
                        t = parts[j][1]
                        if t in ('if', 'unless'): depth += 1
                        elif t in ('endif', 'endunless'):
                            if depth == 0: break
                            depth -= 1
                        elif depth == 0 and t in ('elsif', 'else'):
                            branches.append((t, parts[j][2]))
                    j += 1
                bounds = [b[1] for b in _branch_bounds(i, branches, j)]
                starts = [i + 1] + [b for _, b in _branch_bounds(i, branches, j)][:-1]
                starts = [i + 1] + [pos + 1 for pos in _branch_positions(i, branches, j)] + [j]
                chosen = None
                for k, (t, cond) in enumerate(branches):
                    ok = True if t == 'else' else (not truthy(cond) if t == 'unless' else truthy(cond))
                    if ok:
                        chosen = (starts[k], starts[k + 1]); break
                if chosen:
                    sub, _ = parse(chosen[0], chosen[1])
                    buf.append(sub)
                i = j + 1; continue
            i += 1
        return ''.join(buf), i

    def _branch_positions(i, branches, j):
        depth, pos, out = 0, i + 1, []
        for _ in branches[1:]:
            while pos < j:
                if parts[pos][0] == 'tag':
                    t = parts[pos][1]
                    if t in ('if', 'unless'): depth += 1
                    elif t in ('endif', 'endunless'):
                        if depth == 0: break
                        depth -= 1
                    elif depth == 0 and t in ('elsif', 'else'):
                        out.append(pos); pos += 1; break
                pos += 1
        return out
    def _branch_bounds(*a): return []

    return parse(0, len(parts))[0]

def render_output(tpl, settings):
    def sub(m):
        expr = m.group(1).strip()
        if expr.startswith("'course.css'"): return '<link rel="stylesheet" href="/course.css">'
        if expr.startswith('content_for_header'):
            return ('<!-- content_for_header: Shopify injects analytics, checkout api token, '
                    'and app/pixel scripts here -->')
        if expr.startswith('content_for_layout'): return '<!--INDEX-->'
        if expr.startswith('request.locale'): return 'en'
        if expr.startswith('routes.root_url'): return '/'
        if expr.startswith('page_title'): return 'AI × Shopify Business Bootcamp'
        if expr.startswith('shop.name'): return 'DARTS AI Academy'
        m2 = re.match(r"section\.settings\.(\w+)\s*(.*)$", expr, re.S)
        if m2:
            key, rest = m2.group(1), m2.group(2)
            val = settings.get(key, '')
            dm = re.search(r"\|\s*default:\s*'([^']*)'", rest)
            if val in ('', None) and dm: val = dm.group(1)
            if 'image_url' in rest:
                return f'<!-- image_tag {key}: NOT SET in default state -> nothing renders -->'
            if 'video_tag' in rest or 'external_video' in rest:
                return f'<!-- video {key}: NOT SET in default state -> nothing renders -->'
            if val in ('', None): return ''
            val = str(val)
            if 'escape' in rest: val = html.escape(val, quote=False)
            if 'newline_to_br' in rest: val = val.replace('\n', '<br>')
            return val
        return ''
    return re.sub(r'\{\{-?\s*(.*?)\s*-?\}\}', sub, tpl, flags=re.S)

def render_section(name):
    body, defaults = schema_split(os.path.join(ROOT, 'sections', name + '.liquid'))
    return render_output(render_conditionals(body, defaults), defaults)

layout, _ = schema_split(os.path.join(ROOT, 'layout', 'theme.liquid'))
layout = render_output(layout, {})
layout = layout.replace("{% section 'course-header' %}", render_section('course-header'))
layout = layout.replace("{% section 'course-footer' %}", render_section('course-footer'))
page = layout.replace('<!--INDEX-->', render_section('main-course'))
page = re.sub(r'\{%.*?%\}', '', page, flags=re.S)
open('page.html', 'w').write(page)
print('rendered index.html:', len(page), 'bytes')
print('tag duplication check -> </header> count:', page.count('</header>'), '| </footer> count:', page.count('</footer>'))
