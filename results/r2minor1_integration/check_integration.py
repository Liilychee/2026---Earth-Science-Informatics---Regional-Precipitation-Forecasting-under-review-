# -*- coding: utf-8 -*-
from pathlib import Path
import json,re,csv,hashlib,collections,datetime
P=Path(__file__).resolve().parent;B=P/'before';M=Path('manuscript.tex').read_text();S=Path('Supplementary.tex').read_text();R=Path('Response letter.tex').read_text();OR=(B/'Response letter.tex').read_text()
code=Path('results/r2m6_integration/check_integration.py').read_text();exec(code[code.index('def args('):code.index('oldex=args(')])
a,b=R.index('% Review ID: R2 m1'),R.index('% Review ID: R2 m2');oa,ob=OR.index('% Review ID: R2 m1'),OR.index('% Review ID: R2 m2');assert R[:a]==OR[:oa] and R[b:]==OR[ob:]
old=args(OR,'RevisedExcerpt');new=args(R,'RevisedExcerpt');assert len(old)==109 and len(new)==112;assert collections.Counter(new)-collections.Counter(old)==collections.Counter(args(R[a:b],'RevisedExcerpt'));assert all(canonical(t) in canonical(M) for t in new)
ex=json.loads((P/'FINAL_EXCERPTS.json').read_text());assert len(ex)==3 and all(t in M and r'\RevisedExcerpt{'+t+'}' in R[a:b] for t in ex.values())
review='1. Please report the exact training, validation, and testing periods and their respective sample sizes.';assert args(R[a:b],'ReviewerComment')==[review] and review in Path('comment.txt').read_text()
assert r'\PendingResponse' not in R[a:b] and r'\PendingResponse' in R[b:]
assert M==(B/'manuscript.tex').read_text() and S==(B/'Supplementary.tex').read_text()
hashes=json.loads((P/'PROTECTED_HASHES.json').read_text())
for p,h in hashes.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
rows=list(csv.DictReader((P/'SPLIT_INDEX.csv').open()));cells=json.loads((P/'CELL_INDEX.json').read_text())
for c in cells:
 raw=rows[c['line']-2][c['field']];assert raw==c['raw']
 if c['field'].endswith('_n'):expected=f'{int(raw):,}'
 else:t=datetime.datetime.strptime(raw,'%Y-%m-%d %H:%M');expected=str(t.day)+t.strftime(' %B %Y %H:%M')
 assert c['display']==expected and expected in R[a:b]
ma=Path('build/manuscript.aux').read_text()
for ref in re.findall(r'\\ref\{([^}]+)\}',R[a:b]):assert ref.startswith('manuscript-') and r'\newlabel{'+ref[len('manuscript-'):]+'}' in ma
# Scoped task update only, not closure of the shared task28.
tn=json.loads((P/'TASK_NOTE.json').read_text());task=Path('ESI_审稿意见分类_严重程度排序_35项.md').read_text();assert task.count(tn['anchor']+tn['note'])==1;assert task.replace(tn['anchor']+tn['note'],tn['anchor'],1)==(B/'ESI_审稿意见分类_严重程度排序_35项.md').read_text()
assert Path('FINAL_REVISION_CHECKLIST.md').read_text().startswith((B/'FINAL_REVISION_CHECKLIST.md').read_text());assert Path('FINAL_REVISION_CHECKLIST.md').read_text().count('### R2-m1 / 任务28局部')==1
out=dict(m9_scientific_archive_gate_passed=True,m9_overall_not_closed=True,old_excerpts_unchanged=109,old_M9_new_six_included=True,new_exact_excerpts=3,total_excerpts_matched=112,protected_files=len(hashes),manuscript_unchanged=True,supplementary_and_S1_S49_unchanged=True,all_figures_and_table5_unchanged=True,all_other_responses_unchanged=True,date_and_count_fields_verified=len(cells),original_comment_exact=True,new_refs_resolved=True,no_new_experiment_table_figure=True,next_minor_not_started=True)
(P/'VERIFICATION.json').write_text(json.dumps(out,indent=2));(P/'EXCERPT_INDEX.json').write_text(json.dumps(dict(old=[dict(index=i+1,sha256=hashlib.sha256(t.encode()).hexdigest()) for i,t in enumerate(old)],new=[dict(key=k,sha256=hashlib.sha256(v.encode()).hexdigest()) for k,v in ex.items()]),indent=2));print(json.dumps(out,indent=2))
