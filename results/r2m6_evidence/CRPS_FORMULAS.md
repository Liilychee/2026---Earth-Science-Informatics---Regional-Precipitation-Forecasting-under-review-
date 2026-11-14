# 独立解析CRPS与数值交叉检查

`verify_closed_crps.py`中三种分布的评分均为解析表达式，未用199分位或网格积分代替闭式。自适应积分仅用于验证解析式；原full网格函数仅为复现旧归档评分及配对区间。下列公式由CRPS定义/期望恒等式展开。

设φ、Φ为标准正态密度和CDF，A(u)=uΦ(u)+φ(u)。

1. Gaussian：z=(y−μ)/s，CRPS=s[z(2Φ(z)−1)+2φ(z)−1/√π]。
2. Tobit：X=max(0,Z)，Z~N(μ,s²)，是零删失而不是条件截断后重归一化。令a=−μ/s、z=(y−μ)/s、q=Φ(−a)，对于y≥0：
   J=s[−aq²+2qφ(a)−Φ(−√2a)/√π]；CRPS=2s[A(z)−A(a)]−y+J。
   由CRPS=∫₀ʸF²+∫ʸ∞(1−F)²=2∫₀ʸF−y+∫₀∞(1−F)²得到。反导数u(1−Φ(u))²−2(1−Φ(u))φ(u)−Φ(√2u)/√π给出J。对负观测使用CRPS(max(y,0))+max(−y,0)扩展。
3. Bernoulli–Gamma：P(X=0)=1−p，X|positive~Gamma(a,scale=b)。令Gₐ(y)=P(a,y/b)，M=ab，y≥0：
   E|X−y|=(1−p)y+p[y(2Gₐ(y)−1)+M(1−2Gₐ₊₁(y))]；
   0.5E|X−X′|=p(1−p)M+p²b/B(1/2,a)；CRPS为两者之差。这包含零点质量与连续Gamma之间的交叉项，不能直接套用纯Gamma公式。

独立验证：每配置/种子选取干样本、最大观测及参数极端样本等共99条（逐条见analytic_formula_checks.csv），从CDF定义在观测和零点分段，以无限尾自适应积分验证。最大绝对误差见CRPS_VERIFICATION.json。另检验p=0点质量和强删失极限。数值积分在这里明确只是交叉检查，不是闭式算法。

方法参照（原始作者/官方实现文档）：
- Jordan, Krüger & Lerch, Evaluating Probabilistic Forecasts with scoringRules: https://arxiv.org/abs/1709.04743
- 官方generalised truncated/censored normal闭式接口：https://scoringrules.readthedocs.io/en/latest/generated/scoringrules.crps_gtcnormal.html
- CRPS期望恒等式与加权评分说明：https://github.com/frazane/scoringrules/blob/main/docs/weighted_scores.md

原full为有限网格CDF平方积分：Gaussian −4到8，其余0到8；不是数学意义的“exact”或闭式。原函数逐样本复现后seed平均与full列误差<2e-14。另用同网格只积平滑F²，阶跃交叉项用解析原函数，分离阶跃网格误差；integration_error_diagnostic.csv保留三个主要配置各自误差最大种子的诊断。有限尾遗漏上界远小于所见均值差，差异属于网格求积误差（Gaussian/Tobit主要为观测阶跃处理，Gamma亦有零点附近CDF曲率求积误差），不应归因于不同预测或不同种子。
