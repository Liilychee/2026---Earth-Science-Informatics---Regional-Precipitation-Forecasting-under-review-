from pathlib import Path
import json,csv,re,hashlib,subprocess,difflib,tempfile,shutil,fitz
ROOT=Path.cwd();P=ROOT/'results/r3_batch_07_13_closure';B=ROOT/'results/r3sec32d_integration/before';CLOSED=ROOT/'results/r3nwp_integration/before';docs=['manuscript.tex','Supplementary.tex','Response letter.tex','sn-bibliography.bib'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=Path('results/r2m6_integration/check_integration.py').read_text();exec(source[source.index('def args('):source.index('oldex=args(')])
M=Path('manuscript.tex').read_text();S=Path('Supplementary.tex').read_text();R=Path('Response letter.tex').read_text();old=args((B/'Response letter.tex').read_text(),'RevisedExcerpt');new=args(R,'RevisedExcerpt');assert len(old)==130 and len(new)==144;assert old==new[:130];assert all(canonical(t) in canonical(M+S) for t in new)
# Compare full non-target reviewer blocks with the closed R3-06 state.
allowed={'R3 Section 3.2(d)','R3 Section 3.2(e)','R3 Section 3.2(f)','R3 L329-333','R3 L341-344','R3 L376','R3 Section 3.3.1'}
def blocks(t):
 marks=list(re.finditer(r'% Review ID: ([^\n]+)',t));return {m[1].strip():t[m.start():marks[i+1].start() if i+1<len(marks) else len(t)] for i,m in enumerate(marks)}
ob,nb=blocks((B/'Response letter.tex').read_text()),blocks(R)
for key,txt in ob.items():
 if key not in allowed:assert nb[key]==txt,key
for kind in ['figure','table']:
 pat=r'\\begin\{'+kind+r'\}.*?\\end\{'+kind+r'\}';assert re.findall(pat,M,re.S)==re.findall(pat,(B/'manuscript.tex').read_text(),re.S)
assert S.startswith((B/'Supplementary.tex').read_text().split(r'\end{document}')[0])
# Existing main source is an ordered subsequence; only additions to this baseline are allowed.
it=iter(M.splitlines());assert all(any(x==y for y in it) for x in (B/'manuscript.tex').read_text().splitlines())
assert Path('sn-bibliography.bib').read_text().startswith((B/'sn-bibliography.bib').read_text())
# Prior figure hashes, including the author's final upstream PDF, unchanged.
figs=json.loads(Path('results/r3nwp_integration/FIGURE_HASHES.json').read_text())
for f,h in figs.items():assert sha(Path(f))==h,f
# Re-read all raw source cells, including q15's multi-line header convention.
roots=['r3sec32f_integration','r3window_integration','r3climatology_integration','r3huber_integration','r3nwp_integration'];counts={}
for name in roots:
 path=ROOT/'results'/name;cells=json.loads((path/'CELL_INDEX.json').read_text())
 for x in cells:
  if 'field_index' in x:q=list(csv.reader((path/'evidence'/x['file']).open()))[x['line']-1];assert q[x['field_index']]==x['raw']
  else:q=list(csv.DictReader((path/'evidence'/x['file']).open()))[x['line']-2];assert q[x['field']]==x['raw']
  assert x['display'] in M+S
 counts[name]=len(cells)
q21=list(csv.DictReader(Path('results/r3sec32d_integration/evidence/q21_effect.csv').open()));s52=json.loads(Path('results/r3sec32d_integration/CELL_INDEX_S52.json').read_text())
for row in s52:
 cfg,ref=row['comparison'].split(' vs ');sub={'All':'all','Wet':'wet','Upper tail':'tail'}[row['subset']];q=next(q for q in q21 if q['model']==row['model'] and q['config']==cfg and q['ref']==ref and q['subset']==sub)
 vals=[float(q['rmse_ref']),float(q['rmse_ref'])+float(q['d_rmse_mean']),float(q['d_rmse_mean']),float(q['d_rmse_pct']),float(q['t_lo']),float(q['t_hi']),float(q['boot_lo']),float(q['boot_hi']),int(q['n_better_of_5'])]
 for i,(v,w) in enumerate(zip(vals,row['table'])):assert abs(v-w)<= (0.000501 if i==3 else 0.0000011),row
# Source code checks prevent carrying forward the wrong estimands.
q14=Path('results/r3window_integration/evidence/q14q15_stats.py').read_text();assert 'sea = sea +' in q14 and 'reshape(N_BOOT, -1)' in q14 and 'np.sqrt((ea[idx]' in q14
q05=Path('results/r3huber_integration/evidence/analysis_q05f_xgb_imbalance_strategies.py').read_text();assert 'SEEDS = [42, 123, 7, 2024, 99]' in q05 and 'pv[v], pt[v] = np.mean(PV, 0), np.mean(PT, 0)' in q05
q07=Path('results/r3climatology_integration/evidence/analysis_q07_baselines.py').read_text();assert 'g = tr.groupby(keys)["y"].mean()' in q07 and 'best_clim = min(CLIMS' in q07
q08=Path('results/r3nwp_integration/evidence/q08_hres_comparison.py').read_text();assert 'list(lead_h).index(6)' in q08 and 'regional_mean(a6' in q08
assert 'no strictly matched final-hour NWP comparison' in M and 'not a theoretical error bound' in S
# The two portable patches are canonical; historical per-task patches are not replayed in the live tree.
def makepatch(before,after,out):
 text=''
 for f in docs:
  a=(before/f).read_text();b=(after/f).read_text();text+=''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='a/'+f,tofile='b/'+f))
 text=''.join(l.rstrip('\n')+'\t2026-11-15 00:00:00 +0000\n' if l.startswith(('--- a/','+++ b/')) else l for l in text.splitlines(True));out.write_text(text)
makepatch(B,CLOSED,P/'R3_07_12_CUMULATIVE.patch');makepatch(CLOSED,ROOT,P/'R3_13_OPEN_INCREMENT.patch')
with tempfile.TemporaryDirectory(prefix='r3-batch-reconstruct-',dir='/private/tmp') as tmp:
 t=Path(tmp)
 for f in docs:shutil.copyfile(B/f,t/f)
 for name,expected in [('R3_07_12_CUMULATIVE.patch',CLOSED),('R3_13_OPEN_INCREMENT.patch',ROOT)]:
  subprocess.run(['git','-C',str(t),'apply','--check',str(P/name)],check=True,capture_output=True);subprocess.run(['git','-C',str(t),'apply',str(P/name)],check=True,capture_output=True)
  for f in docs:assert (t/f).read_bytes()==(expected/f).read_bytes(),f
  assert all(canonical(x) in canonical((t/'manuscript.tex').read_text()+(t/'Supplementary.tex').read_text()) for x in args((t/'Response letter.tex').read_text(),'RevisedExcerpt'))
# Freeze source/index for the entire archiving operation.
guard=dict(HEAD=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),index_raw=subprocess.check_output(['git','diff','--cached','--raw'],text=True),source_sha256={f:sha(ROOT/f) for f in docs},figure_sha256=figs)
(P/'ORIGINAL_WORKTREE_GUARD.json').write_text(json.dumps(guard,indent=2));(P/'BASE_AND_AFTER_HASHES.json').write_text(json.dumps(dict(base={f:sha(B/f) for f in docs},closed_after={f:sha(CLOSED/f) for f in docs},current={f:sha(ROOT/f) for f in docs}),indent=2))
labels={};aux=Path('build/Supplementary.aux').read_text()
for lab,n in [('stab:r2m3_upstream_xgboost','S26'),('stab:r2m3_upstream_bilstm_attn','S27'),('stab:r3d_upstream_increments','S52'),('sfig:r3d_upstream_effects','S3'),('stab:r3f_seasonal_associations','S53'),('stab:r3f_seasonal_v10_ablation','S54'),('stab:r3window_six_models','S55'),('stab:r3window_curve','S56'),('stab:r3huber_scores','S57'),('stab:r3huber_pairs','S58'),('stab:r3huber_xgb','S59'),('stab:r3nwp_common_context','S60')]:
 z=re.search(r'\\newlabel\{'+lab+r'\}\{\{([^}]+)\}\{([^}]+)',aux);assert z and z[1]==n;labels[lab]=dict(number=z[1],page=z[2])
for doc in [M,S]:
 labs=re.findall(r'\\label\{([^}]+)\}',doc);assert len(labs)==len(set(labs))
# Counters must be continuous: main label aliases are ignored, Supplementary tables each have one label.
nums=[int(x) for x in re.findall(r'\\newlabel\{stab:[^}]+\}\{\{S(\d+)\}',aux)];assert sorted(nums)==list(range(1,61)),nums
out=dict(protected_baseline_excerpts=130,current_exact_excerpts=144,new_in_batch=14,all_match=True,all_non_target_responses_unchanged=True,old_main_prose_table_figure_source_preserved=True,old_S1_S51_prefix_unchanged=True,figure_hashes_unchanged=len(figs),raw_CSV_fields_checked=counts,total_raw_CSV_fields=sum(counts.values()),S52_rows_checked=len(s52),S52_numeric_entries=9*len(s52),portable_patch_chain_byte_identical=True,R3_07_12_eligible=True,R3_13_core_gap='Strict same-window NWP comparator unavailable; OPEN',labels=labels)
(P/'BATCH_VERIFICATION.json').write_text(json.dumps(out,indent=2));(P/'EXCERPT_INDEX.json').write_text(json.dumps([dict(index=i+1,sha256=hashlib.sha256(x.encode()).hexdigest(),matches=True) for i,x in enumerate(new)],indent=2));print(json.dumps({k:v for k,v in out.items() if k!='labels'},indent=2))
