# R3-11 — seasonal climatology

Status: R3-11 local scientific revision complete — Git archiving deferred.

## Definition and origin
The original saved climatology is a single overall training-period mean, not month/season dependent. The saved file was read from fixed Git evidence and verified:3939 test times, exactly one prediction value. See ORIGINAL_CLIMATOLOGY_CHECK.json. It is a simple constant reference; no separate contemporaneous decision record for preferring it to seasonal climatology was located. No historical rationale invented.
Original Table3 uses18410 raw training times; q07 refit and its conditional variants use18404 windowed training targets. These statistics must not be merged at high precision. q07 loads26,300 raw six-hourly regional times, partitions70/15/15 first, drops the first6rows within each partition as targets. Valid-time month/hour/season labels define conditional groups. DJF/MAM/JJA/SON mapping verified in code; training group means only; test values never used to fit these means. The fitted lookup is frozen, no online updating. July uses training July mean and January training January mean in the new monthly version, but not the original constant. Month×hour also matches UTC valid hour.

## Scores on3939 matched hourly regional-mean test targets
| Forecast | RMSE mm/h | Difference from q07 overall refit |
|---|---:|---:|
|Climatology: global mean|0.273693|+0.000000|
|Climatology: diurnal (hour)|0.273760|+0.000067|
|Climatology: seasonal (DJF..SON)|0.273018|-0.000674|
|Climatology: monthly|0.272957|-0.000736|
|Climatology: month x hour|0.273057|-0.000636|

AR(1) RMSE0.262659; RidgeL1 RMSE0.249733.19CSV fields checked against current main. No new fitted baseline or training executed. q07/q07b scripts, metric CSVs, paired CSVs and logs read from d02519c5f153feb712018cf97efb035f6ca2d7ae; hashes/path index saved. q07 logs explicitly record target counts/alignment; q07b uses training scaling and validation-selected Ridge regularization. Existing single saved model scores and paired comparisons remain distinct from Table3 five-seed summaries.

q07's `best_clim=min(CLIMS,key=testRMSE)` is a post-test descriptive choice (monthly); its Skill_vs_best_clim and paired-to-best columns are not a pre-specified reference and are not used as such in the reply. The current manuscript specifies month×hour as the reported SS denominator and has separate Skill_vs_month_x_hour evidence. We found no contemporaneous pre-registration document for selecting that denominator and make no stronger historical claim. Monthly/seasonal gains are small descriptive differences, not a test of no seasonality. No new seasonal inference or season-normalized RMSE analysis is claimed.

## Existing presentation and minimal changes
Table2 is architecture configuration, not a reference-score table. Table3 already retains original climatology/persistence; Table4 (`tab:strong_baselines`) completely lists the five q07 climatologies and state/linear references on matched samples with fit/sample/run-set caveats. §3.3.1 (`sec:benchmark_models`) defines original and conditional means; §4.2.1 (`sec:stronger_baseline_results`), not historical §4.1, contains actual scores. Supplementary S1/S2 (`stab:ridge_rmse`, `stab:ridge_auc`) support q07b paired evidence; seasonal performance tables support a separate question. No new/modified table, figure or main paragraph is necessary.
Only Response letter.tex R3 Lines341–344 AuthorResponse/ManuscriptChange plus2exact existing-text EvidenceBoxes changed. Full English response below. R1-M2 and R3-01–10 response blocks, entire manuscript/Supplementary/bibliography and allFigures unchanged. Huber response untouched. No staging/commit/push; index unchanged.

## Verification
Original137excerpts unchanged in order/content;2new exact extracts;139/139 match current main/Supplementary. Allrefs resolve to actual labels. Three ordered PDF builds passed:main102,Supp64,reply87pages; main/SuppPDF hashes identical to pre-task build. Main19/52 and reply69/70 actually rendered and inspected, correct red response/blue extracts, no clipping/overlap. No undefined citation/ref, duplicate label, horizontal overflow or blocking error. Existing main1.41457pt template output-vbox warning persists; no new warning type; reply/Supp no overfull warnings.

## Scientific limits
Aggregate conditional-climatology RMSE cannot prove absence of seasonal variability, cannot replace seasonal normalized evaluation, and cannot establish all learning models outperform stronger state/linear references. R1-M2's qualified Ridge conclusions remain intact. Same region/fixed chronological split; simple conditional means do not represent all possible seasonal forecasting strategies. Original design rationale and a pre-registration history are not independently documented. No blocking scientific conflict detected.

## Final English response (full LaTeX)

The original climatology was not seasonally dependent: it used one overall training-period mean for every forecast, so July and January received the same constant. It was a simple reference, not a month-specific climatology; we found no separate documented design rationale for preferring it to a seasonal reference.

We have added training-fitted UTC-hour, seasonal (DJF/MAM/JJA/SON), monthly and month-by-hour climatologies (Section~\ref{manuscript-sec:benchmark_models}). In the monthly version, July forecasts use the training-period July mean and January forecasts the training-period January mean; month-by-hour forecasts additionally match UTC hour. The fitted means remain fixed during validation and testing.

Table~\ref{manuscript-tab:strong_baselines} already reports their RMSEs on the same 3,939 test targets: 0.273760, 0.273018, 0.272957 and 0.273057~mm\,h$^{-1}$, respectively, versus 0.273693 for the refitted overall mean. This refit uses 18,404 training targets and is distinct from the original saved constant in Table~\ref{manuscript-tab:seed_stability}, fitted to 18,410 raw training values. Thus seasonal/monthly conditioning changes overall RMSE only slightly here; the comparison is no longer based solely on the original constant. The reported skill-score denominator is month-by-hour climatology, not whichever climatology minimizes test RMSE. Section~\ref{manuscript-sec:stronger_baseline_results} also retains the stronger statistical references and their qualified conclusions. These aggregate scores do not imply an absence of seasonal precipitation variation or replace season-specific evaluation.
