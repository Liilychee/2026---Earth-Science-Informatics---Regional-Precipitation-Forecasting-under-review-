# R4-M4 P1-c — local implementation report (2026-11-16)

## Change (R4_M4_P1c_LOCAL.patch, manuscript.tex, 1 hunk)
- §5.2, paragraph "The performance of XGBoost in the upper-tail subset should not be interpreted ..." (source line 1232, black text).
- `particularly under limited or imbalanced sample sizes` → `\revminor{particularly for medium-sized datasets}`.
- Wording: the approved replacement "on medium-sized tabular datasets" would have produced "... on tabular data, on medium-sized tabular datasets ..." (repeated "tabular"). The user chose "particularly for medium-sized datasets". The rest of the sentence and the `\citep{grinsztajn2022tree}` are unchanged; only the new phrase is red.
- Resulting sentence: "This pattern is broadly consistent with evidence that tree-based methods can match or exceed deep neural networks on tabular data, particularly for medium-sized datasets (Grinsztajn et al 2022)."

## Meaning
- It now matches the Grinsztajn abstract (tree-based models remain state-of-the-art on medium-sized, ~10K-sample, tabular data); the unsupported "imbalanced" qualifier is removed.
- The following sentence ("This may be useful when high-intensity rainfall events are relatively sparse, although the present experiments do not establish the underlying mechanism directly.") remains hedged. Its link to the citation is now looser, but it does not claim support from Grinsztajn for imbalance.
- Consistent with P3 in §5.1, which cites the same paper for medium-sized tabular data.

## Checks
- The sentence was not quoted in any EvidenceBox; 170/170 matched, identical and in order.
- All P1–P6 inserted texts are intact.
- Builds: manuscript 115 pp, Supplementary 80 pp, Response letter 102 pp; no errors, 0 undefined, 0 multiply defined; no overfull \hbox (114 per-page \vbox artefacts, unchanged).
- The patch rebuilds from before/ with git apply and BSD patch.
- BibTeX, Supplementary and Response letter unchanged. Render: render/manuscript_p089_P1c.png.
