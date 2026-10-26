# R92 G3 十二臂原始证据归档交接

已按根签署的有限决定恰好执行 plan → check → build 各一次，均 exit 0。plan 核定十二个已付 raw 目录、唯一成员与固定顺序；F5 ENS-C/H-ACT、F6 H-ACT/ENS-C 四臂未运行。rest exit 1 仅为 U6 已审计 `severe_open_gap_signal` 研究停批，没有新求解失败或补跑。全部原 `runner_handling_g3/raw/01..12` 保留，不平铺入 Git。

| 指标 | 实际 |
|---|---:|
| 已付源组 | 12 |
| 唯一源文件／stream 验真文件 | 13290／13290 |
| 原始／stream 验真字节 | 300,719,141／300,719,141 |
| 归档包数／总字节 | 18／44,921,834 |
| 最大单包 | 5,029,383 B（严格低于 45 MiB） |

冻结适配器 SHA256 `fa4da22b33ca877bea64fd33c3c5bf199981b3e86a52696f088f383bceb09735`；冻结 R88 kernel SHA256 `d357b232ceb8e14e94cbf9629d57d9f18bc2f60b1b682865042c4cdd622319f0`。plan SHA256 `4559793de244ac727d94e92e8980173190ef3f8bc1b198c9329c5012bfc4291a`；check SHA256 `4c4a819ee058a98bb96535f8ba606396a27599da6fa38f4c15049ae50af69be1`；index SHA256 `ee66e221fda1314c341c4854874e88afde64575d051705649affa8d77bb60c79`。每包源 SHA/size 和 tar 成员的实际流式 SHA/size 对齐；包自身 SHA/size 如下，根可独立抽核。

| 包 | bytes | SHA256 |
|---|---:|---|
| `runner_handling_g3_raw_archives/01_E8_ENS-C.tar.gz` | 287,148 | `4e6ee309798a12b93682ae13d58d2ddfa5a44078f8aa0e7d6bf3a8bb316e1281` |
| `runner_handling_g3_raw_archives/02_E8_H-ACT.tar.gz` | 280,667 | `04b19150493adf55766af77aae30bb95cbd1e623776c200295b45450a3f789c5` |
| `runner_handling_g3_raw_archives/03_S12_H-ACT.tar.gz` | 166,389 | `bd167e81ef8357aac55f8f2f93a98a27c8fd472ab3858a2227e7f7bd1ad05ddd` |
| `runner_handling_g3_raw_archives/04_S12_ENS-C.tar.gz` | 174,361 | `77883956f02213ea4758a8264303e565d715b8a2dd7afbef44610f929f1e2eb6` |
| `runner_handling_g3_raw_archives/05_D3_ENS-C.tar.gz` | 575,645 | `b8b5f8e854073bfdb479980d3f577fdde0d7e4ce8c38d6a84b203c1cafe998ac` |
| `runner_handling_g3_raw_archives/06_D3_H-ACT.tar.gz` | 501,019 | `b55948df5f6e8f8049df8ca02278ef821dec43e52ed2e21b4bca821093d63fb9` |
| `runner_handling_g3_raw_archives/07_C2_H-ACT.tar.gz` | 1,131,202 | `cb26e64b02b5215d1eee0a7320f0452db740a7ff4415cb85338e0b5bc99103fb` |
| `runner_handling_g3_raw_archives/08_C2_ENS-C.tar.gz` | 1,112,454 | `0baa3b1e1b944d6a2324f617571c5ee62597accece651509c7568393fa93bc44` |
| `runner_handling_g3_raw_archives/09_D7_ENS-C.part01-of-02.tar.gz` | 5,028,400 | `61fb4bdc39d6236fc8e684128c421fbd73d742c50f41ad4b44b303d386e1215e` |
| `runner_handling_g3_raw_archives/09_D7_ENS-C.part02-of-02.tar.gz` | 2,667,916 | `3ee7a4e56c02a1aad7963fe852731d255079c2026c25396b47fcb889b798e30b` |
| `runner_handling_g3_raw_archives/10_D7_H-ACT.part01-of-02.tar.gz` | 5,029,383 | `761683b8e6b3592b372ad17aac610ca5e3d1ca99845bc5360df1631f686f9c54` |
| `runner_handling_g3_raw_archives/10_D7_H-ACT.part02-of-02.tar.gz` | 2,665,303 | `1e726f60dfb5151bca365cda961d6cc7e9b36e1ec24125a49765e3c59fee3381` |
| `runner_handling_g3_raw_archives/11_U6_H-ACT.part01-of-03.tar.gz` | 5,002,659 | `e3f32932de3eeee201f1e5735f9d31d7ee49aad828beb47f07ec2a942f93e362` |
| `runner_handling_g3_raw_archives/11_U6_H-ACT.part02-of-03.tar.gz` | 4,989,748 | `fb37484409d08085ded134cabcc73557a34effbe4ffc590603262f97c3d12d95` |
| `runner_handling_g3_raw_archives/11_U6_H-ACT.part03-of-03.tar.gz` | 2,659,559 | `1163540d82b35dfedf460bfb78cf0f137345ec1465a1d16b21c14338ee4b80ed` |
| `runner_handling_g3_raw_archives/12_U6_ENS-C.part01-of-03.tar.gz` | 5,000,683 | `5096ff58e5c745cc767715e4423dbf4723f4c32428592fc402ff617789cd5867` |
| `runner_handling_g3_raw_archives/12_U6_ENS-C.part02-of-03.tar.gz` | 4,987,830 | `c075a44246d2d6ea974c4df70d26f8702a314a7179b471d0e32c90448cb5c6f6` |
| `runner_handling_g3_raw_archives/12_U6_ENS-C.part03-of-03.tar.gz` | 2,661,468 | `69a77673c91e16b03a221061d2ae424d580986ff21289b1f8bf47c54029e7874` |

外层完整命令墙钟：plan `2.527264 s`，check `1.907134 s`，build `73.513071 s`，合计 `77.947470 s`。三份原始 started/stdout/stderr/receipt 均保留；build 里计入索引写入前 `71.517645 s`。build 内嵌分解：源 SHA `50.241272 s`、压缩 `19.451388 s`、包 SHA `0.118461 s`、stream 验真 `1.698047 s`，属于 build 外层成本内部，不再次相加。命令结束后的本交接整理与轻量进程核查未有完整外层计时收据，不计零也不混入归档算法墙钟。

完成后进程检查：无 ExactEBRP/Gurobi/build/该归档器 Python 残留，计算/I-O 槽明确释放。没有运行 solver、build 或 U6 seed 复核。

精确 Git 清单在 `g3_raw_archive_git_paths.json`：53 个 regular 小文件、18 个包，含 plan/check/index、三组外层收据与已有 smoke/rest 证据；`runner_handling_g3/raw/` 显式排除。根只需按 JSON 中逐项 staging，未产生失败收据。归档是无损保存，不代表 H-ACT 晋升或 U6 性能结论。
