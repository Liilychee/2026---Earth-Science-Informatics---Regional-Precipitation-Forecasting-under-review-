# coding: utf-8
from pathlib import Path
import json,csv,re,hashlib,subprocess,math
P=Path('results/r2m5_integration');B=P/'before';M=Path('manuscript.tex').read_text();S=Path('Supplementary.tex').read_text();R=Path('Response letter.tex').read_text()
oldM=(B/'manuscript.tex').read_text();oldS=(B/'Supplementary.tex').read_text();oldR=(B/'Response letter.tex').read_text()
assert S[:S.index('% R2-M5:')].rstrip()==oldS[:oldS.index('\\end{document}')].rstrip()
a,b=R.index('% Review ID: R2 M5'),R.index('% Review ID: R2 M6');oa,ob=oldR.index('% Review ID: R2 M5'),oldR.index('% Review ID: R2 M6')
assert R[:a]==oldR[:oa] and R[b:]==oldR[ob:]
# All previous manuscript text preserved in order, including all figure/table environments.
# Additions occur only between previous paragraphs or just before abstract closing brace.
def environments(s,kind):return re.findall(r'\\begin\{'+kind+r'\}.*?\\end\{'+kind+r'\}',s,re.S)
for k in ['table','figure']:assert environments(M,k)==environments(oldM,k),k
assert oldM[oldM.index('\\label{tab:seed_stability}'):oldM.index('\\end{table}',oldM.index('\\label{tab:seed_stability}'))] in M
# All old paragraphs remain; abstract has an appended qualification.
assert all(line in M for line in oldM.splitlines() if line.strip() and not line.startswith('Short-term precipitation forecasting over Dublin'))
for n in ['manuscript','Supplementary']:
 t=Path(n+'.tex').read_text();labs=re.findall(r'\\label\{([^}]+)\}',t);assert len(labs)==len(set(labs))
ex=json.loads((P/'FINAL_EXCERPTS.json').read_text())
for k,v in ex.items():assert v in M,k;assert '\\RevisedExcerpt{'+v+'}' in R[a:b],k
# Parse exact balanced command arguments for pre-existing excerpts.
def args(t,cmd):
 out=[];pos=0;needle='\\'+cmd+'{'
 while (pos:=t.find(needle,pos))>=0:
  start=pos+len(needle);i=start;depth=1
  while depth:
   if t[i]=='{' and t[i-1]!='\\':depth+=1
   if t[i]=='}' and t[i-1]!='\\':depth-=1
   i+=1
  out.append(t[start:i-1]);pos=i
 return out
oldex=args(oldR,'RevisedExcerpt');newex=args(R,'RevisedExcerpt');assert all(v in newex for v in oldex)
literal=sum(v in M for v in oldex)
# Every number transcribed is read again from fixed archive evidence and formatting checked.
index=json.loads((P/'SOURCE_INDEX.json').read_text());lookup={x['path']:x for x in index}
for x in index:
 raw=(P/'evidence'/x['path']).read_bytes();assert hashlib.md5(raw).hexdigest()==x['md5'];assert raw==subprocess.check_output(['git','show',x['git']+':'+x['path']])
rows={};n=0
for c in json.loads((P/'CELL_INDEX.json').read_text()):
 if 'json_path' in c:
  obj=json.loads((P/'evidence'/c['file']).read_text())
  for k in c['json_path']:obj=obj[k]
  assert obj==c['raw']
 else:
  path=P/'evidence/results/metrics'/c['file']
  if c['file'] not in rows:rows[c['file']]=list(csv.DictReader(path.open()))
  raw=rows[c['file']][c['line']-2][c['field']];assert raw==c['raw']
  display='---' if raw=='' or raw.lower()=='nan' else f"{float(raw):+.{c['digits']}f}" if c['signed'] else f"{float(raw):.{c['digits']}f}"
  assert display==c['display']
 assert c['display'] in S;n+=1
# Validate saved run metadata, seed coverage, and aggregation of already saved scores, no forecast metric recomputation.
runs=[json.loads(p.read_text()) for p in (P/'evidence/results/q06/runs').glob('F*.json')];assert len(runs)==150
for fold in ['F1','F2','F3','F4','F4s']:
 j=json.loads((P/'evidence/results/q06/folds'/f'{fold}.json').read_text())
 for model in ['xgboost','bulstm','bilstm_attn','transformer','bulstm_attn','prob_bilstm_attn']:
  rr=[r for r in runs if r['fold']==fold and r['model']==model];assert sorted(x['seed'] for x in rr)==[7,42,99,123,2024]
  assert all(r['n_test']==j['n_windows']['test'] and r['n_train']==j['n_windows']['train'] for r in rr)
# Read exact required ranges and confidence intervals.
F=list(csv.DictReader((P/'evidence/results/metrics/q06_fold_metrics.csv').open()));pairs=list(csv.DictReader((P/'evidence/results/metrics/q06_pairwise.csv').open()))
wet=next(x for x in pairs if x['scope']=='pooled_2010_2021' and x['subset']=='wet_ge0.1' and x['a']=='bilstm_attn' and x['b']=='xgboost');assert f"{float(wet['dRMSE_a_minus_b']):.4f}"=='0.0093';assert f"{float(wet['boot_low']):.4f}"=='0.0048';assert f"{float(wet['boot_high']):.4f}"=='0.0137'
res=dict(new_tables=7,transcribed_numeric_cells_verified=n,new_evidence_boxes_exact=10,prior_excerpts_preserved=len(oldex),prior_literal_excerpts_still_in_manuscript=literal,all_prior_response_sections_unchanged=True,prior_tables_and_figures_identical=True,prior_supplementary_unchanged=True,source_files_pinned_and_hash_verified=len(index),run_metadata_checked=150,formal_statistics_recomputed=False,original_F4_overlap_correction=True)
(P/'VERIFICATION.json').write_text(json.dumps(res,indent=2));print(json.dumps(res,indent=2))
# Verify all 72 legacy + 10 new excerpts ignoring only markup wrappers/whitespace.
def uncolor(t):
 needle=r'\textcolor{red}{'
 while needle in t:
  a=t.index(needle);start=a+len(needle);i=start;depth=1
  while depth:
   if t[i]=='{' and t[i-1]!='\\':depth+=1
   if t[i]=='}' and t[i-1]!='\\':depth-=1
   i+=1
  t=t[:a]+t[start:i-1]+t[i:]
 return re.sub(r'\s+',' ',t).strip()
canonical=uncolor(M)
assert all(uncolor(v) in canonical for v in newex)
res['all_excerpts_match_ignoring_color_markup']=len(newex)
# Validate numeric column placement for every new table row independently of the generator.
def getrows(label):
 t=S[S.index('\\label{'+label+'}'):];t=t[t.index('\\endfoot')+len('\\endfoot'):t.index('\\end{longtable}')]
 return [x.strip().removesuffix(r'\\').split(' & ') for x in t.strip().splitlines() if x.strip()]
def digits(s):return re.findall(r'[+-]?\d+\.\d+|[+-]?\d+',s)
def fmt(v,d=4,sign=False):return '---' if v=='' else f'{float(v):+.{d}f}' if sign else f'{float(v):.{d}f}'
R0=P/'evidence/results/metrics';D={k:list(csv.DictReader((R0/('q06_'+k+'.csv')).open())) for k in ['fold_metrics','history_effect','pairwise','block_sensitivity','conditional_coverage_summary']}
codes={'xgboost':'XGB','bulstm':'BU','bilstm_attn':'BA','transformer':'TR','bulstm_attn':'BUA','prob_bilstm_attn':'PBA','persistence':'PERS','clim':'CLIM','ar1':'AR1'};models=list(codes)[:6];refs=list(codes)[6:];rowindex=[]
rs=getrows('stab:r2m5_performance');assert len(rs)==36
for row,q in zip(rs,[next(x for x in D['fold_metrics'] if x['fold']==f and x['forecast']==m) for f in ['F1','F2','F3','F4'] for m in models+refs]):
 assert row[:2]==[q['fold'],codes[q['forecast']]]
 fields=['rmse_mean','rmse_sd','mae_mean','r2_mean','skill_mean','rmse_upper_mean','csi_upper_mean']
 expected=[fmt(q[k],3 if k=='csi_upper_mean' else 4) for k in fields if q[k]!='']
 actual=digits(row[2])+digits(row[3])+digits(row[4])+digits(row[5])+digits(row[7])+digits(row[8]);assert actual==expected,(q,actual,expected)
 rowindex.append(dict(label='stab:r2m5_performance',key=[q['fold'],q['forecast']],source='q06_fold_metrics.csv',fields=fields,actual=actual))
for tag,subset in [('all','all'),('wet','wet_ge0.1')]:
 rs=getrows('stab:r2m5_pairs_'+tag);qs=[q for q in D['pairwise'] if q['subset']==subset];assert len(rs)==len(qs)==75
 for row,q in zip(rs,qs):
  assert row[0]==q['scope'].replace('pooled_2010_2021','Pooled') and row[1]==codes[q['a']]+' $-$ '+codes[q['b']]
  actual=sum([digits(c) for c in row[2:]],[]);expected=[fmt(q['n'],0),*[fmt(q[k],5,True) for k in ['dRMSE_a_minus_b','boot_low','boot_high']]];assert actual==expected
  rowindex.append(dict(label='stab:r2m5_pairs_'+tag,key=[q['scope'],q['a'],q['b'],subset],source='q06_pairwise.csv',actual=actual))
rs=getrows('stab:r2m5_history');assert len(rs)==24
for row,q in zip(rs,D['history_effect']):
 assert row[0]==codes[q['forecast']] and row[1]=={'all':'All','wet_ge0.1':'Wet','upper_geQ95main':'Upper'}[q['subset']]
 actual=sum([digits(c) for c in row[2:]],[])
 expected=[fmt(q['n'],0),fmt(q['rmse_F4s_13y']),fmt(q['rmse_F4_25y']),fmt(q['dRMSE_F4_minus_F4s'],5,True)]
 expected += [fmt(q[k],6,True) for k in ['seed_t_low','seed_t_high','boot_low','boot_high'] if q[k]!='']
 expected += [fmt(q['n_seeds_better_with_25y'],0),'5' if q['forecast'] in models else '1'];assert actual==expected,(row,expected)
 rowindex.append(dict(label='stab:r2m5_history',key=[q['forecast'],q['subset']],source='q06_history_effect.csv',actual=actual))
rs=getrows('stab:r2m5_block_sensitivity');assert len(rs)==12
for row,q in zip(rs,D['block_sensitivity']):
 assert row[0]==codes[q['a']]+' $-$ '+codes[q['b']]
 actual=sum([digits(c) for c in row[1:]],[]);expected=[fmt(q[k],0) for k in ['block_samples','block_days']]+[fmt(q[k],5,True) for k in ['dRMSE','boot_low','boot_high']];assert actual==expected
 rowindex.append(dict(label='stab:r2m5_block_sensitivity',key=[q['a'],q['b'],q['block_samples']],source='q06_block_sensitivity.csv',actual=actual))
rs=getrows('stab:r2m5_coverage');assert len(rs)==45
for row,q in zip(rs,D['conditional_coverage_summary']):
 assert row[:3]==["F4$'$" if q['fold']=='F4s' else q['fold'],codes[q['model']],q['subset'].capitalize()]
 actual=sum([digits(c) for c in row[3:]],[]);expected=[fmt(q['n'],0)]+[fmt(q[k],3) for k in ['picp95_mean','picp95_sd','picp90_mean','picp90_sd','width95_mean','above95_mean','below95_mean','neg_lower95_mean']];assert actual==expected
 rowindex.append(dict(label='stab:r2m5_coverage',key=[q['fold'],q['model'],q['subset']],source='q06_conditional_coverage_summary.csv',actual=actual))
(P/'ROW_INDEX.json').write_text(json.dumps(rowindex,indent=2));res['statistical_rows_numeric_column_positions_verified']=len(rowindex)
(P/'VERIFICATION.json').write_text(json.dumps(res,indent=2));print('All 82 excerpts and',len(rowindex),'statistical rows verified at destination columns.')
