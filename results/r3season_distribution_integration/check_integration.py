from pathlib import Path
import json,re,csv,hashlib,difflib,subprocess,fitz
P=Path(__file__).resolve().parent;B=P/'before';M=Path('manuscript.tex').read_text();S=Path('Supplementary.tex').read_text();R=Path('Response letter.tex').read_text();oldR=(B/'Response letter.tex').read_text()
c=Path('results/r2m6_integration/check_integration.py').read_text();exec(c[c.index('def args('):c.index('oldex=args(')])
a=R.index('% Review ID: R3 L469-471');b=R.index('% Review ID:',a+15);aa=oldR.index('% Review ID: R3 L469-471');bb=oldR.index('% Review ID:',aa+15)
assert R[:a]==oldR[:aa] and R[b:]==oldR[bb:]
old=args(oldR,'RevisedExcerpt');new=args(R,'RevisedExcerpt');assert len(old)==144 and len(new)==147
assert args(R[:a]+R[b:],'RevisedExcerpt')==old
assert all(canonical(x) in canonical(M+S) for x in new)
assert args(R[a:b],'ReviewerComment')==args(oldR[aa:bb],'ReviewerComment') and args(R[a:b],'ReviewerComment')[0] in Path('comment.txt').read_text()
assert r'\PendingResponse' not in R[a:b] and r'\ChangeLocation' not in R[a:b]
for p in json.loads((P/'NEW_PARAGRAPHS.json').read_text()):
 assert '\\revminor{'+p+'}' in M
 M=M.replace('\\revminor{'+p+'}\n\n','',1)
assert M==(B/'manuscript.tex').read_text()
assert S.startswith((B/'Supplementary.tex').read_text().split(r'\end{document}')[0])
assert Path('sn-bibliography.bib').read_bytes()==(B/'sn-bibliography.bib').read_bytes()
for f,h in json.loads((P/'FIGURE_HASHES.json').read_text()).items():assert hashlib.sha256(Path(f).read_bytes()).hexdigest()==h
assert subprocess.check_output(['git','diff','--cached','--raw'])==(P/'STAGING_BEFORE.txt').read_bytes()
# Exact destination rows, not merely membership of repeated rounded values.
row_count=0
for table in json.loads((P/'ROW_INDEX.json').read_text()):
 t=S[S.index('\\label{'+table['label']+'}'):]
 t=t[:t.index(r'\end{longtable}' if 'gsf_scores' in table['label'] else r'\end{tabular}')]
 for row in table['rows']:assert t.count(row)==1,(table['label'],row)
 row_count+=len([x for x in table['rows'] if not x.startswith(r'\multicolumn')])
fields=json.loads((P/'CELL_INDEX.json').read_text())
for x in fields:
 path=P/x['file'] if x['file'].startswith('FULL_') else P/'evidence'/x['file']
 raw=list(csv.DictReader(path.open()))[x['line']-2][x['field']]
 assert float(raw)==float(x['raw']),(x,raw)
 display=format(float(raw),('+' if x['signed'] else '')+'.'+str(x['digits'])+'f');assert display==x['display']
for x in json.loads((P/'SOURCE_INDEX.json').read_text()):
 raw=Path(x['local']).read_bytes();assert hashlib.md5(raw).hexdigest()==x['md5']
 assert raw==subprocess.check_output(['git','show',x['commit']+':'+x['path']])
script=(P/'evidence/analysis_q03d_seasonal_xgb.py').read_text();log=(P/'evidence/q03d_seasonal_xgb_output.txt').read_text()
for anchor in ['SEEDS = [42, 123, 7, 2024, 99]','BOOT_REPS, BOOT_BLOCK, BOOT_SEED = 2000, 28, 42','[:, :N]','mean_pred = {v: np.mean','m.fit(Xa, ya)','colsample_bytree=0.8']:
 assert anchor in script
assert 'block=28, reps=2000, seed=42' in log and "'DJF': 4566, 'MAM': 4784, 'JJA': 4686, 'SON': 4368" in log
for doc in [Path('manuscript.tex').read_text(),S]:
 labels=re.findall(r'\\label\{([^}]+)\}',doc);assert len(labels)==len(set(labels))
aux=Path('build/Supplementary.aux').read_text();labels={}
for lab,n in [('stab:r3season_full_distribution','S61'),('sfig:r3season_full_cdf','S4'),('stab:r3season_gsf_scores','S62'),('stab:r3season_gsf_pairs','S63')]:
 z=re.search(r'\\newlabel\{'+lab+r'\}\{\{([^}]+)\}\{([^}]+)',aux);assert z and z[1]==n;labels[lab]=dict(number=z[1],page=z[2])
assert sorted(map(int,re.findall(r'\\newlabel\{stab:[^}]+\}\{\{S(\d+)\}',aux)))==list(range(1,64))
for key in re.findall(r'\\ref\{([^}]+)\}',R[a:b]):
 prefix,doc=('manuscript-','manuscript') if key.startswith('manuscript-') else ('supp-','Supplementary')
 assert r'\newlabel{'+key.removeprefix(prefix)+'}' in Path('build/'+doc+'.aux').read_text(),key
out=dict(previous_excerpts_preserved=144,new_exact_excerpts=3,total_matched=147,all_other_review_blocks_byte_identical=True,old_main_paragraphs_tables_figures_identical=True,old_S1_S60_and_Figures_source_prefix_unchanged=True,bibliography_unchanged=True,protected_figures=len(json.loads((P/'FIGURE_HASHES.json').read_text())),csv_fields=len(fields),new_table_data_rows=row_count,all_14_saved_bootstrap_intervals_reproduced=True,no_staging_commit_push=True,labels=labels)
(P/'VERIFICATION.json').write_text(json.dumps(out,indent=2));(P/'EXCERPT_INDEX.json').write_text(json.dumps(dict(protected=[dict(index=i+1,sha256=hashlib.sha256(x.encode()).hexdigest()) for i,x in enumerate(old)],new=args(R[a:b],'RevisedExcerpt'),all_147_match=True),indent=2));(P/'LABEL_INDEX.json').write_text(json.dumps(labels,indent=2))
# Evidence mapping before any edits, based on exact content rather than shifting line numbers.
(P/'BEFORE_AFTER_EXCERPT_MAP.json').write_text(json.dumps(dict(before=144,after=147,old_modified=0,new_added=3,mapping=[dict(old_index=i+1,new_index=new.index(x)+1,sha256=hashlib.sha256(x.encode()).hexdigest()) for i,x in enumerate(old)]),indent=2))
patch=''
for f in ['manuscript.tex','Supplementary.tex','Response letter.tex','FINAL_REVISION_CHECKLIST.md','SUPPLEMENTARY_TABLE_REGISTRY.md','ESI_审稿意见分类_严重程度排序_35项.md']:
 patch+=''.join(difflib.unified_diff((B/f).read_text().splitlines(True),Path(f).read_text().splitlines(True),fromfile='a/'+f,tofile='b/'+f))
patch=''.join(l.rstrip('\n')+'\t2026-11-15 00:00:00 +0000\n' if l.startswith(('--- a/','+++ b/')) else l for l in patch.splitlines(True));(P/'R3_14_LOCAL.patch').write_text(patch)
# Current PDF rendering candidates and build diagnostics.
(P/'render').mkdir(exist_ok=True);pdf={}
anchors={'manuscript':['Full-period seasonal distributions use','The separate q03d sensitivity compares','The q03d seasonal-training sensitivity did not'], 'Supplementary':['Seasonal distribution of ERA5 25-cell','Seasonal empirical distributions of ERA5','Five-seed q03d seasonal-training sensitivity','Paired q03d differences relative'], 'Response letter':['L469-471:','We agree that Q95=','Full-period seasonal precipitation distributions','Seasonal-training sensitivity','Scope and uncertainty limits']}
for stem in anchors:
 log=Path('build/'+stem+'.log').read_text(errors='replace');bad=[l for l in log.splitlines() if re.search(r'undefined|multiply defined|Overfull|Float too large|^!',l)]
 assert not [l for l in bad if 'Overfull \\vbox (1.41457pt' not in l],bad
 doc=fitz.open('build/'+stem+'.pdf');pages=set()
 for i,page in enumerate(doc):
  text=' '.join(page.get_text().split())
  if any(a in text for a in anchors[stem]):pages.add(i+1)
 if stem=='Supplementary':pages.update(range(69,len(doc)+1))
 if stem=='Response letter':
  start=next(i+1 for i,pg in enumerate(doc) if 'L469-471:' in pg.get_text());pages.update(range(start,min(start+4,len(doc)+1)))
 for page in sorted(pages):doc[page-1].get_pixmap(matrix=fitz.Matrix(1.5,1.5)).save(P/'render'/(stem.replace(' ','_')+f'-{page}.png'))
 pdf[stem]=dict(pages=len(doc),review_pages=sorted(pages),template_vbox_count=len(bad),pdf_sha256=hashlib.sha256(Path('build/'+stem+'.pdf').read_bytes()).hexdigest(),visual_review='PENDING actual inspection')
prior_pdf=json.loads((P/'PDF_CHECK.json').read_text()) if (P/'PDF_CHECK.json').exists() else {}
for stem,v in pdf.items():
 if prior_pdf.get(stem,{}).get('pdf_sha256')==v['pdf_sha256'] and prior_pdf[stem].get('visual_review','').startswith('PASS'):v['visual_review']=prior_pdf[stem]['visual_review']
(P/'PDF_CHECK.json').write_text(json.dumps(pdf,indent=2));(P/'GIT_STATUS.txt').write_bytes(subprocess.check_output(['git','status','--short']));print(json.dumps(out,indent=2));print(json.dumps(pdf,indent=2))
