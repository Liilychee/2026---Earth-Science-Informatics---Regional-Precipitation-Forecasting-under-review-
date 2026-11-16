# Applies the reviewed narrative->parenthetical conversions to manuscript.tex.
# Each old sentence must occur exactly once; red marking: W=wrap in \revminor (black paragraph), N=already inside red.
import json, sys
R = sys.argv[1]
C = [
 ("10512739", "W",
  r"Recent advances in meteorological modeling have been supported by the increasing availability of high-resolution reanalysis datasets and the development of machine learning techniques, both of which have become important for precipitation forecasting, as demonstrated by \citet{10512739}.",
  r"Recent advances in meteorological modeling have been supported by the increasing availability of high-resolution reanalysis datasets and the development of machine learning techniques, both of which have become important for precipitation forecasting, as demonstrated in a recent study \citep{10512739}."),
 ("hersbach2020era5", "W",
  r"\citet{hersbach2020era5} introduced ERA5 with hourly coverage and a spatial resolution of approximately 31~km, showing marked improvements over ERA-Interim in reproducing variability and extremes across multiple atmospheric variables.",
  r"ERA5 was introduced with hourly coverage and a spatial resolution of approximately 31~km, and its introductory evaluation showed marked improvements over ERA-Interim in reproducing variability and extremes across multiple atmospheric variables \citep{hersbach2020era5}."),
 ("mcnicholl2021evaluating", "W",
  r"\citet{mcnicholl2021evaluating} found strong agreement between ERA5 near-surface air temperature and ground-based observations but also reported discrepancies under complex meteorological conditions.",
  r"One evaluation found strong agreement between ERA5 near-surface air temperature and ground-based observations but also reported discrepancies under complex meteorological conditions \citep{mcnicholl2021evaluating}."),
 ("doddy2021reanalysis", "W",
  r"\citet{doddy2021reanalysis} compared several reanalysis products for renewable energy applications in Ireland and showed that ERA5 generally outperforms MERRA-2 and JRA-55, while still exhibiting regional biases that require consideration.",
  r"A comparison of several reanalysis products for renewable energy applications in Ireland showed that ERA5 generally outperforms MERRA-2 and JRA-55, while still exhibiting regional biases that require consideration \citep{doddy2021reanalysis}."),
 ("lavers2022evaluation", "W",
  r"For precipitation, \citet{lavers2022evaluation} evaluated 24-hour totals against 5,637 stations over 2001--2020, finding a general wet bias, lower annual maximum one-day amounts, and smaller random errors in winter than summer in the extratropics.",
  r"For precipitation, an evaluation of 24-hour totals against 5,637 stations over 2001--2020 found a general wet bias, lower annual maximum one-day amounts, and smaller random errors in winter than summer in the extratropics \citep{lavers2022evaluation}."),
 ("palharini2021assessment", "W",
  r"\citet{palharini2021assessment} evaluated eleven satellite-based precipitation products across different regions of Brazil and found that no single product consistently captured extreme rainfall, with performance varying by region and event intensity.",
  r"An evaluation of eleven satellite-based precipitation products across different regions of Brazil found that no single product consistently captured extreme rainfall, with performance varying by region and event intensity \citep{palharini2021assessment}."),
 ("kumar2025long", "W",
  r"Similarly, \citet{kumar2025long} evaluated CHIRPS and GSMaP\_ISRO rainfall estimates against gauge observations over India during 2000--2022 and found that GSMaP\_ISRO agreed more closely with station measurements than CHIRPS, while both products diverged notably over complex terrain such as the Western Ghats.",
  r"Similarly, when CHIRPS and GSMaP\_ISRO rainfall estimates were evaluated against gauge observations over India during 2000--2022, GSMaP\_ISRO agreed more closely with station measurements than CHIRPS, while both products diverged notably over complex terrain such as the Western Ghats \citep{kumar2025long}."),
 ("singh2021deep", "N",
  r"At the global scale, \citet{singh2021deep} trained a residual U-Net on reanalysis data in a cubed-sphere framework and reported improved correlation skill over an operational numerical weather prediction system, while also emphasizing the need for hybrid integration and probabilistic evaluation.",
  r"At the global scale, a residual U-Net trained on reanalysis data in a cubed-sphere framework was reported to improve correlation skill over an operational numerical weather prediction system, and the same study emphasized the need for hybrid integration and probabilistic evaluation \citep{singh2021deep}."),
 ("miller2021analysis", "N",
  r"\citet{miller2021analysis} examined short-term and seasonal rainfall forecasts in Kenya and found substantial regional differences in forecasting skill, highlighting the importance of localized validation.",
  r"An analysis of short-term and seasonal rainfall forecasts in Kenya found substantial regional differences in forecasting skill, highlighting the importance of localized validation \citep{miller2021analysis}."),
 ("kendall2017uncertainties", "W",
  r"\citet{kendall2017uncertainties} introduced a probabilistic regression framework in which neural networks jointly predict the mean and variance of a Gaussian likelihood, allowing data-dependent uncertainty to be estimated directly from the model.",
  r"A probabilistic regression framework has been introduced in which neural networks jointly predict the mean and variance of a Gaussian likelihood, allowing data-dependent uncertainty to be estimated directly from the model \citep{kendall2017uncertainties}."),
 ("9001195", "W",
  r"\citet{9001195} proposed a framework that combines assumed density filtering and Monte Carlo dropout to model both data and model uncertainty without retraining, reporting improvements in calibration and robustness across perception and control tasks.",
  r"Another proposed framework combines assumed density filtering and Monte Carlo dropout to model both data and model uncertainty without retraining, with reported improvements in calibration and robustness across perception and control tasks \citep{9001195}."),
 ("klotz2022uncertainty", "W",
  r"\citet{klotz2022uncertainty} compared several probabilistic deep learning approaches for rainfall-runoff modeling and found that asymmetric Laplacian mixture networks produced more accurately calibrated predictions than Gaussian or dropout-based approaches, particularly under extreme flow conditions.",
  r"In rainfall-runoff modeling, a comparison of several probabilistic deep learning approaches found that asymmetric Laplacian mixture networks produced more accurately calibrated predictions than Gaussian or dropout-based approaches, particularly under extreme flow conditions \citep{klotz2022uncertainty}."),
 ("mena2021survey", "W",
  r"\citet{mena2021survey} reviewed a range of uncertainty estimation methods, including variational inference, Monte Carlo dropout, ensembles, and Dirichlet prior networks, and discussed their trade-offs in calibration, interpretability, and computational cost.",
  r"A review of uncertainty estimation methods, including variational inference, Monte Carlo dropout, ensembles, and Dirichlet prior networks, discussed their trade-offs in calibration, interpretability, and computational cost \citep{mena2021survey}."),
 ("chakraborty2017interpretability", "W",
  r"\citet{chakraborty2017interpretability} provided an early systematic overview of interpretability research, distinguishing model transparency, functionality, and different forms of explanation.",
  r"An early systematic overview of interpretability research distinguished model transparency, functionality, and different forms of explanation \citep{chakraborty2017interpretability}."),
 ("li2022interpretable", "W",
  r"\citet{li2022interpretable} developed a unified taxonomy linking interpretation, interpretability, and trustworthiness, providing a general basis for evaluating explanations produced by machine learning systems.",
  r"A unified taxonomy linking interpretation, interpretability, and trustworthiness has also been developed, providing a general basis for evaluating explanations produced by machine learning systems \citep{li2022interpretable}."),
 ("vinuesa2021interpretable", "W",
  r"\citet{vinuesa2021interpretable} discussed the role of interpretable deep learning in sustainable development and emphasized the value of models that incorporate meaningful and understandable representations.",
  r"In the context of sustainable development, the role of interpretable deep learning has been discussed, with emphasis on the value of models that incorporate meaningful and understandable representations \citep{vinuesa2021interpretable}."),
 ("temenos2023interpretable", "W",
  r"\citet{temenos2023interpretable} developed an interpretable deep learning framework combining a compact CNN with SHAP-based explanations to provide both local and global feature attributions in remote-sensing classification.",
  r"For remote-sensing classification, an interpretable deep learning framework has been developed that combines a compact CNN with SHAP-based explanations to provide both local and global feature attributions \citep{temenos2023interpretable}."),
 ("yoganand2026shap", "W",
  r"\citet{yoganand2026shap} proposed a SHAP-integrated LeNet model with transfer learning for flood prediction in Telangana, combining engineered feature selection with attention-based convolutional layers and using SHAP to explain model outputs.",
  r"For flood prediction in Telangana, a SHAP-integrated LeNet model with transfer learning has been proposed, combining engineered feature selection with attention-based convolutional layers and using SHAP to explain model outputs \citep{yoganand2026shap}."),
 ("yang2024interpretable", "W",
  r"\citet{yang2024interpretable} reviewed recent developments in interpretable machine learning for weather and climate prediction, highlighting the use of feature attribution, attention mechanisms, and physics-informed approaches to examine relationships learned by data-driven models.",
  r"A recent review of interpretable machine learning for weather and climate prediction highlighted the use of feature attribution, attention mechanisms, and physics-informed approaches to examine relationships learned by data-driven models \citep{yang2024interpretable}."),
 ("lerch2017forecaster", "N",
  r"As discussed by \citet{lerch2017forecaster}, evaluating forecasts only on cases selected by their observed outcomes can distort comparative rankings.",
  r"Evaluating forecasts only on cases selected by their observed outcomes can distort comparative rankings \citep{lerch2017forecaster}."),
]
T = open('manuscript.tex', encoding='utf-8').read()
log = []
for key, mode, old, new in C:
    assert T.count(old) == 1, (key, T.count(old))
    ln = T.count('\n', 0, T.index(old)) + 1
    rep = '\\revminor{' + new + '}' if mode == 'W' else new
    T = T.replace(old, rep)
    log.append(dict(key=key, line=ln, red=('wrapped in \\revminor' if mode == 'W' else 'already inside red block'), old=old, new=new))
# global style: drop the author-year comma via natbib's supported \setcitestyle (no class/bst edit)
anchor = '\\newcommand{\\revminor}'
assert T.count(anchor) == 1
T = T.replace(anchor, '\\setcitestyle{aysep={}}% (Author 2022): no comma between author and year\n' + anchor)
open('manuscript.tex', 'w', encoding='utf-8').write(T)
json.dump(log, open(f'{R}/evidence/conversions_applied.json', 'w'), indent=1, ensure_ascii=False)
print(len(log), 'conversions applied')
