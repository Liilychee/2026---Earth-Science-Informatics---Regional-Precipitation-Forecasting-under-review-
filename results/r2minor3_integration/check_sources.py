# -*- coding: utf-8 -*-
from pathlib import Path
import csv,json,hashlib,re
import numpy as np,pandas as pd
P=Path(__file__).resolve().parent;E=P/'evidence';F='r2m4_fixed_event_scores.csv';T='q05e_event_scores.csv';C='r2m4_fixed_event_paired.csv'
def read(f):return list(csv.DictReader((E/f).open()))
f,t,c=read(F),read(T),read(C);cells=[]
def cell(file,row,key,fmt=None,context='reply'):
 rs=read(file);raw=row[key];v=float(raw);d=format(v,fmt) if fmt else raw;z=dict(file=file,csv_line=rs.index(row)+2,field=key,raw=raw,display=d,context=context);cells.append(z);return d
assert len(f)==54 and len(t)==45
models={r['Model'].replace(' (proposed)','') for r in f};assert len(models)==9
learn=models-{'Persistence','AR(1) (train fit)','Climatology (month x hour)'};assert len(learn)==6
assert {r['Threshold'] for r in f}=={'wet>=0.1','Q90','0.5 mm','Q95','Q97.5','1.0 mm'};assert {r['Threshold'] for r in t}=={'wet>=0.1','Q90','Q95','Q97.5','1.0'}
for data in [f,t]:
 for th in {r['Threshold'] for r in data}:assert len([r for r in data if r['Threshold']==th])==9
 for r in data:
  h,n,fc=int(r['Hits']),int(r['N_events_test']),int(r['Forecast_events']);assert abs(float(r['POD'])-h/n)<1e-9;assert abs(float(r['CSI'])-h/(n+fc-h))<1e-9
  if fc==0:assert not r['FAR']
  else:assert abs(float(r['FAR'])-(fc-h)/fc)<1e-9
for th in ['wet>=0.1','Q90','Q95','Q97.5','0.5 mm','1.0 mm']:
 r=next(r for r in f if r['Threshold']==th);cell(F,r,'thr_mm_h','.6f','event intensity and event count');cell(F,r,'N_events_test','.0f','event count')
for th in ['Q90','Q95','Q97.5']:
 r=next(r for r in t if r['Threshold']==th);a=cell(T,r,'thr_mm','.6f','independently stored tuned threshold');assert a==next(z['display'] for z in cells if z['file']==F and z['context']=='event intensity and event count' and z['field']=='thr_mm_h' and z['raw']==next(v for v in f if v['Threshold']==th)['thr_mm_h'])
hi=[r for r in c if r['Threshold'] in ['0.5 mm','Q95','Q97.5','1.0 mm']];assert len(hi)==24
for r in hi:
 assert float(r['dCSI'])<0 and float(r['CI_high'])<0
 for k in ['dCSI','CI_low','CI_high']:cell(C,r,k,'.4f','24 fixed-rule differences / existing exact excerpt support')
fixed1=[r for r in f if r['Threshold']=='1.0 mm' and r['Model'] in learn];assert len(fixed1)==6
for r in fixed1:
 assert int(r['Hits'])==(1 if r['Model']=='XGBoost' else 0)
 for k in ['Hits','Forecast_events','N_events_test']:cell(F,r,k,'.0f','1.0 fixed event counts')
ones=[r for r in t if r['Threshold']=='1.0' and r['Model'].replace(' (proposed)','') in learn];assert len(ones)==6
lo,hi=min(ones,key=lambda r:float(r['FAR'])),max(ones,key=lambda r:float(r['FAR']));assert cell(T,lo,'FAR','.3f','full six-model 1.0 FAR lower')=='0.859';assert cell(T,hi,'FAR','.3f','full six-model 1.0 FAR upper')=='0.916'
for r in ones:
 for k in ['POD','FAR','AUC']:cell(T,r,k,'.6f','1.0 six-model diagnostic')
for model in ['Transformer','Persistence']:
 r=next(r for r in t if r['Threshold']=='Q95' and r['Model']==model);cell(T,r,'CSI','.3f','tuned Q95 CSI')
# Existing fixed/tuned paragraph numerical examples and ranges.
for th in ['Q95','Q97.5','0.5 mm','1.0 mm']:
 for r in [next(r for r in f if r['Threshold']==th and r['Model']=='Persistence'),max((r for r in f if r['Threshold']==th and r['Model'] in learn),key=lambda r:float(r['CSI']))]:cell(F,r,'CSI','.3f','existing fixed-rule excerpt')
for th in ['Q95','1.0']:
 r=next(r for r in t if r['Threshold']==th and r['Model']=='Persistence');cell(T,r,'AUC','.3f','existing AUC excerpt')
# Verify adverse/existing tuned-rule assertions without recomputing any resampling interval.
for th in ['Q95','1.0']:
 pp=[r for r in read('q05e_event_paired.csv') if r['Threshold']==th and r['Metric']=='CSI' and r['B']=='Persistence'];assert len(pp)==6
 if th=='Q95':assert sum(float(r['A_minus_B'])>0 for r in pp)==5
 else:assert sum(float(r['CI_low'])>0 for r in pp)==4
 for r in pp:
  for k in ['A_minus_B','CI_low','CI_high']:cell('q05e_event_paired.csv',r,k,'.4f','existing validation-selected excerpt')
 trf=next(r for r in pp if r['A']=='Transformer');assert float(trf['CI_low'])<0<float(trf['CI_high'])
 for field in ['POD','FAR','AUC']:
  rr=[r for r in t if r['Threshold']==th and r['Model'].replace(' (proposed)','') in learn]
  for r in [min(rr,key=lambda r:float(r[field])),max(rr,key=lambda r:float(r[field]))]:cell(T,r,field,'.2f','existing descriptive rounded range')
g=read('q05g_multiseed_summary.csv');assert {r['Arch'] for r in g}=={'bilstm_attn','bulstm_attn'} and all(int(r['n_seeds'])==5 for r in g)
# Existing-method candidate-boundary check only; no event scores, cutoff tuning or formal metric recomputation.
raw=Path('/Users/yue/Interpretable-BU-LSTM-for-Rainfall-Prediction-in-Dublin/data/dublin_regional_reduced.csv');b=raw.read_bytes();d=pd.read_csv(raw,parse_dates=['valid_time']).sort_values('valid_time').reset_index(drop=True);n=len(d);assert n==26300;a,bound=int(n*.7),int(n*.85);tr=d.iloc[6:a].copy();va=d.iloc[a+6:bound].copy();assert len(tr)==18404 and len(va)==3939
tr['y']=tr['tp']*1000 if 'tp' in tr else tr['tp_mm'];clim=tr.groupby([tr.valid_time.dt.month,tr.valid_time.dt.hour]).y.mean();pv=np.array([clim.loc[(m,h)] for m,h in zip(va.valid_time.dt.month,va.valid_time.dt.hour)]);grid=np.unique(np.quantile(pv,np.linspace(.5,.999,300)))
boundaries=[]
for r in [r for r in t if r['Model']=='Climatology (month x hour)']:
 v=float(r['cutoff_from_val']);side='lower' if abs(v-grid[0])<1e-12 else 'upper' if abs(v-grid[-1])<1e-12 else 'interior';boundaries.append(dict(threshold=r['Threshold'],saved_cutoff=v,boundary=side));cell(T,r,'cutoff_from_val','.6f','climatology candidate-space boundary')
assert any(x['boundary']=='lower' for x in boundaries)
source=[r for r in json.loads((P/'SOURCE_INDEX.json').read_text()) if r.get('git','not-set') is not None];source.append(dict(path=str(raw),git=None,md5=hashlib.md5(raw.read_bytes()).hexdigest(),purpose='Read-only existing candidate-grid boundary verification; raw input not copied'));(P/'SOURCE_INDEX.json').write_text(json.dumps(source,indent=2));(P/'BOUNDARY_CHECK.json').write_text(json.dumps(dict(n_train=18404,n_val=3939,candidate_probabilities=300,unique_values=len(grid),min=float(grid[0]),max=float(grid[-1]),rows=boundaries,scope='No new search/score computation; rebuild candidate values only to locate archived selected cutoffs.'),indent=2));(P/'CELL_INDEX.json').write_text(json.dumps(cells,indent=2))
# Verify method-code definitions without running scripts.
code=(E/'analysis_q05e_event_paired_ci.py').read_text();assert 'np.linspace(0.5, 0.999, 300)' in code and 'pv >= c' in code and 'pos, posv = yt >= tv, yv >= tv' in code and 'S["test"][m], pos' in code
out=dict(fixed_rows=54,fixed_thresholds=6,tuned_rows=45,tuned_thresholds=5,methods_per_threshold=9,learning_models=6,baselines=3,high_fixed_CSI_differences_negative=24,high_fixed_pointwise_upper_bounds_negative=24,not_holm_inference=True,corrected_1mm_FAR_range=[float(lo['FAR']),float(hi['FAR'])],max_FAR_model=hi['Model'],supplied_0913_is_not_the_six_model_upper_bound=True,stored_count_formula_checks=99,cell_fields=len(cells),five_seed_architectures=2,existing_quantiles_rounded_6dp=True,climatology_lower_boundary_thresholds=[x['threshold'] for x in boundaries if x['boundary']=='lower'])
(P/'DATA_CHECK.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
