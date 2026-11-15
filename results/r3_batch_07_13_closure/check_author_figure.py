from pathlib import Path
import fitz,json,re,hashlib
P=Path('results/r3_batch_07_13_closure');rows=json.loads(Path('results/r3sec32d_integration/finalization/FIGURE_CELL_INDEX.json').read_text());d=fitz.open('Figures/r3M7_upstream_effects.pdf');draw=d[0].get_drawings();out=[]
for panel,zero in enumerate([203.37594604492188,322.412353515625]):
 scale=(163.9225616455078-124.46917724609375)/.01
 color=(.9019608,.6235294,0) if panel==0 else (0,.4470588,.6980392)
 lines=[x['rect'] for x in draw if x['type']=='s' and x['color'] and max(abs(a-b) for a,b in zip(x['color'],color))<1e-5 and abs(x['rect'].height)<1e-5 and x['rect'].width>0 and x['rect'].y0<185]
 ys=sorted(set(round(x.y0,3) for x in lines));assert len(ys)==5
 for row,y in zip(rows[panel*5:panel*5+5],ys):
  seg=sorted([x for x in lines if abs(x.y0-y)<.001],key=lambda x:x.width);assert len(seg)==2
  expected=sorted([(float(row[a]),float(row[b])) for a,b in [('t_lo','t_hi'),('boot_lo','boot_hi')]],key=lambda z:z[1]-z[0])
  err=max(abs((rect[j]-zero)/scale-v) for rect,e in zip(seg,expected) for j,v in zip([0,2],e));assert err<1e-7,err
  markers=[x['rect'] for x in draw if x['type']=='fs' and x['color'] and max(abs(a-b) for a,b in zip(x['color'],color))<1e-5 and abs((x['rect'].y0+x['rect'].y1)/2-y)<.001 and x['rect'].width>1 and x['rect'].height>1]
  assert len(markers)==1;point=((markers[0].x0+markers[0].x1)/2-zero)/scale;assert abs(point-float(row['d_rmse_mean']))<1e-7
  out.append(dict(model=row['model'],config=row['config'],ref=row['ref'],interval_max_abs_pdf_roundoff=err,point_abs_pdf_roundoff=abs(point-float(row['d_rmse_mean']))))
(P/'FIGURE_VECTOR_CHECK.json').write_text(json.dumps(out,indent=2));print('10 points + 20 interval pairs matched PDF vector coordinates (tolerance 1e-7 mm/h)')
