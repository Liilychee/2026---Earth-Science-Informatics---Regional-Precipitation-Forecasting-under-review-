"""Inspect saved JSON dry sensitivity, timestamps, target definitions, bootstrap implementation."""
import json,hashlib,ast,re
from evidence_common import *
paths=__import__('subprocess').check_output(['git','ls-tree','-r','--name-only',COMMIT]).decode().splitlines();runs=[p for p in paths if p.startswith('results/q11/runs/') and p.endswith('.json')]
meta={p:json.loads(blob(p)) for p in runs};rows=[]
for dist in ['tobit','bergamma']:
 for dry in ['0','0.001','0.01']:
  p=f'results/q11/runs/{dist}__dry{dry}__s42.json';j=meta[p]
  rows.append(dict(dist=dist,train_dry=float(dry),seed=42,evaluation_key='dry0',val_crps_199_quantile=j['val']['dry0']['crps_all'],test_crps_199_quantile=j['test']['dry0']['crps_all'],finished_utc=j['finished_utc'],zero_tol=j['zero_tol'],source_path=p,source_md5=hashlib.md5(blob(p)).hexdigest()))
write_csv(rows,'dry_seed42_sensitivity.csv')
for dist,expected in [('tobit',[.0779,.0767,.0749]),('bergamma',[.0717,.0715,.0718])]:
 rr=[r for r in rows if r['dist']==dist];assert [f"{r['val_crps_199_quantile']:.4f}" for r in rr]==[f'{x:.4f}' for x in expected]
 assert min(rr,key=lambda r:r['val_crps_199_quantile'])['train_dry']!=0
 assert min(rr,key=lambda r:r['test_crps_199_quantile'])['train_dry']!=0
counts=[]
for dist in ['tobit','bergamma']:
 for dry in ['0','0.001','0.01']:
  js=[j for p,j in meta.items() if p.split('/')[-1].startswith(dist+'__dry'+dry+'__s')];ss=sorted(int(j['tag'].split('__s')[-1]) for j in js)
  assert ss==([42] if dry=='0.01' else [7,42,99,123,2024]);counts.append(dict(dist=dist,dry=dry,seeds=ss,n=len(ss)))
pre=[j['finished_utc'] for p,j in meta.items() if '__s42.' in p and ('tobit' in p or 'bergamma' in p)]
additional=[j['finished_utc'] for p,j in meta.items() if '__s42.' not in p and ('tobit' in p or 'bergamma' in p)]
assert max(pre)<min(additional)
d,y=load('Gaussian',42);raw=d.y_true.to_numpy();time=d.valid_time.to_numpy()
# Original saved targets are read, never overwritten. Only numerical zero convention applied for matched scoring.
orig=frame('results/prob_bilstm_attention_preds.csv');orig=orig[orig.split=='test'].reset_index(drop=True);assert len(orig)==3939 and np.array_equal(pd.to_datetime(orig.valid_time).to_numpy(),pd.to_datetime(d.valid_time).to_numpy())
x=frame('results/xgboost_preds.csv');train=x[x.split=='train'];q95=float(train.y_true.quantile(.95));assert len(train)==18404 and abs(q95-Q95)<1e-6
assert np.array_equal(y>.1,y>=.1)
method={
 'source_commit':COMMIT,'dry_counts':counts,'last_seed42_sensitivity_finished':max(pre),'first_additional_seed_finished':min(additional),'seed42_precedes_other_seeds':True,'pre_specification_record':'No verifiable prespecification record identified; timestamps show exploratory checks before expansion to additional seeds, not preregistration.',
 'numerical_zero_tolerance':ZERO_TOL,'test_raw_count_le_zero_tol':int((raw<=ZERO_TOL).sum()),'test_small_positive_le_tol':int(((raw>0)&(raw<=ZERO_TOL)).sum()),'test_min_positive_above_tol':float(raw[raw>ZERO_TOL].min()),'largest_abs_raw_target_snapped':float(np.abs(raw[raw<=ZERO_TOL]).max()),'n_wet_strict_gt01':int((y>.1).sum()),'n_wet_ge01':int((y>=.1).sum()),'threshold01_event_sets_equal':True,'n_upper':int((y>=Q95).sum()),'q95_training_saved_target_count':len(train),'q95_training_recomputed_for_provenance_only':q95,'q95_analysis_constant':Q95,'original_test_target_max_abs_difference':float(np.max(np.abs(orig.y_true.to_numpy()-raw))),
 'full_score_method':'CDF-squared trapezoid integral, not closed-form and not 199-quantile; Gaussian [-4,8], nonnegative distributions [0,8]; 4000+1000 grid points.',
 'twcrps_sample_population':'All 3939 test cases for every threshold, not conditional observed-wet/upper samples.',
 'brier_wet_event':'y>0.1 in source; on these test targets identical event set to y>=0.1.',
 'bootstrap':{'type':'paired non-circular moving blocks','block_length':28,'replicates':5000,'seed':42,'n_original':3939,'n_blocks':141,'n_actual':3948,'extra':9,'extra_fraction':9/3939,'start_support_inclusive':[0,3939-28],'final_block_truncated':False,'aggregation':'arithmetic mean of five per-case scores first, then paired resampling; not mean predictions','interval':'pointwise 95% percentile, no multiplicity correction','seed_t':'separate paired five-seed mean-difference Student t, df4','limitation':'Retains 9 extra observations (0.2285%); non-circular endpoints have lower sampling weight. Does not implement standard resample length n; no automatic inference that effect is negligible. Same-index truncated-n sensitivity in paired_full_verification.csv is diagnostic only; formal CSV remains unchanged.'}}
(OUT/'METHOD_AUDIT.json').write_text(json.dumps(method,indent=2));print(pd.DataFrame(rows).to_string(index=False));print(json.dumps(method,indent=2))
