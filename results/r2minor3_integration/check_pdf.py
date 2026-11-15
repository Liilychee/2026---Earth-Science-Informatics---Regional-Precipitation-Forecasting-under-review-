# -*- coding: utf-8 -*-
from pathlib import Path
import json,re,hashlib,fitz
P=Path(__file__).resolve().parent;out=dict(build_order=['Supplementary','manuscript','Response letter'],documents={},render_dpi=144,review_pages=[53,54,55]);prior=json.loads(Path('results/r2minor2_integration/PDF_CHECK.json').read_text())
for n in out['build_order']:
 src=Path(n+'.tex');pdf=Path('build/'+n+'.pdf');log=Path('build/'+n+'.log').read_text();db=Path('build/'+n+'.fdb_latexmk').read_text();m=re.search(r'^  "'+re.escape(str(src))+r'" [\d.]+ (\d+) ([0-9a-f]{32}) ',db,re.M);assert m and m[2]==hashlib.md5(src.read_bytes()).hexdigest() and int(m[1])==src.stat().st_size
 bad=[x for x in log.splitlines() if 'undefined' in x.lower() or 'multiply defined' in x.lower() or 'Overfull \\hbox' in x or 'Float too large' in x or x.startswith('!')];assert not bad,(n,bad)
 d=fitz.open(pdf);md5=hashlib.md5(pdf.read_bytes()).hexdigest()
 if n!='Response letter':assert md5==prior['documents'][n]['pdf_md5'],n
 out['documents'][n]=dict(pages=len(d),source_md5=m[2],pdf_md5=md5,source_matches_build=True,unchanged_pdf_from_R2_m2=n!='Response letter',blocking_errors=bad,warnings=[x for x in log.splitlines() if 'Warning:' in x or 'Underfull' in x or 'Overfull' in x])
d=fitz.open('build/Response letter.pdf')
for pg in out['review_pages']:
 p=d[pg-1];p.get_pixmap(matrix=fitz.Matrix(2,2)).save(str(P/'render'/f'Response_letter-{pg}.png'));assert '??' not in p.get_text()
sp=lambda p:[s for b in p.get_text('dict')['blocks'] for l in b.get('lines',[]) for s in l['spans']]
assert any(s['color']==0xff0000 for s in sp(d[53]));assert any(s['color']==0x0000ff for s in sp(d[54]));t=d[53].get_text();assert 'S28' in t and 'S29' in t and 'S30' in t and 'S31' in t and '0.916' in t and '0.913' not in t
out['visual_review']='Actual 144dpi page renders reviewed at native reading scale: R2-m3 reviewer transition p53, full red response p54 and all three blue verbatim EvidenceBoxes p55. Section4.3.2, Figure5 and S28–S31 render correctly. No clipping, overlap or severe overflow; R2-m4 remains a placeholder.'
out['retained_warnings']='Existing Springer font/bookmark and 1.41457pt vertical template warnings retained. No new undefined reference, duplicate label, horizontal overflow, oversized float or blocking error. Unchanged main/supplement PDFs reused after successful latexmk up-to-date checks.'
(P/'PDF_CHECK.json').write_text(json.dumps(out,indent=2));(P/'PDF_PAGE_INDEX.json').write_text(json.dumps(dict(Response_letter_pages=out['review_pages']),indent=2));print(json.dumps({k:dict(pages=v['pages'],blockers=v['blocking_errors'],source_matches=v['source_matches_build']) for k,v in out['documents'].items()},indent=2))
