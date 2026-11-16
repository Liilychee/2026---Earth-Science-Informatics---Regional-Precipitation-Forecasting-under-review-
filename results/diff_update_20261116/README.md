# diff.tex / build/diff.pdf update — 2026-11-16

- Base: original_manuscript.tex (2026-11-02) vs current manuscript.tex (identical to results/r4m8_integration/after, i.e. through R4 minor 8; R4-M4 not yet edited).
- Previous files backed up in before/ (diff.tex and diff.pdf of 2026-11-13 11:11, 82 pp).
- Command: latexdiff 1.4.0 `--append-textcmd=revminor,revised,textcolor original_manuscript.tex manuscript.tex` → latexdiff_raw.tex,
  then `python3 postprocess_diff.py latexdiff_raw.tex original_manuscript.tex manuscript.tex build/original_manuscript.aux <latexdiff> <workdir> diff.tex`.
- postprocess_diff.py (+ fix_steps.py) reproduces the manual edits found in the 11-13 diff.tex:
  1. header comments; 2. abstract as inline word diff; 3. labels of deleted items removed (incl. deleted copies of eq:mean_pooling, eq:global_shap);
  4. \ref to retired figures replaced by original numbers (fig:Spearman 2, fig:temporal_shap 6, fig:shap_summary 7, fig:feature_ablation 8, from build/original_manuscript.aux);
  5. \DIFaddFL colour-only redefinitions at the configuration table and Table 3; 6–7. Table 3 header/row marker clean-up.
  New for this update: 8. `\DIFadd{\textcolor{red}{X}}` / `\DIFadd{\revminor{X}}` rewritten to `\textcolor{red}{\DIFadd{X}}` so added red text can line-break
  (without this, 25 overfull boxes up to 1,800 pt; with it, none of those remain).
- Result: build/diff.pdf 133 pp; no errors, no undefined or multiply defined references; 8 overfull hboxes:
  one 19.7 pt (also present in the 11-13 diff) and seven 6.8 pt at figures included at native width with latexdiff float markers (cosmetic).
- Visual check: render/ p001 (abstract), p027 (minor 8), p061 (R4-M3 §4.1), p064 (Table 3), p072 (R4-M3 §4.2.3).
- manuscript.tex, Supplementary.tex, Response letter.tex, sn-bibliography.bib not modified.
