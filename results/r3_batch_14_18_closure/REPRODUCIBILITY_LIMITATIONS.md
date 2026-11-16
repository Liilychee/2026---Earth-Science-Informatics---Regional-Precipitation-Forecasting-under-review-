# Reproducibility limitations

- The repository archives incremental evidence, scripts, statistics and patches, not full paper sources. Rebuilding the R3-14…R3-18 text requires external full-text base files matching BASE_AND_AFTER_HASHES.json (base = R3-13 archived after-state).
- R3_14_18_CUMULATIVE.patch and the per-task *_SOURCES.patch files apply to that external base; they contain no R3-19 or R4-M1 changes.
- Several predictions used by these items are already archived elsewhere (results/q14, q18, q21, q10, q13 outputs; results/metrics/q04_pairs.csv, results/xgboost_preds.csv, results/ablation/q03d_seasonal_xgb_test_preds.csv) and are referenced, not duplicated. The merged 30-year raw CSV and raw ERA5 grids are not archived (R2-M9).
- Recorded training times are not a controlled computational benchmark; inference cost was not measured.
- Full repository-only reconstruction of the paper is not available.
