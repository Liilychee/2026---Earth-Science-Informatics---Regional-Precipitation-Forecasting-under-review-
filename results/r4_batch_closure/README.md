# Reviewer 4 batch archive record

Contents
- The task directories results/r4m1_integration … r4m4_response_integration, citation_style_unification and diff_update_20261116 hold patches, reports, verification, evidence scripts and small CSVs, compile logs and page renders.
- Full-source snapshots (before/, mid/, after/) and diff.tex/diff.pdf are excluded.

Chain
- CHAIN_NODES_EXPECTED.json lists the 22 nodes, from the R3-19 after-state (archived in 53319b2) to the final state, with the SHA-256 of manuscript.tex, Response letter.tex, Supplementary.tex and sn-bibliography.bib after each step.
- rebuild_chain.py replays the task patches and the user BibTeX steps (user_bib_edits/USER_BIB_EDIT_01–07.patch) and checks every node. The output of the run done for this archive is in CHAIN_REBUILD_OUTPUT.txt.
- USER_BIB_EDITS.patch is the net user-made BibTeX change (six entries added plus metadata fixes) from the R3-19 state to the final state. No task patch modifies sn-bibliography.bib.

Limitation
- The R3-19 after-state sources are not in this public repository. A rebuild needs them supplied externally with matching SHA-256, or derived from the local R4-M1 after-state (`--base-from-r4m1-after`).
- A repository-only full reconstruction is therefore not available.
