# dry定义与探索性选择记录

“The exact-zero definition (dry = 0) treats every positive ERA5 value as wet. A seed-42 check of three dry definitions preceded the five-seed runs; dry = 0 did not give the best validation or test CRPS for either distribution.”

此句的实现限定必须一并说明：dry0使用max(dry,1e-6)的数值零容差，而非把所有浮点重构微差视作湿。测试数据有711个≤1e-6样本（全部为非正重构值，最大绝对值3.5304e-9），没有(0,1e-6]样本；最小明确正值约1.90764e-5。对这些保存测试样本，没有正降水被该容差额外归为干。不得泛化声称任意数据中每个>0浮点数都不受容差影响。

未找到可核实的预先指定记录。JSON时间戳显示seed42的三阈值检查至2026-11-06 00:43:27Z完成，其他seed最早01:38:27Z完成；这是探索后扩展为五种子的证据，不是独立预注册。seed42预检运行也被后续五种子汇总复用。

seed42验证CRPS（JSON的199分位历史评分，评价key统一dry0）：Tobit 0/.001/.01 = .0779/.0767/.0749；Bernoulli–Gamma = .0717/.0715/.0718。测试值分别为.0826157/.0813090/.0797721及.0783347/.0779764/.0783054。dry0不是两种分布的最优验证或测试设定。Tobit随dry变化较大；Bernoulli–Gamma这些设定下变化较小。

每种替代分布的dry0和dry.001各5个种子；dry.01只有seed42。不得将后者描述为五种子敏感性。上述199分位CRPS仅用于历史选择溯源，不混入正式full CRPS表。正式dry.001的full逐种子值可用q11_twcrps_per_seed；匹配的full paired仅保存了Bernoulli–Gamma(.001)减Bernoulli–Gamma，未保存Tobit(.001)减Tobit的full块区间，不能套用199分位区间；dry.01没有同口径的正式full列，不能编造其五种子均值或匹配区间。
