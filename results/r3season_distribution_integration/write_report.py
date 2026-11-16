from pathlib import Path
import json,hashlib,csv,re
P=Path(__file__).resolve().parent;V=json.loads((P/'VERIFICATION.json').read_text());D=json.loads((P/'SAVED_RESULTS_CHECK.json').read_text());F=json.loads((P/'FIGURE_CHECK.json').read_text());pdf=json.loads((P/'PDF_CHECK.json').read_text())
assert all(x['visual_review'].startswith('PASS') for x in pdf.values())
def mdtable(header,rows):return '| '+' | '.join(header)+' |\n|'+'|'.join(['---']*len(header))+'|\n'+''.join('| '+' | '.join(map(str,r))+' |\n' for r in rows)
locs=[]
for file,anchors in {'manuscript.tex':['Full-period seasonal distributions use','The separate q03d sensitivity compares','The q03d seasonal-training sensitivity did not'], 'Supplementary.tex':['stab:r3season_full_distribution','sfig:r3season_full_cdf','stab:r3season_gsf_scores','stab:r3season_gsf_pairs'], 'Response letter.tex':['% Review ID: R3 L469-471']}.items():
 lines=Path(file).read_text().splitlines()
 for a in anchors:locs.append(dict(file=file,anchor=a,line=next(i+1 for i,l in enumerate(lines) if a in l)))
(P/'LOCATIONS.json').write_text(json.dumps(locs,indent=2))
report='''# R3-14 final local scientific report

**R3-14 local scientific revision complete — Git archiving deferred.** Author review pending; not formally CLOSED or remotely archived. No training, downloads, staging, commit or push. R3-13 remains OPEN and its NWP limitations are unchanged.

## Three reviewer questions

A. The protected training Q95 definition is retained:0.5740 mm h⁻¹ comes from18404 regional-mean hourly training targets on the original scale. It is a statistical upper-tail cutoff, not a physical extreme-rainfall classification. The WMO3-minute classification and region/hour support difference remain intact. Wet≥0.1, legacy>0 and≥1 event diagnostics are kept separate; no universal “below1 means no rain” rule is adopted.

B. Existing q03d tests G/S/F with identical base hyperparameters, variables, chronological split and five seeds42/123/7/2024/99, no seasonal retuning. G/S each have42 meteorological inputs (six snapshots×seven variables); F adds four sine/cosine calendar features for the target month/hour. Training windows:DJF4566/MAM4784/JJA4686/SON4368; common3939 test targets. Model labels and run set are distinct from q13 and the main performance table. No evidence of consistent seasonal-specialization gain under these tested settings; no claim of general ineffectiveness and no extension to deep-model seasonal retraining.

C. The existing historical CDF is scientifically useful but uses26282 post-window targets, not all26300 retained timestamps. Its18 exclusions are exactly the first six timestamps in each partition (listed in OMITTED_18_TIMESTAMPS.csv). A new corrected FigureS4 uses the complete sampled archive; old figure/script/CSV preserved byte-for-byte in evidence and existing Git objects. No existing evaluation target or score changed.

## Full-period seasonal CDF

Source: existing regional table MD5 `f9b4f8a22c8b7849f40eb71918fe1fd6`; all26300 unique, uninterrupted six-hourly timestamps from2004-01-01 00:00 through2021-12-31 18:00 UTC. These are preceding-hour amounts (mm, numerically mm h⁻¹) spatially averaged over25 cells, sampled at00/06/12/18UTC: **not all24 daily hours and not six-hour accumulated rainfall**. Regional values were cross-checked against archived q04 pairs at all timestamps, maximum difference1.01e-13mm. Original raw gridded ERA5 file was not newly read or downloaded; the regional dependency matches prior R2-M7's audited MD5.

FigureS4 uses unconditional all-sample ECDFs with exact zeros retained, plus P(Y≥y) on a log scale; ties are handled separately from P(Y≤y). Both panels cover the full observed intensity range0–4.13454, axes extend to4.3. No wet-only conditioning. TrainingQ95 stays fixed; seasonal full-period quantiles are descriptive only.

'''
report+=mdtable(['Season','N','Exact zeros','Wet≥0.1 (%)','≥1 (%)','Q95 mm h⁻¹','Max mm h⁻¹'],[[r['Season'],r['N'],r['Zero_n'],f"{r['Wet_pct']:.4f}",f"{r['Ge1_pct']:.4f}",f"{r['Q95']:.6f}",f"{r['Max']:.6f}"] for r in D['season_stats']])
report+='''
Original historical seasonal counts6494/6618/6618/6552 become6500/6624/6624/6552. The rounding to two decimals remains approximately.62/.46/.59/.67; the actual four-decimal updated values are.6197/.4575/.5877/.6726. Complete ECDF points/counts/denominators are saved in FULL_PERIOD_ECDF.csv. The new figure uses shared fig_style geometry/size constants and Latin Modern, native119.0×132mm, minimum base/tick8pt. The local machine lacks dvipng/Poppler binaries, so PGF/pdflatex renders the same typography; embedded fonts verified as Latin Modern. This is disclosed in FIGURE_CHECK.json. It is inserted without width scaling.

## q03d complete comparison

All105 seed×strategy×subset rows checked against21 summary rows. Below are seed-mean RMSE±sampleSD in mm h⁻¹. Full MAE/SS means and SD are in S62 and the source CSV; S10/S11 remain unchanged.

'''
raw=list(csv.DictReader((P/'evidence/q03d_seasonal_xgb_summary.csv').open()));pairs=list(csv.DictReader((P/'evidence/q03d_seasonal_xgb_paired.csv').open()));ordered=['all','DJF','MAM','JJA','SON','wet>=0.1','tail>=Q95'];counts={'all':3939,'DJF':848,'MAM':895,'JJA':1104,'SON':1092,'wet>=0.1':854,'tail>=Q95':238}
report+=mdtable(['Subset','N','G','S','F'],[[s,counts[s]]+[next(f"{float(z['RMSE_mean']):.4f} ± {float(z['RMSE_std']):.4f}" for z in raw if z['Variant']==v and z['Subset']==s) for v in ['G','S','F']] for s in ordered])
for comp in ['S_minus_G','F_minus_G']:
 report+='\n### '+comp+'\n\n'
 report+=mdtable(['Subset','Seed mean Δ','Seed SD','Worse seeds','Mean-prediction Δ','95% block CI'],[[z['Subset'],z['seed_mean_delta_RMSE'],z['seed_std_delta'],z['n_seeds_worse']+'/5',z['seedavg_pred_delta_RMSE'],'['+z['boot_CI_low']+', '+z['boot_CI_high']+']'] for z in pairs if z['Comparison']==comp])
report+='''
**Estimands:** +.0029 is mean seed-level S−G RMSE; +.0020 and its[-.0012,+.0056] interval score seed-averaged predictions. F SON+.0052(seed-score mean) differs from+.0050(mean-prediction statistic). Neither pair may be interchanged. Seed SD captures fitted-run variation, not a seed-t CI (none saved by q03d). Conditional sample-bootstrap intervals do not combine both uncertainty sources.

All14 mean-prediction point estimates and percentile intervals were independently recomputed using the saved3939-row prediction-mean CSV; all match the archived four-decimal output. Circular blocks28,2000replicates,seed42;141 complete blocks produce3948positions, then truncated to3939. Same sampled indices for all strategies, subset masks applied after sampling. The q03d implementation therefore differs from untruncated noncircular q13/q14 procedures. Intervals are pointwise, unadjusted. The run log records these settings; no new model fit occurred.

S−G all seasonal intervals include zero. F improves JJA and worsens SON on this ensemble-prediction sampling scale, without multiplicity adjustment. Overall both S/F intervals include zero. Seasonal wet/tail score rows are also retained. These findings justify retention under the tested conditions, not proof that seasonal models cannot help.

**Evidence limitations:** individual q03d seed prediction files/weights are not present in this archive; all105 original raw metrics and their aggregation/direction counts were verified, but individual seed predictions cannot be independently regenerated without retraining. The saved five-seed mean predictions suffice for all14 paired bootstrap checks. Hyperparameters were not retuned by season, and deep models were not seasonally retrained. Short test-period seasonal coverage remains a limitation. No causal explanation for specialization gains/losses is claimed.

## Documents and table/figure registry

Main §4.2.3 adds two red paragraphs (full distributions and G/S/F interpretation); §5.4 adds one red paragraph (scope/uncertainty). Existing paragraphs are byte-identical after removal of these additions. No change to Abstract, Conclusion, original model settings or saved results.

S61 (`stab:r3season_full_distribution`) p69:4 seasonal rows. FigureS4 (`sfig:r3season_full_cdf`) p70:corrected full-period distribution. S62 (`stab:r3season_gsf_scores`) p71:21 G/S/F subset score rows. S63 (`stab:r3season_gsf_pairs`) p72:14 paired comparison rows. These expand the previously partial G/S presentation without altering S10/S11 or any S1–S60 content.

Response letter: only R3 Lines469–471 replaced; original comment unchanged, formal response red,3new exact excerpts and location notes blue. Task03/registry/checklist appended only for R3-14; other shared opinions retain prior states. Source locations are in LOCATIONS.json. Final published page/line annotations remain deferred.

## Final verification

-255 new tabulated CSV fields,39 data rows validated at exact destination rows;14 bootstrap comparisons reproduced to archived precision. PROSE_FACT_INDEX.json maps added narrative numbers and settings.
-144 old RevisedExcerpt arguments byte-identical and all match latest sources;3new match,147/147 total. BEFORE_AFTER_EXCERPT_MAP.json records content hashes and stable matches, not only line numbers.
-All other reviewer response blocks byte-identical, including R1-M2/R3-09/R3-11/R3-12/R3-13. Original main tables/figures and all original main paragraphs retained. S1–S60/Fig.S1–S3 source prefix and17 prior figure files unchanged. Bibliography unchanged.
-Three PDFs built in Supplementary→manuscript→Response order:104/72/91pages. No undefined references, duplicate labels, blocking errors, horizontal overflows or oversized floats. The pre-existing manuscript1.41457pt output-vbox warning repeats103times due to its104-page pagination; no new warning type. Supplementary/reply have no overfull warnings.
-Actual rendered checks:main56/93, Supplementary69–72, reply73–76. New graph and tables complete, legible and uncropped; no overlap; red/blue markings correct. PDF_CHECK.json contains hashes and visual results.
-Git index unchanged; no stage/commit/push. Original workspace's unrelated changes retained. R2-M9 repository-documentation pending state and R3-13 OPEN retained. Not proceeding to Reviewer3 Section4.1.

## Formal English reply (readable reference numbers)

'''+(P/'AUTHOR_RESPONSE_READABLE.md').read_text()+'''

## Deliverables

- R3_14_LOCAL.patch: current local manuscript/Supplementary/reply and task-record increment; not applied to original tree twice.
- CELL_INDEX.json / ROW_INDEX.json / PROSE_FACT_INDEX.json / SOURCE_INDEX.json / LOCAL_DEPENDENCY.json.
- SAVED_RESULTS_CHECK.json / BOOTSTRAP_RECHECK.json / EXCERPT_INDEX.json / BEFORE_AFTER_EXCERPT_MAP.json / VERIFICATION.json.
- FULL_PERIOD_SEASON_STATS.csv / FULL_PERIOD_ECDF.csv / OMITTED_18_TIMESTAMPS.csv.
- verify_saved.py and its log; plot_full_season_cdf.py and its log; check_integration.py; FIGURE_CHECK.json; PDF_CHECK.json; GIT_STATUS.txt.
- Figures/r3M14_season_cdf_full.pdf (old figure retained). Compiled submission PDFs stay in build/, not uploaded.

**No blocking scientific issue found for this bounded R3-14 response.** Reproduction limits above remain explicit; Git archive deferred pending author review.
'''
(P/'FINAL_REPORT.md').write_text(report)
# Current final increment, not the initial generator's working draft.
S=Path('Supplementary.tex').read_text();(P/'SUPPLEMENTARY_INCREMENT.tex').write_text(S[S.index('% R3-14:'):S.index(r'\end{document}')])
sourcehash={f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in ['manuscript.tex','Supplementary.tex','Response letter.tex','sn-bibliography.bib']}
for stem,x in pdf.items():x['final_source_sha256']=sourcehash
(P/'PDF_CHECK.json').write_text(json.dumps(pdf,indent=2))
artifacts=[]
for q in sorted(P.glob('*')):
 if q.is_file() and q.name not in ['ARTIFACT_INDEX.json']:
  artifacts.append(dict(path=str(q),bytes=q.stat().st_size,md5=hashlib.md5(q.read_bytes()).hexdigest(),sha256=hashlib.sha256(q.read_bytes()).hexdigest()))
fig=Path(F['path']);artifacts.append(dict(path=str(fig),bytes=fig.stat().st_size,md5=hashlib.md5(fig.read_bytes()).hexdigest(),sha256=hashlib.sha256(fig.read_bytes()).hexdigest()))
(P/'ARTIFACT_INDEX.json').write_text(json.dumps(artifacts,indent=2));print('Final report, readable full response, local artifacts and PDF/source hash record written.')
