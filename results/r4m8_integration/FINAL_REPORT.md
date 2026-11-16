# R4 minor 8 (reference forecasts; lsp as reference) — local integration report (2026-11-16)

## Audit
- First "reference forecasts": Abstract (manuscript.tex l.53) and objective 1 in §2.5 (reviewer's original L.110). Neither was defined there; definitions only in §3.3.1. Neither phrase is quoted in any EvidenceBox.
- Definitions (§3.3.1, verified in code/analysis_q07b_linear_baselines.py and q07 outputs):
  - Persistence: y_hat = tp(t0) (preceding hour at origin); not fitted. RMSE 0.328187.
  - Climatology: overall training mean (original) + training-fitted UTC-hour/seasonal/monthly/month×hour means; RMSE 0.2730–0.2738.
  - AR(1): least squares a + b·tp(t0), training only. RMSE 0.262659.
  - Ridge L1: 42 inputs (6 snapshots × 7, incl. lsp); L2: 7 origin inputs (incl. lsp(t0)); alpha selected on validation. RMSE 0.249733 / 0.253177.
  - OLS L3: LinearRegression on [tp(t0), lsp(t0)] (columns tp0/lsp0 = row W−1 of each window = origin); target tp(t0+6h) = hour (t0+5h, t0+6h]; fitted on 18,404 training windows; coefficients intercept 0.0755, tp 0.3237, lsp −0.0576. RMSE 0.262894. No target-hour information. Same 3,939 test targets. Test predictions computed in-script (not saved to file); metrics and paired comparisons saved (q07b_*.csv).
- L3 is NOT an lsp persistence forecast; it is AR(1) plus origin-time lsp. No reference uses lsp alone.
- Paired model − L3 (q07b_model_minus_linear.csv; circular block 28, 2,000 reps, seed 42; single saved predictions): RMSE −0.0191 XGB, −0.0038 Transformer (CI incl. 0), −0.0142 BU-LSTM, −0.0200 BiLSTM-Attn, −0.0164 BU-LSTM-Attn, −0.0148 Prob BiLSTM-Attn; AUC_Q95 +0.0529..+0.1024, AUC_1.0 +0.0935..+0.1399, all CIs exclude 0. Not previously reported in the paper.

## Decision on extra computation
- Not required: L3 vs AR(1) directly answers whether lsp adds to a persistence reference, and model-vs-L3 paired results exist. Reply states that no lsp-only reference was constructed.
- Optional read-only proposal (NOT run): on the 3,939 test targets, (a) raw lsp(t0) as forecast of tp(t0+6h) and (b) OLS on lsp(t0) alone fitted on training windows; RMSE/MAE/AUC + paired block bootstrap vs models. Diagnostic, uncalibrated in (a); must never use target-hour lsp.

## Edits
- Abstract and §2.5 objective 1: "reference forecasts" → "statistical reference forecasts (climatology, persistence and linear regression)"; objective adds pointer to §3.3.1.
- §3.3.1: new red paragraph (role of persistence/climatology; where lsp enters references; origin-only data; same test set).
- §4.2.1: new red paragraph (L3 vs AR(1); collinear coefficients; paired model−L3 RMSE/AUC).
- Letter: R4 m8 block (reply, ManuscriptChange, 3 EvidenceBoxes). Consistent with R4-M2 (0.7 mm/430/87.9%) — no R4-M2 text changed.
- Note: objective 1 text is now edited after R1 m4 / R4-M1 described the objectives as retained/moved unchanged; those statements remain accurate for their own steps but author may want to be aware.

## Verification
- Excerpts 170/170 match; 167 outside R4 m8 identical and in order; 3 new.
- Compile: Supplementary 80 pp, manuscript 112 pp, Response letter 102 pp; no undefined refs; no overfull hbox.
- Renders: render/ms_p1, ms_p11, ms_p21, ms_p55; rl_p90–91.
- R4_m8_LOCAL.patch rebuilds after/ from before/ via git apply and BSD patch; before == r4m3_integration/after.

## Remaining limitations
- No lsp-only reference; L3/model comparisons use single saved predictions, one split, pointwise unadjusted intervals; L3 test predictions not saved as a file.

## SHA-256
- 8e6c75f46b30ec388e306b3f2bbdfb1fa3004f6d0869bf51f73a336513cc5ccb  before/Response letter.tex
- 2df7e160574947361e653cf78eda9f5c0ac86eb30f841282dadb4c988efda3fd  before/Supplementary.tex
- 8920ad956ee17a528b9ce390346197ed73cfb1d76cf78f4b9eb701546d7dff6f  before/manuscript.tex
- 137c59707308c31c5cee9b6bb7992ed6d0a01f462dd7131552abe75b509f20f5  before/sn-bibliography.bib
- 4a53015dda79356df2b600c4317fd72ad6a1c510bebfee08109f115e89564442  after/Response letter.tex
- 2df7e160574947361e653cf78eda9f5c0ac86eb30f841282dadb4c988efda3fd  after/Supplementary.tex
- d65be30545d00d9740985e95c65d2a9643c5ffddc615d3c0e292beccfa0f67ea  after/manuscript.tex
- 137c59707308c31c5cee9b6bb7992ed6d0a01f462dd7131552abe75b509f20f5  after/sn-bibliography.bib
- 9601384f624a32fa632e42cd4379d51712f9ae4a46fc62441796b96e93a9ff5d  R4_m8_LOCAL.patch
- 66b5dc006ab6cd4648972d78e6d1186c712fd69bdde9f827e6d98ef258cab698  evidence/q07b_linear_baselines.csv
- 586ca2a77839dec3329d52cead36fb22d63bcf66593108368ca568d8f11f5bd4  evidence/q07b_model_minus_linear.csv
- e21d0cf4c6c98a961bcb36aeb17ecf98e7e6f4fbb726598f672d5c3d306de04c  evidence/verify_excerpts.py
