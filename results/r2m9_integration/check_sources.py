"""Read existing archived records/predictions only. No training, scoring of predictions or bootstrap regeneration."""
from pathlib import Path
import subprocess,json,hashlib,csv,re,collections,itertools,statistics,io
import pandas as pd
import numpy as np
P=Path(__file__).resolve().parent;C='d02519c5f153feb712018cf97efb035f6ca2d7ae';NAMES={'xgboost':'XGBoost','bilstm_attn':'BiLSTM-Attention','transformer':'Transformer','bulstm':'BU-LSTM','bulstm_attn':'BU-LSTM-Attention','prob_bilstm_attn':'Prob. BiLSTM-Attention'}
def raw(path):return subprocess.check_output(['git','show',C+':'+path])
def md5(b):return hashlib.md5(b).hexdigest()
for e in json.loads((P/'SOURCE_INDEX.json').read_text()):assert (P/'source'/Path(e['path']).name).read_bytes()==raw(e['path'])
paths=subprocess.check_output(['git','ls-tree','-r','--name-only',C,'--','results/q19/'],text=True).splitlines();runs=[];records=[];predidx=[];reference=None
for path in [p for p in paths if '/runs/' in p and p.endswith('.json')]:
 b=raw(path);r=json.loads(b);runs.append(r);dest=P/'source/runs'/Path(path).name;dest.parent.mkdir(exist_ok=True);dest.write_bytes(b);records.append(dict(path=path,md5=md5(b),model=r['model'],tag=r['tag'],seed=r['seed'],config=r['config'],cap=r['cap'],train_seconds=r['train_seconds'],finished_utc=r['finished_utc'],tf=r['tf'],gpu=r['gpu']))
assert len(runs)==117 and len({r['tag'] for r in runs})==117
assert collections.Counter(r['model'] for r in runs)==dict(xgboost=39,bilstm_attn=38,transformer=11,bulstm=11,bulstm_attn=11,prob_bilstm_attn=7)
assert len([p for p in paths if '/preds/' in p])==117
for r in runs:
 path='results/q19/preds/'+r['tag']+'.csv';b=raw(path);d=pd.read_csv(io.BytesIO(b));assert set(d.split)=={'val','test'} and len(d)==7878
 te=d[d.split=='test'].reset_index(drop=True);va=d[d.split=='val'];assert len(te)==len(va)==3939 and not te.valid_time.duplicated().any()
 if reference is None:reference=te[['valid_time','y_true']].copy()
 assert (te.valid_time.values==reference.valid_time.values).all() and np.array_equal(te.y_true.values,reference.y_true.values)
 assert np.isfinite(te.y_pred_mean).all()
 predidx.append(dict(path=path,md5=md5(b),rows=len(d),n_val=len(va),n_test=len(te),test_times_equal=True,test_targets_equal=True))
# Validate original-reference series identity and targets without re-scoring.
A=[];maxyd=0
for m in ['bilstm_attn','transformer','bulstm','bulstm_attn','prob_bilstm_attn']:
 for s in [42,123,7,2024,99]:
  path=f'results/q21/preds/bilstm_attn__w6__C0__mse__s{s}.csv' if m=='bilstm_attn' else f'results/q14/preds/{m}__w6__'+('mse' if m=='transformer' else 'nll')+f'__s{s}.csv'
  b=raw(path);d=pd.read_csv(io.BytesIO(b));te=d[d.split=='test'].reset_index(drop=True);assert len(te)==3939 and (te.valid_time.values==reference.valid_time.values).all();err=float(np.max(np.abs(te.y_true-reference.y_true)));assert err<2e-7;maxyd=max(maxyd,err);A.append(dict(model=m,seed=s,path=path,md5=md5(b),n_test=len(te),max_abs_y_difference=err))
# Select only by validation scores; no prediction or test metrics used here.
orig={'xgboost':dict(n=100,lr=.05,depth=6),'bilstm_attn':dict(units=64,lr=.001,dropout=.2)};candidate=[];selectioncheck=[]
for m in ['xgboost','bilstm_attn']:
 cap=None if m=='xgboost' else 60;rr=sorted([r for r in runs if r['model']==m and r['seed']==42 and r['cap']==cap],key=lambda r:r['val']['rmse']);assert len(rr)==27
 grid=({(r['config']['n'],r['config']['lr'],r['config']['depth']) for r in rr}==set(itertools.product([100,300,600],[.03,.05,.1],[4,6,8]))) if m=='xgboost' else ({(r['config']['units'],r['config']['lr'],r['config']['dropout']) for r in rr}==set(itertools.product([32,64,128],[.0003,.001,.003],[.1,.2,.3])))
 assert grid;sel=json.loads((P/f'source/selection_{m}.json').read_text());scores=[]
 for r in rr[:3]:
  vs=[next(q['val']['rmse'] for q in runs if q['model']==m and q['config']==r['config'] and q['cap']==cap and q['seed']==s) for s in [42,123,7]];mean=statistics.mean(vs);srec=next(x for x in sel['top3'] if x['config']==r['config']);assert abs(mean-srec['mean'])<1e-15 and vs==srec['val_42_123_7'];scores.append((mean,r['config']))
 assert min(scores,key=lambda x:x[0])[1]==sel['selected']
 for i,r in enumerate(rr):candidate.append(dict(model=m,rank=i+1,tag=r['tag'],config=r['config'],val_metric='rmse',val=r['val']['rmse'],top3_mean=next((q['mean'] for q in sel['top3'] if q['config']==r['config']),None)))
 selectioncheck.append(dict(model=m,grid=27,original_rank=next(i+1 for i,r in enumerate(rr) if r['config']==orig[m]),selected=sel['selected'],validation_only=True))
for m in ['transformer','bulstm','bulstm_attn','prob_bilstm_attn']:
 sel=json.loads((P/f'source/selection_{m}.json').read_text());metric='rmse' if m=='transformer' else 'crps';rr=sorted([r for r in runs if r['model']==m and r['seed']==42],key=lambda r:r['val'][metric]);assert len(rr)==3 and rr[0]['config']==sel['selected']
 for i,r in enumerate(rr):candidate.append(dict(model=m,rank=i+1,tag=r['tag'],config=r['config'],val_metric=metric,val=r['val'][metric],top3_mean=None))
 selectioncheck.append(dict(model=m,grid=3,selected=sel['selected'],selection_metric=metric,validation_only=True))
# Consistency between stored JSON and117-row archived metrics CSV.
allruns=list(csv.DictReader((P/'source/q19_all_runs.csv').open()));assert len(allruns)==117
for r in runs:
 matches=[q for q in allruns if q['model']==r['model'] and int(q['seed'])==r['seed'] and ((q['cap']=='' and r['cap'] is None) or (q['cap']!='' and float(q['cap'])==r['cap'])) and all(float(q['cfg_'+k])==v for k,v in r['config'].items())];assert len(matches)==1;q=matches[0];assert abs(float(q['val_rmse'])-r['val']['rmse'])<1e-15 and abs(float(q['test_rmse'])-r['test']['rmse'])<1e-15
# Triple rule is separate from the archive's medium/strong label.
effect=list(csv.DictReader((P/'source/q19_effect.csv').open()));assert len(effect)==53;strong=[];rule=[]
for i,r in enumerate(effect):
 tx=float(r['t_lo'])>0 or float(r['t_hi'])<0;bx=float(r['boot_lo'])>0 or float(r['boot_hi'])<0;tr=int(r['n_better_of_5']) in (0,5) and tx and bx
 rule.append(dict(csv_line=i+2,model=r['model'],comparison=r['comparison'],metric=r['metric'],subset=r['subset'],triple=tr,improvement=tr and float(r['delta'])<0))
 if tr:strong.append(rule[-1])
assert all(r['model']=='BU-LSTM-Attention' and r['metric']=='crps' and r['improvement'] for r in strong) and len(strong)==2
rankcheck=[]
for sub in ['all','wet','tail']:
 rr=[r for r in effect if r['comparison']=='C-A (total)' and r['metric']=='rmse' and r['subset']==sub];assert len(rr)==6;orderA=[r['model'] for r in sorted(rr,key=lambda r:float(r['ref']))];orderC=[r['model'] for r in sorted(rr,key=lambda r:float(r['new']))];assert orderA==orderC;rankcheck.append(dict(subset=sub,A=orderA,C=orderC,unchanged=True))
# Recorded task seconds aggregate, not fit-only time or GPU hours.
cost=[]
for m in NAMES:
 rs=[r for r in runs if r['model']==m];ss=[float(r['train_seconds']) for r in rs];epochs=[r['best_epoch'] for r in rs if r['best_epoch'] is not None];cost.append(dict(model=m,n_runs=len(rs),recorded_seconds=sum(ss),recorded_hours=sum(ss)/3600,median_seconds=statistics.median(ss),mean_best_epoch=statistics.mean(epochs) if epochs else None,hit_cap=sum(bool(r['hit_cap']) for r in rs) if epochs else None))
with (P/'COST_SUMMARY.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(cost[0]));w.writeheader();w.writerows(cost)
assert round(sum(r['recorded_hours'] for r in cost),2)==3.87
# Logs: exact completed run tags and stages; retain failed pre-training old-LR assertion transparently.
logs={n:(P/'source'/n).read_text() for n in ['q19_gate_output.txt','q19_tune_output.txt','q19_light_output.txt']};done=set(re.findall(r'\[done\] (\S+) \|','\n'.join(logs.values())));assert done=={r['tag'] for r in runs}
assert all('q19 '+stage+' COMPLETE' in logs['q19_tune_output.txt'] for stage in ['SEARCH','RECHECK','FINAL']) and 'LIGHT COMPLETE' in logs['q19_light_output.txt'];assert logs['q19_gate_output.txt'].count('[gate]')==2 and logs['q19_gate_output.txt'].count('OK')==2
for name,value in [('RUN_INDEX.json',records),('PREDICTION_INDEX.json',predidx),('A_REFERENCE_INDEX.json',A),('CANDIDATE_INDEX.json',candidate),('SELECTION_CHECK.json',selectioncheck),('TRIPLE_RULE_INDEX.json',rule),('RANK_CHECK.json',rankcheck)]: (P/name).write_text(json.dumps(value,indent=2))
report=dict(fixed_commit=C,n_runs=117,n_predictions=117,n_effect_rows=53,run_counts=dict(collections.Counter(r['model'] for r in runs)),common_test_samples=3939,max_A_reference_target_difference=maxyd,validation_selections_recovered=6,formal_grids_each=27,bilstm_gate_excluded_from_rank=True,recorded_task_seconds=sum(r['recorded_seconds'] for r in cost),recorded_task_hours=sum(r['recorded_hours'] for r in cost),triple_rule_rows=strong,ranking_unchanged=rankcheck,stages_complete=True,source_q19_tune_md5=md5((P/'source/q19_tune.py').read_bytes()),source_q19_stats_md5=md5((P/'source/q19_stats.py').read_bytes()),no_metrics_recomputed_from_predictions=True)
(P/'SOURCE_CHECK.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:report[k] for k in ['n_runs','n_predictions','n_effect_rows','run_counts','max_A_reference_target_difference','recorded_task_hours','validation_selections_recovered']},indent=2))
