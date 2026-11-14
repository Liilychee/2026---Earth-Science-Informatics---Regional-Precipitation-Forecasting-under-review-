# R2-M2证据索引

|证据|原始路径|MD5|
|---|---|---|
| check_r2m2.txt | `/Users/yue/Interpretable-BU-LSTM-for-Rainfall-Prediction-in-Dublin/esi_github/results/metrics/check_r2m2.txt` | `9b1053fb2bbf43e50d235f56ce52140e` |
| check_r2m2b.py | `/Users/yue/Downloads/check_r2m2b.py` | `19a3fe358b0f9c887a9adba817169acb` |
| check_r2m2b_output.txt | `/Users/yue/Downloads/check_r2m2b_output.txt` | `216254035dfa7dc9137ac749e3d56535` |
| check_r2m2b_issue_time.csv | `/Users/yue/Downloads/check_r2m2b_issue_time.csv` | `0d10c8acdba59f0f962719cd1328db25` |
| q01_extreme_consistency_summary.csv | `/Users/yue/Interpretable-BU-LSTM-for-Rainfall-Prediction-in-Dublin/esi_github/results/metrics/q01_extreme_consistency_summary.csv` | `49297ede9f30840f3568519c691ac07c` |
| q09_selection_table.csv | `/Users/yue/Interpretable-BU-LSTM-for-Rainfall-Prediction-in-Dublin/esi_github/results/metrics/q09_selection_table.csv` | `1dfe2161ae5ca88adbb2fc913862f6f8` |
| Interpretable_analysis.ipynb | `/Users/yue/Interpretable-BU-LSTM-for-Rainfall-Prediction-in-Dublin/esi_github/code/Interpretable_analysis.ipynb` | `18d2f49b5f7399f9bf1dd3e53b308cf9` |

正式归档状态：已完成。详见[ARCHIVE_CLOSURE.md](ARCHIVE_CLOSURE.md)。上表CSV MD5指保留的本地原件，正式远程CSV MD5为`02ee42d7dac2c8a5eaa6732d554c46a7`。

脚本关键行：33–36配置，45–64训练climatology/起报，66–81模型索引检查，86–100组内SS，103–124全序列moving-block与种子平均差，135–146日志与输出。CSV关键行：2–5四时次，6–7 A/B汇总，9–10模型差异。

# R2-M2正式证据归档与关闭确认

日期：2026-11-14。状态：R2-M2完成并关闭；本记录替代此前CSV版本待确认的状态。

正式证据固定提交：`67dfa3e75d09c5a5b51c6ad7a739a7f731792ef6`。

|正式归档路径|正式远程MD5|保留本地原件MD5|
|---|---|---|
|`code/check_r2m2b.py`|`19a3fe358b0f9c887a9adba817169acb`|相同|
|`results/metrics/check_r2m2b_output.txt`|`216254035dfa7dc9137ac749e3d56535`|相同|
|`results/metrics/check_r2m2b_issue_time.csv`|`02ee42d7dac2c8a5eaa6732d554c46a7`|`0d10c8acdba59f0f962719cd1328db25`|

三份文件均已从固定Git对象核验。正式CSV采用该远程版本，不覆盖、不重新生成。本地原件保留在当前项目`results/metrics/check_r2m2b_issue_time.csv`及既有evidence副本中，本次不提交本地CSV。

两版CSV均为10行数据、15列；列名、行顺序、模型、种子、时间分组、文本与缺失值位置一致。34处差异全部为数值字段浮点末位差异，最大绝对差4.44e-16。两版在论文四位小数精度下完全一致，均支持已报告技能值、Bootstrap区间及3/5种子方向，不改变统计结论。

差异具体成因尚无法确定。不得将二者描述为逐字节一致，也不宣称已实现跨环境逐位复现。上述版本关系和统计等价范围已由用户确认接受；科学与PDF核验此前已经通过，本轮未重新计算、编译、训练或绘图，未修改三份LaTeX。

共享Task 02未整体关闭：R4-M2、R4-M3等后续工作及78%包络一致率来源未完全查清的备注继续保留。R2-M2关闭不代表这些任务完成。

同步范围仅限R2-M2记录；保留其他未提交论文修改。后续同步遵循有变更才提交、仅提交授权范围、不强制推送或改写历史的原则。
