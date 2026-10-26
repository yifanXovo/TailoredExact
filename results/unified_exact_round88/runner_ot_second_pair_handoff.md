# 第二批 OT 固定 LP 诊断原始证据交接

已把 `ot_f2_l0_diagnostic_001/` 与 `ot_d7_l00_diagnostic_001/` 的全部 26 个原始文件无损封入同一个 `runner_ot_second_pair_raw.tar.gz`。两份原目录仍原地保留；逐文件路径、大小、SHA256 在 `runner_ot_second_pair_raw_index.json`。封包后实际重读 26 个归档成员，逐一与源文件核对字节数和 SHA256，全部一致。包内包括空 stdout/stderr、监督记录、五臂原生 LP 日志、固定点 primal、基础行残差、分离行、结果与诊断计时；没有复制源码、build 或外部 LP。

| 原始目录 | 文件数 | 原字节 | 监督进程墙钟 | 统一 cap | 结果 |
| --- | ---: | ---: | ---: | ---: | --- |
| `ot_f2_l0_diagnostic_001/` | 13 | 3,455,889 | 7.906422 s | 120 s | exit 0，五臂 OPTIMAL |
| `ot_d7_l00_diagnostic_001/` | 13 | 24,835,796 | 70.726194 s | 120 s | exit 0，五臂 OPTIMAL |

归档原字节合计 `28,291,685`，压缩包 `3,455,472` 字节，SHA256 `966ebdd886b735cc10e673f5351b0fa611c88fbe79072d140d4efc89c96d9a42`。各自 `supervision.json` 的 manifest 前后及结果内 SHA 一致。独立先行 LP 身份审计的 manifest 分别为 `ot_qualification_f2_l0_audit/manifest.json`、`ot_qualification_d7_l00_audit/manifest.json`；外部原 LP SHA 分别是 `a37e2165fb900bb0d26d9158b89ade883202049456b7d1c6180f361070638091`、`27cbb486939374c3f42eb7f1e97cd6ed20281b114115118c89434fa00e85c77f`。

真实成本按两个完整诊断进程合计为 `78.632615 s`，各自均低于 120 秒。程序到结果落盘分别 `7.790233 s`、`70.520298 s`。共享准备在**每个进程内仅计一次**：F2 `7.006392 s`，D7 L0.0 `41.789240 s`；各自四个增量臂 marginal 合计 `0.781310 s`、`28.728053 s`，共享加边际与本体计时分别仅差约 `0.00253 s`、`0.00301 s`。五次 LP solver runtime 每进程 `0.835000 s`、`31.604001 s`，已包含在上述进程墙钟内；各臂 `shared_plus_arm_component_seconds` 不可跨臂相加。先行独立 LP 审计另列 `0.110217 s` 与 `1.263657 s`，不归入这两次诊断进程。结果仅属于冻结根/子叶的一轮固定 LP；不是完整 ENS 证书或速度结论。没有启动 A1 rest。
