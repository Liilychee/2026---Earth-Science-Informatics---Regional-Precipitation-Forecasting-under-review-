from pathlib import Path
import fitz,hashlib,re,json
P=Path(__file__).resolve().parent;R=P/'local_render';R.mkdir(exist_ok=True)
prior={}
for d in Path('results').glob('r3*'):
 if d==P:continue
 for f in d.rglob('*.png'):
  if 'render' in f.parts or f.parent.name in ['finalization','concise_review']:prior.setdefault(hashlib.sha256(f.read_bytes()).hexdigest(),[]).append(str(f))
phrases=['original predictors were restricted','sampled values retain their native temporal','Seasonal training-only diagnostics','six-snapshot (30 h) history is','Input-history sensitivity does not','The original climatology uses','MSE targets the conditional mean','prediction-to-observation standard-deviation ratio decreases','retrieved HRES subset contains','We thank the reviewer for this suggestion','We thank the reviewer for highlighting these distinctions','We distinguish seasonal statistical association','history length requires justification','original climatology was not seasonally dependent','MSE is aligned with our','physical numerical forecast is an important']
out={};new=[]
for stem in ['manuscript','Supplementary','Response letter']:
 d=fitz.open('build/'+stem+'.pdf');log=Path('build/'+stem+'.log').read_text(errors='replace');bad=[l for l in log.splitlines() if re.search('undefined|multiply defined|Overfull|Float too large|^!',l)];assert not [l for l in bad if 'Overfull \\vbox (1.41457pt' not in l]
 inds=set()
 for i,p in enumerate(d):
  text=' '.join(p.get_text().split())
  if any(s in text for s in phrases):inds.add(i)
 if stem=='Supplementary':inds.update(range(58,len(d)))
 pages=[]
 for i in sorted(inds):
  raw=d[i].get_pixmap(matrix=fitz.Matrix(1.5,1.5)).tobytes('png');f=R/(stem.replace(' ','_')+f'-{i+1}.png');f.write_bytes(raw);h=hashlib.sha256(raw).hexdigest();matches=prior.get(h,[]);pages.append(dict(page=i+1,path=str(f.relative_to(P)),sha256=h,pixel_identical_previous_render=matches))
  if not matches:new.append(str(f.relative_to(P)))
 out[stem]=dict(pages=len(d),pdf_sha256=hashlib.sha256(Path('build/'+stem+'.pdf').read_bytes()).hexdigest(),relevant_pages=pages,preexisting_template_vbox_count=len(bad),blocking_new_warnings=False)
(P/'PDF_CHECK.json').write_text(json.dumps(out,indent=2));(P/'NEW_VISUAL_REVIEW_REQUIRED.json').write_text(json.dumps(new,indent=2));print('Page counts:',{k:v['pages'] for k,v in out.items()});print('Rendered',sum(len(x['relevant_pages']) for x in out.values()),'pages;',len(new),'not pixel-identical to saved actual reviews:');print(json.dumps(new,indent=2))
