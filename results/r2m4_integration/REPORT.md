> 当前状态更新：用户指定CSI图由作者绘制，助手图和候选已删除。R2-M4未完成，待作者最终图片及最终PDF核验。下文为此前历史整合记录，其中关闭/图件完成声明不再有效。现行交接见../r2m4_author_figure_handoff/。

# R2-M4最终整合与核验报告

日期：2026-11-14。R2-M4完成并关闭：必要科学、数值及PDF核验通过，新图、patch及证据随本报告正式归档。旧667d6f8仅准备阶段的状态由本轮记录取代，不关闭其他共享意见，不进入R2-M5。

## 实际修改文件与位置

- manuscript.tex：§3.4修正两句未实际报告accuracy/precision/F1的泛称，新增两段事件规则与统计设置；§4.3.2在R1-M1原段后新增固定、优化及五种子区分，插入Figure；§5.2、Conclusion和Abstract补负面结果与因果边界。原R1摘录内容保留。
- Supplementary.tex：只新增分页长表局部环境及S28–S31；caption沿用Springer 8bp、表体10pt，不用resizebox，不修改既有revisiontable和S1–S27。长表逐行标明阈值，翻页后不会丢失定义。
- Response letter.tex：仅R2-M4块完成英文回复及七段逐字EvidenceBox；Response红，摘录/位置蓝。审稿原文及其他回复逐字不变。
- FINAL_REVISION_CHECKLIST.md、35项任务05/12及SUPPLEMENTARY_TABLE_REGISTRY.md：范围化状态、当前自动编号，不整体勾选共享工作。
- Figures/r2M4_event_csi_comparison.pdf与plot_csi.py：七方法77个CSV离散点；A固定、B验证优化，0.5优化留空，固定零点完整保留。119.0×145.0mm原生插入，无缩放。采用归档fig_style的颜色/marker/Latin Modern及至少8pt基础标签；本机缺少dvipng/Poppler CLI，以PGF/pdflatex输出矢量PDF、fitz渲染，未修改归档样式源文件。数学上下标使用正常的较小字形。

## 科学核验结果

1. 固定Q95/Q97.5/0.5/1.0下Persistence CSI为0.139/0.076/0.166/0.058，六模型最多0.071/0.009/0.113/0.011。24差值负、各pointwise区间低于零，不是多重校正结论。零预报时CSI=0、FAR未定义；未把缺项填0。
2. 优化cutoff是另一规则：Q95五模型区间支持改善，Transformer不明确；1.0四模型支持，Transformer及Probabilistic BiLSTM-Attention不明确。FAR约0.73–0.80/0.86–0.92。AUC优势仅表征排序，不能替代固定CSI。优化区间明确遗漏阈值选择不确定性。
3. q05e正式300分位概率网格、去重至多300个候选，仅验证CSI选定后冻结测试，不混用500旧版。q05g种子指标均值/SD与五种子平均预测配对严格分开；后者有自己在平均验证预测上选定的cutoff。
4. 循环块28个六小时样本（7天）、2,000次、种子42、模型/阈值共用IDX、95%百分位区间。全部pointwise且未校正；不展示Holm推断，不新增检验追求显著性。
5. 固定表AUC仅复用同连续保存预测和同事件定义的q05e值。只读核对可用regional序列和XGBoost保存y_true，在六阈值下事件标签逐项一致。0.5 AUC、新固定AR/气候态的AUC及缺失基线配对项保留横线。优化AR为正斜率仿射变换的理论等价规则，保存forecast/hits/POD/FAR/CSI相同，AUC末位tie差异不强行说成完全相等。
6. 预测幅度压缩、漏报、高FAR如实呈现，不声称已识别主要成因。Persistence较高CSI也不意味着其高阈值误报低。

## 数值溯源与范围保护

1,217个数值转录见CELL_INDEX.csv/json（源文件/行号/字段/完整值/显示值/目标label）；77图点见FIGURE_POINTS.json。SOURCE_INDEX.json锁定667d6f80e64076dc6812ca630654a24d1aab5b4e中17份证据的MD5/SHA256。仅核验保存分数的算术、汇总、事件标签及转录，没有训练、正式预测生成或重新抽取正式区间；原始CSV不变。

七段新EvidenceBox与正文逐字匹配；62段旧稿可直接匹配的摘录继续逐字匹配，其余包装差异段落因对应正文及回复区未改而保持有效。旧27表完整保留，旧图文件未编辑；R1和R2-M1–M3的审稿原文、回复、数值不变。SOURCE_INDEX及EVIDENCE_INDEX说明本轮未找到独立对应关系文件，直接核对35项任务05/12中的对应意见和原文。

## 编译与100%版面

按Supplementary → manuscript → Response letter运行latexmk，最终30／82／60页。Figure 5在正文51页，首引用50页；旧覆盖率/SHAP/消融顺延6/7/8，label未变，旧回复ref全部正确解析。S28在补充23–25页、S29在26–28页、S30/S31在29/30页。

正文1–2、26–27、50–52、65、75页、补充23–30页及回复34–36页按100%点比例渲染检查；图、图注、表、说明、框内文字、红蓝和交叉引用完整，无裁切/重叠。新图模型名称、阈值数值、零点及缺失空档可辨。没有未定义/重复引用、Overfull hbox、过大float或阻断错误；原Springer字体/书签和1.41457pt轻微纵向盒警告保留。新增文献为零，数据库未改。最后页码/行号仍待全篇统一补注。

## 归档边界与剩余事项

当前本地main仍有既往大量未提交返修，采用最新origin/main独立工作树，仅提交本轮新图、绘图脚本、独立patch与核验/状态记录，不整份提交LaTeX或构建PDF。patch基线及当前源哈希见DOCUMENT_HASHES.json；正式提交见本目录Git历史和最终回执。远程存在patch不代表完整最新版LaTeX已同步。

无阻断本条的新问题。仍须保留单次范围、规则区别、pointwise未校正区间、阈值选择不确定性、平均预测/平均指标及未确定根因等科学边界。任务05/12其他独立意见继续待办。

## 当前源码索引

- `manuscript.tex:457`
- `manuscript.tex:461`
- `manuscript.tex:810`
- `manuscript.tex:823`
- `manuscript.tex:827`
- `manuscript.tex:1031`
- `manuscript.tex:1115`
- `Supplementary.tex:894`
- `Supplementary.tex:980`
- `Supplementary.tex:1056`
- `Supplementary.tex:1080`
- `Response letter.tex:651`

## 最终链接颜色复核

最后PDF检查发现Springer跨文档引用默认呈青色，已仅在本轮新增正文段落及图注的局部分组中补filecolor/urlcolor=red。正文S28–S31引用经PDF文字颜色提取确认为RGB FF0000；回复Response仍红、EvidenceBox仍蓝。复核证明此追加修改只涉及颜色命令，正文科学文字、所有数值、Supplementary和回复信源文件均与前次核验一致；按既定顺序编译通过。通过追加提交归档，不改写前一提交历史。
