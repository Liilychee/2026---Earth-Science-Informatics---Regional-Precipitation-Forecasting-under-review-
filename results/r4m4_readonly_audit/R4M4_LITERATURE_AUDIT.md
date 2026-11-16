# R4-M4 — Discussion literature audit and revision plan (READ-ONLY)

Status: **R4-M4: READ-ONLY AUDIT COMPLETE — AWAITING USER APPROVAL**
Date: 2026-11-16. No changes to manuscript.tex, Supplementary.tex, Response letter.tex or any .bib file.

Reviewer 4, Major Comment 4: "The discussion include valid issues and I like its structure, however, there is barely any reference to existing literature! This is a major drawback, bigger than point 1."

---

## 1. Audit of the current Discussion (manuscript.tex lines 1180–1331)

The Discussion has 4 subsections and about 41 substantive paragraphs. It cites only 7 sources:
- grinsztajn2022tree (l.1231)
- the 2026 PredRNN/IMERG JGR-MLC paper (l.1200)
- hawcroft2012much, catto2012relating and lavers2013nexus (l.1265)
- ecmwf_era5_documentation (l.1298)
- goutham2023statistical (l.1306)

Four of these were added during this revision; the original Discussion cited essentially only Grinsztajn et al.

"Protected" means the paragraph contains text quoted in an EvidenceBox of a closed item. Additions there must be new whole sentences appended at the end, leaving the quoted sentences byte-identical.

| Line | Core argument | Current citations | Supported by own experiments? | Literature gap | Protected (closed item) | Recommendation |
|---|---|---|---|---|---|---|
| 1186 | BiLSTM-Attn and XGBoost comparable overall | none | yes (5 seeds, paired bootstrap) | no comparison with other ML-vs-DL precipitation/tabular studies | – | **Add (P3)** |
| 1189 | attention gain small, not robust after Holm | none | yes | no verified literature on attention gains for this setting | R3 L822-824 | No change |
| 1191 | complexity not matched by accuracy gains; XGBoost cheaper | none | yes | same as 1186 | R3 L822-824 | Add at end of 1186 instead |
| 1193 | probabilistic models lose point accuracy (MSE vs NLL objectives) | none | yes | could cite proper scoring (gneiting2007proper, already in bib) | – | Optional |
| 1196 | stronger references and HRES narrow claims | none | yes | ground-truth choice in NWP–ML comparisons | – | **Add (P6)**, or at 1321 |
| 1200 | reanalysis vs observational verification | 2026 JGR-MLC (PredRNN/IMERG) | yes | ERA5 precipitation vs gauges | R1 M6 | **Add (P6b)** |
| 1205 | rolling-origin ranking instability | none | yes | – | R2 M5 | No change |
| 1209 | q19 tuning not equal-budget | none | yes | – | – | No change |
| 1215 | ranking changes in the upper tail | none | yes (single saved runs) | evaluation conditioned on observed extremes | – | **Add (P1)** at 1219 |
| 1219 | aggregate metrics hide tail; amplitude compression; AUC vs CSI | none | yes | literature on tail compression / smoothing | – | **Add (P1 + P2)** |
| 1223 | weighting/Huber trade-offs | none | yes | optional imbalanced-regression literature | – | No change |
| 1228 | fixed-rule events; compression observed, not diagnosed | none | yes | – | R2 M4 | No change (P2 placed at 1219) |
| 1231 | XGBoost upper-tail advantage; tree vs DL on tabular data | grinsztajn2022tree | partly (mechanism untested) | adequate | – | Optional (Shwartz-Ziv) |
| 1234/1237 | coverage collapses in wet/upper tail | none | yes | outcome conditioning; calibration literature | – | **Add (P1)** |
| 1239 | Gaussian unsuited to non-negative skewed target; Bernoulli–Gamma | none | yes | precedent for Bernoulli–gamma networks | – | **Add (P4)** |
| 1244 | Bernoulli–Gamma improves overall, not tail | none | yes | – | R2 M6 | Add at 1239 instead |
| 1248 | spatial contrasts by quantile | none | yes | – | R2 M7 | No change |
| 1253–1261 | correlation, SHAP and ablation answer different questions | none | yes | XAI-disagreement literature; Shapley with dependent features | – | **Add (P5)** at 1253 |
| 1265 | physical plausibility of rankings | Hawcroft, Catto, Lavers 2013 | hypotheses | adequate | R3 L745-751, R4 M2 | No change |
| 1269 | screening vs predictive contribution; upstream C3 | none | yes | – | R2 M3 | No change |
| 1276–1284 | q19, likelihood and rolling-origin limits | none | yes | – | R2 M9, R2 M6, R2 M5 | No change |
| 1287/1289 | regional mean vs station extremes | none | yes | areal-reduction literature | R1 M3, R2 M7 | Optional (C-level only) |
| 1294 | observational check limits | none | yes | ERA5 gauge comparisons | R1 M6 | P6b could go here instead |
| 1298 | hindcast, not operational | ERA5 docs | yes | adequate | R2 M2 | No change |
| 1303/1306 | feature-selection / upstream limits | goutham2023 | yes | adequate | R2 M3, R3 3.2(d) | No change |
| 1308/1310 | 6-hourly sampling; hourly experiment | none | yes | – | R3 3.2(e), R3 L979-982 | No change |
| 1313 | scarcity of heavy samples; objectives | none | yes | could share P2 sources | – | Optional |
| 1317 | probabilistic future work | none | – | – | – | Optional |
| 1321 | HRES scope | none | yes | ground-truth choice | – | **Add (P6)** |
| 1324 | SHAP background and interventional masking | none | – | Shapley with dependent features | – | **Add (P5b)** |
| 1326 | single-region generalization | none | – | – | – | No change |
| 1331 | q03d seasonal limits | none | yes | – | R3 L469-471 | No change |

Claims that need care whatever is added:
- XGBoost upper-tail advantage and upper-tail coverage: both are outcome-conditioned (see P1).
- Attention gain: not robust after Holm adjustment.
- Physical explanations in 1265: already framed as hypotheses.
- HRES comparison: not equivalent windows.

---

## 2. Priority of modifications

| Priority | Location | Topic | Necessity |
|---|---|---|---|
| P1 | §5.2, end of l.1219 and/or l.1237 | Outcome-conditioned evaluation (upper tail, coverage) | **Must modify** (qualifies a headline claim) |
| P2 | §5.2, end of l.1219 | Tail compression in data-driven precipitation forecasts | **Must modify** |
| P3 | §5.1, end of l.1186 | Complexity vs accuracy; tree ensembles vs deep models | **Must modify** |
| P4 | §5.2, end of l.1239 | Bernoulli–gamma networks for precipitation | Recommended |
| P5 | §5.3, end of l.1253, and §5.4 l.1324 | XAI disagreement; Shapley with dependent features | Recommended |
| P6 | §5.4 end of l.1321, and l.1200 or l.1294 | ERA5 as ground truth; ERA5 vs gauges | Recommended |

This gives 6 locations and about 8–10 sentences in total, with no large rewrite.

---

## 3. Candidate literature and verification level

Levels:
- **A** — relevant passages read in the full text.
- **B** — only the abstract or official landing page checked.
- **C** — insufficient evidence.

All DOIs below were confirmed against Crossref metadata (title, authors, venue, year).

### A — full text checked

**A1. Lerch, S., Thorarinsdottir, T. L., Ravazzolo, F., Gneiting, T. (2017).** Forecaster's dilemma: Extreme events and forecast evaluation. *Statistical Science* 32(1), 106–127. https://doi.org/10.1214/16-STS588
- Full text read: arXiv:1512.09244 preprint; the journal version was checked by metadata only.
- Problem: forecast evaluation restricted to cases where extremes were observed.
- Data: theory, simulations, and US GDP/inflation forecasts.
- Evidence:
  - §2.3 (p. 9): an indicator weight on the outcome makes the score improper.
  - §4 (p. 25): "restricting the outcome space … renders any proper score improper, with an explicit hedging strategy being available. Arguably the only remedy is to consider all available cases when evaluating predictive performance."
  - Proper weighted scores such as twCRPS emphasise extremes legitimately.
- Relevance here: the upper-tail RMSE ranking (l.1215), the upper-tail coverage (l.1234) and the R4-M3 strata are all conditioned on observed y. The paper already uses twCRPS on all cases (l.537–539, 1091), which Lerch supports.
- Comparable: the evaluation principle. Not comparable: the application domain.

**A2. Ayzel, G., Scheffer, T., Heistermann, M. (2020).** RainNet v1.0: a convolutional neural network for radar-based precipitation nowcasting. *Geoscientific Model Development* 13, 2631–2644. https://doi.org/10.5194/gmd-13-2631-2020
- Data: DWD radar over Germany; 5-min training lead, recursive to 60 min; MAE, CSI (0.125–15 mm h⁻¹), FSS.
- Evidence:
  - Abstract: spatial smoothing increases with lead time; "limited ability … to predict heavy rainfall intensities".
  - §4: "loss of skill for high intensities is particularly remarkable"; it fails to predict exceedance of 15 mm h⁻¹ at longer leads.
- Relevance here: amplitude compression and few or no high-threshold detections (l.1219, 1228).
- Not comparable: gridded radar, minute-scale leads, recursive application.

**A3. Ravuri, S., et al. (2021).** Skilful precipitation nowcasting using deep generative models of radar. *Nature* 597, 672–677. https://doi.org/10.1038/s41586-021-03854-z
- Full text read via PMC8481123.
- Data: UK radar, 5–90 min, 2016–2018 training, 2019 test.
- Evidence:
  - Abstract: existing deep-learning nowcasts are "blurry … at longer lead times, yielding poor performance on rarer medium-to-heavy rain events".
  - Methods (UNet baseline): measures to mitigate "excessive blurring".
- Caution: the paper does **not** attribute the blurring specifically to MSE; do not cite it for that.
- Relevance here: P2. Not comparable: domain, scale, generative models.

**A4. Dai, L., Yuan, H., Liu, Y., Li, X., Gu, X., Li, J., Zhao, Y. (2026).** Improving extreme precipitation forecasts via cascade binary classification with diffusion post-processing. *JGR: Machine Learning and Computation* 3(4), e2026JH001347. https://doi.org/10.1029/2026JH001347
- Full text read from local PDF (~/Downloads).
- Data: ERA5 predictors with GPM IMERG targets, eastern China, 6-hourly samples, 2013–2023, 2023 as test year; CSI at 0.1–100 mm per 6 h.
- Evidence:
  - Introduction (p. 2): "When optimized with mean squared error (MSE) loss, these models tend to predict values close to the conditional mean, systematically underestimating extreme precipitation intensities."
  - Table 2 (p. 11): MSE-trained U-Net regression has CSI of 0.066 at 100 mm per 6 h.
- Relevance here: P2; the conditional-mean interpretation already used at l.1219.
- Not comparable: gridded 6-h totals, eastern China, image models.

**A5. Baño-Medina, J., Manzanas, R., Gutiérrez, J. M. (2020).** Configuration and intercomparison of deep learning neural models for statistical downscaling. *Geoscientific Model Development* 13, 2109–2124. https://doi.org/10.5194/gmd-13-2109-2020
- Data: ERA-Interim predictors with E-OBS daily precipitation over Europe (VALUE); train 1979–2002, test 2003–2008.
- Evidence:
  - §3: networks minimise the NLL of a Bernoulli–gamma distribution.
  - §4.2: deterministic predictions slightly underestimate P98, which "can be solved by stochastically sampling from the predicted gamma distribution", at some cost to temporal and spatial correlation.
  - The Figure 3 caption says "binomial–lognormal", which is inconsistent with the text; cite the text, not the figure.
- Relevance here: P4. Not comparable: daily downscaling, not lead-time forecasting.

**A6. Rasp, S., et al. (2024).** WeatherBench 2: A benchmark for the next generation of data-driven global weather models. *JAMES* 16, e2023MS004019. https://doi.org/10.1029/2023MS004019
- Full text read: arXiv:2308.15560 HTML.
- Evidence:
  - §3.3.1: IFS HRES is verified against its own analysis rather than ERA5, because ERA5 verification "would put the IFS at an unfair disadvantage compared to data-driven models trained on and evaluated against ERA5".
  - §3.3.1 and §5.1: precipitation for all models, including IFS, is verified against ERA5 because no analysis precipitation exists.
  - §3.1 and §6.1: ERA5 precipitation "sometimes shows large differences to rain gauge measurements" and should be treated as a placeholder.
- Relevance here: P6. The current text (l.1196) says shared IFS structure "could favour HRES" when ERA5 is the target. WB2 documents the opposite concern for analysis-based variables, so the honest wording is that the direction of the effect for precipitation is unquantified.
- Not comparable: global medium range, 24-h precipitation.

**A7. Makridakis, S., Spiliotis, E., Assimakopoulos, V. (2018).** Statistical and machine learning forecasting methods: Concerns and ways forward. *PLOS ONE* 13, e0194889. https://doi.org/10.1371/journal.pone.0194889
- Full text: publisher HTML; sections located but read only in summary.
- Evidence:
  - Abstract: ML methods "are dominated across both accuracy measures … and for all forecasting horizons", with greater computational requirements.
  - Sections 3.4, 3.5 and 4.2.
- Relevance here: P3 (stronger statistical references).
- Weak transferability: M3 monthly business series. **Optional; I recommend not using it** unless you want a general forecasting reference.

### B — abstract only

**B1. Shwartz-Ziv, R., Armon, A. (2022).** Tabular data: Deep learning is not all you need. *Information Fusion* 81, 84–90. https://doi.org/10.1016/j.inffus.2021.11.011
- Abstract: "XGBoost outperforms these deep models across the datasets … XGBoost requires much less tuning."
- Relevance: P3, a complement to grinsztajn2022tree. No precipitation data.

**B2. Aas, K., Jullum, M., Løland, A. (2021).** Explaining individual predictions when features are dependent: More accurate approximations to Shapley values. *Artificial Intelligence* 298, 103502. https://doi.org/10.1016/j.artint.2021.103502
- Abstract (arXiv:1903.10464): Kernel SHAP "assumes that the features are independent, which may give very wrong explanations", even for linear models. The paper proposes dependence-aware estimates and **group aggregation** of Shapley values.
- Relevance: P5b (l.1324, interventional masking; the grouped analysis).

**B3. Mamalakis, A., Barnes, E. A., Ebert-Uphoff, I. (2022).** Investigating the fidelity of explainable artificial intelligence methods for applications of convolutional neural networks in geoscience. *Artificial Intelligence for the Earth Systems* 1(4). https://doi.org/10.1175/AIES-D-22-0012.1
- Abstract: an intercomparison of popular XAI methods on a benchmark with known ground truth and on a climate CNN. It highlights limitations and calls for "a cautious implementation of XAI in geoscience".
- Caution: the abstract does not explicitly say "use several methods".
- Relevance: P5 (methods not interchangeable). CNN, not LSTM/XGBoost.

**B4. McGovern, A., et al. (2019).** Making the black box more transparent: Understanding the physical implications of machine learning. *BAMS* 100, 2175–2199. https://doi.org/10.1175/BAMS-D-18-0195.1
- Abstract: synthesises interpretation methods (permutation importance, forward/backward selection, saliency, etc.) for meteorological ML.
- Relevance: P5, general context only. **Optional.**

**B5. Otero, N., Horton, P. (2023).** Intercomparison of deep learning architectures for the prediction of precipitation fields with a focus on extremes. *Water Resources Research* 59(11), e2023WR035088 (authors and volume confirmed via Crossref). https://doi.org/10.1029/2023WR035088
- **Already in the bib and cited in §2.2.**
- Abstract: over Europe at daily scale, heavy (>P95) and extreme (>P99) events; "a simplified version of the original U-Net with two encoder-decoder levels generally achieved similar skill scores than deeper versions for predicting precipitation extremes, while significantly reducing the overall complexity and computing resources."
- Relevance: P3. The publisher full text returned 403.

**B6. Lavers, D. A., Simmons, A., Vamborg, F., Rodwell, M. J. (2022).** An evaluation of ERA5 precipitation for climate monitoring. *QJRMS* 148, 3152–3165. https://doi.org/10.1002/qj.4351
- **Already in the bib and cited in §2.1**, with a daily-scale qualification (R1 M6).
- Abstract: 24-h totals at 5,637 stations, 2001–2020. Smallest errors are in the winter extratropics, and errors grow in summer. There is "an ERA5 wet bias". ERA5 "cannot model the highest observed precipitation totals".
- Relevance: P6b. It is consistent in direction with the Dublin check (regional ERA5 wet frequency 20.4% vs station 12.8%; maxima 4.13 vs 16.4 mm h⁻¹), but daily vs hourly and point vs region.

**B7. Cannon, A. J. (2008).** Probabilistic multisite precipitation downscaling by an expanded Bernoulli–gamma density network. *J. Hydrometeorology*. https://doi.org/10.1175/2008JHM960.1
- **Already in the bib and cited in Methods (l.368).**
- Abstract: an ANN outputs Bernoulli–gamma parameters for daily multisite precipitation in coastal British Columbia.
- Relevance: P4.

**B8. Vandal, T., et al. (2018).** Quantifying uncertainty in discrete-continuous and skewed data with Bayesian deep learning. *KDD 2018*, 2377–2386. https://doi.org/10.1145/3219819.3219996
- Abstract: Gaussian/Euclidean losses are ill-suited to skewed precipitation; a discrete-continuous model is applied to DeepSD precipitation downscaling.
- Relevance: P4. **Optional** (conference paper, lognormal rather than gamma).

### C — insufficient evidence; do not cite yet
- **Chen & Knutson (2008)**, J. Climate, https://doi.org/10.1175/2007JCLI1494.1: areal vs point extreme rainfall indices. No abstract obtained. Possibly relevant to l.1287/1289, which are protected (R1 M3, R2 M7).
- **Gneiting, Balabdaoui & Raftery (2007)**, JRSSB, https://doi.org/10.1111/j.1467-9868.2007.00587.x: calibration and sharpness. No abstract checked; not needed beyond gneiting2007proper.
- No verified source was found for attention-layer gains in comparable precipitation time-series models. I recommend **no** literature claim at l.1189.

### Existing bib entries reusable without new BibTeX
- gneiting2011weighted (P1)
- grinsztajn2022tree (P3)
- otero2023intercomparison (P3)
- cannon2008bernoulli (P4)
- lundberg2017unified (P5)
- lavers2022evaluation (P6b)

Uncited bib entries that I do **not** recommend for the Discussion: rampal2022high, gascon2024post and haiden2021evaluation. Their content was not checked this round; haiden2021 is a technical memorandum.

---

## 4. Proposed modifications (not executed)

### P1 — §5.2, append to l.1219 ("This change in ranking …") or to l.1237
- **Original point:** the ranking changes in the upper tail, and coverage collapses there.
- **Problem:** subsets are defined by the observed outcome, and the text does not say that such subsets cannot rank forecasts properly.
- **Literature:** A1 Lerch 2017, plus gneiting2011weighted.
- **Draft:**
  > Subsets defined by the observed outcome, such as the upper tail, are informative diagnostics but not a proper basis for ranking forecasts: restricting evaluation to cases in which high values were observed renders proper scores improper and can reward forecasts that overpredict \citep{lerch2017forecaster}. Threshold-weighted scores computed on all cases avoid this problem \citep{gneiting2011weighted,lerch2017forecaster}, which is why the likelihood comparison also reports threshold-weighted CRPS on the complete test set. The upper-tail RMSE and coverage results are therefore read as conditional diagnostics of the tail behaviour of each model, not as a ranking of models for heavy precipitation.
- **Necessity:** must modify.
- **Risk:** this weakens the "XGBoost better in the upper tail" headline, and it partly bears on R4-M3. You must decide whether to accept it. Lerch's hedging argument applies to probabilistic scores; for RMSE on y ≥ Q95 the same logic (rewarding larger predicted amplitudes) is an inference, so keep "can reward".

### P2 — §5.2, append to l.1219 (after P1, or on its own)
- **Original point:** predictions compress the observed tail, consistent with a limited-skill conditional-mean forecast.
- **Problem:** no link to the documented tail compression of deterministic data-driven precipitation forecasts.
- **Literature:** A4 Dai 2026, A2 Ayzel 2020, A3 Ravuri 2021.
- **Draft:**
  > Underestimation of high intensities is widely reported for deterministic data-driven precipitation forecasts. Models optimized with mean squared error tend towards the conditional mean and systematically underestimate extreme intensities \citep{dai2026improving}, and radar-based nowcasting networks have produced increasingly smoothed fields with reduced skill for heavy rainfall \citep{ayzel2020rainnet,ravuri2021skilful}. Those studies use gridded radar or ERA5--IMERG fields at different scales and lead times, so they provide context for, rather than an explanation of, the compression observed here.
- **Necessity:** must modify.
- **Risk:** low if the last sentence is kept. Do not attribute Ravuri's blurring to MSE.

### P3 — §5.1, append to l.1186 (unprotected), not to l.1191 (protected)
- **Original point:** compact recurrent and tree models perform comparably, and complexity brings no clear gain.
- **Problem:** no comparison with other studies.
- **Literature:** grinsztajn2022tree (bib), B1 Shwartz-Ziv 2022, B5 otero2023intercomparison (bib).
- **Draft:**
  > Comparable performance from simpler or tree-based models has also been reported elsewhere. Tree ensembles such as XGBoost frequently match or outperform deep networks on tabular inputs while requiring less tuning \citep{grinsztajn2022tree,shwartzziv2022tabular}, and for European daily precipitation extremes a simplified two-level U-Net achieved skill similar to deeper versions at lower computational cost \citep{otero2023intercomparison}. The flattened 42-input representation used by XGBoost here is tabular in this sense, but those comparisons concern different data, targets and architectures.
- **Necessity:** must modify.
- **Risk:** moderate. Otero is verified at abstract level only. grinsztajn2022tree is already cited at l.1231, so citing it again is fine.

### P4 — §5.2, append to l.1239 (unprotected)
- **Original point:** the Gaussian is structurally unsuited to the target, and Bernoulli–Gamma removes negative bounds without fixing tail undercoverage.
- **Literature:** cannon2008bernoulli (bib), A5 Baño-Medina 2020; optionally B8 Vandal 2018.
- **Draft:**
  > Occurrence-and-amount likelihoods of this type are established in neural-network precipitation downscaling \citep{cannon2008bernoulli,banomedina2020configuration}. In European daily downscaling, deterministic Bernoulli--gamma predictions still slightly underestimated the 98th percentile, which sampling from the predicted distribution could address at some cost to temporal and spatial correlation \citep{banomedina2020configuration}. This is consistent with a better-specified likelihood not by itself resolving tail underestimation, although that study concerns daily downscaling rather than six-hour-ahead forecasting.
- **Necessity:** recommended.
- **Risk:** low to moderate. Baño-Medina's "slight underestimation" concerns deterministic expected values, not interval coverage; the draft says "consistent with", not "explains".

### P5 — §5.3, append to l.1253 (unprotected) and to §5.4 l.1324 (unprotected)
- **Original point:** correlation, SHAP and ablation answer different questions; SHAP depends on the background and masking.
- **Literature:** B3 Mamalakis 2022, B2 Aas 2021, lundberg2017unified (bib); optionally B4 McGovern 2019.
- **Draft for l.1253:**
  > Similar caution has been urged for geoscientific applications, where intercomparisons of explanation methods applied to the same network revealed method-specific limitations \citep{mamalakis2022investigating}.
- **Draft for l.1324:**
  > Shapley-value approximations that treat predictors as independent can give misleading attributions when predictors are dependent; dependence-aware estimates and aggregation over groups of dependent variables have been proposed \citep{aas2021explaining}. The precipitation-group ablation used here addresses predictive redundancy, not this attribution bias.
- **Necessity:** recommended.
- **Risk:** low. Both sources are at abstract level; the wording stays at abstract claims. Before writing "interventional", check that the SHAP implementation used is kernel/interventional-style.

### P6 — §5.4, append to l.1321 (unprotected); P6b to l.1200 or l.1294 (both protected → append only)
- **Original point:** HRES uses mismatched windows and a shared IFS framework; ERA5 vs station is a limited check.
- **Literature:** A6 WeatherBench 2, B6 lavers2022evaluation (bib).
- **Draft for l.1321:**
  > The choice of verifying data is known to affect comparisons between NWP and data-driven models: WeatherBench 2 verifies IFS HRES against its own analysis rather than ERA5 to avoid penalizing it, but verifies precipitation for all models against ERA5, noting that ERA5 precipitation can differ substantially from gauge measurements \citep{rasp2024weatherbench}. The net effect of verifying HRES precipitation against ERA5 in the present comparison was not quantified.
- **Draft for l.1294 (P6b):**
  > Global evaluations of ERA5 daily precipitation against 5,637 stations found the smallest errors in the winter extratropics, a general wet bias, and an inability to reproduce the highest observed totals \citep{lavers2022evaluation}; the higher wet-hour frequency and lower maxima of the ERA5 regional mean relative to Dublin Airport are consistent in direction, although that evaluation used 24-h station totals rather than hourly regional means.
- **Necessity:** recommended.
- **Risk:**
  - P6 wording must stay compatible with the existing l.1196 sentence ("could favour HRES"). You may want to soften l.1196, but it belongs to a closed R3 HRES item, so I do not recommend editing it.
  - P6b: l.1294 belongs to closed R1 M6, so append only.

---

## 5. Parts that should not be changed
- **l.1189** (attention gain): no verified comparable literature; the claim is already appropriately weak.
- **l.1205, 1209, 1276–1284, 1310, 1331**: these describe the study's own experimental-design limits, so literature adds little. Most are protected by closed items.
- **l.1265** (physical plausibility): already cited (Hawcroft, Catto, Lavers 2013) and closed (R3 L745-751, R4 M2).
- **l.1298** (operational vs hindcast) and **l.1306** (upstream domain): already cited and closed.
- **l.1248, 1287, 1289** (spatial averaging): protected (R2 M7, R1 M3). The only candidate (Chen & Knutson 2008) is at C level.
- **l.1223, 1313** (objective sensitivity): adequately qualified; adding imbalanced-regression literature would broaden scope without a verified link.

---

## 6. Ready metadata for user-managed BibTeX (not written to any .bib file)

```bibtex
@article{lerch2017forecaster,
  title={Forecaster's Dilemma: Extreme Events and Forecast Evaluation},
  author={Lerch, Sebastian and Thorarinsdottir, Thordis L. and Ravazzolo, Francesco and Gneiting, Tilmann},
  journal={Statistical Science}, volume={32}, number={1}, pages={106--127}, year={2017},
  doi={10.1214/16-STS588}}
@article{ayzel2020rainnet,
  title={{RainNet} v1.0: a convolutional neural network for radar-based precipitation nowcasting},
  author={Ayzel, Georgy and Scheffer, Tobias and Heistermann, Maik},
  journal={Geoscientific Model Development}, volume={13}, pages={2631--2644}, year={2020},
  doi={10.5194/gmd-13-2631-2020}}
@article{ravuri2021skilful,
  title={Skilful precipitation nowcasting using deep generative models of radar},
  author={Ravuri, Suman and Lenc, Karel and Willson, Matthew and Kangin, Dmitry and Lam, Remi and Mirowski, Piotr and others},
  journal={Nature}, volume={597}, pages={672--677}, year={2021},
  doi={10.1038/s41586-021-03854-z}}
@article{dai2026improving,
  title={Improving Extreme Precipitation Forecasts via Cascade Binary Classification With Diffusion Post-Processing},
  author={Dai, Leyan and Yuan, Huiling and Liu, Yiheng and Li, Xinyue and Gu, Xuanhao and Li, Jiajun and Zhao, Yang},
  journal={Journal of Geophysical Research: Machine Learning and Computation}, volume={3}, number={4}, pages={e2026JH001347}, year={2026},
  doi={10.1029/2026JH001347}}
@article{banomedina2020configuration,
  title={Configuration and intercomparison of deep learning neural models for statistical downscaling},
  author={Ba{\~n}o-Medina, Jorge and Manzanas, Rodrigo and Guti{\'e}rrez, Jos{\'e} Manuel},
  journal={Geoscientific Model Development}, volume={13}, pages={2109--2124}, year={2020},
  doi={10.5194/gmd-13-2109-2020}}
@article{rasp2024weatherbench,
  title={{WeatherBench} 2: A Benchmark for the Next Generation of Data-Driven Global Weather Models},
  author={Rasp, Stephan and Hoyer, Stephan and Merose, Alexander and Langmore, Ian and Battaglia, Peter and Russell, Tyler and others},
  journal={Journal of Advances in Modeling Earth Systems}, volume={16}, pages={e2023MS004019}, year={2024},
  doi={10.1029/2023MS004019}}
@article{shwartzziv2022tabular,
  title={Tabular data: Deep learning is not all you need},
  author={Shwartz-Ziv, Ravid and Armon, Amitai},
  journal={Information Fusion}, volume={81}, pages={84--90}, year={2022},
  doi={10.1016/j.inffus.2021.11.011}}
@article{aas2021explaining,
  title={Explaining individual predictions when features are dependent: More accurate approximations to {Shapley} values},
  author={Aas, Kjersti and Jullum, Martin and L{\o}land, Anders},
  journal={Artificial Intelligence}, volume={298}, pages={103502}, year={2021},
  doi={10.1016/j.artint.2021.103502}}
@article{mamalakis2022investigating,
  title={Investigating the Fidelity of Explainable Artificial Intelligence Methods for Applications of Convolutional Neural Networks in Geoscience},
  author={Mamalakis, Antonios and Barnes, Elizabeth A. and Ebert-Uphoff, Imme},
  journal={Artificial Intelligence for the Earth Systems}, volume={1}, number={4}, year={2022},
  doi={10.1175/AIES-D-22-0012.1}}
```

Volume, issue and pages come from Crossref. Mamalakis has no page or article number in Crossref; check the publisher page. For author lists marked "and others", complete them from the publisher page if your style requires full lists.

---

## 7. Decisions for the user
1. Accept P1? It reframes upper-tail RMSE and coverage as conditional diagnostics, partly qualifying a headline result and touching the R4-M3 strata interpretation.
2. Which of P1–P6 to adopt, and whether P6b goes to l.1200 or l.1294 (both closed; append only).
3. Which citations to add to the BibTeX yourself:
   - core set: A1–A6;
   - optional: B1–B4, B8, A7.
4. Whether abstract-level (B) sources are acceptable for the specific wording proposed, or whether you will obtain full texts for Otero 2023, Aas 2021 and Mamalakis 2022 first.
5. Whether to cite a 2026 JGR-MLC article (Dai et al.) alongside the 2026 JGR-MLC paper already cited at l.1200.
6. Whether the R4-M4 reply should list the added references per subsection; recommended, since the reviewer weighted this comment heavily.
7. Whether to soften the l.1196 HRES sentence in view of WeatherBench 2. It belongs to a closed HRES item, so I recommend leaving it and adding P6 instead.

---

## Sources consulted (read-only)
- Crossref API for every DOI above.
- arXiv:1512.09244 (full text PDF): Lerch et al.
- gmd.copernicus.org/articles/13/2631/2020 (full text): Ayzel et al.
- gmd.copernicus.org/articles/13/2109/2020 (full text): Baño-Medina et al.
- pmc.ncbi.nlm.nih.gov/articles/PMC8481123 (full text): Ravuri et al.
- arxiv.org/html/2308.15560 (full text): WeatherBench 2
- journals.plos.org/plosone/article?id=10.1371/journal.pone.0194889: Makridakis et al.
- Local PDF ~/Downloads/…2026 - Dai - Improving Extreme Precipitation Forecasts.pdf (full text)
- arXiv abstract pages 1903.10464, 2202.03407 and 2106.03253; Semantic Scholar abstracts for McGovern 2019, Vandal 2018, Otero 2023, Lavers 2022 and Cannon 2008.
- Wiley and AMS publisher pages returned HTTP 403 (Otero, Lavers, Mamalakis); those sources stay at abstract level.
