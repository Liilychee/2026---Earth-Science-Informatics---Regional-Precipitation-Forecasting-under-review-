# R4-M4 P5 — local implementation report (2026-11-16)

Scope: P5 only (two locations). P1–P4, P6, the R4-M4 reply, EvidenceBoxes, Supplementary, BibTeX and the template are untouched.

## Changes (R4_M4_P5_LOCAL.patch, manuscript.tex, 2 hunks)
1. §5.3 (`sec:predictor_complementarity`), the paragraph "The three analyses answer different questions. ..." (source line 1254). The approved Mamalakis sentence is appended after "... none of these analyses establishes meteorological causality.". The section already sits inside an outer red group; the nested `\revminor` compiles cleanly.
2. §5.4 Limitations and Future Work, the paragraph "The interpretation is conditional on the fixed SHAP background ..." (source line 1325, black text). The approved Aas sentences are appended after "... rather than causal effects.", wrapped in `\revminor` (red text and citation; old text unchanged).
- Both paragraphs matched the read-only audit (first and last sentences). Approved text inserted verbatim.
- The patch rebuilds from before/ with git apply and BSD patch → identical to after/.

## Protection
- No excerpt quotes either paragraph. Window hits (ex157 R4 M1; ex15/98/118 R1 M4, R2 M8, R2 m4) are generic phrases elsewhere, and none spans a paragraph end. 170/170 matched, identical and in order. P1–P4 citations intact; P6 not touched.

## Meaning
- §5.3: Mamalakis et al. 2022 is cited only as general support that XAI methods have method-dependent strengths and limitations and that several methods should be used together. Not presented as validating this study's SHAP/correlation/ablation rankings or as identifying a correct ranking. The original causality caveat stays immediately before it. The following paragraphs (mntpr attribution; precipitation-group ablation) are not repeated or contradicted.
- §5.4: Aas et al. 2021 is cited as a methodological risk under feature dependence. This is consistent with the existing sentence "interventional masking can break dependencies among correlated predictors". It does not claim the present SHAP values are wrong or explain the SHAP–ablation differences. Background, seeds and sampling limits are unchanged.
- Neither addition turns attribution into meteorological causality.

## Checks
- BibTeX: both keys present once and resolved. They render "(Mamalakis et al 2022)" and "(Aas et al 2021)". BibTeX unchanged; `\citet` occurrences 9 (accepted E1–E9).
- Reference-list rendering issues (report only):
  - sn-basic.bst inserts a thousands separator in numeric page fields: "298:103,502" and "1(4):e220,012".
  - The Aas title prints "shapley" lower-cased.
  - A scratch test with the same cls/bst showed that moving the article number from `pages` to `eid` (e.g. `eid={103502}`) prints it without a comma; braces inside `pages` do not help. Writing `{Shapley}` keeps the capital. For the user to decide; BibTeX not modified.
- Builds: manuscript 114 pp (unchanged), Supplementary 80 pp, Response letter 102 pp; no errors, 0 undefined, 0 multiply defined.
- Layout: overfull 113 → 113 (per-page 1.41 pt \vbox template artefact), no \hbox. Renders: render/manuscript_p091_P5a.png, render/manuscript_p101_P5b.png.
