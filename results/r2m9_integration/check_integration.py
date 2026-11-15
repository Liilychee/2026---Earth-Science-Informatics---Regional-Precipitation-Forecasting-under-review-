"""Verify local additive integration and numeric transcription against existing evidence. No model/statistical reruns."""
from pathlib import Path
import json,re,csv,hashlib,collections,subprocess
P=Path(__file__).resolve().parent;B=P/'before';M=Path('manuscript.tex').read_text();S=Path('Supplementary.tex').read_text();R=Path('Response letter.tex').read_text();OM=(B/'manuscript.tex').read_text();OS=(B/'Supplementary.tex').read_text();OR=(B/'Response letter.tex').read_text()
code=Path('results/r2m6_integration/check_integration.py').read_text();exec(code[code.index('def args('):code.index('oldex=args(')])
a,b=R.index('% Review ID: R2 M9'),R.index('% Review ID: R2 m1');oa,ob=OR.index('% Review ID: R2 M9'),OR.index('% Review ID: R2 m1');assert R[:a]==OR[:oa] and R[b:]==OR[ob:]
assert args(R[a:b],'ReviewerComment')==args(OR[oa:ob],'ReviewerComment');assert args(R[a:b],'ReviewerComment')[0] in Path('comment.txt').read_text()
old=args(OR,'RevisedExcerpt');new=args(R,'RevisedExcerpt');assert len(old)==103 and len(new)==109;assert collections.Counter(new)-collections.Counter(old)==collections.Counter(args(R[a:b],'RevisedExcerpt'));assert all(canonical(x) in canonical(M) for x in new)
ex=json.loads((P/'FINAL_EXCERPTS.json').read_text());assert len(args(R[a:b],'RevisedExcerpt'))==6
for v in args(R[a:b],'RevisedExcerpt'):assert v in M
# Remove only today's additive blocks and restore the explicit unprotected Code Availability paragraph.
rest=M
def red(v):return '\n{\\color{red}\\hypersetup{linkcolor=red,citecolor=red,filecolor=red,urlcolor=red}\n'+v+'\n\\par}\n'
for v in [ex['methods_search']+'\n\n'+ex['methods_groups'],ex['results']+'\n\n'+ex['cost'],ex['discussion'],ex['limitations']]:assert red(v) in rest;rest=rest.replace(red(v),'',1)
c=json.loads((P/'CODE_AVAILABILITY_CHANGE.json').read_text());assert red(c['new']) in rest;rest=rest.replace(red(c['new']),c['old'],1);assert rest==OM,'Unexpected original manuscript edit'
assert S[:S.index('% R2-M9')].rstrip()==OS[:OS.index(r'\end{document}')].rstrip()
for typ in ['figure','table']:
 pat=r'\\begin\{'+typ+r'\}.*?\\end\{'+typ+r'\}';assert re.findall(pat,M,re.S)==re.findall(pat,OM,re.S)
for path,h in json.loads((P/'PROTECTED_HASHES.json').read_text()).items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==h,path
# Original source bytes are unchanged; derived ledgers are kept distinct.
for e in json.loads((P/'SOURCE_INDEX.json').read_text()):assert hashlib.md5((P/'source'/Path(e['path']).name).read_bytes()).hexdigest()==e['md5']
D={p.name:list(csv.DictReader(p.open())) for p in (P/'source').glob('*.csv')}
for n in ['COST_SUMMARY.csv','CANDIDATE_TABLE.csv','PROSE_DERIVATIONS.csv']:D[n]=list(csv.DictReader((P/n).open()))
cs=json.loads((P/'CELL_INDEX.json').read_text())
for q in cs:
 raw=D[q['file']][q['line']-2][q['field']];assert raw==q['raw'];expected='---' if raw=='' else format(float(raw),('+' if q['sign'] and float(raw)!=0 else '')+'.'+str(q['digits'])+'f');assert expected==q['display'];assert q['display'] in S or q['display'] in M or q['display'] in R[a:b]
# Exact destination rows verify placement, not just numeric membership.
rows=json.loads((P/'ROW_INDEX.json').read_text());counts={}
for label in ['stab:r2m9_search','stab:r2m9_effects']:
 pos=S.index(r'\label{'+label+'}');t=S[pos:S.index(r'\end{longtable}',pos)].split(r'\endfoot')[1];expected=''.join(q['latex'] for q in rows if q['label']==label);assert t.strip()==expected.strip();counts[label]=dict(collections.Counter(q['kind'] for q in rows if q['label']==label))
assert counts['stab:r2m9_search']['candidate']==66 and counts['stab:r2m9_effects']['effect']==53 and counts['stab:r2m9_effects']['interval']==53
sa=Path('build/Supplementary.aux').read_text();ma=Path('build/manuscript.aux').read_text();assert re.search(r'\\newlabel\{stab:r2m9_search\}\{\{S48\}',sa) and re.search(r'\\newlabel\{stab:r2m9_effects\}\{\{S49\}',sa)
for t in [M,S]:
 labs=re.findall(r'(?m)^[^%\n]*?\\label\{([^}]+)\}',t);assert len(labs)==len(set(labs))
assert len(re.findall(r'\\label\{stab:',S))==49
for label in re.findall(r'\\ref\{([^}]+)\}',R[a:b]):
 pref='manuscript-' if label.startswith('manuscript-') else 'supp-' if label.startswith('supp-') else '';aux=sa if pref=='supp-' else ma;assert r'\newlabel{'+label[len(pref):]+'}' in aux,label
assert 'CODE-AVAILABILITY TODO' in M and 'CODE-AVAILABILITY TODO' in R[a:b] and 'not presented as the final code release' in R[a:b]
assert r'\PendingResponse' not in R[a:b] and r'\PendingResponse' in R[b:]
# Only the three authorized task notes and appendix-only checklist/registry records differ.
task=Path('ESI_审稿意见分类_严重程度排序_35项.md').read_text()
for anchor,note in json.loads((P/'TASK_NOTES.json').read_text()).items():
 assert task.count(anchor+note)==1;task=task.replace(anchor+note,anchor,1)
assert task==(B/'ESI_审稿意见分类_严重程度排序_35项.md').read_text()
for n in ['FINAL_REVISION_CHECKLIST.md','SUPPLEMENTARY_TABLE_REGISTRY.md']:assert Path(n).read_text().startswith((B/n).read_text())
assert Path('FINAL_REVISION_CHECKLIST.md').read_text().count('### R2-M9本地科学/论文整合')==1
assert Path('SUPPLEMENTARY_TABLE_REGISTRY.md').read_text().count('### R2-M9追加')==1
result=dict(previous_excerpts_unchanged=103,new_exact_excerpts=6,total_matched=109,all_old_manuscript_text_preserved_except_explicit_unquoted_code_statement=True,all_main_tables_and_figures_unchanged=True,old_S1_S47_source_identical=True,protected_hashes=len(json.loads((P/'PROTECTED_HASHES.json').read_text())),all_other_response_sections_identical=True,numeric_displays_checked=len(cs),table_rows=counts,new_tables=['S48','S49'],source_run_count=117,source_effect_rows=53,new_metrics_calculated=False,code_availability_pending=True,git_publication_performed=False)
(P/'VERIFICATION.json').write_text(json.dumps(result,indent=2));(P/'EXCERPT_INDEX.json').write_text(json.dumps(dict(old=[dict(index=i+1,sha256=hashlib.sha256(v.encode()).hexdigest()) for i,v in enumerate(old)],new=[dict(index=i+1,sha256=hashlib.sha256(v.encode()).hexdigest()) for i,v in enumerate(args(R[a:b],'RevisedExcerpt'))]),indent=2));print(json.dumps(result,indent=2))
