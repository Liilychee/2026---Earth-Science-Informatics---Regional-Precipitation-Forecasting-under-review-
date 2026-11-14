"""Separate finite-support truncation and Heaviside grid errors; diagnostic only, no formal CSV replacement."""
from scipy.special import ndtr,gammainc,gammaincc
from scipy.stats import norm

from evidence_common import *
r=frame('results/metrics/q11_twcrps_per_seed.csv')
closed=pd.read_csv(OUT/'closed_crps_per_seed.csv')
rows=[]
for config in list(CONFIGS)[:3]:
 q=closed[closed.config==config].sort_values('abs_difference').iloc[-1];seed=int(q.seed);d,y=load(config,seed);dist=CONFIGS[config].split('__')[0]
 lo=-4. if dist=='gaussian' else 0.;U=8.;z=np.concatenate([np.linspace(lo,1.5,4000,endpoint=False),np.linspace(1.5,U,1000)])
 smooth=np.empty(len(y));p1=d.par1.to_numpy();p2=d.par2.to_numpy()
 for i in range(0,len(y),500):
  sl=slice(i,i+500)
  if dist in ['gaussian','tobit']:
   F=ndtr((z[None,:]-p1[sl,None])/p2[sl,None])
   def A(x):
    a=(x-p1[sl])/p2[sl];return p2[sl]*(a*ndtr(a)+norm.pdf(a))
   IF=A(U)-A(y[sl])
  else:
   p,a,b=p1[sl],p2[sl],d.par3.to_numpy()[sl]
   F=1-p[:,None]+p[:,None]*gammainc(a[:,None],z[None,:]/b[:,None])
   def A(x):return (1-p)*x+p*(x*gammainc(a,x/b)-a*b*gammainc(a+1,x/b))
   IF=A(U)-A(y[sl])
  smooth[sl]=np.trapezoid(F*F,z,axis=1)-2*IF+U-y[sl]
 if dist in ['gaussian','tobit']:
  a=(U-p1)/p2;S=ndtr(-a);bound=S*np.maximum(p2*norm.pdf(a)+(p1-U)*S,0.)
  if dist=='gaussian':
   a=(lo-p1)/p2;F=ndtr(a);bound+=F*np.maximum((lo-p1)*F+p2*norm.pdf(a),0.)
 else:
  p,a,b=p1,p2,d.par3.to_numpy();S=p*gammaincc(a,U/b)
  bound=S*np.maximum(p*(a*b*gammaincc(a+1,U/b)-U*gammaincc(a,U/b)),0.)
 rows.append(dict(config=config,seed=seed,archived_grid_full=q.archived_full,analytic_crps=q.closed_crps,archived_grid_error=q.abs_difference,same_grid_smooth_F_squared_with_analytic_step_integral=smooth.mean(),smooth_grid_abs_error=abs(smooth.mean()-q.closed_crps),mean_omitted_tail_upper_bound=bound.mean()))
write_csv(rows,'integration_error_diagnostic.csv');print(pd.DataFrame(rows).to_string(index=False))
