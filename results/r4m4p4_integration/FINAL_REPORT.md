# R4-M4 P4 — local implementation report (2026-11-16)

Scope: P4 only. P1–P3, P5–P6, the R4-M4 reply, EvidenceBoxes, Supplementary, BibTeX and the template are untouched.

## Change
- manuscript.tex §5.2, the paragraph starting "The Gaussian likelihood also imposes a structural limitation on the uncertainty estimates." (source line 1240; a black, non-red paragraph).
- The approved text is appended verbatim after "... test periods or event-detection rules.", wrapped in `\revminor{...}` (red text and red citation links; old text keeps its colour).
- Patch: R4_M4_P4_LOCAL.patch (manuscript.tex, 1 hunk), rebuilt from before/ with git apply and BSD patch → identical to after/.

## Protection
- No excerpt quotes the target paragraph. Excerpt 90 (R2 M6) quotes the following red paragraph ("An alternative precipitation-appropriate likelihood ..."). The insertion sits before it and the excerpt stays contiguous. Other window hits are generic phrases.
- 170/170 matched, identical and in order. §5.4 "Limitations and Future Work" onward is byte-identical. P1, P2 and P3 are intact.

## Literature and meaning
- Cannon 2008: expanded Bernoulli–Gamma density network for probabilistic multisite precipitation downscaling. It is cited only for using the distribution to represent occurrence and positive amounts, not for superiority over Gaussian.
- Baño-Medina et al. 2020 (full text §4.2, checked in the R4-M4 read-only audit): deterministic predictions slightly underestimate P98, which "can be solved by stochastically sampling from the predicted gamma distribution", at some cost to temporal and spatial correlation. The new text matches this.
- The text explicitly separates percentile bias from prediction-interval coverage. It claims neither the same upper-tail coverage result, nor B–G superiority, nor that the distribution change solved the reliability problem. The existing statements (B–G removed negative bounds and improved overall scores; upper-tail undercoverage remained; limited to Probabilistic BiLSTM-Attention) are unchanged.
- Flow: the next paragraph (R2 M6, protected) restates that the alternative likelihood improved overall skill but undercoverage remained. Mild thematic repetition, no contradiction.

## Checks
- BibTeX: cannon2008bernoulli ×1, bano2020configuration ×1, banomedina2020configuration ×0 (not used). Both resolve. Renders "(Cannon 2008; Baño-Medina et al 2020)" and "(Baño-Medina et al 2020)". No metadata gaps found in either entry. BibTeX unchanged.
- `\citet` occurrences 9 (accepted E1–E9).
- Builds: manuscript 114 pp (was 113), Supplementary 80 pp, Response letter 102 pp; no errors, 0 undefined, 0 multiply defined.
- Layout: no overfull \hbox. The overfull count 113 = one per-page 1.41 pt \vbox template artefact per page. Render: render/manuscript_p090_P4.png.
