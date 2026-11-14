# R2-M3证据索引

固定读取版本：`fb7e55ca89edb72779a3525c4dc0f72ab280228d`（包含q09/q21证据）。q09稳定性三文件首次归档于`66516cd97bb021a92e2e8e53a03eeb33ad3a9164`；q09/q21其余主要证据为`d02519c5f153feb712018cf97efb035f6ca2d7ae`。所有内容从Git固定对象读取；本地实验档案同名文件逐字节一致。

|路径|MD5|
|---|---|
|`code/q09_lead_corr.py`|`daf7b0987e7336da0f85dd8c1f8a00ae`|
|`code/q09_stability_check.py`|`1838913b33d6f0a377937c99a7819d52`|
|`code/q21_build_features.py`|`73a71e764f000e7b224b1e2947490001`|
|`code/q21_train.py`|`3e0fbf44821862514be54ecd0db7632a`|
|`code/q21_stats.py`|`558e20d8fad4fa150495fd4f3276c489`|
|`results/metrics/q09_selection_table.csv`|`1dfe2161ae5ca88adbb2fc913862f6f8`|
|`results/metrics/q09_output.txt`|`c0456ec554f55af03405d6bb6ee3e1bf`|
|`results/metrics/q09_stability_check.csv`|`13f9101368827f51b83d03987cdebda6`|
|`results/metrics/q09_stability_check_output.txt`|`3957acd6638ddf5962713061d12081d5`|
|`results/metrics/q09_lead_spearman.csv`|`8c9033ddf39c3500182ec9357384d744`|
|`results/metrics/q21_effect.csv`|`3b71b76b2997c6c386b4a05d34c12863`|
|`results/metrics/q21_runs.csv`|`88a3d1ea00849d6b419e6e7e7947f73a`|
|`results/metrics/q21_stats_output.txt`|`89b96656822849acfef368c5f23c0003`|
|`results/metrics/q21_summary.csv`|`69555a167ac6b8d6489bcc909106be9b`|
|`results/metrics/q21_build_output.txt`|`27fb28bf4a64ea4e3f82e325f8f29c66`|
|`results/metrics/q21_train_output.txt`|`ea6d5926dcc87ba42dfb59adadeea66d`|
|`results/metrics/q21_train_c3ab_output.txt`|`2ee8d45a9be54c4932f2f0c2a8534e4d`|
|`code/q06_train.py`|`fc5c0797007f3181edb6d2955a002b18`|
|`code/q06_common.py`|`fd11bd85160fe9118bc945a40feffa28`|
|`code/q10_train.py`|`a9a7c4ffa10303e11e835655c5a2ac5b`|

## 逐格与配对溯源

`cell_evidence_index.csv/json`记录374个转录数值的原文件、CSV行号（含表头）、字段、完整原值及显示值；同一原数用于多表时分别记录。`run_index_verification.json`记录50份运行JSON和对应预测CSV的路径、MD5、特征列表、样本量和环境元数据；不复制大型预测数据。`paired_direction_verification.json`对照保存的逐种子RMSE检查24组差值方向及均值精度，仅做轻量核验，不从预测重估指标，也不重抽样。

## 方法与边界

- q09_lead_corr.py：训练前18,410时刻；18,409配对；原始未截cp，偏相关是秩对tp(t)秩及截距回归后的残差相关；移动块28、2,000次、42，百分位pointwise区间。q09_stability_check.py复用相同随机抽样，11/13池分别重排，完整集合按无序集合相等计数；与q09原表频率交叉检查。
- q21_train.py第38–52行定义C0/C6及C3/C3a/C3b；72–88行匹配划分和训练期标准化；93–134行公共训练参数和运行元数据。q21_build_features.py第126行逐格cp截零，然后空间均值；原q09第63行不截零。
- q21_stats.py第33–40行设置、95–102行构造共同全测试序列moving blocks（28/5,000/42），逐种子重抽样RMSE差再平均；seed-t df=4；子集在抽到的全序列上应用。保存配对统计使用float32平方误差，不能用summary的高精度均值反推其末位。
- 子集All=3,939，Wet>=0.1为854，Upper tail>=保存训练Q95 0.574048为238；正文四位小数为0.5740。所有RMSE均为同一架构的q21控制，不替换Table 3。
- C3预设、C3a/C3b看过C3后追加的性质依据已归档脚本/日志；不声称独立预注册。两类区间均为pointwise，未控制多重比较。
- comment.txt第45行审稿原文与Response letter的R2-M3原文一致；本轮未改审稿文字。

## 共享边界

R2-M3完成仅覆盖本轮变量筛选问题。R3候选文献依据、季节性分析及R4变量实验/回复继续保留。R1与R2-M1/M2回复均保持原样；R2-M2正式CSV未改。
