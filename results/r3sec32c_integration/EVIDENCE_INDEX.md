# R3-06 evidence index

- q21 sources (copies): evidence/q21_effect.csv, q21_summary.csv, q21_runs.csv, q21_build_output.txt, q21_repro_output.txt, q21_build_features.py, q21_train.py, q21_stats.py, 04-21_README.txt (z500 = geopotential, m**2 s**-2; tcwv kg m**-2).
- Prediction/run files (tracked in esi_github results/q21): SHA-256 in evidence/Q21_SOURCE_HASHES.json (C0/C1/C2, both models, five seeds).
- Cell tracing: CELL_INDEX.json — all 12 table rows independently recomputed from the prediction files (seed-t df 4; moving block 28, 5,000, seed 42).
- Excerpts: EXCERPT_INDEX.json (129 + 1 = 130), VERIFICATION.json, VERIFICATION_DETAIL.json.
- Increment: R3S32c_LOCAL/PORTABLE.patch; PATCH_RECONSTRUCTION.json; DOCUMENT_HASHES.json.
- Protection: PROTECTED_HASHES.json, ORIGINAL_WORKTREE_GUARD.json, GIT_STATE.json, GIT_STATUS.txt.
- R3-05 post-closure delta (separate item): r3_05_post_closure_delta/.
- Build/layout: PDF_CHECK.json, compile_*.txt, render/.
