# Round 60 模型身份

Round 60 将 stable `paper-k1-am-sf` 与固定区间实验入口共用的 F0 开关集中到
`configurePaperK1AmSfCanonicalF0`，并在单元测试中逐项比较。新增 HGA 发布、
候选 DRY/INJECT、固定库存和 Single-H 都默认关闭；正式 `paper-k1-am-sf` 与
plain P-GRB 没有自动启用 Round 60 行为。

同一输入、T、handling 和空状态下，Round 60 与 Round 59 的 canonical LP
逐字节相同：

| ID | T | SHA-256 | 字节相同 |
|---|---:|---|---|
| D2 | 18000 | `01eb80f6b68d69ad44578e339376bed2d11be5ac41c747b36d1cb2a99ff5fedc` | true |
| D3 | 2850 | `66d0428e14ffd3e31764d324d6cd00d23f2eb3b3053d77f32178df87d7f630e5` | true |
| D4 | 2400 | `33e165ce2552c44f0787b696542f57aeee981aa404a3f93c70d0feb926ae2601` | true |

完整机器记录见 `build_identity_comparison.json`。最终交付二进制 SHA-256 为：

* `ExactEBRP.exe`: `f41af6fe368a2808b5713c5b8db2de151365bbb273c425dae73b88ca9edd65a9`
* `Round50IntervalMipExperiment.exe`: `363c85ffe71918d7a793109f46729d564c79b7a142926a76c4af0eeea6e5edf5`

固定 F0 与 600 秒原生注入配对使用 Round50 hash
`fdb9cf61838aaff0b2a3354ea562eeb094e01a614d6d43e0e529746cf8aaaeee`；
HGA、split 和 D1/C1 完整集成配对使用 ExactEBRP hash
`f1651345f95ab8e95274b332d8d925130ce6235723833cdabb2c12f953b0154a`。
代码审计随后补齐 partial-target 接线、日志失败回退、完整线性行计数和元数据；
final-build C2 配对与第六个 native micro 分别使用上述最终交付 hash。每一组匹配配对
内部始终使用完全相同的可执行文件。所有构建与运行分段见 `build_ledger.json`。
