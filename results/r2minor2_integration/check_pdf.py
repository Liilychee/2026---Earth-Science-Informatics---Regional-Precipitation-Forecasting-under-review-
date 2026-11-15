# -*- coding: utf-8 -*-
from pathlib import Path
import json,re,hashlib,fitz
P=Path(__file__).resolve().parent;order=['Supplementary','manuscript','Response letter'];out=dict(build_order=order,documents={},review_pages={'Supplementary':[57],'manuscript':[22,63,64,66,78],'Response letter':[52,53]},render_dpi=144)
for n in order:
 src=Path(n+'.tex');pdf=Path('build/'+n+'.pdf');log=Path('build/'+n+'.log').read_text();db=Path('build/'+n+'.fdb_latexmk').read_text();m=re.search(r'^  "'+re.escape(str(src))+r'" [\d.]+ (\d+) ([0-9a-f]{32}) ',db,re.M);assert m and m[2]==hashlib.md5(src.read_bytes()).hexdigest() and int(m[1])==src.stat().st_size
 bad=[s for s in log.splitlines() if 'undefined' in s.lower() or 'multiply defined' in s.lower() or 'Overfull \\hbox' in s or 'Float too large' in s or s.startswith('!')];assert not bad,(n,bad)
 d=fitz.open(pdf);review=out['review_pages'][n];fonts=[]
 for pg in review:
  p=d[pg-1];p.get_pixmap(matrix=fitz.Matrix(2,2)).save(str(P/'render'/f'{n.replace(" ","_")}-{pg}.png'))
  sp=[s for b in p.get_text('dict')['blocks'] for l in b.get('lines',[]) for s in l['spans']];fonts.extend(s['size'] for s in sp if s['text'].strip() and s['color']==0xff0000)
  if n=='Response letter':assert any(s['color']==0xff0000 for s in sp) and any(s['color']==0x0000ff for s in sp)
  assert '??' not in p.get_text(),(n,pg)
 if n=='Supplementary':
  t=d[56].get_text();assert 'Table S50' in t and '90% central' in t and '95% central' in t and '1.23' in t
 out['documents'][n]=dict(pages=len(d),source_md5=m[2],pdf_md5=hashlib.md5(pdf.read_bytes()).hexdigest(),source_matches_build=True,blocking_errors=bad,review_pages=review,minimum_reviewed_red_font_pt=min(fonts),warnings=[s for s in log.splitlines() if 'Warning:' in s or 'Underfull' in s or 'Overfull' in s])
out['visual_review']='Actual full-page 144dpi renders inspected at native-page reading scale: S50 all 18 model/subset/level rows and notes; main methods, Table5 vicinity/new results, run identity, two 95% qualifiers; reply pages52–53. No clipping, overlap or unreadable text. Final corrected local Table5 alias and red external S50 links rechecked.'
out['existing_warning_note']='Springer font/bookmark and repeated 1.41457pt vertical-box template warnings retained; no undefined references, duplicate labels, horizontal overflow, oversized float or blocking error.'
(P/'PDF_PAGE_INDEX.json').write_text(json.dumps(out['review_pages'],indent=2));(P/'PDF_CHECK.json').write_text(json.dumps(out,indent=2));print(json.dumps({n:{k:v for k,v in d.items() if k in ['pages','source_matches_build','blocking_errors','minimum_reviewed_red_font_pt']} for n,d in out['documents'].items()},indent=2))
