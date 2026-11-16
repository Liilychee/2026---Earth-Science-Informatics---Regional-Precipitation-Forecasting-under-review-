import re, json, sys
R = sys.argv[1]; M = sys.argv[2] if len(sys.argv) > 2 else 'manuscript.tex'
def excerpts(t):
    out, k = [], 0
    while True:
        k = t.find('\\RevisedExcerpt{', k)
        if k < 0: return out
        s = k + len('\\RevisedExcerpt{'); depth, j = 1, s
        while depth:
            depth += {'{': 1, '}': -1}.get(t[j], 0); j += 1
        out.append(t[s:j-1]); k = j
def canon(s):
    s = re.sub(r'\\hypersetup\{[^}]*\}', '', s)
    s = re.sub(r'\\(textcolor|color)\{[^}]*\}', '', s)
    s = re.sub(r'\\(revminor|revised|par)\b', '', s)
    s = s.replace('{', '').replace('}', '')
    return re.sub(r'\s+', ' ', s).strip()
L = open('Response letter.tex', encoding='utf-8').read()
EX = [canon(e) for e in excerpts(L)]
T = open(M, encoding='utf-8').read()
lines = T.split('\n')
rows = []
for m in re.finditer(r'\\cite(t|p)(\[[^\]]*\])*\{([^}]*)\}', T):
    ln = T.count('\n', 0, m.start()) + 1
    line = lines[ln-1]
    if line.lstrip().startswith('%'): continue
    tok = canon(m.group(0))
    # protected if an excerpt contains the citation token with >=40 chars of its context on either side
    pos = m.start() - sum(len(x)+1 for x in lines[:ln-1])
    pre = canon(line[max(0,pos-80):pos]); post = canon(line[pos+len(m.group(0)):pos+len(m.group(0))+80])
    prot = [i for i, e in enumerate(EX) if tok in e and (pre[-25:] in e or post[:25] in e)]
    rows.append(dict(line=ln, cmd='cite'+m.group(1), keys=m.group(3), protected_excerpts=prot,
                     context=line[max(0,pos-160):pos+len(m.group(0))+200]))
json.dump(rows, open(f'{R}/evidence/citation_inventory_{"before" if M=="manuscript.tex" and len(sys.argv)<=3 else "x"}.json','w'), indent=1, ensure_ascii=False)
print(len(rows), sum(r['cmd']=='citet' for r in rows), sum(r['cmd']=='citep' for r in rows))
for r in rows:
    if r['cmd']=='citet': print(r['line'], r['keys'], 'PROT' if r['protected_excerpts'] else '-', r['protected_excerpts'])
