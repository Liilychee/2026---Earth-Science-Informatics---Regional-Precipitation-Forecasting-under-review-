# Git archive preparation

Fetched latest origin/main: `53a757ab603ef23a909ff27bdc9637212afa44b1`. Main author workspace remains on its original ae4cd53 baseline with mixed uncommitted changes; no pull/reset/clean or staging there. The remote additions since the last confirmed 4aabdcb baseline are R3-01–06 archives and R3-05 reply refinement. No existing remote path will be modified: this archive adds only the batch directory and allowlisted new R3-07–13 evidence paths.

A single independent worktree based on this remote main is used. Only explicit allowlisted files are staged; full paper/rebuttal sources, PDFs, before snapshots, raster page previews and raw datasets are excluded. Public scientific figure is archived as the author's unchanged PDF. Historical remote archive trees must remain byte-identical. A normal fast-forward push only is authorized; any concurrent remote advance/conflict stops the push.

Scientific archive commit/remote HEAD/file hashes will be written to the local FINAL_REMOTE_RECEIPT.json after successful remote readback. CLOSED is effective only on that successful receipt for R3-07–12; R3-13 stays OPEN. No claim of remote-only complete reproducibility is made.
