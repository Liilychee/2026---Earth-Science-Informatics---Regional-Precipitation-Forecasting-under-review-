# R2-M9恢复后的本地整合与核验报告

日期：2026-11-15。范围：Reviewer 2 Major Comment 9，任务18/19/34中的R2-M9部分。

**当前结论：M9科学与论文整合及本地核验通过；Code Availability最终公开链接确认、发布范围、复现文档及最终发布commit仍为明确TODO，因此不关闭R2-M9。** 本轮不提交、不推送、不训练；未开始R2-m1。R3-L822–824及任务18/34共享事项保持Pending。

## 一、中断状态及恢复范围

恢复首先只读检查，已向作者列出实际状态：

- 已完成：q19固定证据核验、117运行与117预测索引、6选择JSON、53行效应、计时汇总及epoch-cap核对。
- 未完成：六份论文/任务文档当时均与M9开始前快照完全一致，M9正文未写、回复仍Pending、S48/S49不存在；本轮报告、patch、CELL_INDEX和M9编译/PDF核验记录尚未生成。
- 已有JSON均可完整解析，无部分写入迹象。系统拒绝ps进程查询，因此没有声称已排除所有后台进程；已有工具返回记录中无未完成命令迹象。
- 中断前留下repository_draft/及临时目录中的README等本地草稿，但未发布。依作者后来要求，本次不更新、不继续准备、不把它们用于已完成复现材料的证明，也不纳入本轮交付/后续科学归档范围。

没有重跑先前整合脚本或已完成的117预测/53效应核验。只补原本不存在的正文、两张表、回复、任务记录及本地核验。RESUME_STATE.json保留该恢复检查点。全部改动以本轮原before快照作基线，避免混入更早返修。

## 二、实际修改文件及位置

| 文件 | 本地源码行 | 本轮内容 |
|---|---:|---|
| manuscript.tex | 391、393 | §3.4新增红色验证搜索、预算、A/B/C、配对区间及三重改善规则 |
| manuscript.tex | 718、720 | §4.2 Table3之后新增q19结果、运行集合边界及计时范围 |
| manuscript.tex | 1143 | Discussion补充epoch cap、选参不确定性及未调参无注意力控制 |
| manuscript.tex | 1208 | §5.4新增回顾性、预算不对称、单划分及pointwise边界 |
| manuscript.tex | 1310 | 替换原未被摘录引用的旧Code Availability链接，改为拟议完整URL与醒目TODO，不宣称完成发布 |
| Supplementary.tex | 1804起；S49始于1904 | 仅追加S48和S49；原S1–S47不改 |
| Response letter.tex | 902起；回复自912 | 仅R2-M9正式AuthorResponse、位置说明、6段逐字摘录 |
| 35项任务文件 | 任务18/19/34各一段 | 追加M9限定记录，覆盖历史“尚无运行结果”等过时状态，保留共享Pending |
| FINAL_REVISION_CHECKLIST.md | 496起 | 科学整合通过/代码发布Pending/未关闭记录 |
| SUPPLEMENTARY_TABLE_REGISTRY.md | 97起 | 真实自动编号、label及页码 |

完整行号见LOCATIONS.json。这些是本地核查位置，不是最终回信中的审稿页码/行号；最终全稿位置仍待统一补齐。

除新增段落外，旧正文只改未被任何旧摘录引用的Code Availability段。核验脚本移除新红色块并恢复旧Code Availability后，manuscript与before全文精确一致。原Table3、Table5及所有既有主文图表环境逐字不变。

## 三、补充表实际编号、范围和数据

| 自动编号 | 稳定label | PDF页 | 内容 |
|---|---|---|---|
| S48 | stab:r2m9_search | 52–53 | 6模型成本、原/选择配置、搜索设计及66条完整候选验证排名 |
| S49 | stab:r2m9_effects | 54–56 | 53行原始A/B/C效应的均值/差/百分比/种子方向与两类区间/三重改善判断 |

66候选=2×27完整网格+4×3轻量学习率候选。S49的53行各分估计和区间两个逻辑面板展示，共106个目的行，不是106个独立比较。全表原生longtable、沿用既有字体/红色修订环境，不使用resizebox或表格图片、不重置table计数器。跨页重复表头；S49的E/I行前缀明确区分估计与区间列。正文和回复都用真实label/ref。

S49只列档案实际存在的比较。XGBoost的A=B，Probabilistic BiLSTM-Attention的B=C；不存在的C−B不补造。0个改善种子可能表示平局，不能把0/5自动写成5/5恶化。95%区间是pointwise，不是多重比较校正。三重“改善”列要求5/5下降、seed-t和block两区间均全在零以下，不把档案medium标签当作稳健。

## 四、科学证据及数值溯源

固定证据完整SHA：**d02519c5f153feb712018cf97efb035f6ca2d7ae**。

SOURCE_INDEX含19份固定代码/CSV/日志/选择及环境来源的路径、完整MD5、Git blob。q19_tune.py MD5为7fa8fb3283aca5dcb687c43af8cfc5c7；q19_stats.py为1664664b471c3f5464a50b5a80a79074。中断前已通过GitHub读取该固定提交与关键源文件；本次未重新下载数据或改写档案。

已完成证据：117运行JSON与117预测一一对应；模型数为XGB39、BiAttn38、Trf/BU/BUAttn各11、ProbBi7。六个选择都能仅依验证记录恢复；gate通过，search/recheck/final/light均有完成标记。预测共用3,939测试目标，A参考q21/q14索引与目标核对见A_REFERENCE_INDEX。没有声称本次重新训练、重算所有性能指标、重新做Bootstrap或SHAP。

数值索引：

- **CELL_INDEX：914个显示字段，其中828个数值、86个缺省标记。** 每项给出源CSV、行、列、原值、显示精度及目的位置。
- ROW_INDEX逐行核对两表的实际LaTeX目的文本，避免只靠数字全局出现就判通过。
- METHOD_INDEX：17项源代码设置/网格/控制索引；选择配置来自selection JSON和完整候选记录。
- CANDIDATE_TABLE为已核验候选排序的展示派生CSV，保留q19_all_runs原CSV行及run tag；不是新增训练结果。
- COST_SUMMARY由117份原JSON的train_seconds只读汇总；PROSE_DERIVATIONS明确记录保存评分差值、验证均值差及计时合计的输入字段。没有对预测重新评分。

关键结果全部保留：

1. q19内部六模型在All/Wet/Tail的A→C排序均未变；不是宣称与原Table3每个集合完全相同。
2. BiLSTM-Attention对XGBoost的整体差距，从保存均值差0.0010565336缩至0.0001606232 mm h⁻¹；正文六位小数显示**0.001057→0.000161**，与审计中的约0.00106→0.00016一致。
3. BiLSTM-Attention选择配置在测试整体略退化（+0.06%）；XGB上尾略退化（+0.26%，无种子改善），不隐藏不利结果。
4. Transformer B−A整体数值改善0.78%，C−B再改善0.59%，C−A总计1.37%；对应种子区间仍含零，不把数值改进称三重稳健。
5. 只有BU-LSTM-Attention全测试CRPS改善满足三重规则（1.73%降低）。S49出现两行Yes是C−B和C−A，因为其B=A，不能视为两个独立重复证据。
6. A是q21/q14等特定重跑集合。q19 A中BU-LSTM在BU-LSTM-Attention前，与原Table3二者次序不同；未改Table3。
7. 原固定参数的最初选取依据未独立确立，未虚构原系统搜索。两主模型候选数相同不等于计算量相同，其他模型预算更小；无注意力BiLSTM未参加q19调参。
8. BiLSTM两个最佳三种子验证均值只差0.0000529203 mm h⁻¹，正文约0.000053。只解释选参不确定性，不声称已证明由噪声主导或正式等效。

代码/日志边界：统计日志的BiLSTM“28组”混入cap30 gate；正式cap60网格仅27。已在表注与回复解释，原日志不改。曾有旧set_lr断言在训练前失败，后续归档light日志完成；117份JSON/预测均有完成对应，不把旧失败信息当作当前实验缺失。

## 五、计时

117份JSON累计记录**13,923.6秒=3.8676667小时**，正文3.87h。XGBoost原记录合计16.4秒；Claude审计“约15秒”为近似，本轮采用原始记录精度。BiLSTM-Attention合计4703.2秒（约1.31h）。每模型完整计时、单次中位数及epoch见S48/COST_SUMMARY。

计时器位于模型构造之前，止于拟合与验证/测试预测之后；随后的指标整理和文件写入在计时之外。该数不是纯fit、推理基准、端到端搜索墙钟或GPU小时；也不包括此前q21/q14 A参考训练。主机可见RTX5090不证明XGBoost用GPU，设备未知限制明确保留。未用q10计时替代q19，也没有推断原Table3全部训练成本。

## 六、摘录及已关闭材料保护

- **103段旧RevisedExcerpt全部保留**，新增6段与最终正文逐字一致，合计109段。
- R2-M9以外Response前后全文字节一致，所有原ReviewerComment不变；R2-m1以后保持Pending原文。
- Table3、完整Table5及所有原主文table/figure环境不变；S1–S47源代码逐字不变，仅end document之前追加两表。
- **149个保护文件SHA256不变**，覆盖Figures、文献库及R1-M4/R2-M7/R2-M8关闭材料。
- 任务18/19/34仅各追加R2-M9专属说明；检查清单及注册表仅追加，不关闭共享事项。
- 为使新的逐字摘录保留原manuscript中的tab:model_config和tab:seed_stability引用，R2-M9区块内局部引入对应外部标签别名；不手写编号、不影响其他回复。PDF显示正确Table2/3和S48/S49。

详细结果：VERIFICATION、EXCERPT_INDEX、PROTECTED_HASHES。

## 七、PDF编译和实际版面

按Supplementary→manuscript→Response letter顺序完成必要编译；只针对新表续页表头、链接断行和逐字摘录局部引用进行了必要修复，没有重做已通过的q19实验核验。

| PDF | 页数 | 实际查看的相关页 |
|---|---:|---|
| Supplementary | 56 | 52–56 |
| manuscript | 96 | 26–27、46–48、74–75、80–81、96 |
| Response letter | 73 | 48–51 |

19页均在72dpi原生比例实际渲染查看；144dpi副本另存，密集表页及回复页又做了放大可读性核对。新表完整、续页列含义清楚、无裁切/重叠；正文/表/caption/回复红色，位置与摘录蓝色，图片内部文字未变。

PDF_CHECK逐份确认当前源码MD5与成功构建记录一致。最终无undefined reference、重复label、Overfull hbox、过大float、缺图或阻断错误。初次新URL的39.3pt横向溢出已用局部URL断行修复；未全局改变文档排版。保留模板字号/书签和1.41457pt vbox警告。新Code Availability的URL段及其摘录仍有Underfull字距记录，但不溢出，实际页面检查通过；完整警告均已存档，未虚称零警告。

## 八、GitHub及Code Availability：明确未完成

依作者最新指令，GitHub整理延后到全部意见处理结束。稿件显示拟议完整ESI URL，并有醒目**CODE-AVAILABILITY TODO**：确认最终公开链接与发布范围、完成所需文档、填写最终release commit。回复也明确该项未完成，不宣称README/环境包或完整复现发布已具备。

固定d02519c仅是本轮科学源证据pin，绝非未来Code Availability最终发布commit。不能用占位声明或当前科学来源代替代码发布任务的完成证明。上述Todo本身是待办位置，不是已完成公开性的证据。

历史PUBLIC_REPOSITORY_CHECK/PUBLICATION_RISKS与本地repository_draft保持为中断前记录；本次没有继续README、环境文件或LICENSE整理，没有添加LICENSE，没有公开新数据/权重/私人材料，也没有修改GitHub。它们不纳入本轮完成事项。任务34及相关共享工作继续Pending。

## 九、交付、Git状态及剩余事项

交付主文件：FINAL_REPORT.md、R2M9_LOCAL.patch（及相同hunk的可移植版）、CELL_INDEX/ROW_INDEX/METHOD_INDEX、EVIDENCE_INDEX、PDF_CHECK、GIT_STATUS。DOCUMENT_HASHES及临时副本patch应用验证精确重建六份目标文档，未把旧main分支的其他返修混入本轮差异。

本轮仅本地修改，没有git add/commit/push/fetch或强制覆盖，也未为本轮建立Git worktree。原主工作区仍含大量先前未提交/未跟踪内容，GIT_STATUS如实记录；不得据此整份暂存。R3-L822–824、任务18与34共享事项Pending；未开始R2 Minor Comments。

剩余：作者审核本轮科学/论文内容；全文意见完成后统一完成代码公开范围、复现材料与最终commit/Code Availability；再另行决定选择性Git归档和正式关闭。**M9目前为本地科学与论文核验通过，未正式关闭。**


## 本地审阅通过后的授权状态（科学选择性归档，不关闭M9）

作者现授权科学与论文增量归档，明确不授权整体关闭。当前权威状态为`SCIENTIFIC_INTEGRATION_COMPLETE — FINAL_REPOSITORY_DOCUMENTATION_PENDING`。尚待事项：GitHub README、环境及复现说明、Code Availability最终固定commit、公开仓库内容审核。它们不因本次归档而完成，留待全部审稿意见处理结束后统一解决。

使用最新已核实origin/main2de6f3e独立worktree，仅归档R2-M9增量patch及核验材料，不整份提交混合返修的根目录文档，不包含历史README草稿，也不重新训练/绘图。后续实际提交与回读结果另写回执；原报告中“本轮不提交”属于此前本地整合阶段记录，不是本次明确归档授权后的状态。原已关闭意见及任务22历史必须完整保留。
