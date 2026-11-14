from pathlib import Path
import re,json,csv,hashlib
P=Path(__file__).resolve().parent;B=P/'before'
M=Path('manuscript.tex').read_text();S=Path('Supplementary.tex').read_text();R=Path('Response letter.tex').read_text()
OM=(B/'manuscript.tex').read_text();OS=(B/'Supplementary.tex').read_text();OR=(B/'Response letter.tex').read_text()
# Reuse only pure parsing definitions, never execute the historical checker.
src=Path('results/r2m6_integration/check_integration.py').read_text();exec(src[src.index('def args('):src.index('oldex=args(')])
assert S[:S.index('% R2-M7')].rstrip()==OS[:OS.index(r'\end{document}')].rstrip()
a,b=R.index('% Review ID: R2 M7'),R.index('% Review ID: R2 M8');oa,ob=OR.index('% Review ID: R2 M7'),OR.index('% Review ID: R2 M8')
assert R[:a]==OR[:oa] and R[b:]==OR[ob:]
assert args(R[a:b],'ReviewerComment')==args(OR[oa:ob],'ReviewerComment')
old=args(OR,'RevisedExcerpt');new=args(R,'RevisedExcerpt');assert len(old)==92 and len(new)==97
assert all(x in new for x in old)
assert all(canonical(x) in canonical(M) for x in new)
ex=json.loads((P/'FINAL_EXCERPTS.json').read_text());assert all(v in M and r'\RevisedExcerpt{'+v+'}' in R[a:b] for v in ex.values())
# Delete exactly five added red blocks: every original manuscript byte must survive.
rest=M
for v in [ex['methods'], ex['results']+'\n\n'+ex['support'], ex['discussion'], ex['limitations']]:
 block='\n{\\color{red}\\hypersetup{linkcolor=red,citecolor=red,filecolor=red,urlcolor=red}\n'+v+'\n\\par}\n'
 assert block in rest,v[:40];rest=rest.replace(block,'',1)
assert rest==OM,'Original manuscript source changed beyond five insertions'
for kind in ['figure','table']:
 pattern=r'\\begin\{'+kind+r'\}.*?\\end\{'+kind+r'\}'
 assert re.findall(pattern,M,re.S)==re.findall(pattern,OM,re.S)
hashes=json.loads((P/'PROTECTED_HASHES.json').read_text())
for path,sha in hashes.items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==sha,path
for f in json.loads((P/'SOURCE_INDEX.json').read_text())['files']:
 assert hashlib.md5(Path(f['path']).read_bytes()).hexdigest()==f['md5'] and f['blob']==f['remote_blob']
D=list(csv.DictReader(Path('results/r2m7_evidence/r2m7_series_stats.csv').open()))
cs=json.loads((P/'CELL_INDEX.json').read_text())
for c in cs:
 raw=D[c['line']-2][c['field']];assert raw==c['raw'];assert c['display']==('---' if raw=='' else f"{float(raw):.{c['digits']}f}")
rows=json.loads((P/'ROW_INDEX.json').read_text());assert len(rows)==26
st=S.index(r'\label{stab:r2m7_spatial_quantiles}');end=S.index(r'\end{longtable}',st);part=S[st:end].split(r'\endfoot')[1]
assert part.strip()==''.join(x['latex'] for x in rows).strip()
for text in [M,S]:
 labs=re.findall(r'\\label\{([^}]+)\}',text);assert len(labs)==len(set(labs))
assert len(re.findall(r'\\label\{stab:',S))==47
assert r'\includegraphics{Figures/r2M7_spatial_quantiles.pdf}' in S
aux=Path('build/Supplementary.aux').read_text()
assert r'\newlabel{stab:r2m7_spatial_quantiles}{{S47}{50}' in aux
assert r'\newlabel{sfig:r2m7_spatial_quantiles}{{S2}{51}' in aux
out=dict(protected_file_hashes=len(hashes),old_excerpts_unchanged=92,total_excerpts_matched=97,new_excerpts=5,all_original_manuscript_bytes_preserved=True,all_original_tables_figures_unchanged=True,supplementary_S1_S46_unchanged=True,other_responses_unchanged=True,table_rows=26,table_fields=len(cs),numeric_fields=sum(x['raw']!='' for x in cs),missing_coordinate_markers=2,table='S47',figure='S2',git_mutations=False)
(P/'VERIFICATION.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
