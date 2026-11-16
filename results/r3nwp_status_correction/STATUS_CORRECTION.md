# R3-13 (Reviewer 3, Section 3.3.1) — status correction

**New status: CLOSED — qualified operational NWP comparison; matched-target limitation disclosed.**

Decision (author, 2026-11-16, option C): the existing q08 comparison answers the reviewer's request for an operational NWP reference; the absence of a strictly matched-window HRES product is a disclosed limitation, not an unanswered comment.

## Evidence (unchanged; archived in 8f9c52ff3661f73a0f8a27cf86c4aeda09d793c3, results/r3nwp_integration/)
- 1,970 common targets at 06/18 UTC, 22 April 2019 – 31 December 2021 (HRES initialized 00/12 UTC, +6 h, same 25-cell box).
- RMSE against the final-hour ERA5 target (q08_hres_comparison.csv): HRES six-hour mean 0.2061, BiLSTM-Attention 0.2428, XGBoost 0.2443 mm h⁻¹ (six saved learning forecasts 0.2428–0.2622).
- ERA5 six-hour-mean diagnostic: 0.1882 mm h⁻¹ (0.18824165…).
- Independent Dublin Airport station comparison (q08b) and event AUC (q08c).

## Limitations retained (manuscript §4.2.2/§5.4, Supplementary S3–S6/S60 and the formal reply are unchanged)
1. HRES supplies a six-hour accumulation converted to a mean rate; the learning models predict the single final hour, so the target windows differ.
2. The 0.1882 value uses post-origin verifying ERA5 information; it is a diagnostic, not an available forecast and not a strict error lower bound.
3. HRES has lower RMSE in this comparison, but this does not establish that it would remain better under a strictly matched target window.
4. No claim that the learning models outperform operational NWP; the window mismatch and shared-IFS (ERA5/HRES) limitations remain.
5. No hourly HRES download or retraining was performed for this revision.

## Scope of this correction
- No change to experimental data, numbers, manuscript, Supplementary, response letter or any EvidenceBox excerpt.
- Historical archived records stating "R3-13 OPEN" are not rewritten; this record supersedes their status line:
  - results/r3_batch_07_13_closure/{STATUS.md, CLOSURE_MANIFEST.md, SCIENCE_AUDIT.md, FINAL_REPORT.md, FINAL_REMOTE_RECEIPT.json (local)}
  - results/r3nwp_integration/STATUS.md
  - results/r3_batch_14_18_closure/{CLOSURE_MANIFEST.md, BATCH_VERIFICATION.json, FINAL_REMOTE_RECEIPT.json (local)}
- Tracking-file notes are provided as CLOSURE_STATUS.patch (original files not edited).
- R3-19 is unaffected and remains a separate item.
