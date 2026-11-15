# -*- coding: utf-8 -*-
from pathlib import Path
import subprocess,io,json,hashlib
import numpy as np,pandas as pd
P=Path(__file__).resolve().parent;C='d02519c5f153feb712018cf97efb035f6ca2d7ae'
def read(f):
 b=subprocess.check_output(['git','show',C+':'+f]);sources.append(dict(path=f,commit=C,md5=hashlib.md5(b).hexdigest()));return pd.read_csv(io.BytesIO(b))
sources=json.loads((P/'SOURCE_INDEX.json').read_text());raw=pd.read_csv(P/'evidence/q16_interval_per_run.csv');summ=pd.read_csv(P/'evidence/q16_interval_summary.csv');diffs=[];overlap=[]
for model in ['bulstm','bulstm_attn','prob_bilstm_attn']:
 for seed in [42,123,7,2024,99]:
  f=f'results/q14/preds/{model}__w6__nll__s{seed}.csv';d=read(f);d=d[d.split=='test'];assert len(d)==3939
  y,mu,sd=[d[k].to_numpy(float) for k in ['y_true','y_pred_mean','y_pred_std']]
  for sub,mask in [('all',np.ones(len(d),bool)),('wet>=0.1',y>=.1),('upper>=Q95',y>=.574048)]:
   q=raw[(raw.source=='q14_rerun_5seed')&(raw.model==model)&(raw.seed==seed)&(raw.subset==sub)].iloc[0];assert mask.sum()==int(q.n)
   for level,z in [(90,1.6448536269514722),(95,1.959963984540054)]:
    lo,hi=mu[mask]-z*sd[mask],mu[mask]+z*sd[mask];yy=y[mask]
    vals={'PICP':np.mean((yy>=lo)&(yy<=hi)),'MPIW':np.mean(hi-lo),'above':np.mean(yy>hi),'below':np.mean(yy<lo),'neglow':np.mean(lo<0)}
    for key,v in vals.items():diffs.append(dict(model=model,seed=seed,subset=sub,field=f'{key}{level}',saved=float(q[f'{key}{level}']),recomputed=float(v),abs_diff=abs(float(q[f'{key}{level}'])-v)))
  if model=='prob_bilstm_attn':
   b=read(f'results/q11/preds/gaussian__s{seed}.csv');b=b[b.split=='test'];assert list(d.valid_time)==list(b.valid_time)
   ds={k:float(np.max(np.abs(d[a].to_numpy()-b[k].to_numpy()))) for a,k in [('y_true','y_true'),('y_pred_mean','y_pred_mean'),('y_pred_mean','par1'),('y_pred_std','par2')]};assert ds['y_true']==0 and ds['y_pred_mean']==0 and ds['par1']==0 and ds['par2']<1e-6,ds
   overlap.append(dict(seed=seed,test_rows=len(b),max_differences=ds))
mx=max(x['abs_diff'] for x in diffs);assert mx<1e-14,mx
for _,s in summ[summ.source=='q14_rerun_5seed'].iterrows():
 r=raw[(raw.source==s.source)&(raw.model==s.model)&(raw.subset==s.subset)];assert set(r.seed)=={42,123,7,2024,99}
 for f in ['PICP90','MPIW90','PICP95','MPIW95','above90','above95','below90','below95','neglow90','neglow95']:
  assert abs(r[f].mean()-s[f+'_mean'])<1e-14;assert abs(r[f].std(ddof=1)-s[f+'_std'])<1e-14
pd.DataFrame(diffs).to_csv(P/'INDEPENDENT_CHECK.csv',index=False);(P/'SOURCE_INDEX.json').write_text(json.dumps(sources,indent=2));out=dict(prediction_files=15,per_run_fields=len(diffs),max_abs_difference=mx,summary_rows=9,seeds=[42,123,7,2024,99],q14_q11_overlap=overlap,full_precision_z=[1.6448536269514722,1.959963984540054]);(P/'DATA_CHECK.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
