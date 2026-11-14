# coding: utf-8
"""Read-only verification of saved outputs; no model fitting, source-output writing or null test."""
from pathlib import Path
import csv, hashlib, json, subprocess, sys
import numpy as np
import pandas as pd
DL=Path('/Users/yue/Downloads'); HERE=Path(__file__).resolve().parent
sha=subprocess.check_output(['git','rev-parse','origin/main'],text=True).strip()
files=['r2m4_fixed_event_paired.csv','r2m4_fixed_event_scores.csv','r2m4_fixed_output.txt','analysis_r2m4_fixed_paired_ci.py']
manifest=[]
for f in files:
 b=(DL/f).read_bytes();manifest.append(dict(source=str(DL/f),archive=('code/' if f.endswith('.py') else 'results/metrics/')+f,md5=hashlib.md5(b).hexdigest(),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b)))
for f in ['manuscript.tex','Supplementary.tex','Response letter.tex']:
 b=Path(f).read_bytes();manifest.append(dict(protected_file=f,sha256=hashlib.sha256(b).hexdigest()))
models={'XGBoost':'xgboost_preds.csv','Transformer':'transformer_preds.csv','BU-LSTM':'bulstm_preds.csv','BiLSTM-Attention':'bilstm_attention_preds.csv','BU-LSTM-Attention':'proposed_model_preds.csv','Probabilistic BiLSTM-Attention':'prob_bilstm_attention_preds.csv','Persistence':'persistence_preds.csv'}
raw={m:pd.read_csv(DL/f,parse_dates=['valid_time']) for m,f in models.items()}
r=raw['XGBoost'];splits={s:r[r.split==s].reset_index(drop=True) for s in ['train','val','test']};Y=splits['test'].y_true.to_numpy();N=len(Y);assert N==3939
align=[]
for m,df in raw.items():
 f=models[m];b=(DL/f).read_bytes();remote=subprocess.check_output(['git','show',sha+':results/'+f]);assert b==remote,f
 for s in splits:
  z=df[df.split==s].reset_index(drop=True);ref=splits[s]
  assert len(z)==len(ref) and np.array_equal(z.valid_time.to_numpy(),ref.valid_time.to_numpy())
  delta=float(abs(z.y_true.to_numpy()-ref.y_true.to_numpy()).max());assert delta<1e-6
  align.append(dict(model=m,split=s,n=len(z),max_target_difference=delta))
 manifest.append(dict(input='results/'+f,ref=sha,md5=hashlib.md5(b).hexdigest(),downloads_equal_git=True))
thresholds={'wet>=0.1':.1,'Q90':float(np.quantile(splits['train'].y_true,.90)),'Q95':float(np.quantile(splits['train'].y_true,.95)),'Q97.5':float(np.quantile(splits['train'].y_true,.975)),'0.5 mm':.5,'1.0 mm':1.}
B=2000;block=28;rng=np.random.default_rng(42);start=rng.integers(0,N,size=(B,int(np.ceil(N/block))));IDX=((start[:,:,None]+np.arange(block)[None,None,:])%N).reshape(B,-1)[:,:N]
paired=pd.read_csv(DL/files[0]);scores=pd.read_csv(DL/files[1]);assert paired.shape==(36,16) and scores.shape==(54,12)
# Exact textual comparison after the documented original export precision (%.10g).
with (DL/files[0]).open() as f:paired_text={(x['Threshold'],x['Model']):x for x in csv.DictReader(f)}
with (DL/files[1]).open() as f:score_text={(x['Threshold'],x['Model']):x for x in csv.DictReader(f)}
def check_fmt(value,raw):assert format(float(value),'.10g')==raw,(value,raw)
checks=[];pvals=[]
for tn,tv in thresholds.items():
 pos=Y>=tv;assert np.array_equal(pos,raw['Persistence'][raw['Persistence'].split=='test'].y_true.to_numpy()>=tv)
 bo={};point={}
 for m,df in raw.items():
  pred=df[df.split=='test'].y_pred_mean.to_numpy();pb=pred>=tv
  h=int((pb&pos).sum());fa=int((pb&~pos).sum());mi=int((~pb&pos).sum());csi=h/(h+fa+mi) if h+fa+mi else 0.;point[m]=csi
  sc=score_text[(tn,m)]
  for field,v in [('N_events_test',int(pos.sum())),('Forecast_events',int(pb.sum())),('Hits',h),('False_alarms',fa),('Misses',mi)]:assert int(sc[field])==v
  check_fmt(csi,sc['CSI']);check_fmt(tv,sc['thr_mm_h'])
  X=pb[IDX];P=pos[IDX];hb=(X&P).sum(1);fb=(X&~P).sum(1);mb=(~X&P).sum(1);bo[m]=hb/np.maximum(hb+fb+mb,1)
 for m in list(models)[:-1]:
  d=bo[m]-bo['Persistence'];ge=int((d>=0).sum());le=int((d<=0).sum());lo,hi=np.percentile(d,[2.5,97.5]);p=min(1.,2*(min(ge,le)+1)/(B+1));a=paired_text[(tn,m)]
  for key,v in [('CSI_model',point[m]),('CSI_reference',point['Persistence']),('dCSI',point[m]-point['Persistence']),('CI_low',lo),('CI_high',hi),('p_two_sided',p)]:check_fmt(v,a[key])
  assert ge==int(a['n_boot_ge0']) and le==int(a['n_boot_le0'])
  assert (lo>0 or hi<0)==(a['CI_excludes_0']=='True')
  pvals.append(p);checks.append(dict(threshold=tn,model=m,dCSI=point[m]-point['Persistence'],CI_low=float(lo),CI_high=float(hi),n_ge0=ge,n_le0=le,n_eq0=ge+le-B,m=min(ge,le),p_sign_approx=p,export_10sig_exact=True))
# Independent scalar Holm implementation (sorted step-down Bonferroni cumulative maximum).
def holm_scalar(ps):
 ix=sorted(range(len(ps)),key=lambda i:ps[i]);out=[None]*len(ps);prev=0.
 for rank,i in enumerate(ix):prev=max(prev,min(1.,(len(ps)-rank)*ps[i]));out[i]=prev
 return out
allp=holm_scalar(pvals);high=[i for i,x in enumerate(checks) if x['threshold'] in ['Q95','Q97.5','0.5 mm','1.0 mm']];hip=holm_scalar([pvals[i] for i in high]);hd=dict(zip(high,hip))
for i,x in enumerate(checks):
 a=paired_text[(x['threshold'],x['model'])];check_fmt(allp[i],a['p_holm_all36']);x['holm_all36']=allp[i]
 if i in hd:check_fmt(hd[i],a['p_holm_high24']);x['holm_high24']=hd[i]
 else:assert a['p_holm_high24']==''
# Arithmetic verification for all 54 saved score rows, including two saved fitted references (not refitted).
for _,a in scores.iterrows():
 h,fa,mi=int(a.Hits),int(a.False_alarms),int(a.Misses)
 assert h+mi==a.N_events_test and h+fa==a.Forecast_events
 st=score_text[(a.Threshold,a.Model)]
 for key,v in [('CSI',h/(h+fa+mi) if h+fa+mi else 0),('POD',h/(h+mi)),('Frequency_bias',(h+fa)/(h+mi))]:check_fmt(v,st[key])
 if h+fa:check_fmt(fa/(h+fa),st['FAR'])
 else:assert st['FAR']==''
# Formal q05e reference is the immutable 300-grid script; record the older 500-grid copy separately.
qpath='code/analysis_q05e_event_paired_ci.py';qcode=subprocess.check_output(['git','show',sha+':'+qpath]);assert b'linspace(0.5, 0.999, 300)' in qcode
assert qcode==(DL/'analysis_q05e_event_paired_ci (1).py').read_bytes()
manifest.append(dict(q05e_formal_path=qpath,ref=sha,md5=hashlib.md5(qcode).hexdigest(),grid=300,matching_download='analysis_q05e_event_paired_ci (1).py',excluded_500_grid_md5=hashlib.md5((DL/'analysis_q05e_event_paired_ci.py').read_bytes()).hexdigest()))
# Distinguish 300-grid saved q05e scores from the older 500-grid variant (no refitting of models).
import io
q05e=pd.read_csv(io.BytesIO(subprocess.check_output(['git','show',sha+':results/metrics/q05e_event_scores.csv'])))
q05e['Model']=q05e.Model.replace({'BU-LSTM-Attention (proposed)':'BU-LSTM-Attention'})
grid_matches={}
for grid in [300,500]:
 count=0
 for tn in ['wet>=0.1','Q90','Q95','Q97.5','1.0 mm']:
  tv=thresholds[tn]
  for m,df in raw.items():
   pv=df[df.split=='val'].y_pred_mean.to_numpy();posv=splits['val'].y_true.to_numpy()>=tv
   best=-1.;cut=None
   for c in np.unique(np.quantile(pv,np.linspace(.5,.999,grid))):
    pb=pv>=c;h=(pb&posv).sum();fa=(pb&~posv).sum();mi=(~pb&posv).sum();v=h/(h+fa+mi) if h+fa+mi else 0.
    if v>best:best=v;cut=c
   pb=df[df.split=='test'].y_pred_mean.to_numpy()>=cut;pos=Y>=tv;h=int((pb&pos).sum());fa=int((pb&~pos).sum());mi=int((~pb&pos).sum());v=h/(h+fa+mi) if h+fa+mi else 0.
   ref=q05e[(q05e.Threshold==('1.0' if tn=='1.0 mm' else tn))&(q05e.Model==m)].iloc[0]
   count+=int(h==int(ref.Hits) and abs(v-float(ref.CSI))<1e-9)
 grid_matches[str(grid)]=dict(matches=count,comparisons=35)
assert grid_matches['300']['matches']==35

# Check the 48-row overlap with the archived earlier fixed table, without replacing it.
rev=pd.read_csv(__import__('io').BytesIO(subprocess.check_output(['git','show',sha+':results/metrics/revision_event_detection.csv'])))
rev['Threshold']=rev.Threshold.replace({'0.1 mm':'wet>=0.1'});rev['Model']=rev.Model.replace({'BU-LSTM-Attention (proposed)':'BU-LSTM-Attention'})
j=scores.merge(rev,on=['Threshold','Model'],suffixes=('','_old'));assert len(j)==48 and (j.Hits==j.Hits_old).all() and (j.Forecast_events==j.N_pred_events).all() and np.allclose(j.CSI,j.CSI_old)
result=dict(source_ref=sha,python=sys.version,numpy=np.__version__,pandas=pd.__version__,scores_rows=54,paired_rows=36,train_n=18404,test_n=N,thresholds=thresholds,alignment=align,block=block,B=B,seed=42,index_sha256=hashlib.sha256(IDX.astype('<i8').tobytes()).hexdigest(),all_36_match_saved_export_10significant_digits=True,original_unrounded_arrays_not_saved=True,checks=checks,high24_holm_below_05=sum(x<.05 for x in hip),all36_holm_below_05=sum(x<.05 for x in allp),high_tests_not_below_05_in_all36=[checks[i]['model']+' '+checks[i]['threshold'] for i in high if allp[i]>=.05],earlier_fixed_table_overlap=48,q05e_grid_reproduction=grid_matches,null_hypothesis_resampling=False,posthoc_high24_family=True)
(HERE/'VERIFICATION.json').write_text(json.dumps(result,indent=2));(HERE/'SOURCE_MANIFEST.json').write_text(json.dumps(manifest,indent=2))
print('Verified 54 score rows, 36 paired estimates/CIs/sign counts/raw p and Holm columns at saved 10-significant-digit precision; no source files written.')
print('Holm arithmetic only:',result['high24_holm_below_05'],'/24;',result['all36_holm_below_05'],'/36; exception:',result['high_tests_not_below_05_in_all36'])
