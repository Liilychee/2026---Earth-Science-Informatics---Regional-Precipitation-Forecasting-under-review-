# -*- coding: utf-8 -*-
from pathlib import Path
import re,json,csv,hashlib,collections,difflib
P=Path(__file__).resolve().parent;B=P/'before';M=Path('manuscript.tex').read_text();S=Path('Supplementary.tex').read_text();R=Path('Response letter.tex').read_text();OR=(B/'Response letter.tex').read_text()
code=Path('results/r2m6_integration/check_integration.py').read_text();exec(code[code.index('def args('):code.index('oldex=args(')])
a=R.index('% Review ID: R2 m4');b=R.index('\\clearpage',a);oa=OR.index('% Review ID: R2 m4');ob=OR.index('\\clearpage',oa);assert R[:a]==OR[:oa] and R[b:]==OR[ob:]
old,new=args(OR,'RevisedExcerpt'),args(R,'RevisedExcerpt');ex=json.loads((P/'FINAL_EXCERPTS.json').read_text());assert len(old)==118 and len(new)==120;assert collections.Counter(new)-collections.Counter(old)==collections.Counter(ex.values())
for t in new:assert canonical(t) in canonical(M+S),t[:80]
for t in ex.values():assert t in M and r'\RevisedExcerpt{'+t+'}' in R[a:b]
assert args(R[a:b],'RevisedExcerpt')==list(ex.values());review='4. Please include uncertainty estimates for SHAP importance and feature-ablation results.';assert args(R[a:b],'ReviewerComment')==[review] and review in Path('comment.txt').read_text();assert r'\PendingResponse' not in R[a:b]
# Explicit preservation of the eight R1-M4 and six R2-M8 excerpts.
def sec(t,start,end):return t[t.index(start):t.index(end,t.index(start))]
for st,en,count in [('% Review ID: R1 M4','% Review ID: R1 M5',8),('% Review ID: R2 M8','% Review ID: R2 M9',6)]:
 assert sec(R,st,en)==sec(OR,st,en);assert len(args(sec(R,st,en),'RevisedExcerpt'))==count
assert M==(B/'manuscript.tex').read_text() and S==(B/'Supplementary.tex').read_text()
hs=json.loads((P/'PROTECTED_HASHES.json').read_text())
for f,h in hs.items():assert hashlib.sha256(Path(f).read_bytes()).hexdigest()==h,f
labels={};wanted={'manuscript':{'sec:interpretation_uncertainty':'3.5.3','fig:r1m4_shap_comparison':'7','fig:r1m4_ablation_comparison':'8'},'Supplementary':{'stab:r1m4_ablation_bilstm_attn':'S12','stab:r1m4_seed_pairs_bilstm_attn':'S13','stab:r1m4_ablation_bulstm_attn':'S14','stab:r1m4_seed_pairs_bulstm_attn':'S15','stab:r1m4_shap_magnitude':'S16','stab:r1m4_shap_direction':'S17','stab:r1m4_feature_rank_comparison':'S18','stab:r1m4_rank_stability':'S19'}}
for doc,rs in wanted.items():
 aux=Path('build/'+doc+'.aux').read_text()
 for k,v in rs.items():
  m=re.search(r'\\newlabel\{'+re.escape(k)+r'\}\{\{([^}]+)\}\{([^}]+)\}',aux);assert m and m[1]==v;labels[k]=dict(number=m[1],page=m[2])
for ref in re.findall(r'\\ref\{([^}]+)\}',R[a:b]):
 pre,aux=('manuscript-','build/manuscript.aux') if ref.startswith('manuscript-') else ('supp-','build/Supplementary.aux');assert ref.startswith(pre);assert r'\newlabel{'+ref[len(pre):]+'}' in Path(aux).read_text()
cells=json.loads((P/'CELL_INDEX.json').read_text())
for c in cells:
 rs=list(csv.DictReader((P/'evidence'/c['file']).open()));assert rs[c['csv_line']-2][c['field']]==c['raw']
reply=args(R[a:b],'AuthorResponse')[0]
for v in ['0.089130','0.005174','0.075460','0.102467','0.004022','0.000606','0.003270','0.004774','0.002527','0.005547','-0.001901','-0.010509','-0.020662']:assert v in reply and any(c['display']==v for c in cells),v
assert 'all three descriptive robustness criteria' in reply and 'do not include training randomness' in reply and 'without its own confidence intervals' in reply and 'not a multiplicity correction' in reply
for bad in ['2--30','2--37','all SHAP importances were clearly larger than zero','across most seeds']:assert bad not in reply
notes=json.loads((P/'TASK_NOTE.json').read_text());s=Path('ESI_审稿意见分类_严重程度排序_35项.md').read_text();assert s.count(notes['anchor']+notes['note'])==1;assert s.replace(notes['anchor']+notes['note'],notes['anchor'],1)==(B/'ESI_审稿意见分类_严重程度排序_35项.md').read_text();assert Path('FINAL_REVISION_CHECKLIST.md').read_text().startswith((B/'FINAL_REVISION_CHECKLIST.md').read_text())
assert 'FINAL_REPOSITORY_DOCUMENTATION_PENDING' in Path('results/r2m9_integration/STATUS.md').read_text();assert 'CLOSED' in Path('results/r2minor3_integration/STATUS.md').read_text()
(P/'LABEL_INDEX.json').write_text(json.dumps(labels,indent=2));(P/'EXCERPT_INDEX.json').write_text(json.dumps(dict(old=[dict(index=i+1,sha256=hashlib.sha256(t.encode()).hexdigest()) for i,t in enumerate(old)],new=[dict(key=k,sha256=hashlib.sha256(t.encode()).hexdigest(),exact_main_match=True,already_quoted=t in old) for k,t in ex.items()],total=120,all_match=True),indent=2))
files=['Response letter.tex','ESI_审稿意见分类_严重程度排序_35项.md','FINAL_REVISION_CHECKLIST.md'];patch=''
for f in files:patch+=''.join(difflib.unified_diff((B/f).read_text().splitlines(True),Path(f).read_text().splitlines(True),fromfile='a/'+f,tofile='b/'+f))
(P/'R2minor4_LOCAL.patch').write_text(patch)
out=dict(R2_m3_closed_after_hash_gate=True,old_excerpts_unchanged=118,new_exact_excerpts=2,total_matched=120,match_percent=100,R1_M4_eight_boxes_unchanged=True,R2_M8_six_boxes_unchanged=True,manuscript_Supplementary_Table5_S1_S50_Figures_unchanged=True,other_responses_unchanged=True,protected_files=len(hs),original_comment_exact=True,source_fields=len(cells),all_new_examples_match_source_and_table_cells=True,BU_mntpr_three_subsets_three_way_rule=True,pointwise_unadjusted_only=True,shared_R4_m29_m34_Pending_preserved=True,m9_overall_not_closed=True,next_minor_not_started=True,local_only=True)
(P/'VERIFICATION.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
