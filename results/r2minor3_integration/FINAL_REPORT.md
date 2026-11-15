# R2-m3 local scientific integration — verified; awaiting author review

## Result and scope

R2-m3 is **LOCAL_VERIFIED_AWAITING_AUTHOR_REVIEW**, not CLOSED. Only the R2-m3 block of Response letter.tex, the task12 R2-m3 note and the matching final-checklist note were changed. No manuscript.tex, Supplementary.tex, Table5, S1–S50, registry, Figure, original experiment result or saved prediction was modified. No training, new experiment, new plot, formal score/Bootstrap rerun, Git commit or push occurred. R2-m4 was not started. M9 remains SCIENTIFIC_INTEGRATION_COMPLETE — FINAL_REPOSITORY_DOCUMENTATION_PENDING.

## Actual references and evidence coverage

Latest build auxiliary labels, rather than historical plans, confirm:

| Content | Label | Actual number / page |
|---|---|---|
| Event-detection section | sec:event_detection | §4.3.2 / main p59 |
| Existing author CSI Figure | fig:r2m4_event_csi | Figure5 / main p60 |
| Fixed-rule scores | stab:r2m4_fixed_events | S28 / supplement pp23–25 |
| Validation-selected scores | stab:r2m4_tuned_events | S29 / supplement pp26–28 |
| Seed-level summaries | stab:r2m4_seed_scores | S30 / supplement p29 |
| Five-seed mean-prediction comparisons | stab:r2m4_ensemble_events | S31 / supplement p30 |

The red formal reply names six learning models and three baselines, separates the observed event intensity from the decision cutoff, defines POD/FAR/CSI, and explains cutoff-independent continuous-score ROC-AUC and its dependence on event definition. It distinguishes probabilistic-model mean event decisions from exceedance-probability Brier analyses. All cross-references use actual label/ref commands. Reviewer wording is unchanged.

- S28:6 thresholds×9 methods=54 saved rows; fixed intensity0.1/0.5/1.0 plus training Q90/Q95/Q97.5.
- S29:5 thresholds×9 methods=45 rows; no validation-selected0.5 result.
- Training-quantile values rounded to six decimals:0.295784,0.574048,0.932169, from18,404 training targets. Both fixed and tuned source records support those displayed values; the tiny full-precision differences between stored source threshold values were not relabelled as byte-identical.
- No complete0.5 AUC in these event tables; fixed-reference AR(1)/climatology AUC dashes retained; undefined zero-forecast FAR is a dash, not zero.
- Only BiLSTM-Attention and BU-LSTM-Attention have the five-seed diagnostics in S30/S31. Single saved runs, individual-seed summaries and mean-prediction paired comparisons remain separate.
- All24 fixed-rule learning-model minus Persistence CSI differences at0.5/Q95/Q97.5/1.0 are negative. Existing pointwise upper confidence limits are also negative, but no Holm inference is introduced.
- At fixed1.0, XGBoost has one hit and the other five learning models have none.
- Under the selected-cutoff rule, Q95 CSI for Transformer=0.133 versus Persistence=0.156. ROC-AUC ranking information is not treated as useful-warning evidence.
- Existing reported paired intervals remain pointwise/unadjusted; selected-cutoff intervals omit cutoff-selection uncertainty. No new climatology paired interval is added.

## Correction required by primary evidence

The instruction's1.0 FAR range0.859–0.913 excludes the largest learning-model FAR. The original q05e_event_scores.csv and existing S29 give **0.8586387434554974 (XGBoost) to0.9163763066202091 (Transformer)**, hence the correct six-model range is **0.859–0.916**. Probabilistic BiLSTM-Attention is0.9128367670364501, which rounds to0.913 but is not the upper endpoint. The new reply uses the complete six-model range. Existing main text's approximately0.86–0.92 remains accurate and was not edited. This was reported during execution and is not a change to an experimental result.

## Source and numerical checks

Eleven original scripts/CSV/output files were read at their fixed Git versions; full commits, paths, MD5 and SHA256 are in SOURCE_INDEX.json. This round checked stored counts/formula consistency for all99 fixed/tuned rows, the24 adverse saved CSI differences and intervals, key threshold/count/FAR/CSI/AUC statements and seed-scope metadata. It did not claim to rerun the prior independent full-prediction/Bootstrap audit.

CELL_INDEX.json contains190 field references with source CSV line/column/raw/display values, including numerical evidence used by the three freshly extracted excerpts. DATA_CHECK.json records54/45 rows, six/nine/five scope and corrected range. No archived source CSV was replaced.

A lightweight check reproduced only the existing q05e candidate values from the original local reduced regional series and original training month-by-hour means, without retuning or recalculating event scores. The300 probability positions yield27 unique candidate values for climatology; the archived wet/Q90/Q95 cutoffs coincide with the lower grid boundary to floating precision (difference<4e-15). The reply states only that this limits the comparison, without predicting an untested improvement. BOUNDARY_CHECK.json and raw-input MD5 document this check; raw data were not copied into the evidence folder.

Fixed source commits used: `667d6f80e64076dc6812ca630654a24d1aab5b4e`, `d02519c5f153feb712018cf97efb035f6ca2d7ae`.

## EvidenceBox protection

All115 prior RevisedExcerpt arguments remain unchanged. Three additional blue boxes are freshly extracted verbatim from the latest manuscript's fixed-rule paragraph, validation-selected paragraph, and original R1-M1 one-millimetre paragraph. Those paragraphs already support earlier replies; the new boxes are intentional reuse, not new manuscript text.

**118/118 excerpt occurrences match**,100%. Multiplicity checks ensure all old occurrences were preserved despite duplicate quoted passages. Response text outside R2-m3 is byte-identical.706 prior/source/Figure hashes passed, including closed R2-m2 records, M9 records, unchanged main/supplement and old Figures. No old EvidenceBox needed rewriting because no manuscript passage moved or changed. EXCERPT_BEFORE_MAP.json preserves stable anchors, source lines and hashes; EXCERPT_INDEX.json and VERIFICATION.json store full checks.

## Compilation and visual review

Ordered latexmk checks: Supplementary → manuscript → Response letter. Main and Supplementary were already up-to-date; both PDF hashes match the preceding verified R2-m2 build exactly. Reply was rebuilt successfully. Final lengths: supplement57pp, main97pp, reply76pp (previous75pp).

Actual144dpi page renders of reply pp53–55 were inspected: reviewer transition, full red response, three blue EvidenceBoxes, resolved §4.3.2/Figure5/S28–S31 references and no clipping/overlap. R2-m4 remains its placeholder. No undefined reference, duplicate label, horizontal overflow, oversized float or blocking error. Existing Springer template font/bookmark and1.41457pt vertical warnings remain recorded without unrelated cleanup.

## Files and next status

- Response letter.tex (only R2-m3); task12 note; FINAL_REVISION_CHECKLIST.md matching note. Exact source line locations: LOCATIONS.json.
- R2minor3_LOCAL.patch: only these three file increments against protected before snapshots.
- CELL_INDEX.json; SOURCE_INDEX.json; DATA_CHECK.json; BOUNDARY_CHECK.json; LABEL_INDEX.json.
- EXCERPT_BEFORE_MAP.json; EXCERPT_INDEX.json; FINAL_EXCERPTS.json; PROTECTED_HASHES.json; DOCUMENT_HASHES.json; VERIFICATION.json.
- PDF_CHECK.json; PDF_PAGE_INDEX.json; compile logs; render/; GIT_STATUS.txt.

No blocking scientific/layout issue remains for local integration. Author review and later selective Git archive are still pending; do not mark CLOSED. Remaining scientific boundaries are intentionally disclosed: incomplete0.5/AUC coverage, single-run versus limited five-seed scope, candidate-grid dependence and conditional pointwise intervals. Task12 other shared items retain their prior state; closed R1-M1/R2-M4/R2-m2 remain protected. M9's repository documentation and final Code Availability remain pending. No R2-m4 work or repository README/environment/LICENSE work was undertaken.


## Author-authorised selective archive and formal closure — 2026-11-15

The approved R2-m3 reply/task/checklist increment and selected evidence were archived from latest main7e2939aecfac856d422fd95003e0d48e834a7252 in an independent worktree. Scientific commit `87a9c95e77d37686c25af8a32216f005e9eb2059` was normally pushed. Fixed-commit GitHub readback **48/48 files matched local blob hashes**. The three-file portable patch reconstructs exact reviewed source bytes in scratch.115 old excerpts remain unchanged;3 new reused/extracted boxes match the current main source;118/118 matched.190 CSV references, correct FAR0.859–0.916, six/nine versus five/nine rule scope,706 protected artifacts and source-matched three-PDF checks passed.

R2-m3 is CLOSED after successful remote verification. A separate closure commit records STATUS, the successful remote receipt, archive report and task12/checklist closure-note patch, with final post-push per-file verification. Original paper files/index/PDFs were not overwritten. Historical local-pending statements above are superseded by current STATUS; no prior scientific/closed archive is rewritten. R2-m2 and older closed results are preserved. Other shared matters retain their prior status, unfinished items Pending. M9 remains SCIENTIFIC_INTEGRATION_COMPLETE — FINAL_REPOSITORY_DOCUMENTATION_PENDING (not overall CLOSED). No R2-m4 or final repository-documentation work was started. Existing missing-metric, candidate-space and conditional-unadjusted-interval limits remain disclosed; no new blocker was found.
