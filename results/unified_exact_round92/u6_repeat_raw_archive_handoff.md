# R92 U6 seed1/2 四臂原始证据归档交接

已按 root 签署决定恰好执行 plan→check→build 各一次，三条子进程均 exit 0，无修复/重试。仅保存 seed1/2 新 raw 四目录；G3 seed0 的 `11_U6_H-ACT`、`12_U6_ENS-C` 只作比较引用，绝未重复打包。四臂均为正常完成但截止未认证的 open 端点，归档不改变删失或独立审查结论。

| 项目 | 结果 |
|---|---:|
| 已付源组／包 | 4／12 |
| 唯一源成员／stream 核验成员 | 1,122／1,122 |
| 源字节／stream 核验字节 | 342,317,694／342,317,694 |
| 压缩包总字节 | 50,609,166 |
| 最大单包 | 5,002,740 B（严格小于45 MiB） |

adapter SHA256 `0acabefe5303a3d06e0b507302d9c1bca8252bad5042367740be351d233aa573`；冻结 R88 kernel SHA256 `d357b232ceb8e14e94cbf9629d57d9f18bc2f60b1b682865042c4cdd622319f0`。plan SHA256 `258e71bfb09b574adb4fa094c6b295029cdf1bbce699fa0cb4c1564a0cd31c7d`；check `1084b1f02f531cb069508a2f3882a8802585dd6306d07f00258ac8c117e931fb`；index `2ee16092289aafdd3773e05c1d3a2f7d482196747ffc37a44188202d76f12dca`。每份包在源 SHA/size 记录后已由实际 tar stream 逐 member 读取并验 SHA/size；每包 SHA 与字节数如下，供 root 独立检查。

| 包 | bytes | SHA256 |
|---|---:|---|
| `runner_u6_repeat_raw_archives/seed_1_01_U6_ENS-C.part01-of-03.tar.gz` | 5,000,741 | `79799b6e1d3c7c5025d2707de33067f225af226a43bdbde7c6aaf310c67a77b4` |
| `runner_u6_repeat_raw_archives/seed_1_01_U6_ENS-C.part02-of-03.tar.gz` | 4,987,878 | `bb1a728bc02c57085f5c7743519db4362f087ebcbb27ee6fbb4ff740d1c57d97` |
| `runner_u6_repeat_raw_archives/seed_1_01_U6_ENS-C.part03-of-03.tar.gz` | 2,660,600 | `c8520668eb7f2e17fb3e0b615c1de5d427166b8904a63d0000f08c1de6c3ab76` |
| `runner_u6_repeat_raw_archives/seed_1_02_U6_H-ACT.part01-of-03.tar.gz` | 5,002,382 | `4922d85f6737ac232467c4cbba950b8f0e93e0350b50454c203ba7fd5f5bdcab` |
| `runner_u6_repeat_raw_archives/seed_1_02_U6_H-ACT.part02-of-03.tar.gz` | 4,989,782 | `5676f41f949fa25d944fc22675542b91d2339875302563e34168b46eb286be65` |
| `runner_u6_repeat_raw_archives/seed_1_02_U6_H-ACT.part03-of-03.tar.gz` | 2,666,544 | `55de46dc5f170f65c2080bc448d01106655d2f30b39e7d3e3c62a1cbf615adb8` |
| `runner_u6_repeat_raw_archives/seed_2_01_U6_H-ACT.part01-of-03.tar.gz` | 5,002,740 | `ffda8f9a61d746aafa05550353c4900cdae45bd843e00dff3c3eb803a27127ee` |
| `runner_u6_repeat_raw_archives/seed_2_01_U6_H-ACT.part02-of-03.tar.gz` | 4,989,782 | `3b5ec72f07525b20d88407d131cbb05ff865692eb56b2f56c72aa98cdc6a05bb` |
| `runner_u6_repeat_raw_archives/seed_2_01_U6_H-ACT.part03-of-03.tar.gz` | 2,656,442 | `8f324aabc8df97e1fb08646101af0b9277205db3867309444e01dd4f81a55c5c` |
| `runner_u6_repeat_raw_archives/seed_2_02_U6_ENS-C.part01-of-03.tar.gz` | 5,000,851 | `543e1e80cc908a96b055795deaf03bbebd026a8b42af20d62ab213971164a32c` |
| `runner_u6_repeat_raw_archives/seed_2_02_U6_ENS-C.part02-of-03.tar.gz` | 4,987,876 | `70c6887fd8ee0ed2d8087a21bacf67c98158f9c189eae282a3cee20ac46f64af` |
| `runner_u6_repeat_raw_archives/seed_2_02_U6_ENS-C.part03-of-03.tar.gz` | 2,663,548 | `92457deeb3a2ae6d8a7f05e526b801fd8952383ea2489f5564dd08c140e3afe5` |

外层完整命令墙钟：plan `0.617671 s`、check `0.476295 s`、build `23.313550 s`，合计 `24.407516 s`。build 的索引写前内部墙钟 `22.785606 s`；其中源 SHA `0.759889 s`、压缩 `20.913374 s`、包 SHA `0.094923 s`、stream 验真 `1.014143 s`，均嵌在 build 外层，不能二次相加。三组 started/stdout/stderr/receipt 保存原始命令、exit、时钟；报告整理和轻量进程检查没有完整外层计时收据，不计零也不混入归档命令成本。

归档完成后 OS 检查无 ExactEBRP/Gurobi/build/本归档器 Python 残留，计算/I-O 槽已释放。四个原 raw 目录均保留，未运行求解。独立四臂小证据验收 [u6_repeat_independent_evidence_review.md](u6_repeat_independent_evidence_review.md) 已写 PASS，结论只为预注册风险未复现、H-ACT 不晋升；归档不延伸其数学或性能结论。

精确 staging 清单见 [u6_repeat_raw_archive_git_paths.json](u6_repeat_raw_archive_git_paths.json)：regular 小文件与包逐项列出，三个 raw 前缀明确排除。没有失败归档收据；root 独立抽核包 hash/size 后才提交。
