# R3 Section 3.2(c) (R3-06) — Local integration report

Baseline: remote main dc72acc4e138c4675f81559f71564df562090fd1 (verified); paper HEAD ae4cd53, index 1d0b3404… unchanged, nothing staged. No training or download.

## R3-05 version protection (separate item)
Closed R3-05 Response letter (archive 7faac6b/dc72acc) sha256 44f89086…; local version before R3-06 e14c0f89…. The only difference is the R3 Section 3.2(b) AuthorResponse (author-instructed simplification): closed f35ca4bb… → local b4652891…; ManuscriptChange and EvidenceBox unchanged. Recorded in r3_05_post_closure_delta/ (closed copy, delta patch, JSON with full local text). Not overwritten, restored or rewritten; not part of R3-06. R3-05 stays CLOSED; the simplification awaits its own version archive.

## Changes
| File | Change |
|---|---|
| manuscript.tex | §4.1 (sec:predictor_selection_results): new `\revminor` paragraph after the C6 results (author-approved text; "Table X" → `Supplementary Table~\ref{supp-stab:r3c_local_additions}`). Pure insertion. |
| Supplementary.tex | New red final section "Local wind speed and large-scale predictors" with Table S51 (`stab:r3c_local_additions`), appended before `\end{document}` so that all 50 existing table numbers stay unchanged. Pure insertion. |
| Response letter.tex | R3 Section 3.2(c) only: Pending/ChangeLocation replaced by red reply, location box and one blue EvidenceBox. |
| sn-bibliography.bib | unchanged |

Placement note: inserting the table after the R2-M3 upstream tables would have renumbered 23 closed tables (S28 onward); the end-of-document section avoids this.

## Table S51
C0/C1/C2 × XGBoost/BiLSTM-Attention × All (3,939)/Wet (854)/Upper tail (238): C0 and configuration RMSE, paired ΔRMSE, Δ%, seed-t interval, moving-block interval, improve count. Values from q21_effect.csv (Δ, intervals, counts, C0 RMSE) and q21_summary.csv (configuration RMSE); all 12 rows independently recomputed from the 60 saved prediction files (match within display rounding). Caption covers C0/C1/C2 definitions, ws per-cell computation, z500 geopotential m² s⁻² (not converted), tcwv kg m⁻², common test targets, seed vs test-sampling uncertainty, no multiplicity adjustment, scope (two models, original split), and non-separability of z500/tcwv.

## Key values
- C1 (+ws): XGB −0.000457 (−0.19%, 4/5), BiAttn +0.000100 (+0.04%, 2/5); intervals include zero.
- C2 (+z500, tcwv): BiAttn −0.002858 (−1.177% → "1.18%"), 5/5, seed-t [−0.004084, −0.001632], block [−0.005183, −0.000442]; XGB −0.000126 (−0.05%, 2/5), intervals include zero.

## Reply
Covers: ws computed and tested, no clear gain; joint local z500+tcwv: BiAttn −1.18% with both intervals excluding zero, no clear change for XGB; joint result not attributable to either variable; original candidate pool limited; upstream predictors deferred to comment (d). No claim that z500 or tcwv lacks predictive value.

## Verification
- EvidenceBoxes: 129 unchanged verbatim and in order + 1 new = 130/130 match; R3-05 local reply hash preserved.
- Response letter unchanged outside the 3.2(c) block; closed R2-M3 tables byte-identical; 961 protected files unchanged.
- Compile: 0 undefined/multiply defined/overfull. manuscript 99 pp; Supplementary 58 pp (+1); Response letter 83 pp (+1).
- Rendered: manuscript p46, Supplementary p58 (Table S51), Response letter pp63–64.
- Patches: LOCAL (git) and PORTABLE (git + BSD) rebuild all three files byte-identically from before/.

## Not done
No staging/commit/push; not CLOSED; Section 3.2(d) not started; R2-M9 untouched.
