# Follow-up for R2-M9 final reproduction materials (registered here; R2-M9 records not modified)

q06 / 30-year rolling-origin evidence availability, checked 2026-11-15:
- Archived and verifiable: q06_yearly_summary.csv (1992-2021, 30 years, 43,832 timestamps); fold definitions F1-F4, F4s, ORIG (q06/folds/*.json: periods, window counts, target-time ranges, fold training Q95); 150 fold runs + 3 reproduction runs (q06/runs/*.json); 153 prediction files with y_true and persistence (q06/preds/*.csv, also tarball); summary CSVs (fold metrics, history effect, rank stability, pairwise, coverage); execution logs (results/metrics/q06_*_output.txt).
- NOT archived locally or in the evidence repository: the merged raw 30-year regional series data/q06/dublin_regional_1992_2021.csv. Consequently climatology/AR(1) fits and per-fold screening can only be checked against archived outputs, not recomputed from raw data.
- Action for R2-M9 final repository documentation: either archive this CSV (size/licence permitting) or document how to rebuild it from CDS ERA5 with q06_build_regional.py, with a checksum.
