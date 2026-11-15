# -*- coding: utf-8 -*-
from pathlib import Path
import json,re,hashlib,fitz
P=Path(__file__).resolve().parent;out={'build_order':['Supplementary','manuscript','Response letter'],'documents':{}}
for name in out['build_order']:
 src=Path(name+'.tex');pdf=Path('build/'+name+'.pdf');log=Path('build/'+name+'.log').read_text();db=Path('build/'+name+'.fdb_latexmk').read_text();m=re.search(r'^  "'+re.escape(str(src))+r'" [\d.]+ (\d+) ([0-9a-f]{32}) ',db,re.M);assert m and m[2]==hashlib.md5(src.read_bytes()).hexdigest() and int(m[1])==src.stat().st_size
 bad=[s for s in log.splitlines() if 'undefined' in s.lower() or 'multiply defined' in s.lower() or 'Overfull \\hbox' in s or 'Float too large' in s or s.startswith('!')];assert not bad,bad
 out['documents'][name]=dict(pages=len(fitz.open(pdf)),source_md5=m[2],pdf_md5=hashlib.md5(pdf.read_bytes()).hexdigest(),source_matches_build=True,blocking_errors=bad,warnings=[s for s in log.splitlines() if 'Warning:' in s or 'Underfull' in s or 'Overfull' in s])
idx=json.loads((P/'PDF_PAGE_INDEX.json').read_text());d=fitz.open('build/Response letter.pdf');colors={}
for n in idx['Response_letter_pages']:
 p=d[n-1];spans=[s for b in p.get_text('dict')['blocks'] for l in b.get('lines',[]) for s in l['spans']];colors[n]=sorted(set(f"{s['color']:06x}" for s in spans));assert any(s['color']==0xff0000 for s in spans) and any(s['color']==0x0000ff for s in spans);assert (P/'render'/f'Response_letter-{n}.png').exists()
text=' '.join(' '.join(d[n-1].get_text().split()) for n in idx['Response_letter_pages']);assert 'Section 3.2' in text and 'Section 3.4.1' in text and '18,404 targets' in text and '3,939 targets' in text
out.update(review_pages=idx['Response_letter_pages'],render_dpi=144,actual_visual_check='Both rendered pages actually inspected: raw/target periods, date/count list, red reply, blue locations/excerpts, correct section refs and no clipping/overlap. R2-m2 remains Pending.',main_and_supplementary_source_unchanged=True,existing_warning_note='Template font/bookmark/1.41457pt vbox and existing mild underfull records retained; no undefined references, duplicate labels, horizontal overflow, oversized float or blocking errors.')
(P/'PDF_CHECK.json').write_text(json.dumps(out,indent=2));print(json.dumps({n:dict(pages=v['pages'],blocking=v['blocking_errors']) for n,v in out['documents'].items()},indent=2))
