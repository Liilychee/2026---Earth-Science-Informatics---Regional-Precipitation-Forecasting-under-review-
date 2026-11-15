# R3-12 — Huber versus MSE

Status: R3-12 local scientific revision complete — Git archiving deferred.

## Configuration and independent checks
Existing q15 evidence: two deterministic models, MSE plus standard Huber delta0.5/1/2 in standardized target units;five seeds (42, 123, 7, 2024, 99), W=6 (30 h), seven predictors, chronological70/15/15, train-only scaling, same optimizer/batch 32, epoch cap 30 and patience 10 within architecture.3,939 matched test targets, Wet>=0.1 n=854, Upper>=trainingQ95=0.574048 n=238. No smoke runs included. Each delta's validation mean recomputed from five run JSON files; min among Huber candidates selects 2 for both, a grid boundary, not established optimum. MSE was a control, not part of that delta search. No original design-history record is inferred from the statistical MSE rationale.
40 saved predictions and 40 run JSON files read from fixed d02519c5f153feb712018cf97efb035f6ca2d7ae. Recomputed existing means/SDs, biases, SD ratios, seed differences/tCI and pooled-error point diagnostics: maximum discrepancy 3.33e-16. Stored block interval fields transcribed; bootstrap not rerun. Common timestamps and targets match across paired losses. See SAVED_RESULTS_CHECK.json, SOURCE_INDEX and CELL_INDEX.

## Complete deep-model regime results (mm/h)
| Model | Loss | All RMSE | Wet RMSE | Upper RMSE |
|---|---|---:|---:|---:|
|BiLSTM-Attention|MSE|0.242864|0.484963|0.873204|
|BiLSTM-Attention|huber0.5|0.257348|0.543764|0.972671|
|BiLSTM-Attention|huber1|0.252726|0.529090|0.952395|
|BiLSTM-Attention|huber2|0.246831|0.508858|0.918214|
|Transformer|MSE|0.259990|0.528298|0.949053|
|Transformer|huber0.5|0.262386|0.555338|0.991317|
|Transformer|huber1|0.256663|0.537696|0.964682|
|Transformer|huber2|0.254297|0.523929|0.941451|

All 18 Huber/subset rows have pointwise seed-t intervals, paired block intervals and seed directions in S58. BiLSTM-Attention at delta=2 overall difference+0.003967 and upper +0.045010; 0/5 seeds improved. At delta=0.5, overall +0.014484. Transformer at delta=2 overall −0.005693; 5/5 seeds improved. Wet/upper seed CIs span0 while pooled-error block CIs exclude0. Transformer MSE epochs[30,30,30,16,30], and every Huber configuration has 5/5 runs at 30. These counts indicate a shared budget limit, not proven non-convergence or an identified improvement mechanism.
BiLSTM-Attention full-test prediction SD ratio0.413532→0.327463(MSE→delta2);upper bias−0.764207→−0.815818. These descriptive changes do not identify the causal source of compression. The table/main use rounded−0.8158, not an inaccurate historical approximation.

## XGBoost evidence and limits
| Variant | All RMSE | Upper RMSE | All bias |
|---|---:|---:|---:|
|M0 MSE|0.242643|0.841628|-0.004325|
|M1 pseudo-Huber 0.1|0.251829|0.942545|-0.051047|
|M2 pseudo-Huber 0.5|0.243845|0.881630|-0.022373|
|M3 weight inv-freq|0.293047|0.649013|+0.128188|
|M4 weight inv-sqrt-freq|0.253637|0.742807|+0.054351|
|M5 log1p target|0.242719|0.882654|-0.022955|
|M6 Tweedie 1.5|0.241745|0.876288|-0.025064|

q05f_raw has 35 records = seven variants × five seeds, each seedset complete; old single-seed draft is false. q05f_summary evaluates five-seed mean predictions, distinct from mean of seed-level RMSEs. Its q05f_paired fields are consistent with summary point scores; script/log establish aggregation. Pseudo-Huber slopes0.1/0.5mm/h are converted to standardized slope, not standard deep Huber. Targets/scales differ for log1p/Tweedie; all strategies retain own M0control, not original main Table3. M3/M4weights use inverse/inverse-sqrt training-class frequencies normalizedmean1. M5usesexpm1 plus clipping at0;M6Tweediepower1.5. No loss-parameter validation tuning. Parameter declarations are verified; a contemporaneous preregistration claim is not independently established.
Archived q05f code constructs seed predictions in memory; no per-case q05f prediction files were located in the fixed tree. Thus ensemble scoring/paired intervals cannot independently be rebuilt from q05f_raw (which contains only per-run aggregate scores). This turn verifies code,35 raw records, summary/paired consistency and output log; does not claim independent reconstruction of those ensemble predictions/intervals. Actual NBOOT is environment-overridable; script default 2,000, block length 28, circular sampling truncated to n=3,939, seed 42; log does not independently establish actual count. S59 explicitly discloses this. Conditional case-bootstrap intervals do not measure training randomness. No new computation/training fills these gaps.

## Existing/new presentation and prose
Existing §3.4 / §4.3.3 / §5.4 already report selected Huberdelta2, adverse BA result, favourableTR result, weightedXGB tradeoff and limits; preserved word-for-word. Historical task05/15 plans S9b/S24 were not actual inserted tables.
New S57 `stab:r3huber_scores`,Suppp65:eight MSE/Huber settings,validation/test meansSD,regime results,SD ratios,upperbias. New S58 `stab:r3huber_pairs`,p66:18 paired rows, distinct estimands/CIs/directions/counts. New S59 `stab:r3huber_xgb`,p67:seven strategies,errors/bias/dispersion and relevant saved blockCIs.290 CSV fields indexed with exact physical lines/columns (multi-level q15_runs header handled). Existing S1–S56 and Figures unchanged. No new figure required.
manuscript.tex: insert concise MSE/Huber rationale after the MSE equation in §3.3.2(p22); append tablelinks and descriptive distribution diagnostics in existing actual §4.3.3(p66), not historical§4.2. Existing §5.4scientific limitations are adequate and unchanged. No protected existing prose deleted or rewritten.
Response letter.tex: only the R3 L376 response/location plus3exact excerpts. Red reply/blue boxes preserved; local refalias ensures quoted main syntax remains verbatim. Bibliography unchanged. The next Reviewer 3 response untouched; no Git staging, commit or push.

## Statistical and scientific boundaries
MSE minimizes expected squared error at the conditional mean and aligns with RMSE. Huber reduces leverage of large residuals but does not know which observations are rare rainfall, nor by itself solve occurrence/amount modelling. A large residual need not be an extreme-rainfall case. Neither results nor theory establishHuber universally unsuitable or prove that MSE causes all compression. Present statistical rationale is not an invented historical choice record.
The q15 seed-t CI (df=4) concerns mean paired seed RMSE; block CI concerns a difference of square roots of seed-averaged squared errors, a slightly different estimand. Same non-circular movingblock implementation as S55: block length 28, 5,000 replicates, seed 42; 141 whole blocks retained, giving 3,948 sampled positions for 3,939 targets. S58 reports both point values and distinguishes intervals. All intervals are pointwise and unadjusted; no combined total interval or general causal claim. q05f uses different circular scheme and ensemble-mean predictions, not q15 estimand.

## Evidence and PDFs
The original 139 RevisedExcerpts exactly unchanged in order/content; three added exact main extracts; 142/142 matching. Other closed responses, including R3-01–11, unchanged. Original main paragraphs/table/figure blocks unchanged;the original Supplementary prefix unchanged;all Figure PDF hashes and the Git index unchanged.
Ordered Supplementary → manuscript → response builds passed. Final page counts: 67/103/88. Actually inspected main 22/66, Supplementary 65–67 and response 70–71: no cropping/overlap or incorrect references/colors. Initial table overflow was resolved by slightly reducing S57 column padding; font unchanged. Final undefined references/citations, duplicate labels, horizontal overflow, oversized floats and blocking errors: none. The existing main output-vbox warning (1.41457 pt, 102 instances) persists; no new warning type. See PDF_CHECK.

## Remaining limits
Limitations include one chronological split, two architectures, three Huber deltas with boundary selection, the Transformer epoch budget, distinct interval estimands, unadjusted multiple comparisons, and missing q05f per-case predictions and confirmed bootstrap count. These limits are explicit. No missing evidence was replaced by invented results, and no blocking conflict with closed scientific conclusions was found.

## Final English response (full LaTeX)

MSE is aligned with our conditional-mean point forecasts and RMSE evaluation. Huber reduces the influence of large residuals, which are not necessarily all heavy-rainfall cases; it does not by itself resolve excess zeros or guarantee better upper-tail prediction. We now explain this in Section~\ref{manuscript-sec:bilstm_attention_components}.

We tested standard Huber with $\delta=0.5,1,2$ in standardized target units for BiLSTM-Attention and Transformer, using the same split, six-snapshot inputs, within-model hyperparameters and five fixed seeds. Both selected $\delta=2$ by mean validation RMSE among the Huber candidates; this boundary choice is not a proven optimum. Supplementary Tables~\ref{supp-stab:r3huber_scores} and~\ref{supp-stab:r3huber_pairs} report all candidates and regime scores. For BiLSTM-Attention, selected Huber increases overall RMSE by 0.0040 and upper-tail RMSE by 0.0450~mm\,h$^{-1}$, with no seed improving. Its prediction SD ratio falls from 0.414 to 0.327. Conversely, Transformer overall RMSE improves by 0.0057~mm\,h$^{-1}$ with all five seeds improving; its wet/upper-tail seed intervals include zero, and both losses frequently approach the shared 30-epoch cap. These findings are conditional on the tested training budget.

The separate XGBoost comparison includes pseudo-Huber, log1p, Tweedie and two weighting schemes (Supplementary Table~\ref{supp-stab:r3huber_xgb}). All have five seed records, but metrics are calculated from seed-averaged predictions, not averaged seed scores. Pseudo-Huber is distinct from standard Huber; weighting reduces upper-tail error at a cost in overall error and bias. These tests do not identify the dominant cause of compressed forecasts or show that Huber is generally unsuitable for precipitation. We retain the model-specific results and limitations in Section~\ref{manuscript-sec:training_objective_sensitivity}; all reported intervals are pointwise and unadjusted for multiple comparisons.
