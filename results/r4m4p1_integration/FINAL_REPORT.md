# R4-M4 P1 — local implementation report (2026-11-16)

Scope: only P1 (user-approved). P2–P6, the P1-c Grinsztajn wording, the R4-M4 reply and EvidenceBoxes are untouched.

## Change
- File: manuscript.tex, §5.2 (`sec:upper_tail_discussion`), first paragraph (source line 1215), appended after `(Section~\ref{sec:regime_results}).`
- Text (approved wording, verbatim) wrapped in `\revminor{...}` inside the existing `{\color{red}\hypersetup{linkcolor=red} ... \par}` block, so the `\citet` link is also red; existing sentences unchanged.
- Patch: R4_M4_P1_LOCAL.patch (1 hunk, manuscript.tex only); rebuilt from before/ with `git apply` and BSD `patch` → identical to after/.

## Evidence for the wording
- Upper-tail subsets are selected on the observed target: Methods l.478 (Q90/Q95/Q97.5 training-derived; "observations at or above this fixed threshold"), Results l.895/909, revised wet `y>=0.1`.

## Checks
- BibTeX: `lerch2017forecaster` present once (sn-bibliography.bib:1316), DOI 10.1214/16-STS588; resolved in build/manuscript.bbl; reference list p.107. Note: entry has no `volume`/`number` (Statistical Science 32(1)); the reference prints without them. BibTeX not modified.
- EvidenceBox excerpts: 170/170 matched in canonical manuscript+Supplementary; full excerpt list identical and in order vs before/ (VERIFICATION.json). Response letter unchanged.
- Semantics: XGBoost conditional RMSE advantage is qualified, not described as spurious ("can distort", "conditional error diagnostics"). No conflict with later §5.2 paragraphs (tree-based not generally superior; amplitude compression; Q95 coverage) or §5.1 (BiLSTM-Attention numerically best overall, small difference).
- Builds: manuscript 112 pp, Supplementary 80 pp, Response letter 102 pp; no errors, no undefined citations/references, no multiply defined labels; manuscript last-run overfull boxes 111 = previous baseline 111. Render: render/manuscript_p086_P1.png (new text on p.86, lines 1999–2005).
- Supplementary.tex, Response letter.tex, sn-bibliography.bib: byte-identical to before/.
