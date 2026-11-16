# Reviewer 4 — pre-archive Git audit (read-only, 2026-11-16)

Scope covered: R4-M1, R4-M2, R4-M3, R4-m8, citation-style unification, R4-M4 P1–P6, P1-c and the R4-M4 Response-letter integration.
No `git add/commit/push/reset/checkout/restore` was run, and no project source was modified.

One incident:
- An integrity re-check re-ran `results/r4m4_response_integration/evidence/verify_excerpts.py`.
- That script rewrites its `VERIFICATION.json` and dropped the 10 post-integration fields.
- The file was immediately regenerated with the same deterministic code on unchanged inputs (16 keys, same values); only its mtime changed.
- All other checks were done in memory.

Raw outputs: GIT_STATE_SNAPSHOT.txt, UNTRACKED_FILES.txt, PROPOSED_ALLOWLIST.json.

## 1. Workspace

### Paper directory (this repo)
- `origin` = github.com/Liilychee/2026---Earth-Science-Informatics---Regional-Precipitation-Forecasting-under-review- — **the same remote as esi_github**.
- Local `main` is at `ae4cd53 Initial Overleaf Import`; remote `main` is at `53319b2` (ls-remote) with the full archive history.
- Committing here and pushing would need a force push and would overwrite that history. **Never commit or push from this directory.** This matches the standing rule "do not stage the paper repo".
- Tracked diff vs ae4cd53: `M manuscript.tex` (+/− 1058 lines), `M sn-bibliography.bib` (+322/−1), `D rebuttal-template.tex`. This is the cumulative R1–R4 revision since the Overleaf import, not Reviewer 4 only.
- `git diff --check`: trailing whitespace at sn-bibliography.bib l.1144–1145 (`bidirectional` entry). It was already present in the archived R3-19 state (bib hash 137c5970…); it is not an R4 change.
- Untracked: 2,885 files. Mostly `results/` (R1–R4 records); also `Response letter.tex`, `Supplementary.tex`, `original_manuscript.tex`, `diff.tex`, `Figures/r1M*–r3M*`, `code/`, `.vscode/`, `.gitignore`, `comment.txt`, the docx, and the task and checklist .md files.

### Archive repo (esi_github, `~/Interpretable-BU-LSTM-for-Rainfall-Prediction-in-Dublin/esi_github`)
- `main` at 53319b2 = origin/main; clean apart from untracked `.DS_Store` and `AGENTS.md` (not ours, leave alone).
- 11 old worktrees remain in /private/tmp from earlier rounds; harmless, can be pruned later with approval.
- Not yet archived: all R4 record directories listed in §5.1, plus older local-only dirs `r1*`, `r2m1_final` (Codex-era, not Reviewer 4; out of scope).

## 2. Task reconciliation (SHA-256 chain of the four sources)

| Step | before/ equals previous after? | Note |
|---|---|---|
| R3-19 archived after → R4-M1 | before/ differs; reconciled | R4-M1's before/ was captured at an intermediate state (manuscript 66a0b0e4…). The archive (53319b2, `r3_batch_19_closure/BASE_AND_AFTER_HASHES.json`) already records that `R4_M1_LOCAL.patch` applied to the R3-19 after-state reproduces the R4-M1 state (a0eb8f27…), which is exactly the before/ of the next step. |
| R4-M1 → labelfix + R4-M2 → R4-M3 → R4-m8 | OK | |
| R4-m8 → P1 | bib differs | user added `lerch2017forecaster` |
| P1 → citation unification | OK | |
| citation → P2 → P3 → P4 → P5 → P6 → P1-c | bib differs at each step | user BibTeX additions and fixes: ayzel2020rainnet (+ title/DOI fix), bano2020configuration, aas2021explaining and mamalakis2022investigating (+ `eid`, `{Shapley}`), rasp2024weatherbench (+ `eid`, Russell) |
| P1-c → Response → current workspace | OK | |

- No task patch of mine changed sn-bibliography.bib: before/ == after/ for the bib in all 12 R4 task directories. Every BibTeX change since R4-m8 is a user edit; they need one bridging `USER_BIB_EDITS` patch in the archive so that the chain is reproducible.
- `.tex` sources chain without gaps from the R4-M1 state to the current workspace.
- Template files: sn-jnl.cls, sn-basic.bst and sn-mathphys.bst are unchanged vs ae4cd53.
- Supplementary.tex: changed only by R4-M3 (Table S70 section).
- The citation-unification record is present and consistent (20 conversions; E1–E9 accepted exceptions).
- Other reviewers' accepted changes in the workspace (R1–R3, plus the `rebuttal-template.tex` deletion from the Overleaf/Codex era) are part of the cumulative diff. They are already archived in esi_github up to R3-19 and must not be re-committed or excluded by hand.

## 3. Security and file checks
- No credentials found: the only regex hit is the word "token" in a code comment (`citation_style_unification/evidence/inventory.py`). No `.cdsapirc`, keys or passwords.
- No raw ERA5/HRES data, NetCDF/GRIB or large CSVs in R4 dirs; the largest CSV is 14 KB.
- No copyrighted literature PDFs. `r4m4_readonly_audit` holds bibliographic metadata, short quotations and manuscript paragraph extracts only.
- Full-text material that must not be uploaded:
  - `before/`, `mid/`, `after/` in every task dir (full manuscript, letter, Supplementary and bib);
  - `diff_update_20261116/{before,after}/diff.{tex,pdf}` and `latexdiff_raw.tex`.
- LaTeX build files live in `build/` (ignored by `.gitignore`); no PDF intermediates in R4 dirs apart from the diff PDFs above.
- `.gitignore` (paper dir): `/build/`, `.DS_Store`. No change needed: the paper directory is never staged, and esi_github uses an explicit allowlist.

## 4. Integrity (current workspace)
- Builds (latest, PDFs newer than sources): manuscript 115 pp, Supplementary 80 pp, Response letter 105 pp. 0 undefined references or citations, 0 multiply defined labels, no overfull \hbox.
- EvidenceBoxes: 179/179 matched: the original 170 identical and in order outside the R4 M4 block, plus 9 new inside it.
- `\citet` occurrences: 9 = accepted exceptions E1–E9.
- R4-M4: all eight P1–P6 inserted texts are present verbatim; P1-c `\revminor{particularly for medium-sized datasets}` is present and "imbalanced sample sizes" is gone.

## 5. Archive plan (for approval — not executed)

### 5.1 Proposed commit content (esi_github, new worktree based on 53319b2)
Exact list: `PROPOSED_ALLOWLIST.json` → `proposed_include` (218 files, 9.5 MB) from these directories, minus before/, mid/, after/, diff.tex/diff.pdf and latexdiff_raw.tex:

`r4m1_integration`, `r4m1m2_integration`, `r4m3_integration`, `r4m8_integration`, `r4m4_readonly_audit`, `r4m4p1_integration`, `citation_style_unification`, `r4m4p2_integration` … `r4m4p6_integration`, `r4m4p1c_integration`, `r4m4_response_extract`, `r4m4_response_integration`, `diff_update_20261116` (README, scripts, compile log, renders only).

The following would be added at archive time (not created now):
- `results/r4_batch_closure/`:
  - `BASE_AND_AFTER_HASHES.json` (R3-19 after → final);
  - `USER_BIB_EDITS.patch` (bridging the bib gaps);
  - a chained rebuild check (R3-19 after + all patches → current workspace, byte-identical);
  - `ARCHIVE_MANIFEST.json` (md5 + sha256);
  - `STATUS.md`;
  - `PORTABLE` patch variants as needed.

### 5.2 Do not commit
- Anything in the paper directory, which must not be staged.
- Full sources: manuscript.tex, Response letter.tex, Supplementary.tex, sn-bibliography.bib, original_manuscript.tex, diff.tex, and all before/mid/after dirs.
- `build/`, diff PDFs, `.vscode/`, the docx, comment.txt (reviewer comments), the task and checklist .md files, `code/`, `Figures/`, R1–R3 or Codex-era result dirs, and esi_github's untracked `.DS_Store`/`AGENTS.md`.

### 5.3 Unauthorised or unknown changes
None within Reviewer 4 scope. All differences are explained by the task patches, the user's own BibTeX edits (to be recorded as USER_BIB_EDITS) and pre-R4 history.

### 5.4 Single integrated commit?
Yes — one archive commit in esi_github holding all R4 record dirs plus `r4_batch_closure/`. Then, after the fast-forward push and fresh-clone readback, the usual closure commit (STATUS CLOSED, REMOTE_RECEIPT, CLOSURE_MANIFEST), following the established two-commit pattern.

### 5.5 Proposed commit messages
1. `revision: archive Reviewer 4 (M1–M4, m8) verified evidence and citation-style unification`
2. `revision: close Reviewer 4 M1–M4 and m8 after verified remote archive`

### 5.6 .gitignore
No update needed.

### 5.7 Risk conclusion
- LOW if done in esi_github via a fresh worktree from 53319b2 with the explicit allowlist, a fast-forward push only and a blob readback.
- HIGH and unacceptable if done from the paper directory: divergent history (force push), and full manuscript, letter and Supplementary sources made public.
- Remaining R4 comments (m1–m7, m9 onward) stay pending and are unaffected.

Status: READ-ONLY AUDIT COMPLETE — awaiting final archive authorization.
