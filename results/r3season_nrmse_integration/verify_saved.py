"""Independent q13 saved-prediction check; no fitting, no data download.
Reproduces original reference-target/float32 scoring and RNG call order.
"""
from pathlib import Path
import pandas as pd,numpy as np,subprocess,io,json,hashlib,os
from scipy.stats import t as tdist
P=Path(__file__).resolve().parent;E=P/'evidence';COMMIT='d02519c5f153feb712018cf97efb035f6ca2d7ae';SEEDS=[42,123,7,2024,99];SEAS=['DJF','MAM','JJA','SON'];SM={12:'DJF',1:'DJF',2:'DJF',3:'MAM',4:'MAM',5:'MAM',6:'JJA',7:'JJA',8:'JJA',9:'SON',10:'SON',11:'SON'}
rawpath=Path('/Users/yue/Interpretable-BU-LSTM-for-Rainfall-Prediction-in-Dublin/data/dublin_regional_reduced.csv');raw=pd.read_csv(rawpath,parse_dates=['valid_time']);assert hashlib.md5(rawpath.read_bytes()).hexdigest()=='f9b4f8a22c8b7849f40eb71918fe1fd6';tr=raw.iloc[:18410];trainy=tr.tp.to_numpy()*1000;trainseas=tr.valid_time.dt.month.map(SM);means=pd.Series(trainy).groupby(trainseas).mean()
counts=pd.read_csv(E/'q13_season_counts.csv').set_index('season');M=pd.read_csv(E/'q13_season_metrics.csv');C=pd.read_csv(E/'q13_season_paired.csv');mtrerr=max(abs(means-counts.mean_train));assert mtrerr<1e-12
load={};source=[];tag={'xgboost':('tree','XGBoost'),'bulstm':('nll','BU-LSTM'),'bilstm_attn':('mse','BiLSTM-Attention'),'transformer':('mse','Transformer'),'bulstm_attn':('nll','BU-LSTM-Attention'),'prob_bilstm_attn':('nll','Prob. BiLSTM-Attention')}
for m,(loss,name) in tag.items():
 load[name]={}
 for seed in SEEDS:
  f=f'results/q14/preds/{m}__w6__{loss}__s{seed}.csv';b=subprocess.check_output(['git','show',COMMIT+':'+f]);df=pd.read_csv(io.BytesIO(b),parse_dates=['valid_time']);df=df[df.split=='test'].reset_index(drop=True);assert len(df)==3939
  load[name][seed]=df;source.append(dict(path=f,commit=COMMIT,md5=hashlib.md5(b).hexdigest(),sha256=hashlib.sha256(b).hexdigest()))
ref=load['XGBoost'][42];y=ref.y_true.to_numpy();tt=ref.valid_time;seas=tt.dt.month.map(SM).to_numpy();clim=pd.Series(trainy).groupby([tr.valid_time.dt.month,tr.valid_time.dt.hour]).mean();arp=np.polyfit(trainy[:-1],trainy[1:],1)
refs={'Persistence':ref.persistence.to_numpy(),'Clim (month×hour)':np.array([clim.loc[(mo,hr)] for mo,hr in zip(tt.dt.month,tt.dt.hour)]),'AR(1)':np.polyval(arp,ref.persistence.to_numpy())}
assert (tt.to_numpy()==raw.iloc[22355+6:].valid_time.to_numpy()).all();assert abs(y-raw.iloc[22355+6:].tp.to_numpy()*1000).max()<5e-7
max_target_diff=0
for d in load.values():
 for df in d.values():assert df.valid_time.equals(tt);max_target_diff=max(max_target_diff,float(abs(df.y_true.to_numpy()-y).max()))
rmse=lambda a,b:float(np.sqrt(np.mean((a-b)**2)))
metricerrs=[];perseed=[]
for sn in SEAS+['all']:
 mk=seas==sn if sn!='all' else np.ones(len(y),bool);tk=mk&(y>=.574048);meantr=float(counts.loc[sn,'mean_train']) if sn!='all' else trainy.mean();crm=rmse(refs['Clim (month×hour)'][mk],y[mk]);mt=y[mk].mean()
 if sn!='all':
  q=counts.loc[sn];assert mk.sum()==q.n_test and (y[mk]>=.1).sum()==q.wet_test and tk.sum()==q.tail_test;assert abs(mt-q.mean_test)<1e-15
 for model in M[M.season==sn].model:
  z=M[(M.season==sn)&(M.model==model)].iloc[0]
  ps=[refs[model]] if model in refs else [load[model][seed].y_pred_mean.to_numpy() for seed in SEEDS]
  vals=np.array([rmse(p[mk],y[mk]) for p in ps]);value=vals.mean();sd=0. if len(vals)==1 else vals.std(ddof=1)
  expected={'rmse':value,'rmse_sd':sd,'nrmse_train':value/meantr,'nrmse_test':value/mt,'ss_clim':1-value/crm,'rmse_tail':np.mean([rmse(p[tk],y[tk]) for p in ps]),'bias':np.mean([np.mean(p[mk]-y[mk]) for p in ps])}
  err=max(abs(v-z[k]) for k,v in expected.items());assert err<1e-12,(sn,model,err);metricerrs.append(err)
  if len(vals)==5:
   for seed,v in zip(SEEDS,vals):perseed.append(dict(season=sn,model=model,seed=seed,rmse=v))
# Full q13 C-section order: one RNG draw per comparison, NOT common indices across comparisons.
rng=np.random.default_rng(42);tq=tdist.ppf(.975,4);pairerrs=[];pairchecks=[]
for sn in SEAS+['all']:
 mk=seas==sn if sn!='all' else np.ones(len(y),bool);n=int(mk.sum());yy=y[mk]
 for model in list(load)+['pair']:
  if model=='pair':as_=[load['BiLSTM-Attention'][s].y_pred_mean.to_numpy() for s in SEEDS];bs_=[load['XGBoost'][s].y_pred_mean.to_numpy() for s in SEEDS]
  else:as_=[load[model][s].y_pred_mean.to_numpy() for s in SEEDS];bs_=[refs['Clim (month×hour)']]*5
  W=np.empty((5000,n),dtype=np.float32);nb=int(np.ceil(n/28))
  for b in range(5000):
   starts=rng.integers(0,max(n-28+1,1),nb);ii=(starts[:,None]+np.arange(28)).ravel()[:n]%n;W[b]=np.bincount(ii,minlength=n)
  ds=[];db=np.zeros(5000)
  for a,b in zip(as_,bs_):
   e1=((a[mk]-yy)**2).astype(np.float32);e0=((b[mk]-yy)**2).astype(np.float32);ds.append(np.sqrt(e1.mean())-np.sqrt(e0.mean()));db+=np.sqrt((W@e1)/n)-np.sqrt((W@e0)/n)
  ds=np.array(ds);mu=ds.mean();sd=ds.std(ddof=1);lo=mu-tq*sd/np.sqrt(5);hi=mu+tq*sd/np.sqrt(5);blo,bhi=np.percentile(db/5,[2.5,97.5]);z=C[(C.season==sn)&(C.model==model)].iloc[0]
  vals={'delta':float(mu),'t_lo':lo,'t_hi':hi,'boot_lo':blo,'boot_hi':bhi};err=max(abs(v-z[k]) for k,v in vals.items());assert err<3e-7,(sn,model,err)
  assert (ds<0).sum()==z.n_better_of_5 and n==z.n
  assert (lo>0 or hi<0)==(z.t_lo>0 or z.t_hi<0);assert (blo>0 or bhi<0)==(z.boot_lo>0 or z.boot_hi<0)
  pairerrs.append(err);pairchecks.append(dict(season=sn,model=model,max_abs_error=err,matching_interval_zero_conclusions=True,n_better=int((ds<0).sum())))
 pd.DataFrame(perseed).to_csv(P/'INDEPENDENT_PER_SEED.csv',index=False)
 print('Verified paired season',sn,flush=True)
# Existing S8/S9 RMSE & SS entries must agree at their published precision.
for sn in SEAS:
 for model in M[M.season==sn].model:
  z=M[(M.season==sn)&(M.model==model)].iloc[0];assert z.nrmse_train>0
(p:=P/'PREDICTION_SOURCE_INDEX.json').write_text(json.dumps(source,indent=2));(P/'PAIR_RECHECK.json').write_text(json.dumps(pairchecks,indent=2))
summary={sn:dict(n_test=int(counts.loc[sn,'n_test']),n_train=int((trainseas==sn).sum()),mean_train=float(counts.loc[sn,'mean_train']),mean_test=float(counts.loc[sn,'mean_test']),nrmse_train_min=float(M[(M.season==sn)&M.model.isin(load)].nrmse_train.min()),nrmse_train_max=float(M[(M.season==sn)&M.model.isin(load)].nrmse_train.max()),nrmse_test_min=float(M[(M.season==sn)&M.model.isin(load)].nrmse_test.min()),nrmse_test_max=float(M[(M.season==sn)&M.model.isin(load)].nrmse_test.max()),clim_rmse=float(M[(M.season==sn)&(M.model=='Clim (month×hour)')].rmse.iloc[0])) for sn in SEAS}
out=dict(saved_metric_rows=45,saved_paired_rows=35,q14_prediction_files=30,per_seed_rows=len(perseed),max_metric_abs_error=max(metricerrs),max_pair_abs_error=max(pairerrs),max_training_mean_abs_error=mtrerr,max_prediction_target_difference=max_target_diff,all_interval_zero_conclusions_match=True,denominator_source='18410 raw training timestamps; NOT18404 windowed training targets; no validation/test fitting',q06_original_extended_file_available=False,independent_normalizer_check='Existing2004–2021 regional table with audited MD5;18410-row prefix agrees to2.7e-15',bootstrap='noncircular moving blocks28 within each concatenated seasonal subsequence;5000 replicates;seed42 once, RNG continued per original35 comparison order; block positions truncated to seasonal n; gaps/years may be bridged; paired per seed then mean RMSE effect, NOT prediction-mean scoring; conditional on fitted models',replicate_count_evidence='Source-code5000 configuration, no standalone loop-count execution log; independent reproduction using5000 agrees with saved intervals',season_summary=summary)
(P/'SAVED_RESULTS_CHECK.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
