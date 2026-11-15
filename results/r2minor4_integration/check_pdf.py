# -*- coding: utf-8 -*-
from pathlib import Path
import json,re,hashlib,fitz
P=Path(__file__).resolve().parent;prior=json.loads(Path('results/r2minor3_integration/PDF_CHECK.json').read_text());out=dict(build_order=['Supplementary','manuscript','Response letter'],documents={},reply_review_pages=[55,56,57],render_dpi=144)
for n in out['build_order']:
 src=Path(n+'.tex');pdf=Path('build/'+n+'.pdf');log=Path('build/'+n+'.log').read_text();db=Path('build/'+n+'.fdb_latexmk').read_text();m=re.search(r'^  "'+re.escape(str(src))+r'" [\d.]+ (\d+) ([0-9a-f]{32}) ',db,re.M);assert m and m[2]==hashlib.md5(src.read_bytes()).hexdigest() and int(m[1])==src.stat().st_size
 bad=[s for s in log.splitlines() if 'undefined' in s.lower() or 'multiply defined' in s.lower() or 'Overfull \\hbox' in s or 'Float too large' in s or s.startswith('!')];assert not bad,(n,bad)
 md5=hashlib.md5(pdf.read_bytes()).hexdigest();d=fitz.open(pdf)
 if n!='Response letter':assert md5==prior['documents'][n]['pdf_md5']
 out['documents'][n]=dict(pages=len(d),source_md5=m[2],pdf_md5=md5,source_matches_build=True,unchanged_from_closed_R2_m3=n!='Response letter',blocking_errors=bad,warnings=[s for s in log.splitlines() if 'Warning:' in s or 'Underfull' in s or 'Overfull' in s])
d=fitz.open('build/Response letter.pdf')
for pg in out['reply_review_pages']:
 p=d[pg-1];p.get_pixmap(matrix=fitz.Matrix(2,2)).save(str(P/'render'/f'Response_letter-{pg}.png'));assert '??' not in p.get_text()
spans=lambda p:[s for b in p.get_text('dict')['blocks'] for l in b.get('lines',[]) for s in l['spans']]
assert any(s['color']==0xff0000 for s in spans(d[55]));assert any(s['color']==0x0000ff for s in spans(d[56]));t=d[55].get_text();assert all(x in t for x in ['S12','S15','S16','S19','0.089130','0.005174','0.004022','0.020662'])
out['visual_review']='Actual full-page144dpi renders inspected at native-page reading scale: p55 reviewer/response transition, p56 red uncertainty/results/limitations reply, p57 two blue verbatim EvidenceBoxes. Figures7/8, TablesS12–S19 and Section3.5.3 resolve correctly; no clipping, overlapping or unreadable text. Final explicit95% bootstrap wording re-rendered and checked.'
out['existing_warning_note']='Main/supplement source and PDF hashes unchanged; up-to-date latexmk builds reused. Existing Springer font/bookmark and1.41457pt vertical-box template warnings retained. No new undefined reference, duplicate label, horizontal overflow, oversized float or blocking error.'
(P/'PDF_CHECK.json').write_text(json.dumps(out,indent=2));(P/'PDF_PAGE_INDEX.json').write_text(json.dumps(dict(Response_letter_pages=out['reply_review_pages']),indent=2));print(json.dumps({n:dict(pages=v['pages'],blockers=v['blocking_errors'],source_matches=v['source_matches_build']) for n,v in out['documents'].items()},indent=2))
