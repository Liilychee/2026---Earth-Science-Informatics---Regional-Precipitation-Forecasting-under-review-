# R2-m1本地正式整合与核验报告

日期：2026-11-15。范围：Reviewer 2 Minor Comment 1，任务28中的R2-m1部分。

**结论：本地整合与日期/样本数、全量摘录、交叉引用、三PDF及回复版面核验通过；等待作者审核及另行授权的选择性归档。本轮不提交、不推送，不标记正式CLOSED。** 未开始R2-m2。没有新增实验、表格、正文或图。

## 一、M9版本安全检查

开始修改回复信前已确认：

- M9科学归档：0530327235da8ebe251b85503a9fabdfcfb0e481；回执提交：209522ca9a91d576ca0cb83481986d0cf51c5605。
- 已有GitHub逐文件回读回执89/89全部通过。此次核对六项关键归档patch/索引文件，其固定Git对象与本地原字节一致；六份文档哈希匹配最后通过核验的M9 after状态。未把本次只读对象核对冒充新一轮GitHub远程回读。
- M9明确处于SCIENTIFIC_INTEGRATION_COMPLETE — FINAL_REPOSITORY_DOCUMENTATION_PENDING，不是整体CLOSED。
- M9待办仍是README、环境/复现说明、Code Availability最终固定commit、公开仓库内容审核；本轮不处理或改变这些状态。

因此可以独立补R2-m1，不需要等待最终仓库包装，也没有发生与M9未归档修改竞争的情况。M9_BASELINE_GATE保存检查结果。原M9报告/回执等历史记录全部受保护，未改写。

## 二、实际修改清单

根目录仅三份文件发生本轮增量：

1. Response letter.tex：仅`% Review ID: R2 m1`到`% Review ID: R2 m2`之间；审稿原文不变，将Pending替换为正式红色回复，补蓝色位置说明及三段逐字EvidenceBox。
2. 35项任务文件：仅任务28追加一段R2-m1本地核验说明。
3. FINAL_REVISION_CHECKLIST.md：仅追加本轮R2-m1记录。

manuscript.tex、Supplementary.tex、Supplementary注册表、文献库及所有Figures均字节不变；R2-m1以外回复全部字节不变。Table5、S1–S49及此前关闭意见保持。精确行号及稳定锚点见LOCATIONS.json。

ReviewerComment逐字保留：

> 1. Please report the exact training, validation, and testing periods and their respective sample sizes.

没有精简、合并、移动或改写任何正文段落，也没有为了答复本意见重新计算正式模型指标。

## 三、原始时刻、构窗和样本数核验

只读读取原保留区域序列：`/Users/yue/Interpretable-BU-LSTM-for-Rainfall-Prediction-in-Dublin/data/dublin_regional_2004_2021.csv`，使用其valid_time列，完整MD5与字节数在SOURCE_INDEX。该文件共26,300个唯一、单调、无缺口的六小时UTC时间戳。没有重下载数据、重聚合格点、重建特征或训练模型。

构窗依据固定6495abc81101074b02b3a5c8cfc83cd6cbc33d79中的q10_prepare_data.py及其已保存输出日志。代码先用int(n×0.70)/int(n×0.85)划分，再在各分区分别构窗，目标下标为窗口起点+6。输出日志给出(18404,6,7)/(3939,6,7)/(3939,6,7)。本轮没有执行该训练数据生成脚本，只核对原代码/日志并对时间列做轻量切片。

原始范围和目标范围均为UTC：

| 分区 | 原始时间范围 | 原始数 | 目标时间范围 | 目标数 |
|---|---|---:|---|---:|
| Training | 2004-01-01 00:00—2016-08-07 06:00 | 18,410 | 2004-01-02 12:00—2016-08-07 06:00 | 18,404 |
| Validation | 2016-08-07 12:00—2019-04-20 12:00 | 3,945 | 2016-08-09 00:00—2019-04-20 12:00 | 3,939 |
| Testing | 2019-04-20 18:00—2021-12-31 18:00 | 3,945 | 2019-04-22 06:00—2021-12-31 18:00 | 3,939 |

每段前六个时刻不能作为具有完整“本分区内输入”的目标，不是六个随机缺测。六快照输入跨30小时，最后输入到目标提前6小时，所以首个目标距该分区原始首时刻36小时；没有跨分区构窗。模型目标是提前量最后一小时的降水，不是六小时累计量。

另从d02519c5f153feb712018cf97efb035f6ca2d7ae中的q21 C0 seed42保存预测只读取split/valid_time，验证和测试全部目标时刻与上述切片逐项一致。该预测仅用于时间索引旁证，没有将其评分与原主表或M9统计混用。

DATE_CHECK/SPLIT_INDEX记录逐分区边界、计数、源行号及窗口时间关系；CELL_INDEX逐项记录12个日期时间和6个样本数，共18个显示字段。SOURCE_INDEX记录原区域序列、代码、日志及预测的路径、固定提交和MD5，原数据和预测没有复制到本轮交付或发布。

## 四、正文依据与EvidenceBox

三个摘录从当前正文直接按稳定文本锚点提取，不凭记忆改写，不依赖旧行号：

1. §3.2 `sec:dataset`：“The main 2004--2021 experiment contains...”前三句，提供raw/target计数、三个目标时间范围及目标时刻含义。
2. 同节“Feature screening used the absolute contemporaneous Spearman...”前两句，提供原始训练起止时刻与原始/构窗样本区别。
3. 同节“Thus, the latest precipitation input represents...”完整原句，提供输入/目标小时的区别。

新增摘录原始LaTeX字符串均直接存在于当前manuscript中，字面一致。既有**109段摘录（包括M9六段）全部逐字保留**；新增3段，合计112段匹配。全量内容检查沿用既定规则仅归一空白及颜色包裹，数字、单位、标点和数学/引用表达不改；三个新增摘录还单独通过原始字符串匹配。EXCERPT_INDEX保留修改前109个摘录的顺序与哈希。

回复明确区分本主实验70%/15%/15%和R2-M5的回顾性扩展窗口评估，后者引用真实`sec:rolling_origin_methods`标签，编译为§3.4.1。没有重写R2-M5、R1-M3或其他关闭意见正文。共594个保护文件哈希不变，包括正文/补充/旧图及M9、M8、M5历史证据包。

## 五、PDF和交叉引用

按Supplementary→manuscript→Response letter顺序编译三份PDF，均成功。PDF_CHECK核对当前源码MD5与成功构建记录一致。

| 文件 | 修改前页数 | 修改后页数 | 检查 |
|---|---:|---:|---|
| manuscript | 96 | 96 | 源码不变，重编译成功 |
| Supplementary | 56 | 56 | 源码不变，S1–S49保持 |
| Response letter | 73 | 74 | 新增内容在51–52页，144dpi逐页实际检查 |

回复两页实际检查：raw/target各三段清楚区分，日期与样本数完整，Response红色、位置与摘录蓝色，§3.2和§3.4.1引用正确；无裁切、重叠或文字不可读问题。R2-m2原Pending仍显示，未启动处理。

最终日志无未定义引用、重复label、Overfull hbox、Float too large、缺图或阻断错误。原模板字体/书签和1.41457pt vbox、轻微Underfull记录保留，不误称全局零警告。源码未变的正文/补充不额外重复进行全部旧图矢量审计。

## 六、状态和剩余事项

R2-m1本地回复及核验已通过，尚待作者审核和另行归档授权，不自动CLOSED。本轮没有Git add/commit/push/fetch、pull/reset或worktree修改。原主工作区仍有大量先前未提交/未跟踪返修，GIT_STATUS/GIT_SCOPE如实记录，不可整份暂存。LOCAL/PORTABLE两个patch具有相同hunk内容，后者只增加含空格文件名的分隔时间戳；已在临时副本验证准确重建三份修改文件。

R4-m23、R4-m27及R3相关共享意见仍Pending，任务28整体不关闭。M9的最终仓库文档与Code Availability发布仍Pending；本轮无README/环境/LICENSE或公开仓库整理。正式全文页码/行号仍待最终组装。**未发现本轮科学或版本冲突，未开始R2-m2。**


## 作者授权后的归档准备

作者已授权选择性归档与核验后正式关闭R2-m1。归档基线核实为最新origin/main209522ca9a91d576ca0cb83481986d0cf51c5605，包含M9安全科学归档；独立worktree只暂存本轮patch/核验文件，不覆盖原论文。先前“不提交”是本地审阅阶段的历史状态，本次明确授权另行生效。当前仅归档准备，不预先CLOSED；推送和逐文件回读后再更新最终状态。M9整体未关闭，其四项仓库待办及R4-m23/m27、R3共享事项保持。
