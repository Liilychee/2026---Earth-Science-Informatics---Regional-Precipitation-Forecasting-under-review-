# R3-14 final local scientific report

**R3-14 local scientific revision complete — Git archiving deferred.** Author review pending; not formally CLOSED or remotely archived. No training, downloads, staging, commit or push. R3-13 remains OPEN and its NWP limitations are unchanged.

## Three reviewer questions

A. The protected training Q95 definition is retained:0.5740 mm h⁻¹ comes from18404 regional-mean hourly training targets on the original scale. It is a statistical upper-tail cutoff, not a physical extreme-rainfall classification. The WMO3-minute classification and region/hour support difference remain intact. Wet≥0.1, legacy>0 and≥1 event diagnostics are kept separate; no universal “below1 means no rain” rule is adopted.

B. Existing q03d tests G/S/F with identical base hyperparameters, variables, chronological split and five seeds42/123/7/2024/99, no seasonal retuning. G/S each have42 meteorological inputs (six snapshots×seven variables); F adds four sine/cosine calendar features for the target month/hour. Training windows:DJF4566/MAM4784/JJA4686/SON4368; common3939 test targets. Model labels and run set are distinct from q13 and the main performance table. No evidence of consistent seasonal-specialization gain under these tested settings; no claim of general ineffectiveness and no extension to deep-model seasonal retraining.

C. The existing historical CDF is scientifically useful but uses26282 post-window targets, not all26300 retained timestamps. Its18 exclusions are exactly the first six timestamps in each partition (listed in OMITTED_18_TIMESTAMPS.csv). A new corrected FigureS4 uses the complete sampled archive; old figure/script/CSV preserved byte-for-byte in evidence and existing Git objects. No existing evaluation target or score changed.

## Full-period seasonal CDF

Source: existing regional table MD5 `f9b4f8a22c8b7849f40eb71918fe1fd6`; all26300 unique, uninterrupted six-hourly timestamps from2004-01-01 00:00 through2021-12-31 18:00 UTC. These are preceding-hour amounts (mm, numerically mm h⁻¹) spatially averaged over25 cells, sampled at00/06/12/18UTC: **not all24 daily hours and not six-hour accumulated rainfall**. Regional values were cross-checked against archived q04 pairs at all timestamps, maximum difference1.01e-13mm. Original raw gridded ERA5 file was not newly read or downloaded; the regional dependency matches prior R2-M7's audited MD5.

FigureS4 uses unconditional all-sample ECDFs with exact zeros retained, plus P(Y≥y) on a log scale; ties are handled separately from P(Y≤y). Both panels cover the full observed intensity range0–4.13454, axes extend to4.3. No wet-only conditioning. TrainingQ95 stays fixed; seasonal full-period quantiles are descriptive only.

| Season | N | Exact zeros | Wet≥0.1 (%) | ≥1 (%) | Q95 mm h⁻¹ | Max mm h⁻¹ |
|---|---|---|---|---|---|---|
| DJF | 6500 | 829 | 19.9846 | 2.4923 | 0.619711 | 3.419266 |
| MAM | 6624 | 1681 | 19.4444 | 1.2379 | 0.457459 | 2.867031 |
| JJA | 6624 | 1237 | 21.7844 | 2.1437 | 0.587696 | 3.940315 |
| SON | 6552 | 964 | 20.3449 | 2.9762 | 0.672553 | 4.134541 |

Original historical seasonal counts6494/6618/6618/6552 become6500/6624/6624/6552. The rounding to two decimals remains approximately.62/.46/.59/.67; the actual four-decimal updated values are.6197/.4575/.5877/.6726. Complete ECDF points/counts/denominators are saved in FULL_PERIOD_ECDF.csv. The new figure uses shared fig_style geometry/size constants and Latin Modern, native119.0×132mm, minimum base/tick8pt. The local machine lacks dvipng/Poppler binaries, so PGF/pdflatex renders the same typography; embedded fonts verified as Latin Modern. This is disclosed in FIGURE_CHECK.json. It is inserted without width scaling.

## q03d complete comparison

All105 seed×strategy×subset rows checked against21 summary rows. Below are seed-mean RMSE±sampleSD in mm h⁻¹. Full MAE/SS means and SD are in S62 and the source CSV; S10/S11 remain unchanged.

| Subset | N | G | S | F |
|---|---|---|---|---|
| all | 3939 | 0.2439 ± 0.0002 | 0.2468 ± 0.0010 | 0.2443 ± 0.0005 |
| DJF | 848 | 0.2819 ± 0.0020 | 0.2811 ± 0.0011 | 0.2806 ± 0.0014 |
| MAM | 895 | 0.1731 ± 0.0011 | 0.1707 ± 0.0013 | 0.1724 ± 0.0011 |
| JJA | 1104 | 0.2467 ± 0.0015 | 0.2497 ± 0.0015 | 0.2443 ± 0.0010 |
| SON | 1092 | 0.2585 ± 0.0012 | 0.2673 ± 0.0021 | 0.2637 ± 0.0018 |
| wet>=0.1 | 854 | 0.4735 ± 0.0011 | 0.4784 ± 0.0023 | 0.4746 ± 0.0016 |
| tail>=Q95 | 238 | 0.8428 ± 0.0020 | 0.8476 ± 0.0041 | 0.8432 ± 0.0029 |

### S_minus_G

| Subset | Seed mean Δ | Seed SD | Worse seeds | Mean-prediction Δ | 95% block CI |
|---|---|---|---|---|---|
| all | 0.0029 | 0.0008 | 5/5 | 0.002 | [-0.0012, 0.0056] |
| DJF | -0.0009 | 0.0024 | 3/5 | -0.0013 | [-0.0103, 0.0074] |
| MAM | -0.0024 | 0.0013 | 0/5 | -0.0025 | [-0.0074, 0.003] |
| JJA | 0.003 | 0.0016 | 5/5 | 0.0023 | [-0.0011, 0.0059] |
| SON | 0.0088 | 0.0029 | 5/5 | 0.0071 | [-0.0005, 0.0148] |
| wet>=0.1 | 0.0049 | 0.0029 | 5/5 | 0.0037 | [-0.0032, 0.0111] |
| tail>=Q95 | 0.0047 | 0.0056 | 4/5 | 0.0041 | [-0.0093, 0.0184] |

### F_minus_G

| Subset | Seed mean Δ | Seed SD | Worse seeds | Mean-prediction Δ | 95% block CI |
|---|---|---|---|---|---|
| all | 0.0004 | 0.0007 | 3/5 | 0.0004 | [-0.0011, 0.0018] |
| DJF | -0.0013 | 0.0019 | 1/5 | -0.0013 | [-0.0038, 0.0013] |
| MAM | -0.0008 | 0.0003 | 0/5 | -0.0007 | [-0.003, 0.0013] |
| JJA | -0.0024 | 0.0024 | 1/5 | -0.0025 | [-0.005, -0.0004] |
| SON | 0.0052 | 0.0011 | 5/5 | 0.005 | [0.0022, 0.0079] |
| wet>=0.1 | 0.0012 | 0.0017 | 4/5 | 0.001 | [-0.0015, 0.0033] |
| tail>=Q95 | 0.0004 | 0.003 | 1/5 | 0.0004 | [-0.0048, 0.0051] |

**Estimands:** +.0029 is mean seed-level S−G RMSE; +.0020 and its[-.0012,+.0056] interval score seed-averaged predictions. F SON+.0052(seed-score mean) differs from+.0050(mean-prediction statistic). Neither pair may be interchanged. Seed SD captures fitted-run variation, not a seed-t CI (none saved by q03d). Conditional sample-bootstrap intervals do not combine both uncertainty sources.

All14 mean-prediction point estimates and percentile intervals were independently recomputed using the saved3939-row prediction-mean CSV; all match the archived four-decimal output. Circular blocks28,2000replicates,seed42;141 complete blocks produce3948positions, then truncated to3939. Same sampled indices for all strategies, subset masks applied after sampling. The q03d implementation therefore differs from untruncated noncircular q13/q14 procedures. Intervals are pointwise, unadjusted. The run log records these settings; no new model fit occurred.

S−G all seasonal intervals include zero. F improves JJA and worsens SON on this ensemble-prediction sampling scale, without multiplicity adjustment. Overall both S/F intervals include zero. Seasonal wet/tail score rows are also retained. These findings justify retention under the tested conditions, not proof that seasonal models cannot help.

**Evidence limitations:** individual q03d seed prediction files/weights are not present in this archive; all105 original raw metrics and their aggregation/direction counts were verified, but individual seed predictions cannot be independently regenerated without retraining. The saved five-seed mean predictions suffice for all14 paired bootstrap checks. Hyperparameters were not retuned by season, and deep models were not seasonally retrained. Short test-period seasonal coverage remains a limitation. No causal explanation for specialization gains/losses is claimed.

## Documents and table/figure registry

Main §4.2.3 adds two red paragraphs (full distributions and G/S/F interpretation); §5.4 adds one red paragraph (scope/uncertainty). Existing paragraphs are byte-identical after removal of these additions. No change to Abstract, Conclusion, original model settings or saved results.

S61 (`stab:r3season_full_distribution`) p69:4 seasonal rows. FigureS4 (`sfig:r3season_full_cdf`) p70:corrected full-period distribution. S62 (`stab:r3season_gsf_scores`) p71:21 G/S/F subset score rows. S63 (`stab:r3season_gsf_pairs`) p72:14 paired comparison rows. These expand the previously partial G/S presentation without altering S10/S11 or any S1–S60 content.

Response letter: only R3 Lines469–471 replaced; original comment unchanged, formal response red,3new exact excerpts and location notes blue. Task03/registry/checklist appended only for R3-14; other shared opinions retain prior states. Source locations are in LOCATIONS.json. Final published page/line annotations remain deferred.

## Final verification

-255 new tabulated CSV fields,39 data rows validated at exact destination rows;14 bootstrap comparisons reproduced to archived precision. PROSE_FACT_INDEX.json maps added narrative numbers and settings.
-144 old RevisedExcerpt arguments byte-identical and all match latest sources;3new match,147/147 total. BEFORE_AFTER_EXCERPT_MAP.json records content hashes and stable matches, not only line numbers.
-All other reviewer response blocks byte-identical, including R1-M2/R3-09/R3-11/R3-12/R3-13. Original main tables/figures and all original main paragraphs retained. S1–S60/Fig.S1–S3 source prefix and17 prior figure files unchanged. Bibliography unchanged.
-Three PDFs built in Supplementary→manuscript→Response order:104/72/91pages. No undefined references, duplicate labels, blocking errors, horizontal overflows or oversized floats. The pre-existing manuscript1.41457pt output-vbox warning repeats103times due to its104-page pagination; no new warning type. Supplementary/reply have no overfull warnings.
-Actual rendered checks:main56/93, Supplementary69–72, reply73–76. New graph and tables complete, legible and uncropped; no overlap; red/blue markings correct. PDF_CHECK.json contains hashes and visual results.
-Git index unchanged; no stage/commit/push. Original workspace's unrelated changes retained. R2-M9 repository-documentation pending state and R3-13 OPEN retained. Not proceeding to Reviewer3 Section4.1.

## Formal English reply (readable reference numbers)

We agree that Q95=0.5740 mm h⁻¹ is a relative upper-tail threshold for regional-mean hourly ERA5 precipitation, not a meteorological extreme definition. It is the untransformed 95th percentile of 18,404 training targets. The existing Methods discussion distinguishes it from WMO's intensity classification and its different temporal/spatial support. We use wet ≥0.1 mm h⁻¹, with >0 retained only as a labelled legacy diagnostic; rainfall below 1 mm h⁻¹ is not treated as universally dry.

Supplementary Fig. S4 now shows unconditional four-season CDFs and upper-tail exceedance curves for all 26,300 retained 00/06/12/18 UTC timestamps in 2004--2021, including zeros. The earlier figure used 26,282 windowed targets, omitting six initial timestamps per partition; we corrected that scope while preserving the old figure. The seasonal Q95 values are 0.6197/0.4575/0.5877/0.6726 mm h⁻¹ in DJF/MAM/JJA/SON (Table S61); these full-period descriptions do not change the training event threshold.

We also report the existing five-seed XGBoost comparison of year-round (G), four seasonal (S) and year-round calendar-augmented (F) models, with identical meteorological inputs, splits and hyperparameters and no retuning (Tables S62 and S63). Overall mean seed-level RMSE is 0.2439/0.2468/0.2443 mm h⁻¹. The S--G mean seed-level difference is +0.0029 (5/5 worse), but its block interval belongs to the distinct five-seed-mean-prediction difference +0.0020 $[-0.0012,+0.0056]$. F--G is +0.0004 $[-0.0011,+0.0018]$ on the latter scale. Seasonal S--G intervals all include zero; calendar augmentation improves JJA and worsens SON with pointwise intervals excluding zero. These unadjusted, conditional intervals do not combine training and sampling uncertainty.

We therefore retain year-round models and evaluate them by season, without claiming that seasonal modelling is generally ineffective. The experiment tests only fixed-configuration XGBoost, with smaller seasonal training sets, not season-specific deep models or retuning. Existing seasonal variable-ablation and climatology results remain separate.


## Deliverables

- R3_14_LOCAL.patch: current local manuscript/Supplementary/reply and task-record increment; not applied to original tree twice.
- CELL_INDEX.json / ROW_INDEX.json / PROSE_FACT_INDEX.json / SOURCE_INDEX.json / LOCAL_DEPENDENCY.json.
- SAVED_RESULTS_CHECK.json / BOOTSTRAP_RECHECK.json / EXCERPT_INDEX.json / BEFORE_AFTER_EXCERPT_MAP.json / VERIFICATION.json.
- FULL_PERIOD_SEASON_STATS.csv / FULL_PERIOD_ECDF.csv / OMITTED_18_TIMESTAMPS.csv.
- verify_saved.py and its log; plot_full_season_cdf.py and its log; check_integration.py; FIGURE_CHECK.json; PDF_CHECK.json; GIT_STATUS.txt.
- Figures/r3M14_season_cdf_full.pdf (old figure retained). Compiled submission PDFs stay in build/, not uploaded.

**No blocking scientific issue found for this bounded R3-14 response.** Reproduction limits above remain explicit; Git archive deferred pending author review.
