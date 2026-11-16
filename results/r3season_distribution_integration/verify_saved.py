"""Read-only verification of saved q03d outputs; full-period distribution diagnostic.
No model fit, no modification to archived q03/q03d files.
"""
from pathlib import Path
import pandas as pd,numpy as np,json,hashlib
P=Path(__file__).resolve().parent;E=P/'evidence'
REG=Path('/Users/yue/Interpretable-BU-LSTM-for-Rainfall-Prediction-in-Dublin/data/dublin_regional_reduced.csv')
assert hashlib.md5(REG.read_bytes()).hexdigest()=='f9b4f8a22c8b7849f40eb71918fe1fd6'
d=pd.read_csv(REG,parse_dates=['valid_time']);x=pd.read_csv(E/'xgboost_preds.csv',parse_dates=['valid_time']);pair=pd.read_csv(E/'q04_pairs.csv',parse_dates=['valid_time'])
season=lambda t:t.dt.month.map({12:'DJF',1:'DJF',2:'DJF',3:'MAM',4:'MAM',5:'MAM',6:'JJA',7:'JJA',8:'JJA',9:'SON',10:'SON',11:'SON'})
assert len(d)==26300 and d.valid_time.is_unique and not d.isna().any().any()
assert list(d.valid_time)==list(pd.date_range('2004-01-01','2021-12-31 18:00',freq='6h'))
assert np.max(abs(d.tp.to_numpy()*1000-pair.era5_regional_mm.to_numpy()))<1.1e-13
assert (d.valid_time==pair.valid_time).all()
d['season']=season(d.valid_time);d['y']=d.tp*1000
miss=d[~d.valid_time.isin(x.valid_time)][['valid_time','season','y']];assert len(miss)==18
parts=[d.iloc[:18410],d.iloc[18410:22355],d.iloc[22355:]]
assert set(miss.valid_time)==set(pd.concat([p.iloc[:6] for p in parts]).valid_time)
miss.to_csv(P/'OMITTED_18_TIMESTAMPS.csv',index=False)
rows=[];ec=[]
for s in ['DJF','MAM','JJA','SON']:
 y=d.loc[d.season==s,'y'].to_numpy();v,c=np.unique(y,return_counts=True)
 rows.append(dict(Season=s,N=len(y),Zero_n=int((y==0).sum()),Wet_n=int((y>=.1).sum()),Wet_pct=100*(y>=.1).mean(),Ge1_n=int((y>=1).sum()),Ge1_pct=100*(y>=1).mean(),Mean=y.mean(),Q90=np.quantile(y,.9),Q95=np.quantile(y,.95),Q99=np.quantile(y,.99),Max=y.max()))
 ec.extend(dict(Season=s,x_mm_h=a,count=int(b),CDF_le=cc/len(y),Survival_ge=(len(y)-cc+b)/len(y),N=len(y)) for a,b,cc in zip(v,c,np.cumsum(c)))
pd.DataFrame(rows).to_csv(P/'FULL_PERIOD_SEASON_STATS.csv',index=False);pd.DataFrame(ec).to_csv(P/'FULL_PERIOD_ECDF.csv',index=False)
old=pd.read_csv(E/'revision_season_precip_dist.csv').set_index('Season');x['season']=season(x.valid_time)
for s,g in x.groupby('season'):
 assert len(g)==old.loc[s,'N']
 assert abs(g.y_true.quantile(.95)-old.loc[s,'Q95_mm'])<1e-14
# Original 105 seed rows and rounded summaries must agree (not refitting).
r=pd.read_csv(E/'q03d_seasonal_xgb_raw.csv');summ=pd.read_csv(E/'q03d_seasonal_xgb_summary.csv');q=pd.read_csv(E/'q03d_seasonal_xgb_paired.csv');pred=pd.read_csv(E/'q03d_seasonal_xgb_test_preds.csv',parse_dates=['valid_time'])
assert len(r)==105 and set(r.Seed)=={42,123,7,2024,99} and len(summ)==21 and len(q)==14 and len(pred)==3939
te=parts[2].iloc[6:];assert list(pred.valid_time)==list(te.valid_time)
assert (pred.season==season(pred.valid_time)).all();assert abs(pred.y_true.to_numpy()-te.tp.to_numpy()*1000).max()<5e-7
errors=[]
for _,z in summ.iterrows():
 t=r[(r.Variant==z.Variant)&(r.Subset==z.Subset)]
 for f in ['RMSE','MAE','R2','Skill_vs_monthhour_clim']:
  for stat,v in [('mean',t[f].mean()),('std',t[f].std())]:
   assert abs(round(v,4)-z[f+'_'+stat])<1e-12
# Reproduce bootstrap from saved seed-mean predictions, not from five seed-level RMSEs.
n=len(pred);rng=np.random.default_rng(42);idx=((rng.integers(0,n,(2000,int(np.ceil(n/28))))[:,:,None]+np.arange(28))%n).reshape(2000,-1)[:,:n]
tr_y=d.iloc[6:18410].y.to_numpy();q95=np.quantile(tr_y,.95)
masks={'all':np.ones(n,bool),**{s:pred.season.eq(s).to_numpy() for s in ['DJF','MAM','JJA','SON']},'wet>=0.1':pred.y_true.to_numpy()>=.1,'tail>=Q95':pred.y_true.to_numpy()>=q95}
for _,z in q.iterrows():
 v=z.Comparison[0];mk=masks[z.Subset];a=r[(r.Variant==v)&(r.Subset==z.Subset)].set_index('Seed').RMSE;b=r[(r.Variant=='G')&(r.Subset==z.Subset)].set_index('Seed').RMSE;diff=a-b
 assert round(diff.mean(),4)==z.seed_mean_delta_RMSE and round(diff.std(),4)==z.seed_std_delta and (diff>0).sum()==z.n_seeds_worse
 e1=(pred.y_true.to_numpy()-pred['y_'+v].to_numpy())**2;e0=(pred.y_true.to_numpy()-pred.y_G.to_numpy())**2
 pt=np.sqrt(e1[mk].mean())-np.sqrt(e0[mk].mean());bs=[]
 for ii in np.array_split(idx,8):
  w=mk[ii];den=w.sum(1);bs.extend(np.sqrt((e1[ii]*w).sum(1)/den)-np.sqrt((e0[ii]*w).sum(1)/den))
 ci=np.percentile(bs,[2.5,97.5]);assert round(pt,4)==z.seedavg_pred_delta_RMSE
 assert np.max(abs(np.round(ci,4)-[z.boot_CI_low,z.boot_CI_high]))<1e-12
 errors.append(dict(comparison=z.Comparison,subset=z.Subset,point=pt,low=ci[0],high=ci[1],matches_saved_4dp=True))
(P/'BOOTSTRAP_RECHECK.json').write_text(json.dumps(errors,indent=2))
report=dict(raw_n=26300,old_windowed_n=26282,missing=18,full_first=str(d.valid_time.min()),full_last=str(d.valid_time.max()),sampling='00/06/12/18 UTC; hourly regional precipitation, not six-hour totals',season_stats=rows,train_seasons={s:int((d.iloc[6:18410].season==s).sum()) for s in ['DJF','MAM','JJA','SON']},old_counts={s:int(z.N) for s,z in old.iterrows()},bootstrap='circular blocks28,2000,seed42;141 blocks=3948 positions truncated to3939; full-timeline indices shared, mask after sampling; score five-seed mean prediction; pointwise, no multiplicity adjustment',seed_rows=105,summary_rows=21,paired_rows=14,all_rounding_matches=True,limitations=['Per-seed q03d predictions were not archived; 105 raw metrics can be checked against saved summaries but not independently regenerated from individual seed predictions.','Seed-mean prediction file supports all 14 paired point estimates and full bootstrap reproduction.','No seasonal retuning or deep-model seasonal retraining.'])
(P/'SAVED_RESULTS_CHECK.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
