# Reconstruction limitations

1. This repository archives incremental patches and evidence for the revision. It is not a complete source-version repository of the paper.
2. A full rebuild of `manuscript.tex`, `Supplementary.tex`, `Response letter.tex` and `sn-bibliography.bib` requires externally supplied full-text base files whose SHA-256 match those listed in `APPLY_ORDER.json`. These base files are not archived here; the paper is under review.
3. The R1-stage patches and the complete initial base documents are not archived (the repository root `manuscript.tex` is the 2026-11-02 Overleaf import; `Response letter.tex` and `Supplementary.tex` were never archived). The full paper therefore cannot be rebuilt from this repository alone, starting from an initial version.
4. This supplementary archive only removes the dependence on the locally stored R3-05 refinement delta. With the correct external base files, the R3-05 → refinement → R3-06 chain can be rebuilt using patches downloaded from this repository only.
5. Full repository-only reconstruction is **not** achieved and is not claimed.

| Conclusion | Status |
|---|---|
| Patch files fully obtainable from the remote repository | YES |
| Patch chain rebuildable when correct external base files are supplied | YES |
| Full paper rebuildable from the remote repository alone | NO |
