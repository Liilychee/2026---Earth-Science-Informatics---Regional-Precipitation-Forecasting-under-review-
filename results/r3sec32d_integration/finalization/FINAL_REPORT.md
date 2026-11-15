# R3-07 final local integration

Status: LOCAL_SCIENTIFIC_INTEGRATION_COMPLETE — GIT_ARCHIVING_DEFERRED.

## Changes
- Supplementary.tex: replace the sole R3-07 TODO with the author's unchanged final PDF, native width 119.0 mm (337.3228 x 221.1024 pt); red caption; label `sfig:r3d_upstream_effects`.
- manuscript.tex §5.4 (PDF p.86): C3 vs C0 now cites S26/S27; conditional comparisons cite S52 and Fig. S3.
- Response letter.tex: only Section 3.2(d) reply/location/one EvidenceBox updated for those references. Reply pp.64–65. Approved wording and scientific results retained.
- sn-bibliography.bib unchanged. All old figure PDFs and table environments unchanged. Git index unchanged; no commit/push.

## Figure and numerical checks
Fig. S3 is Supplementary p.60. Source: Figures/r3M7_upstream_effects.pdf; MD5 `492642ca839946d6a9778bb1040cf96b`. Native insertion, no image editing or scaling.
Ten percentages independently matched saved q21_effect.csv: XGBoost -6.43/-6.37/-1.82/-0.06/-4.70%; BiLSTM-Attention -6.95/-5.36/-3.33/-1.69/-3.75%.
All ten point locations and twenty interval segments (two intervals each) independently compared using PDF vector coordinates to saved q21 values; differences below 1e-7 mm/h (PDF coordinate precision). See FIGURE_CELL_INDEX.json and FIGURE_VECTOR_CHECK.json. No formal statistic recomputed.
S26/S27/S51/S52 remain pp.21/22/58/59 and figures S1/S2/S3 remain correctly numbered. Existing table source environments unchanged.

## Evidence and PDF verification
130 protected excerpts byte-identical in order; only R3-07 excerpt updated; 131/131 effective-text matches current main/Supplementary. Other reviewer responses unchanged. See VERIFICATION.json.
Built manuscript, Supplementary, then manuscript again to refresh external references, then response. Final page counts: 100/60/83. Actual rendered main86, Supp60, reply64–65 inspected: readable, uncropped, correct red/blue and references.
No undefined citation/reference, duplicate label, horizontal overflow or blocking error. The manuscript retains the existing repeated 1.41457pt output vbox template warning; therefore a literal zero-overfull condition is not claimed. Supplementary and response have no overfull warnings. This is the only remaining layout qualification; no new blocking issue found.

R3-07 local scientific integration completed. Git archiving deferred.
