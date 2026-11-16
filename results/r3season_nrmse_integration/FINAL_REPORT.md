# R3-15 (R3 Section 4.1: seasonal RMSE normalized by seasonal climatological mean)

## Handover
- Codex (20:46–21:28): copied q13/q06 sources and outputs to evidence/ (SOURCE_INDEX.json, archive commits d02519c/395234e); snapshot before/ (== R3-14 after-state; confirmed byte-identical to current sources at takeover); independently re-verified saved q13 metrics and paired intervals from the 30 q14 prediction files read via `git show` (verify_saved.py → SAVED_RESULTS_CHECK.json, INDEPENDENT_PER_SEED.csv, PAIR_RECHECK.json; max errors 7.5e-14 metrics, 3.7e-8 pairs). No manuscript/Supplementary/letter edits had been made.
- Claude: one further independent spot check (denominators 2.6e-15; RMSE/SD/NRMSE 6.8e-14); integration; verification. Codex files left untouched; Claude files prefixed CLAUDE_ or R3_15_.

## Definitions (q13_seasonal.py)
NRMSE_s = RMSE_s / mean training precipitation of season s (18,410 raw training timestamps 2004-01-01 00:00–2016-08-07 06:00; n 4,572/4,784/4,686/4,368). Sensitivity: test-period seasonal mean. SS = 1 − RMSE/RMSE_clim(month×hour, training-fitted). Predictions: q14 W=6 five-seed reruns, six models (not the main-table run set; not q08). Paired intervals: seed-t (df 4) and non-circular moving blocks of 28 within each concatenated seasonal subsequence, 5,000 replicates, seed 42.

## Changes
- manuscript §4.2.3 (sec:seasonal_baseline_check): one \revminor paragraph (pure insertion).
- Supplementary: new final section "Seasonal normalized RMSE": S64 stab:r3season_nrmse, S65 stab:r3season_clim_pairs (pure append; S1–S63 and Figs S1–S4 unchanged).
- Response letter: R3 Section 4.1 reply, location box, one EvidenceBox (block only).
## Checks
60/60 table rows match the saved CSVs; paragraph numbers match; 147 old excerpts verbatim + 1 = 148/148; bib unchanged; three PDFs compile with 0 undefined/multiply defined/overfull (manuscript 105, Supplementary 75, Response letter 91 pp).

## Follow-up (author)
S65 caption: replaced the gap-bridging clause with the author-approved limitation (season-filtered moving blocks may span discontinuities; intervals are conditional sensitivity estimates, not fully dependence-preserving). No recalculation; manuscript paragraph and reply unchanged. Recompiled: 0 undefined/overfull; pages 105/75/91.
