from pathlib import Path
import pandas as pd,numpy as np,json,subprocess,io,hashlib
from scipy.stats import rankdata,spearmanr
P=Path(__file__).resolve().parent;E=P/'evidence';C='d02519c5f153feb712018cf97efb035f6ca2d7ae';al=pd.read_csv(E/'q08_hres_aligned_samples.csv',float_precision='round_trip',parse_dates=['valid_time','init']);assert len(al)==1970 and al.valid_time.is_unique;assert set(al.valid_time.dt.hour)=={6,18};assert set(al.init.dt.hour)=={0,12};assert (al.valid_time-al.init).eq(pd.Timedelta(hours=6)).all();assert al.valid_time.diff().dropna().eq(pd.Timedelta(hours=12)).all()
assert al.valid_time.iloc[0]==pd.Timestamp('2019-04-22 06:00') and al.valid_time.iloc[-1]==pd.Timestamp('2021-12-31 18:00');assert al.valid_time.dt.date.nunique()==985
assert np.allclose(al['hres_tp6_mm']/6,al['HRES (6 h mean)'],rtol=0,atol=1e-14);assert np.allclose(al['era5_tp6_mm']/6,al['Perfect 6 h mean (ceiling)'],rtol=0,atol=1e-14)
raw=subprocess.check_output(['git','show',C+':results/metrics/q04_pairs.csv']);pairs=pd.read_csv(io.BytesIO(raw),float_precision='round_trip',parse_dates=['valid_time']).drop_duplicates('valid_time');d=al.merge(pairs[['valid_time','station_mm','era5_regional_mm']],on='valid_time',how='left');assert d.station_mm.notna().all();assert max(abs(d.era5_regional_mm-d.y_true))<1e-5
(P/'STATION_SOURCE.json').write_text(json.dumps(dict(commit=C,path='results/metrics/q04_pairs.csv',md5=hashlib.md5(raw).hexdigest(),matched_station_n=len(d),missing_station=0),indent=2))
point=pd.read_csv(E/'q08_hres_comparison.csv');st=pd.read_csv(E/'q08b_station_comparison.csv');auc=pd.read_csv(E/'q08c_event_auc.csv');paired=pd.read_csv(E/'q08c_event_auc_paired.csv');err=[];allvals={};ML=['BiLSTM-Attention','XGBoost','BU-LSTM-Attention','Probabilistic BiLSTM-Attention','BU-LSTM','Transformer']
for target,tab,y in [('ERA5',point,al.y_true.values),('station',st,d.station_mm.values)]:
 vals={}
 def pred(lab):
  if lab=='ERA5 label (regional mean)':return al.y_true.values
  if lab=='ERA5 6 h mean (window diagnostic)':return al['Perfect 6 h mean (ceiling)'].values
  return al[lab].values
 denom=np.sqrt(np.mean((pred('Climatology (month x hour)')-y)**2))
 for _,q in tab.iterrows():
  p=pred(q.forecast);rmse=np.sqrt(np.mean((p-y)**2));mae=np.mean(abs(p-y));bias=np.mean(p-y);values=[(rmse,q.RMSE),(mae,q.MAE),(bias,q.bias),(1-rmse/denom,q.skill_vs_clim)]
  if target=='ERA5':values.append((1-np.sum((p-y)**2)/np.sum((y-y.mean())**2),q.R2))
  for tag,thr in ([('wet01',.1),('Q95',.574048)] if target=='ERA5' else [('wet01',.1),('ge1mm',1.)]):
   o=y>=thr;f=p>=thr;h=sum(o&f);fa=sum(~o&f);mi=sum(o&~f);v={'POD':h/(h+mi),'FAR':fa/(h+fa) if h+fa else np.nan,'CSI':h/(h+fa+mi)}
   for k,n in v.items():
    saved=q[f'{tag}_{k}'];assert (np.isnan(n) and np.isnan(saved)) or abs(n-saved)<1e-12
  e=max(abs(a-b) for a,b in values);assert e<1e-12;err.append(e);vals[q.forecast]=rmse
 for _,q in auc[auc.target==target].iterrows():
  p=d.era5_regional_mm.values if target=='station' and q.model=='ERA5 label (regional mean)' else pred(q.model);thr={'wet>=0.1':.1,'Q95':.5740,'>=1.0':1.}[q.event];pos=y>=thr;nr=int(pos.sum());assert nr==q.n_obs;r=rankdata(p);a=(r[pos].sum()-nr*(nr+1)/2)/(nr*(len(y)-nr));assert abs(a-q.AUC)<1e-12
  cutoff=np.sort(p)[::-1][nr-1];forecast=p>=cutoff;h=sum(forecast&pos);nf=sum(forecast);assert nf==q.FM_n_fcst;assert abs(h/nr-q.FM_POD)<1e-12;assert abs(h/(nr+nf-h)-q.FM_CSI)<1e-12
 # Point differences vs HRES must be exactly the ones paired in the original output.
 boot=pd.read_csv(E/('q08_hres_bootstrap.csv' if target=='ERA5' else 'q08b_station_bootstrap.csv'))
 for _,q in boot.iterrows():assert abs(vals[q.forecast]-vals[q.reference]-q.dRMSE)<1e-12
 allvals[target]=vals
# Rounded and full training Q95 happen to identify the same verification event set here.
assert np.array_equal(al.y_true.values>=.5740,al.y_true.values>=.574048)
identity={}
for name,fn in {'BiLSTM-Attention':'bilstm_attention_preds.csv','XGBoost':'xgboost_preds.csv','BU-LSTM-Attention':'proposed_model_preds.csv','Probabilistic BiLSTM-Attention':'prob_bilstm_attention_preds.csv','BU-LSTM':'bulstm_preds.csv','Transformer':'transformer_preds.csv'}.items():
 raw=subprocess.check_output(['git','show',C+':results/'+fn]);p=pd.read_csv(io.BytesIO(raw),float_precision='round_trip',parse_dates=['valid_time']);p=p[p.split=='test'].set_index('valid_time').loc[al.valid_time];diff=np.max(abs(p.y_pred_mean.values-al[name].values));assert diff<1e-12;identity[name]=dict(path='results/'+fn,md5=hashlib.md5(raw).hexdigest(),max_saved_prediction_difference=float(diff))
res=dict(common_n=1970,dates=[str(al.valid_time.iloc[0]),str(al.valid_time.iloc[-1])],distinct_days=985,matched_origins_and_leads=True,point_score_max_error=max(err),point_rows_checked=len(point)+len(st),event_auc_rows_checked=len(auc),forecast_identities=identity,station_target_count=len(d),Q95_rounded_exact_same_event_set=True,strict_final_hour_HRES_not_available=True,block_intervals_read_from_archived_outputs_not_recomputed=True)
(P/'SAVED_RESULTS_CHECK.json').write_text(json.dumps(res,indent=2));print(json.dumps({k:v for k,v in res.items() if k!='forecast_identities'},indent=2))
