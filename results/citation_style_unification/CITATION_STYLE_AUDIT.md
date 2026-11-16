# Citation style audit (read-only stage, 2026-11-16)

Hashes of the pre-change sources: evidence/before_sha256.txt. Inventories: evidence/citation_inventory_before.json, evidence/citet_sentences_before.json.

## Template and configuration
- `\documentclass[referee,pdflatex,sn-basic]{sn-jnl}`: the `sn-basic` option makes sn-jnl.cls load `natbib` with `[authoryear]` and `\bibliographystyle{sn-basic}` (cls l.1657–1661).
- No `\bibpunct`/`\setcitestyle` in manuscript.tex before this task, so natbib defaults applied: author–year separator `,`, multi-citation separator `;`, round brackets.
- `sn-basic.bst` writes `et~al` **without a period** (`FUNCTION {bbl.etal} { "et~al" }`, l.240–241). The same string goes into the `\bibitem` label that natbib uses for in-text citations, and into the reference list.
- Rendered before: `(Li and Dev, 2024)`, `Hersbach et al (2020)`.

## Citation commands in manuscript.tex (before)
- `\citet` 29 occurrences (29 keys); `\citep` 38 commands (46 keys); no `\cite`, `\citeauthor`, `\citeyear`, `\citealp`, `\citealt`.
- 57 distinct keys, all present in sn-bibliography.bib; no duplicate BibTeX keys.
- All `\citet` were in Introduction/Related Work (l.80, 85, 87, 92, 99), §2.5 scope (l.145), Methods data (l.572), Discussion (l.1200, 1215, 1306). None in Abstract, captions, tables or footnotes.
- No hand-written author–year citations (regex search for `Name (2020)`, `Name et al. (2020)`, `(Name, 2020)`).

## EvidenceBox protection
- 9 of the 29 `\citet` sentences are quoted verbatim in EvidenceBoxes (overlap test: any 30-character canonical window of the sentence occurs in an excerpt). See PROTECTED_EXCEPTIONS.md.
- 20 sentences are not quoted in any excerpt.

## Supplementary.tex / Response letter.tex (read-only)
- Supplementary.tex: no citation commands.
- Response letter.tex: `natbib[authoryear,round]` + `plainnat`, 23 `\citet` and 57 `\citep`; renders `(Author et al., 2022)` with comma and narrative forms. Not changed (outside scope); unifying it would be a separate task and would touch reply text.

## Feasibility of the target format
- No comma between author and year: achievable with natbib's documented `\setcitestyle{aysep={}}` in the manuscript preamble. No class or .bst edit.
- `et al.` with period: **not achievable without changing the .bst output**. natbib takes the short-author string verbatim from the `\bibitem` label written by sn-basic.bst. Minimal alternative (not done, needs approval): a renamed local copy of sn-basic.bst with `bbl.etal` set to `"et~al."`, selected via `\bibliographystyle` after the class. It would also add the period in the reference list, which Springer Basic style prints without it. The journal's production typesetting re-applies its own house style in any case.
