# R2-M6正式整合证据索引

原实验固定提交d02519c5f153feb712018cf97efb035f6ca2d7ae；闭式/90%宽度/方法核验固定提交7923bfefe65095621f2064d9b99adadb7e999e8b。13个直接制表/定义输入的实际路径及MD5见SOURCE_INDEX.json；全部均与对应Git对象逐字节相符。

CELL_INDEX.csv/json逐条给出685个数值转录的源文件、原始CSV行号/字段、原值与显示值；full均值/SD列出其5个seed键和聚合定义。ROW_INDEX.json记录新8表的94行目标位置；check_integration.py独立核对每行CSV列与主表A2/B。原A1的18个标量保持原tabular逐字相同，见ORIGINAL_A_TABULAR.tex。

- q11 full/twCRPS及其区间仅使用q11_twcrps_per_seed和q11_twcrps_paired；不用q11_summary/crps_all或q11_paired_bootstrap/crps的199分位近似替代。
- q11非CRPS指标使用q11_per_seed/q11_summary，IS95、Cov95、Width95和Brier配对使用其匹配q11_paired_seed/q11_paired_bootstrap。
- Width90直接使用7923bfe的width90_per_seed和width90_summary；原q05/q95未改动。
- 原研究扩展A2仅取q16_interval_summary的q14_rerun_5seed行，独立于A1主研究与B的q11 Gaussian。
- S45为seed42历史选择，S46为观测条件历史诊断，均明确标199分位、不是主表full。dry.01 nseed=1；Tobit(.001)匹配full块区间未保存，不借其他区间。
- Review原文由comment及原始Word核实为heavy rainfall；REVIEW_SOURCE记录Word路径、MD5及段号。35项任务误引已纠正。未修改审稿人原话。
- 新增4条原始方法/评分参考文献，题名/作者/卷期页/DOI及出版商来源见BIB_VERIFICATION。保留印刷年份，不误用平台后补上线年份。

## 实际label和起始页

| label | 自动编号 | 页 |
|---|---|---|
| `stab:r2m6_q16_intervals` | S39 | 42 |
| `stab:r2m6_seed_scores` | S40 | 43 |
| `stab:r2m6_seed_intervals` | S41 | 44 |
| `stab:r2m6_score_pairs` | S42 | 45 |
| `stab:r2m6_other_pairs` | S43 | 46 |
| `stab:r2m6_dry001` | S44 | 47 |
| `stab:r2m6_dry_history` | S45 | 48 |
| `stab:r2m6_conditional_history` | S46 | 49 |
| `tab:probabilistic_results` | 5 | 60 |
| `sec:r2m6_likelihood_results` | 4.4.1 | 63 |

最终全稿页码/行号尚未写入Response位置说明；此处为当前核验PDF定位。旧R1/R2-M1–M5摘录、S1–S38、其他主表及旧图保持，见VERIFICATION和DOCUMENT_HASHES。

## 归档与关闭

首轮必要整合归档`86fdcfb3ef039be31c685346510b5a3ab023a463`已推送origin/main，24/24固定提交GitHub blob与本地一致（REMOTE_RECEIPT）。最终关闭提交补充历史CRPS措辞、当前PDF哈希和限定任务状态；正式实验数据未改变。原始科学输入仍为d02519c/7923bfe，不改写。
