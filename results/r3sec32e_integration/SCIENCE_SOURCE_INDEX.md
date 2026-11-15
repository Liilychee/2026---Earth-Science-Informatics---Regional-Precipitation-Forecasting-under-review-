# R3-08 source-to-claim index

Official reference (accessed this turn): https://confluence.ecmwf.int/spaces/CKB/pages/76414402/ERA5+data+documentation
- Instantaneous parameters: section Instantaneous parameters and Table 2; u10/v10/t2m/d2m/sp/tcc; native units m/s, K, Pa, fraction.
- Accumulations: section Mean rates/fluxes and accumulations and Table 3; reanalysis processing period is the hour ending at validity time; tp/lsp/e (m), ssr (J/m2).
- Hourly extrema: section Minimum/maximum since previous post processing and Table 5; mxtpr 228226 and mntpr 228227; kg m-2 s-1; extrema over the preceding processing hour, not mean rates.
- CDS analyses vs short forecasts and publication latency: existing R2-M2 evidence/closed response retained.

Existing raw-metadata evidence: results/r2m2_integration/evidence/check_r2m2.txt, section 3 (line92 onward): archived raw ERA5 extension-file headers identify tp/lsp as accum and mxtpr/mntpr as max/min, dataType fc, correct units. These are 1992–2003 extension headers, not newly opened 2004–2021 original GRIB headers. Reused as existing corroboration, not claimed as a fresh raw-file verification. Original exported CSV does not retain GRIB processing-period metadata; official product definitions establish the one-hour duration. Local raw NetCDF reopening was not performed (xarray/netCDF4/h5py unavailable in selected runtime); no new dependency installed.

Main pipeline: results/r2m2_integration/evidence/Interpretable_analysis.ipynb cell8 (zero-based, In[8]), lines50–55: groupby(valid_time).mean and tp*1000; lines126–150: final seven variables and train-fit X/Y StandardScaler; lines166–225: six rows to next sampled-row target, continuity and six-hour gap assertion. Full extracted cells in NOTEBOOK_SOURCE_EXTRACT.txt. Cell3 reads the already sampled original CSV. No fresh ERA5 download or data regeneration.
q10 reconstruction: results/r2m8_integration/source/q10_prepare_data.py lines28–40: read CSV, spatial mean, only tp*1000; lines50–59: train-only scaling. This is confirmation of the main preprocessing, not an executed rebuild.
Existing run evidence check_r2m2.txt section2: 26,300 timestamps, hours[0,6,12,18], all adjacent steps6h, 25 grid cells per main time; native predictor magnitudes. This supports subsampling; no claim that the unavailable original retrieval/generation log has newly been recovered.

No conflict with closed R2-M1/M2 detected. Valid-time ordering is distinct from operational availability; known same-cycle/assimilation limitations remain. No original 78% envelope ambiguity or unverified extremum-consistency percentages are used to justify this response.
