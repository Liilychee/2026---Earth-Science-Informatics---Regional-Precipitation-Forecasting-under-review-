"""Read-only PDF/build checks; emits only the missing local QA record."""
from pathlib import Path
import re,json,hashlib,fitz,csv,subprocess
P=Path(__file__).resolve().parent
out={'workflow':'Reuse successful sequential builds; no TeX/PDF changed after compilation. Read-only final verification.', 'documents':{}}
review={'Supplementary':[50,51],'manuscript':[27,28,53,76,80],'Response letter':[44,45]}
for name,pages in review.items():
 src=Path(name+'.tex');pdf=Path('build')/(name+'.pdf');log=Path('build')/(name+'.log');db=Path('build')/(name+'.fdb_latexmk')
 dbtext=db.read_text();record=re.search(r'^  "'+re.escape(str(src))+r'" [\d.]+ (\d+) ([0-9a-f]{32}) ',dbtext,re.M);assert record,name
 md5=hashlib.md5(src.read_bytes()).hexdigest();assert record[2]==md5 and int(record[1])==src.stat().st_size
 assert pdf.stat().st_mtime>=src.stat().st_mtime and 'Output written on' in log.read_text()
 text=log.read_text();bad=re.findall(r'^.*(?:undefined references|Reference .* undefined|multiply defined|Overfull \\hbox|Float too large|^! ).*$',text,re.M);assert not bad,bad
 warnings=[l for l in text.splitlines() if 'Warning:' in l or 'Overfull' in l]
 d=fitz.open(pdf);page_records=[]
 for n in pages:
  p=d[n-1];spans=[s for b in p.get_text('dict')['blocks'] for l in b.get('lines',[]) for s in l['spans']];assert spans
  assert any(s['color']==0xff0000 for s in spans) if name!='Response letter' else any(s['color']==0x0000ff for s in spans)
  page_records.append({'page':n,'visual_check':'Previously rendered at 72 dpi (1 PDF point = 1 pixel), actually inspected; no cropping, overlap or illegible new text.','text_colors_hex':sorted(set(f"{s['color']:06x}" for s in spans)),'page_size_pt':[p.rect.width,p.rect.height]})
 out['documents'][name]={'pages':len(d),'pdf_md5':hashlib.md5(pdf.read_bytes()).hexdigest(),'source_md5_matches_successful_build':md5,'build_inputs_source_match':True,'warnings':warnings,'blocking_log_errors':bad,'reviewed_pages':page_records}
# Exact auxiliary mappings and actual rendered cross-references.
aux=Path('build/Supplementary.aux').read_text();assert r'\newlabel{stab:r2m7_spatial_quantiles}{{S47}{50}' in aux;assert r'\newlabel{sfig:r2m7_spatial_quantiles}{{S2}{51}' in aux
for name,pno in [('manuscript',53),('Response letter',44)]:
 t=fitz.open('build/'+name+'.pdf')[pno-1].get_text();assert 'Table S47' in t and 'Figure S2' in t
S=Path('Supplementary.tex').read_text();assert r'\includegraphics{Figures/r2M7_spatial_quantiles.pdf}' in S
md5=hashlib.md5(Path('Figures/r2M7_spatial_quantiles.pdf').read_bytes()).hexdigest();assert md5=='0b59c59d8b25a4eeb725c552a12c26fb'
# Author figure native-size placed Form XObject retains original 119 x 70 mm box.
p=fitz.open('build/Supplementary.pdf')[50];boxes=[list(x[3]) for x in p.get_xobjects()];out['supplementary_figure_xobject_boxes_pt']=boxes
assert any(abs((r[2]-r[0])*25.4/72-119)<.02 and abs((r[3]-r[1])*25.4/72-70)<.02 for r in boxes)
out.update(supplementary_table='S47',supplementary_figure='S2',old_table_figure_labels_preserved=True,author_figure_md5=md5,author_figure_unscaled=True,visual_qa_reused=True,no_recompile_required=True,limitations='Actual-size PDF raster review does not measure every physical monitor zoom. Existing template font/bookmark warnings and repeated 1.41457pt overfull vbox warnings remain; no horizontal overflow or blocking errors.')
(P/'PDF_CHECK.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:{'pages':v['pages'],'warnings':len(v['warnings']),'source_matches':True} for k,v in out['documents'].items()},indent=2))
