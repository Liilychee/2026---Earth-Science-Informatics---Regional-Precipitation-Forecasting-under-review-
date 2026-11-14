# 数值溯源索引

固定科学输入Git提交：`d02519c5f153feb712018cf97efb035f6ca2d7ae`。SOURCE_INDEX.json包含全部72个源路径、MD5、SHA256及大小。脚本只读这些固定Git对象；不依赖AutoDL或可变本地CSV。

| Git路径 | MD5 |
|---|---|
| `code/q11_stats.py` | `5ad200a4a78ed2a1ada1b59ea4305ca7` |
| `code/q11_train.py` | `e59bff8daba12117db1ce73da1b0d737` |
| `code/q11_twcrps.py` | `a88c6a5a59bae87ea3de4cb2e0e1d707` |
| `results/metrics/q11_summary.csv` | `0448a9536a3c87edc0ab4e4c5c6f757e` |
| `results/metrics/q11_twcrps_paired.csv` | `92942f1e0a3d1e87c54d5aea691fbdc7` |
| `results/metrics/q11_twcrps_per_seed.csv` | `3f39755dbe60f8506347c62eb8c977cb` |
| `results/metrics/q16_interval_summary.csv` | `c7377d7eca9d675bb9d660e93f7e7a25` |

- 闭式逐seed与full原行：closed_crps_per_seed.csv按config+seed对应q11_twcrps_per_seed.csv；原字段保留，不改源文件。
- paired_full_verification.csv按a+b+threshold对应paired源；archived/reproduced/closed/diagnostic各列明确区分。
- width90逐seed原参数：SOURCE_INDEX中的results/q11/preds/<config>__s<seed>.csv，split=test,q05/q95/y_true；picp90原比较为q11_per_seed.csv的config+seed。
- dry CSV原JSON精确path与MD5逐行列出，路径val/dry0/crps_all及test/dry0/crps_all；这两个字段为199分位历史评分。
- Claude历史脚本/输出复制原件，方法审计见CLAUDE_SCRIPT_AUDIT；本轮新脚本为正式核验入口。
- 本目录新证据文件MD5见MD5SUMS.txt及ARCHIVE_MANIFEST.json；原论文及任务文件保护哈希见PROTECTED_HASHES。
