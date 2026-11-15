# R2-M8本地正式整合与最终核验报告

日期：2026-11-15。范围：Reviewer 2 Major Comment 8，任务10及17中的R2-M8部分。

**结论：本地整合及必要科学、数值、摘录、引用、颜色与PDF核验通过；待作者审核及另行授权的选择性Git归档，不正式关闭R2-M8。** 未开始R2-M9，未关闭R2-m4、R4-m29或R4-m34。

## 修改范围

根目录只改三份文件，详LOCATIONS.json及R2M8_LOCAL.patch：

| 文件 | 本地源码位置 | 本轮修改 |
|---|---:|---|
| Response letter.tex | 856起；正式Response自862行 | 仅R2-M8：原审稿意见不变，补AuthorResponse、自动引用的位置说明和6段逐字EvidenceBox |
| ESI_审稿意见分类_严重程度排序_35项.md | 1990、3376行 | 任务10、17各追加一段R2-M8限定说明，保留全部历史内容及其他意见Pending状态 |
| FINAL_REVISION_CHECKLIST.md | 484行起 | 追加本轮本地通过、待审核归档记录，不关闭共享任务 |

manuscript.tex **完全不改**，无需追加可选句子：§3.5、4.5、4.6、5.3已有完整方法、负面结果及S19引用，回复直接报告Wet/Upper的保存排名系数即可。Supplementary.tex、Supplementary注册表、Table 5、S1–S47、全部原Figure和文献库均不改。没有新实验、表、图或训练；没有重算SHAP、重新生成预测或Bootstrap区间。

本轮在results/r2m8_integration/保存源代码/CSV字节副本、索引、检查脚本、报告、编译日志及回复页渲染。before/是仅供核验的本地快照，不代表后续允许整份暂存文档。LOCAL与PORTABLE两个patch的hunk内容相同，后者仅增加文件名后的制表分隔时间戳，使BSD patch正确识别含空格的Response letter.tex。已在临时副本验证两者代表的增量准确重建三份审阅后文件。

## 审稿原文与逐项回应

原文与comment.txt一致，ReviewerComment保留“8.”后无空格：

> 8.SHAP and feature ablation are applied to different model architectures, limiting direct comparison. Please use a consistent architecture and assess the stability of feature importance across runs.

| 核心要求 | 已有证据及本轮回复 |
|---|---|
| 统一SHAP/消融架构 | 两架构分别在内部匹配，SHAP解释同五个完整模型，消融与同种子控制配对；不把一个架构的SHAP与另一个的消融拼接 |
| 一致消融条件 | 每架构5 full+35 single+10 group，合计100次已保存运行；固定42/123/7/2024/99，七变量及两降水组，同划分/预处理/架构内训练设置 |
| 跨运行稳定性 | 五种子SD、seed-t、方向计数、配对移动块与SHAP日历日Bootstrap、分子集Kendall τ；保留BU较弱稳定性和负效应，不凭bootstrap单独称稳健 |
| 方法含义及不一致 | 七变量玩家、完整128联盟、固定训练背景；SHAP为模型归因、消融为匹配重训的增量预测效用；上尾排序弱一致为描述性差异，不是计算错误或因果结论 |

现有正式自动编号为正文**Figure 7**（fig:r1m4_shap_comparison）、**Figure 8**（fig:r1m4_ablation_comparison）。补充证据是**S12–S22**（stab:r1m4_*），并非历史计划的S14–S17或Fig.S6。Response用manuscript-/supp-前缀真实label引用；EvidenceBox标题中的章节也用ref自动生成，不手写图表编号。

## 证据固定版本与核验深度

固定科学提交：`6495abc81101074b02b3a5c8cfc83cd6cbc33d79`。已证明其为R2-M7正式关闭提交`71eac69e0c37c5330a2310e074e5cb45bf783db0`的祖先。SOURCE_INDEX记录14份原始代码/CSV的完整路径、MD5和Git blob；source/副本与git show固定提交原字节一致。没有假称本轮另做GitHub逐文件远程回读或重新运行原训练/解释过程。

六份脚本MD5：

| 脚本 | MD5 |
|---|---|
| q10_train.py | a9a7c4ffa10303e11e835655c5a2ac5b |
| q10_prepare_data.py | 2a415cd4c18404af82bd9abb59750ba5 |
| q10_ablation_stats.py | e5d9d092e1c4a41261fd957076b856fa |
| q10_group_stats.py | 22a8e22896a66842cb0a035fc29ed139 |
| q10_shap.py | df0e501f84f7294a73303e01d8840712 |
| q10_shap_stats.py | 3da365ab160e9fd4a061f8ed0f519d86 |

100个run JSON已逐一读取：2架构×10配置×5种子齐全，删除/保留的特征通道正确；完整模型removed=null、缩减模型removed为逗号分隔字符串，按实际格式规范化验证，而非假设均为列表。RUN_METADATA_INDEX记录每份文件MD5及架构/配置/种子/训练epoch。相同划分和训练设置另由q10_train中的共享构窗数组、统一run_one及build分支直接核查。没有声称当前重新训练或恢复模型权重。

本轮不重复R1-M4已经充分完成的1,335单元格审计。R1M4_SOURCE_PROTECTION确认其**19/19**原始补充来源文件SHA256不变；本轮所引用的值单独回查固定CSV。

## 数值及统计口径

- CELL_INDEX：**32个CSV字段**（回复及新增摘录31项，任务10的lsp精度澄清1项），记录源文件、CSV实际行、筛选条件、字段、原始值及显示精度。
- METHOD_INDEX：**20个代码/运行清单条目**，覆盖种子、背景、联盟分析单位、阈值和重抽样配置等；100次运行的构成单独有清单。
- SOURCE_CHECK：配对方向与两类区间的判读、tcc/sp种子排序、训练epoch上限等只读核验；未重新估计正式性能指标、Kendall或SHAP。

关键保存值：

| 稳定性指标（种子间平均Kendall τ） | BiLSTM-Attention | BU-LSTM-Attention |
|---|---:|---:|
| SHAP random | 0.733 | 0.733 |
| SHAP upper | 0.924 | 0.752 |
| Ablation all | 0.867 | 0.543 |
| Ablation revised wet | 0.486 | 0.238 |
| Ablation upper | 0.562 | 0.238 |

两架构之间的SHAP排序系数在两个子集均为0.810；上尾SHAP与消融仅0.048。随机SHAP/全测试消融用不同样本，不作同样本检验。这些τ均为描述性结果，无新增显著性或多重比较校正声明。

Bi整体移除sp/tcc/v10的ΔRMSE为+0.004022/+0.002664/+0.002481 mm h⁻¹，均5/5同向，seed-t和Bootstrap区间均在零以上。BU的sp/tcc仅4/5，seed-t跨零但Bootstrap不跨零，不并列称同样稳健；也保留BU v10为5/5且双区间支持、mntpr整体负效应双区间低于零的事实。

Bi降水组三变量整体移除ΔRMSE为+0.004805，上尾+0.019359，均5/5为正；新增摘录中的配套Bootstrap端点也逐项匹配原CSV。只解释为当前模型中的预测信息重叠，不据此推断物理互换性或因果作用。

Task10原“所有降水单变量变化在±0.0005内”已以专属追加注释澄清：lsp实际−0.000511。Task17原CV2%–30%已用归档sd_seeds/mean_abs_phi的只读算术核对，实际约2%–37%（精确比值范围0.0249958–0.3689761）；这是任务记录精度修正，未重新估计SHAP。

## 已关闭材料保护

BASELINE_INDEX确认R2-M7 after与本轮before六份文档SHA256全部一致；R2-M7状态按正式71eac69 CLOSED处理。作者本轮提供Claude完整报告中的“未归档”及整合责任待定是过时流程前提，本轮指令已解决。核对说明见CLAUDE_AUDIT_RECONCILIATION。

check_integration.py通过：

- **97段旧RevisedExcerpt全部保持**；6段新摘录逐字来自现有正文，合计**103段**均匹配。
- R1-M4原**8个EvidenceBox**和整个R1-M4回复区块逐字不变。
- R2-M8以外整份Response前后字节一致，包括已关闭R2-M7及未开始R2-M9。
- manuscript及Supplementary文件字节不变，故Table5完整结构、S1–S47及所有旧图环境/路径/label不变。
- **111个保护文件**哈希不变，包含全部Figure、文献库、R1-M4旧核验记录及R2-M7全部关闭材料。
- 任务文件差异仅为任务10、17两个专属追加说明，检查清单仅追加R2-M8记录，注册表不改；R2-m4/R4-m29/R4-m34保持Pending，未关闭任务10/17整体。

## 三PDF编译及版面检查

按Supplementary→manuscript→Response letter执行latexmk -g -pdf，三个均成功。PDF_CHECK逐份核对当前源码MD5与成功fdb_latexmk构建记录一致。

| PDF | 页数 | 核验 |
|---|---:|---|
| Supplementary | 51 | 源码不变，成功重编译；S1–S47及现有图引用保持 |
| manuscript | 94 | 源码不变，成功重编译；Figure7/8与章节编号保持 |
| Response letter | 70 | 新R2-M8在45–48页，144 dpi逐页渲染、实际检查 |

回复45–48页已实际查看：原文“8.”格式正确，Response红色，位置说明及6个摘录框蓝色；自动引用显示Fig.7/8、S12–S22及§3.5/3.5.3/4.5/4.6/5.3；无裁切、重叠或字体不可读问题。未改动图片内部文字颜色。

三个最终日志均无undefined reference、duplicate label、Overfull hbox、float too large或阻断错误。manuscript原模板字体/bookmark及重复1.41457pt vbox警告保留；与R2-M7基线相比**无新增警告**。本轮未修改的新图表不重复重绘或全量矢量核验。

## 限制及未解决事项

没有发现必须中止本轮整合的科学矛盾。以下已知边界保留：

1. 背景固定；未进行替代背景敏感性。SHAP完整联盟枚举不消除背景与依赖结构假设。
2. 只有五种子，seed-t四自由度；训练、测试抽样及背景不确定性不能合并解释。所有区间pointwise，无多重比较校正。
3. q10非循环移动块实现保留141个完整块，共3,948个位置，未截断回3,939；本轮代码核对并在证据记录披露，未改变原区间，也未把它称为标准长度n重抽样。现有正文未声称截断，不需要为此改动已关闭R1-M4。
4. BU有9次缩减模型运行达到30 epoch预算上限；这不是本轮新实验，也不能据此确定其不稳定性的原因。
5. 当前Git证据缺模型权重和构窗缓存；没有重建缓存或重新推理，不能把现有统计核验等同从头复现。旧环境版本不可恢复，不声明新旧运行环境普遍等价。
6. Claude在审计中的额外tcc-sp差值CI和块长14/56检查未正式存档，本轮不将其作为新论文统计证据。回复仅报告已归档逐种子tcc/sp排序变化。
7. 正式全稿最终页码/行号仍统一待补。

## Git与完成状态

本轮**未add、commit、push或fetch**，未建立归档worktree或改写历史。当前主论文目录仍为原main旧检出ae4cd53，存在多项先前未提交/未跟踪内容；GIT_STATUS和GIT_SCOPE记录选择性归档边界。不得整份暂存混合返修LaTeX、Bib、任务文件或无关实验。

后续步骤：作者审核本报告、patch与回复PDF；得到明确授权后，按R2-M7方式在最新远端基础上独立worktree中归档仅本轮增量，并完成逐文件远程核验，方可正式关闭R2-M8。**当前状态LOCAL VERIFIED / NOT CLOSED；R2-M9未开始。**


## 作者授权后选择性Git归档及正式关闭（2026-11-15）

核查远端main仍为R2-M7最终71eac69e0c37c5330a2310e074e5cb45bf783db0，无新增提交或冲突。独立worktree中仅提交50个results/r2m8_integration下的patch/证据/检查记录/source副本及四张144dpi渲染，不整份提交或应用根目录LaTeX/任务文件。归档提交f29a5881b8d1b865124b197c1607d9946e81d201已正常推送；GitHub固定提交逐文件50/50 blob身份核验通过，PNG以base64回读。REMOTE_RECEIPT.json记录逐项预期及远端SHA。

关闭前再次运行现有scope/PDF核验：97段旧摘录、R1-M4八框、六新摘录、32CSV字段及111保护哈希保持；正文、Supplementary、Figure、Table5和S1–S47未变；当前源码仍与三份已检查PDF一致，无新增警告。仅本轮任务/检查清单的关闭注释通过CLOSURE_STATUS.patch归档，未覆盖原论文工作目录。此后状态和回执再独立提交/回读，STATUS.md为最新权威状态。**R2-M8本轮范围CLOSED；R2-m4、R4-m29、R4-m34保持Pending，未开始R2-M9。** 原报告中的LOCAL VERIFIED/尚待授权属于此前阶段记录。
