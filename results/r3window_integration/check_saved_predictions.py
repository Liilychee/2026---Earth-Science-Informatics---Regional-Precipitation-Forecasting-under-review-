from pathlib import Path
import subprocess,json,io,numpy as np,pandas as pd
from scipy.stats import t
P=Path(__file__).resolve().parent;commit='d02519c5f153feb712018cf97efb035f6ca2d7ae';seeds=[42,123,7,2024,99];models={'XGBoost':('xgboost','tree'),'BU-LSTM':('bulstm','nll'),'BiLSTM-Attention':('bilstm_attn','mse'),'Transformer':('transformer','mse'),'BU-LSTM-Attention':('bulstm_attn','nll'),'Prob. BiLSTM-Attention':('prob_bilstm_attn','nll')};cache={};meta={}
models['Probabilistic BiLSTM-Attention']=models['Prob. BiLSTM-Attention']
def load(name,w,seed):
 key=(name,w,seed)
 if key not in cache:
  m,l=models[name];tag=f'{m}__w{w}__{l}__s{seed}'
  raw=subprocess.check_output(['git','show',commit+f':results/q14/preds/{tag}.csv']);p=pd.read_csv(io.BytesIO(raw));cache[key]=p[p.split=='test'].set_index('valid_time');meta[key]=json.loads(subprocess.check_output(['git','show',commit+f':results/q14/runs/{tag}.json']))
  j=meta[key];assert (j['window'],j['seed'],j['n_train'],j['n_val'],j['n_test'])==(w,seed,18410-w,3945-w,3945-w)
 return cache[key]
def masks(y):return {'all':np.ones(len(y),bool),'wet':y>=.1,'upper':y>=.574048}
D=pd.read_csv(P/'evidence/q14_window_effect.csv');C=pd.read_csv(P/'evidence/q14b_window_curve.csv');errs=[]
T=load('XGBoost',6,42).index;assert len(T)==3939
for name in D.model.unique():
 stats={}
 for w in [3,6]:
  per=[];es=[]
  for seed in seeds:
   p=load(name,w,seed).loc[T];y=p.y_true.values;e=(p.y_pred_mean.values-y)**2;per.append({k:np.sqrt(e[v].mean()) for k,v in masks(y).items()});es.append(e)
  stats[w]=(pd.DataFrame(per),np.mean(es,axis=0),y)
 for _,q in D[D.model==name].iterrows():
  tag=q['subset'];ds=(stats[3][0][tag]-stats[6][0][tag]).values;mean=ds.mean();h=t.ppf(.975,4)*ds.std(ddof=1)/np.sqrt(5);mk=masks(stats[3][2])[tag];pool=np.sqrt(stats[3][1][mk].mean())-np.sqrt(stats[6][1][mk].mean())
  vals=[(stats[3][0][tag].mean(),q.a_rmse_mean),(stats[6][0][tag].mean(),q.b_rmse_mean),(mean,q.diff_seed_mean),(mean-h,q.seed_t_low),(mean+h,q.seed_t_high),(pool,q.diff_boot_point)];err=max(abs(a-b) for a,b in vals);assert err<1e-12;errs.append(err);assert int((ds<0).sum())==q.n_seeds_a_better
T2=load('XGBoost',12,42).index;assert len(T2)==3933
for name in C.model.unique():
 stats={}
 for w in [2,3,4,6,8,12]:
  per=[]
  for seed in seeds:
   p=load(name,w,seed).loc[T2];y=p.y_true.values;e=(p.y_pred_mean.values-y)**2;per.append({k:np.sqrt(e[v].mean()) for k,v in masks(y).items()})
  stats[w]=pd.DataFrame(per)
 for _,q in C[C.model==name].iterrows():
  w=int(q.window);assert 6*(w-1)==q.history_h
  for tag in ['all','wet','upper']:
   vals=[(stats[w][tag].mean(),q[f'rmse_{tag}_mean']),(stats[w][tag].std(ddof=1),q[f'rmse_{tag}_sd'])]
   if w!=6:
    ds=(stats[w][tag]-stats[6][tag]).values;h=t.ppf(.975,4)*ds.std(ddof=1)/np.sqrt(5);vals +=[(ds.mean(),q[f'd_{tag}']),(ds.mean()-h,q[f'd_{tag}_seed_low']),(ds.mean()+h,q[f'd_{tag}_seed_high'])];assert int((ds<0).sum())==q[f'd_{tag}_n_better']
   err=max(abs(a-b) for a,b in vals);assert err<1e-12;errs.append(err)
(P/'PREDICTION_CHECK.json').write_text(json.dumps(dict(unique_prediction_files=len(cache),matched_run_json=len(meta),common_test_times_12_30=len(T),common_test_times_curve=len(T2),max_point_seed_interval_difference=max(errs),block_intervals_checked_against_saved_CSV_only=True,bootstrap_not_rerun=True,run_metadata_sample_counts_verified=True),indent=2));print((P/'PREDICTION_CHECK.json').read_text())
