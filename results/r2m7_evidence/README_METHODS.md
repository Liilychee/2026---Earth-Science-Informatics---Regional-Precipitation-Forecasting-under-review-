# R2-M7 / 任务03：空间统计口径说明

## 数据与抽取
- 原始文件：`data/04-24.csv`（ERA5 hourly single levels，tp 以 m 计；MD5 `f788445e030ab7bcd4617d97aff52656`）。
- 区域：52.75–53.75°N，6.75–5.75°W，0.25° 网格，5×5 = 25 个格点；2004-01-01 至 2021-12-31；只保留 00/06/12/18 UTC。
- 抽取逻辑与 `code/analysis_q03_spatial_averaging.py` 相同：坐标四舍五入到 0.01；同一（时刻，格点）取均值（本数据无重复记录）；tp × 1000 → mm。每个值是该时刻之前一小时的累计量，数值上等于 mm h⁻¹。
- 区域平均：每个时刻对 25 个格点**等权**平均。与 `dublin_regional_reduced.csv` 最大相差 1.0e-13 mm。

## 统一时间集合
- **所有统计都只用 18,404 个训练预测目标**：26,300 个时刻中第 6 至第 18,409 行，即 2004-01-02 12:00 至 2016-08-07 06:00 UTC。
- 这组时刻与 `prob_bilstm_attention_preds.csv` 中 split = train 的 `valid_time` 逐一相同；y_true 与区域平均最大相差 4.4e-7。
- **不使用** 18,410 个未构窗的原始训练时刻，**不混入** 验证期、测试期或 2004–2021 全期数据。
- 分位数采用 numpy 线性插值（与 pandas 默认相同，也与 notebook Step 14 一致）。湿小时定义为 y ≥ 0.1 mm h⁻¹。

## 输出文件
| 文件 | 内容 |
|---|---|
| `r2m7_series_stats.csv` | 26 条序列（区域平均 + 25 格）：经纬度、N、均值、湿频率、Q90/Q95/Q99/Q99.9、最大值及其出现时刻；Role 列标出离机场最近的格点 (53.50, −6.25) 和离市中心最近的格点 (53.25, −6.25) |
| `r2m7_pct_by_cell.csv` | 长表：每个统计量 × 每个格点，给出格点值、区域值、百分比差、区域值是否低于该格点 |
| `r2m7_summary_comparison.csv` | 每个统计量的区域值；25 格的最小值、中位数、最大值；区域相对格点中位数的百分比；25 个逐格百分比的最小值和最大值（`Pct_min_over_25_cells` / `Pct_max_over_25_cells`）；区域值低于多少个格点；两个代表格点的值与百分比 |
| `r2m7_run_manifest.json` | 输入 MD5、运行环境、时间集合、检查结果、输出 MD5 |
| `r2m7_run_log.txt` | 正式运行日志 |
| `r2m7_crosscheck_log.txt` | 交叉核对：与审计复算对照，原 q03 脚本重跑，与原 `q03_cell_stats.csv` 对照 |
| `r2m7_q03_rerun_log.txt` | 原 q03 脚本（未修改）在 scratch 目录重跑的日志 |

## 百分比
所有百分比统一为 `(regional_value − cell_value) / cell_value × 100%`，**比较基准始终是同一统计量、同一组 18,404 个时刻上的单格点值**。"相对中位数"的基准是 25 个格点该统计量的中位数。负值表示区域平均更低。

## 与原 q03 文件的关系
原 q03 脚本和 CSV 均未修改。`q03_cell_stats.csv` 不能作为最终补充表，原因有两点：
1. Q90/Q95/Q99 用的是 18,410 个原始时刻；`Max_mm`、`Frac_ge_1.0mm` 和 Spearman 用的是 2004–2021 全期；
2. 没有逐格的 Q99.9。

本目录的 CSV 取代它，作为 R2-M7 补充表的数据来源。

## 重新生成
```
python3 results/r2m7_evidence/r2m7_spatial_quantiles.py <04-24.csv> <dublin_regional_reduced.csv> <prob_bilstm_attention_preds.csv> results/r2m7_evidence
```
运行环境：Python 3.9.6，numpy 2.0.2，pandas 2.3.3；本地 Mac，2026-11-14。不需要 GPU，也不需要 scipy。
