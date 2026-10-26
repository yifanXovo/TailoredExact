# R94 zero-Optimize prepare：独立审查

**结论：PASS，仅限 prepare。** 我只读核查了预注册、实际 `identity.json`、166 条冻结源码快照、`preflight.json`、外层收据和当前 R90 二进制；未启动资格或正式进程，也未调用 Optimize。`require_prepared` 对实际身份文件重新展开并逐项比较了 4 条资格、12 条正式命令，返回通过。此结论不授权随后 4 次资格 Optimize 或 12 次正式运行；两者仍需 root 各自的租约。

实际文件 SHA-256：runner `5dcb3e481aef4767ee16372ef3c095c88dd36e8635e10b1184edba8669cbc587`，预注册 `767b8abe628bb5e84c8c44ddf2b65869f44212e17bea362fc0284b4afb445774`，身份 `295777d61db71e084e1822295c8fa588cc9732d747f57abc4ebd454053ba0066`，源码快照 `7919085ca84ae9e41b309d27d72e6daf9d1309dc938e39b8cfded2f0dc8a285d`，preflight `4e5ebef8a9f4509e61b79854c2a31dd06cc631a53df97b4ca8da129139506d8b`，外层收据 `bbd3ce4df21334301eb8e6869f464902e370ed268a1f154b546b4c998d9803e2`。身份绑定当前二进制 SHA `bac65ff3b5b099852f2eedd7ef462ad700e5c1131778bd56dca310b3dd0af2f2`，与独立读取的文件字节相符。源码快照有 166 个唯一路径，逐条 expected/actual SHA 相等；当前源码与输入等冻结约束由只读 `require_prepared` 再验证。

我另外从身份文件逐条解析 16 条实际命令：正式顺序为 F2 的 P/ENS/LP、C20 的 LP/ENS/P、B50 的 ENS/P/LP、U6 的 LP/P/ENS；上限分别为 900/600/1800/1200 秒，12 次上限合计 13,500 秒。所有正式臂的 native time-limit 是 cap−6、process wall 是 cap、shutdown margin 是 3；线程、MIP 线程、seed、presolve 和实例参数均与预注册一致。四条资格命令均是对应实例的 P-GRB，外层各限 15 秒，三个内层时间参数均为 0，明确各预期一次 native Optimize 且不计入正式比较。16 个结果目录互不重叠。

P 命令均为 `--method gurobi --plain-baseline`，输出 compact 模型，Round24 指纹逐实例匹配、两个 executable SHA 参数同时指向冻结 R90；没有 ENS 预设、LP split 或 HGA 启动参数。ENS/LP 命令均为 `gcap-frontier`、Round83 预设、witness audit 与 HGA zero-stop；`--round90-lp-g-split` 对 ENS 为 false、LP 为 true。所有输出、日志和 native journal 均落在本臂独立目录。它们仅是已锁定的启动命令，尚无实际 native 参数回读或模型证书。

外层 PowerShell Stopwatch 在命令真实退出时记录 **1.066536 秒，exit 0**；工具传输计时 1.2278775 秒，preflight 写收据前内部采样 0.9797938 秒，后两者不作为完整 prepare wall。外层收据记载资格与正式进程均为 0；campaign 目录只有三份 prepare 产物，没有原始试跑目录。只读审查使用毫秒级 Python 导入、哈希和命令解析；首次审查脚本的最终摘要打印用了错误的外层收据字段名而报 `KeyError`，此前全部核验断言已通过，随后读取正确字段并独立运行 `require_prepared` 成功。这是审查脚本输出错误，不是 prepare 失败；没有为此启动 native 进程。
