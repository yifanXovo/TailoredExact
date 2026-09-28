# R93 纯有理微型 oracle 收据

脚本：[round93_coquantity_oracle.py](../../tests/round93_coquantity_oracle.py)，SHA256 `57cf9bc189e54f88fcc1a141976e6b596c40fe5547890b58859127c87c3c17f0`。命令使用桌面捆绑 Python：`C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe tests/round93_coquantity_oracle.py --out results/unified_exact_round93/coquantity_oracle_results.json`。最终返回码 0，九例全部断言通过，原始逐整数结果在 [coquantity_oracle_results.json](coquantity_oracle_results.json)。脚本自测 wall `0.0015425002202391624 s`、CPU 计时分辨率下 `0.0 s`；外层命令完成约 `0.1972245 s`。此前一次 WindowsApps `python` 入口失败（约 `0.1836 s`、无输出），第一次捆绑 Python 启动暴露脚本括号语法错误（约 `0.1823 s`）；修复后一次通过。这些开发成本不属于正式算法运行成本。

oracle 独立于 C++ 增量目标逻辑，用 `fractions.Fraction` 从整数路线操作重新计算每个车辆的逐站载量、返仓剩余载货装卸、删零后的旅行、库存、`S/H/P/F`。它枚举容量给出的全部同向整数 `t`，另在主例枚举 R75 的全部单站/等量转移形状。主例 `initial=(3,6), C=(6,6), D=(4,4), Q=5` 从 `F=3/20` 出发，同向 `t=1` 达 `3/40`；旧 R75 可行邻点最小 `17/80`。原指定零旅行/处理时间和额外正度量旅行/处理时间两个版本一致，新路线仍服务站 2。空路线目标 `67/240≈0.279167`，比原点差。

另外七例覆盖 `S=0` 的 Gini 约定、不同目标/权重、跨车并返仓载货、取放变号、非度量删站后旅行增加、精确有理 `T+1e-7` 等号可行及越界不可行。`sign_flip` 的 `t=2` 在取转放后仍物理可行；非度量例的删站候选因旅行从 3 增至 101 而被拒。等号检查是**有理数学**，不能推论二进制浮点 Evaluator 的边界行为。所有九例都不是 Gurobi 模型、原生数值证书或真实基准实例的完整算法比较；生产实现仍需独立 C++ 源审、构建和与原 Evaluator 的边界资格。
