# -*- coding: utf-8 -*-
from pathlib import Path
import re,json,hashlib,difflib
P=Path(__file__).resolve().parent;B=P/'before';M=Path('manuscript.tex').read_text();R=Path('Response letter.tex').read_text();assert R==(B/'Response letter.tex').read_text()
code=Path('results/r2m6_integration/check_integration.py').read_text();exec(code[code.index('def args('):code.index('oldex=args(')])
old=args(R,'RevisedExcerpt');assert len(old)==115
# Extract current source paragraphs by stable anchors, never from historical reply quotations.
anchors={'fixed':'Figure~\\ref{fig:r2m4_event_csi} compares the two decision rules using saved single-run forecasts.','tuned':'Validation-selected cutoffs changed the operating rule rather than removing the fixed-rule failure.','one_mm':'At the fixed mean-based rule $c_\\tau=\\tau=1.0$'}
ex={}
for k,a in anchors.items():
 matches=[x for x in M.splitlines() if x.startswith(a)];assert len(matches)==1;ex[k]=matches[0];assert ex[k] in M
(P/'FINAL_EXCERPTS.json').write_text(json.dumps(ex,indent=2));(P/'EXCERPT_BEFORE_MAP.json').write_text(json.dumps(dict(old_count=115,old=[dict(index=i+1,sha256=hashlib.sha256(t.encode()).hexdigest(),matches_before=canonical(t) in canonical(M)) for i,t in enumerate(old)],new=[dict(name=k,stable_anchor=anchors[k],sha256=hashlib.sha256(t.encode()).hexdigest(),current_source_line=M[:M.index(t)].count('\n')+1,already_quoted_in_other_reply=t in old) for k,t in ex.items()],manuscript_edits=0,affected_old_boxes=0),indent=2))
response=r'''We have expanded the event-detection reporting in Section~\ref{manuscript-sec:event_detection}, Figure~\ref{manuscript-fig:r2m4_event_csi} and Supplementary Tables~\ref{supp-stab:r2m4_fixed_events}--\ref{supp-stab:r2m4_ensemble_events}. The fixed intensity thresholds are 0.1, 0.5 and 1.0~mm\,h$^{-1}$. The training-quantile thresholds are Q90 $=0.295784$, Q95 $=0.574048$ and Q97.5 $=0.932169$~mm\,h$^{-1}$ (rounded to six decimal places), estimated from 18,404 windowed training targets rather than the test set. The six learning models are XGBoost, Transformer, BU-LSTM, BiLSTM-Attention, BU-LSTM-Attention and Probabilistic BiLSTM-Attention. The three references are Persistence, training-fitted AR(1), and training-fitted month-by-hour climatology.

We report the available POD, FAR, CSI and ROC-AUC, together with forecast and hit counts. POD is $\mathrm{TP}/(\mathrm{TP}+\mathrm{FN})$, FAR is the false alarm ratio $\mathrm{FP}/(\mathrm{TP}+\mathrm{FP})$, and CSI is $\mathrm{TP}/(\mathrm{TP}+\mathrm{FP}+\mathrm{FN})$. Under the fixed rule, the predicted mean is compared with the observed-event intensity threshold ($c_\tau=\tau$). Under the validation-selected rule, each method's cutoff maximizes validation CSI over up to 300 distinct candidates and is then frozen for testing. ROC-AUC uses the continuous forecast score and is independent of that decision cutoff, while depending on the observed-event definition $y\geq\tau$. For the probabilistic models, these mean-based event decisions are distinct from the exceedance-probability Brier-score analysis.

The reporting scope is explicit: Supplementary Table~\ref{supp-stab:r2m4_fixed_events} has six thresholds by nine methods, whereas Table~\ref{supp-stab:r2m4_tuned_events} has five thresholds by nine methods. The validation-selected rule was not evaluated at 0.5~mm\,h$^{-1}$, and complete AUC results were not saved at that intensity. The unavailable fixed-rule AR(1)/climatology AUC entries remain dashes; undefined FAR when no events are forecast is also shown as a dash, not zero. We do not claim that every metric is available for every threshold, method and rule. The separate five-seed diagnostics in Tables~\ref{supp-stab:r2m4_seed_scores} and~\ref{supp-stab:r2m4_ensemble_events} cover only BiLSTM-Attention and BU-LSTM-Attention. Seed-level summaries, five-seed mean-prediction comparisons and the single saved runs are kept distinct.

The adverse results are retained. Under the fixed rule, all 24 learning-model minus Persistence CSI differences at 0.5, Q95, Q97.5 and 1.0~mm\,h$^{-1}$ are negative. At 1.0~mm\,h$^{-1}$, XGBoost detects only one observed event, while the other five learning models detect none. Validation-selected cutoffs recover detections, but the six learning models' FAR at 1.0~mm\,h$^{-1}$ remains 0.859--0.916. At Q95 under that rule, Transformer CSI is 0.133, below Persistence's 0.156. ROC-AUC describes ranking information and does not establish useful warning performance. At some event thresholds, the climatology's selected cutoff lies at the lower boundary of its candidate grid, so that comparison can depend on the candidate space; no untested improvement is inferred.

The reported paired intervals are pointwise and unadjusted for multiple comparisons. Validation-selected-rule intervals are conditional on the selected cutoffs and omit cutoff-selection uncertainty. We add no Holm-adjusted inference or new climatology paired intervals here. The existing event results answer this comment without new training, figures or tables. Final page and line numbers will be added after full-manuscript assembly.'''
# Scope local aliases to the new boxes so their literal source references render correctly.
alias=r'''\begingroup
\makeatletter
\expandafter\let\csname r@fig:r2m4_event_csi\expandafter\endcsname\csname r@manuscript-fig:r2m4_event_csi\endcsname
\makeatother
'''
boxes=[]
for k,title in [('fixed','Existing fixed-rule results'),('tuned','Existing validation-selected results and AUC boundary'),('one_mm','Existing 1.0 mm h$^{-1}$ event diagnostic')]:
 boxes.append(r'\EvidenceBox{'+title+r' (Section~\ref{manuscript-sec:event_detection}; final page and line numbers pending)}{'+'\n'+r'\RevisedExcerpt{'+ex[k]+'}\n}')
a,b=R.index('% Review ID: R2 m3'),R.index('% Review ID: R2 m4');block=R[a:b];assert block.count(r'\PendingResponse')==1
block=block.replace('\\PendingResponse\n\n\\ChangeLocation',r'\AuthorResponse{'+response+'}\n\n'+alias+'\n\n'.join(boxes)+'\n\\endgroup');R=R[:a]+block+R[b:];Path('Response letter.tex').write_text(R)
f='ESI_审稿意见分类_严重程度排序_35项.md';s=Path(f).read_text();anchor='### 12. 降水事件评估不完整';note='\n\n**R2-m3局部正式整合（2026-11-15，本地待作者审核）**：复用§4.3.2、Figure 5及S28–S31，现有正文/表/图不变，仅补正式回复与3段逐字摘录。S28为6阈值×9方法，S29为5阈值×9方法；0.5优化规则及完整AUC缺失如实披露。按原始q05e核实，六模型1.0阈值FAR为0.859–0.916（Transformer为上限），不是0.859–0.913。任务12其他共享事项保留原状态，M9仓库文档待办不变，未启动R2-m4。未Git提交/推送，不标CLOSED。\n';assert s.count(anchor)==1;Path(f).write_text(s.replace(anchor,anchor+note,1));(P/'TASK_NOTE.json').write_text(json.dumps(dict(anchor=anchor,note=note),indent=2))
f='FINAL_REVISION_CHECKLIST.md';s=Path(f).read_text();s+='\n\n### R2-m3 / 任务12局部（2026-11-15）\n\n本地正式回复复用现有事件证据与3段逐字摘录；正文、Supplementary S1–S50、Table 5及Figures不改。按q05e纠正1.0阈值六模型FAR上限为0.916。待作者审核及后续选择性归档，不标CLOSED；任务12其他共享事项原状态保留，M9最终仓库文档待办保留，未启动R2-m4。\n';Path(f).write_text(s)
(P/'STATUS.md').write_text('R2-m3 LOCAL_INTEGRATION — VERIFICATION_IN_PROGRESS\nNo commit/push; not CLOSED. R2-m4 not started. M9 repository documentation pending.\n')
print('Only R2-m3 reply, task12 note and checklist updated; three excerpts freshly extracted from current manuscript.')
