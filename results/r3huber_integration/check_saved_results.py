from pathlib import Path
import json,subprocess,io,numpy as np,pandas as pd
from scipy.stats import t
P=Path(__file__).resolve().parent;commit='d02519c5f153feb712018cf97efb035f6ca2d7ae';D=pd.read_csv(P/'evidence/q15_loss_effect.csv');sels=pd.read_csv(P/'evidence/q15_delta_selection.csv');seeds=[42,123,7,2024,99];checks=[];epochs={};nfiles=0;selection={}
for model,arch in [('BiLSTM-Attention','bilstm_attn'),('Transformer','transformer')]:
 data={};val={}
 for loss in ['mse','huber0.5','huber1','huber2']:
  per=[];jrows=[]
  for seed in seeds:
   tag=f'{arch}__w6__{loss}__s{seed}';j=json.loads(subprocess.check_output(['git','show',commit+':results/q14/runs/'+tag+'.json']));raw=subprocess.check_output(['git','show',commit+':results/q14/preds/'+tag+'.csv']);p=pd.read_csv(io.BytesIO(raw));p=p[p.split=='test'].reset_index(drop=True);assert len(p)==3939;nfiles+=1
   assert j['seed']==seed and j['window']==6 and j['n_train']==18404 and j['n_val']==3939 and j['n_test']==3939;per.append(p);jrows.append(j)
  data[loss]=per;val[loss]=np.mean([j['val']['rmse'] for j in jrows]);epochs[arch+'/'+loss]=dict(epochs=[j['epochs_trained'] for j in jrows],best_epoch=[j['best_epoch'] for j in jrows],count_at_30=sum(j['epochs_trained']==30 for j in jrows))
 choice=min(['huber0.5','huber1','huber2'],key=lambda x:val[x]);assert choice==sels[sels.model==model].iloc[0].selected_loss;selection[model]=dict(validation_means=val,chosen=choice)
 for loss in ['huber0.5','huber1','huber2']:
  v=[];b=[];ea=[];eb=[]
  for pa,pb in zip(data[loss],data['mse']):
   assert pa.valid_time.equals(pb.valid_time);assert np.array_equal(pa.y_true.values,pb.y_true.values);y=pa.y_true.values;ma={'all':np.ones(len(y),bool),'wet':y>=.1,'upper':y>=.574048};a={};base={}
   for tag,mk in ma.items():
    a[tag]=np.sqrt(np.mean((pa.y_pred_mean.values[mk]-y[mk])**2));base[tag]=np.sqrt(np.mean((pb.y_pred_mean.values[mk]-y[mk])**2));a[tag+'_bias']=np.mean(pa.y_pred_mean.values[mk]-y[mk]);base[tag+'_bias']=np.mean(pb.y_pred_mean.values[mk]-y[mk])
   a['sd_ratio']=pa.y_pred_mean.std(ddof=0)/np.std(y);base['sd_ratio']=pb.y_pred_mean.std(ddof=0)/np.std(y);v.append(a);b.append(base);ea.append((pa.y_pred_mean.values-y)**2);eb.append((pb.y_pred_mean.values-y)**2)
  va,pb=pd.DataFrame(v),pd.DataFrame(b)
  for _,q in D[(D.model==model)&(D.huber==loss)].iterrows():
   tag=q['subset'];ds=(va[tag]-pb[tag]).values;mean=ds.mean();h=t.ppf(.975,4)*ds.std(ddof=1)/np.sqrt(5);mk=ma[tag];pool=np.sqrt(np.mean(ea,axis=0)[mk].mean())-np.sqrt(np.mean(eb,axis=0)[mk].mean());err=max(abs(va[tag].mean()-q.a_rmse_mean),abs(pb[tag].mean()-q.b_rmse_mean),abs(va[tag].std(ddof=1)-q.a_rmse_sd),abs(mean-q.diff_seed_mean),abs(mean-h-q.seed_t_low),abs(mean+h-q.seed_t_high),abs(pool-q.diff_boot_point),abs(va[tag+'_bias'].mean()-q.a_bias),abs(va.sd_ratio.mean()-q.a_sd_ratio));assert err<1e-12;assert sum(ds<0)==q.n_seeds_a_better;checks.append(err)
raw=pd.read_csv(P/'evidence/q05f_raw.csv');assert len(raw)==35
for _,g in raw.groupby('Variant'):assert set(g.Seed)==set(seeds)
S=pd.read_csv(P/'evidence/q05f_summary.csv');Q=pd.read_csv(P/'evidence/q05f_paired.csv');qerrs=[]
for _,q in Q.iterrows():
 s=S[S.Variant==q.Variant].iloc[0];base=S.iloc[0];assert abs(s[q.Metric]-q.Variant_value)<1e-12;assert abs(base[q.Metric]-q.M0)<1e-12;assert abs(s[q.Metric]-base[q.Metric]-q.Diff_variant_minus_M0)<1e-12
out=dict(q15_predictions_and_runJSON=nfiles,common_test_targets=3939,max_existing_score_seedCI_error=max(checks),selected=selection,training_epochs=epochs,q05f_raw_runs=35,q05f_each_variant_seeds=seeds,q05f_summary_paired_fields_consistent=True,q05f_saved_predictions_not_archived_in_located_tree=True,bootstrap_not_rerun=True)
(P/'SAVED_RESULTS_CHECK.json').write_text(json.dumps(out,indent=2));print('40 predictions + runJSON verified; max difference',max(checks));print('Transformer epochs:',{k:v for k,v in epochs.items() if k.startswith('transformer')})
