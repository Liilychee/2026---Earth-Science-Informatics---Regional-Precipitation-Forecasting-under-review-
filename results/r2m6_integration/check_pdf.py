"""Final PDF/reference/color QA. No statistics are recalculated."""
from pathlib import Path
import re,json,hashlib
import fitz
P=Path(__file__).resolve().parent;(P/'render').mkdir(exist_ok=True);loc={};out={};colors=[]
for name in ['Supplementary','manuscript']:
 a=Path('build/'+name+'.aux').read_text()
 for label,num,page in re.findall(r'\\newlabel\{((?:stab:r2m6_|sec:r2m6_|tab:probabilistic_results)[^}]*)\}\{\{([^}]+)\}\{([^}]+)\}',a):loc[label]=dict(number=num,page=int(page),document=name)
assert loc['tab:probabilistic_results']['number']=='5'
for name in ['Supplementary','manuscript','Response letter']:
 log=Path('build/'+name+'.log').read_text();assert not re.search(r'undefined|multiply defined|Overfull \\hbox|Float too large|^!',log,re.M),name
 d=fitz.open('build/'+name+'.pdf');raw=Path('build/'+name+'.pdf').read_bytes();out[name]=dict(pages=len(d),md5=hashlib.md5(raw).hexdigest(),sha256=hashlib.sha256(raw).hexdigest(),no_undefined_or_duplicate_references=True,overfull_hbox=0,vbox_warnings=sorted(set(re.findall(r'Overfull \\vbox \(([^)]+)\)',log))))
 for i,page in enumerate(d):
  text=page.get_text();render=name=='Supplementary' and i>=41
  if name=='manuscript':
   if 'B. Likelihood reruns' in text:
    out[name]['probabilistic_table_page']=i+1
    assert i+1<70,'Table drifted after the Results section'
   # Main definitions/results/scope pages plus front matter/conclusion.
   if any(w in text for w in ['For the Tobit alternative','likelihood comparison reused','likelihood comparison used paired','Comparison of Precipitation-Appropriate','alternative-likelihood evidence is limited','An alternative precipitation-appropriate likelihood','B. Likelihood reruns','full CRPS and threshold-weighted CRPS']):render=True
  if name=='Response letter' and (40<=i+1<=44):render=True
  if render:page.get_pixmap(matrix=fitz.Matrix(1,1)).save(str(P/'render'/(name.replace(' ','_')+'_'+str(i+1)+'.png')))
  for block in page.get_text('dict')['blocks']:
   for line in block.get('lines',[]):
    for span in line['spans']:
     txt=span['text']
     if name=='Supplementary' and i>=41 and span['bbox'][1]<790 and txt.strip():
      assert span['color']==0xff0000,(name,i+1,txt,hex(span['color']))
      assert span['bbox'][0]>=65 and span['bbox'][2]<=page.rect.width-65,(i+1,span['bbox'])
     if 'S39' in txt or 'S46' in txt:
      if name=='manuscript':assert span['color']==0xff0000
      if name=='Response letter':assert span['color'] in [0xff0000,0x0000ff]
      colors.append(dict(document=name,page=i+1,color=hex(span['color']),text=txt))
(P/'PDF_CHECK.json').write_text(json.dumps(out,indent=2));(P/'LOCATIONS.json').write_text(json.dumps(loc,indent=2));(P/'COLOR_CHECK.json').write_text(json.dumps(colors,indent=2));print(json.dumps(out,indent=2));print(json.dumps(loc,indent=2))
