# R2-M7本地最终核验报告

核验日期：2026-11-14。范围：Reviewer 2 Major Comment 7 / 35项任务03中的R2-M7部分。**本地整合及科学、数值、摘录、引用、PDF核验通过；等待作者审查及后续授权的选择性Git归档，不正式关闭R2-M7。** 未开始R2-M8。

## 中断恢复与实际状态

只读检查确认`/private/tmp/r2m7_finish.py`此前已经完整运行：LOCATIONS.json、R2M7_LOCAL.patch、GIT_STATUS.txt、PROSE_FACT_INDEX.json及任务记录均存在。任务03的R2-M7权威更新、检查清单条目、注册表追加各只有一份。缺少的仅为FINAL_REPORT.md与PDF_CHECK.json。本次未重跑finish脚本，未重复追加记录，未再次修改三个LaTeX文件或作者图。仅补充本报告、PDF核验记录及可复用只读核验脚本check_pdf.py；重运行现有check_integration.py通过。

## 已完成修改与位置

| 文件 | 本地源码行 | 内容/当前PDF位置 |
|---|---:|---|
| manuscript.tex | 447 | Methods：同一18,404训练目标，先空间平均后取分位数，原尺度Q95、不作对数变换，单格点范围；PDF27–28页 |
| manuscript.tex | 824、826 | Results：分布不同位置的空间对比及补充表/图引用；PDF53页 |
| manuscript.tex | 1166 | Discussion：方向随分布位置变化，描述性差异非因果机制；PDF76页 |
| manuscript.tex | 1201 | Limitations：远端差异量化及区域小时目标不等同站点极端；PDF80页 |
| Supplementary.tex | 1747–1803 | 新增26行原生表及原生大小作者最终图；PDF50、51页 |
| Response letter.tex | 820起 | R2-M7完整回复及5段新增EvidenceBox；PDF44–45页 |
| 任务03、FINAL_REVISION_CHECKLIST.md、SUPPLEMENTARY_TABLE_REGISTRY.md | LOCATIONS及patch可查 | R2-M7本地核验状态、实际编号、待作者审核及归档；其他共享意见不关闭 |

精确位置见LOCATIONS.json；源码行仅供本地审查，正式页码/审稿行号仍待全稿定稿统一填写。修改patch为R2M7_LOCAL.patch，基于本轮before快照生成，不包含此前其他返修的差异。

## 自动编号及作者图

- Table **S47**，永久label：`stab:r2m7_spatial_quantiles`，Supplementary PDF第50页。
- Figure **S2**，永久label：`sfig:r2m7_spatial_quantiles`，Supplementary PDF第51页。
- 正文、回复使用现有外部引用前缀`supp-`；补充材料内部使用自身label，未手写固定编号或重置计数器。
- 作者图：`Figures/r2M7_spatial_quantiles.pdf`；311,767 bytes；单页矢量，无栅格图像。
- MD5：`0b59c59d8b25a4eeb725c552a12c26fb`；原生119×70 mm，`
\includegraphics{Figures/r2M7_spatial_quantiles.pdf}`不带缩放或裁剪参数。文件哈希未变；最终PDF内Form XObject边界核对原生尺寸。
- 125个灰色格点标记和5个黑色区域菱形共130个，逐标记与正式CSV归一化比值核对。最大绝对比值误差`1.100573608914246e-7`，小于`1e-5`容差；容差反映归档CSV六位小数及PDF坐标精度，不是重新估计数据。五个百分比标注均正确；每一统计量分别以25格对应统计量的中位数归一化。见FIGURE_POINT_CHECK.csv及FIGURE_METADATA.json。

## 正式证据与数值核验

正式固定提交：`dc850836b486e8f326ddcb432a3602fe8b8448b6`。五个原始证据文件已通过GitHub固定提交读取，逐文件Git blob SHA-1与本地字节计算结果一致；MD5及远程blob见SOURCE_INDEX.json。该提交未假称已存在当前本地Git对象库中。

| 文件（results/r2m7_evidence/） | MD5 |
|---|---|
| r2m7_series_stats.csv | 167750324c60c51d19150c4c13ba9dc8 |
| r2m7_summary_comparison.csv | 115852d177d2b46426bcb170d5262836 |
| r2m7_pct_by_cell.csv | b2b00e14dde9a0f7ad8c312260f9dc1e |
| README_METHODS.md | cd48dbfcb3e8b13a306dfd9d668a0b38 |
| r2m7_spatial_quantiles.py | c18dc37e7a83e9624ca46df02b3f48f2 |

- 所有26序列均为同一18,404个训练目标时刻：2004-01-02 12:00至2016-08-07 06:00 UTC。未混入18,410个原始训练时刻、测试时期或旧q03混合时期统计。
- 原生表26行，**206个数值+2个缺省坐标标记=208个字段**；CELL_INDEX逐值回溯CSV行/列/格式，ROW_INDEX逐行核对实际LaTeX目的位置。
- PROSE_FACT_INDEX核对10项正文/回复事实；DATA_CHECK核对7项汇总统计、175个逐格百分比、全部最大值时间范围及远端三项低于全部25格。
- 正式结论：区域湿小时频率相对格点中位数+14.3%，Q90 +8.8%，Q95 −7.3%，Q99 −13.1%，Q99.9 −13.9%，最大值−31.4%。这些是各统计量的相对变化，不是百分点变化。
- 区域Q95=0.574048 mm h⁻¹，单格点范围0.5441–0.6990 mm h⁻¹，中位数0.618935。远端Q99、Q99.9及最大值均低于全部25格。
- 计算顺序为空间平均后取分位数，原降水尺度；脚本中log1p仅为后续诊断打印，不参与阈值定义。Q95是训练期统计上尾阈值，不是物理定义的强降水分类。
- CSV六位小数舍入会造成从已舍入值复算比例与归档百分比的微小差别，核验采用明确的舍入误差界；未宣称所有舍入后比值逐位一致。

## 关闭材料保护及摘录

check_integration.py通过，结果见VERIFICATION.json：

- **92段旧RevisedExcerpt原文全部保留**；新增5段与最终manuscript逐字匹配；合计97段均匹配（仅忽略已有颜色包裹及空白规范化）。
- 移除四个本轮追加红色块后，整个manuscript与before快照字节内容一致；五段摘录中的Results及support同属一个追加块。
- Table 5完整A1/A2/B、全部既有正文表/图环境、Supplementary S1–S46及Figure S1源代码均保持。
- R2-M7以外Response letter前后内容完全一致；ReviewerComment保留原文mm，回复说明正确mm h⁻¹。
- 112个保护文件SHA256不变，包括作者图、原q03相关文件、R2-M6整合记录及文献库。
- 新正文、表、caption及Response红色；EvidenceBox和位置说明蓝色，图片内部文字未改色。

## PDF编译、引用和实际版面

复用此前成功的Supplementary→manuscript→Response letter顺序编译。本次直接核对三个当前.tex的MD5及字节数，均与成功构建的.fdb_latexmk记录一致；PDF生成时间晚于源码，故没有再次编译不变内容。

| PDF | 总页数 | 实际100%比例检查页 |
|---|---:|---|
| build/Supplementary.pdf | 51 | 50、51 |
| build/manuscript.pdf | 94 | 27、28、53、76、80 |
| build/Response letter.pdf | 68 | 44、45 |

上述页此前以72 dpi（1 PDF point=1像素）渲染并逐页实际查看，核对表格完整、图像未裁剪、图例/坐标/正文/caption可读、无重叠；这不等同测量每个用户物理显示器的缩放。Table S47完整26行单页，无强制resizebox；作者图原生119×70 mm完整显示。

三份最终log无undefined reference、重复label、Overfull hbox、float too large或阻断错误。正文模板已有字体/bookmark警告及重复1.41457pt overfull vbox警告保留，不将其误报为本轮新增横向溢出。Supplementary及Response最终log未记录警告。aux中的S47/50页和S2/51页与正文及回复实际显示一致，新增内容颜色经PDF span颜色及实际页面检查确认。详见PDF_CHECK.json、PDF_PAGES.json及三个compile_*.txt。

## 任务范围与Git

任务03只更新R2-M7相关范围；R3-C14、R4-m12/m20/m26/m36仍Pending，未将共享任务整体关闭。历史规划中的S1、旧混合时期q03文件及代表格点百分比保留为历史，已明确由本轮同一时期/25格中位数口径取代，不能当成当前正式编号或数值来源。

本地分支`main`，HEAD为`ae4cd53b795943878bcf135634f62432b7e2b922`。工作区有大量此前已存在的未提交/未跟踪返修内容，GIT_STATUS.txt为本轮整合末的快照，恢复时再次只读检查状态；未执行add、commit、push、fetch、覆盖CSV或历史改写。本轮固定科学源证据已在远程dc85083；新增论文整合及报告**尚未Git归档**。后续只能在作者授权后按本轮patch选择性归档，禁止整份暂存混合返修LaTeX。

## 剩余事项与关闭判断

未发现新的科学或排版阻断问题。本地整合标准已满足。仍需：

1. 作者审查本报告、patch及三份PDF。
2. 得到明确授权后选择性提交/推送本轮文件，并远程回读核验。
3. 归档通过后再更新R2-M7正式关闭状态；最终全文页码/行号仍待全稿统一补齐。

**当前结论：R2-M7本地最终核验通过，等待作者审核及授权归档，尚不满足包含Git归档在内的正式关闭条件。**
