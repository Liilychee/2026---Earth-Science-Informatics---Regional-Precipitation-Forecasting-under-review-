# Closure manifest — remote-verification gate

Base: `53a757ab603ef23a909ff27bdc9637212afa44b1` (origin/main). One batch scientific-archive commit is intended; no per-task worktrees or commits.

**This is a conditional disposition, not a pre-push CLOSED declaration.** Before successful remote verification, R3-07–12 are `ELIGIBLE — ARCHIVE_PENDING`. Only after every allowlisted remote blob matches does the local FINAL_REMOTE_RECEIPT.json activate CLOSED for these six tasks. This avoids claiming closure before push and avoids a self-referential receipt commit. The post-push receipt is generated locally and is not falsely claimed to be contained in the commit it verifies.

| Task | Reviewer ID | Disposition after successful remote verification | Evidence / position |
|---|---|---|---|
| R3-07 | Section 3.2(d) | CLOSED | Main §5.4; S26/S27/S52; Fig. S3; r3sec32d_integration/finalization |
| R3-08 | Section 3.2(e) | CLOSED | Main §3.2/3.3; existing Table 1; concise_review reply |
| R3-09 | Section 3.2(f) | CLOSED | Main §4.1; S53/S54 |
| R3-10 | Lines 329–333 | CLOSED | Main §3.3/4.2; S55/S56 |
| R3-11 | Lines 341–344 | CLOSED | Existing §3.3.1/4.2.1; main Table 4; no new table |
| R3-12 | Lines 376 | CLOSED | Main §3.3.2/4.3.3; S57–S59 |
| R3-13 | Section 3.3.1 | OPEN | §4.2.2; S3–S6/S60. Missing strict same-window NWP comparison. |

Historical per-task final reports are preserved as historical local-completion records, not silently rewritten. Their page numbers can predate the batch pagination; current labels and pages are authoritative in BATCH_VERIFICATION.json/PDF_CHECK.json. Source/after hashes and canonical patches distinguish the six closure-ready tasks from the open R3-13 increment. Other reviewer/task states are not modified; in particular R2-M9's repository-documentation pending state is preserved.
