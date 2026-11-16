# Reviewer 4 batch — Git archive report (2026-11-16)

1. Base 53319b2 (remote main confirmed by ls-remote immediately before the push).
2. Isolated worktree /private/tmp/esi-r4-batch-sync on branch claude/r4-batch-sync. The paper working directory was never staged, committed or pushed.
3. The commit staged 238 explicit paths (the 218 audited allowlist files plus 20 closure records); the staged list equalled the expected list.
4. Archive commit 5305b27, pushed as a normal fast-forward 53319b2..5305b27 to main. Only main was pushed; the work branch was not.
5. Fresh-clone readback:
   - HEAD 5305b27;
   - 236/236 manifest files match md5 and sha256;
   - no before/mid/after paths, diff.tex or diff.pdf;
   - user BibTeX patches present;
   - rebuild_chain.py run from the clone reproduces all 22 nodes byte-for-byte.
6. No CLOSURE_STATUS.patch: the task-checklist entries for R4 are shared with still-open minor comments (e.g. R4-m15/m37, R4-M2/M3/m34), so they were not marked closed.
7. Open items unaffected: R4 minor 1–7 and 9–37, R2-M9.
