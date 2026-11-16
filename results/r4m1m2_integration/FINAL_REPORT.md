# R4-M1 label fix + R4-M2 (lsp/tp) — local integration report (2026-11-16)

## Part 1 — R4-M1 stale location labels (Response letter only)
- R1 m3 ManuscriptChange: 'Introduction (study contributions and first ECMWF definition)' -> 'Introduction (first ECMWF definition); Section 2.5 (study objectives, formerly the contribution list in Section 1.1)'.
- R1 m3 box title: 'NLL and MSE definitions (Introduction, contributions; Section 3.3.2)' -> '(Section 2.5, objectives; Section 3.3.2)'. ECMWF/RMSE box title kept (sentence still in Introduction).
- R1 m4 ManuscriptChange: Introduction (temporal rationale); Section 2.3 (probabilistic scope, moved from Introduction); Section 2.2 (Rahman, TRU-NET); Section 2.5 (closing scope paragraph); former Section 1.1 statements now in Section 2.5, unchanged.
- R1 m4 box titles: 'Introduction' -> 'Introduction; Section 2.3'; 'Section 2, Related work' -> 'Section 2.2'; 'Section 2, closing paragraph' -> 'Section 2.5'.
- Further precision (still-correct 'Section 2' refs made specific): R1 M6 Lavers note -> 2.1; R3 Section 2 (CERRA) ManuscriptChange/box -> 2.1; R3 L169-177 (ML paragraph) ManuscriptChange/box -> 2.2. AuthorResponse prose unchanged.
- Scan: every hard-coded 'Section X.Y (Title)' in the letter matches the compiled manuscript numbering; only remaining '1.1' mentions are deliberate 'former Section 1.1'. No stale refs in manuscript/Supplementary.

## Part 2 — R4-M2
- Time semantics verified in code: windows X = rows i..i+5, y = row i+6 (q10_prepare_data.build_windows; analysis_q02b windows), 6-hourly rows; manuscript §3.2 already states lsp over (t0-1h,t0], target (t0+5h,t0+6h].
- Units: ERA5 m x1000 = mm per one-hour accumulation. Same-hour lsp - tp: max 3.43e-4 mm; 117 rows > 1e-4 mm; 0 rows > 1e-3 mm (numerical precision).
- Large-scale share (q02_lsp_share.csv reproduced exactly): ratio of summed lsp to summed tp over all 26,300 sampled regional-mean hours 2004-2021, dry hours included: All 61.95, DJF 71.99, MAM 60.14, JJA 50.92, SON 64.50 %. Training-only (18,410): 61.53 / 72.53 / 58.42 / 51.02 / 64.37 %. Median hourly ratio among wet hours (>=0.1 mm): 57.84 % (all).
- Lower-bound check (pipeline windows): training origins with latest lsp>=0.7 mm: 430; target<lsp(t0) 87.91 %, target<0.1 mm 39.77 %. lsp>=0.1 mm: 2285; 71.12 % / 47.13 %. Test: 105 origins (>=0.7), 86.67 % / 34.29 %.
- Ablation reused (q10_group_ablation.csv / q10_ablation_summary.csv): BiLSTM-Attn no_precip +0.004805 all [0.001980,0.008062], +0.019359 upper [0.005695,0.034165], 5/5 seeds; no_mxtpr_mntpr -0.000188; lsp alone -0.000511 (n.s.). BU-LSTM-Attn lsp alone -0.000870 (boot CI excludes 0, seed-t includes 0).
- Paper edits: manuscript §3.2, one red paragraph after the input-timing paragraph. No Supplementary table (share not previously present; numbers fit in text; full table in evidence CSV). §4.6/§5.3 unchanged, cited via EvidenceBoxes.
- Letter: R4 M2 reply + ManuscriptChange + 3 EvidenceBoxes (1 new §3.2 excerpt, 2 unchanged excerpts from §4.6 and §5.3). cp-as-input deferred to R4-M3.

## Verification
- Excerpts: 162/162 match canonical manuscript+Supplementary; 159 excerpts outside R4 M2 block identical and in order to baseline; 3 new in R4 M2.
- Compile: Supplementary 79 pp, manuscript 110 pp, Response letter 98 pp; no undefined refs; no overfull hbox; template-wide 1.41pt vbox warnings unchanged (220).
- Patches: R4_M1_LABELFIX_LOCAL.patch then R4_M2_LOCAL.patch rebuild after/ exactly from before/ via git apply and BSD patch (rebuild_check.sh).
- Renders: render/ms_p16.png (§3.2), rl_p22/p24 (R1 m3/m4), rl_p59 (CERRA), rl_p83-85 (R4 M2).

## Note for author
- R4 minor 8 (L.110) asks 'what if a predictor like lsp would be a reference? Consider it together with major comment 2.' Not handled here; the existing OLS L3 (tp and lsp) reference in Table 'reference forecasts' may be relevant when that item is answered.

## SHA-256
- cb22fcfd279f380cf6abe9063c00e5341e600193b4f027c6557902e0da0926ba  before/Response letter.tex
- 067683bf23d20e866ab82c0fff0ec03f2d186054553e62917e8a5344f8c165cb  before/Supplementary.tex
- a0eb8f27065e6789f531b37b7351101ec2948c0eb0bd179ee36c48f60efd4f78  before/manuscript.tex
- 137c59707308c31c5cee9b6bb7992ed6d0a01f462dd7131552abe75b509f20f5  before/sn-bibliography.bib
- 99b8ec1ea94a63adf0d95f8583846472a22555c809f31cbc7b5eac60b4c61daf  mid/Response letter.tex
- 067683bf23d20e866ab82c0fff0ec03f2d186054553e62917e8a5344f8c165cb  mid/Supplementary.tex
- a0eb8f27065e6789f531b37b7351101ec2948c0eb0bd179ee36c48f60efd4f78  mid/manuscript.tex
- 137c59707308c31c5cee9b6bb7992ed6d0a01f462dd7131552abe75b509f20f5  mid/sn-bibliography.bib
- 12cf66ee1eec4aac7498c74b4b1c2d830d7852d8530e4d84e2a9d51a4d80809c  after/Response letter.tex
- 067683bf23d20e866ab82c0fff0ec03f2d186054553e62917e8a5344f8c165cb  after/Supplementary.tex
- e09c84d2a667924192cff7ef76d4857adcf9c3c2edc5f27f4447f99c49473d08  after/manuscript.tex
- 137c59707308c31c5cee9b6bb7992ed6d0a01f462dd7131552abe75b509f20f5  after/sn-bibliography.bib
- 14caba513a97d9e4e0c1f33106c6ef9574de9de6756ac44cc6ed2480742d59ab  R4_M1_LABELFIX_LOCAL.patch
- 5740e3a8351b27cb37ebc1333a29b470cf2b7658f38f1e6d2e44aab90fda8ff0  R4_M2_LOCAL.patch
- 4545d977a048dcbb9c500079f1ce5170640c9babbfd9e2ebec65ddc7d326616c  evidence/R4M2_LOWER_BOUND_RECOMPUTE.csv
- c7da0a3b9d837ac031a389b7bf1e31d15a33526db1d492156a0c79fe42180b9d  evidence/R4M2_LSP_SHARE_RECOMPUTE.csv
- 2e96059a1db8ada09dce26e88844a90c01c2e02e39fa6d1e3a81d0ed4cc841c1  evidence/R4M2_SAME_HOUR_CHECK.json
- ce0f3f174e141d10fd14e881f1655d2aa2229cd404b5a05aadfd5707e9f465be  evidence/r4m2_lsp_semantics_check.py
- 995437b8e75349befd42da064413944ffc58a2c67a48d4a0456153dc5ab81a79  evidence/verify_excerpts.py
- data/dublin_regional_reduced.csv 1a384092ef6f78e5ed757d50db5fbaaff11baf64fcf1779ca3629e76e847d45f (source, not copied)
