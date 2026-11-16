# Replaces the R4 M4 placeholders (\PendingResponse, \ChangeLocation) with the approved reply,
# a \ManuscriptChange box and EvidenceBoxes quoting current manuscript.tex verbatim.
import json, sys
R = sys.argv[1]
X = {e['item']: e['text'] for e in json.load(open(f'{R}/evidence/excerpts_from_current_manuscript.json'))}
RESP = r"""\AuthorResponse{We thank the reviewer for this important comment. We agree that, although the original Discussion addressed the main findings and limitations, its connections to the existing literature were insufficient. We have therefore revised Sections~5.1--5.4 to relate the principal results to relevant published studies, clarify the similarities and differences between their settings and ours, and make the limits of these comparisons explicit.

\textit{Overall model comparison (Section~\ref{manuscript-sec:overall_discussion}).} We now discuss the comparable overall performance of XGBoost and the recurrent models in relation to evidence that tree-based methods remain competitive with deep neural networks on medium-sized tabular datasets, and to precipitation forecasting research reporting comparable performance from shallower and deeper U-Net configurations. We explicitly acknowledge differences in data representation, architecture and prediction setting.

\textit{Upper-tail evaluation and probabilistic reliability (Section~\ref{manuscript-sec:upper_tail_discussion}).} We have added literature addressing the forecaster's dilemma to clarify that RMSE evaluated on observed upper-tail events is a conditional diagnostic, rather than evidence of unconditional forecasting superiority. We also compare the observed upper-tail amplitude compression with findings from radar-based deep-learning nowcasting, without assuming a shared mechanism. The Bernoulli--Gamma discussion is now connected to earlier neural-network precipitation downscaling studies, while explicitly distinguishing precipitation-percentile bias from prediction-interval coverage. We additionally refined the wording of the tree-model comparison to align the scope of the cited evidence with medium-sized tabular datasets rather than making an unsupported claim about imbalanced sample sizes.

\textit{Predictor attribution (Sections~\ref{manuscript-sec:predictor_complementarity} and~\ref{manuscript-sec:limitations}).} We have related the complementary interpretation of correlation, SHAP and ablation to published geoscientific research on the strengths and limitations of different XAI methods. We further cite methodological work demonstrating that Shapley-value explanations can be misleading when dependencies between correlated predictors are not adequately accounted for. These references support a cautious interpretation of attribution results without implying meteorological causality.

\textit{Verification and observational limitations (Section~\ref{manuscript-sec:limitations}).} We have strengthened the discussion of ERA5-based verification by citing evaluations of ERA5 precipitation against rain-gauge measurements and the verification design of WeatherBench~2. We explicitly distinguish reanalysis-referenced assessment from independent observational validation. We also clarify that the net effect of the verification reference on the present HRES comparison has not been quantified and that differences in precipitation accumulation windows remain a limitation.

Together, these revisions connect the Discussion more directly to established research while distinguishing supporting evidence, relevant differences in experimental settings, and unresolved methodological limitations. No numerical results or substantive experimental conclusions have been changed.}"""
CHG = r"""\ManuscriptChange{Section~\ref{manuscript-sec:overall_discussion}: literature on tree-based versus deep models and on U-Net depth added at the end of the first paragraph. Section~\ref{manuscript-sec:upper_tail_discussion}: conditional upper-tail evaluation (forecaster's dilemma) added to the first paragraph; comparison with radar-based deep-learning nowcasting added to the second paragraph; the scope of the tree-model citation corrected from ``limited or imbalanced sample sizes'' to ``medium-sized datasets''; Bernoulli--Gamma downscaling literature added to the paragraph on the Gaussian likelihood. Section~\ref{manuscript-sec:predictor_complementarity}: XAI method-intercomparison literature added to the first paragraph. Section~\ref{manuscript-sec:limitations}: ERA5--rain-gauge evaluation added to the station-validation paragraph; WeatherBench~2 verification design added to the HRES-scope paragraph; Shapley values under feature dependence added to the SHAP-interpretation paragraph. Nine sources were added to the Discussion; no numerical result was changed.}"""
BOXES = [
 ('P3',  r'Tree-based and U-Net comparisons (Section~\ref{manuscript-sec:overall_discussion})'),
 ('P1',  r'Conditional upper-tail evaluation (Section~\ref{manuscript-sec:upper_tail_discussion})'),
 ('P2',  r'Amplitude compression in data-driven forecasts (Section~\ref{manuscript-sec:upper_tail_discussion})'),
 ('P1c', r'Corrected scope of the tree-model citation (Section~\ref{manuscript-sec:upper_tail_discussion})'),
 ('P4',  r'Bernoulli--Gamma downscaling literature (Section~\ref{manuscript-sec:upper_tail_discussion})'),
 ('P5a', r'XAI method intercomparison (Section~\ref{manuscript-sec:predictor_complementarity})'),
 ('P6a', r'ERA5 precipitation against rain gauges (Section~\ref{manuscript-sec:limitations})'),
 ('P6b', r'WeatherBench~2 verification design (Section~\ref{manuscript-sec:limitations})'),
 ('P5b', r'Shapley values under feature dependence (Section~\ref{manuscript-sec:limitations})'),
]
block = RESP + '\n\n' + CHG + '\n\n' + '\n\n'.join(f'\\EvidenceBox{{{t}}}{{\n\\RevisedExcerpt{{{X[k]}}}\n}}' for k, t in BOXES) + '\n'
L = open('Response letter.tex', encoding='utf-8').read()
old = "This is a major drawback, bigger than point 1.}\n\n\\PendingResponse\n\n\\ChangeLocation\n\n% Review ID: R4 m1"
assert L.count(old) == 1
L = L.replace(old, "This is a major drawback, bigger than point 1.}\n\n" + block + "\n% Review ID: R4 m1")
open('Response letter.tex', 'w', encoding='utf-8').write(L)
print('boxes', len(BOXES))
