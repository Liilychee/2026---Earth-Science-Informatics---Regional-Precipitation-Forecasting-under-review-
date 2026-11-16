# Science audit — R3-13 status correction and R3-19

## R3-13 (Reviewer 3, Section 3.3.1)
Status correction only (results/r3nwp_status_correction/). Evidence unchanged from archive 8f9c52f: 1,970 common targets; final-hour-target RMSE HRES six-hour mean 0.2061, BiLSTM-Attention 0.2428, XGBoost 0.2443 mm/h; ERA5 six-hour-mean diagnostic 0.1882 mm/h using post-origin verifying ERA5 information in the test period (not an available forecast, not a strict lower bound); Dublin Airport auxiliary check. Limitations retained in §4.2.2/§5.4/S3–S6/S60: window mismatch, no ranking under a strictly matched target, shared-IFS origin, station-comparison limits. No text, numbers or excerpts changed.

## R3-19 (Reviewer 3, Lines 979–982)
Reviewer comment: "It is better to use hourly ERA5 data and still forecast at 6h lead time. This way, you will have more data to train and validate the model."

| Check | Result |
|---|---|
| Configurations | A, B (q22, 20 runs; archive 558da58) and CA, CB (q22c, 20 runs; archive eae9d63) |
| Training samples | A/B 4,374 (00/06/12/18 UTC issue times); CA/CB 26,244 (hourly; synoptic subset equals A/B set) |
| Validation / test | 1,458 (2020) / 1,454 (2021), identical for all four configurations; 6-h lead; final-hour target (t0+5 h, t0+6 h] |
| Leakage / scaling | No input after issue time; no window crosses a split; scalers from 00/06/12/18 UTC training stamps only (q22/q22c check logs) |
| Models / seeds | XGBoost, BiLSTM-Attention; seeds 42, 123, 7, 2024, 99; RTX 4090 |
| Hourly-data reproduction | 7,304 six-hourly stamps reproduce the main regional series (max diff/SD 5.6e-5; identical event labels) |
| Independent recomputation | q22 A/B effects ≤4e-8; q22c 24 RMSE rows ≤2.4e-8 vs saved CSV; seed counts identical |

Primary CB−A (overall RMSE): XGBoost −1.57% (5/5 seeds; seed-t excludes 0, block includes 0); BiLSTM-Attention −1.86% (4/5; both include 0). No robust overall improvement is established, and no absence of benefit is established. Exploratory B−A −1.08/−0.74%, CA−A −0.92/−1.89%, CB−CA −0.65/+0.03%, CB−B −0.49/−1.12%. CB−A wet and upper-tail RMSE 2.3–6.0% lower in 5/5 seeds for both models (exploratory, unadjusted).
Limitations: 2017–2021 only; one test year; two models; CA/CB designed after A/B results; lag-1 target autocorrelation 0.89; XGBoost seeds are not independent data replications; six-fold optimization steps per epoch with untuned protocol; no full 2004–2021 or rolling-origin repetition.
