# R2-M4正式整合证据索引

锁定版本：`667d6f80e64076dc6812ca630654a24d1aab5b4e`。原fixed四文件与工作区一致。所有下列文件从该固定Git对象读取。

|原路径|MD5|
|---|---|
|`code/analysis_r2m4_fixed_paired_ci.py`|`fe3b951eb09c0f3d4f11cef00135535c`|
|`code/analysis_q05e_event_paired_ci.py`|`b429dd451547da117ff7d7819b49deaf`|
|`code/analysis_q05g_multiseed_events.py`|`01307d3d2c9df238e8f38e07f75ef7a8`|
|`code/fig_style.py`|`b97ce38e27500160de582a79b7f34a9a`|
|`results/r2m4_evidence_archive/METHOD_AUDIT.md`|`b1b0021bd6f4c4bf0a8d07cc12c6463a`|
|`results/metrics/r2m4_fixed_event_paired.csv`|`9739ce1b23215652b3f0204835c7d51b`|
|`results/metrics/r2m4_fixed_event_scores.csv`|`9062d963e8604283005c81b82bacc6cf`|
|`results/metrics/r2m4_fixed_output.txt`|`5b6fce34f4a05e8b7188c79722009a3b`|
|`results/metrics/q05e_event_scores.csv`|`df8e768a265692e597c39ecf7ccf643d`|
|`results/metrics/q05e_event_paired.csv`|`305d0bab643fbee5d1f5d5fefe8a25d6`|
|`results/metrics/q05e_output.txt`|`a14fdf1cc1b07f81b02906bed38451b4`|
|`results/metrics/q05g_multiseed_summary.csv`|`3b6ee8c01a97b7141628bb556be9edf3`|
|`results/metrics/q05g_multiseed_paired.csv`|`9d33d5bb27a598aa6ea709bb74498565`|
|`results/metrics/q05g_multiseed_per_seed.csv`|`b3d27be356f024b32948e8bf6cc66421`|
|`results/metrics/q05g_output.txt`|`625714619864fa45f448b5671900292f`|
|`results/metrics/q05_spread_calibration.csv`|`a0150c8bf8f666950e3635d6921cccdc`|
|`results/figures/revision/r1M1_prediction_distribution_stats.csv`|`39dee70a92fb1433ffaa774274c8f9a8`|

逐格数值映射：CELL_INDEX.csv/json，含目标label、源CSV行号（含表头）、字段、完整值、排版值和行键；图点另列FIGURE_POINTS.json。图中数值均由保存CSV读取，实际τ标签由固定分数表的thr_mm_h读取，不手工估计。

q05e正式300网格脚本与输出已在先前METHOD_AUDIT及35/35匹配中核验，不使用Downloads的500旧版本。q05g脚本和运行输出确认28/2,000/42；汇总表是种子指标均值/SD，paired表是五种子平均预测另选验证cutoff后的差值，二者不混用。

Supplementary固定表的AUC复用相同连续保存预测在q05e的值，仅用于六学习模型/Persistence及已有五阈值。0.5 AUC、固定规则新AR/气候态AUC和未保存的基线配对项均留空横线，不从其他运行集合填入。旧regional序列与XGBoost y_true在六阈值下的事件标签逐样本一致，已只读验证。

既有METHOD_AUDIT中的Holm近似p及事后选族问题保留为方法背景，本轮主文/补充表不展示Holm结果，不新增检验追求显著性。没有重新训练或生成正式预测；只对保存指标进行算术/转录核验。

独立对应关系表未在项目根目录找到；本轮直接核对35项任务文件05/12中的审稿原文、对应意见和清单，不依赖不存在的额外表。
