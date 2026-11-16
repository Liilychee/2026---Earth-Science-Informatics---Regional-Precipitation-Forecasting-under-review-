# R4-M4 — P1–P6 verbatim Discussion extraction (READ-ONLY)

Base: current manuscript.tex, identical to results/r4m8_integration/after/ (the audit base). No file modified.
Text below is copied programmatically from the LaTeX source lines (verbatim, including LaTeX markup).

## P1
### P1-a — source line 1214–1216 — §5.2 Performance under Upper-Tail Precipitation and Probabilistic Reliability
- First sentence: "A different model ranking emerged when the analysis was restricted to upper-tail precipitation."
- Citations in paragraph: none
- EvidenceBox protection: none (0/5 sentences quoted in any EvidenceBox)

```latex
A different model ranking emerged when the analysis was restricted to upper-tail precipitation. BiLSTM-Attention and XGBoost performed similarly over the full test set, while XGBoost achieved lower RMSE at the higher precipitation thresholds. The separate revised-wet comparison ($\geq0.1$~mm\,h$^{-1}$; $N=854$) also favoured XGBoost, with a paired RMSE difference of $+0.016144$~mm\,h$^{-1}$ (BiLSTM-Attention minus XGBoost) and a pointwise 95\% interval of $[+0.007102,+0.025956]$~mm\,h$^{-1}$. This evidence comes from the original single saved predictions, not from the legacy wet interval or five-seed mean scores. The paired upper-tail comparison supports an XGBoost advantage more clearly than the complete-test comparison (Section~\ref{sec:regime_results}).
```

### P1-b — source line 1218–1220 — §5.2 Performance under Upper-Tail Precipitation and Probabilistic Reliability
- First sentence: "This change in ranking illustrates a limitation of aggregate forecast metrics."
- Citations in paragraph: none
- EvidenceBox protection: none (0/6 sentences quoted in any EvidenceBox)

```latex
This change in ranking illustrates a limitation of aggregate forecast metrics. Overall RMSE is dominated by common low amounts, while predictions substantially compress the observed upper tail (Section~\ref{sec:amplitude_diagnostics}). The BU-LSTM-Attention calibration slope, standard-deviation ratio and correlation are consistent with a limited-skill conditional-mean forecast, but do not isolate whether limited predictors, event scarcity, the objective or other model choices dominate the compression. The restricted three-sample timing diagnostic cannot establish an event-wise peak delay because selected samples are not independent storm peaks and some windows overlap. Low CSI at the fixed 1.0~mm\,h$^{-1}$ rule must also be distinguished from ranking ability: AUC remained approximately 0.82--0.87, yet validation-selected cutoffs produced FAR of approximately 0.86--0.92 (Section~\ref{sec:event_detection}). More detections therefore did not translate into reliable high-threshold warnings.
```

### P1-c — source line 1231 — §5.2 Performance under Upper-Tail Precipitation and Probabilistic Reliability
- First sentence: "The performance of XGBoost in the upper-tail subset should not be interpreted as evidence that tree-based models were generally superior to the deep-learning mo"
- Citations in paragraph: ['grinsztajn2022tree']
- EvidenceBox protection: none (0/6 sentences quoted in any EvidenceBox)

```latex
The performance of XGBoost in the upper-tail subset should not be interpreted as evidence that tree-based models were generally superior to the deep-learning models. BiLSTM-Attention remained numerically best for the overall point-forecast comparison, and the difference from XGBoost was small. The clearer advantage of XGBoost appeared only in the upper tail of the precipitation distribution. One possible explanation is that tree-based models can partition predictor space effectively without requiring the same amount of repeated examples needed to estimate complex neural-network representations. This pattern is broadly consistent with evidence that tree-based methods can match or exceed deep neural networks on tabular data, particularly under limited or imbalanced sample sizes \citep{grinsztajn2022tree}. This may be useful when high-intensity rainfall events are relatively sparse, although the present experiments do not establish the underlying mechanism directly.
```

### P1-d — source line 1237 — §5.2 Performance under Upper-Tail Precipitation and Probabilistic Reliability
- First sentence: "Prediction intervals widened as rainfall intensity increased, but the additional width was insufficient to maintain nominal coverage for the strongest events."
- Citations in paragraph: none
- EvidenceBox protection: none (0/3 sentences quoted in any EvidenceBox)

```latex
Prediction intervals widened as rainfall intensity increased, but the additional width was insufficient to maintain nominal coverage for the strongest events. This result shows that near-nominal \textcolor{red}{95\%} coverage over the complete test distribution can conceal substantial undercoverage in a less frequent but meteorologically important regime. Reporting only overall coverage would therefore give an incomplete assessment of probabilistic forecast reliability.
```

## P2
### P2-a — source line 1218–1220 — §5.2 Performance under Upper-Tail Precipitation and Probabilistic Reliability
- First sentence: "This change in ranking illustrates a limitation of aggregate forecast metrics."
- Citations in paragraph: none
- EvidenceBox protection: none (0/6 sentences quoted in any EvidenceBox)
- Full text: identical to P1-b above.

### P2-b — source line 1227–1229 — §5.2 Performance under Upper-Tail Precipitation and Probabilistic Reliability
- First sentence: "The fixed-rule event results sharpen the limitation identified by the amplitude diagnostics."
- Citations in paragraph: none
- EvidenceBox protection: R2 M4 (7/7 sentences quoted)

```latex
The fixed-rule event results sharpen the limitation identified by the amplitude diagnostics. Compressed forecast amplitudes led to few or no forecasts at high fixed thresholds and consequently many misses. This is an observed property of these saved predictions, not a causal diagnosis of why their amplitudes are compressed. Persistence achieved higher fixed-rule CSI at the four thresholds examined above, yet its own FAR ranged from approximately 0.72 to 0.89, so it was not a reliable high-intensity warning system either. Higher learning-model AUC indicates useful event ranking but does not guarantee skill when the predicted mean is compared directly with the physical intensity threshold. Validation-selected cutoffs constitute another operating rule and recover some detections at a large false-alarm cost; their intervals omit selection uncertainty. The existing experiments do not identify whether predictors, event scarcity, loss functions or other modelling choices are the dominant cause of amplitude compression.
```

### P2-c — source line 1312–1314 — §5.4 Limitations and Future Work
- First sentence: "A further limitation is the relative scarcity of high-intensity regional-mean precipitation: only 402 training samples reached 1.0~mm\,h$^-1$."
- Citations in paragraph: none
- EvidenceBox protection: none (0/8 sentences quoted in any EvidenceBox)

```latex
A further limitation is the relative scarcity of high-intensity regional-mean precipitation: only 402 training samples reached 1.0~mm\,h$^{-1}$. The loss and weighting sensitivity experiments have already examined Huber, pseudo-Huber, sample weighting, log1p-target and Tweedie objectives in the specified model settings (Section~\ref{sec:training_objective_sensitivity}). Huber worsened BiLSTM-Attention but improved the Transformer in overall RMSE at $\delta=2$. Both Transformer configurations frequently approached the 30-epoch limit, and its wet- and upper-tail seed-based intervals included zero; no intrinsic advantage under fully converged training is established. XGBoost weighting improved tail RMSE on five-seed mean predictions at a substantial cost in overall error and M3's own positive bias. This aggregation is distinct from the mean of five seed-level RMSE values in the main comparison. These experiments do not exhaust objective functions or model configurations and cannot identify a dominant cause of underestimation. The peak-timing diagnostic is limited to neighborhoods of the largest sampled amounts, with overlapping windows and a selected sample that is not a local observed maximum; it does not establish delays of independent storm peaks.
```

## P3
### P3-a — source line 1185–1187 — §5.1 Overall Forecasting Performance and Model Robustness
- First sentence: "The results show that several machine-learning and deep-learning models achieved similar levels of performance for short-term regional precipitation forecasting"
- Citations in paragraph: none
- EvidenceBox protection: none (0/7 sentences quoted in any EvidenceBox)

```latex
The results show that several machine-learning and deep-learning models achieved similar levels of performance for short-term regional precipitation forecasting over Dublin. Across five fixed random seeds, BiLSTM-Attention obtained the lowest mean RMSE of 0.2429~mm\,h$^{-1}$, followed closely by XGBoost at 0.2439~mm\,h$^{-1}$. The difference between the two models was small relative to the overall forecast error. The paired block-bootstrap analysis showed no clear RMSE difference for the complete test set. The legacy wet-subset interval is retained only for its original definition. For the revised wet subset ($\geq0.1$~mm\,h$^{-1}$), the separate single-saved-run comparison supports lower RMSE for XGBoost, as reported in Section~\ref{sec:overall_results}; it is not a five-seed comparison. The main result is therefore not that one model consistently outperformed all alternatives, but that a relatively compact recurrent model and a tree-based machine-learning model produced comparable overall point forecasts under the same data and evaluation protocol.
```

### P3-b — source line 1189 — §5.1 Overall Forecasting Performance and Model Robustness
- First sentence: "The comparison between BiLSTM-Attention and the otherwise identical BiLSTM-NoAttention control isolates the temporal attention layer."
- Citations in paragraph: none
- EvidenceBox protection: R3 L822-824 (5/5 sentences quoted)

```latex
\revminor{The comparison between BiLSTM-Attention and the otherwise identical BiLSTM-NoAttention control isolates the temporal attention layer. Attention reduced mean RMSE from 0.2447 to 0.2429~mm\,h$^{-1}$ (paired difference $-0.0018$~mm\,h$^{-1}$, $-0.73\%$); all five seeds improved, and both the seed-t and moving-block intervals, each $[-0.0033,-0.0003]$~mm\,h$^{-1}$, excluded zero. After Holm adjustment over the 16 all-target RMSE comparisons in Supplementary Table~\ref{supp-stab:r3sig_pairs}, however, the adjusted $p$ values were 0.17 (seed-t) and 0.13 (block), and the wet and upper-tail differences were not clearly separated. The attention layer added 8,320 trainable parameters (36,993 to 45,313). The gain is therefore consistent in sign but small, and it is not established after multiplicity adjustment.}
```

### P3-c — source line 1191 — §5.1 Overall Forecasting Performance and Model Robustness
- First sentence: "Greater model complexity was not matched by clear gains in point accuracy."
- Citations in paragraph: none
- EvidenceBox protection: R3 L822-824 (8/8 sentences quoted)

```latex
\revminor{Greater model complexity was not matched by clear gains in point accuracy. BiLSTM-Attention and XGBoost differed by $-0.0011$~mm\,h$^{-1}$ ($-0.43\%$) overall, with both intervals including zero, whereas XGBoost had lower RMSE in the wet ($+2.4\%$) and upper-tail ($+3.6\%$) subsets, with all five seeds and both intervals favouring it; in the rolling-origin evaluation, the pooled difference slightly favoured XGBoost but depended on block length (Section~\ref{sec:rolling_origin_results}). BU-LSTM, BU-LSTM-Attention and Probabilistic BiLSTM-Attention had 1.3--2.2\% higher overall RMSE than XGBoost in all five seeds, and adding attention to BU-LSTM (159,272 additional parameters) produced no clear RMSE or CRPS improvement. All models except the Transformer had lower RMSE than AR(1) after Holm adjustment. In the recorded runs, training the neural models took about 105--393~s per seed, compared with 0.1--0.4~s for XGBoost, but timer definitions differ, the XGBoost device was not recorded and inference time was not benchmarked (Supplementary Table~\ref{supp-stab:r3sig_cost}). For point forecasts in this setting, XGBoost therefore provided comparable overall accuracy and better wet and upper-tail accuracy, with much shorter recorded training times that do not constitute a unified computational-cost benchmark. The probabilistic models are justified only where predictive distributions are required, and their upper-tail undercoverage remains a limitation. These conclusions apply to this regional ERA5 target, the 6-h lead time and the tested configurations, without a formal cost--benefit criterion.}
```

### P3-d — source line 1195–1197 — §5.1 Overall Forecasting Performance and Model Robustness
- First sentence: "The stronger-reference comparisons narrow the interpretation of model gains."
- Citations in paragraph: none
- EvidenceBox protection: none (0/6 sentences quoted in any EvidenceBox)

```latex
The stronger-reference comparisons narrow the interpretation of model gains. Only three saved learning-model predictions had statistically supported RMSE improvements over the 42-input Ridge reference, and the available seasonal specialization test does not establish a general benefit of season-specific models. The HRES comparison is unfavourable to claims of NWP competitiveness: its ERA5 RMSE was lower than that of all six learning models, and its airport event AUC was higher. The six-hour versus final-hour accumulation mismatch, regional versus station support, and shared IFS framework must nevertheless be retained in interpreting these results. Shared modelling structure could favour HRES when ERA5 is the target, but its effect was not separately quantified; station verification does not remove the other mismatches. No end-to-end computational-cost advantage was measured or established.
```

## P4
### P4-a — source line 1233–1235 — §5.2 Performance under Upper-Tail Precipitation and Probabilistic Reliability
- First sentence: "The probabilistic forecasts showed a similar dependence on rainfall intensity."
- Citations in paragraph: none
- EvidenceBox protection: none (0/5 sentences quoted in any EvidenceBox)

```latex
The probabilistic forecasts showed a similar dependence on rainfall intensity. When evaluated over the complete test set, empirical coverage of the nominal 95\% prediction interval ranged from approximately 0.956 to 0.958 across the five-seed experiments. In the separate single-saved-run diagnostic in Figure~\ref{fig:prob_coverage}, legacy-wet coverage ranged from 0.9340 to 0.9452, whereas revised-wet coverage was 0.7693--0.7927 and upper-tail coverage was 0.4370--0.5000. The inclusion of near-zero amounts in the legacy subset may contribute to its higher aggregate coverage; these descriptive contrasts do not identify the cause of undercoverage. The Figure~\ref{fig:prob_coverage} values are not five-seed means.
```

### P4-b — source line 1237 — §5.2 Performance under Upper-Tail Precipitation and Probabilistic Reliability
- First sentence: "Prediction intervals widened as rainfall intensity increased, but the additional width was insufficient to maintain nominal coverage for the strongest events."
- Citations in paragraph: none
- EvidenceBox protection: none (0/3 sentences quoted in any EvidenceBox)
- Full text: identical to P1-d above.

### P4-c — source line 1239 — §5.2 Performance under Upper-Tail Precipitation and Probabilistic Reliability
- First sentence: "The Gaussian likelihood also imposes a structural limitation on the uncertainty estimates."
- Citations in paragraph: none
- EvidenceBox protection: none (0/7 sentences quoted in any EvidenceBox)

```latex
The Gaussian likelihood also imposes a structural limitation on the uncertainty estimates. Precipitation is non-negative and strongly right-skewed, whereas the Gaussian distribution is symmetric and unbounded. In the single-run diagnostic, the lower bound of the nominal 95\% interval extended below 0~mm\,h$^{-1}$ throughout the test set. Negative interval bounds do not correspond to physically meaningful precipitation and indicate a mismatch between the assumed predictive distribution and the support of the target variable. The Gaussian formulation remains a baseline. The controlled Bernoulli--Gamma comparison removed negative bounds and improved overall probabilistic scores, but substantial upper-tail undercoverage remained. This comparison was limited to Probabilistic BiLSTM-Attention; it does not establish the same benefit for other architectures, test periods or event-detection rules.
```

### P4-d — source line 1243–1245 — §5.2 Performance under Upper-Tail Precipitation and Probabilistic Reliability
- First sentence: "An alternative precipitation-appropriate likelihood improved overall probabilistic skill and eliminated negative prediction bounds by construction, but substant"
- Citations in paragraph: none
- EvidenceBox protection: R2 M6 (3/3 sentences quoted)

```latex
An alternative precipitation-appropriate likelihood improved overall probabilistic skill and eliminated negative prediction bounds by construction, but substantial upper-tail undercoverage remained. The comparison does not isolate the likelihood family from changes in output parameterization, loss and training-target scale. It supports the tested Bernoulli--Gamma formulation within this backbone, not a general claim that it improves every architecture or rare-event diagnostic.
```

### P4-e — source line 1316–1318 — §5.4 Limitations and Future Work
- First sentence: "The probabilistic formulation also warrants further development."
- Citations in paragraph: none
- EvidenceBox protection: none (0/5 sentences quoted in any EvidenceBox)

```latex
The probabilistic formulation also warrants further development. A Bernoulli--Gamma occurrence-and-amount likelihood has already been tested for one network and improved overall probabilistic scores without eliminating upper-tail undercoverage. Its benefit in other architectures and test periods remains untested. Future work should assess additional predictive information, broader objective and calibration settings, and the tradeoffs between common and rare events rather than presenting these completed distribution and objective comparisons as wholly untested proposals. Ensemble or Bayesian approaches could additionally examine uncertainty associated with model parameters and training variability.
```

## P5
### P5-a — source line 1253 (red group 1241–1263) — §5.3 Predictor Attribution and Incremental Contribution
- First sentence: "The three analyses answer different questions."
- Citations in paragraph: none
- EvidenceBox protection: none (0/5 sentences quoted in any EvidenceBox)

```latex
The three analyses answer different questions. Marginal correlation describes statistical association with precipitation; partial correlation describes association after controlling for current precipitation. SHAP describes how a fitted model attributes its predictions relative to a background distribution, including changes in reliance across precipitation regimes. Retrained feature ablation measures incremental predictive utility in the presence of the remaining inputs. Neither SHAP nor correlation alone establishes that a predictor improves performance, and none of these analyses establishes meteorological causality.
```

### P5-b — source line 1255 (red group 1241–1263) — §5.3 Predictor Attribution and Incremental Contribution
- First sentence: "The upper-tail mntpr attribution illustrates what SHAP adds beyond aggregate single-variable ablation."
- Citations in paragraph: none
- EvidenceBox protection: none (0/5 sentences quoted in any EvidenceBox)

```latex
The upper-tail mntpr attribution illustrates what SHAP adds beyond aggregate single-variable ablation. In BiLSTM-Attention, its mean absolute attribution increased by a factor of 2.71 and its mean signed attribution was positive relative to the background, but only 53.7\% of case--seed attributions were positive; individual removal had little detectable effect. The precipitation-group ablation resolves the apparent discrepancy: the three related variables jointly carry useful predictive information that can remain available when only one is removed. High attribution and a small individual-removal effect can therefore coexist. The group result supports predictive redundancy in these fitted models, rather than physical interchangeability of the variables.
```

### P5-c — source line 1257 (red group 1241–1263) — §5.3 Predictor Attribution and Incremental Contribution
- First sentence: "The correlation-based rankings also differed from model-based rankings."
- Citations in paragraph: none
- EvidenceBox protection: none (0/4 sentences quoted in any EvidenceBox)

```latex
The correlation-based rankings also differed from model-based rankings. Marginal-correlation rankings showed weak or negative agreement with SHAP and ablation, while partial-correlation rankings were descriptively closer. These comparisons span training-period associations and model evaluations on different subsets and are not formal same-sample tests of which method is correct. The $\tau=0.524$ random-SHAP/full-test-ablation comparison is descriptive; upper-tail agreement of only 0.048 in both architectures further shows that the methods are not interchangeable.
```

### P5-d — source line 1259 (red group 1241–1263) — §5.3 Predictor Attribution and Incremental Contribution
- First sentence: "Conclusions also depend on architecture and training variability."
- Citations in paragraph: none
- EvidenceBox protection: none (0/5 sentences quoted in any EvidenceBox)

```latex
Conclusions also depend on architecture and training variability. BiLSTM-Attention provided consistent single-variable effects for sp, tcc and v10, whereas BU-LSTM-Attention had less stable ablation rankings and disagreement between some sampling and seed-based intervals. Its individual precipitation-variable removals sometimes improved performance. Total cloud cover is therefore not identified as a universally most important predictor. Combining the methods distinguishes statistical association, regime-dependent model reliance and individual or jointly shared predictive utility without treating any one ranking as definitive.
```

### P5-e — source line 1261 (red group 1241–1263) — §5.3 Predictor Attribution and Incremental Contribution
- First sentence: "The model-matched contrasts in Figs.~\reffig:r1m4_shap_comparison and~\reffig:r1m4_ablation_comparison, together with Supplementary Tables~\refsupp-stab:r1m4_sh"
- Citations in paragraph: none
- EvidenceBox protection: none (0/2 sentences quoted in any EvidenceBox)

```latex
The model-matched contrasts in Figs.~\ref{fig:r1m4_shap_comparison} and~\ref{fig:r1m4_ablation_comparison}, together with Supplementary Tables~\ref{supp-stab:r1m4_shap_direction}--\ref{supp-stab:r1m4_correlation_rank_agreement}, provide the evidence for this complementary interpretation. Temporal attribution remains a separate finite-permutation approximation, without an established convergence claim.
```

### P5-f — source line 1324 — §5.4 Limitations and Future Work
- First sentence: "The interpretation is conditional on the fixed SHAP background and the tested model configurations."
- Citations in paragraph: none
- EvidenceBox protection: none (0/6 sentences quoted in any EvidenceBox)

```latex
The interpretation is conditional on the fixed SHAP background and the tested model configurations. The main grouped analysis used 100 training windows shared across models and seeds; sensitivity to alternative background selections was not evaluated and is not claimed. Coalition enumeration does not remove this uncertainty, and interventional masking can break dependencies among correlated predictors. Five seeds provide limited information about training variability, with only four degrees of freedom for the seed-based intervals. The less stable BU-LSTM-Attention ablations, the overlap between the random and upper-tail SHAP samples, and comparisons of rankings across different evaluation subsets limit broader conclusions. Attribution magnitudes and ranks should therefore be read as model- and background-dependent associations rather than causal effects.
```

## P6
### P6-a — source line 1195–1197 — §5.1 Overall Forecasting Performance and Model Robustness
- First sentence: "The stronger-reference comparisons narrow the interpretation of model gains."
- Citations in paragraph: none
- EvidenceBox protection: none (0/6 sentences quoted in any EvidenceBox)
- Full text: identical to P3-d above.

### P6-b — source line 1199–1201 — §5.1 Overall Forecasting Performance and Model Robustness
- First sentence: "The observational checks distinguish within-reanalysis predictability from agreement with local measurements (Section~\refsec:observational_checks)."
- Citations in paragraph: ['https://doi.org/10.1029/2026JH001291']
- EvidenceBox protection: R1 M6 (7/7 sentences quoted)

```latex
The observational checks distinguish within-reanalysis predictability from agreement with local measurements (Section~\ref{sec:observational_checks}). Moderate ERA5--station correspondence and limited gains over a constant training-mean reference constrain external interpretation. The constant is the ERA5 training-period mean, 0.1061~mm\,h$^{-1}$, not a station-derived mean. The small, non-significant XGBoost label-training difference does not support a conclusion that observations lack value. Changing labels while retaining regional ERA5 inputs and untuned settings would in any case be a restricted test, not an optimized station forecast. A related distinction is made by \citet{https://doi.org/10.1029/2026JH001291}, who treated ERA5-referenced precipitation evaluation as a model-consistency check and used satellite-derived IMERG as an independent observational benchmark. Their global forecasting design and observational product differ from ours; the citation supports separating reanalysis and observational verification rather than transferring their skill to this study.
```

### P6-c — source line 1293–1295 — §5.4 Limitations and Future Work
- First sentence: "The independent observational assessment is limited to one airport station and remains exploratory."
- Citations in paragraph: none
- EvidenceBox protection: R1 M6 (9/9 sentences quoted)

```latex
The independent observational assessment is limited to one airport station and remains exploratory. Point rainfall and regional-mean reanalysis have different spatial supports, and spatial averaging cannot be assumed to explain all distributional differences or model errors. No multi-station validation was implemented, and no independent station-based or radar-derived precipitation target was constructed at a spatial support matched to the 25-grid-point ERA5 regional mean. The station rainfall accumulation window remains uncertain under the adopted timestamp alignment. All 26,300 matched station observations carried rainfall indicator 111 (``investigation required''), with no indicator-0 (``satisfactory'') subset, so an indicator-0 sensitivity analysis could not be undertaken. This does not establish why code 111 occurs or imply that every amount is erroneous, but it limits the strength of observational validation. The XGBoost station-label experiment used regional ERA5 inputs and unchanged hyperparameters, without station-specific predictors or tuning, multi-station training, or deep-learning retraining on observations. Neither the exploratory observational comparison nor the non-significant label-training difference establishes transferability to other stations, regions or temporal scales. Our conclusions remain restricted to ERA5-derived regional-mean precipitation over Dublin.
```

### P6-d — source line 1320–1322 — §5.4 Limitations and Future Work
- First sentence: "The archived NWP reference also has a restricted scope."
- Citations in paragraph: none
- EvidenceBox protection: none (0/5 sentences quoted in any EvidenceBox)

```latex
The archived NWP reference also has a restricted scope. It uses only 1,970 common 06/18~UTC samples, a six-hour mean HRES rate rather than the final-hour learning target, and station observations with different spatial support. ERA5 and HRES share the IFS framework, so the ERA5-target comparison is not independent of modelling structure. Neither the more limited station RMSE differences nor the use of matched leads makes this a fully equivalent-window operational comparison. Seasonal results are descriptive because each season has only two to three test-period realizations, and season-specific training was examined only for XGBoost.
```

---

## Location validity after R4-M1, M2, M3 and minor 8
- The Discussion section heads are unchanged: Discussion 1180, §5.1 1182, §5.2 1211, §5.3 1250, §5.4 1272, Conclusion 1333.
- manuscript.tex is byte-identical to the audit base, so all audit line numbers are valid.
- R4-M1 to minor 8 changed only §1, §2, §3.2, §3.3.1, §4.1, §4.2.1, §4.2.3 and the Supplementary; none of those edits is inside the Discussion.
- Two edits are relevant context outside the Discussion:
  - §4.2.3, R4-M3 convective strata: outcome-conditioned, so relevant to P1.
  - §4.2.1, minor 8 OLS L3 paragraph: stronger references, relevant to P3.
- Correction to the audit: the P5 note "check that the SHAP implementation is kernel/interventional-style" is already answered. Line 1324 itself says "interventional masking can break dependencies among correlated predictors".

## Extra checks
- **P1 (over-claim):**
  - 1231 explicitly says the upper-tail result "should not be interpreted as evidence that tree-based models were generally superior".
  - 1215 still presents the upper-tail RMSE as a model ranking ("A different model ranking emerged", "supports an XGBoost advantage more clearly"). That ranking is on subsets selected by the observed outcome, which is the Lerch et al. issue. The result is not stated as universal, but as written it is a ranking claim.
  - Separate finding: 1231 cites grinsztajn2022tree for "particularly under limited or imbalanced sample sizes". The Grinsztajn abstract (arXiv:2207.08815) supports "medium-sized data (~10K samples)" but does not mention imbalance. The "imbalanced" part is unsupported at abstract level; full text not checked.
- **P2 (peak underestimation):**
  - Amplitude/tail compression is explicit: 1219 "predictions substantially compress the observed upper tail"; 1228 "Compressed forecast amplitudes led to few or no forecasts at high fixed thresholds"; 1313 "cannot identify a dominant cause of underestimation".
  - Event-peak timing or delay is explicitly not claimed (1219, 1313).
  - No literature link exists.
- **P3 (attention qualification):** adequate. 1189 reports −0.73%, both intervals excluding zero, Holm-adjusted p = 0.17 (seed-t) and 0.13 (block), "not established after multiplicity adjustment", and the +8,320 parameters. 1191 qualifies the cost comparison.
- **P4 (overall vs tail coverage):** distinguished.
  - 1234 gives full-test five-seed coverage of 0.956–0.958, separately from single-run legacy-wet, revised-wet and upper-tail coverage.
  - 1237 states that near-nominal overall coverage "can conceal substantial undercoverage".
  - 1239 and 1244 limit Bernoulli–Gamma to one backbone.
- **P5 (SHAP and causality):** covered. 1253: "none of these analyses establishes meteorological causality". 1324: "rather than causal effects". 1255 and 1259 limit interpretation further.
- **P6 (conflict with closed R3-13):** no conflict found.
  - 1196 (HRES ERA5 RMSE lower than all six; airport event AUC higher; window, support and shared-IFS caveats; "unfavourable to claims of NWP competitiveness") matches the closed R3-13 reply and its §4.2.2 excerpts.
  - 1321 matches as well (1,970 samples, six-hour mean rate vs final hour, limited station RMSE differences).
  - Constraint for any P6 addition: it must not say whether ERA5 verification favours or penalises HRES precipitation. 1196 says "could favour HRES … not separately quantified", and WeatherBench 2 documents the opposite concern for analysis-based variables. A neutral "net effect not quantified" is compatible with both.

## D/E per item

**P1**
- Literature:
  - Lerch et al. 2017 (A, arXiv full text, §2.3 p.9, §4 p.25): restricting evaluation to observed outcomes makes proper scores improper and can reward hedging; consider all cases or use proper weighted scores.
  - gneiting2011weighted (bib): twCRPS on all cases, already used in Methods l.537–539 and Results l.1091.
- Argument: the upper-tail RMSE and coverage are conditional diagnostics, not a ranking of models for heavy precipitation.
- Placement: append to 1219 or 1237 (both unprotected).
- Necessity: must modify. Optionally also narrow the 1231 Grinsztajn wording (unprotected).
- Risk: medium. It qualifies the "XGBoost better in the upper tail" message and bears on the reading of the R4-M3 strata.

**P2**
- Literature:
  - Dai et al. 2026 (A, local full text, Introduction p.2, Table 2): MSE-trained models tend to the conditional mean and underestimate extreme intensities.
  - Ayzel et al. 2020 (A, abstract and §4): smoothing and loss of high-intensity skill.
  - Ravuri et al. 2021 (A, PMC): blurry nowcasts, poor on medium-to-heavy rain. Not attributed to MSE.
- Argument: tail compression is a documented property of deterministic data-driven precipitation forecasts; context, not causal explanation.
- Placement: append to 1219 (unprotected). 1228 is protected (R2 M4, 7/7 sentences).
- Necessity: must modify. Risk: low with the scale/lead-time qualifier.

**P3**
- Literature:
  - grinsztajn2022tree (bib; already cited at 1231).
  - Shwartz-Ziv & Armon 2022 (B, abstract): XGBoost beats deep tabular models with less tuning.
  - otero2023intercomparison (bib; B abstract): a two-level U-Net matched deeper ones for European daily extremes at lower cost.
- Argument: comparable performance of simpler or tree models is reported elsewhere; the flattened 42-input setting is tabular.
- Placement: append to 1186 (unprotected). 1189 and 1191 are fully protected (R3 L822-824).
- Necessity: must modify. Risk: medium (two B sources; different domains).

**P4**
- Literature:
  - cannon2008bernoulli (bib; B abstract; already cited in Methods l.368).
  - Baño-Medina et al. 2020 (A, §3 and §4.2): Bernoulli–gamma NLL; deterministic predictions slightly underestimate P98, and sampling helps.
- Argument: precedent for the likelihood; a better-specified likelihood does not by itself remove tail underestimation.
- Placement: append to 1239 (unprotected). 1244 is protected (R2 M6).
- Necessity: recommended. Risk: low to medium (P98 of deterministic expected values ≠ interval coverage; write "consistent with").

**P5**
- Literature:
  - Mamalakis et al. 2022 (B): XAI intercomparison in geoscience; method-specific limitations; caution.
  - Aas et al. 2021 (B): independence-assuming Shapley approximations can mislead with dependent features; grouped Shapley values proposed.
  - Optional: McGovern et al. 2019 (B).
- Argument: method disagreement is documented; correlated predictors bias interventional SHAP.
- Placement: append to 1253 and 1324 (both unprotected).
- Necessity: recommended. Risk: low (stay at abstract-level claims).

**P6**
- Literature:
  - WeatherBench 2 (A, arXiv HTML §3.3.1, §3.1, §6.1): HRES is verified against its own analysis to avoid an ERA5 disadvantage, but precipitation for all models is verified against ERA5; ERA5 precipitation can differ substantially from gauges.
  - lavers2022evaluation (bib; B abstract): smallest errors in the winter extratropics, wet bias, highest totals not reproduced.
- Argument: the choice of verifying data affects NWP–ML comparison (net effect unquantified); ERA5–gauge differences are consistent in direction with the Dublin check.
- Placement:
  - WB2: append to 1321 (unprotected).
  - Lavers: append to 1294 or 1200. Both are fully protected (R1 M6), so append only without touching existing sentences; 1294 is the more natural place.
- Necessity: recommended. Risk: medium for WB2 (do not imply direction); low for Lavers (daily vs hourly qualifier).

## Approval table

| Item | Location (LaTeX source) | Adequately cited now? | Addition needed? | Risk |
|---|---|---|---|---|
| P1 | §5.2: 1214–1216, 1218–1220, 1231, 1237 | No; 1231 cites Grinsztajn for "imbalanced", unsupported at abstract level | Yes, must (append at 1219 or 1237); optionally narrow the 1231 wording | Medium: qualifies the upper-tail ranking and R4-M3 strata |
| P2 | §5.2: 1218–1220 (+1227–1229 protected, 1312–1314) | No | Yes, must (append at 1219) | Low |
| P3 | §5.1: 1185–1187 (+1189, 1191 protected; 1195–1197) | No | Yes, must (append at 1186) | Medium: B-level sources |
| P4 | §5.2: 1233–1235, 1237, 1239, 1243–1245 protected; §5.4 1316–1318 | No | Recommended (append at 1239) | Low–medium |
| P5 | §5.3: 1253–1261 (red group 1241–1263); §5.4: 1324 | No | Recommended (append at 1253 and 1324) | Low |
| P6 | §5.1: 1195–1197, 1199–1201 protected; §5.4: 1293–1295 protected, 1320–1322 | Partly (1200 cites the 2026 JGR-MLC paper) | Recommended (append at 1321; Lavers appended at 1294) | Medium (WB2 direction); low (Lavers) |

Status: **R4-M4: READ-ONLY AUDIT COMPLETE — AWAITING USER APPROVAL**
