# R3-08 author-approved concise response

Only the R3 Section3.2(e) AuthorResponse in Response letter.tex was edited. Main/Supplementary/bibliography/Figures and all three R3-08 EvidenceBoxes/position text remain byte-identical. All135 current excerpts are unchanged and match current main/Supplementary. Other reviewer responses (including R3-09) unchanged.

The concise version follows the author's three-paragraph structure. It uses “fields” for the list that includes the tp target, the existing ECMWF cite key, automatic section refs, and “does not directly include a value from the target hour” to avoid an unsupported general no-information-leakage statement.

Whitespace-delimited word tokens273→143 (LaTeX tokens included, not a formal prose word count). Ordered three-document build passed; reply pp65–66 actually rendered and inspected: red response/blue boxes, correct references, no clipping/overlap. Main/Supplementary required no rebuild changes. Reply no undefined refs/citations, overfull or blocking errors; original main template vbox warning retained.

No Git staging, commit or push. R3-08 remains local scientific revision complete — Git archiving deferred.

## Final response

We thank the reviewer for highlighting these distinctions. We retained the ERA5 values at 00, 06, 12 and 18~UTC without additional temporal aggregation. The fields preserve their native temporal meanings: u10, v10, t2m, d2m, sp and tcc represent instantaneous conditions; tp, lsp, e and ssr represent preceding-hour accumulations; and mxtpr and mntpr represent the maximum and minimum precipitation rates within the preceding hour \citep{ecmwf_era5_documentation}.

These variables were aligned by their valid timestamps and spatially averaged over the study domain. No conversion to a common temporal window was performed. In the main forecasting pipeline, predictor values were standardized using training-period statistics, which does not alter their temporal meanings.

The latest input at $t_0$ therefore does not directly include a value from the target hour $(t_0+5\,\mathrm{h},t_0+6\,\mathrm{h}]$. We have clarified these distinctions in Section~\ref{manuscript-sec:dataset} and acknowledge the omitted hourly evolution and retrospective reanalysis setting in Section~\ref{manuscript-sec:limitations}.
