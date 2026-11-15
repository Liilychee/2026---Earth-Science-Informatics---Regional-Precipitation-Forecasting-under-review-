# R3-03 evidence index

- Baseline gate (R3-02 CLOSED, remote 8bb8a69): BASELINE_GATE.json.
- Literature: CELL_INDEX.json; evidence/crossref_{rahman2022,latif2023,adewoyin2021}.json and evidence/openalex_{rahman2022,latif2023,adewoyin2021}.json (dates, metadata, abstracts).
- Paragraph construction: PARAGRAPH_ASSEMBLY.json (verbatim preserved pieces, removed and added text, new order).
- Excerpts: EXCERPT_INDEX.json (122 unchanged + 2 new verbatim; R1-m4 excerpts raw substrings); VERIFICATION.json.
- Source increments: R3L169_LOCAL.patch / R3L169_PORTABLE.patch (manuscript.tex line 95; Response letter R3 L169-177 block); DOCUMENT_HASHES.json; PATCH_RECONSTRUCTION.json.
- Protection: PROTECTED_HASHES.json (921 files incl. sn-bibliography.bib), ORIGINAL_WORKTREE_GUARD.json.
- Build and layout: PDF_CHECK.json, compile_*.txt, render/ (144 dpi).
