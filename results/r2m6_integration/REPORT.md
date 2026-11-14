# R2-M6正式整合最终核验报告

本版科学/数值/文档/PDF核验通过；必要Git归档远程回读成功后才正式关闭，以STATUS.md及回执为准。只处理R2-M6，不开始R2-M7。

## 审稿原文与逐项完成状态

> The Gaussian assumption produces negative prediction bounds and severe undercoverage for heavy rainfall. Please evaluate a precipitation-appropriate distribution or provide stronger justification for the chosen formulation.

原文与comment.txt、原始Word第48段一致，已纠正任务11中的upper-tail误引；Response原审稿文字保持。

1. 负下界：已回应。Tobit为零删失正态而非截断重归一化；BG为零质量+正Gamma。非负支持在构造上消除负分位界，不把它误称校准已经解决。
2. 上尾欠覆盖：已回应。q11 BG Cov95 Upper=.6445，Gaussian=.4941，Tobit=.5454，仍远低于.95。总体改善与高阈值改善幅度小、条件诊断不利并列呈现。
3. 降水适用对照：已完成。§3.3.3给分布/NLL/参数稳定化/分位数/超越概率/预测均值。相同Prob. BiLSTM-Attention主体、输入、划分、五种子和预算；输出层、损失及标准化/物理目标尺度共同改变，不作仅换分布的严格单因素声称。NLL不跨参考测度和尺度比较。
4. 评分与区间：§3.4明确CRPS/twCRPS/IS95/Brier/Cov90/95/Widths/负界比例；全3939目标评分，wet原代码>.1与本样本>=.1同854事件。Q95来自训练期。full为有限支持的CDF数值积分，不是闭式；199分位不进入正式主表B。闭式仅独立核验，原full匹配区间不替换。
5. 统计透明：非循环moving28/5000/42，五seed逐样本评分先均值再配对抽样；141完整块=3948，非长度n。pointwise未多重校正；seed-t与test bootstrap分列。既有同索引截断诊断对4个full配对的跨零判断不变，最大端点变化1.46855e-5；这不证明其他指标无影响。透明保留原实现/区间，本轮不重算或修正主分析。
6. dry选择：披露数值零容差1e-6、无可核实预先指定记录、seed42探索先于其余seed、dry0非最优验证/测试CRPS。dry.001五种子，dry.01仅1种子；Tobit敏感、BG相对较小。缺失Tobit(.001) full block区间明确未保存，不挪用。

## 最终主表结构与位置

**现实际为Table5，label仍tab:probabilistic_results，第60页。** Table4早已是R1-M2强基线；未手动重编号或改变该已关闭表。指令历史“Table4A/B”对应当前Table5分部：

- A1：原Gaussian三模型五种子NLL、CRPS、Cov95原tabular/18个数值标量逐字保护，未重算。
- A2：另列q16的q14 W6 Gaussian五种子interval reruns（Cov90/Width90/Width95），来源与A1明确区分；不替换A1、不与q11合并统计。
- B：三种q11 likelihood reruns，Full CRPS、IS95、Cov95 All/Wet/Upper、Cov90、Width95、Width90、negative95。列为三种分布，行是指标，原生排版未resize。twCRPS及配对区间放S40/S42，保留包括BG与Tobit高阈值不稳定的全部结果。

## 新增Supplementary（自动S39–S46）

S39 q16区间参考；S40 三分布逐seed full/tw/IS/Brier；S41 逐seed覆盖率/95及90宽度/负界；S42 全部保存的full/tw配对seed-t与block区间；S43 全部保存的All非CRPS主要概率指标配对；S44 dry.001十个运行；S45 dry.01等seed42历史选择；S46 条件CRPS不利历史诊断。完整label映射见LOCATIONS/EVIDENCE_INDEX。

S45/S46特意保留199分位历史诊断身份，不是正式full分布评分；S46只用于呈现按观测筛选后BG更差的负面诊断，不能用于proper总体排名。没有把不存在的dry.01五种子或Tobit(.001) full CI填入表格。

## 数值、来源与保护检查

- 685个新增数值转录条目逐项回到固定CSV/已归档摘要核验；94行补充表独立核对目标列，主表B27项和A2九项指标独立匹配。
- full三分布四位均值.0961/.0847/.0773；max闭式验证均值差4.31615e-5来自原积分离散误差，未替换原full或其CI。
- BG/Gaussian：Full CRPS约降19.6%，IS95约29%，Width95约32%，总体Cov95相近而非统计等效性证明。twQ95/tw1.0仅约2.8%/1.9%。BG vs Tobit full双区间排零、高阈值block跨零。负面条件诊断保留。所有数值来自CSV，不从用户舍入表直接抄入。
- Width90均值分别.670460/.449480/.406727（mm/h），逐seed来自保存q05/q95，与95宽度区分；不把q11 Gaussian映射为A1/q16运行。
- 全部92段摘录匹配，原82保持、新10逐字；Response红、位置/摘录蓝。旧主表除概率表外、所有Figure环境及S1–S38源完全一致，R2-M5 S32–S38未改。其他Reviewer回复逐字保持。
- 4条原始参考元数据/DOI经出版商来源核验，仅追加Bib条目，未清理历史重复项。没有新Figure、模型训练或原预测/实验输出改动。

## 编译与100%版面

按Supplementary→manuscript→Response letter完成。最终49/92/66页；无阻断、缺图、未定义/重复引用、Overfull hbox或过大float。manuscript保留已有模板1.41457pt overfull vbox及字体/bookmark类警告；未改变模板规避。

新表页42–49、主表60、方法22–23/31–32、结果63–64、Discussion75、Limitations77–78、Abstract2、Conclusion82及Response40–43以72dpi（100%物理尺寸）渲染检查，完整、无裁剪/重叠，正常字号清楚。主表与首次引用相邻，未漂到文末。红蓝及外部表引用检查通过。最终全稿页码行号仍待统一。

## 科学边界与剩余共享任务

单网络/原测试期、训练尺度不同、探索性dry、缺失敏感性区间、3,948项非循环块和未校正pointwise区间均已披露。BG没有12年rolling证据；不得外推至其他模型、年份或宣称欠覆盖消失。现有必要证据足以完成R2-M6透明报告，无新阻断项；缺失敏感性CI是披露边界而非被伪造补齐。

任务11仅R2-M6范围待Git核验后关闭。任务05/06/12/16/30及R3/R4等共享未完成部分保持；R2-M7未开始。

## Git范围

原论文工作区仍有其他未提交修订，未pull/reset。独立工作区基于origin/main；只提交本轮增量patch、数值溯源/验证/报告及限定任务状态，不整份提交LaTeX、Bib历史或任务历史，不重复上传原预测、大型数据或图片。不强推、不改历史。patch以前置本地完整修订稿为基准，哈希见DOCUMENT_HASHES，不应盲目用于旧远程LaTeX。
