# coding: utf-8
from pathlib import Path
import fitz,json,re,hashlib,csv
P=Path('results/r2m5_integration');out={};colors=[]
for n in ['Supplementary','manuscript','Response letter']:
 log=Path('build/'+n+'.log').read_text();assert not re.search(r'undefined|multiply defined|Overfull \\hbox|Float too large|^!',log,re.M),n
 d=fitz.open('build/'+n+'.pdf');raw=Path('build/'+n+'.pdf').read_bytes();out[n]=dict(pages=len(d),md5=hashlib.md5(raw).hexdigest(),sha256=hashlib.sha256(raw).hexdigest(),no_undefined_references_or_blocking_error=True,overfull_hbox=0,overfull_vbox_heights=sorted(set(re.findall(r'Overfull \\vbox \(([^)]+)\)',log))))
 for i,p in enumerate(d):
  t=p.get_text()
  if n=='Supplementary' and i>=30:
   for b in p.get_text('dict')['blocks']:
    for l in b.get('lines',[]):
     for s in l['spans']:
      if s['text'].strip() and s['bbox'][1]<790:
       assert s['color']==0xff0000,(n,i+1,s['text'],hex(s['color']))
       assert s['bbox'][0]>=65 and s['bbox'][2]<=p.rect.width-65,(i+1,s['bbox'])
   p.get_pixmap(matrix=fitz.Matrix(1,1)).save(str(P/'render'/f'Supplementary_{i+1}.png'))
  if n=='manuscript' and ('Retrospective Rolling-Origin' in t or 'The rolling-origin analysis is retrospective' in t):out[n].setdefault('key_pages',[]).append(i+1)
  if n=='Response letter' and 'Insufficient Temporal Robustness' in t:out[n]['R2_M5_start']=i+1
  if n=='Response letter' and 'Qualified model comparison' in t:out[n]['R2_M5_end']=i+1
  for b in p.get_text('dict')['blocks']:
   for l in b.get('lines',[]):
    for s in l['spans']:
     if 'S32' in s['text'] or ('S38' in s['text'] and n!='Supplementary'):
      if n=='manuscript':assert s['color']==0xff0000
      if n=='Response letter':assert s['color'] in [0xff0000,0x0000ff]
      colors.append(dict(document=n,page=i+1,color=hex(s['color']),text=s['text']))
(P/'PDF_CHECK.json').write_text(json.dumps(out,indent=2));(P/'COLOR_CHECK.json').write_text(json.dumps(colors,indent=2))
# Actual aux table/section numbers and pages.
loc={}
for n in ['Supplementary','manuscript']:
 aux=Path('build/'+n+'.aux').read_text()
 for label,number,page in re.findall(r'\\newlabel\{((?:stab:r2m5_|sec:rolling_origin_)[^}]+)\}\{\{([^}]+)\}\{([^}]+)\}',aux):loc[label]=dict(number=number,page=int(page),document=n)
(P/'LOCATIONS.json').write_text(json.dumps(loc,indent=2))
# Machine-readable flat transcription index in addition to raw JSON with per-cell settings.
rows=json.loads((P/'CELL_INDEX.json').read_text())
with (P/'CELL_INDEX.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['file','line','field','json_path','raw','display']);w.writeheader();w.writerows({k:r.get(k,'') for k in w.fieldnames} for r in rows)
print(json.dumps(out,indent=2));print(json.dumps(loc,indent=2))
