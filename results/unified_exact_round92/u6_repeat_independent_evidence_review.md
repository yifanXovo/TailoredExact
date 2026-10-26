# Round92 U6 三 seed 固定复核：独立小证据验收

结论：本次四个新臂证据 **PASS**，预注册的 `risk_not_reproduced` 判定成立，但 H-ACT 不获得晋升。四臂都是 1200 s 限额内正常返回的 **open** 端点，均无最终认证；seed 2 的候选绝对 gap 仍更大。按既定有限协议收口，不追加 seed、延长时间、恢复 F5/F6 或改变方法。

审查绑定：`u6_repeat_report.md` SHA256 `81b8b7d24efaf50364a71c8a6c1e6a94dcacaf321ada6c50f23cf2442ba57d4c`，42 项小证据索引 SHA256 `d0a2f486ec66bd40a259a5bacd4e5a215a572b03481545ff7791ea836a70852b`，顶层 outer receipt `1f9281e6b08c7eb9f4b725973d4de2bcd906f93886a6aced29939c068509809e`，四臂 summary `8399b60e00a77a38aaff3a89023f25a8be2c8b0034f5391dd3f8e8c4f96977c0`，三 seed summary `e9c4283172b5489b055904e2a04f9568bd147363bfa57a728fa493aa7a4b4b7c`，同期 postflight `80d81ae03035d08dcd3d11c4b297744993bbd559bd2670a4a2c64178afce068b`。我独立重算了这些小文件的 SHA；未逐项重算索引所列原始结果文件、重放 journal 或读取大型 LP。

四条 launch 的顺序确为 seed 1 ENS-C→H-ACT、seed 2 H-ACT→ENS-C；同一 U6 输入 SHA `1556e893...11787e3f`、同一可执行文件，实际命令仅切换固定 seed、方法开关和输出路径。每臂完整进程 cap 1200 s、native limit 1194 s、硬停 1198 s，实际进程秒依次为 1197.250、1197.172、1197.156、1197.110。四份审计均 `passed=true`，各有 6/6 native calls、物理见证数 16/29/4/26，最终 witness 的原 T 检查通过；跨臂矛盾审计两份均通过，但其 U/L 没有合并为单臂证书。实际 `result.json` 参数读回与适配记录显示 seed requested/effective 依次 1/1/2/2，Threads=1、Presolve=-1、25 个启动 seed；适配先核原始每条 call 的真实 seed 与其它参数，才仅在内存副本投影 Seed=0 给冻结 R86 reader。ENS-C 两臂无候选行账。H-ACT 两臂各五代模型、每代四行、累计二十行及四次缓存命中；小型行账和 Optimize 账本的五个 LP 模型 SHA 逐项相合，终端 MIP 复用对应 L0.0 模型 SHA。两份行账的 B 均为 148、proof version 2；当前 canonical 字节经原审计确认，历史被覆盖模型旧字节未单独归档。

seed 0 仅引用冻结 G3 原两臂，未重跑。三对同为 open，候选减基准 gap 依次为 `+0.014607209974366236`、`−0.004214434998261296`、`+0.008253802196471982`。原联合严重线要求同一 seed 的候选 gap 同时大于 `1.5×` 基准及多于 `0.01`：仅 seed 0 满足，计 `1/3`。两项中位数分别为 `median(gap_H−1.5 gap_ENS)=−0.005984681912724596`、`median(gap_H−gap_ENS)=+0.008253802196471982`，亦未共同过线。因此“seed 0 风险未复现”准确；“无回退”“显著改善”或“已证明最终速度”均不成立。各臂 gap 是截止时未闭合的 U−L；审计中的单独 native-global-bound 字段不能替代正常 result 的 frontier 端点 L。

顶层子进程 exit 0，外层 launch-to-exit `4797.9466449 s`，runner `4797.282400700264 s`，四臂进程合计 `4788.688000000082 s`，包含预检及离线审计的 full-attempt 合计 `4796.90800000075 s`；这些嵌套口径不可相加。准备阶段另计 `1.0021432 s`，seed 0 旧成本不混入本次。completion 记 4/4、失败尝试为空；postflight 同期记录 15 源与 main/core 身份匹配、无残余重进程。该小证据验收支持保守停用当前 H-ACT 候选作为统一方法，保留有效性与局部正例，不对跨实例性能下普遍结论。

附带阅读 `research_handoffs/2026-09-28/OPTIMIZATION_NOTES.md`：排序无并列时的 Gini 梯度与含并列的方向导数公式正确；严格原目标下降结合有限合法整数状态、且每次候选生成终止时，确能排除循环。cover 预案明确要求服务事件变量精确定义及原物理接受域的可靠联合时长下界，所述反证有效。未发现需立即纠正的实质数学错误；这些仍是未实现、未测试的研究预案，不构成新颖性或运行收益证据。
