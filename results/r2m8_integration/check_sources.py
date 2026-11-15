"""Read only archived q10 values/code/metadata; never train, rerun SHAP or bootstrap."""
from pathlib import Path
import json,csv,hashlib,subprocess,collections,re
P=Path(__file__).resolve().parent;C='6495abc81101074b02b3a5c8cfc83cd6cbc33d79';D={p.name:list(csv.DictReader(p.open())) for p in (P/'source').glob('*.csv')}
for e in json.loads((P/'SOURCE_INDEX.json').read_text()):
 b=(P/'source'/Path(e['path']).name).read_bytes();assert hashlib.md5(b).hexdigest()==e['md5'];assert b==subprocess.check_output(['git','show',C+':'+e['path']])
# Inventory every archived run, including the two group configurations.
paths=subprocess.check_output(['git','ls-tree','-r','--name-only',C,'--','results/q10/runs/'],text=True).splitlines();assert len(paths)==100
seed={42,123,7,2024,99};features=['mxtpr','mntpr','lsp','tcc','v10','sp','d2m'];configs={'full':[],'no_precip':['mxtpr','mntpr','lsp'],'no_mxtpr_mntpr':['mxtpr','mntpr']};configs.update({'no_'+x:[x] for x in features});runs=[]
for path in paths:
 b=subprocess.check_output(['git','show',C+':'+path]);m=json.loads(b);assert m['features']==[x for x in features if x not in configs[m['config']]];assert (m['removed'].split(',') if m['removed'] else [])==configs[m['config']]
 runs.append(dict(path=path,md5=hashlib.md5(b).hexdigest(),arch=m['arch'],config=m['config'],seed=m['seed'],epochs_trained=m['epochs_trained'],best_epoch=m['best_epoch'],test_n=m['test'].get('n'),train_n=m['train'].get('n'),val_n=m['val'].get('n')))
assert {(r['arch'],r['config'],r['seed']) for r in runs}=={(a,c,s) for a in ['bilstm_attn','bulstm_attn'] for c in configs for s in seed}
(P/'RUN_METADATA_INDEX.json').write_text(json.dumps(dict(commit=C,rows=runs,total=100,architectures=2,configs_per_arch=10,seeds=sorted(seed),full_per_arch=5,single_ablation_per_arch=35,group_ablation_per_arch=10),indent=2))
# Source-value robust-effect rule: unanimous deterioration + BOTH pointwise interval types above zero.
summary=D['q10_ablation_summary.csv'];checks=[]
for a in ['bilstm_attn','bulstm_attn']:
 for f in ['sp','tcc','v10','mntpr']:
  r=next(x for x in summary if x['arch']==a and x['subset']=='all' and x['removed']==f)
  checks.append(dict(arch=a,feature=f,n_seeds_worse=int(r['n_seeds_worse']),seed_interval=[float(r['seed_t_low']),float(r['seed_t_high'])],bootstrap_interval=[float(r['boot_low']),float(r['boot_high'])],robust_deterioration=int(r['n_seeds_worse'])==5 and float(r['seed_t_low'])>0 and float(r['boot_low'])>0))
assert all(x['robust_deterioration'] for x in checks if x['arch']=='bilstm_attn' and x['feature'] in ['sp','tcc','v10'])
assert all(not x['robust_deterioration'] and x['n_seeds_worse']==4 and x['seed_interval'][0]<0<x['seed_interval'][1] and x['bootstrap_interval'][0]>0 for x in checks if x['arch']=='bulstm_attn' and x['feature'] in ['sp','tcc'])
# Simple arithmetic checks of archived diagnostics, not regeneration of SHAP or formal metrics.
g=D['q10_shap_global.csv'];print('SHAP global fields',list(g[0]));cvs=[float(r['sd_seeds'])/float(r['mean_abs_phi']) for r in g]
bi=[r for r in g if r['arch']=='bilstm_attn' and r['subset']=='random'];t=next(r for r in bi if r['feature']=='tcc');s=next(r for r in bi if r['feature']=='sp');directions=[float(t['s'+str(x)])>float(s['s'+str(x)]) for x in [42,123,7,2024,99]];assert any(directions) and not all(directions)
cap=[r for r in runs if r['arch']=='bulstm_attn' and r['config']!='full' and r['epochs_trained']==30];assert len(cap)==9
out=dict(fixed_commit=C,source_files_verified=14,runs_verified=100,matched_design_complete=True,robustness_checks=checks,cv_min=min(cvs),cv_max=max(cvs),random_bi_tcc_gt_sp_by_seed=directions,bu_reduced_runs_reaching_cap=cap,bootstrap_implementation_note='q10 uses 141 complete non-circular blocks of28 ->3948 positions, not explicitly truncated; masks applied via block sums. Same starts used for all configurations/seeds. This is preserved, not rerun. Intervals condition on fitted models; differences computed within seed then averaged.',shap_background_conditional=True,models_not_reexecuted=True)
(P/'SOURCE_CHECK.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:out[k] for k in ['runs_verified','cv_min','cv_max','random_bi_tcc_gt_sp_by_seed']},indent=2))
