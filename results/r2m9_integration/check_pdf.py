"""Final PDF/build metadata and actual rendered-page audit; does not author or recompile PDFs."""
from pathlib import Path
import json,re,hashlib,fitz
P=Path(__file__).resolve().parent;idx=json.loads((P/'PDF_PAGE_INDEX.json').read_text());out={'build_order':['Supplementary','manuscript','Response letter'],'documents':{}}
for name in out['build_order']:
 src=Path(name+'.tex');pdf=Path('build/'+name+'.pdf');db=Path('build/'+name+'.fdb_latexmk').read_text();log=Path('build/'+name+'.log').read_text();m=re.search(r'^  "'+re.escape(str(src))+r'" [\d.]+ (\d+) ([0-9a-f]{32}) ',db,re.M);assert m and m[2]==hashlib.md5(src.read_bytes()).hexdigest() and int(m[1])==src.stat().st_size
 bad=[s for s in log.splitlines() if 'undefined' in s.lower() or 'multiply defined' in s.lower() or 'Overfull \\hbox' in s or 'Float too large' in s or s.startswith('!')];assert not bad,bad
 warnings=[s for s in log.splitlines() if 'Warning:' in s or 'Overfull' in s or 'Underfull' in s]
 d=fitz.open(pdf);pages=idx[name]['review_pages'];colors={}
 for n in pages:
  page=d[n-1];spans=[s for b in page.get_text('dict')['blocks'] for l in b.get('lines',[]) for s in l['spans']];colors[n]=sorted(set(f"{s['color']:06x}" for s in spans));assert (P/'render'/f'{name.replace(" ","_")}-{n}.png').exists()
  assert all(s['bbox'][0]>=-1 and s['bbox'][2]<=page.rect.width+1 for s in spans)
  target=P/'render144';target.mkdir(exist_ok=True);page.get_pixmap(matrix=fitz.Matrix(2,2)).save(str(target/f'{name.replace(" ","_")}-{n}.png'))
 out['documents'][name]=dict(page_count=len(d),pdf_md5=hashlib.md5(pdf.read_bytes()).hexdigest(),source_md5=m[2],source_matches_final_build=True,review_pages=pages,overall_review_dpi=72,legibility_render_dpi=144,colors_by_page=colors,blocking_log_errors=bad,warnings=warnings)
sa=Path('build/Supplementary.aux').read_text();assert r'\newlabel{stab:r2m9_search}{{S48}{52}' in sa and r'\newlabel{stab:r2m9_effects}{{S49}{54}' in sa
sup=fitz.open('build/Supplementary.pdf');assert 'Table S48' in sup[51].get_text() and 'Table S49' in sup[53].get_text()
main=fitz.open('build/manuscript.pdf');assert 'CODE-AVAILABILITY TODO' in main[-1].get_text();resp=fitz.open('build/Response letter.pdf');assert any('CODE-AVAILABILITY TODO' in resp[n-1].get_text() for n in idx['Response letter']['review_pages'])
out.update(table_S48_pages=[52,53],table_S49_pages=[54,55,56],new_page_actual_visual_review='All19 listed pages inspected at native72dpi scale;144dpi copies retained for legibility. Table continuations have actual repeated headings and E/I panel keys. Red manuscript/captions/response and blue excerpts checked. No clipping, overlap or unresolved references.',new_supplementary_figures=0,existing_warning_note='Existing template font/bookmark warnings and1.41457pt vbox remain; full per-document warning/underfull lines retained. Initial new URL hbox overflow was fixed locally with scoped URL breaks; final logs contain no horizontal overflow or blocking errors.',code_publication_finalization='PENDING and visible in manuscript/response; no final release or full documentation claimed')
(P/'PDF_CHECK.json').write_text(json.dumps(out,indent=2));print(json.dumps({n:dict(pages=x['page_count'],review_pages=x['review_pages'],warning_lines=len(x['warnings'])) for n,x in out['documents'].items()},indent=2))
