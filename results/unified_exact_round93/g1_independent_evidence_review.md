# R93 隔离 G1 独立收据复核

结论：**G1 PASS，仅限隔离构建与微测资格；不是固定见证 G2 或正式 ENS-C 性能结果。** 我未执行构建、C++ 测试、原生诊断、Optimize 或 Git；仅独立读取日志并用 `Get-FileHash -Algorithm SHA256` 重算实际文件。

工作目录 `E:/codes/ExactEBRP`。按 `g1_identity_manifest.json` 重算共 **21** 项：13 个源码文件、4 个构件、`CMakeCache.txt`、3 个完整阶段日志，逐项与清单匹配，零缺失、零哈希差异。五个新 R93/CMake 受审源码哈希与 `math_source_static_review.md` 的静审 PASS 身份一致；其中 driver 二进制 SHA256 为 `fa67457fcb80a6b385b147bd6fda96c83593c106f8da75b471243d4bd2331c8c`，微测二进制为 `001d28106ecc91a18c0a7a97b0325c07f7b6a460b5b4d6afd88a18a73aedff0c`。全部身份、命令、工具链与逐项哈希以 [g1_identity_manifest.json](g1_identity_manifest.json) 为准。

日志显示 configure、只指定 `Round93CoQuantityTests` 和 `Round93CoQuantityDiagnostic` 两个隔离目标的 build、以及 `ctest -R ^Round93CoQuantityTests$ --output-on-failure` 各一次，三个退出码均为 0；微测 **1/1 passed**。清单记录 configure 外层 **2.9311226 s**，ctest 外层 **0.6530438 s**、内部 **0.20 s**。build 首次工具调用等待 **30.0070009 s** 时仍为 live session，随后完成轮询才观察到退出码 0；完整 build launch-to-exit 墙钟**未精确记录，不能把 30.0070009 s 称作完整成本**。构建日志含旧 core 的编译警告，未见 R93 编译错误。清单明确 `optimize_calls=0`、`real_fixed_witness_diagnostics=0`、`production_algorithm_connected=false`；这些是提交者记录，与上述日志一致但不能由一次 ctest 推断真实实例表现。

结论范围：哈希证明当前落盘字节等于 G1 清单所记，日志证明该身份的隔离构建/微测返回成功。之后任一源码、构件或日志变动须重算相应身份；G2 尚需单独准入、固定见证身份与完整外层费用审计。

独立审查会话日志：`C:/Users/Administrator/.codex/sessions/2026/09/28/rollout-2026-09-28T12-55-39-01a0e65e-5f9f-7b92-9e7b-975d53f9cc35.jsonl`。
