from pathlib import Path
import pandas as pd,numpy as np,subprocess,io,json
from scipy.stats import t
P=Path('results/r3sec32f_integration');A=pd.read_csv(P/'evidence/q13_season_ablation.csv');D=pd.read_csv(P/'evidence/q09_seasonal.csv');commit='d02519c5f153feb712018cf97efb035f6ca2d7ae';SM={12:'DJF',1:'DJF',2:'DJF',3:'MAM',4:'MAM',5:'MAM',6:'JJA',7:'JJA',8:'JJA',9:'SON',10:'SON',11:'SON'};errs=[];rows=[]
ref=pd.read_csv(io.BytesIO(subprocess.check_output(['git','show',commit+':results/q14/preds/xgboost__w6__tree__s42.csv'])));ref=ref[ref.split=='test'].reset_index(drop=True)
yref=ref.y_true.values
for arch,name in [('bilstm_attn','BiLSTM-Attention'),('bulstm_attn','BU-LSTM-Attention')]:
 ds=[]
 for seed in [42,123,7,2024,99]:
  f=[]
  for cfg in ['full','no_v10']:
   raw=subprocess.check_output(['git','show',commit+f':results/q10/preds/{arch}__{cfg}__s{seed}.csv']);p=pd.read_csv(io.BytesIO(raw));p=p[p.split=='test'].reset_index(drop=True);f.append(p)
  assert f[0].valid_time.equals(f[1].valid_time);assert np.array_equal(f[0].y_true.values,f[1].y_true.values);assert f[0].valid_time.equals(ref.valid_time);y=yref;seas=pd.to_datetime(f[0].valid_time).dt.month.map(SM)
  ds.append({s:float(np.sqrt(np.mean((f[1].y_pred_mean.values[seas==s]-y[seas==s])**2))-np.sqrt(np.mean((f[0].y_pred_mean.values[seas==s]-y[seas==s])**2))) for s in ['DJF','MAM','JJA','SON']})
 for s in ['DJF','MAM','JJA','SON']:
  v=np.array([d[s] for d in ds]);q=A[(A.arch==name)&(A.removed=='v10')&(A.season==s)&(A.subset=='all')].iloc[0];lo,hi=v.mean()+np.array([-1,1])*t.ppf(.975,4)*v.std(ddof=1)/np.sqrt(5)
  err=max(abs(v.mean()-q.d_rmse),abs(lo-q.t_lo),abs(hi-q.t_hi));assert err<1e-12,err;assert int((v>0).sum())==q.n_worse_of_5;errs.append(err);rows.append(dict(arch=name,season=s,paired_seed_differences=v.tolist(),max_error=err))
# Seasonal training-pair sample counts using timestamps alone, no new correlations.
time=pd.date_range('2004-01-01',periods=18410,freq='6h');counts=pd.Series(time[1:].month).map(SM).value_counts().to_dict();assert sum(counts.values())==18409
for s,n in counts.items():assert D[D.season==s].n.eq(n).all()
sel=pd.read_csv(P/'evidence/q09_selection_table.csv');raw=['u10','v10','d2m','t2m','sp','e','mxtpr','mntpr','tcc','ssr','lsp'];rank=sel[sel['var'].isin(raw)].assign(abs=lambda x:x.rho_contemp.abs()).sort_values('abs',ascending=False)['var'].tolist();assert rank.index('v10')+1==7 and rank.index('u10')+1==11
(P/'INDEPENDENT_CHECK.json').write_text(json.dumps(dict(rows=rows,max_abs_error=max(errs),training_pair_counts=counts,original_11_contemporaneous_rank=rank,seasonal_correlations_point_only=True,seasonal_ablation_seed_t_only=True),indent=2));print('8 ablation rows independently verified, max error',max(errs));print(counts)
