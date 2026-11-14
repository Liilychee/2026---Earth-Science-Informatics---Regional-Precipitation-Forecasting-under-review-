# 下一阶段正式制表应使用的统一来源（本轮不制作LaTeX）

| 用途 | 数据文件及字段 | 限制 |
|---|---|---|
| 拟议Table 4B和Supplementary完整CRPS | 固定d02519c: results/metrics/q11_twcrps_per_seed.csv 的full | 五个seed的均值/SD；不是q11_summary的crps_all（后者199分位） |
| full配对差异/区间 | results/metrics/q11_twcrps_paired.csv 的threshold=full | 同一full积分评分；保留seed_t_low/high及boot_low/high分别报告 |
| twCRPS | 上述per_seed的r0.1/rQ95/r1.0及paired匹配threshold | 全3939样本，不能当作观测条件子集平均 |
| q11的90%宽度和覆盖率 | 本轮width90_per_seed.csv和width90_summary.csv | q05/q95不改动；五种子sample SD，不能用95%宽度代替 |
| q11其他概率指标 | results/metrics/q11_per_seed.csv、q11_summary.csv的非CRPS字段 | 90%覆盖率已独立验证；保留q11重跑Gaussian标签 |
| 原研究Table 4A概率区间 | 既有q16_interval_per_run.csv、q16_interval_summary.csv及q16脚本 | source=q14_rerun_5seed和saved_single_run分开，使用已有匹配方案，不把q11重跑Gaussian覆盖为原研究结果 |
| dry.001的full配对 | q11_twcrps_paired仅BG(.001)减BG | Tobit(.001)有full逐seed值，但没有保存的匹配full区间；不得借用199分位区间 |
| dry定义选择历史 | 本轮dry_seed42_sensitivity.csv与原run JSON | 明确199分位历史评分，不混入正式full；dry.01 nseed=1 |
| 闭式独立核验 | 本轮closed_crps_per_seed.csv、summary及formula checks | 仅验证，不替换原full CSV或匹配区间 |

目前正文Table编号已因前轮整合变化；“Table 4A/4B”是本条的逻辑表块名称，不预占实际最终表号。后续正式整合须依真实label与自动编号安排。R2-M6本轮不关闭。
