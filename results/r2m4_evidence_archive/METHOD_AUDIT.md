# R2-M4固定阈值证据与统计方法核验

日期：2026-11-14。范围：35项任务05+12的证据准备，不修改LaTeX，不绘图、不训练模型、不启动R2-M5，也不关闭R2-M4。

## 文件与生成关系

第三个实际文件为`r2m4_fixed_output.txt`，不是第三张CSV。三份原件均来自`/Users/yue/Downloads/`：

|标准归档路径|MD5|
|---|---|
|results/metrics/r2m4_fixed_event_paired.csv|9739ce1b23215652b3f0204835c7d51b|
|results/metrics/r2m4_fixed_event_scores.csv|9062d963e8604283005c81b82bacc6cf|
|results/metrics/r2m4_fixed_output.txt|5b6fce34f4a05e8b7188c79722009a3b|
|code/analysis_r2m4_fixed_paired_ci.py|fe3b951eb09c0f3d4f11cef00135535c|

生成脚本注释列出AutoDL运行命令（脚本stdout经tee形成txt），运行时自动搜索results/predictions或results。当前取得的实际物理原件在Downloads；没有证据证明其是在本机还是AutoDL执行，也不从文件时间推定执行环境。输出与脚本的算法及配置已独立复核相符；原日志没有脚本自校验和、完整环境或唯一运行ID。正式归档后以固定Git提交、源码与输入MD5追溯，不夸称恢复原运行环境。

paired CSV为36行×16列，scores为54行×12列（6阈值×9方法，其中六学习模型、Persistence、训练拟合AR(1)、训练月×小时气候态）。比较族不包括两种新增参照，配对均为六学习模型减Persistence。脚本/三个输出逐字节复制，原件保留，未覆盖或再生成原输出。新增审计文件与原始证据明确区分。

## 输入、CSI与Bootstrap

- 七份保存预测来自Downloads，全部与固定Git版本ac2c4eb5287749c6c08ca9f9772c6b29c743b4fb的results同名文件逐字节一致；路径、MD5及划分核验见SOURCE_MANIFEST.json和VERIFICATION.json。train/val/test分别18,404/3,939/3,939，各模型时间顺序完全对齐。
- 统一采用XGBoost文件中的y_true。Persistence的目标值因保存精度与其不同：训练最大约4.36e-7、测试约1.64e-7；脚本允许小于1e-6，六阈值下事件标签逐项相同，已再次核验。
- 固定规则为预测均值>=事件阈值tau，观测事件同样用y>=tau；Q90/Q95/Q97.5来自18,404构窗训练目标。不能与验证集优化cutoff混为一谈。
- CSI=H/(H+FA+M)，零预测且存在观测事件时为0，FAR分母为0时保留NaN，不能写FAR=0。
- 循环块Bootstrap：N=3,939，块长28个六小时样本（7天），2,000次，种子42；每次抽ceil(N/28)个[0,N)均匀起点，索引按模N绕回，拼接后截至N。全模型和全阈值共享同一个IDX；不是普通不绕回moving-block，也不是按子集单独重抽。
- 每次重抽样分别重算CSI(model)-CSI(Persistence)，区间为np.percentile的2.5/97.5百分位（当前NumPy默认线性插值），为pointwise 95%区间，不是同时置信区间；条件于单次保存预测，不是五种子统计。
- 独立核验只在内存重建同一IDX和36组差值分布以检查已保存证据，未改输入、重训或执行原脚本的AR(1)拟合/写输出步骤。54行保存计数与派生分数、42行原预测分数、36组点估计/区间/符号次数均通过；AR(1)/气候态的12行做保存计数算术核验，未独立重拟合这两个参照。
- 原CSV使用float_format="%.10g"。全部重现至已保存的10位有效数字；未保存原始未舍入Bootstrap数组，不能声称原运行和当前环境逐位相同。当前复核环境、IDX摘要及未舍入复核数值见VERIFICATION.json。
- 与既有revision_event_detection.csv重叠48行的hits、预测事件数及CSI一致。

## p值公式的实际含义

脚本第118–126行令d_b=CSI_b(model)-CSI_b(Persistence)，ge=#{d_b>=0}，le=#{d_b<=0}，m=min(ge,le)，并计算

`p_sign=min(1, 2*(m+1)/(B+1))`，B=2,000。

m是Bootstrap差值落在零两侧中较小一侧的次数，不是“零假设分布中比观测差值更极端”的次数。恰为零的d_b同时计入ge及le，因此ge+le可能大于B。它是一种带加一规则的双侧Bootstrap符号尾比例/百分位区间反演式近似p值；不是对逐时误差做二项符号检验，也不是后验概率。

脚本没有将差值重中心化到H0:DeltaCSI=0，没有在可交换性假设下置换模型标签，也没有生成H0约束分布。故没有实施真正的零假设重抽样检验。**这本身不意味着所有百分位Bootstrap反演式p值都无效**：此类推断可在合适的Bootstrap有效性条件下成立；但当前稀疏、离散CSI和相关时序下未验证其零假设校准，不能把加一规则解释为自动获得有限样本精确性或保守性。

最小报告值2/2001约0.0009995只是这条有限B计算规则的下限，不是已证明的真实p值下界。大量m=0结果和少量尾端计数，不能提供任意精细的显著性分辨率。增加B仅改善Monte Carlo精度，不能解决事后选族或p值校准问题。

方法参照：Rousselet, Pernet & Wilcox (2021)讨论百分位Bootstrap尾比例p值，但其零点平局采用半权处理，不能声称脚本的含平局/加一版本与该文完全相同，也不能把均值示例的性能直接套用到CSI时序数据。SciPy permutation_test文档的加一说明针对随机零假设置换分布，不能直接为这里未约束H0的Bootstrap提供精确检验保证。

## Holm实现与比较族

脚本第130–139行排序原p，按(k-rank)*p进行step-down Bonferroni，再累积最大并截1，最后恢复原顺序。独立标量实现逐项重现24族和36族调整值，算术正确，模型间相关并非Holm本身要求独立的理由；关键仍是输入p值的有效性和比较族选择。

24项族=六模型×{Q95,Q97.5,0.5,1.0}，脚本第10–11行明确“chosen after inspection”。所以它是事后指定的探索性子族，不能描述为预先设定的确认性比较。36项族覆盖本次六阈值×六模型，是更完整的敏感性分析，但不能把它声称为预注册或全论文所有检验的校正。

|算术结果（不是校准有效性证明）|值|
|---|---|
|高阈值24项的DeltaCSI及pointwise区间|全部为负且各自区间不含0|
|24族近似p经Holm后<0.05|24/24，最大0.023988006|
|36族近似p经Holm后<0.05|30/36|
|在36族中仍<0.05的高阈值项|23/24|
|例外XGBoost@0.5：m=8，原近似p|0.00899550225|
|该例24族调整值／36族调整值|0.023988006／0.05397301349|

XGBoost@Q95的m=2，原近似p=0.00299850075。两种族的差异来自明确的多重比较范围，不能隐藏36族敏感性结果。Holm并未修改原pointwise区间；不能把它们称为Holm校正区间。

## 论文可用范围与建议结论

**可以使用**保存的固定规则计数、CSI差值及pointwise循环块Bootstrap区间，附明单次保存预测、B/块长/种子和事件定义等限制。它们支持“在所测试的四个高阈值下，各学习模型的CSI均低于Persistence，逐项95%区间均在零以下”这一受限描述，不等于24项同时显著。

Holm列可保留原始证据，若进入论文只能明确标作**对近似Bootstrap符号尾比例p值的探索性Holm调整敏感性分析**，同时披露事后24项族、完整36项族及0.5阈值例外。**当前不能使用“24项均经严格Holm校正后显著／已确认控制FWER为5%”作为确认性结论。** Holm算法正确不能弥补输入p校准尚未验证或事后选族问题。若确需确认性多重检验声明，应另行设计并验证适用于时序CSI的检验及比较族；本轮不新增这种检验。

建议英文限定语：

> The paired CSI intervals are pointwise circular-block bootstrap intervals. An exploratory sensitivity analysis applied Holm adjustment to approximate bootstrap sign-tail p-values. The 24-comparison high-threshold family was selected after inspection; under the full 36-comparison family, the XGBoost contrast at 0.5 mm h^-1 had an adjusted approximate p-value of 0.054. These calculations are not presented as a calibrated, confirmatory family-wise error-controlled test.

## q05e版本核验

正式Git脚本code/analysis_q05e_event_paired_ci.py第84行使用np.linspace(0.5,0.999,300)，MD5=b429dd451547da117ff7d7819b49deaf，与Downloads/analysis_q05e_event_paired_ci (1).py逐字节一致。Downloads同名无(1)旧副本使用500，MD5=cfc873efcecdb23bd6b7ddfc4186e34f，明确排除。

以六学习模型及Persistence在五事件阈值上的35个保存分数组合复核：300点35/35匹配，500点仅10/35匹配。该复核只核对验证cutoff搜索与保存CSI/hits，未重抽q05e区间。新的fixed脚本完全不做cutoff调优，因此不受300/500候选网格影响；两类实验的结果不可混用。

## 归档与状态

只归档原样三输出、原样生成脚本及本核验说明/来源清单/验证程序和结果。既有q05e不覆盖，旧500点版本不归档为正式证据。主工作区有大量其他未提交返修，使用最新origin/main的独立工作树提交本轮白名单文件，不提交三份LaTeX、PDF、图件、其他实验或大型原始数据，不强推或改写历史。具体提交由本目录Git历史及最终回执确认。

R2-M4仍为准备阶段，尚未正式整合，任务05+12不整体关闭；论文如何采用探索性Holm结果仍需按上述边界处理。R2-M5未启动。

## 外部方法来源（仅方法核验，不添加到论文文献）

- Rousselet et al. (2021), The percentile bootstrap: a primer with step-by-step instructions in R, DOI 10.1177/2515245920911881：https://www.pure.ed.ac.uk/ws/portalfiles/portal/203604809/2515245920911881.pdf
- SciPy permutation_test官方文档，随机零分布和加一规则：https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.permutation_test.html
- statsmodels官方multipletests源码，Holm step-down实现：https://www.statsmodels.org/stable/_modules/statsmodels/stats/multitest.html
