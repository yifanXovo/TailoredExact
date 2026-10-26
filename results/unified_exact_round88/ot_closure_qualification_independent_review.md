# Round 88 OT 闭包运行资格独立验收

审查范围：只读核对最终测试增补、资格报告、原始命令收据/日志、共享准备 manifest 和三个源的零求解结构审计；本审查未执行测试、脚本或求解。结论限于微型资格与真实原 LP 的身份读模，尚无真实闭包诊断结果。

## 冻结身份

- `scripts/round88_ot_closure.py` SHA256 `129b9224ac36e44b52fcc911604938a024d79986f8bd5fe8a8ffd6b14d1b2934`。
- `tests/round88_ot_closure_test.py` SHA256 `01fc21c9689f956a53adff95430cdd4ddd9bafef7bc5a56593c9d0a91bf43a61`。
- `ot_closure_qualification/preparation/manifest.json` SHA256 `6293e196160ff00e778c43be2275d8b3fe93020c5207f814dac3ce05f2a0db18`。

以上三个哈希已从当前文件独立重算。最终测试增加的 toy 以固定两站 Dirac 库存比率 `0`、`1` 和 `min h` 为独立手算期望：原 LP 最优 `0`，B1 行 `h−state_1_0+state_2_0≥0` 后最优 `1`。测试检查精确违背 `1`、既定可靠余量 `10⁻⁶`，并显式 gated 于 `ROUND88_OT_CLOSURE_TOY_OPTIMIZE=1`；它不是以被测分离器结果自身作为最优值 oracle。

## 原始收据复核

- 首轮普通微测日志为 7/7 通过，最终日志为 8 项中的 7 通过、toy 按预期跳过；两份命令收据 exit code 均为 0。
- 两次单独 toy 日志/收据均为 1/1 通过，每次测试源码有恰好 2 处 `model.optimize()` 调用；合计 **4 次 toy Optimize**，两份 toy LP、求解日志、结果 JSON 均保留。不存在真实 LP toy 化的结果替代。
- F2 root、D7 root、D7 child 三份新审计的 LP SHA、输入 SHA、支持 fingerprint、实际 G 边界及结构均与冻结源记录一致；`source_comparison.json` 的三个 `structure_equal` 为 true。审计入口只读 `gp.read` 并作结构审计，三份原始收据退出码为 0，**真实 LP Optimize 为 0**；没有真实 primal、违背量或闭包界可推断。
- 原始首轮/最终微测、两次 toy、三份审计以及准备收据均留存。本阶段没有真实失败；测试中的返回码 7 是故意模拟的准备失败，并验证写入失败收据。

成本口径：准备命令的完整外层墙钟见 `prepare_command_receipt.json`，为 `0.3251317 s`；嵌套的 `preparation_supervision.json` 从 Python supervisor 启动子进程至退出为 `0.1216253997 s`，不能当完整准备成本重复或替代计算。以完整准备命令和其余七份命令收据相加，已记录外层命令墙钟为 `5.3059186 s`，仍不含人工审查等时间。Root 已根据八份原始收据重新求和并在资格报告中修正，同时留下本次更正记录。

**结论：**微测和零 Optimize 身份审计达到后续由 root 单独授权九臂诊断的资格门槛；不构成九臂已运行、数值闭包已证或正式算法优于基线的证据。成本措辞已修正，当前无未解静态阻断。
