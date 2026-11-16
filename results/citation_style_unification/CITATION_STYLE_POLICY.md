# Citation style policy (standing, manuscript.tex)

**Future manuscript writing must use parenthetical author–year citations, with natural sentence restructuring where necessary.**

New citations added to manuscript.tex should preferably use the parenthetical author–year form, with the punctuation produced by the current official Springer template (sn-jnl.cls + sn-basic.bst + `\setcitestyle{aysep={}}`, e.g. `(Lerch et al 2017)`). Unifying citation style must never break an existing EvidenceBox.

- Use `\citep{...}`; do not write new `\citet`, `\citeauthor`, or hand-typed `Author (Year)`.
- Rewrite the sentence so the finding or method is the subject; place the citation at the end of the clause it supports. Do not turn `\citet{x} showed` into `\citep{x} showed`.
- Keep each claim attached to its own source; do not merge citations for different findings at the end of a sentence.
- Preserve the original evidence strength (proposed / evaluated / found / demonstrated are not interchangeable) and the source's scope.
- Proper names of datasets, methods or institutions (ERA5, ECMWF, Shapley values, Met Éireann) are not citations and stay as names.
- Template: keep the official sn-jnl.cls and sn-basic.bst unchanged; do not copy or modify the .bst. `et al` is printed without a period, as the template generates it; this is accepted.
- Sentences quoted verbatim in an EvidenceBox are not changed for style reasons.

## Accepted exceptions (user decision, 2026-11-16)
E1–E9 in PROTECTED_EXCEPTIONS.md: nine narrative `\citet` citations whose sentences are quoted in verified EvidenceBoxes. They are retained knowingly as **style exceptions**. They are not compile errors and not scientific problems. Neither manuscript.tex nor Response letter.tex is changed for them.

## Out of scope
The existing citation format in Response letter.tex (natbib/plainnat, `(Author et al., 2022)`) is not part of this policy round.

## New literature
1. The user selects and approves it.
2. The user adds it to BibTeX.
3. The assistant verifies the key (exists once; metadata).
4. The assistant adds the citation only after approval.
5. New citations are parenthetical, as above.
6. No new narrative author–year citations.
