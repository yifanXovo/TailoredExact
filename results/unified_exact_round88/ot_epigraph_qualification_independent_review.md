# Round88 稀疏 OT epigraph 资格收据独立验收

**结论：资格收据一致，无阻断；可供 root 决定是否单独准入六臂真实固定 LP 诊断。** 本次只读原始小型收据、日志、primal、精确新增行和资格 helper；未运行脚本、测试、Gurobi、LP 或求解。验收不等于六臂已执行，也不预判增界、内存或运行时间。

身份：`round88_ot_epigraph.py` SHA-256 `5d49c3fc12cc806a8008e43d756bf9c46810b21e7efc2b64c2383da4624bd7da`，测试 `2be3e3e51333e29fcfa3b52c17f90ce4603603dd2032979191fb96a1624913ab`，资格 helper `ceb04bbc9b2df245df3cd09a9d1b5977ef009b7913768201f0d83e239d39e912`，均与报告、运行身份及现存文件相符。预注册 manifest 的实算 SHA-256 为 `d431b54bf9e3b640e9c49774a10b9ad65680abf695a53388665d719a570a09b1`，状态 `prepared_not_admitted`，检查时 `ot_epigraph_lease.json` 不存在。五项 stage 各有 attempt/receipt，returncode 都为零；目录未显示重试或失败尝试。

无求解测试的原始 stderr 写明 `Ran 8 tests ... OK`，外层 stage 收据为 0.3272459 s；测试源包括独立 Fraction 累计与符号枚举、非比例 q、满前缀 `Q=G`、错误子结果监督收据。toy helper 源中仅 B1、B2 循环各一次 `model.optimize()`；两个原 toy LP 均 10 列/8 行/18 NZ。手算点的 `A=0,B=−1/2,Δ=1,[a,b]=[0,1]` 给 B1 最小 `h=0`、B2 最小 `h=1`。两份 Gurobi 日志各有一次 Optimize，目标分别 0 和 1；primal 中 B1 `h=0`，B2 `h=1,u=v=1/2`，原行/新增行/界最大残差均为零。B1 预测及实际增量均为 3 列/5 行/12 NZ，B2 均为 6 列/9 行/27 NZ；原始与扩展 toy LP、行账本、完整 primal 和残差文件均留存。toy 外层 stage 0.1273013 s，不能把这两次 Optimize 称为零求解资格。

Win32 Job 资格调用生产 `_wait_with_deadline`，用 0.2 s 微型截止测试 Python 子进程及孙进程，无模型/solver。`job_result.json` 记录 timeout、两个 PID 均不存活；外层 job stage 0.4433238 s。三份真实来源的审计 helper 仅 `load_model`、`audit_model`、结构比较与支持计数，未调用 Optimize 或对真实 LP 插入 epigraph 行。`source_comparison.json` 的 LP/input SHA、支持指纹、实际 G 域及结构一致标记覆盖 F2 root、D7 root、D7 historical child；F2 原维度 3488/9269/52879，D7 两域均 25943/104726/724951。其 B1/B2 行列和 NZ 上界只是从完整支持预估，**真实大 LP 的新增矩阵/求解表现仍未验证**。三源审计外层 2.9690132 s。

共享准备完整外层 stage 为 0.2502552 s，内层 prepare 子进程发射至退出为 0.1457236 s，后者已包含在前者中。五 stage 外层合计 4.1171394 s，整个 qualification helper 4.1380760 s，最外 shell/tool 4.416753 s，是嵌套成本口径，不相加。各来源内部审计时间也包含在 audit stage。实际六臂若获准，应按冻结 manifest 各从原 LP 开始并分别记完整 300 s 监督成本，浮点 OPTIMAL 仅按原容差与残差口径解释。
