# R2-M3最终整合与核验报告

日期：2026-11-14。结论：本条必要科学内容与最终PDF核验通过，R2-M3可关闭；不启动R2-M4。

## 实际修改

- manuscript.tex：仅新增六段，§3.2两段方法、§4.1两段结果、§5.3上游敏感性、§5.4筛选局限。原同期筛选历史及既有R1/R2-M1/M2文字均保留，新增内容全部红色。
- Supplementary.tex：原S1–S22全文保留，自动新增S23关联与区间、S24候选池稳定性、S25 C6配对、S26/S27两模型上游敏感性。语义label为stab:r2m3_*，不用预留号。原生LaTeX排版，沿用revisiontable，数值正文10 pt、原有caption约8 pt，无resizebox。新表局部行距1.15，两类区间分行以避免溢出。
- Response letter.tex：仅替换R2-M3占位，原审稿文字不变；Response红、位置及六段EvidenceBox蓝。六段摘录与最终正文逐字相同；为其中原样章节引用建立局部名称别名，未手写章节/表号。其他审稿回复逐字保持原样。
- FINAL_REVISION_CHECKLIST.md、35项清单任务09、SUPPLEMENTARY_TABLE_REGISTRY.md：范围化完成记录和实际编号映射；共享R3/R4任务不整体关闭。

## 科学核验

1. 已确认原稿同期筛选，18,410原始训练时刻与18,409训练内提前量配对、18,404构窗目标区分明确。q09的x(t)对tp(t+6h)，rank-partial仅控制tp(t)，移动块28/2,000/42；不将相关或区间不跨零解释为预测增益或因果。
2. q09未截cp的13变量关联、区间和排名来自原CSV。11池完整集合保持率0.9965（99.7%），13池0；13池v10频率0.797、d2m为0、cp为1，分别呈现，未混用候选池。
3. C6逐格截零cp后再空间平均；不套用q09未截cp的数值或区间。C0/C6同七变量预算、架构内相同超参数与训练程序、五固定种子、划分、窗口和3,939目标。配对均值与两类区间取自q21_effect；seed-t df4，测试全序列moving blocks28/5,000/42，子集后施加，均为pointwise、无多重校正。
4. C6 XGBoost全测试差+0.000132，两区间跨零；BiLSTM-Attention+0.001113（+0.458%）、5/5变差，两区间正。BiLSTM湿时及上尾seed-t跨零、bootstrap正，均保留，不据总体结果宣称所有子集稳定变差。
5. C3预设，C3a/C3b后续探索，按已归档代码/日志说明，不声称独立预注册；C3双模型整体改善6.4%/7.0%，但同时扩大空间域及特征数，不能作为固定预算筛选比较。保留原配置仅限已测试条件，不声称全局最优。

## 证据深度与范围

374个数值转录条目逐格映射CSV文件/行/字段/完整值/显示值/目标table label，见cell_evidence_index.csv及json。核验50组原始运行JSON及对应预测CSV的特征、18,404/3,939/3,939划分、共同测试时刻及目标完全一致；仅检查保存指标的24组配对方向及均值末位容差，未从预测重新计算指标或重抽Bootstrap。原表格保存数值不变。固定Git版本、MD5及各文件路径见EVIDENCE_INDEX.md、source_index.json和run_index_verification.json。

## 编译和最终版面

Supplementary → manuscript → Response letter顺序编译通过，最终分别22、78、57页。Supplementary S23–S27位于18–22页；正文核对14–16、36–37、64–66页；回复31–33页。相关最终页面以100%点比例渲染并检查，表格、图文引用、红蓝颜色、框内文字完整，无裁切或重叠；旧图件未改动。无未定义/重复引用、Overfull hbox、过大float或阻断错误。正文保留Springer原有字体/书签和1.41457 pt纵向盒等模板警告。首次构建修复了生成字符串的转义错误及宽表溢出，最终日志已无这些问题。没有新实验、训练、绘图或正式指标重算。

## Git同步边界与共享待办

当前主工作树main仍以早期ae4cd53为基线，存在其他任务的大量未提交返修；远程已经有独立实验归档。因此采用隔离工作树仅提交本轮独立patch和R2-M3证据/状态记录，不整份提交三份LaTeX而混入既往其他任务修改。远程patch对应本地已完成的整合，不能声称远程整篇LaTeX已经同步。实际提交及远程核验状态见GIT_SYNC.md。

R3候选文献依据与季节性分析、R4相关变量实验/审稿回复仍未关闭。两种cp定义之间存在已披露的处理差异，C6并非未截cp的严格同值重训；候选池、单时间划分、五种子及pointwise多重比较限制保留。无阻断本条关闭的新科学问题。最终页码行号仍待全篇统一补注。

## 独立patch基线

- `manuscript.tex`: SHA256 `331f06a6d7786c51592c24d75d491ae82b7143135cf966a526baba150a6a32a2`
- `Supplementary.tex`: SHA256 `b28efcf501104ca915d5937da70403e08dd33dc248141041f9eac6eb9adfe5dd`
- `Response letter.tex`: SHA256 `71ca977e251eafc6c72b078c905f0466c912c800cbdd9a2c62a41da9e50bb164`
- `FINAL_REVISION_CHECKLIST.md`: SHA256 `4deade89ecfd19c46493bea842b7f8d4efcfd976d68cf24366c3401650ff40d5`
- `SUPPLEMENTARY_TABLE_REGISTRY.md`: SHA256 `6aeb535b2f50fa7ee6d3094a1198d8a26e1590a562175a4c19b0dc7dd4d0eb12`
- `ESI_审稿意见分类_严重程度排序_35项.md`: SHA256 `4e01de76cf3fb1865d95e40a3e5dafcd083a7e871f96ac0278d06a7701460856`

## 当前源码位置

- `manuscript.tex:169`：To examine the mismatch between contemporaneous screening and the six-hour targe…
- `manuscript.tex:174`：The saved q21 C6 comparison replaces d2m with cp in the original seven-predictor…
- `manuscript.tex:583`：The six-hour lead-time correlations of mxtpr, mntpr and lsp fell to 0.515, 0.525…
- `manuscript.tex:588`：Replacing d2m with the processed cp in C6 did not improve overall RMSE under the…
- `manuscript.tex:1027`：Contemporaneous association is not six-hour predictive contribution, and a rank-…
- `manuscript.tex:1045`：The feature-selection evidence is restricted to the tested candidate pools, two …
- `Supplementary.tex:770`：\label{stab:r2m3_associations}
- `Supplementary.tex:795`：\label{stab:r2m3_selection_stability}
- `Supplementary.tex:822`：\label{stab:r2m3_c6}
- `Supplementary.tex:842`：\label{stab:r2m3_upstream_xgboost}
- `Supplementary.tex:863`：\label{stab:r2m3_upstream_bilstm_attn}
- `Response letter.tex:606`：% Review ID: R2 M3
