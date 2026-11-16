import re, json, sys, collections
R = sys.argv[1]
def cites(t):
    t = '\n'.join(l for l in t.split('\n') if not l.lstrip().startswith('%'))
    out = []
    for m in re.finditer(r'\\cite(t|p)(\[[^\]]*\])*\{([^}]*)\}', t):
        out += [(m.group(1), k.strip()) for k in m.group(3).split(',')]
    return out
b = cites(open(f'{R}/before/manuscript.tex').read()); a = cites(open('manuscript.tex').read())
bk = re.findall(r'@\w+\{([^,\s]+),', open('sn-bibliography.bib').read())
bbl = re.findall(r'\\bibitem\[[^\n]*?\]\{([^}]+)\}', open('build/manuscript.bbl').read())
log = open('build/manuscript.log').read()
prot = [o['key'] for o in json.load(open(f'{R}/evidence/citet_sentences_before.json'))
        if o['protected_excerpts'] and o['key'] != 'palharini2021assessment']  # palharini: splitter artefact, verified unprotected
remaining = [k for c, k in a if c == 't']
v = json.load(open(f'{R}/VERIFICATION.json'))
v.update({
 "cite_keys_before": len(set(k for _, k in b)), "cite_keys_after": len(set(k for _, k in a)),
 "key_multiset_equal": collections.Counter(k for _, k in b) == collections.Counter(k for _, k in a),
 "citation_key_occurrences_before": len(b), "citation_key_occurrences_after": len(a),
 "citet_before": sum(c == 't' for c, _ in b), "citet_after": sum(c == 't' for c, _ in a),
 "citep_before": sum(c == 'p' for c, _ in b), "citep_after": sum(c == 'p' for c, _ in a),
 "keys_missing_in_bib": sorted(set(k for _, k in a) - set(bk)),
 "duplicate_bib_keys": [k for k, n in collections.Counter(bk).items() if n > 1],
 "bbl_bibitems": len(bbl), "keys_cited_not_in_bbl": sorted(set(k for _, k in a) - set(bbl)),
 "undefined_citation_warnings": len(re.findall(r'Citation .* undefined', log)),
 "remaining_citet_keys": remaining,
 "remaining_citet_all_protected": collections.Counter(remaining) == collections.Counter(prot),
 "manuscript_overfull_last_run": log.count('\nOverfull'), "overfull_baseline": 111})
json.dump(v, open(f'{R}/VERIFICATION.json', 'w'), indent=2); print(json.dumps(v, indent=1))
