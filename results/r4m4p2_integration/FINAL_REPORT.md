# R4-M4 P2 — local implementation report (2026-11-16)

Scope: P2 only. P3–P6, the R4-M4 reply, EvidenceBoxes, Supplementary, BibTeX and the template are untouched.

## Change
- manuscript.tex, §5.2 (`sec:upper_tail_discussion`), the paragraph starting "This change in ranking illustrates a limitation of aggregate forecast metrics." (source line 1220).
- The approved text is appended after "More detections therefore did not translate into reliable high-threshold warnings.", inside the existing `{\color{red} ... \par}` block, wrapped in `\revminor{...}` so the citation link is also red (same nesting as P1, compiles cleanly). Existing sentences are unchanged.
- Patch: R4_M4_P2_LOCAL.patch (manuscript.tex, 1 hunk), rebuilt from before/ with git apply and BSD patch → identical to after/.

## Literature check
- GMD abstract (gmd.copernicus.org/articles/13/2631/2020/): "The limited ability of RainNet to predict heavy rainfall intensities is an undesirable property ... which we attribute to a high level of spatial smoothing introduced by the model"; "pronounced features of intense precipitation tend to get lost over longer lead times". This supports "spatial smoothing and reduced representation of intense rainfall features".
- The new text keeps the task difference explicit (radar spatial nowcasts vs regional-mean ERA5). It offers the study only as a comparison and leaves the causes in our models unresolved. No mechanism, MSE causation, identity of mechanisms, equivalent design or peak delay is claimed. It is consistent with the preceding sentences (compression not isolated; no event-wise peak delay) and with P1 (conditional upper-tail diagnostics).

## Checks
- BibTeX: `ayzel2020rainnet` present once; resolved; reference list p.104, "Ayzel G, Scheffer T, Heistermann M (2020) Rainnet v1. 0: ... Geoscientific Model Development 13(6):2631--2644".
- Metadata gaps (report only, BibTeX not modified): no `doi` (10.5194/gmd-13-2631-2020); title "v1. 0" has a stray space and is unbraced, so sn-basic lower-cases it to "Rainnet". Writing `{RainNet v1.0}` would keep the case.
- Citation style: `\citep`, renders "(Ayzel et al 2020)"; no new `\citet` (9 occurrences, all the accepted E1–E9).
- EvidenceBox: the target paragraph overlapped no excerpt before the edit; 170/170 matched, identical and in order; Response letter unchanged. P1 and the citation-unification edits are intact.
- Builds: manuscript 113 pp (was 112), Supplementary 80 pp, Response letter 102 pp; no errors, 0 undefined citations or references, 0 multiply defined labels.
- Layout: no overfull \hbox. The overfull count went 111 → 112 only because of the extra page (the template's per-page 1.41 pt \vbox). Render: render/manuscript_p087_P2.png.
