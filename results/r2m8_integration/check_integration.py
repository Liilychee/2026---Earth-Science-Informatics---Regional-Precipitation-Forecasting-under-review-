"""Scope, exact excerpts and archived numerical transcription checks only."""
from pathlib import Path
import json,re,csv,hashlib,collections
P=Path(__file__).resolve().parent;B=P/'before';M=Path('manuscript.tex').read_text();S=Path('Supplementary.tex').read_text();R=Path('Response letter.tex').read_text();OR=(B/'Response letter.tex').read_text()
code=Path('results/r2m6_integration/check_integration.py').read_text();exec(code[code.index('def args('):code.index('oldex=args(')])
a,b=R.index('% Review ID: R2 M8'),R.index('% Review ID: R2 M9');oa,ob=OR.index('% Review ID: R2 M8'),OR.index('% Review ID: R2 M9');assert R[:a]==OR[:oa] and R[b:]==OR[ob:]
comment='8.SHAP and feature ablation are applied to different model architectures, limiting direct comparison. Please use a consistent architecture and assess the stability of feature importance across runs.'
assert args(R[a:b],'ReviewerComment')==[comment] and comment in Path('comment.txt').read_text()
old=args(OR,'RevisedExcerpt');new=args(R,'RevisedExcerpt');assert len(old)==97 and len(new)==103;assert collections.Counter(new)-collections.Counter(old)==collections.Counter(args(R[a:b],'RevisedExcerpt'))
assert all(canonical(x) in canonical(M) for x in new)
ex=json.loads((P/'FINAL_EXCERPTS.json').read_text());assert len(ex)==6 and all(v in M and r'\RevisedExcerpt{'+v+'}' in R[a:b] for v in ex.values())
r1=R[R.index('% Review ID: R1 M4'):R.index('% Review ID: R1 M5')];oldr1=OR[OR.index('% Review ID: R1 M4'):OR.index('% Review ID: R1 M5')];assert r1==oldr1;assert len(args(r1,'RevisedExcerpt'))==8
hashes=json.loads((P/'PROTECTED_HASHES.json').read_text())
for path,sha in hashes.items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==sha,path
assert M==(B/'manuscript.tex').read_text() and S==(B/'Supplementary.tex').read_text()
D={p.name:list(csv.DictReader(p.open())) for p in (P/'source').glob('*.csv')};cs=json.loads((P/'CELL_INDEX.json').read_text())
for c in cs:
 r=D[c['file']][c['csv_line']-2];assert all(r[k]==v for k,v in c['criteria'].items());assert r[c['field']]==c['raw'];assert f"{float(c['raw']):.{c['digits']}f}"==c['display'];assert c['display'] in (Path('ESI_审稿意见分类_严重程度排序_35项.md').read_text().replace('−','-') if c.get('destination') else R[a:b])
# All newly cited labels resolve to current build auxiliary definitions.
ma=Path('build/manuscript.aux').read_text();sa=Path('build/Supplementary.aux').read_text()
for label in re.findall(r'\\ref\{([^}]+)\}',R[a:b]):
 pref='manuscript-' if label.startswith('manuscript-') else 'supp-';aux=ma if pref=='manuscript-' else sa
 assert r'\newlabel{'+label[len(pref):]+'}' in aux,label
assert re.search(r'\\newlabel\{fig:r1m4_shap_comparison\}\{\{7\}',ma);assert re.search(r'\\newlabel\{fig:r1m4_ablation_comparison\}\{\{8\}',ma)
for n in range(12,23):assert re.search(r'\\newlabel\{stab:r1m4_[^}]+\}\{\{S'+str(n)+r'\}',sa)
assert len(re.findall(r'\\label\{stab:',S))==47
# Only the two authorized task notes and one checklist append may differ.
task=Path('ESI_审稿意见分类_严重程度排序_35项.md').read_text()
for anchor,note in json.loads((P/'TASK_NOTES.json').read_text()).items():
 assert task.count(anchor+note)==1;task=task.replace(anchor+note,anchor,1)
assert task==(B/'ESI_审稿意见分类_严重程度排序_35项.md').read_text()
checklist=Path('FINAL_REVISION_CHECKLIST.md').read_text();assert checklist.startswith((B/'FINAL_REVISION_CHECKLIST.md').read_text()) and checklist.count('### R2-M8 / 任务10及17局部')==1
assert Path('SUPPLEMENTARY_TABLE_REGISTRY.md').read_bytes()==(B/'SUPPLEMENTARY_TABLE_REGISTRY.md').read_bytes()
assert r'\PendingResponse' not in R[a:b] and r'\ChangeLocation' not in R[a:b]
out=dict(protected_files=len(hashes),prior_excerpts_unchanged=97,new_excerpts_exact=6,total_excerpts_matched=103,r1m4_evidenceboxes_preserved=8,manuscript_byte_identical=True,supplementary_byte_identical=True,table5_and_S1_S47_preserved=True,all_prior_figures_preserved=True,all_other_responses_identical=True,original_reviewer_comment_exact=True,source_csv_display_fields_verified=len(cs),new_references_resolved=True,current_figures=[7,8],supplementary_table_range=['S12','S22'],new_experiments=0,new_figures=0,new_tables=0)
(P/'VERIFICATION.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
# Per-excerpt identities retain the original order, even where an excerpt is reused.
(P/'EXCERPT_INDEX.json').write_text(json.dumps(dict(old=[dict(index=i+1,sha256=hashlib.sha256(x.encode()).hexdigest()) for i,x in enumerate(old)],new=[dict(key=k,sha256=hashlib.sha256(v.encode()).hexdigest()) for k,v in ex.items()],r1m4_8_exact=True),indent=2))
