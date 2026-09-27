# C2 finite seed repeat：独立证据验收

只读核查修订后的 `c2_repeat_report.md` SHA256 `a3f2bbceb66c9463a71dddf0c751d68ffd06c5f83f065b123e9f5570b8cfbf6d`、冻结 prereg/identity/lease、四条 summary、各 raw 的 launch/completion/audit/native readback、两份 cross-arm、outer/postflight 与原 seed-0 G3 收据；未重跑、求解、构建或归档。**四条新增进程臂的身份、物理可行性和数值证书审计通过，可作为有限 C2 波动复核；不支持晋级 LP-G。**

新批次仅 `seed_1/raw/01_C2_ENS-C,02_C2_LP-G` 和 `seed_2/raw/01_C2_LP-G,02_C2_ENS-C` 四目录、summary 四条，均 returncode 0、`normal_return`、600 s cap 内、原物理路线合格、audit 和最终原问题证书通过。四条命令分别读回原 Seed 1/2，Threads 1、Presolve −1 和对应 Round83 ENS-C/Round90 LP-G preset；同一输入、二进制 `bac65ff3b5b099852f2eedd7ef462ad700e5c1131778bd56dca310b3dd0af2f2`、七份 source 与冻结 runner/参数。两份同 seed 的原问题 L/U 交叉矛盾检查通过；LP-G 每条三次合格提案、两次实际原子双子分裂，ENS-C 开关关闭。`run_completion` 为 completed=4/error=null/failed_attempt_costs=[]，无失败或 risk 文件，outer 收据 `no_retry=true`，postflight 无残留 solver/lock。原 seed-0 G3 对由新 prereg 固定原 summary、cross-arm 与两臂 raw SHA，preflight 确认已证书且未重跑。

由原始 process wall 重算 LP-G/ENS-C 比值：seed 0 为 `112.141/123.813=0.9057288006893817`，seed 1 为 `99.859/141.610=0.7051691264726901`，seed 2 为 `151.703/136.469=1.111629747416386`；中位数 `0.9057288006893817`。三对均有物理 U≈`0.8299634131717752` 与数值 L 达原终止容差，未截尾。预定的“两对方向有利且中位数<1”满足，因此**仅支持继续先做 D6/F2 等已规划保护筛选**；seed 2 明确反向，不能称所有 seed 加速、稳健统计显著或统一优于 P-GRB。

新 `run` 外层发射至退出为 `531.7086207 s`，内部四臂 process wall 合计 `529.641 s`、prelaunch `1.312 s`，剩余外层 `0.7556207 s` 包含已嵌套的离线 audit `0.1428904 s`。单次零 Optimize `prepare` 另计 `0.6492336 s`。outer 结束与 postflight 观察相隔约 `98.88 s`，属后续证据阅读/写报告的墙钟区间，缺单独完整活动计时；已在作者报告披露，既不冒称零成本，也不把整段当作测得 CPU 或算法运行成本与 `run` 相加。上述证书是既定 solver 数值标准与原物理验证，不是有理原对偶证明。
