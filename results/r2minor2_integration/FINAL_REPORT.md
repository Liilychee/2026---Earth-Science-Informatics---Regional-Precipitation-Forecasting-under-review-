# R2-m2 local integration — verified; author review and Git archive pending

## Outcome and scope

The requested 90%/95% interval diagnostics are integrated locally using option(b). R2-m2 is **LOCAL_VERIFIED_AWAITING_AUTHOR_REVIEW**, not CLOSED. No commit/push, training, model rerun, new prediction, Figure change, Abstract change or Conclusion change occurred. Current origin/main reference is 5196e40cd56af42afe6c82c08125b6374696efaf; original working-tree unrelated changes were retained. No README/environment/LICENSE work occurred.

## Modified source files and actual locations

- manuscript.tex: §3.3.3 after Eq.(18), line330: red definitions of central 90%/95% intervals, PICP/MPIW and both negative-bound diagnostics; full-precision computation distinguished from rounded z values.
- manuscript.tex: §4.4 lines998–1000: concise red coverage/width/subset results and transparent A1/A2/B identity statement, referring to Supplementary Table S50. Line1024 and §5.2 line1182 add only the necessary red 95% qualifications. Exact main delta verified as three added paragraphs and two narrow qualifiers; all remaining main bytes unchanged.
- Supplementary.tex line2034: automatic **Table S50**, `stab:r2minor2_intervals`, PDF p57. Eighteen model/subset/level rows, with 90% and 95% blocks; four mean±sample-SD metrics (coverage, width, above-upper frequency, negative-lower frequency). 144 numeric fields. All original S1–S49 source bytes and labels preserved; new table starts after a clearpage so it does not crowd S49.
- Response letter.tex R2-m2, line979 onward: original reviewer wording retained; formal response red and three exact EvidenceBoxes/locations blue. Reply PDF pp52–53. Cross-document Table5 alias scoped only to the new identity EvidenceBox; this fixed the undefined reference without editing the literal excerpt.
- Task16 note, FINAL_REVISION_CHECKLIST.md and SUPPLEMENTARY_TABLE_REGISTRY.md: only the local R2-m2 increment/status and S50 registration. Shared tasks remain Pending; no R2-m3 work.

## Fixed evidence and independent checks

Formal q16 code, per-run CSV, summary CSV and output were read from full fixed commit `d02519c5f153feb712018cf97efb035f6ca2d7ae`; SOURCE_INDEX.json records actual paths/MD5 and the fifteen q14 plus five q11 comparison files. Original source predictions remain in Git and are not overwritten or republished here.

- 3 Gaussian models × seeds42,123,7,2024,99 =15 q14 prediction files.
- All=3,939, Wet(y≥0.1)=854, Upper(y≥training Q95=0.574048)=238 in every run.
- q16 uses z=1.6448536269514722 and1.959963984540054; text reports rounded1.645/1.960.
- Independent saved-prediction verification: **450 per-run fields**, maximum difference **2.220446049250313e-16**; 9 summary rows, mean and sample SD independently checked (180 summary fields, including below-bound diagnostics). No formal archived CSV was replaced.
- Table144 fields traced cell-by-cell to the original summary row/column; 16 prose range endpoints separately indexed. ROW_INDEX.json records all18 displayed rows; DEFINITION_INDEX.json traces constants/counts.
- All-sample coverage90=0.9456–0.9464; coverage95=0.9560–0.9571. Width90=0.6526–0.6705 and Width95=0.7776–0.7989 mm h^-1. Wet coverage90/95=0.7546–0.7571 /0.8002–0.8042; upper coverage90/95=0.3958–0.4101 /0.4941–0.5042. All negative-lower proportions=1 and all below-lower proportions=0; all misses are above the upper bound. These are descriptive diagnostics, not significant model rankings or established causes.

### Important identity refinement

For A2 Probabilistic BiLSTM-Attention and B Gaussian, all five saved test timestamp sequences, targets and predictive means are identical. Saved standard-deviation parameters differ by at most **1.2205347710292358e-7 mm h^-1**, not exactly zero. Both the new main paragraph and table note disclose this using the conservative rounded upper bound1.23e-7. We do **not** claim every distribution parameter or CSV byte is identical, nor treat these as two independent prediction-evidence sets. The cause of that small saved-parameter difference was not established in this round. This does not alter q16 results and does not replace Table5 or R2-M6 evidence.

## EvidenceBox and protected material

- Old **112/112** RevisedExcerpt arguments remain byte-identical (including all prior closed replies); all112 match current manuscript text with only whitespace/color wrappers normalised for source lookup.
- New **3/3** excerpts are extracted verbatim from final main text; **115/115**,100% pass.
- Both amended original near-nominal sentences have no old EvidenceBox reference. **0 old boxes affected,0 old excerpts rewritten,112 old excerpts preserved**. Before/after raw texts, stable anchors and SHA256 are saved in EXCERPT_PROTECTION_MAP.json; per-review excerpt hashes in EXCERPT_INDEX.json.
- Table5 entire source block unchanged. S1–S49 unchanged, all Figure files/references unchanged. **591** prior archive/Figure artifacts match their protected hashes; the three authorised source/registry edits are checked separately. Response outside R2-m2 is byte-identical; earlier closed scientific evidence is not rewritten.
- M9 remains `SCIENTIFIC_INTEGRATION_COMPLETE — FINAL_REPOSITORY_DOCUMENTATION_PENDING`; README, environment/reproduction documentation, final release commit and public-content review remain unfinished. R4/R3 shared matters remain Pending.

## PDF/build and visual checks

Build order: Supplementary → manuscript → Response letter. Latest sources match latexmk build-record MD5. Final pages: Supplementary57 (previous56), manuscript97 (previous96), Response letter75 (previous74).

Actual full-page144dpi renders inspected at native reading scale:
- Supplementary p57: all S50 rows, 90%/95% blocks, SDs and notes complete, readable, no crop/overlap; native table typography, no resizebox.
- Main p22,63–64,66,78: Methods, results, Table5 vicinity, run identity and both95% qualifications; new text and external S50 links red.
- Reply pp52–53: red response and blue exact evidence; Table S50 and Table5 references correct; no overflowing frame.

No undefined references, duplicate labels, horizontal overflow, oversized float or blocking compilation errors. Existing Springer template font/bookmark and1.41457pt vertical-box warnings retained and recorded, without unrelated cleanup. PDF_CHECK.json stores hashes, pages and actual visual-review record.

## Deliverables and remaining work

- R2minor2_LOCAL.patch: six-file incremental patch against this round's protected before snapshots.
- CELL_INDEX.json, ROW_INDEX.json, PROSE_CELL_INDEX.json, DEFINITION_INDEX.json, SOURCE_INDEX.json.
- INDEPENDENT_CHECK.csv, DATA_CHECK.json, verification scripts/logs, EXCERPT_PROTECTION_MAP.json, EXCERPT_INDEX.json, VERIFICATION.json.
- PDF_CHECK.json, render/, compile logs, LOCATIONS.json, DOCUMENT_HASHES.json and GIT_STATUS.txt.

No scientific or layout blocker remains for this local integration. Author review and later selective Git archive are still required; **do not mark CLOSED or start R2-m3**. Final page/line annotations remain deferred to full-revision assembly. M9 repository work is deliberately still pending.
