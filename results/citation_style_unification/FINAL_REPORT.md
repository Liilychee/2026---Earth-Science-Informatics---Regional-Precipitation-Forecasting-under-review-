# Citation style unification — final report (2026-11-16)

Status: CITATION STYLE UNIFICATION: LOCALLY IMPLEMENTED — PROTECTED EXCEPTIONS PENDING REVIEW

1. Style before → after: `(Li and Dev, 2024)` / `Hersbach et al (2020)` → `(Li and Dev 2024)` / `(Hersbach et al 2020)`; multiple citations `(A 2007; B 2011)`.
2. Global configuration: one preamble line in manuscript.tex, `\setcitestyle{aysep={}}` (natbib-supported). sn-jnl.cls and sn-basic.bst untouched. `et al` stays without period (bst; see CITATION_STYLE_AUDIT.md for the minimal alternative).
3. Converted narrative citations: 20 of 29 (CITATION_CONVERSION_TABLE.md). 17 sentences in previously black paragraphs are wrapped in `\revminor`; 3 were already inside red blocks (singh, miller, P1 lerch). P1 keeps its approved meaning; only the citation form changed.
4. Each conversion keeps the source's verb strength, scope, numbers and single-source attribution; no new claims.
5. Not converted (protected): 9 `\citet` (PROTECTED_EXCEPTIONS.md, E1–E9; R1 M6, R1 m4, R3 Section 2, R3 L169-177, R3 Section 3.2(d), R4 M1).
6. Keys: 57 before / 57 after, identical multiset of 75 key-citations; `\citet` 29 → 9, `\citep` keys 46 → 66; none missing from BibTeX, no duplicate keys, 57 `\bibitem`, 0 undefined citations.
7. EvidenceBox: 170/170 matched; full excerpt list identical and in order; Response letter unchanged.
8. Builds: manuscript 112 pp, Supplementary 80 pp, Response letter 102 pp; no errors, no undefined references, no multiply defined labels.
9. Layout: manuscript overfull boxes 111 = baseline 111. Visual checks: render/ (Abstract p1, §2.1 p4, §2.2 p6, §2.3 p8, §2.4 p9, Methods p40, P1 p86, References p107).
10. Needs separate approval: E1–E9; optional local .bst copy for `et al.`; Response letter citation style (read-only audit only); BibTeX metadata gaps (evidence/bib_metadata_gaps.txt, report only — e.g. lerch2017forecaster has no volume).

Patch: CITATION_STYLE_LOCAL.patch (manuscript.tex only, 3 hunks), rebuilt from before/ with git apply and BSD patch. No Git commit/push, no training, no downloads.

## Acceptance decision (user, 2026-11-16)
- The 20 completed conversions are kept as implemented.
- The official sn-basic.bst is kept; no copy or modification; `et al` stays without a period.
- E1–E9 are retained unchanged as accepted style exceptions (not errors).
- The Response letter citation format is out of scope.
- No further changes to the paper, BibTeX or template this round; no Git commit or push.

Status: CITATION STYLE UNIFICATION: LOCAL COMPLETE WITH ACCEPTED EXCEPTIONS — Git archiving deferred
