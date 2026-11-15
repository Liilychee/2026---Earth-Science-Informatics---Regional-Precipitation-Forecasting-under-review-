# -*- coding: utf-8 -*-
from pathlib import Path
import csv,json,re
import numpy as np
from scipy.stats import t
P=Path(__file__).resolve().parent;E=P/'evidence';S=Path('Supplementary.tex').read_text();cells=[];errs=[]
def read(f):return list(csv.DictReader((E/f).open()))
def add(f,r,k,fmt,label,context):
 v=r[k];display=format(float(v),fmt);i=read(f).index(r)+2;cells.append(dict(file=f,csv_line=i,field=k,raw=v,display=display,table_label=label,context=context));return display
A='q10_ablation_summary.csv';G='q10_shap_global.csv';a=read(A);g=read(G)
# Check each referenced table's actual printed cells as well as original CSV fields.
def block(label):
 i=S.index(r'\label{'+label+'}');j=S.index(r'\end{revisiontable}',i);return S[i:j]
bishap=next(r for r in g if r['arch']=='bilstm_attn' and r['subset']=='upper' and r['feature']=='mntpr')
for k in ['mean_abs_phi','sd_seeds','boot_low','boot_high']:
 d=add(G,bishap,k,'.6f','stab:r1m4_shap_magnitude','Bi upper-tail mntpr SHAP example');assert d in block('stab:r1m4_shap_magnitude')
x=np.array([float(bishap[f's{s}']) for s in [42,123,7,2024,99]]);assert abs(x.mean()-float(bishap['mean_abs_phi']))<1e-15;assert abs(x.std(ddof=1)-float(bishap['sd_seeds']))<1e-15
selected=[r for r in a if (r['arch']=='bilstm_attn' and r['subset']=='all' and r['removed']=='sp') or (r['arch']=='bulstm_attn' and r['removed']=='mntpr') or (r['arch']=='bulstm_attn' and r['subset']=='all' and r['removed'] in ['sp','tcc'])];assert len(selected)==6
checks=[]
for r in selected:
 lab='stab:r1m4_ablation_bilstm_attn' if r['arch']=='bilstm_attn' else 'stab:r1m4_ablation_bulstm_attn';pairlab='stab:r1m4_seed_pairs_bilstm_attn' if r['arch']=='bilstm_attn' else 'stab:r1m4_seed_pairs_bulstm_attn';vs=np.array([float(r[f'dRMSE_s{s}']) for s in [42,123,7,2024,99]])
 m,sd=vs.mean(),vs.std(ddof=1);lo,hi=m-t.ppf(.975,4)*sd/np.sqrt(5),m+t.ppf(.975,4)*sd/np.sqrt(5)
 for k,v in [('dRMSE_mean',m),('dRMSE_sd',sd),('seed_t_low',lo),('seed_t_high',hi)]:errs.append(abs(float(r[k])-v));assert abs(float(r[k])-v)<1e-15
 for k in ['dRMSE_mean','dRMSE_sd','seed_t_low','seed_t_high','boot_low','boot_high']:
  d=add(A,r,k,'.6f',lab,r['arch']+'/'+r['subset']+'/'+r['removed']);assert d.lstrip('+') in block(lab)
 add(A,r,'n_seeds_worse','.0f',lab,'seed direction')
 for seed in [42,123,7,2024,99]:
  d=add(A,r,f'dRMSE_s{seed}','.6f',pairlab,'paired seed direction');assert d.lstrip('+') in block(pairlab)
 if r['arch']=='bilstm_attn':assert all(vs>0) and float(r['seed_t_low'])>0 and float(r['boot_low'])>0
 elif r['removed']=='mntpr':assert all(vs<0) and float(r['seed_t_high'])<0 and float(r['boot_high'])<0
 else:assert (vs>0).sum()==4 and float(r['seed_t_low'])<0<float(r['seed_t_high']) and float(r['boot_low'])>0
 checks.append(dict(arch=r['arch'],subset=r['subset'],removed=r['removed'],all_seeds_improve=bool(np.all(vs<0)),n_positive=int((vs>0).sum()),seed_interval=[float(r['seed_t_low']),float(r['seed_t_high'])],block_interval=[float(r['boot_low']),float(r['boot_high'])]))
for r in read('q10_ablation_rank_stability.csv'):
 if r['subset']=='all' and 'between seeds' in r['comparison']:
  add('q10_ablation_rank_stability.csv',r,'kendall_tau','.3f','stab:r1m4_rank_stability','existing BU paragraph rank coefficients')
code=(E/'q10_ablation_stats.py').read_text();shcode=(E/'q10_shap_stats.py').read_text();assert 'N_BOOT, BLOCK, BSEED = 10000, 28, 42' in code;assert 'N_BOOT, BSEED = 2000, 42' in shcode;assert 'df=len(SEEDS) - 1' in code;assert 'd_boot = np.mean([boot_rmse' in code;assert 'mean_abs[b].mean(0)' in shcode
# Map methodological numbers to existing table captions and original code, not invent new table cells.
methods=[dict(value='5',meaning='number of training seeds',table_label='stab:r1m4_ablation_bilstm_attn',table_location='caption: five paired seed-level differences',code='SEEDS = [42, 123, 7, 2024, 99]'),dict(value='4',meaning='Student-t degrees of freedom',table_label='stab:r1m4_ablation_bilstm_attn',table_location='caption: df=4'),dict(value='28 / 10,000 / 42',meaning='moving-block length / replicates / seed',table_label='stab:r1m4_ablation_bilstm_attn',table_location='caption',code='q10_ablation_stats.py:N_BOOT, BLOCK, BSEED'),dict(value='2,000 / 95%',meaning='calendar-day replicates / pointwise coverage',table_label='stab:r1m4_shap_magnitude',table_location='caption',code='q10_shap_stats.py:N_BOOT, BSEED'),dict(value='100',meaning='fixed grouped training-background windows',table_label='stab:r1m4_shap_magnitude',table_location='caption; grouped background definition'),dict(value='0.1',meaning='revised-wet threshold',table_label='stab:r1m4_ablation_bulstm_attn',table_location='Wet subheading')]
(P/'METHOD_INDEX.json').write_text(json.dumps(methods,indent=2));(P/'CELL_INDEX.json').write_text(json.dumps(cells,indent=2));(P/'DATA_CHECK.json').write_text(json.dumps(dict(rows_checked=len(selected),source_fields=len(cells),shap_example={k:bishap[k] for k in ['mean_abs_phi','sd_seeds','boot_low','boot_high']},paired_checks=checks,max_seed_summary_difference=max(errs),BU_mntpr_all_three_subsets_meet_three_way_rule=True,BU_sp_tcc_not_three_way_robust=True,pointwise_only=True,bootstrap_not_recomputed=True,SHAP_not_recomputed=True),indent=2))
# Preserve a precise implementation note without re-estimating archived intervals.
(P/'BOOTSTRAP_METHOD_CHECK.md').write_text('''# Existing q10 uncertainty implementation (read-only source audit)

- SHAP: mean absolute attribution is averaged over the five fitted models per explained case, then explained cases are resampled in whole calendar-day clusters within each subset;2,000 replicates, seed42, percentile95% intervals. The training background and fitted models are not resampled. Training variability is separately summarized by per-seed attribution SD.
- Ablation: same non-circular moving-block starts across full/reduced configurations and seeds;28 samples per block,10,000 replicates, seed42. Each seed has its own paired bootstrap RMSE difference and these differences are averaged; not an ensemble-prediction RMSE.
- Archived q10 code uses ceil(3939/28)=141 complete blocks (3948 draw positions) with cumulative block sums, without truncating the final block. The new reply retains the documented configured moving-block method and does not claim exact-n resamples. No original interval or result is changed or newly estimated. This implementation detail is retained as a reproducibility boundary, not used to overturn already closed evidence.
- Seed-t intervals use sample SD and df4. Only existing seed-level summary arithmetic is checked in this round; no bootstrap, prediction metric, SHAP or model training is rerun. Two uncertainty summaries are not combined, all intervals pointwise, unadjusted for multiplicity.
''');print(json.dumps(dict(source_fields=len(cells),max_seed_summary_difference=max(errs),BU_mntpr_all_three_subsets_meet_three_way_rule=True,SHAP_example= {k:bishap[k] for k in ['mean_abs_phi','sd_seeds','boot_low','boot_high']}),indent=2))
