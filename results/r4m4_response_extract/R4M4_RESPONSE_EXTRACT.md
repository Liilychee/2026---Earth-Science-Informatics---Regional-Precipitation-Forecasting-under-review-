# R4-M4 — read-only extraction for the formal reply (2026-11-16)

Read-only. No source file was modified. Source hashes: source_sha256.txt. Machine-readable locations: R4M4_LOCATIONS.json.

## A. Reviewer comment and current Response letter block

Response letter.tex lines 1579–1587 (`% Review ID: R4 M4`), verbatim:

```latex
% Review ID: R4 M4
\Needspace{5\baselineskip}
\subsection*{Major Comment~4}

\ReviewerComment{4. The discussion include valid issues and I like its structure, however, there is barely any reference to existing literature! This is a major drawback, bigger than point 1.}

\PendingResponse

\ChangeLocation
```

- The block is still a placeholder: `\PendingResponse` and `\ChangeLocation`, with no EvidenceBox.
- "Point 1" in the comment is R4 Major Comment 1 (Related Work), answered separately (R4 M1 block, l.1487).

## B. P1–P6 final locations (manuscript.tex, current build: 115 pp)

| Item | Section (`\ref` label for the letter) | Source line | PDF page / printed lines | Keys |
|---|---|---|---|---|
| P1 | §5.2 Performance under Upper-Tail Precipitation and Probabilistic Reliability (`manuscript-sec:upper_tail_discussion`) | 1216 | p.86 l.2010 – p.87 l.2015 | `lerch2017forecaster` |
| P2 | §5.2 Performance under Upper-Tail Precipitation and Probabilistic Reliability (`manuscript-sec:upper_tail_discussion`) | 1220 | p.87 l.2028 – p.87 l.2035 | `ayzel2020rainnet` |
| P3 | §5.1 Overall Forecasting Performance and Model Robustness (`manuscript-sec:overall_discussion`) | 1187 | p.82 l.1903 – p.83 l.1912 | `grinsztajn2022tree`, `otero2023intercomparison` |
| P4 | §5.2 Performance under Upper-Tail Precipitation and Probabilistic Reliability (`manuscript-sec:upper_tail_discussion`) | 1240 | p.90 l.2101 – p.90 l.2110 | `cannon2008bernoulli,bano2020configuration`, `bano2020configuration` |
| P5a | §5.3 Predictor Attribution and Incremental Contribution (`manuscript-sec:predictor_complementarity`) | 1254 | p.91 l.2134 – p.91 l.2137 | `mamalakis2022investigating` |
| P5b | §5.4 Limitations and Future Work (`manuscript-sec:limitations`) | 1325 | p.102 l.2413 – p.102 l.2418 | `aas2021explaining` |
| P6a | §5.4 Limitations and Future Work (`manuscript-sec:limitations`) | 1295 | p.97 l.2282 – p.97 l.2287 | `lavers2022evaluation` |
| P6b | §5.4 Limitations and Future Work (`manuscript-sec:limitations`) | 1322 | p.101 l.2394 – p.101 l.2401 | `rasp2024weatherbench` |

Printed line numbers come from the referee-mode line numbering and will shift if any earlier text changes. `\ref` labels are stable.

## C. Inserted text, verbatim (candidate `\RevisedExcerpt` content)

Each block below is exactly what manuscript.tex now contains inside `\revminor{...}`. It is a contiguous substring, so it can be quoted as an EvidenceBox excerpt unchanged.

### P1 — §5.2

```latex
These upper-tail RMSE comparisons are conditional on observed precipitation exceeding the specified thresholds. Evaluating forecasts only on cases selected by their observed outcomes can distort comparative rankings \citep{lerch2017forecaster}. Accordingly, the present upper-tail results are interpreted as conditional error diagnostics rather than evidence of unconditional forecasting superiority.
```

### P2 — §5.2

```latex
Similar difficulties in representing high precipitation intensities have been reported in data-driven rainfall forecasting. For example, radar-based deep-learning nowcasts have exhibited spatial smoothing and reduced representation of intense rainfall features \citep{ayzel2020rainnet}. Although the present study concerns regional-mean ERA5 precipitation rather than spatial radar nowcasts, these findings provide a relevant comparison for the observed upper-tail amplitude compression. The underlying causes in our models remain unresolved.
```

### P3 — §5.1

```latex
The comparable overall performance of the tree-based and recurrent models is consistent with broader evidence that tree-based methods remain competitive with deep neural networks on medium-sized tabular datasets \citep{grinsztajn2022tree}. Related precipitation-focused work has also shown that shallower U-Net configurations can achieve performance comparable to deeper variants with fewer trainable parameters \citep{otero2023intercomparison}. Although these studies differ in data representation, architecture and prediction setting, they reinforce the importance of evaluating model complexity against demonstrated predictive gains rather than assuming that more complex models will necessarily perform better.
```

### P4 — §5.2

```latex
Bernoulli--Gamma distributions have previously been used in neural-network-based precipitation downscaling to jointly represent precipitation occurrence and positive amounts \citep{cannon2008bernoulli,bano2020configuration}. In related precipitation downscaling experiments, deterministic predictions slightly underestimated the 98th precipitation percentile, while stochastic sampling improved this aspect at the expense of some temporal and spatial correlation \citep{bano2020configuration}. Although percentile bias and prediction-interval coverage are distinct diagnostics, these findings underscore the importance of evaluating high-intensity precipitation performance separately from aggregate probabilistic skill.
```

### P5a — §5.3

```latex
This complementary interpretation is consistent with previous geoscientific research highlighting the method-dependent strengths and limitations of XAI techniques and advocating the combined use of multiple explanation methods \citep{mamalakis2022investigating}.
```

### P5b — §5.4

```latex
Previous methodological research has shown that Shapley-value explanations can be misleading when dependencies among correlated features are not adequately accounted for \citep{aas2021explaining}. This reinforces the need to interpret the present attributions cautiously, without assuming that they uniquely identify the contribution of each meteorological predictor.
```

### P6a — §5.4

```latex
Independent evaluations have documented differences between ERA5 precipitation and rain-gauge measurements, including biases in daily precipitation and underrepresentation of the largest observed daily totals \citep{lavers2022evaluation}. Although these findings concern daily precipitation across a much broader geographical domain, they reinforce the need to distinguish ERA5-referenced forecast evaluation from validation against local observations.
```

### P6b — §5.4

```latex
WeatherBench 2 likewise distinguishes reanalysis-based evaluation from verification against operational analyses and acknowledges the limitations of ERA5 precipitation as a reference dataset \citep{rasp2024weatherbench}. Although that benchmark uses ERA5 to verify precipitation accumulations across models, the net effect of the verification reference on the present HRES comparison has not been quantified, and the mismatch in precipitation accumulation windows remains an additional limitation.
```

## D. Literature in the Discussion before and after revision

- Original manuscript (`original_manuscript.tex`), Discussion: 1 citation, 1 source (grinsztajn2022tree).
- Current manuscript, Discussion: 18 citation instances, 16 distinct sources.
- Added for R4-M4 (P1–P6): lerch2017forecaster, ayzel2020rainnet, otero2023intercomparison, cannon2008bernoulli, bano2020configuration, mamalakis2022investigating, aas2021explaining, lavers2022evaluation, rasp2024weatherbench (9 new sources), plus grinsztajn2022tree re-cited in §5.1.
- Added earlier for other reviewers' comments and also in the Discussion: catto2012relating, hawcroft2012much, lavers2013nexus, ecmwf_era5_documentation, goutham2023statistical, https://doi.org/10.1029/2026JH001291.

## E. Points to settle before writing the reply

1. Scope: P1–P6 are the only R4-M4 manuscript changes. Supplementary and BibTeX are unchanged by R4-M4, apart from your own BibTeX additions and fixes.
2. P1-c (left for separate approval): §5.2 source l.1232 still cites Grinsztajn for tree-based models matching deep networks "particularly under limited or imbalanced sample sizes". The abstract supports medium-sized data but does not mention imbalance. This sentence is not quoted in any EvidenceBox. Decide whether to fix it before or after the reply, or to leave it.
3. Abstract-level verification: Otero and Horton 2023 (P3, "fewer trainable parameters" is not verbatim in the abstract) and Grinsztajn 2022 were checked at abstract level only. The other sources were checked against full text or the publisher abstract (see the P1–P6 FINAL_REPORTs).
4. Response letter rendering: the letter uses natbib/plainnat, so any `\citep` inside the reply or the excerpts renders as "(Author et al., 2022)", with a comma. This was confirmed out of scope by the citation-style decision.
5. Planned additions to the letter: the reply text (`\AuthorResponse`), `\ManuscriptChange` and new EvidenceBoxes. The existing 170 excerpts must stay verbatim and in order; the new excerpts would make 170 + n.
6. Git: R4-M1, M2, M3, m8, citation-style unification and P1–P6 are all local only; archiving is deferred until after the reply.

## F. Draft reply (for review only — NOT written to the Response letter)

```latex
\AuthorResponse{We thank the reviewer for this important point and agree that the original Discussion was insufficiently connected to the literature: it cited a single source. We have revised Sections~5.1--5.4 so that each main finding is now discussed against relevant published work, while keeping the scope of each comparison explicit.

\textit{Overall model comparison (Section~\ref{manuscript-sec:overall_discussion}).} The comparable performance of XGBoost and the recurrent models is now related to evidence that tree-based methods remain competitive with deep networks on medium-sized tabular data, and to precipitation work showing that shallower U-Nets can match deeper variants. We note that these studies differ in data representation, architecture and prediction setting.

\textit{Upper-tail evaluation and amplitude compression (Section~\ref{manuscript-sec:upper_tail_discussion}).} We now explain, following the forecaster's-dilemma literature, that upper-tail RMSE conditioned on observed exceedance is a conditional diagnostic rather than evidence of unconditional superiority. We relate the observed amplitude compression to similar behaviour in radar-based deep-learning nowcasts, without attributing a common mechanism. We also place the Bernoulli--Gamma comparison in the context of earlier neural-network downscaling studies, distinguishing their percentile bias from our interval coverage.

\textit{Attribution (Sections~\ref{manuscript-sec:predictor_complementarity} and~\ref{manuscript-sec:limitations}).} The complementary use of correlation, SHAP and ablation is now supported by geoscientific XAI intercomparisons. The SHAP limitations are linked to work showing that Shapley explanations can mislead when feature dependence is not accounted for.

\textit{Verification reference (Section~\ref{manuscript-sec:limitations}).} The station and HRES limitations are now linked to published evaluations of ERA5 precipitation against rain gauges and to the verification design of WeatherBench~2. We state that the net effect of the verification reference on our HRES comparison was not quantified.

In total, nine additional sources are now cited in the Discussion, which cites sixteen distinct sources in the revised manuscript. These citations provide context and do not change any numerical result or conclusion.}
```

The EvidenceBoxes would quote the C-section texts verbatim (one box per P-item; P5 and P6 each have two locations).
