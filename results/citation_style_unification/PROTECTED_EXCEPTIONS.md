# Protected exceptions — narrative citations NOT converted

Each sentence below is quoted verbatim in at least one EvidenceBox of a reply (excerpt index = 0-based order in Response letter.tex). Converting it would break that reply's evidence chain, so it was left unchanged. Approving a row means editing BOTH manuscript.tex and the matching `\RevisedExcerpt` in Response letter.tex together.

## E1. `ridal2024cerra` — manuscript.tex:80

- Affected reply / excerpt: R3 Section 2; excerpt 121
- Current: Although \citet{ridal2024cerra} reported improvements over ERA5 for several near-surface variables, the present study uses ERA5 for both predictors and target precipitation and does not assess whether CERRA would improve regional precipitation forecasting.}
- Proposed: Although improvements over ERA5 have been reported for several near-surface variables \citep{ridal2024cerra}, the present study uses ERA5 for both predictors and target precipitation and does not assess whether CERRA would improve regional precipitation forecasting.

## E2. `rahman2022rainfall` — manuscript.tex:85

- Affected reply / excerpt: R1 m4; R3 L169-177; excerpt 45, 122
- Current: Among conventional machine-learning approaches, \citet{rahman2022rainfall} developed a fusion-based system for smart-city rainfall prediction that combines multiple classifiers with fuzzy logic, reporting improvements in prediction accuracy in their study.
- Proposed: Among conventional machine-learning approaches, a fusion-based system for smart-city rainfall prediction has been developed that combines multiple classifiers with fuzzy logic, with improvements in prediction accuracy reported in that study \citep{rahman2022rainfall}.

## E3. `adewoyin2021tru` — manuscript.tex:85

- Affected reply / excerpt: R1 m4; excerpt 46
- Current: \citet{adewoyin2021tru} proposed TRU-NET, which incorporates attention mechanisms and ERA5 inputs to produce high-resolution rainfall predictions over the UK.
- Proposed: TRU-NET, which incorporates attention mechanisms and ERA5 inputs, was proposed to produce high-resolution rainfall predictions over the UK \citep{adewoyin2021tru}.
- Note: The next sentence 'Their model outperformed ...' (same excerpt) would need 'This model outperformed ...'.

## E4. `latif2023assessing` — manuscript.tex:85

- Affected reply / excerpt: R3 L169-177; excerpt 123
- Current: More recently, \citet{latif2023assessing} compared statistical, machine-learning and deep-learning approaches to rainfall prediction and concluded that machine learning performed well across climates and timescales, with LSTM models among the most effective.
- Proposed: More recently, a comparison of statistical, machine-learning and deep-learning approaches to rainfall prediction concluded that machine learning performed well across climates and timescales, with LSTM models among the most effective \citep{latif2023assessing}.

## E5. `otero2023intercomparison` — manuscript.tex:87

- Affected reply / excerpt: R4 M1 (local, not archived); excerpt 155
- Current: Where heavy precipitation was examined separately, aggregate results did not describe tail behaviour: TRU-NET underpredicted the largest daily amounts more than IFS \citep{adewoyin2021tru}, and \citet{otero2023intercomparison} compared architectures specifically with regard to extremes.
- Proposed: ... TRU-NET underpredicted the largest daily amounts more than IFS \citep{adewoyin2021tru}, and a separate intercomparison evaluated architectures specifically with regard to extremes \citep{otero2023intercomparison}.
- Note: Two citations stay attached to their own clauses (type D).

## E6. `otero2023intercomparison` — manuscript.tex:145

- Affected reply / excerpt: R1 M6; R4 M1; excerpt 26, 155
- Current: \citet{otero2023intercomparison} likewise used ERA5 predictors and precipitation fields for an architecture intercomparison, but their European daily contemporaneous modelling task differs from our six-hour-ahead hourly target.
- Proposed: A previous architecture intercomparison likewise used ERA5 predictors and precipitation fields \citep{otero2023intercomparison}, but its European daily contemporaneous modelling task differs from our six-hour-ahead hourly target.

## E7. `met_eireann_dublin_hourly` — manuscript.tex:572

- Affected reply / excerpt: R1 M6; excerpt 27
- Current: Hourly precipitation observations at Dublin Airport were obtained from \citet{met_eireann_dublin_hourly}.
- Proposed: Hourly precipitation observations at Dublin Airport were obtained from the Irish national meteorological service \citep{met_eireann_dublin_hourly}.
- Note: Data-provider attribution (type F). Keeping 'from Met Éireann \citep{...}' would print 'Met Éireann (Met Éireann 2026)'.

## E8. `https://doi.org/10.1029/2026JH001291` — manuscript.tex:1200

- Affected reply / excerpt: R1 M6; excerpt 32
- Current: A related distinction is made by \citet{https://doi.org/10.1029/2026JH001291}, who treated ERA5-referenced precipitation evaluation as a model-consistency check and used satellite-derived IMERG as an independent observational benchmark.
- Proposed: A related distinction has been made in a recent study that treated ERA5-referenced precipitation evaluation as a model-consistency check and used satellite-derived IMERG as an independent observational benchmark \citep{https://doi.org/10.1029/2026JH001291}.
- Note: The next sentence 'Their global forecasting design ...' (same excerpt) would need 'Its global forecasting design ...'.

## E9. `goutham2023statistical` — manuscript.tex:1306

- Affected reply / excerpt: R3 Section 3.2(d); excerpt 130
- Current: In subseasonal downscaling of weekly mean fields, \citet{goutham2023statistical} found that restricting the predictor domain to the predictand domain considerably degraded prediction quality, whereas shifting a predictand-sized domain westward did not improve on a centred one; this provides context rather than validation of six-hour precipitation prediction or of the present boxes.
- Proposed: In subseasonal downscaling of weekly mean fields, restricting the predictor domain to the predictand domain considerably degraded prediction quality, whereas shifting a predictand-sized domain westward did not improve on a centred one \citep{goutham2023statistical}; this provides context ...
- Note: Rest of sentence unchanged.

---
**User decision (2026-11-16):** E1–E9 are retained unchanged as accepted style exceptions (user informed). They are not compile errors or scientific problems. manuscript.tex and Response letter.tex are not modified for them. The proposals above are kept for reference only.
