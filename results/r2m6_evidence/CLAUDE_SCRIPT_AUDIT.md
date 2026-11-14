# Claude原脚本只读审计

原文件位于/private/tmp/claude-501下的同项目scratchpad，已原样复制到claude_original/verify_r2m6.py和verify_r2m6_output.txt，作为历史证据，不覆盖原件。

- Gaussian为解析CRPS，但normal CDF采用误差约1.5e-7的erf多项式；新脚本使用SciPy ndtr。
- Bernoulli–Gamma使用E|X−y|−0.5E|X−X′|混合分布解析表达式，考虑零点质量，方法正确。
- Tobit使用[0,12]上24,001点梯形积分，不是闭式CRPS。旧输出的“exact CRPS”统一标签不能直接用于正式方法说明。
- 旧脚本读取用户Downloads中的原预测文件及另一个本地仓库，路径依赖且没有固定Git版本。新脚本只读固定d02519c的Git对象。
- 旧Bootstrap保留3,948项，与正式源实现一致；旧Tobit积分不能充当本轮闭式验证。没有重新运行旧脚本，也没有将其输出用作正式CSV替代品。
