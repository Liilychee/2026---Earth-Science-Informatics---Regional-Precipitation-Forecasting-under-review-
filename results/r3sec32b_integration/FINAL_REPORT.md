# R3 Section 3.2(b) (R3-05) — Local integration report

Baseline: remote main 29fa0e54ed57f9aac5433fe929de4b12ddf48b5c (verified); paper HEAD ae4cd53, index 1d0b3404… unchanged, nothing staged.

## Scope
| File | Change |
|---|---|
| manuscript.tex | L129: pure insertion of one `\revminor{}` block between "...large-scale precipitation (lsp)." and "Total precipitation (tp) was used...". Line count unchanged; candidate list bytes unchanged. |
| Response letter.tex | Only the R3 Section 3.2(b) block: `\PendingResponse`/`\ChangeLocation` replaced by AuthorResponse, ManuscriptChange and one EvidenceBox. |
| sn-bibliography.bib | `manandhar2019data`: `doi={10.1109/TGRS.2019.2926110}` added. New `gao2025applying` appended. `gascon2024post` body unchanged (a newline was added after its final `}` because the file previously ended without one). |

Unchanged: Supplementary.tex, Table 1, Figures, candidate pool, final seven inputs, all results (962/962 protected files identical to the R3-04 record).

## Differences from the author-specified paragraph (verbatim)
1. `surface radiative and moisture exchanges (ssr and e)` → `surface radiative and moisture exchanges (ssr and e, where e is the modelled actual evaporation rather than potential evaporation)` — implements decision 5 (e ≠ potential evaporation) in the manuscript.
2. `The inclusion of these variables defines` → `The inclusion of all eleven variables defines` — "these variables" directly followed the lsp/mxtpr/mntpr sentence and could be read as only those three.
3. `[INSERT VERIFIED CITATIONS]` → `\citep{manandhar2019data,rahman2022rainfall,gao2025applying}`; `[INSERT ERA5 DOCUMENTATION CITATION]` → `\citep{ecmwf_era5_documentation}`.

## Bib metadata
Gao 2025 checked against Crossref (evidence/crossref_gao2025.json): GAO Yuan-yuan, WANG Dong-hai, HUANG Ling-dong, LI En-guang; J. Trop. Meteorol. 31(6):603–621; 2025; DOI 10.3724/j.1006-8775.2025.040. The second syllable of each given name is capitalised in the .bib (Yuan-Yuan etc.); with Crossref's lower case the sn style rendered "Gao Yy, Wang Dh, Huang Ld".

## Citation support
- Gao 2025: T, DPT, P, Ws/Wd, SR, Cloud (station + CERES) — supports all six analogues.
- Manandhar 2019: T, DPT, SR (ground station).
- Rahman 2022: Temperature, Dew Point, Atmospheric Pressure, Mean Wind Speed (station).
- ECMWF documentation: e vs pev; lsp component of tp; mxtpr/mntpr within-hour extrema.
None is used to claim equivalence with ERA5 fields; the text states the analogues are not necessarily identical. Gao's potential evaporation is explicitly not used as support for e.

## Consistency with closed items
- R2-M2 timing sentence (L138) unchanged and consistent: "preceding-hour" = hour ending at valid time; "within-hour extrema" = max/min rates within that hour.
- R2-M3 screening and lead-time results unchanged; reply refers to them without new numbers.
- L129 protected excerpts R1-M3 (#6), R1-m2 (#37), R2-M1 (#52) still match.

## Verification
- RevisedExcerpts: 128 old verbatim and in order; 1 new (sha256 0f8e6cf4…), verbatim in manuscript; 129/129 match.
- Compile (Supplementary → manuscript → Response letter): 0 undefined, 0 multiply defined, 0 overfull. manuscript 99 pp (+1), Response letter 82 pp (+1), Supplementary 57 pp (PDF identical).
- Rendered: manuscript p13 (§3.2), p92 (Gao), p95 (Manandhar DOI); Response letter p62–63 (reply, box), p80 (references).
- Patches: LOCAL (git apply) and PORTABLE (git apply + BSD patch) reconstruct all three after-files byte-identically.
- Reply wording: "We did not identify…" (reply only); no "no study has used" claim; no claim of literature-driven original selection.

## Not done
No staging/commit/push; not CLOSED; tasks 09/21 open; R3 Section 3.2(c) not started.

## Selective archive and closure (2026-11-15)
Scientific commit 7faac6b6918417d2e8acdccf871adf26fd83b6de (fast-forward from 29fa0e5), 40 files under results/r3sec32b_integration only. Fresh-clone readback: 40/40 blobs and manifest SHA-256 match; remote PORTABLE patch rebuilt manuscript.tex, Response letter.tex and sn-bibliography.bib byte-for-byte (git apply and BSD patch); 129/129 excerpts; Gao/Manandhar metadata match Crossref; 964 protected files unchanged. Closure commit adds STATUS (CLOSED), REMOTE_RECEIPT, GIT_ARCHIVE_REPORT, CLOSURE_STATUS.patch (tracking-file notes as patch only; originals not edited), this report update, GIT_SCOPE update and CLOSURE_MANIFEST. Tasks 09/21: only the R3-05 part is recorded as complete.
