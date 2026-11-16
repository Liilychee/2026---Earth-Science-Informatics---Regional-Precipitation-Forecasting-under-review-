import re, json, sys
R = sys.argv[1]
def excerpts(t):
    out, k = [], 0
    while True:
        k = t.find('\\RevisedExcerpt{', k)
        if k < 0: return out
        s = k + len('\\RevisedExcerpt{'); depth, j = 1, s
        while depth:
            depth += {'{': 1, '}': -1}.get(t[j], 0); j += 1
        out.append((k, t[s:j-1])); k = j
def canon(s):
    s = re.sub(r'\\hypersetup\{[^}]*\}', '', s)
    s = re.sub(r'\\(textcolor|color)\{[^}]*\}', '', s)
    s = re.sub(r'\\(revminor|revised|par)\b', '', s)
    s = s.replace('{', '').replace('}', '')
    return re.sub(r'\s+', ' ', s).strip()
L = open('Response letter.tex', encoding='utf-8').read()
B = open(f'{R}/before/Response letter.tex', encoding='utf-8').read()
src = canon(open('manuscript.tex', encoding='utf-8').read()) + ' ||| ' + canon(open('Supplementary.tex', encoding='utf-8').read())
ex = excerpts(L)
miss = [i for i, (_, e) in enumerate(ex) if canon(e) not in src]
def outside(t):
    i = t.index('% Review ID: R4 m8'); j = t.index('% Review ID: R4 m9')
    return [e for k, e in excerpts(t) if not (i <= k < j)], [e for k, e in excerpts(t) if i <= k < j]
oa, ia = outside(L); ob, ib = outside(B)
res = {"total_excerpts": len(ex), "matched": len(ex) - len(miss), "missing_idx": miss,
       "outside_R4m8_equal_baseline": oa == ob, "outside_count": len(oa), "baseline_total": len(excerpts(B)),
       "inside_R4m8_new": len(ia)}
print(json.dumps(res, indent=2)); json.dump(res, open(f'{R}/VERIFICATION.json', 'w'), indent=2)
