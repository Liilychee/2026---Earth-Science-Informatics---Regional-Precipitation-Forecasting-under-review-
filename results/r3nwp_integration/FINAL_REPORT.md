# R3-13 — ECMWF/NWP reference

Status: R3-13 local revision integrated — Git archiving deferred.
The strictly matched-window operational forecasting comparison remains unavailable. This is not a claim that the core equivalent-window benchmark has been completed or that R3-13 is scientifically CLOSED.

## Initialization, spatial support and accumulation window
| Component | Origin / valid time | Precipitation support |
|---|---|---|
| Saved HRES | 00/12 UTC, +6 h, valid06/18 UTC | Full (t0,t0+6h] accumulation, converted m→mm and divided by6h |
| Learning forecasts | Same origins/leads/valid times | Final hour (t0+5h,t0+6h] only |
| ERA5 verification | Same valid time | Regional-mean final-hour saved y_true |
| ERA5 six-hour diagnostic | Same ending time | Verifying (t0,t0+6h] amount divided by6; post-origin information |
| Airport verification | Same valid-time indices | Point rainfall; physical accumulation-window certainty and quality limits remain those already documented for R1-M6 |

HRES download log identifies `datasets/hres/2016-2022-0012-1440x721.zarr`, selected leads[0,6]h; local box52.75–53.75N,353.25–354.25E(−6.75 to−5.75),5×5cells. ERA5 and HRES regional means are simple equal-cell means, not a new cosine-weighted calculation. Geographic averaging box matches, but this does not remove native model resolution, IFS framework or temporal-support differences.
The retrieved subset has no+5h or direct final-hour field. No strictly equivalent-window saved forecast from another product was located. This states the limit of the retrieved evidence, not that no such forecast exists in any ECMWF archive. The versioned source-store name and download/check logs are preserved; per-date operational IFS cycle identifiers are not present in the aligned CSV, so no frozen-model-version homogeneity is claimed. No new archive download attempted.

## Pairing and results
All 1,970 targets verified one-to-one:2019-04-22 06:00 through2021-12-31 18:00 UTC;985days,two times/day,12h gaps,no duplicates. Six saved learning series match the aligned CSV exactly. Original single-run identity retained; no five-seed claim (in particular, saved BUA is not its main seed42). All point scores/references were evaluated on this subset, with month×hour denominator0.2741794069163142 rather than the full-test value.
| Target | HRES RMSE | Six learning forecasts RMSE range |
|---|---:|---:|
|ERA5 final hour|0.206097|0.242850–0.262164|
|Dublin Airport hourly|0.437246|0.467753–0.474481|

On the ERA5 labels, all six archived paired RMSE intervals favour HRES; paired AUC intervals favour HRES in 18 learning-model/event comparisons at0.1,Q95,1.0. At the airport, paired RMSE intervals exclude0 only for XGBoost/Transformer, while all 12 AUC comparisons at0.1/1.0 favour HRES. No airport Q95 result inferred.
These are score comparisons of mismatched windows, not fair operational skill rankings. Main/supplementary retain all unfavourable outcomes without converting them into a stronger causal/operational conclusion.

Independent verification reproduced 23 point-score rows and 57 event-AUC/frequency-matched rows from saved per-case values; point-score max difference9.80118763926896e-17. All stored paired-AUC point differences and interval signs cross-checked; no bootstrap rerun. ERA5 exactQ95=0.574048 and code's rounded0.5740 identify the same116subset events. ERA5 wet/1.0 counts422/46 verified; station counts use its own target.
q08/q08b/q08c scripts and logs agree on non-circular moving blocks14successive12-hourly samples(~7days),10000replicates,seed42,paired indices; concatenate141completeblocks then truncate1974positions to1970. These are pointwise case-sampling intervals conditional on single fitted forecasts, without multiplicity correction or training-seed uncertainty. q08c frequency-matched cutoffs use observed event frequency in this test subset and are descriptive ranking diagnostics, not prospective warning thresholds. New S60 shows fixed-cutoff CSI, not that post-hoc frequency-matched rule.

## ERA5 verification-window diagnostic
Saved ERA5 six-hour mean RMSE0.18824165412226743 against the final-hour target is a descriptive mismatch diagnostic using post-origin verifying data. It is neither an available forecast nor a theoretical error lower bound, nor an experiment isolating a unique causal contribution of temporal smoothing. Legacy raw column `Perfect 6 h mean (ceiling)` is preserved in evidence but renamed clearly in the paper/table. HRES6hmean=stored6hamount/6 and ERA5diagnostic=stored6hamount/6 independently verified; no amounts changed.

## Existing versus added presentation
Existing actual §4.2.2andS3–S6 already contain HRES comparison, two verification targets and limitations. Existing Methods paragraph and §5.4 limits retained verbatim. No mainTable2/3 or earlierresults edited.
Added S60 `stab:r3nwp_common_context`, Supplementaryp68:11rows,66CSVfields for matched-subset errors,SS and fixed-ruleCSI, includingPersistence/month×hour/AR1 and the verification diagnostic. This supplies missing reference/diagnostic context without duplicating pairedCIs or modifyingS3–S6. No new figure necessary: new and existing table captions state the two windows explicitly.
Added one red paragraph at end of §4.2.2(mainp55), explicitly acknowledging missing+5h/final-hourNWP and forbidding a fair-ranking interpretation. Added onlyR3Section3.3.1formalresponse/location plus2exactblue excerpts. All otherresponses,originalmainprose/tables/figures,bibliography and earlierSupplementaryprefix unchanged. No stage/commit/push or next-comment work.

## Numerical provenance and parsing details
Fixed source Git object d02519c5f153feb712018cf97efb035f6ca2d7ae; script/log/CSV paths andMD5 inSOURCE_INDEX; per-series originals andMD5 inSAVED_RESULTS_CHECK; stationq04_pairs source hash inSTATION_SOURCE. No rawNetCDF re-download or new forecast generation.
Round-trip float parsing is used for per-case rank checks. The default parser merges/splits some near-equal Persistence values and gives tinyAUC differences(up to2.33e-6); round-trip/legacy parsing reproduces storedAUC. q08c's airport ERA5-label ranking uses q04 `era5_regional_mm`, whereas q08b's score row uses saved y_true; these series are near-equal but cannot be silently substituted in exact rank verification. Using the actual script-specific sources reproduces allreported AUCs. None of these details alters the learning-model/HRES conclusions or original data.

## EvidenceBox and PDF validation
The original 142 RevisedExcerpts unchanged in order/content; two new exact extracts; 144/144 match. PreviousR1andR3responses protected. Allrefs resolve; originalFigures and oldtables unchanged. SeeVERIFICATION/EXCERPT_INDEX/LABEL_INDEX.
Ordered Supplementary → manuscript → response builds pass. Final page counts 68/103/90. Actual main 55, Supplementary 68 and response 72–73 rendered and inspected:readable, correct red/blue, no cropping, missing references or overlaps. No undefined reference/citation, duplicate label, horizontal overflow, oversized float or blocking error. The existing main output-vbox warning (1.41457 pt, 102 instances) persists; no new warning type. Strict same-window NWP comparison remains an acknowledged scientific limitation, not a closed empirical claim.

## Final English response (full LaTeX)

We agree that a physical numerical forecast is an important reference. The revised manuscript already includes an exploratory comparison with archived ECMWF IFS HRES forecasts, rather than relying only on persistence and climatology (Section~\ref{manuscript-sec:hres_reference_results}; Supplementary Tables~\ref{supp-stab:hres_era5_rmse}--\ref{supp-stab:hres_station_auc}).

There are 1,970 paired targets at 06/18~UTC, from 22 April 2019 to 31 December 2021. HRES is initialized at 00/12~UTC with a +6 h lead, matching the learning-model origins and leads, and uses the same 25-cell study box. Crucially, HRES supplies the six-hour accumulation divided by six, while the learning models predict only $(t_0+5\,\mathrm{h},t_0+6\,\mathrm{h}]$. These are different temporal supports. The saved subset lacks +5 h forecasts, so we cannot reconstruct a strictly matched final-hour NWP forecast. We do not present the comparison as a fair operational skill ranking.

Against the final-hour ERA5 target, HRES RMSE is 0.2061~mm\,h$^{-1}$ versus 0.2428--0.2622 for the six saved learning forecasts; the paired intervals favour HRES on these labels. HRES also has higher AUC at wet, Q95 and 1.0~mm\,h$^{-1}$ thresholds. Airport-target comparisons retain the window and point-to-area differences: HRES has higher AUC for all six models at the two evaluated station thresholds, but its RMSE advantage is supported only against XGBoost and Transformer. These are single saved forecasts, not five-seed averages.

The new Supplementary Table~\ref{supp-stab:r3nwp_common_context} includes persistence, training-fitted month-by-hour climatology and AR(1), rescored on the common subset. It also identifies the ERA5 six-hour mean as a verification-window diagnostic, not an available forecast or an error bound. Section~\ref{manuscript-sec:limitations} retains the shared IFS framework, temporal-window and spatial-support limitations. The results do not establish NWP competitiveness, computational advantage or the models' superiority to an equivalent-window operational forecast; that stricter comparison remains unavailable.
