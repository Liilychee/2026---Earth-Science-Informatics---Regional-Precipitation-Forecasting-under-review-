import re
def drop_deleted_eq_labels(t, log):
    """Remove \\label{X} lines that sit at the end of a deleted equation copy
    (pattern: \\label{X} immediately followed by }\\end{displaymath}%DIFAUXCMD) when X is also defined elsewhere."""
    lines = t.split('\n'); keep = []; removed = []
    for k, l in enumerate(lines):
        mm = re.fullmatch(r'\s*\\label\{([^}]*)\}\s*', l)
        nxt = lines[k + 1] if k + 1 < len(lines) else ''
        if mm and nxt.startswith('}\\end{displaymath}') and t.count('\\label{' + mm.group(1) + '}') > 1:
            removed.append(mm.group(1)); continue
        keep.append(l)
    log.append(f'duplicate labels removed from deleted equations: {removed}')
    return '\n'.join(keep)

def _arg(s, i):
    """s[i] == '{' ; return index after matching brace"""
    d = 0; j = i
    while True:
        c = s[j]
        if c == '\\': j += 2; continue
        if c == '{': d += 1
        elif c == '}':
            d -= 1
            if d == 0: return j + 1
        j += 1

def push_diffadd_inside(t, log):
    """\\DIFadd{ ... \\textcolor{red}{X} ... \\revminor{Y} ... } ->
    \\textcolor{red}{\\DIFadd{X}} \\revminor{\\DIFadd{Y}} with remaining plain text kept in \\DIFadd{}.
    ulem cannot break lines inside a macro argument, so the underline must be inside the colour macro."""
    out = []; i = 0; n = 0
    pat = re.compile(r'\\DIFadd\{')
    while True:
        m = pat.search(t, i)
        if not m: out.append(t[i:]); break
        out.append(t[i:m.start()])
        b = m.end() - 1; e = _arg(t, b); arg = t[b + 1:e - 1]
        if not re.search(r'\\(textcolor\{[^}]*\}|revminor)\{', arg):
            out.append(t[m.start():e]); i = e; continue
        n += 1; pieces = []; j = 0; buf = ''
        while j < len(arg):
            mm = re.compile(r'\\textcolor\{[^}]*\}\{|\\revminor\{').match(arg, j)
            if mm:
                if buf.strip(): pieces.append('\\DIFadd{' + buf + '}')
                elif buf: pieces.append(buf)
                buf = ''
                ab = mm.end() - 1; ae = _arg(arg, ab)
                pieces.append(arg[j:ab] + '{\\DIFadd{' + arg[ab + 1:ae - 1] + '}}')
                j = ae
            else:
                if arg[j] == '\\' and j + 1 < len(arg): buf += arg[j:j + 2]; j += 2
                elif arg[j] == '{': ae = _arg(arg, j); buf += arg[j:ae]; j = ae
                else: buf += arg[j]; j += 1
        if buf.strip(): pieces.append('\\DIFadd{' + buf + '}')
        elif buf: pieces.append(buf)
        out.append(''.join(pieces)); i = e
    log.append(f'DIFadd blocks with colour macros pushed inside: {n}')
    return ''.join(out)
