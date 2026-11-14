"""Width90 from unchanged saved q05/q95. Does not use 95% widths or q16 values."""
import json,sys
from evidence_common import *
rows=[];summary=[];official=frame('results/metrics/q11_per_seed.csv');ref={(r.config,int(r.seed)):float(r.picp90_all) for r in official.itertuples()}
for config in list(CONFIGS)[:3]:
 r0=[]
 for seed in SEEDS:
  d,y=load(config,seed);lo=d.q05.to_numpy();hi=d.q95.to_numpy();assert (hi>=lo).all() and np.isfinite(hi-lo).all()
  w=float(np.mean(hi-lo));c=float(np.mean((y>=lo)&(y<=hi)));assert abs(c-ref[config,seed])<1e-14
  r=dict(config=config,seed=seed,n=len(y),width90=w,picp90=c,archived_picp90=ref[config,seed],coverage_difference=c-ref[config,seed],unit='mm h^-1');rows.append(r);r0.append(r)
  print(config,seed,'Width90',format(w,'.12f'),'PICP90',format(c,'.12f'))
 summary.append(dict(config=config,n_seeds=5,width90_mean=np.mean([r['width90'] for r in r0]),width90_sd=np.std([r['width90'] for r in r0],ddof=1),picp90_mean=np.mean([r['picp90'] for r in r0]),picp90_sd=np.std([r['picp90'] for r in r0],ddof=1),unit='mm h^-1'))
write_csv(rows,'width90_per_seed.csv');write_csv(summary,'width90_summary.csv');print(pd.DataFrame(summary).to_string(index=False));print('Coverage matched saved q11 scores for all 15 runs. q16 original-run evidence not substituted.')
