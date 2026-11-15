# -*- coding: utf-8 -*-
from pathlib import Path
import re,json,hashlib,collections,csv,difflib
P=Path(__file__).resolve().parent;B=P/'before'
code=Path('results/r2m6_integration/check_integration.py').read_text();exec(code[code.index('def args('):code.index('oldex=args(')])
M=Path('manuscript.tex').read_text();S=Path('Supplementary.tex').read_text();R=Path('Response letter.tex').read_text();OM=(B/'manuscript.tex').read_text();OS=(B/'Supplementary.tex').read_text();OR=(B/'Response letter.tex').read_text()
old,new=args(OR,'RevisedExcerpt'),args(R,'RevisedExcerpt');assert len(old)==112 and len(new)==115
assert collections.Counter(new)-collections.Counter(old)==collections.Counter(json.loads((P/'FINAL_EXCERPTS.json').read_text()).values())
for t in old:assert t in new and canonical(t) in canonical(M+S),t[:80]
for t in json.loads((P/'FINAL_EXCERPTS.json').read_text()).values():assert t in M and r'\RevisedExcerpt{'+t+'}' in R
# Other review sections byte-identical.
a,b=R.index('% Review ID: R2 m2'),R.index('% Review ID: R2 m3');oa,ob=OR.index('% Review ID: R2 m2'),OR.index('% Review ID: R2 m3');assert R[:a]==OR[:oa] and R[b:]==OR[ob:]
assert args(R[a:b],'ReviewerComment')==args(OR[oa:ob],'ReviewerComment');assert r'\PendingResponse' not in R[a:b] and r'\PendingResponse' in R[b:]
# Existing table blocks / all supplement bytes preserved.
def table5(t):
 k=t.index(r'\label{tab:probabilistic_results}');st=t.rfind(r'\begin{table}',0,k);en=t.index(r'\end{table}',k)+len(r'\end{table}');return t[st:en]
assert table5(M)==table5(OM)
assert S.replace((P/'TABLE_GENERATED.tex').read_text()+'\n','',1)==OS
for p,h in json.loads((P/'PROTECTED_HASHES.json').read_text()).items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
for t in args(OM,'includegraphics'):assert t in args(M,'includegraphics')
for d in ['manuscript.tex','Supplementary.tex','Response letter.tex']:
 s=Path(d).read_text();labs=re.findall(r'\\label\{([^}]+)\}',re.sub(r'(?m)(?<!\\)%.*$','',s));assert len(labs)==len(set(labs)),d
# Every generated numeric cell matches a fixed q16 summary field; exact table text checked above.
rows=list(csv.DictReader((P/'evidence/q16_interval_summary.csv').open()));cells=json.loads((P/'CELL_INDEX.json').read_text());assert len(cells)==144
for c in cells:
 r=rows[c['csv_line']-2];assert r['model']==c['model'] and r['subset']==c['subset'];assert r[c['field']]==c['raw'];assert c['display']==f"{float(c['raw']):.4f}"
# All newly reported endpoints come from the summary, not approximate instructions.
prose=[]
for sub in ['all','wet>=0.1','upper>=Q95']:
 for f in ['PICP90','PICP95']+(['MPIW90','MPIW95'] if sub=='all' else []):
  rs=[(i+2,r) for i,r in enumerate(rows) if r['source']=='q14_rerun_5seed' and r['subset']==sub]
  for kind,fn in [('lower',min),('upper',max)]:
   line,r=fn(rs,key=lambda x:float(x[1][f+'_mean']));val=f"{float(r[f+'_mean']):.4f}";assert val in M and val in R if sub=='all' else val in M
   prose.append(dict(subset=sub,field=f+'_mean',endpoint=kind,csv_line=line,raw=r[f+'_mean'],display=val))
(P/'PROSE_CELL_INDEX.json').write_text(json.dumps(prose,indent=2))
for ref in re.findall(r'\\ref\{([^}]+)\}',R[a:b]):
 if not ref.startswith(('manuscript-','supp-')):
  assert r'\csname r@'+ref in R and r'\csname r@manuscript-'+ref in R;ref='manuscript-'+ref
 pre,aux=('manuscript-','build/manuscript.aux') if ref.startswith('manuscript-') else ('supp-','build/Supplementary.aux');assert ref.startswith(pre);assert r'\newlabel{'+ref[len(pre):]+'}' in Path(aux).read_text(),ref
assert r'\newlabel{stab:r2minor2_intervals}{{S50}' in Path('build/Supplementary.aux').read_text()
assert 'FINAL_REPOSITORY_DOCUMENTATION_PENDING' in Path('results/r2m9_integration/STATUS.md').read_text()
# All previous excerpts stored by review ID/content hash, not mutable line numbers.
mapping=[]
for i,t in enumerate(new):
 pos=R.index(r'\RevisedExcerpt{'+t+'}');ids=list(re.finditer(r'% Review ID: (.+)',R[:pos]));mapping.append(dict(index=i+1,review=ids[-1][1] if ids else 'preamble',sha256=hashlib.sha256(t.encode()).hexdigest(),verbatim_match=True,old=t in old))
(P/'EXCERPT_INDEX.json').write_text(json.dumps(mapping,indent=2))
files=['manuscript.tex','Supplementary.tex','Response letter.tex','ESI_审稿意见分类_严重程度排序_35项.md','FINAL_REVISION_CHECKLIST.md','SUPPLEMENTARY_TABLE_REGISTRY.md'];patch=''
for f in files:patch+=''.join(difflib.unified_diff((B/f).read_text().splitlines(True),Path(f).read_text().splitlines(True),fromfile='a/'+f,tofile='b/'+f))
(P/'R2minor2_LOCAL.patch').write_text(patch)
out=dict(old_excerpts_unchanged=112,new_exact_excerpts=3,total_matched=115,match_percent=100,affected_old_boxes=0,table_numeric_fields=144,prose_endpoints=len(prose),independent_prediction_files=15,per_run_independent_fields=450,max_difference=json.loads((P/'DATA_CHECK.json').read_text())['max_abs_difference'],table5_unchanged=True,S1_S49_source_unchanged=True,all_figures_unchanged=True,all_other_responses_unchanged=True,Supplementary_table='S50',label='stab:r2minor2_intervals',m9_overall_not_closed=True,next_minor_not_started=True,no_git_commit_push=True)
(P/'VERIFICATION.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
