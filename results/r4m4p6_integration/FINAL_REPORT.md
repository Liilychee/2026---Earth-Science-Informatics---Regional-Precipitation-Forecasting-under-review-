# R4-M4 P6 — local implementation report (2026-11-16)

Scope: P6 only (two locations in §5.4). P1–P5, the R4-M4 reply, EvidenceBoxes, Supplementary, BibTeX and the template are untouched.

## Changes (R4_M4_P6_LOCAL.patch, manuscript.tex, 2 hunks)
1. Source line 1295, the station-limitation paragraph ("The independent observational assessment is limited to one airport station ..."). The approved Lavers sentences are appended after "Our conclusions remain restricted to ERA5-derived regional-mean precipitation over Dublin.", inside the existing red group, wrapped in `\revminor`.
2. Source line 1322, the HRES-scope paragraph ("The archived NWP reference also has a restricted scope. ..."). The approved WeatherBench 2 sentences are appended after "... season-specific training was examined only for XGBoost.", inside the existing red group, wrapped in `\revminor`.
- Both paragraphs matched the read-only audit. Approved text inserted verbatim. The patch rebuilds from before/ with git apply and BSD patch → identical to after/.

## Protection
- Excerpt 31 (R1 M6) quotes paragraph 1 in full and ends exactly at its last sentence. Only appending was done, and the excerpt still matches. Paragraph 2 is not quoted.
- 170/170 matched, identical and in order. P1–P5 citations intact. The Results HRES paragraph (1,970 samples; RMSE/AUC results) is unchanged.

## Literature ↔ claim
- Lavers et al. 2022 (QJRMS 148:3152–3165): ERA5 24-h totals vs 5,637 gauges, with a general wet bias and lower annual maximum one-day amounts. This supports "biases in daily precipitation and underrepresentation of the largest observed daily totals". The text limits it to daily precipitation over a broad domain and makes no claim about Dublin hourly bias or about the models' underestimation being caused by ERA5. §2.1 (l.80) already summarises Lavers with the caveat that daily-scale findings do not establish Dublin hourly accuracy; the two are consistent, with mild repetition.
- Rasp et al. 2024 (WeatherBench 2; arXiv 2308.15560 HTML, §3.1, §3.3.1, §6.1):
  - "For evaluating IFS forecasts, we use operational analyses as ground truth rather than ERA5".
  - "for precipitation accumulations we use ERA5 as a precipitation ground truth for all models".
  - ERA5 precipitation "sometimes shows large differences to rain gauge measurements".
  - These support the approved wording. The text claims no bias in favour of HRES or ML; it states that the net effect is not quantified and keeps the accumulation-window mismatch.

## Consistency with closed items
- R1-M6: station limits unchanged (single airport station, spatial support, accumulation window, indicator 111, label experiment). The addition reinforces the existing separation of ERA5-referenced evaluation from observational validation (cf. l.1200).
- R3-13: HRES limits unchanged (1,970 06/18 UTC samples, six-hour mean vs final-hour target, station support, shared IFS framework, not a fully equivalent-window comparison).
- P1–P6 together: conditional upper-tail diagnostics (P1), amplitude compression context (P2), complexity (P3), B–G context (P4), XAI caution (P5), ERA5/HRES verification limits (P6). No contradictions found.

## Checks
- BibTeX: lavers2022evaluation ×1 (DOI 10.1002/qj.4351), rasp2024weatherbench ×1 (DOI 10.1029/2023MS004019); both resolved. They render "(Lavers et al 2022)" and "(Rasp et al 2024)". BibTeX unchanged; `\citet` occurrences 9 (accepted E1–E9).
- Reference-list issues (report only):
  - Rasp pages print "e2023MS004,019"; moving the number to `eid` fixes this, as with Aas/Mamalakis.
  - The author list has "Russel, Tyler", likely "Russell"; please verify.
- Builds: manuscript 115 pp (was 114), Supplementary 80 pp, Response letter 102 pp; no errors, 0 undefined, 0 multiply defined.
- Layout: no overfull \hbox. The overfull count went 113 → 114 because of the extra page (per-page 1.41 pt \vbox template artefact). Renders: render/manuscript_p097_P6a.png, render/manuscript_p101_P6b.png.
