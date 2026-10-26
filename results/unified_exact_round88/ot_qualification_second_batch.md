# Round 88 OT 第二批固定 LP：零求解准备

状态：**已准备，未获本批 Optimize 许可**。冻结的 `round88_ot_math.py`、`round88_ot_diagnostic.py`、`round88_ot_supervise.py` 及原 12 项微型资格不变；本批未编辑工具、构建 C++、复制旧模型或启动 Optimize。唯一待批顺序和原样命令在 `ot_second_batch_preregistration.json`，SHA256 `7320ccf28b60bdffb3b58e7a60a51e4c28d758749c857b4dbbacf3233ae9cb02`。两目标输出目录目前均不存在，正式启动前还需重验哈希和独占资源。

| 预定顺序 | R87 原始 LP 与来源 | 实际 `G` 域；构建时 cutoff | 零 Optimize audit manifest SHA256 | 结构规模与审计 |
| --- | --- | --- | --- | --- |
| 1. F2 ENS-C L0 | `07_F2_ENS-C/external/models/L0.lp`，LP SHA `a37e2165fb900bb0d26d9158b89ade883202049456b7d1c6180f361070638091`；R87 `package_index.json` 同值 | `[0,0.885348300934578]`；`0.885348300934578` | `d223756f601a5f9c1966e5087e6ddace81bcf1b53130afdad2bb79366421b905` | 3,488 列、9,269 行、52,879 非零元；1,776 条必需行核对，0.110 秒 |
| 2. D7 ENS-C L0.0 | `03_D7_ENS-C/external/models/L0.0.lp`，LP SHA `27cbb486939374c3f42eb7f1e97cd6ed20281b114115118c89434fa00e85c77f`；R87 `package_index.json` 同值 | `[0,0.14572448675212263]`；父模型原 cutoff `0.29144897350424526` | `e73e08318afe65d9c4d145f2dd8efe8732783b11e0628f347434b4093c2f09fd` | 25,943 列、104,726 行、724,951 非零元；5,616 条必需行核对，1.264 秒 |

F2 在 R87 `paper_leaf_ledger.csv` 中是深度 0 的根叶，整次 ENS-C 运行给出 `optimal` 证书。其 ledger 端点文本为 `0.88534830093457795`，与 LP 解析后的双精度 `0.885348300934578` 相同；切口只采用 LP 实际双精度界。F2 后来完成时的 UB `0.8659435203229894` 不是根 LP 构建时的 cutoff。输入 SHA `ebdf99e77dc9dcc57946970fa6d7e1cdf2defdcd277562a454d4889c716b645e` 与 R87 协议一致，场景 `T=3600`、`lambda=0.15`、取放各 60 秒。详见 `ot_qualification_f2_l0_audit/source_meta.json` 和同目录 manifest。

D7 的 `L0.0` 确实存在，是 `L0` 的左侧深度 1 **试探子域**，`lp_status_ledger.csv` 与 `paper_optimize_ledger.csv` 均记 LP 最优，`parent_child_bound_ledger.csv` 和 `c6_split_decision_ledger.csv` 则记“无严格子界增益，保留父域覆盖”。因此它不是最终 `paper_leaf_ledger.csv` 的已保留叶，诊断只针对这份真实保存的同源子域 LP，不能将其结果算作原 R87 认证树中已采纳的子叶收益。该 LP 的 cutoff 仍为 `0.29144897350424526`，不能换成最后改善的 UB `0.2235315457737183`；输入 SHA `d7dbd018331b9d5f3d84c0fd6c907560ef1fa92a2f8c153ac7d81e46a6cd4e9c`。详见 `ot_qualification_d7_l00_audit/source_meta.json` 和同目录 manifest。

两次审计均只调用 `gp.read` 和结构核对，LP/input 哈希、真实 G 边界、onehot/透视/zprod/Y/r/h/Gini/cutoff 与目标均通过。预注册每个 LP 从一个固定 `x0` 生成 B1、B2、合并、aggregate 四臂，加 base 共最多五次 Optimize；每个独立诊断进程统一 120 秒硬墙钟，顺序运行 F2 后 D7 子域，超时标 `unknown` 并保留全部原始文件和已耗成本，不自动重试或扩时。F2 较小、D7 子域与首轮根同规模，但真实求解时间和违背/界变化尚未知；固定 LP 结果仅用于机制诊断，不等同完整 ENS 认证提速。
