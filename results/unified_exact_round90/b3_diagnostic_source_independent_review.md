# R91 五站 canonical 导出与 A/B/C 诊断：独立静态审查

审查 `scripts/round91_handling_rounding_diagnostic.py` SHA256 `5a39d8b26e91d61ae2e5835fefa890d0b982aa8f7fd7c345c828642a2e5753ca`，以及 `b3_probe_build_handoff_revision.md` SHA256 `d25d4822ba00c38f27251d992119dc7030cd6d59d4db58d20bc3bec131a17a70`。仅阅读新文件、真实 canonical writer、VD-P 行和冻结 `build.ninja`；未导入、测试、编译、导出 LP 或求解。**静态通过；仅可由 root 后续单独准入 standalone 零 Optimize 导出资格。A/B/C 三臂尚须另签真实 LP 身份与外部 300 s watchdog 门。**

独立 build 方案使用冻结的 `libexact_ebrp_core.a`，编译 `-std=c++17 -Wall -Wextra -Wpedantic -DEXACT_EBRP_ENABLE_GUROBI=1`、相同 include 路径，并沿用原 `ExactEBRP.exe` 在 `build.ninja` 中的 MinGW 链接库。新目录只编译新 probe，不改 Round90 的 CMake、七份源码、主二进制或旧库；库 SHA、编译器和实际 link 成败仍须授权操作者记录。原 exporter 已通过 source-only 物理/模型选项审查，但尚无真实 LP；不能现在声称同字节 canonical 身份。

诊断脚本把 admission 精确绑定自身、导出 manifest、LP、输入及 exporter 二进制 SHA；重新核 source 哈希、完整 canonical interval scope、VD-P、实际 verifier F cutoff、G 域与原目标。三个 arm 都从同一固定 LP SHA 新读并 `relax()`，保持全部原行和变量 bounds：A 不加行，B 只加每车 `Σ_i p_{ki}≤2` 两行，C 只加 `Σ_i state_{i,1}≤4`；目标统一 `max Σ_i state_{i,1}`。原始矩阵签名逐臂相等，新增行之前的每条原行还作逐项相等比较。源 writer 的 `Y_i+Σ_k p_{ki}−Σ_k d_{ki}=2`、`Σ_y state_{iy}=1`、`Y_i−state_{i1}−2state_{i2}=0` 与脚本的新行身份 gate 一致；`p_{ki}` 的整数 `[0,2]`、`d_{ki}` 的整数 `[0,0]`、state 的 binary `[0,1]` 同实际固定输入域。于是 B 行在此 LP 中代数蕴含 C 行；若 A>4 而 B/C≤4，是逐车处理时间取整族的缺口，不是独特 B3 增益。真实完整 LP 是否存在这种点，仍无证据。

每臂保存完整 primal、每条原/新行活动残差、每变量上下界残差与数值 allowance、原 F/G/P、取量/状态、求解器参数/状态/Work/迭代、读取和序列化成本。只有三臂均为 Gurobi `OPTIMAL` 且原行/界残差在其未改变的容差加舍入余量内时，才作该固定 LP 的**数值**最优比较；`certified` 状态不是有理原对偶证明，临界 4 需报告余量。非最优、无 primal、残差不合格或身份漂移不得当作增界。初版遗漏的 drop 零域与结构行 gate 已补；截止前置 catch 也已修为逾限 unknown。

脚本内部从 supervisor 开始共享一个 300 s 单调截止，子进程只获剩余时间，Gurobi 在该计时开始后由子进程导入；没有每臂固定预算或自动重试。该计时不覆盖 supervisor 解释器启动和父进程结束收据，因此**真实 A/B/C 执行须有 root 绑定的发射至退出 300 s 外部进程树 watchdog 与完整成本收据**，逾限全项 unknown。修订 handoff 已将此列为执行门槛。没有该门或零 Optimize 导出身份资格，不可运行三臂。该诊断不构成生产切割或统一求解性能候选。
