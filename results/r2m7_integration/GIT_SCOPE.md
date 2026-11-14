# R2-M7 selective archive — author authorized 2026-11-14

Base origin/main: `8005ab08506dc8e0f9123f81e1861fdacc9de942`, descendant of `dc850836b486e8f326ddcb432a3602fe8b8448b6`.
Isolated worktree: `/private/tmp/esi-r2m7-integration-sync`; branch `codex/r2m7-integration-sync`; target `origin/main`.

Archive only explicitly enumerated files under results/r2m7_integration. R2M7_LOCAL.patch carries precisely the six reviewed document/task/registry deltas; DOCUMENT_HASHES proves it reproduces each local after-document from its before-snapshot. Do not apply these changes to remote root manuscript.tex, and do not stage any complete LaTeX/Bib, task list, prior evidence directory, before snapshots, raw data or unrelated Figure. R2M7_PORTABLE.patch has identical hunks with tab-separated header timestamps so BSD patch handles the space in Response letter.tex; its exact six-file reconstruction is verified. Subsequent CLOSURE_STATUS.patch contains only R2-M7 closure record deltas relative to this reviewed local state.

Author Figure is already archived at base commit under results/figures/revision/r2M7_spatial_quantiles.pdf; local Figures PDF is byte-identical (AUTHOR_FIGURE_SOURCE.json). A duplicate binary is unnecessary. Fixed dc85083 statistics remain unchanged.

Original paper worktree and index are not pulled, reset, staged or overwritten. Fetch updates only remote metadata; all commits occur in isolated worktree. Normal fast-forward push only; any conflict/permission failure stops closure. First remote archive verification precedes CLOSED; closure receipt is subsequently committed and final closure commit re-read. Receipt does not claim to contain its own commit hash.


Retry update: origin/main advanced to558da58341bcd8d1aedc9f6cd9754b58774b56fa (49 task22 additions, no overlap). New worktree /private/tmp/esi-r2m7-retry-sync, branch codex/r2m7-retry-sync. Clean cherry-pick09de6bb produced2268b154ee3f3a6cc302ee8093b6e44f406c5327; pushed normally and verified31/31 through GitHub. Root documents/index remain unchanged. Subsequent closure commit adds only the explicitly listed R2-M7 receipt/status/report/closure patch metadata, never raw data or other tasks.
