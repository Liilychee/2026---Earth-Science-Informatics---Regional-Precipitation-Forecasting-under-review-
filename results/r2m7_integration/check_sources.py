"""Read-only checks of fixed archived statistics and author PDF; no raw-data recomputation or drawing."""
from pathlib import Path
import csv,json,hashlib,itertools
import numpy as np
import fitz
P=Path(__file__).resolve().parent;E=Path('results/r2m7_evidence')
rows=list(csv.DictReader((E/'r2m7_series_stats.csv').open()));summary=list(csv.DictReader((E/'r2m7_summary_comparison.csv').open()));long=list(csv.DictReader((E/'r2m7_pct_by_cell.csv').open()))
assert len(rows)==26;reg=next(r for r in rows if r['Role']=='regional');cells=[r for r in rows if r['Role']!='regional'];assert len(cells)==25
assert len({(r['Latitude'],r['Longitude']) for r in cells})==25
assert set((float(r['Latitude']),float(r['Longitude'])) for r in cells)==set(itertools.product([52.75,53,53.25,53.5,53.75],[-6.75,-6.5,-6.25,-6,-5.75]))
assert all(r['N']=='18404' and r['First_time']=='2004-01-02 12:00:00' and r['Last_time']=='2016-08-07 06:00:00' and r['First_time']<=r['Max_time']<=r['Last_time'] for r in rows)
stats=['Mean','Wet_freq_ge_0.1','Q90','Q95','Q99','Q99.9','Max'];assert len(long)==175
# Six-decimal archived values can induce small ratio differences. Bound rounding rather than demand false bit equality.
def pct_ok(r,c,p):
 eps=.500001e-6;lo=100*((r-eps)/(c+eps)-1);hi=100*((r+eps)/(c-eps)-1)
 return lo-.500001e-6<=p<=hi+.500001e-6
for q in summary:
 key=q['Statistic'];x=np.array([float(r[key]) for r in cells]);R=float(reg[key]);assert float(q['Regional'])==R
 for f,v in [('Cell_min',x.min()),('Cell_median',np.median(x)),('Cell_max',x.max())]:assert abs(float(q[f])-v)<.500001e-6
 assert int(q['N_cells_regional_below'])==sum(R<x) and int(q['N_cells'])==25
 assert pct_ok(R,float(q['Cell_median']),float(q['Pct_vs_cell_median']))
for q in long:
 r=next(x for x in cells if x['Latitude']==q['Cell_latitude'] and x['Longitude']==q['Cell_longitude']);key=q['Statistic'];R=float(reg[key]);x=float(r[key]);assert float(q['Cell_value'])==x and float(q['Regional_value'])==R
 assert pct_ok(R,x,float(q['Pct_diff_regional_vs_cell']));assert (q['Regional_below_cell']=='True')==(R<x)
for key in ['Q99','Q99.9','Max']:assert all(float(reg[key])<float(r[key]) for r in cells)
# Actual vector marker coordinates independently checked against all 125 cell ratios and 5 regional ratios.
f=Path('Figures/r2M7_spatial_quantiles.pdf');d=fitz.open(f);assert len(d)==1;p=d[0];draw=p.get_drawings();plot=next(x['rect'] for x in draw if x.get('fill')==(1.,1.,1.) and x['rect'].width>290 and 10<x['rect'].y0<30)
keys=['Q90','Q95','Q99','Q99.9','Max'];ticks={k:p.search_for(k)[0] for k in keys};xs=[(ticks[k].x0+ticks[k].x1)/2 for k in keys]
markers={k:dict(cell=[],regional=[]) for k in keys}
for a in draw:
 if a.get('fill') is None:continue
 rr=a['rect'];x=(rr.x0+rr.x1)/2;y=(rr.y0+rr.y1)/2
 if not plot.contains(fitz.Point(x,y)):continue
 rgb=a['fill']
 kind='cell' if len(a['items'])==8 and all(.5<c<.8 for c in rgb) else 'regional' if len(a['items'])==4 and rgb==(0.,0.,0.) else None
 if kind:
  key=keys[int(np.argmin(np.abs(np.array(xs)-x)))];ratio=.6+(plot.y1-y)/plot.height*.7;markers[key][kind].append((x,y,ratio))
checks=[]
for key in keys:
 q=next(x for x in summary if x['Statistic']==key);median=float(q['Cell_median'])
 for kind,expected in [('cell',sorted(float(r[key])/median for r in cells)),('regional',[float(reg[key])/median])]:
  observed=sorted(markers[key][kind],key=lambda z:z[2]);assert len(observed)==len(expected)==(25 if kind=='cell' else 1)
  for i,(a,b) in enumerate(zip(observed,expected)):
   err=abs(a[2]-b);assert err<1e-5,(key,kind,i,err)
   checks.append(dict(statistic=key,series_type=kind,rank_by_ratio=i+1,pdf_ratio=a[2],csv_ratio=b,abs_error=err,pdf_x=a[0],pdf_y=a[1]))
 text=p.get_text();expected_annot=f"{float(q['Pct_vs_cell_median']):+.1f}%".replace('-','−');assert expected_annot in text,(key,expected_annot)
with (P/'FIGURE_POINT_CHECK.csv').open('w',newline='') as h:
 w=csv.DictWriter(h,fieldnames=list(checks[0]));w.writeheader();w.writerows(checks)
meta=dict(path=str(f),pages=1,bytes=f.stat().st_size,md5=hashlib.md5(f.read_bytes()).hexdigest(),sha256=hashlib.sha256(f.read_bytes()).hexdigest(),width_mm=p.rect.width*25.4/72,height_mm=p.rect.height*25.4/72,embedded_raster_images=len(p.get_images()),fonts=[x[3] for x in p.get_fonts()],font_pdf_bp=sorted(set(round(s['size'],3) for b in p.get_text('dict')['blocks'] for l in b.get('lines',[]) for s in l['spans'])),plot_markers_verified=len(checks),gray_markers=125,black_diamonds=5,max_abs_ratio_error=max(x['abs_error'] for x in checks),ratio_tolerance=1e-5,ratio_tolerance_reason='Six-decimal source CSV rounding and PDF coordinate precision; no raw prediction or figure regeneration.')
(P/'FIGURE_METADATA.json').write_text(json.dumps(meta,indent=2));(P/'DATA_CHECK.json').write_text(json.dumps(dict(series=26,cells=25,n_training_targets=18404,summary_rows=7,per_cell_percentages_verified=175,uniform_period=True,all_maxima_times_within_period=True,far_tail_below_all25=True,rounding_aware_ratio_verification=True),indent=2));print(json.dumps(meta,indent=2))
