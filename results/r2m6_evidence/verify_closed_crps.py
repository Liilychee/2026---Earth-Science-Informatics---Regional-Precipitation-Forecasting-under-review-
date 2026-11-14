"""Independent analytic CRPS; quadrature used only to validate formulas and diagnose archive-grid error.
Run from repository: /path/to/python results/r2m6_evidence/verify_closed_crps.py
Reads pinned q11 blobs; never imports training modules or modifies original outputs.
"""
import json,ast,math,platform,sys
import numpy as np
import scipy
from scipy.special import ndtr,betaln,gammainc
from scipy.integrate import quad
from scipy.stats import norm,gamma as gamma_dist,t
from evidence_common import *
PHI=lambda z:np.exp(-.5*np.asarray(z)**2)/np.sqrt(2*np.pi)

def gaussian(y,mu,s):
 z=(y-mu)/s
 return s*(z*(2*ndtr(z)-1)+2*PHI(z)-1/np.sqrt(np.pi))

def tobit(y,mu,s):
 # X=max(0,N(mu,s^2)); not a truncated/renormalized Gaussian.
 yp=np.maximum(y,0);a=-mu/s;z=(yp-mu)/s;q=ndtr(-a)
 # J=s int_a^inf (1-Phi(u))^2 du, evaluated analytically.
 J=s*(-a*q*q+2*q*PHI(a)-ndtr(-np.sqrt(2)*a)/np.sqrt(np.pi))
 A=lambda u:u*ndtr(u)+PHI(u)
 return 2*s*(A(z)-A(a))-yp+J+np.maximum(-y,0)

def bergamma(y,p,a,b):
 # P(X=0)=1-p; X|X>0~Gamma(a,scale=b).
 yp=np.maximum(y,0);G=gammainc(a,yp/b);G1=gammainc(a+1,yp/b)
 eabs=(1-p)*yp+p*(yp*(2*G-1)+a*b*(1-2*G1))
 half_pair=p*(1-p)*a*b+p*p*b*np.exp(-betaln(.5,a))
 return eabs-half_pair+np.maximum(-y,0)

def analytic(dist,y,d):
 a=d.par1.to_numpy();b=d.par2.to_numpy()
 assert np.isfinite(a).all() and (b>0).all()
 if dist=='gaussian':return gaussian(y,a,b)
 if dist=='tobit':return tobit(y,a,b)
 c=d.par3.to_numpy();assert ((a>0)&(a<1)&(c>0)).all()
 return bergamma(y,a,b,c)

def scalar_cdf(dist,x,par):
 if dist=='gaussian':return norm.cdf((x-par[0])/par[1])
 if x<0:return 0.
 if dist=='tobit':return norm.cdf((x-par[0])/par[1])
 return (1-par[0])+par[0]*gamma_dist.cdf(x,par[1],scale=par[2])

def independent_integral(dist,y,par):
 # Split at y and atom 0; infinite tails. This checks, not defines, closed-form values.
 f=lambda x:(scalar_cdf(dist,x,par)-(y<=x))**2
 lo=-np.inf if dist=='gaussian' else min(0.,y)
 points=sorted(set([v for v in [0.,y] if lo<v]));ends=[lo]+points+[np.inf]
 return sum(quad(f,a,b,epsabs=2e-11,epsrel=2e-10,limit=250)[0] for a,b in zip(ends[:-1],ends[1:]))

if __name__ == '__main__':
    # Only function AST nodes from the archived integration module: no top-level execution/writes.
    source=blob('code/q11_twcrps.py').decode();tree=ast.parse(source)
    functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['cdf','twcrps']]
    ns={'np':np,'norm':norm,'gamma_dist':gamma_dist,'ZMAX':8.,'NZ':3000,'TRAPZ':np.trapezoid if hasattr(np,'trapezoid') else np.trapz}
    exec(compile(ast.Module(body=functions,type_ignores=[]),'<archived q11 integration functions only>','exec'),ns)
    refs=frame('results/metrics/q11_twcrps_per_seed.csv');reference={(r.config,int(r.seed)):float(r.full) for r in refs.itertuples()}
    checks=[];summ=[];formula=[];cases={};closed_cases={};alignment=None
    for config,prefix in CONFIGS.items():
     dist=prefix.split('__')[0];av=[];rv=[];scores=[];an_scores=[]
     for seed in SEEDS:
      d,y=load(config,seed);identity=(d.valid_time.to_list(),d.y_true.to_list())
      if alignment is None:alignment=identity
      else:assert identity==alignment
      c=analytic(dist,y,d);assert np.isfinite(c).all() and c.min()>-1e-10
      # Reproduce ONLY the saved full-integral scoring, not training or replacing formal CSV.
      v=ns['twcrps'](dist,d,y,None);stored=reference[config,seed]
      assert abs(v.mean()-stored)<2e-14,(config,seed,v.mean(),stored)
      a=c.mean();raw_c=analytic(dist,d.y_true.to_numpy(),d);av.append(a);rv.append(stored);scores.append(v);an_scores.append(c)
      checks.append(dict(config=config,seed=seed,n=len(y),closed_crps=a,raw_target_closed_crps=raw_c.mean(),raw_vs_scored_target_mean_difference=raw_c.mean()-a,archived_full=stored,difference=a-stored,abs_difference=abs(a-stored),reproduced_full=v.mean(),grid_reproduction_abs_error=abs(v.mean()-stored)))
      # Extremes and zeros exercise the censor/point-mass contribution for every seed.
      take=sorted(set([0,int(np.argmax(y)),int(np.argmax(d.par2)),int(np.argmin(np.abs(y))),len(y)//2]))
      for i in take:
       par=[float(d.iloc[i][k]) for k in ['par1','par2','par3']];q=independent_integral(dist,float(y[i]),par);err=abs(q-c[i]);assert err<2e-8,(dist,seed,i,err)
       formula.append(dict(config=config,seed=seed,row_test_zero_based=i,y=y[i],analytic=c[i],adaptive_quadrature=q,abs_error=err))
      print(config,seed,'closed=',format(a,'.12f'),'full=',format(stored,'.12f'),'delta=',format(a-stored,'.3g'),flush=True)
     cases[config]=np.mean(scores,axis=0);closed_cases[config]=np.mean(an_scores,axis=0)
     summ.append(dict(config=config,closed_mean=np.mean(av),closed_sd=np.std(av,ddof=1),full_mean=np.mean(rv),full_sd=np.std(rv,ddof=1),closed_4dp=format(np.mean(av),'.4f'),full_4dp=format(np.mean(rv),'.4f'),max_seed_abs_difference=max(abs(np.array(av)-rv))))
    # Analytic identity limits: zero point mass and near-uncensored/censored normal.
    assert np.allclose(bergamma(np.array([0.,1.]),np.array([0.,0.]),np.array([2.,2.]),np.array([.3,.3])),[0.,1.])
    assert np.allclose(tobit(np.array([0.,1.]),np.array([-10.,-10.]),np.array([.1,.1])),[0.,1.],atol=1e-12)
    write_csv(checks,'closed_crps_per_seed.csv');write_csv(summ,'closed_crps_summary.csv');write_csv(formula,'analytic_formula_checks.csv')
    # Original paired full rows: mean per-case scores across seeds, then shared resampling.
    paired=frame('results/metrics/q11_twcrps_paired.csv');full=paired[paired.threshold=='full'];rng=np.random.default_rng(42);n=3939;L=28;B=5000;nb=int(np.ceil(n/L));starts=rng.integers(0,n-L+1,size=(B,nb));idx=(starts[:,:,None]+np.arange(L)).reshape(B,-1)
    assert idx.shape==(5000,3948);pr=[]
    for r in full.itertuples():
     v=cases[r.a]-cases[r.b] # seed-averaged scores, not predictions.
     bd=v[idx].mean(axis=1);lo,hi=np.percentile(bd,[2.5,97.5]);bdn=v[idx[:,:n]].mean(axis=1);lon,hin=np.percentile(bdn,[2.5,97.5])
     dseed=np.array([reference[r.a,s]-reference[r.b,s] for s in SEEDS]);m=dseed.mean();h=t.ppf(.975,4)*dseed.std(ddof=1)/np.sqrt(5)
     assert max(abs(lo-r.boot_low),abs(hi-r.boot_high),abs(m-r.diff_seed_mean),abs(m-h-r.seed_t_low),abs(m+h-r.seed_t_high))<2e-13
     cv=closed_cases[r.a]-closed_cases[r.b];cl,ch=np.percentile(cv[idx].mean(axis=1),[2.5,97.5])
     pr.append(dict(a=r.a,b=r.b,threshold='full',archived_difference=r.diff_seed_mean,reproduced_difference=m,archived_seed_t_low=r.seed_t_low,archived_seed_t_high=r.seed_t_high,reproduced_seed_t_low=m-h,reproduced_seed_t_high=m+h,archived_boot_low=r.boot_low,archived_boot_high=r.boot_high,reproduced_boot_low=lo,reproduced_boot_high=hi,closed_formula_boot_low=cl,closed_formula_boot_high=ch,diagnostic_truncated_n_boot_low=lon,diagnostic_truncated_n_boot_high=hin,retained_samples=3948,diagnostic_truncated_samples=n))
    write_csv(pr,'paired_full_verification.csv')
    info=dict(source_commit=COMMIT,python=sys.version,numpy=np.__version__,scipy=scipy.__version__,n=n,block=L,replicates=B,seed=42,blocks_per_replicate=nb,actual_resample_length=idx.shape[1],extra_samples=9,targets_at_or_below_zero_tol=int(np.sum(np.array(alignment[1])<=ZERO_TOL)),primary_max_seed_abs_difference=max(r['abs_difference'] for r in checks if r['config'] in list(CONFIGS)[:3]),all_configs_max_seed_abs_difference=max(r['abs_difference'] for r in checks),max_formula_quadrature_error=max(r['abs_error'] for r in formula),all_full_rows_matched=True)
    (OUT/'CRPS_VERIFICATION.json').write_text(json.dumps(info,indent=2));print(json.dumps(info,indent=2));print(pd.DataFrame(summ).to_string(index=False))
