# R2-M4作者最终Figure整合与关闭报告

2026-11-14。结论：作者最终图、科学定义、数值溯源、caption、EvidenceBox、三份PDF及本轮选择性Git归档核验通过后，R2-M4正式关闭；只关闭本条，不整体关闭任务05/12，不开始R2-M5。

## 最终Figure

- 原件：Figures/r2M4_event_csi.pdf，626,022字节，MD5 `f73dd3d355084727bb13bf644ce332d3`，SHA256 `931cbc9e74a7b316764ba373afc5ffa7726aef43c288b28df8230a244c29923e`。
- PDF为1页、337.322815×212.598419 PDF点，即约119.0×75.0mm；无栅格图像，嵌入Latin Modern字体。Downloads同名副本MD5一致。图片内容未修改、重绘、裁剪或重编码。
- 图为作者确认的双面板分组散点图：(a)固定c_tau=tau，(b)验证期选择cutoff；两面板七种方法。a有六组42点；b有五组35点，0.5位置为not evaluated。固定零CSI点仍可见；横向偏移为显示需要，不改变CSI。没有连接线暗示连续数值尺度。
- manuscript采用原生尺寸includegraphics，未额外缩放。Figure label=`fig:r2m4_event_csi`，最终自动Figure 5，正文第51页，首引用第50页。其他figure环境、图片路径、caption及label逐字不变。旧助手图没有恢复。

## 77点核验的确切层次

本轮重新读取交接r2M4_csi_both_rules_plot.csv，逐行对照固定Git版本667d6f80e64076dc6812ca630654a24d1aab5b4e的fixed/q05e分数CSV。42+35=77行的CSI、命中数和预报次数全部一致，差异0；完整记录POINT_VERIFICATION.json。

未在项目、Downloads、实验档案、临时目录和当前origin/main找到作者最终`r2M4_event_csi_values.csv`。因此不能声称本轮直接读取作者最终导出或从PDF恢复77点全精度。最终图片77点完全一致以及最大横移0.36类别宽度，明确引用作者本次指令提供的此前独立核验。Downloads/plot_r2m4 (2).py只读检查的结构与说明一致，但没有执行，亦未假定其唯一生成了最终PDF。这一数据输入回查、作者此前核验及本轮图像内容/版面检查的区别已写入证据索引；没有捏造缺失文件或核验过程。

## caption、正文和回复

占位已删除，正文R2-M4新增段落恢复正式Figure引用；caption完整说明N=3,939、两规则、各方法独立验证CSI选cutoff并冻结、300概率候选网格、Q90/Q95/Q97.5实际值及18,404训练目标来源、等距分类轴、纯视觉横移、b的0.5未评估、零值保留、固定高阈值不如Persistence、b中除Transformer外Q95 CSI更高、Persistence自己选cutoff及其面板差异，以及配对区间的pointwise/未多重校正/条件性。使用用户指定的固定规则科学表述，不推断幅度压缩根因。

Methods、Results、Discussion、Abstract和Conclusion已有科学内容核查通过，无需无意义重写：tau与c_tau分清；正式q05e为300候选网格而非旧500；POD/FAR/CSI/AUC定义与原输出相符；FAR不是false positive rate；循环块28个六小时样本、2,000次、42、共用配对索引、95%百分位区间；固定0.5结果保留；优化CSI和高FAR代价不否定固定规则失败；无校准Holm/FWER确认性声明；条件区间遗漏选择不确定性清楚保留。

Response只修改R2-M4的待图语句、位置说明和对应摘录，并增一段作者图caption EvidenceBox。R2-M4原审稿文字与comment.txt逐字一致。八段EvidenceBox与最终manuscript逐字一致；Response红、框及位置蓝，新增正文/图注及跨文档引用均红，RGB抽取复核见COLOR_CHECK.json。没有修改R1或R2-M1–M3回复、审稿原文或已核验数值。

## Supplementary

S28–S31源码与本轮开始时逐字节一致；1,217个既有数值转录再次回查原CSV行/字段/完整值，全部匹配。单次固定/验证优化、两个Attention结构种子均值/SD和平均预测配对各自分表，未混用。0.5只在固定规则；缺失AR/气候态项不捏造，零预报FAR为横线；区间规则对应、pointwise未校正及阈值选择不确定性说明保留。

|表号|label|PDF页|
|---|---|---|
|S28|stab:r2m4_fixed_events|23–25|
|S29|stab:r2m4_tuned_events|26–28|
|S30|stab:r2m4_seed_scores|29|
|S31|stab:r2m4_ensemble_events|30|

caption引用前两表，回复引用四表；均以ref自动解析，无SX占位、重复label或手写预占号。原S1–S27不变。

## 三PDF最终核验

Supplementary → manuscript → Response letter顺序latexmk成功，最终分别30、82、60页。正文1–2、26–27、50–52、64–65、74页；补充23–30页；回复34–37页按100%点比例查看。作者图完整、未裁剪，图例/坐标/两面板/图注可读，caption无需放大缩小图片即可容纳；表格、说明、框内摘录、脚注及引用位置无新严重问题。没有缺失图片、未定义或重复引用、Overfull hbox、过大float或阻断错误。旧Springer字体、书签及1.41457pt轻微纵向盒警告保留。

62段旧稿可直接字面匹配的摘录继续匹配；其他旧摘录涉及不同颜色包装，但对应正文因严格scope等价保持原样。所有非本图figure环境逐字不变。没有新引用或参考文献修改；原有参考文献及既有成果不受影响。最终页码行号仍待全篇统一补注。

## 修改与Git边界

实际文档修改：manuscript.tex、Response letter.tex、FINAL_REVISION_CHECKLIST.md及35项任务05/12的R2-M4状态；Supplementary及参考文献未改。图文件为作者最终原件。新的窄patch只对本轮开始快照记录上述四份文档差异，基线/当前SHA256见DOCUMENT_HASHES.json。

只向正确origin/main选择性归档作者PDF、最终patch、来源/点值核验/颜色/文档哈希/编译检查摘要和关闭状态；不整份上传含其他未授权返修的LaTeX，不提交原始预测、大型数据或整篇构建PDF。使用隔离工作树、普通快进，不强制或改写历史；实际提交SHA与远程核验见最终回执。旧准备/交接状态记录保留为历史并增加本轮最终状态指针，不误当当前未完成。

剩余边界：作者最终values CSV不可访问，精确图点一致性采用作者此前确认，本轮独立输入回查的范围已如实披露；pointwise未校正区间、cutoff选择不确定性和未确定根因均保留，不构成新编造或被隐瞒的问题。任务05/12其他共享意见不关闭，R2-M5未启动。
