"""Read final successful PDF build metadata and rendered page properties; no PDF authoring."""
from pathlib import Path
import json,re,hashlib,fitz,collections
P=Path(__file__).resolve().parent;old=json.loads(Path('results/r2m7_integration/PDF_CHECK.json').read_text())['documents'];out={'build_order':['Supplementary','manuscript','Response letter'],'documents':{}}
for name in out['build_order']:
 src=Path(name+'.tex');pdf=Path('build/'+name+'.pdf');db=Path('build/'+name+'.fdb_latexmk').read_text();log=Path('build/'+name+'.log').read_text();m=re.search(r'^  "'+re.escape(str(src))+r'" [\d.]+ (\d+) ([0-9a-f]{32}) ',db,re.M);assert m and m[2]==hashlib.md5(src.read_bytes()).hexdigest() and int(m[1])==src.stat().st_size
 bad=[l for l in log.splitlines() if 'undefined' in l.lower() or 'multiply defined' in l.lower() or 'Overfull \\hbox' in l or 'Float too large' in l or l.startswith('!')];assert not bad,bad
 warnings=[l for l in log.splitlines() if 'Warning:' in l or 'Overfull' in l];added=list((collections.Counter(warnings)-collections.Counter(old[name]['warnings'])).elements());assert not added,added
 d=fitz.open(pdf);out['documents'][name]=dict(pages=len(d),pdf_md5=hashlib.md5(pdf.read_bytes()).hexdigest(),source_md5=m[2],source_matches_build=True,warnings=warnings,new_warnings=added,blocking_errors=bad)
d=fitz.open('build/Response letter.pdf');review=json.loads((P/'PDF_PAGE_INDEX.json').read_text())['Response_letter_pages'];colors={}
for page in review:
 p=d[page-1];spans=[s for b in p.get_text('dict')['blocks'] for l in b.get('lines',[]) for s in l['spans']];colors[page]=sorted(set(f"{s['color']:06x}" for s in spans));assert any(s['color'] in [0xff0000,0x0000ff] for s in spans)
 assert (P/'render'/f'Response_letter-{page}.png').exists()
t=' '.join(d[i-1].get_text() for i in review);assert 'Figures 7 and 8' in t and 'S12–S22' in t and 'Section 3.5.3' in t
out.update(actual_render_review_pages=review,render_dpi=144,actual_visual_review='All four rendered pages inspected: complete red response, blue locations/quoted boxes, automatic section/figure/table references, no cropping/overlap or unreadable text.',colors_by_page=colors,manuscript_and_supplementary_no_source_changes=True,current_figures=[7,8],current_supplementary=['S12','S22'],existing_warning_note='Existing manuscript template font/bookmark and repeated1.41457pt vbox warnings retained; no new warnings. No horizontal overflow, undefined refs, duplicate labels, float-limit or blocking errors.')
(P/'PDF_CHECK.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:dict(pages=v['pages'],new_warnings=v['new_warnings']) for k,v in out['documents'].items()},indent=2))
