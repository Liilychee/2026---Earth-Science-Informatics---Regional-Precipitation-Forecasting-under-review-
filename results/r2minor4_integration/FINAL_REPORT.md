# R2-m4 local integration — verified, awaiting author review

## Status and mandatory starting gate

**LOCAL_VERIFIED_AWAITING_AUTHOR_REVIEW; NOT CLOSED.** No commit or push.

Before any paper modification, remote main was read using git ls-remote and confirmed as `4aabdcb0aaadf3fa679c0c4bfe08d477ec755f81`. R2-m3 STATUS is CLOSED; its final52-file receipt and scientific/closure chain were checked. Current response/task/checklist bytes match R2-m3 after-SHA256 records, and all preceding protected hashes match. Remote-fixed STATUS and DOCUMENT_HASHES agree with local records. BASELINE_GATE.json preserves this prerequisite check. No pull/reset, force push or original-worktree replacement occurred.

## Historical-answer review and permitted change

Task17 was read in full, together with the relevant task10 experimental/uncertainty/current-state records and task25 complementarity records. Historical drafts are not treated as final results. The new reply does not reuse:2–30% CV; positive absolute SHAP as significance; bootstrap-plus-majority direction as sufficient robustness; all single precipitation removals as ineffective; old section/figure/table plans; or the unmade R4 temporal heatmap. Existing R1-M4 and R2-M8 replies were used to maintain scientific boundaries and current automatic references, not rewritten.

Only three source/task files changed:
- Response letter.tex, R2-m4 block: reviewer wording retained verbatim; formal AuthorResponse red and two fresh EvidenceBoxes/locations blue. Exact source lines are in LOCATIONS.json. No other reviewer response changed.
- Task17: one scoped R2-m4 local-progress note; all original task text and tasks10/25 remain untouched.
- FINAL_REVISION_CHECKLIST.md: one matching R2-m4 append.

Main text, Supplementary, registry, bibliography, Table5, S1–S50 and all Figures are unchanged. No training, SHAP calculation, new plot, model prediction, new experiment or bootstrap computation was performed. Only existing seed-summary arithmetic was checked.

## Verified evidence and actual references

Source scripts and original CSV/logs were read from fixed q10 commit **6495abc81101074b02b3a5c8cfc83cd6cbc33d79**, with paths/MD5/SHA256 in SOURCE_INDEX.json. Numerical claims are traced to source row/field and actual existing table cells in CELL_INDEX.json(78 references); methodological counts/seed identifiers are separately mapped to the relevant table captions/column headings and original code in METHOD_INDEX.json.

Actual labels, verified against current aux files:

| Evidence | Label | Current number / PDF page |
|---|---|---|
| Uncertainty method | sec:interpretation_uncertainty | §3.5.3 / main43 |
| SHAP Figure | fig:r1m4_shap_comparison | Fig.7 / main69 |
| Ablation Figure | fig:r1m4_ablation_comparison | Fig.8 / main71 |
| Bi ablation / seed pairs | stab:r1m4_ablation_bilstm_attn / stab:r1m4_seed_pairs_bilstm_attn | S12/S13 / supplement7/8 |
| BU ablation / seed pairs | stab:r1m4_ablation_bulstm_attn / stab:r1m4_seed_pairs_bulstm_attn | S14/S15 / supplement9/10 |
| SHAP magnitude / direction | stab:r1m4_shap_magnitude / stab:r1m4_shap_direction | S16/S17 / supplement11/12 |
| Rank comparison / stability | stab:r1m4_feature_rank_comparison / stab:r1m4_rank_stability | S18/S19 / supplement13/14 |

The response separates training variability from test-case sampling uncertainty:
- SHAP: five-seed mean/SD;2,000 calendar-day cluster bootstrap replicates, seed42, fixed fitted models and training background. Bi upper-tail mntpr=0.089130 mm h^-1, seed SD0.005174, pointwise interval[0.075460,0.102467]. Those magnitudes do not prove independent predictive gain or significance of forecast improvement.
- Ablation: same-seed removal-minus-full RMSE differences, mean/sample SD, Student-t95% interval(df4), paired moving blocks28 six-hourly samples,10,000 replicates, seed42. Within-seed differences precede seed averaging, not ensemble-mean predictions.
- Bi sp full-test mean difference+0.004022, SD0.000606, seed interval[0.003270,0.004774], block interval[0.002527,0.005547];5/5 deterioration.
- BU mntpr removal gives mean differences−0.001901(all),−0.010509(revised wet),−0.020662(upper tail). Every subset has five negative seed differences and both intervals entirely below zero. All three descriptive criteria hold, without implying mntpr is generally harmful or meteorological causality.
- BU sp/tcc full-test effects are positive in only4/5 seeds; bootstrap intervals above0 but seed intervals cross0. They are not assigned the same robustness conclusion.

Six targeted source rows and the SHAP example were checked, including same-seed SD/t-interval arithmetic; maximum difference from stored seed summaries **2.0816681711721685e-17**. Existing sampling intervals were read, not recomputed. No repeated full1,335-cell transcription audit or new SHAP/bootstrap job was needed.

## Explicit retained limits

The red reply states that SHAP bootstrap does not include training randomness; fixed-background sensitivity was not evaluated; temporal SHAP is an approximate finite-permutation calculation without its own intervals; seed intervals have only five fitted models; training/case-sampling uncertainties are not combined; all intervals are pointwise without multiplicity correction. The three-way descriptive rule is not itself a multiple-testing correction.

Read-only code audit also records a precise existing implementation detail in BOOTSTRAP_METHOD_CHECK.md: q10 aggregates141 complete moving blocks of28, i.e.3,948 draw positions, without truncating to3,939. The response does not describe the implementation as exact-n resampling and no archived interval or closed source was changed. This is a retained implementation/reproducibility boundary, not a newly estimated correction or causal explanation. No unsupported statement that all sources of uncertainty have been captured is made.

## EvidenceBox and prior-result protection

**118 prior RevisedExcerpt arguments unchanged +2 newly extracted/reused boxes=120/120 matches,100%.** Both new source paragraphs are freshly taken from latest manuscript §3.5.3 and §4.6. Before hashes/stable anchors/source lines are in EXCERPT_BEFORE_MAP.json. Multiplicity checks handle the intentional re-use of paragraphs quoted in prior replies.

R1-M4's8 EvidenceBoxes and R2-M8's6 are individually checked byte-identical. Response outside R2-m4 is byte-identical. **767 protected files** match before hashes, including prior closed evidence, unchanged manuscript/supplement and all Figures. No old excerpt synchronization was needed because the manuscript was not changed or moved.

R1-M4/R2-M8/R2-m3 remain CLOSED; R4-m29/R4-m34 remain Pending. Other shared task17 matters retain their prior state; task17 as a whole is not closed. M9 remains SCIENTIFIC_INTEGRATION_COMPLETE — FINAL_REPOSITORY_DOCUMENTATION_PENDING, not overall CLOSED. No R2-m5 or final README/LICENSE/environment work was started.

## Build and actual PDF check

Ordered latexmk checks: Supplementary → manuscript → Response letter. Unchanged main/supplement were up-to-date, and their PDF hashes are identical to the verified R2-m3 build. Reply rebuilt successfully.

Final lengths: main97pp, supplement57pp, reply78pp(previous76pp). Actual144dpi renders at native-page reading scale were inspected for reply pp55–57: reviewer/response transition, red results/uncertainty/limitations and two blue boxes. The final explicit95% block-interval wording was re-rendered and inspected. Section3.5.3, Fig.7/8 and S12–S19 render correctly; no clipping/overlap/unreadable text.

No undefined references, duplicate labels, horizontal overflow, oversized float or blocking error. Existing Springer template font/bookmark and1.41457pt vertical-box warnings were retained. PDF_CHECK.json records source/build hashes and actual visual review; compile logs are saved.

## Deliverables and remaining status

- R2minor4_LOCAL.patch: only the response block, task17 note and matching checklist append.
- CELL_INDEX.json(78), METHOD_INDEX.json, SOURCE_INDEX.json, LABEL_INDEX.json, DATA_CHECK.json and BOOTSTRAP_METHOD_CHECK.md.
- BASELINE_GATE.json, EXCERPT_BEFORE_MAP.json, FINAL_EXCERPTS.json, EXCERPT_INDEX.json, PROTECTED_HASHES.json, VERIFICATION.json, DOCUMENT_HASHES.json and LOCATIONS.json.
- PDF_CHECK.json, PDF_PAGE_INDEX.json, three compile logs, render/ and GIT_STATE.json/GIT_STATUS.txt.

No blocking local scientific/layout issue found. Await author review and separate selective archive authorisation; do not commit/push or mark CLOSED in this round. Historical task drafts remain archival context and are superseded for this response by current verified evidence, not silently edited. Final page/line annotation remains deferred to whole-revision assembly.


## Author-authorised selective archive and formal closure — 2026-11-15 (Claude Code takeover)

Breakpoint recovered: Codex stopped after LOCAL_VERIFIED_AWAITING_AUTHOR_REVIEW; no R2-m4 worktree, stage, commit or push existed and remote main remained 4aabdcb0aaadf3fa679c0c4bfe08d477ec755f81. Claude Code re-verified the local integration read-only (Codex check scripts were not re-run because they rewrite records): 120/120 excerpts, 78/78 CSV fields, 767 protected files, unchanged main/Supplementary/Figures, R1-M4/R2-M8/R2-m3 reply blocks unchanged, PDF records and page-57 render reviewed. The q10 ablation bootstrap's 141 complete blocks (3,948 draw positions) are not described as 3,939-sample resamples anywhere in the reply or manuscript; no interval was reinterpreted or recomputed.

The R2-m4 reply/task/checklist increment and selected evidence were archived from main 4aabdcb in independent worktree /private/tmp/esi-r2minor4-integration-sync. Scientific commit `9603d29738378d5788d4c18efdd1a4e49360857b` was normally pushed. A fresh remote clone matched 50/50 blobs; the remote PORTABLE patch reconstructed the exact reviewed source bytes in scratch; 120/120 excerpts and 78/78 CSV fields re-verified from the remote copies. Original paper files, git index and PDFs were not overwritten (ORIGINAL_WORKTREE_GUARD.json).

R2-m4 is CLOSED after successful remote verification. A separate closure commit records STATUS, the remote receipt, archive report and the task17/checklist closure-note patch (CLOSURE_STATUS.patch, recorded for later assembly; original paper files not modified). Historical local-pending statements above are superseded by current STATUS. Other shared matters retain their prior status; M9 remains not overall closed. No new experiment, interval, figure or table; no other reviewer item started.
