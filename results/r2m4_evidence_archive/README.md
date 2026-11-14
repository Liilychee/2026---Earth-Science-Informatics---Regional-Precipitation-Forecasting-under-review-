# R2-M4 evidence preparation

Status: evidence verified and archived; R2-M4 is NOT closed. No LaTeX changes.

Canonical new evidence: `code/analysis_r2m4_fixed_paired_ci.py`, `results/metrics/r2m4_fixed_event_paired.csv`, `results/metrics/r2m4_fixed_event_scores.csv`, `results/metrics/r2m4_fixed_output.txt`.

Read METHOD_AUDIT.md before using the p-value/Holm columns: the p-values are bootstrap sign-tail approximations, not null-constrained resampling p-values; the high24 family was chosen after inspection. Holm arithmetic was verified but confirmatory FWER control was not established. Original outputs are preserved without edits.

SOURCE_MANIFEST.json records MD5/SHA256 and protected LaTeX hashes. VERIFICATION.json records the read-only reproduction, including 300-grid q05e confirmation and the 36-family sensitivity exception. verify_evidence.py performs evidence checks without fitting models or overwriting source outputs; it uses the local Downloads copies and archived Git inputs.
