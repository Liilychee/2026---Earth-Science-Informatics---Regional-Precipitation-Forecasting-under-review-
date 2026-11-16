# Reproducibility limitations

- Only incremental evidence is archived. R3_19_SOURCES.patch applies to the external R3-18 after-state (hashes in BASE_AND_AFTER_HASHES.json; equals the remote-rebuildable R3-14–18 chain end) and contains no R4-M1 changes.
- q22 and q22c predictions, run records, scripts and logs are already archived (558da58, eae9d63) and are referenced by blob and SHA-256 in Q22_Q22C_REMOTE_INDEX.json, not re-uploaded. The hourly ERA5 box-mean CSV and raw ERA5/HRES files are not archived.
- Statistical intervals are pointwise, without multiplicity adjustment; recorded training times are not a computational benchmark.
- Full repository-only reconstruction of the paper is not available.
