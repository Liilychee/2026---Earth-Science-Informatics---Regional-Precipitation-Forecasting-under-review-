# R4-M4 — Response letter integration report (2026-11-16)

## Change (R4_M4_RESPONSE_LOCAL.patch / .diff; Response letter.tex only, 1 hunk)
- In the `% Review ID: R4 M4` block, `\PendingResponse` is replaced by the user-approved `\AuthorResponse`, inserted verbatim (it already mentions the P1-c correction). `\ChangeLocation` is replaced by a `\ManuscriptChange` box naming §5.1–§5.4 via `manuscript-sec:overall_discussion`, `manuscript-sec:upper_tail_discussion`, `manuscript-sec:predictor_complementarity` and `manuscript-sec:limitations`.
- `\ReviewerComment` unchanged verbatim. Letter byte-identical outside the R4 M4 block.
- Nine new EvidenceBoxes in manuscript order: P3, P1, P2, P1-c, P4, P5a, P6a, P6b, P5b. Each excerpt was re-extracted from the current manuscript.tex (evidence/excerpts_from_current_manuscript.json); build script: evidence/build_block.py.
- P1-c needs its own box because the change is a phrase inside an existing sentence. That box quotes the full current sentence, including `\revminor{particularly for medium-sized datasets}`.

## Verification (VERIFICATION.json)
- Original EvidenceBoxes: 170/170 matched, outside the R4 M4 block, identical and in the same order as before/.
- New EvidenceBoxes: 9/9 matched (canonical check) and each is a raw substring of the current manuscript.tex.
- Total 179/179.
- Labels and citations: all `manuscript-sec:` refs resolve (render as Sections 5.1–5.4). The letter cites the nine sources through its own natbib/plainnat setup, e.g. "(Lerch et al., 2017)" with a comma, as accepted out of scope. 0 undefined references or citations, 0 multiply defined labels.
- Builds:
  - manuscript 115 pp (114 per-page \vbox artefacts, no \hbox);
  - Supplementary 80 pp;
  - Response letter 105 pp (was 102), no overfull boxes.
- Visual check: letter pp. 88–90 (render/). Reply red, location box and EvidenceBoxes blue, no overflow; R4 Minor Comment 1 follows normally.
- manuscript.tex, Supplementary.tex and sn-bibliography.bib unchanged. The patch rebuilds from before/ with git apply and BSD patch. No Git commit or push.
