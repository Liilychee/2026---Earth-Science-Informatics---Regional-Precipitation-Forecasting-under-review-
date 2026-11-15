# R3-05 (R3 Section 3.2(b)) response refinement — supplementary version archive

**Purpose.** After R3-05 was closed (scientific archive 7faac6b, closure dc72acc), the author replaced the formal reply to R3 Section 3.2(b) with a shorter version. This directory archives that post-closure text change as an applicable patch, so that the R3-05 → R3-06 patch chain no longer depends on a delta file held only locally. R3-05 and R3-06 remain CLOSED; no scientific content, experiment, manuscript, Supplementary or bibliography text is changed.

**Contents.**
- `R3S32b_REFINEMENT_LOCAL.patch` (git format) and `R3S32b_REFINEMENT_PORTABLE.patch` (unified diff with timestamps; works with git apply and BSD patch): one hunk replacing only the R3 Section 3.2(b) `\AuthorResponse{...}` in `Response letter.tex`.
- `VERSION_HASHES.json`: SHA-256 of the closed, refined and current Response letter and of both AuthorResponse texts.
- `APPLY_ORDER.json`: exact bases and patch order for R3-05 → refinement → R3-06.
- `EXCERPT_CHECK.json`: 130/130 EvidenceBox verification on the reconstructed letter.
- `PUBLIC_CONTENT_CHECK.json`, `ARCHIVE_MANIFEST.json`, `GIT_ARCHIVE_REPORT.json`.
- `RECONSTRUCTION_LIMITATIONS.md`: what can and cannot be rebuilt from this repository.
