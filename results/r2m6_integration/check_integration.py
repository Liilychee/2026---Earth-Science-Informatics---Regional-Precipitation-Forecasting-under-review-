"""Stored-value / scope verification only: no model fitting or re-estimation of formal metrics."""
from pathlib import Path
import re,json,csv,hashlib,subprocess,statistics
P=Path(__file__).resolve().parent;B=P/'before';M=Path('manuscript.tex').read_text();S=Path('Supplementary.tex').read_text();R=Path('Response letter.tex').read_text();OM=(B/'manuscript.tex').read_text();OS=(B/'Supplementary.tex').read_text();OR=(B/'Response letter.tex').read_text()
assert S[:S.index('% R2-M6:')].rstrip()==OS[:OS.index('\\end{document}')].rstrip()
a,b=R.index('% Review ID: R2 M6'),R.index('% Review ID: R2 M7');aa,bb=OR.index('% Review ID: R2 M6'),OR.index('% Review ID: R2 M7');assert R[:a]==OR[:aa] and R[b:]==OR[bb:]
comment='The Gaussian assumption produces negative prediction bounds and severe undercoverage for heavy rainfall. Please evaluate a precipitation-appropriate distribution or provide stronger justification for the chosen formulation.'
assert comment in R[a:b] and comment in Path('comment.txt').read_text()
for kind in ['figure','table']:
 p=r'\\begin\{'+kind+r'\}.*?\\end\{'+kind+r'\}'
 old=re.findall(p,OM,re.S);new=re.findall(p,M,re.S)
 if kind=='table':old=[x for x in old if 'tab:probabilistic_results' not in x];new=[x for x in new if 'tab:probabilistic_results' not in x]
 assert old==new,kind
assert (P/'ORIGINAL_A_TABULAR.tex').read_text() in M
assert Path('sn-bibliography.bib').read_text().startswith((B/'sn-bibliography.bib').read_text())
# All old excerpts preserved, including colors stripped only for textual equivalence.
def args(text,command):
 out=[];pos=0;needle='\\'+command+'{'
 while (pos:=text.find(needle,pos))>=0:
  start=pos+len(needle);i=start;depth=1
  while depth:
   if text[i]=='{' and text[i-1]!='\\':depth+=1
   if text[i]=='}' and text[i-1]!='\\':depth-=1
   i+=1
  out.append(text[start:i-1]);pos=i
 return out

def canonical(t):
 needle=r'\textcolor{red}{'
 while needle in t:
  a=t.index(needle);st=a+len(needle);i=st;dep=1
  while dep:
   if t[i]=='{' and t[i-1]!='\\':dep+=1
   if t[i]=='}' and t[i-1]!='\\':dep-=1
   i+=1
  t=t[:a]+t[st:i-1]+t[i:]
 return re.sub(r'\s+',' ',t).strip()
oldex=args(OR,'RevisedExcerpt');newex=args(R,'RevisedExcerpt');assert all(x in newex for x in oldex)
assert all(canonical(x) in canonical(M) for x in newex)
ex=json.loads((P/'FINAL_EXCERPTS.json').read_text());assert all(v in M and '\\RevisedExcerpt{'+v+'}' in R[a:b] for v in ex.values())
source={}
for x in json.loads((P/'SOURCE_INDEX.json').read_text()):
 raw=(P/'evidence'/Path(x['path']).name).read_bytes();assert hashlib.md5(raw).hexdigest()==x['md5'];assert raw==subprocess.check_output(['git','show',x['commit']+':'+x['path']]);source[Path(x['path']).name]=x
D={}
for p in (P/'evidence').glob('*.csv'):D[p.name]=list(csv.DictReader(p.open()))
cs=json.loads((P/'CELL_INDEX.json').read_text())
for c in cs:
 if 'aggregate' in c:
  v=[float(next(x['full'] for x in D[c['file']] if x['config']==cfg and int(x['seed'])==seed)) for cfg,seed in c['keys']]
  value=statistics.mean(v) if c['aggregate']=='mean' else statistics.stdev(v);assert f'{value:.4f}'==c['display']
 else:
  raw=D[c['file']][c['line']-2][c['field']];assert raw==c['raw'];display='---' if raw=='' or raw.lower()=='nan' else format(float(raw),('+' if c['signed'] else '')+'.'+str(c['digits'])+'f');assert display==c['display']
 assert c['display'] in S or c['display'] in M
# Exact destination row positions, not merely global numeric membership.
rowcount=0
for t in json.loads((P/'ROW_INDEX.json').read_text()):
 a=S.index('\\label{'+t['label']+'}');z=S[a:S.index('\\end{longtable}',a)];z=z[z.index('\\endfoot')+len('\\endfoot'):]
 assert ''.join(t['rows']).strip()==z.strip(),t['label'];rowcount+=len(t['rows'])
for text in [M,S]:
 labs=re.findall(r'\\label\{([^}]+)\}',text);assert len(labs)==len(set(labs))
assert len(re.findall(r'\\label\{stab:',S))==46
# Main B must only use numerical-integral full CRPS; original A is preserved separately.
qtab=M[M.rfind('\\begin{table}',0,M.index('\\label{tab:probabilistic_results}')):M.index('\\end{table}',M.index('\\label{tab:probabilistic_results}'))]
assert '0.0961' in qtab and '0.0847' in qtab and '0.0773' in qtab
assert '3,948' in ex['bootstrap'] and 'not a strict single-factor experiment' in ex['likelihood_design']
assert 'upper-tail precipitation' not in R[R.index('% Review ID: R2 M6'):R.index('% Review ID: R2 M7')].split('\\ReviewerComment{')[1].split('}')[0]
result=dict(numeric_transcriptions_verified=len(cs),new_supplementary_tables=8,supplementary_data_rows_verified=rowcount,all_evidence_excerpts_verified=len(newex),previous_excerpts_preserved=len(oldex),new_excerpts_exact=len(ex),old_table_A1_numeric_tabular_identical=True,all_other_main_tables_and_figures_identical=True,all_supplementary_S1_S38_source_unchanged=True,all_other_response_sections_unchanged=True,original_review_heavy_rainfall_correct=True)
(P/'VERIFICATION.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
# Independent per-row numeric-column check against CSV fields (beyond membership checks).
def getrows(label):
 st=S.index('\\label{'+label+'}');end=S.index('\\end{longtable}',st);u=S[st:end];u=u[u.index('\\endfoot')+len('\\endfoot'):]
 return [l.strip().removesuffix(r'\\').split(' & ') for l in u.strip().splitlines()]
def dig(s):return re.findall(r'[+-]?\d+\.\d+|[+-]?\d+',s)
def fmt(v,n=4,sign=False):return format(float(v),('+' if sign else '')+'.'+str(n)+'f')
def flat(cols):return sum([dig(x) for x in cols],[])
r=getrows('stab:r2m6_q16_intervals');qs=D['q16_interval_summary.csv'];assert len(r)==len(qs)==9
for cells0,q in zip(r,qs):
 expect=[fmt(q['n_runs'],0),fmt(q['n_mean'],0)]+[fmt(q[k]) for k in ['PICP90_mean','PICP90_std','MPIW90_mean','MPIW90_std','PICP95_mean','PICP95_std','MPIW95_mean','MPIW95_std']];assert flat(cells0[2:])==expect
configs=['Gaussian','Tobit','Bernoulli-gamma'];ss=[42,123,7,2024,99]
per={(x['config'],int(x['seed'])):x for x in D['q11_per_seed.csv']};tw={(x['config'],int(x['seed'])):x for x in D['q11_twcrps_per_seed.csv']};w={(x['config'],int(x['seed'])):x for x in D['width90_per_seed.csv']}
r=getrows('stab:r2m6_seed_scores');assert len(r)==15
for cells0,(cfg,seed) in zip(r,[(c,s) for c in configs for s in ss]):
 q=tw[cfg,seed];p=per[cfg,seed];assert cells0[1]==str(seed);assert flat(cells0[2:])==[fmt(q[k],6) for k in ['full','r0.1','rQ95','r1.0']]+[fmt(p[k],6) for k in ['is95_all','brier_gt0.1','brier_geQ95','brier_ge1.0']]
r=getrows('stab:r2m6_seed_intervals');assert len(r)==15
for cells0,(cfg,seed) in zip(r,[(c,s) for c in configs for s in ss]):
 p=per[cfg,seed];assert cells0[1]==str(seed);assert flat(cells0[2:])==[fmt(p[k],6) for k in ['picp95_all','picp95_wet','picp95_upper','picp90_all','width95_all']]+[fmt(w[cfg,seed]['width90'],6),fmt(p['neg_lower95'],3)]
r=getrows('stab:r2m6_score_pairs');assert len(r)==16
for cells0,q in zip(r,D['q11_twcrps_paired.csv']):assert flat(cells0[2:])==[fmt(q[k],6,True) for k in ['diff_seed_mean','seed_t_low','seed_t_high','boot_low','boot_high']]+[fmt(q['n_seeds_a_better'],0),'5']
mapping={'is95':'is95_all','cov95':'picp95_all','width95':'width95_all','bs_gt0.1':'brier_gt0.1','bs_geQ95':'brier_geQ95','bs_ge1.0':'brier_ge1.0'}
qs=[q for q in D['q11_paired_bootstrap.csv'] if q['subset']=='all' and q['score'] in mapping];r=getrows('stab:r2m6_other_pairs');assert len(r)==len(qs)==18
for cells0,q in zip(r,qs):
 z=next(x for x in D['q11_paired_seed.csv'] if x['a']==q['a'] and x['b']==q['b'] and x['metric']==mapping[q['score']]);assert flat(cells0[2:])==[fmt(q['diff'],5,True),fmt(z['seed_t_low'],5,True),fmt(z['seed_t_high'],5,True),fmt(q['boot_low'],5,True),fmt(q['boot_high'],5,True)]
r=getrows('stab:r2m6_dry001');assert len(r)==10
for cells0,(cfg,seed) in zip(r,[(c,s) for c in ['Tobit (dry 0.001)','Bernoulli-gamma (dry 0.001)'] for s in ss]):
 q=tw[cfg,seed];p=per[cfg,seed];assert cells0[1]==str(seed);assert flat(cells0[2:])==[fmt(q[k],6) for k in ['full','r0.1','rQ95','r1.0']]+[fmt(p[k],6) for k in ['picp95_all','picp95_upper','width95_all']]
r=getrows('stab:r2m6_dry_history');assert len(r)==6
for cells0,q in zip(r,D['dry_seed42_sensitivity.csv']):assert flat(cells0[1:])==[fmt(q['train_dry'],3),'42',fmt(q['val_crps_199_quantile'],6),fmt(q['test_crps_199_quantile'],6)]
r=getrows('stab:r2m6_conditional_history');assert len(r)==5
for cells0,q in zip(r,D['q11_summary.csv']):assert flat(cells0[1:])==[fmt(q[k]) for k in ['crps_wet_mean','crps_wet_sd','crps_upper_mean','crps_upper_sd']]
# Verify main B metric columns separately against full integrals and interval summary sources.
mt=qtab[qtab.index('Metric & Gaussian'):];mt=mt[mt.index('\\hline')+len('\\hline'):mt.index('\\hline',mt.index('\\hline')+len('\\hline'))]
mainrows=[x.strip().removesuffix(r'\\').split(' & ') for x in mt.strip().splitlines()];assert len(mainrows)==9
summary={q['config']:q for q in D['q11_summary.csv']};ws={q['config']:q for q in D['width90_summary.csv']}
keys=['full','is95_all','picp95_all','picp95_wet','picp95_upper','picp90_all','width95_all','width90','neg_lower95']
for rr,key in zip(mainrows,keys):
 for cell,cfg in zip(rr[1:],configs):
  if key=='full':v=[float(tw[cfg,s]['full']) for s in ss];expected=[fmt(statistics.mean(v)),fmt(statistics.stdev(v))]
  elif key=='width90':expected=[fmt(ws[cfg]['width90_mean']),fmt(ws[cfg]['width90_sd'])]
  else:expected=[fmt(summary[cfg][key+'_mean']),fmt(summary[cfg][key+'_sd'])]
  assert dig(cell)==expected,(key,cfg,cell,expected)
result['independent_numeric_column_checks_all_new_tables']=True;result['main_B_metrics_checked']=27
(P/'VERIFICATION.json').write_text(json.dumps(result,indent=2));print('All 94 supplementary data rows and 27 main B metric entries independently matched CSV columns.')
# Main A2: the three separate q16 all-target rows, each with Cov90/Width90/Width95 mean+SD.
u=qtab[qtab.index('A2. Separate'):];u=u[u.index('\\begin{tabular}'):u.index('\\end{tabular}')];u=u[u.index('\\hline')+len('\\hline'):];u=u[u.index('\\hline')+len('\\hline'):];u=u[:u.index('\\hline')]
rr=[l.strip().removesuffix(r'\\').split(' & ') for l in u.strip().splitlines()];qq=[q for q in D['q16_interval_summary.csv'] if q['subset']=='all'];assert len(rr)==len(qq)==3
for r,q in zip(rr,qq):assert flat(r[1:])==[fmt(q[k]) for k in ['PICP90_mean','PICP90_std','MPIW90_mean','MPIW90_std','MPIW95_mean','MPIW95_std']]
result['main_A2_metrics_checked']=9;result['original_A1_scalars_preserved']=18
(P/'VERIFICATION.json').write_text(json.dumps(result,indent=2))
