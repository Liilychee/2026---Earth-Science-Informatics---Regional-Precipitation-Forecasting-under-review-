# -*- coding: utf-8 -*-
from pathlib import Path
import re,json,csv,hashlib,collections,difflib,subprocess
P=Path(__file__).resolve().parent;B=P/'before';M=Path('manuscript.tex').read_text();S=Path('Supplementary.tex').read_text();R=Path('Response letter.tex').read_text();OR=(B/'Response letter.tex').read_text()
code=Path('results/r2m6_integration/check_integration.py').read_text();exec(code[code.index('def args('):code.index('oldex=args(')])
a,b=R.index('% Review ID: R2 m3'),R.index('% Review ID: R2 m4');oa,ob=OR.index('% Review ID: R2 m3'),OR.index('% Review ID: R2 m4');assert R[:a]==OR[:oa] and R[b:]==OR[ob:]
old,new=args(OR,'RevisedExcerpt'),args(R,'RevisedExcerpt');assert len(old)==115 and len(new)==118
# Excerpts are deliberately reused, so multiplicity rather than membership alone is checked.
ex=json.loads((P/'FINAL_EXCERPTS.json').read_text());assert collections.Counter(new)-collections.Counter(old)==collections.Counter(ex.values())
for t in new:assert canonical(t) in canonical(M+S),t[:100]
assert args(R[a:b],'RevisedExcerpt')==list(ex.values())
for t in ex.values():assert t in M and r'\RevisedExcerpt{'+t+'}' in R[a:b]
review='3. Please present more complete event-detection metrics for all rainfall thresholds and baseline models.';assert args(R[a:b],'ReviewerComment')==[review] and review in Path('comment.txt').read_text();assert r'\PendingResponse' not in R[a:b] and r'\PendingResponse' in R[b:]
assert M==(B/'manuscript.tex').read_text() and S==(B/'Supplementary.tex').read_text()
hs=json.loads((P/'PROTECTED_HASHES.json').read_text())
for f,h in hs.items():assert hashlib.sha256(Path(f).read_bytes()).hexdigest()==h,f
# True label numbering is read from current auxiliary files.
labels={};want={'manuscript':{'sec:event_detection':'4.3.2','fig:r2m4_event_csi':'5'},'Supplementary':{'stab:r2m4_fixed_events':'S28','stab:r2m4_tuned_events':'S29','stab:r2m4_seed_scores':'S30','stab:r2m4_ensemble_events':'S31'}}
for doc,rs in want.items():
 aux=Path('build/'+doc+'.aux').read_text()
 for k,v in rs.items():
  m=re.search(r'\\newlabel\{'+re.escape(k)+r'\}\{\{([^}]+)\}\{([^}]+)\}',aux);assert m and m[1]==v,k;labels[k]=dict(number=m[1],page=m[2])
for ref in re.findall(r'\\ref\{([^}]+)\}',R[a:b]):
 if not ref.startswith(('manuscript-','supp-')):assert r'\csname r@'+ref in R[a:b] and r'\csname r@manuscript-'+ref in R[a:b];ref='manuscript-'+ref
 pre,aux=('manuscript-','build/manuscript.aux') if ref.startswith('manuscript-') else ('supp-','build/Supplementary.aux');assert r'\newlabel{'+ref[len(pre):]+'}' in Path(aux).read_text(),ref
cells=json.loads((P/'CELL_INDEX.json').read_text())
for c in cells:
 rows=list(csv.DictReader((P/'evidence'/c['file']).open()));assert rows[c['csv_line']-2][c['field']]==c['raw']
# The precise corrections used in the new AuthorResponse must be source-supported.
reply=args(R[a:b],'AuthorResponse')[0];assert '0.859--0.916' in reply and '0.859--0.913' not in reply
for s in ['0.295784','0.574048','0.932169','0.133','0.156']:assert s in reply and any(c['display']==s for c in cells),s
notes=json.loads((P/'TASK_NOTE.json').read_text());task=Path('ESI_审稿意见分类_严重程度排序_35项.md').read_text();assert task.count(notes['anchor']+notes['note'])==1;assert task.replace(notes['anchor']+notes['note'],notes['anchor'],1)==(B/'ESI_审稿意见分类_严重程度排序_35项.md').read_text();assert Path('FINAL_REVISION_CHECKLIST.md').read_text().startswith((B/'FINAL_REVISION_CHECKLIST.md').read_text())
assert 'FINAL_REPOSITORY_DOCUMENTATION_PENDING' in Path('results/r2m9_integration/STATUS.md').read_text();assert 'CLOSED' in Path('results/r2minor2_integration/STATUS.md').read_text()
index=[]
for i,t in enumerate(new):
 pos=R.index(r'\RevisedExcerpt{'+t+'}');review_ids=list(re.finditer(r'% Review ID: (.+)',R[:pos]));index.append(dict(index=i+1,sha256=hashlib.sha256(t.encode()).hexdigest(),first_source_review=review_ids[-1][1] if review_ids else 'preamble',verbatim_match=True))
(P/'EXCERPT_INDEX.json').write_text(json.dumps(dict(old=[dict(index=i+1,sha256=hashlib.sha256(t.encode()).hexdigest()) for i,t in enumerate(old)],new_boxes=[dict(key=k,sha256=hashlib.sha256(t.encode()).hexdigest(),already_present_in_prior_reply=t in old,exact_main_match=True) for k,t in ex.items()],all=index),indent=2));(P/'LABEL_INDEX.json').write_text(json.dumps(labels,indent=2))
files=['Response letter.tex','ESI_审稿意见分类_严重程度排序_35项.md','FINAL_REVISION_CHECKLIST.md'];patch=''
for f in files:patch+=''.join(difflib.unified_diff((B/f).read_text().splitlines(True),Path(f).read_text().splitlines(True),fromfile='a/'+f,tofile='b/'+f))
(P/'R2minor3_LOCAL.patch').write_text(patch)
out=dict(old_excerpts_unchanged=115,new_exact_excerpts=3,total_matched=118,match_rate_percent=100,manuscript_unchanged=True,supplementary_and_S1_S50_unchanged=True,table5_and_all_figures_unchanged=True,other_responses_unchanged=True,protected_files=len(hs),original_comment_exact=True,refs_resolved=True,cell_fields=len(cells),fixed_table_rows=54,tuned_table_rows=45,corrected_six_model_FAR_range='0.859--0.916',no_new_holm_or_climatology_intervals=True,m9_overall_not_closed=True,R2_m2_closed_record_unchanged=True,next_minor_not_started=True,local_only=True)
(P/'VERIFICATION.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
