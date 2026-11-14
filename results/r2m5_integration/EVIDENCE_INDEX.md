# R2-M5证据索引（2026-11-14）

固定科学证据提交：`395234ebcce2269a71bfcfc6bff5bcdf14ce0086`，已确认为当前origin/main历史中的祖先。
全部214个小型原始源文件/运行记录的Git路径、MD5、SHA256和大小见SOURCE_INDEX.json；未重新生成输出。下面列关键文件。

| 原始Git路径 | MD5 |
|---|---|
| `code/q06_common.py` | `fd11bd85160fe9118bc945a40feffa28` |
| `code/q06_train.py` | `fc5c0797007f3181edb6d2955a002b18` |
| `code/q06_stats.py` | `f9bc9ac25c40f69e60d9632ce5ce7045` |
| `results/metrics/q06_audit_output.txt` | `26c48cc0eaff19463eff0d98448784ee` |
| `results/metrics/q06_fold_metrics.csv` | `5ec53804f8dc1eb9975ad3e81390bc89` |
| `results/metrics/q06_history_effect.csv` | `1f72678e61c8b5a1be5093b4396a01f9` |
| `results/metrics/q06_pairwise.csv` | `96e28ac9cf9ade14e3e3f6de1a367639` |
| `results/metrics/q06_block_sensitivity.csv` | `bacaa2b532e227fbf74d4f3df41b9137` |
| `results/metrics/q06_conditional_coverage_summary.csv` | `51aa5f64c426d5881d97d7b15a8a20d0` |
| `results/q06/folds/ORIG.json` | `0d273e7c79ca68e244b3b2b81e1ae160` |
| `results/q06/folds/F4.json` | `02b5f16a6020cb5124ac65c1ba3c71c3` |
| `results/metrics/q06_repro_output.txt` | `9ce5465a1f3f46d8e760f137eee6f478` |

- 归档预测包：`results/q06/q06_preds_20261106.tar.gz`，MD5 `09df56057dd05fa2ac7451e6fed2306f`。包内150份F1/F2/F3/F4/F4s预测CSV逐文件MD5、行数见PREDICTION_ALIGNMENT.json；没有重新拟合或计算预测指标。
- 所有预测在各配置内部跨模型/种子的有效时刻与保存y_true一致；与fold JSON的首末时刻及n逐一吻合。F4/F4s时刻完全一致，逆标准化y_true最大差：validation 2.283782185585892e-07，test 1.8135786339357196e-07。原统计脚本使用<1e-6容差；不宣称两配置数值逐位相同。
- `CELL_INDEX.csv/json`：1,541个数值转录，含CSV原始行号、字段、原值、显示值；JSON源含json_path。`ROW_INDEX.json`进一步逐行验证267个统计行的目标列位置（另5个设计行来自fold JSON）。未填造缺失值。
- 原主研究Bootstrap：固定提交内`code/Interpretable_analysis.ipynb`第32格（零起始31，Step17B）；文件及单元源MD5见MAIN_BOOTSTRAP_SOURCE.json。`code/analysis_q03c_wet01_bootstrap.py`补充确认新版wet掩码；circular28/10000/42、按完整时间轴抽样后掩码，截断末块。
- q06统计方法：`code/q06_stats.py:29–31`配置，`:112–121`非循环完整块，`:129–152`history统计及common Q95，`:174–217`配对/合并/敏感性。最终准确行号以该固定源文件为准；无重抽样检验或p值声明。
- q06覆盖：`code/q06_coverage.py`及原per-seed与summary CSV，Gaussian参数、fold Q95、五种子SD。没有新增未保存区间。
- 原始审稿文档与完整映射表均可读取；路径、MD5、匹配段号和原文见REVIEW_SOURCE.json，审稿原文与comment.txt一致。
- Claude只读审计已作为导航阅读；其补算逐年表没有作为新增正式结果使用。

## 最终自动编号与位置

| label | 实际编号 | 起始页 |
|---|---|---|
| `stab:r2m5_design` | S32 | 31 |
| `stab:r2m5_performance` | S33 | 32 |
| `stab:r2m5_history` | S34 | 34 |
| `stab:r2m5_pairs_all` | S35 | 35 |
| `stab:r2m5_pairs_wet` | S36 | 37 |
| `stab:r2m5_block_sensitivity` | S37 | 39 |
| `stab:r2m5_coverage` | S38 | 40 |
| `sec:rolling_origin_methods` | 3.4.1 | 33 |
| `sec:rolling_origin_results` | 4.2.5 | 48 |

## 科学边界

F4并非与ORIG测试目标完全相同。ORIG验证至2019-04-20 12:00，测试自2019-04-22 06:00；F4从2019-01-02 12:00开始，其早2019部分亦参与过原开发。各折拟合/预处理隔离不等于模型设计独立。F4prime13完整训练年也不是主研究原70/15/15划分。

q06的CLIM是逐折训练拟合的month×hour参考，不是Table3原overall-mean climatology；history上尾用common Q95=.574048，coverage/event用各配置Q95。q06 Bootstrap逐种子RMSE差取均值，不是平均预测后计分；非循环完整末块，5000重复，与主比较circular10000不同。
