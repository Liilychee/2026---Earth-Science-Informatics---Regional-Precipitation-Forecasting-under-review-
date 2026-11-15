# -*- coding: utf-8 -*-
from pathlib import Path
import re,json,hashlib,csv,difflib
P=Path(__file__).resolve().parent;B=P/'before'
code=Path('results/r2m6_integration/check_integration.py').read_text();exec(code[code.index('def args('):code.index('oldex=args(')])
M=(B/'manuscript.tex').read_text();S=(B/'Supplementary.tex').read_text();R=(B/'Response letter.tex').read_text();old=args(R,'RevisedExcerpt');assert len(old)==112
changes=[('near-nominal overall coverage, but did not improve','near-nominal overall coverage of the nominal 95\\% interval, but did not improve'),('This result shows that near-nominal coverage over the complete test distribution','This result shows that near-nominal 95\\% coverage over the complete test distribution')]
mapout=[]
for a,b in changes:
 assert M.count(a)==1
 para=next(x for x in M.split('\n\n') if a in x);refs=[i+1 for i,t in enumerate(old) if a in t or canonical(t) in canonical(para)];assert not refs,refs
 new=para.replace(a,b);mapout.append(dict(anchor=a,before=para,after=new,old_excerpt_indices=refs,before_sha256=hashlib.sha256(para.encode()).hexdigest(),after_sha256=hashlib.sha256(new.encode()).hexdigest()))
 # Restrict red markup to the inserted words; paragraph itself may already be inside a red group.
 if a.startswith('near-'):b=b.replace('of the nominal 95\\% interval',r'\textcolor{red}{of the nominal 95\% interval}')
 else:b=b.replace('95\\% coverage',r'\textcolor{red}{95\%} coverage')
 M=M.replace(a,b)
method=r'''For the additional Gaussian interval diagnostics, central 90\% and 95\% intervals use standard-normal multipliers $z=1.645$ and $z=1.960$, respectively (rounded here; the archived calculations use full-precision quantiles). Prediction-interval coverage probability (PICP) is the proportion of observations within the interval, and mean prediction-interval width (MPIW) is the mean upper minus lower bound in mm\,h$^{-1}$. We report the negative-lower-bound proportion at both levels, together with diagnostic coverage for the observed wet ($y\geq0.1$~mm\,h$^{-1}$) and upper-tail ($y\geq0.574048$~mm\,h$^{-1}$, using training Q95) subsets. These diagnostics use the separate q14 five-seed Gaussian reruns summarised in Supplementary Table~\ref{supp-stab:r2minor2_intervals}.'''
anchor=r'\label{eq:prediction_interval_95}'+'\n'+r'\end{equation}';assert M.count(anchor)==1
M=M.replace(anchor,anchor+'\n\n{\\color{red}\\hypersetup{linkcolor=red}\n'+method+'\n\\par}')
result=r'''Supplementary Table~\ref{supp-stab:r2minor2_intervals} reports both interval levels for the separate q14 five-seed Gaussian reruns on the same 3,939 test targets. Across the three models, mean all-sample coverage was 0.9456--0.9464 for the nominal 90\% interval and 0.9560--0.9571 for the nominal 95\% interval. The corresponding widths were 0.6526--0.6705 and 0.7776--0.7989~mm\,h$^{-1}$. For the 854 wet targets, coverage was 0.7546--0.7571 and 0.8002--0.8042, respectively; for the 238 upper-tail targets, it was 0.3958--0.4101 and 0.4941--0.5042. At both nominal levels, every lower bound was negative and every uncovered observation exceeded the upper bound. Thus, near-nominal overall 95\% coverage and above-nominal overall 90\% coverage conceal marked wet and upper-tail undercoverage. These are descriptive conditional diagnostics, not evidence of a significant model ranking.'''
identity=r'''These reruns are the A2 run set in Table~\ref{tab:probabilistic_results}, rather than the complete original A1 run set. The A2 Probabilistic BiLSTM-Attention and the B Gaussian have identical saved test targets and predictive means for each of the five seeds, with small differences in the saved standard-deviation parameters (at most $1.23\times10^{-7}$~mm\,h$^{-1}$). Their agreement therefore does not constitute independent prediction evidence, despite the separate run records.'''
start=M.index(r'\label{tab:probabilistic_results}');end=M.index(r'\end{table}',start)+len(r'\end{table}');M=M[:end]+'\n\n{\\color{red}\\hypersetup{linkcolor=red}\n'+result+'\n\n'+identity+'\n\\par}\n'+M[end:]
(P/'EXCERPT_PROTECTION_MAP.json').write_text(json.dumps(dict(old_count=112,old=[dict(index=i+1,sha256=hashlib.sha256(t.encode()).hexdigest(),present_before=canonical(t) in canonical((B/'manuscript.tex').read_text())) for i,t in enumerate(old)],modified_paragraphs=mapout,affected_old_evidence_boxes=0),indent=2))
# Preserve every existing supplement byte before its terminal document command.
rows=list(csv.DictReader((P/'evidence/q16_interval_summary.csv').open()));rows=[r for r in rows if r['source']=='q14_rerun_5seed'];assert len(rows)==9
names={'bulstm':'BU-LSTM','bulstm_attn':'BU-LSTM-Attention','prob_bilstm_attn':'Prob. BiLSTM-Attn.'};sets={'all':'All (3,939)','wet>=0.1':'Wet (854)','upper>=Q95':'Upper (238)'};cells=[]
body=[]
for lev in [90,95]:
 body.append(r'\multicolumn{6}{l}{\textbf{'+str(lev)+r'\% central intervals}}\\\hline')
 for model in names:
  for sub in sets:
   r=next(x for x in rows if x['model']==model and x['subset']==sub);parts=[names[model],sets[sub]]
   for f in ['PICP','MPIW','above','neglow']:
    vals=[]
    for stat in ['mean','std']:
     field=f+str(lev)+'_'+stat;v=float(r[field]);s=f'{v:.4f}';vals.append(s);cells.append(dict(model=model,subset=sub,level=lev,field=field,source='results/metrics/q16_interval_summary.csv',csv_line=rows.index(r)+2,raw=r[field],display=s))
    parts.append(r'\shortstack{$'+vals[0]+r'$\\$\pm'+vals[1]+r'$}')
   body.append(' & '.join(parts)+r'\\')
caption=r'''Central 90\% and 95\% Gaussian prediction intervals from the q14 reruns (q16 diagnostics), reported as five-seed mean $\pm$ sample SD. Cov is PICP; Width is MPIW (mm\,h$^{-1}$); Above is the proportion of observations exceeding the upper bound; NegLB is the proportion of negative lower bounds. All other quantities are proportions.'''
notes=r'''The three models use seeds 42, 123, 7, 2024 and 99. All has 3,939 test targets; Wet is $y\geq0.1$~mm\,h$^{-1}$ ($n=854$); Upper is $y\geq$training Q95 $=0.574048$~mm\,h$^{-1}$ ($n=238$). The code uses $z=1.6448536269514722$ and $1.959963984540054$. At both levels, the below-lower-bound proportion is $0\pm0$ for every model and subset, so all misses are above the upper bound. Conditional subset coverage is descriptive and does not establish significant model rankings. A1 in main Table~5 retains the original runs; the q14 A2 reruns are not the complete A1 run set. A2 Probabilistic BiLSTM-Attention and the q11 B Gaussian have identical saved targets and predictive means for all five seeds, with saved standard-deviation differences no larger than $1.23\times10^{-7}$~mm\,h$^{-1}$; their matching results are not independent prediction evidence. No original Table~5 value is replaced.'''
# Cross-document label for Table5 rather than manual number: Supplementary does not currently import main; use neutral panel names.
notes=notes.replace('A1 in main Table~5 retains','The main-table A1 panel retains').replace('No original Table~5 value is replaced.','No original main-table value is replaced.')
table='\n% R2-m2: separate q14/q16 interval diagnostics; original tables unchanged.\n{\\color{red}\n\\section*{Additional Gaussian interval diagnostics}\n}'+r'''
\begin{revisionlongtable}
\begin{longtable}{@{}llcccc@{}}
\caption{'''+caption+r'''}\label{stab:r2minor2_intervals}\\
\hline
\textbf{Model} & \textbf{Subset ($n$)} & \textbf{Cov} & \textbf{Width} & \textbf{Above} & \textbf{NegLB}\\\hline
\endfirsthead
\multicolumn{6}{l}{\tablename\ \thetable\ (continued)}\\\hline
\textbf{Model} & \textbf{Subset ($n$)} & \textbf{Cov} & \textbf{Width} & \textbf{Above} & \textbf{NegLB}\\\hline
\endhead
\hline\endfoot
'''+ '\n'.join(body)+r'''
\end{longtable}
\end{revisionlongtable}
{\color{red}\small '''+notes+'\n\\par}\n'
assert S.count(r'\end{document}')==1;S=S.replace(r'\end{document}',table+'\n'+r'\end{document}')
response=r'''We now report the 90\% and 95\% coverage and interval widths side by side in Supplementary Table~\ref{supp-stab:r2minor2_intervals}, retaining Table~\ref{manuscript-tab:probabilistic_results} unchanged. The table uses the archived q16 diagnostics of 15 q14 prediction files: three Gaussian models, each with seeds 42, 123, 7, 2024 and 99, on the same 3,939 test targets. It gives five-seed means and sample SDs for coverage, width, above-upper-bound frequency and negative-lower-bound frequency, separately for all targets, wet targets and training-Q95 upper-tail targets. No model was retrained for this addition.

Section~\ref{manuscript-sec:probabilistic_output} specifies both interval levels and the PICP/MPIW definitions. Section~\ref{manuscript-sec:probabilistic_results} reports all-sample coverage of 0.9456--0.9464 at 90\% and 0.9560--0.9571 at 95\%, with widths of 0.6526--0.6705 and 0.7776--0.7989~mm\,h$^{-1}$, respectively. The rerun 95\% results are broadly consistent with the original A1 results, without being substituted for them. Wet and upper-tail undercoverage remains substantial at both levels. Every lower bound is negative and all misses are above the upper bound. We have restricted the two relevant near-nominal-coverage statements to the 95\% level; these results do not establish a causal explanation for undercoverage or significant differences between the models.

We distinguish the original A1 runs, q14 A2 reruns and q11 B likelihood comparison. In particular, A2 Probabilistic BiLSTM-Attention and B Gaussian have identical saved targets and predictive means for each seed, with only small differences in saved standard-deviation parameters; they are not independent prediction evidence. The table note states this overlap explicitly. Final page and line numbers will be added after the full revision is assembled.'''
a,b=R.index('% Review ID: R2 m2'),R.index('% Review ID: R2 m3');block=R[a:b];assert block.count(r'\PendingResponse')==1
newex={'methods':method,'results':result,'identity':identity};boxes='\n\n'.join(r'\EvidenceBox{'+title+r'}{'+'\n'+r'\RevisedExcerpt{'+newex[k]+'}\n}' for k,title in [('methods',r'Both interval levels (Section~\ref{manuscript-sec:probabilistic_output}; final page and line numbers pending)'),('results',r'Coverage and width results (Section~\ref{manuscript-sec:probabilistic_results}; final page and line numbers pending)'),('identity',r'Run-set overlap (Section~\ref{manuscript-sec:probabilistic_results}; final page and line numbers pending)')])
block=block.replace('\\PendingResponse\n\n\\ChangeLocation',r'\AuthorResponse{'+response+'}\n\n'+boxes);R=R[:a]+block+R[b:]
for t in newex.values():assert t in M
for f,t in [('manuscript.tex',M),('Supplementary.tex',S),('Response letter.tex',R)]:Path(f).write_text(t)
(P/'FINAL_EXCERPTS.json').write_text(json.dumps(newex,indent=2));(P/'CELL_INDEX.json').write_text(json.dumps(cells,indent=2));(P/'TABLE_GENERATED.tex').write_text(table)
# Scoped status notes, no shared task closure.
f='ESI_审稿意见分类_严重程度排序_35项.md';s=Path(f).read_text();anchor='### 16. 概率区间评估指标不完整';note='\n\n**R2-m2局部整合（2026-11-15，待作者审核，未Git归档）**：采用方案(b)，Table 5不变，q14/q16五种子90/95%完整诊断另入自动编号补充表`stab:r2minor2_intervals`（S50）；Methods、§4.4及两处95%限定和正式回复已同步。任务16其他共享事项仍Pending；R2-m3未启动。M9保持SCIENTIFIC_INTEGRATION_COMPLETE — FINAL_REPOSITORY_DOCUMENTATION_PENDING，不整体关闭。\n';assert s.count(anchor)==1;s=s.replace(anchor,anchor+note,1);Path(f).write_text(s)
f='FINAL_REVISION_CHECKLIST.md';s=Path(f).read_text();s+='\n\n### R2-m2 / 任务16局部（2026-11-15）\n\n本地科学整合与核验；待作者审核及后续选择性归档，不标CLOSED。Table 5保留；新增S50（`stab:r2minor2_intervals`）并列90/95%概率区间。证据见`results/r2minor2_integration/`。其他共享事项Pending，M9最终仓库文档待办保留，未启动R2-m3。\n';Path(f).write_text(s)
f='SUPPLEMENTARY_TABLE_REGISTRY.md';s=Path(f).read_text();s+='\n\n### R2-m2新增表（2026-11-15，本地待审核）\n\n- S50：`stab:r2minor2_intervals`，q14/q16三模型五种子，全部/有雨/上尾90%与95%覆盖率、宽度、上界漏覆盖及负下界比例（均值±样本SD）。\n- S1–S49原内容及label不变；任务16其他共享事项保持Pending。\n';Path(f).write_text(s)
(P/'STATUS.md').write_text('R2-m2 LOCAL_INTEGRATION — VERIFICATION_IN_PROGRESS\nNo commit/push; not CLOSED. R2-m3 not started. M9 final repository documentation remains pending.\n')
print('Integrated minimal changes; 112 old excerpts mapped; 144 numeric table fields generated.')
