#!/usr/bin/env python3
"""Rebuild the Reviewer 4 source chain from the archived R3-19 after-state.

usage: rebuild_chain.py <records_root> <work_dir> [--base-from-r4m1-after] [--snapshots <paper_results_dir>]

<records_root> is the directory that contains results/ (the archive checkout).
The R3-19 after-state is not archived (full sources are never uploaded). It is
either supplied in <work_dir>/base/ or, with --base-from-r4m1-after, derived by
reverse-applying R4_M1_LOCAL.patch to the R4-M1 after-state found in
<snapshots>/r4m1m2_integration/before/. Either way its SHA-256 must equal the
archived R3_19_only_after hashes. Every node is checked against the expected
hashes in CHAIN_NODES_EXPECTED.json.
"""
import hashlib, json, os, shutil, subprocess, sys
F = ['manuscript.tex', 'Response letter.tex', 'Supplementary.tex', 'sn-bibliography.bib']
root, work = sys.argv[1], sys.argv[2]
args = sys.argv[3:]
snap = args[args.index('--snapshots') + 1] if '--snapshots' in args else None
C = os.path.join(root, 'results', 'r4_batch_closure')
EXP = json.load(open(os.path.join(C, 'CHAIN_NODES_EXPECTED.json')))
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
state = lambda d: {f: sha(os.path.join(d, f)) for f in F}
def apply(d, patch, reverse=False):
    cmd = ['git', 'apply', '--unsafe-paths'] + (['-R'] if reverse else []) + [os.path.abspath(patch)]
    subprocess.run(cmd, cwd=d, check=True)
cur = os.path.join(work, 'chain'); shutil.rmtree(cur, ignore_errors=True); os.makedirs(cur)
if '--base-from-r4m1-after' in args:
    for f in F: shutil.copy(os.path.join(snap, 'r4m1m2_integration', 'before', f), cur)
    assert state(cur) == EXP['nodes'][1]['state'], 'R4-M1 after-state snapshot mismatch'
    apply(cur, os.path.join(root, EXP['nodes'][1]['patch']), reverse=True)
else:
    for f in F: shutil.copy(os.path.join(work, 'base', f), cur)
report = []
ok = state(cur) == EXP['nodes'][0]['state']; report.append((EXP['nodes'][0]['name'], ok))
assert ok, 'base does not match archived R3-19 after-state'
for n in EXP['nodes'][1:]:
    apply(cur, os.path.join(root, n['patch']))
    ok = state(cur) == n['state']; report.append((n['name'], ok))
    assert ok, f"node mismatch at {n['name']}"
for name, ok in report: print(f'{"OK " if ok else "BAD"} {name}')
print('chain rebuilt byte-for-byte:', all(ok for _, ok in report))
