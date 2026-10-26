# Round89 native B1 G3 rest 早停独立审查

**结论：D3 配对出现可信的严重负面性能信号；建议按预注册早停停放当前 native B1 候选，不自动续跑剩余十臂。** 这是一个完整配对实例的观察，不是跨实例已证实的普遍回退，也不能把差额全部归因于 cut 本身。本次只读既有收据、结果与小型 Optimize ledger，未重跑或修改求解配置。

两臂均使用 commit `946cec5e61643964b9aa8122700e041615e67b56` 的同一可执行文件 SHA-256 `8d5f0ad4a3cf588875a6a3b8ac67c5bdbb2b2df54a5fd49bea56de2034a17e8d`、同一 D3 输入 SHA-256 `29e0ca2c95ec2e061aa1cc524aaf6a41bf6c4a34355dca86df6966aa8a29b6b4` 与同一历史 canonical P 祖先 SHA `e9e2fae0b045a3e244047ac79b2afbeafcbf3486464f5fd0567317bf6e7f838b`。命令的 λ、T=2850、取送各60秒、线程1、seed0、presolve−1、594秒 solver time、600秒整进程 cap 相同；基线 `--round89-native-ot-b1 false` 为 R83 ENS-C preset，候选 true 为 Round89 preset，`option_audit_consistent=true`。两边终端 L0 MIP 的 canonical 模型字节 SHA 均为 `66e5027dc8cff64e0e62c001dd0d233831d4cb3812b1e75c97759f4bb36dca70`。两臂正常返回、原问题 verifier 的 depot/唯一站/载重/库存/时长/目标核对全真且无错误；最终相同物理 U=`0.04500155005562836`，全域根及父子覆盖、闭合、叶界门禁通过，开放叶0，数值 L 分别为 `0.04500155005562838` 与 `0.045001550055627795`，均在原 `1e−7` 证书门禁内。`runner_cross_arm_D3.json` 也仅做原问题矛盾检查，未拼接证书。

| D3 同代臂 | 整进程墙钟 | 终端 MIP runtime | 终端 MIP Work | 节点 | simplex 迭代 |
|---|---:|---:|---:|---:|---:|
| ENS-C | 155.391 s | 154.282 s | 216.499 | 18,229 | 2,214,579 |
| native B1 | 299.828 s | 298.668 s | 429.367 | 29,271 | 4,359,135 |

候选整进程为基线约 `1.93×`，终端 Work 约 `1.98×`、节点约 `1.61×`、迭代约 `1.97×`；两臂根松弛同为 `0.02834812`，前期三个 LP 与 child-target MIP 的 Work 近同。严重差异集中在相同 L0 的终端证明 MIP，不能仅用主机计时噪声解释。候选的两份 B1 摘要分别唯一 join 到 ledger 的 child-target 与 terminal 行，`PreCrush=1`、实读 `FeasibilityTol=1e−6`、审计180行/66对且 canonical SHA 匹配；child-target 为合法零 MIPNODE/零提交，terminal 为29,287 MIPNODE、1,168,398站对检查、21,772可靠行及 API 成功提交、零数值跳过。Gurobi 日志汇总 `User: 779`；API 成功数不等于永久保留行数或增界因果量。B1 setup=`0.0100`秒、回调=`15.861`秒，相比约 `144.44` 秒的整进程增量，显式回调耗时只解释小部分；更大的 Work/搜索树变化与额外求解负担一致，但单对不能分辨 cut、`PreCrush` 与求解路径扰动各自贡献。

rest 命令仅调用一次，因预注册 `severe_certification_time_signal` 以 exit 1 停在 2/12；这是受控研究早停，不是任一 D3 臂求解失败。两臂均完整认证，没有删失的 D3 终点；其余十臂没有 Round89 观测，不能按失败或成功计。外层完整墙钟 `456.1180496` 秒，内层两个进程合计 `455.219` 秒，应采用外层成本且不重复相加。旧 Round88 D3 约153.797秒仅是非配对历史背景，不能混作当代第三臂。对保守的不晋级决策无需付费重复；若未来要主张一般性能回退或拆解因果，才需另行设计并授权配对重复，当前证据不足以作该主张。
