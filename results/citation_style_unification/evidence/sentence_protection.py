import re, json, sys
sys.path.insert(0, sys.argv[1] + '/evidence')
R = sys.argv[1]
exec(open(f'{R}/evidence/inventory.py').read().split('L = open')[0].split('R = sys.argv')[1].split('\n',1)[1])
L = open('Response letter.tex', encoding='utf-8').read()
EX = [canon(e) for e in excerpts(L)]
T = open('manuscript.tex', encoding='utf-8').read()
# sentence split on '. ' followed by capital/backslash, ignoring 'et al.' 'e.g.' etc.
out = []
for m in re.finditer(r'\\citet(\[[^\]]*\])*\{([^}]*)\}', T):
    ln = T.count('\n', 0, m.start()) + 1
    a = max(T.rfind('. ', 0, m.start()), T.rfind('\n', 0, m.start()), T.rfind('{', 0, m.start()) if T[m.start()-1]=='{' else -1)
    a = a + 2 if T[a:a+2] == '. ' else a + 1
    b = m.end()
    while True:
        b2 = re.search(r'\.(\s|\}|$)', T[b:]); b = b + b2.end(); 
        if not re.search(r'(e\.g|i\.e|et al|approx|Fig|Sect|Eq)\.\s*$', T[a:b].rstrip()): break
    s = T[a:b].strip(); cs = canon(s)
    wins = {cs[i:i+30] for i in range(0, max(1, len(cs)-29), 5)}
    prot = sorted({i for i, e in enumerate(EX) for w in wins if w in e})
    out.append(dict(line=ln, key=m.group(2), sentence=s, protected_excerpts=prot))
json.dump(out, open(f'{R}/evidence/citet_sentences_before.json', 'w'), indent=1, ensure_ascii=False)
for o in out: print(o['line'], o['key'], o['protected_excerpts'], '|', o['sentence'][:260].replace('\n',' '), '\n')
