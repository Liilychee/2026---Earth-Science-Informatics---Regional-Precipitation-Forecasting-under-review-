# R4-M4 P3 — local implementation report (2026-11-16)

Scope: P3 only. P1, P2, P4–P6, the R4-M4 reply, EvidenceBoxes, Supplementary, BibTeX and the template are untouched.

## Change
- manuscript.tex §5.1 (`sec:overall_discussion`), the paragraph starting "The results show that several machine-learning and deep-learning models achieved similar levels of performance ..." (source line 1187).
- The approved text is appended verbatim after "... under the same data and evaluation protocol.", inside the existing `{\color{red}\hypersetup{linkcolor=red} ... \par}` block, wrapped in `\revminor{...}` (same nesting as P1/P2; citation links red).
- Patch: R4_M4_P3_LOCAL.patch (manuscript.tex, 1 hunk), rebuilt from before/ with git apply and BSD patch → identical to after/.

## Protection
- 30-character window matches to excerpts 25, 78, 121 and 123 are generic phrases shared with other passages ("wet subset ($\geq0.1$...", "regional precipitation forecasting", "machine-learning and deep-learning"). No excerpt quotes this paragraph or runs past its end, so the paragraph is unprotected. 170/170 excerpts matched, identical and in order after the edit.

## Literature and meaning
- Grinsztajn et al. 2022: the abstract supports tree-based models staying state-of-the-art on medium-sized (~10K samples) tabular data. The text says only "remain competitive ... on medium-sized tabular datasets". No claim about all data types or imbalanced samples.
- Otero and Horton 2023 (Semantic Scholar abstract; Wiley full text returned 403): a simplified two-level U-Net achieved similar skill for heavy/extreme precipitation as deeper versions "while significantly reducing the overall complexity and computing resources".
  - The approved wording "with fewer trainable parameters" is not stated verbatim in the abstract. It follows from fewer encoder–decoder levels but is unverified against the full text.
  - Abstract-faithful alternative if wanted: "with reduced complexity and computing resources".
  - The text frames the source as U-Net depth only, not as validating this study's XGBoost/LSTM ranking, and states the differences in data representation, architecture and setting.
- Consistency: the next two §5.1 paragraphs (attention gain not established after Holm; "Greater model complexity was not matched by clear gains in point accuracy", parameter counts, cost) are unchanged. The new sentence introduces that theme without restating their numbers; mild thematic overlap, no contradiction.

## Checks
- BibTeX: both keys present once; both resolved (bbl). Renders "(Grinsztajn et al 2022)", "(Otero and Horton 2023)". BibTeX unchanged. `\citet` occurrences remain 9 (accepted E1–E9). P1 and P2 intact.
- Builds: manuscript 113 pp, Supplementary 80 pp, Response letter 102 pp; no errors, 0 undefined, 0 multiply defined.
- Layout: overfull 112 = baseline (all per-page 1.41 pt \vbox template artefact), no \hbox. Render: render/manuscript_p083_P3.png.
