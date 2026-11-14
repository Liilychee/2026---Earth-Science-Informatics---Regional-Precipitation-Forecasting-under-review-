# R2-M4选择性Git归档边界

本轮仅新增图件Figures/r2M4_event_csi_comparison.pdf、对应plot_csi.py、R2-M4独立patch、逐格/图点索引、版本锁定及核验/任务关闭报告。

不整份提交当前manuscript.tex、Supplementary.tex、Response letter.tex：它们含既往其他返修，完整最新稿仍在本地；本次patch只记录本轮六份授权文档相对before快照的实际差异，基线/当前SHA256见DOCUMENT_HASHES.json。不能声称远程整篇LaTeX已同步。未提交旧图、原始预测、CSV副本或构建PDF。

绘图可在固定来源版本667d6f8和所需PGF/pdflatex环境下从原CSV重现。已有fig_style不修改，仅对本机缺少的dvipng/Poppler CLI采用PDF后端适配。原输出文件保留不覆盖；首次布局候选仅保留本地，不归档为正式图。

使用最新origin/main的独立工作树，白名单暂存，普通快进推送，不强制、不改写历史。主工作区原分支及未提交修改保留。本目录正式提交与远程核验以Git历史和最终回执为准。任务05/12共享待办不整体关闭，R2-M5不启动。
