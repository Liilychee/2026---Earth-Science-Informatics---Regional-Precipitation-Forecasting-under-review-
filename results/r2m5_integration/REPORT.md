# R2-M5整合与核验报告（2026-11-14）

科学、数值、正文/回复和PDF核验已通过。此版在独立Git归档及远程回读成功后方正式关闭；状态以STATUS.md和远程回执为准。未开始R2-M6或其他审稿意见。

## 审稿原文与逐项回答

> Insufficient Temporal Robustness Evaluation. Five random seeds are insufficient to demonstrate temporal generalization. Rolling-window or multi-year testing is recommended, and the block-bootstrap settings should be specified.

1. **五种子不足以刻画跨期泛化：已回应。** 明确seed SD仅描述固定划分训练波动；在新§3.4.1/§4.2.5与Supplementary S32–S38加入4个互不重叠三年测试期、F4prime历史对照、六模型五种子150运行。
2. **跨期检验：已回应但限于回顾性稳健性。** 30年资料、最长25年训练；F1/F2仅16/19年。逐折scaler/Q95/基线拟合；训练期同期筛选检核均得到相同7变量，但架构/超参复用、未逐折调参。原开发数据与滚动测试有重叠，包括原指令容易忽略的F4早2019。不能声称独立前瞻验证。
3. **Bootstrap配置：已完整区分。** 主比较单次保存预测circular28/10000/42，原长度截断末块；q06 moving非循环28/5000/42及56/120敏感性，完整末块、同索引跨模型/种子、先逐种子RMSE差再均值， pooled块可能跨42小时折间空档。全部pointwise百分位区间，未经多重比较校正；seed-t与sample bootstrap分列。

## 实际修改范围

- manuscript.tex：§3.2新增原始/构窗计数与精确UTC目标区间；§3.4补主研究Bootstrap；新增§3.4.1和§4.2.5；Abstract、§5.1、§5.4、Conclusion追加结论边界。
- Supplementary.tex：仅追加7张原生LaTeX表，自动S32–S38。5个设计行；36行全模型/基线表现；24行history；75行All配对；75行Wet配对；12行block sensitivity；45行conditional coverage。正常10pt主体、8pt现有caption样式，无resizebox；S34仅将本表tabcolsep调整为2pt，区间6位保留接近零端点符号。
- Response letter.tex：仅替换R2-M5占位，原审稿文字保持；新增10段逐字EvidenceBox。Response红，Evidence及位置蓝。
- 本地任务06/28、FINAL_REVISION_CHECKLIST及Supplementary登记表：仅追加R2-M5范围记录，保留R3/R2 Minor1/R4共享待办。
- 不修改原Table3/全部旧Figure和路径/旧S1–S31/其他Reviewer回复；未新增Figure、实验、正式指标或预测。

## 关键结论（由原始CSV回查）

- 全六模型逐期相对month×hour climatology SS=.077–.125；AR1=.031–.055，Persistence负SS。固定Q95下所有学习模型mean CSI仍低于Persistence；这是不同指标，不能相互替换。
- 数值最小RMSE为XGB(F1–F3)、BA(F4)，六模型Kendall tau=.60–.87。BA–XGB仅F1逐期All区间排零；不能判定总体最佳。
- pooled n=17508，BA–XGB=+.0020380；7天[+.00006877,+.00397572]，14天[−.00002515,+.00402272]跨零，30天[+.00006218,+.00403526]。文中保留正确近似精度，不以舍入制造显著性。
- Wet>=.1单独n3610，差+.0092582、7天区间[+.004782,+.013723]；不外推为All总体优势。
- 25y/13y均值RMSE约降.4–2.3%，上尾不作普遍改善声明。保留负面和区间分歧；BA history seed-t上端约−.000002，S34采用六位避免显示为−0.00000。
- 跨F1–F4 PICP95 All .953–.963，Wet .801–.828，Upper .473–.592；负下界和上尾欠覆盖未由滚动评价解决。

## 溯源及保护检查

214个固定Git小型源文件/记录逐字节和MD5匹配；150运行的配置、种子和n通过；150预测CSV的时刻与保存目标一致性通过（F4/F4prime仅目标浮点逆变换微差，见证据索引）。1,541个转录数值回查通过，267个统计行目标列位置验证通过，5个设计行依据fold JSON。

全部82段摘录通过匹配（原72保留，新增10逐字；仅允许颜色标记/空白差异）。主表3、全部既有figure/table环境逐字不变；Supplementary原S1–S31源不变；所有R2-M5以外的回复源不变。检查脚本、VERIFICATION、ROW_INDEX、SOURCE_INDEX及文档前后SHA256共同记录上述结果。

## PDF与版面

Supplementary → manuscript → Response letter顺序编译完成：41 / 86 / 63页。无阻断错误、未定义/重复引用、Overfull hbox或超大浮动。manuscript保留模板已有的1.41457pt Overfull vbox及字体/bookmark类警告，未通过改字体或改旧内容规避。

新增表页31–41逐页以72dpi（100%物理尺寸）渲染检查，完整、无裁剪/列碰撞；正文方法/结果/局限和回复37–40页亦检查。红蓝颜色与外部S32–S38引用颜色通过。主研究Abstract仍按模板跨页延续，未扩大模板字号修改范围。PDF哈希和实际label/page见PDF_CHECK、LOCATIONS；最终全稿页码行号尚未填入回复位置说明。

## 尚存科学限制（已披露，非本条未完成任务）

回顾性设计/开发重叠、未折内调参、早期不足20年、块长敏感和跨折空档；无ENSO分层、滚动plain-BiLSTM或Bernoulli–Gamma。上尾检测和覆盖仍不足。这些限制不允许将q06写成业务前瞻验证或宣称某模型持续最佳。R2-M6及共享任务由后续独立处理。

## Git范围

当前论文工作区旧main并有其他未提交修订，未pull/reset或整份暂存。独立工作区基于origin/main（父提交e3cdca6）；仅归档本轮增量patch、可追溯证据索引、核验报告与限定任务状态。历史原始证据、CSV、预测包、LaTeX整文件和大型数据均不覆盖、不重新提交。不强推、不改历史。patch以本地整合前快照为基准，SHA256见DOCUMENT_HASHES，不应盲目对旧origin LaTeX应用。
