"""Apply the hand edits of the 2026-11-13 diff.tex to a fresh latexdiff output.
Usage: python postprocess_diff.py <raw_diff> <original_manuscript.tex> <manuscript.tex> <original.aux> <latexdiff> <workdir> <out>"""
import re, sys, subprocess, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fix_steps
raw, old_ms, new_ms, old_aux, LD, work, out = sys.argv[1:8]
t = open(raw, encoding='utf-8').read()
new = open(new_ms, encoding='utf-8').read(); old = open(old_ms, encoding='utf-8').read()
log = []
# 1. header comments
t = ("% R1-m2: retain revised labels; remove labels only from deleted equations.\n"
     "% Deleted references to moved/retired figures retain their original numbers.\n") + t
# 2. abstract as inline word diff instead of whole-block delete/add
def inner(s):
    i = s.index('\\abstract{') + len('\\abstract{'); d = 1; j = i
    while d: d += {'{': 1, '}': -1}.get(s[j], 0); j += 1
    return s[i:j - 1]
ao, an = inner(old), inner(new)
open(f'{work}/abs_old.tex', 'w').write(ao); open(f'{work}/abs_new.tex', 'w').write(an)
absdiff = subprocess.run([LD, '--append-textcmd=revminor,revised,textcolor', f'{work}/abs_old.tex', f'{work}/abs_new.tex'], capture_output=True, text=True).stdout
absdiff = '\n'.join(l for l in absdiff.split('\n') if not l.startswith('%DIF ')).strip('\n')
m = re.search(r'\\DIFdelbegin %DIFDELCMD < \\abstract\{\n.*?\\DIFdelend \\DIFaddbegin \\abstract\{\n(.*?)\n\\DIFaddend \n', t, re.S)
assert m, 'abstract block not found'
# keep the following keywords block that latexdiff placed inside the added abstract
tail = m.group(1)[m.group(1).find('\n\n\\keywords'):] if '\n\n\\keywords' in m.group(1) else ''
t = t[:m.start()] + '\\abstract{\n' + absdiff + '\n}\n' + t[m.end():]
log.append(f'abstract inline diff ({len(absdiff)} chars)')
# 3. remove active \label{} of labels that no longer exist (deleted equations/figures)
newlabels = set(re.findall(r'\\label\{([^}]*)\}', '\n'.join(re.split(r'(?<!\\)%', l)[0] if not l.lstrip().startswith('%') else '' for l in new.split('\n'))))
def droplabel(mm):
    return '' if mm.group(1) not in newlabels else mm.group(0)
lines = t.split('\n'); n3 = 0
for k, l in enumerate(lines):
    if l.lstrip().startswith('%'): continue
    l2 = re.sub(r'\\label\{([^}]*)\}', droplabel, l)
    if l2 != l: n3 += 1; lines[k] = l2
t = '\n'.join(lines); log.append(f'labels of deleted items removed on {n3} lines')
# 3b. labels duplicated by deleted equation copies
t = fix_steps.drop_deleted_eq_labels(t, log)
# 4. \ref to retired labels -> original numbers
auxn = dict(re.findall(r'\\newlabel\{([^}]*)\}\{\{([^}]*)\}', open(old_aux, encoding='utf-8', errors='ignore').read()))
n4 = []
def fixref(mm):
    k = mm.group(1)
    if k in newlabels: return mm.group(0)
    if k in auxn: n4.append(k); return auxn[k]
    return mm.group(0)
lines = t.split('\n')
for k, l in enumerate(lines):
    if l.lstrip().startswith('%'): continue
    lines[k] = re.sub(r'\\ref\{([^}]*)\}', fixref, l)
t = '\n'.join(lines); log.append(f'retired refs numbered: {sorted(set(n4))}')
# 5. table additions coloured without underlining (two anchors used in the 11-13 file)
a1 = '\\renewcommand{\\arraystretch}{1.2}\n\\begin{tabularx}{\\textwidth}{@{}p{0.17\\textwidth}X'
if a1 in t:
    t = t.replace(a1, '\\renewcommand{\\arraystretch}{1.2}\n% Diff-only table additions use colour without underlining to preserve wrapping.\n\\renewcommand{\\DIFaddFL}[1]{{\\color{blue}#1}}\n\\begin{tabularx}{\\textwidth}{@{}p{0.17\\textwidth}X', 1); log.append('DIFaddFL redefinition 1 inserted')
a2 = '\\label{tab:seed_stability}\n\\small\n\\setlength{\\tabcolsep}{4pt}\n'
if a2 in t:
    t = t.replace(a2, a2 + '% R1-m5: colour table additions without underlining to preserve cell baselines.\n\\renewcommand{\\DIFaddFL}[1]{{\\leavevmode\\color{blue}#1}}\n', 1); log.append('DIFaddFL redefinition 2 inserted')
# 6. Table 3 header cells: drop begin/end markers inside \textbf cells (as in the 11-13 file)
t = t.replace('\\textbf{RMSE\\DIFdelbeginFL \\DIFdelFL{(mm)}\\DIFdelendFL }', '\\textbf{RMSE \\DIFdelFL{(mm)} }')
t = t.replace('\\textbf{MAE\\DIFdelbeginFL \\DIFdelFL{(mm)}\\DIFdelendFL }', '\\textbf{MAE \\DIFdelFL{(mm)} }')
# 7. Table 3 body: markers between table rows break the alignment (same removals as the 11-13 file)
i = t.find('\label{tab:seed_stability}'); j = t.find('\end{table}', i)
blk = t[i:j]
for x, y in [('\DIFaddendFL \hline', ' \hline'),
             ('\DIFdelbeginFL %DIFDELCMD < \end{tabular}', ' %DIFDELCMD < \end{tabular}'),
             (r'\DIFdelendFL \DIFaddbeginFL \revminor{Climatology', r'  \revminor{Climatology')]:
    if x in blk: blk = blk.replace(x, y, 1); log.append('table 3 marker removed: ' + x[:30])
t = t[:i] + blk + t[j:]
# 8. underline inside colour macros so added red text can break across lines
t = fix_steps.push_diffadd_inside(t, log)
open(out, 'w', encoding='utf-8').write(t)
print('\n'.join(log))
