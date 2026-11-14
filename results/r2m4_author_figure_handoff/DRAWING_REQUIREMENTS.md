# 作者绘图交接要求

建议最终文件：`Figures/r2M4_event_csi_comparison.pdf`（矢量PDF）；LaTeX标签保持`fig:r2m4_event_csi`。最终图由作者绘制，助手不再生成候选或最终图。

数据锁定Git版本667d6f80e64076dc6812ca630654a24d1aab5b4e；原始fixed及q05e CSV未修改。本目录CSV仅选列/选行和复制原值，不重新计算、拟合或优化任何指标。每行保留源文件、行号和MD5。

- Panel A：r2M4_csi_fixed_plot.csv，42行，固定c_tau=tau。
- Panel B：r2M4_csi_validation_selected_plot.csv，35行，验证CSI选定cutoff后冻结测试；正式300分位概率网格、去重后至多300个候选。
- 合并数据：r2M4_csi_both_rules_plot.csv，77行。
- 固定配色、marker和打印名称：r2M4_csi_model_style.csv，沿用归档fig_style.py。

七方法：XGBoost、Transformer、BU-LSTM、BiLSTM-Attention、BU-LSTM-Attention、Prob. BiLSTM-Attention、Persistence。全部为单次保存预测（概率模型用预测均值），不是五种子均值；共同测试N=3,939。

按强度递增的分类顺序：Wet>=0.1、Q90、0.5、Q95、Q97.5、1.0。数值标签从Threshold_mm_h读取，建议显示4位小数；单位mm h^-1。Q分位来自18,404个构窗训练目标，不能写测试集分位。两种CSV保留各来源原始精度，科学显示精度一致。

Panel B无0.5数据：可省略此类别或保留明确空档，绝不能补零、插值或虚构优化结果。Panel A所有零CSI必须保留并可辨识。建议离散点、分类坐标；若同点重叠，可按模型小幅水平错位，不暗示连续阈值响应。建议两面板使用一致纵轴范围，纵轴CSI无单位；完整图例和两规则名称必须清晰。

建议原生正文宽约119.0–119.1mm，不在LaTeX二次缩放；高度以可读性及图注容纳为准，不强制沿用已删除候选尺寸。Latin Modern字体、基础字号至少8pt；采用现有模型配色。100%比例确认七模型名称、阈值、零点和图例。图内不标红；图注和新增正文按返修规范标红。

图注须说明：单次保存预测、N=3,939、固定与验证优化规则、300候选概率网格、训练分位来源、0.5优化缺失、零值保留。无支持绝对CSI区间的数据时不添加误差棒；已有model-minus-Persistence的pointwise配对区间在补充表中，不得当作绝对CSI误差棒。不要在图中加入Holm显著性星号或宣称控制FWER。

优化CSI改善不否定固定规则失败；高FAR代价在正文/表格保留。若标注优化规则不确定性，必须说明：Confidence intervals are conditional on the selected decision thresholds and do not account for uncertainty in threshold selection.

现有图注仅为待图草稿，最终措辞将根据作者实际图片校对；不得把占位稿的可编译性检查视为最终图片/版面核验通过。
