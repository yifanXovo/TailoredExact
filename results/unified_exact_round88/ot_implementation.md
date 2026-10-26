# Round 88 OT 独立诊断实现（冻结待审）

此工具只比较同一份冻结 ENS-C 真实 VD-P LP 的松弛。`scripts/round88_ot_math.py` 用 `Fraction` 构造 B1、叶局部 B2 和全站 aggregate 的精确系数；`scripts/round88_ot_diagnostic.py audit` 只读 LP，`diagnose` 才调用 Gurobi Optimize；`scripts/round88_ot_supervise.py` 对整个 `diagnose` 子进程施加一次外部墙钟截止。没有接入正式 ENS 算法，也没有实例/时间/Work 选型或迭代闭合。

## 模型与行

对每对 `i<j`，令比率支持 `y/D_i` 的相邻间距为 `Δ`、CDF 差为 `A`、透视 CDF 差为 `B`。B1 行为 `h_ij ≥ ΣΔ αA`，`α=sign(A)`；正宽 `w=b−a` 的 B2 行为 `w h_ij ≥ ΣΔ[(bα−aβ)A+(β−α)B]`，`α=sign(bA−B)`、`β=sign(B−aA)`。`a=b` 只做 B1。aggregate 用所有 pair 的同一点符号行相加，再用真实 Gini 行替换 `Σh`，得到 `n w Σ_i zprod_i/D_i ≥ Σ pair RHS_B2`（等域版本用 B1）。它是独立诊断臂，不删除 pair 行，也不宣称 polytope hull。

`audit` 必须读原始 LP 的 SHA、输入 SHA 和声明的 `a,b,lambda,cutoff`，核对 `Minimize G+lambda Σw_i e_i`、`G`/selector/透视/zprod/Y/r/h 的类型与边界，以及 onehot、`Y=Σys`、`r=Y/D`、`Σq=G`、`a s≤q≤b s`、`zprod=Σyq`、`h≥±(r_i−r_j)`、Gini 与 cutoff 的真实线性行。声明的 gamma 经双精度解析后必须与 LP 的真实 `G` 上下界严格相等；所有局部切口最终以真实双精度边界的 `Fraction.from_float` 精确值构造，防止近似比较把较窄声明域误用于较宽 LP。保存全部库存支持、目标 `D_i`、行列非零元和指纹。`source_sha256`、二进制、场景、叶 ID 等 CLI 参数是操作者的来源声明；LP 和输入的内容与哈希可独立核验，历史来源仍须对照 R87 package_index、叶账本和运行收据。

`diagnose` 重验资产和结构，`relax()` 原 LP 全部整数列，只求一次 base 最优点 `x0`。完整逐列 primal、全基础行残差和变量界残差分别落盘；残差超过 `1e−5` 则停止。全部 pair 和 aggregate 在同一 `x0` 取符号、系数、未归一化及归一化违背；只选数值可靠的正违背行。守门使用 `max(1e−6, 10×基础最大残差×归一化系数 L1 + 128ε×归一化活动 L1)`，并拒绝大于 `1e8` 的归一化单项系数；这尤其避免窄区间把容差噪声当作切口。所选行从同一个 `base` 分别复制形成 B1、B2、B1+B2、aggregate 四臂；重复的归一化行在合并臂去重。每臂独立求解，不根据前一臂新点取符号。

`fixed_point_rows.jsonl` 保存全系数的有理串、符号、支持/叶指纹、行签名、残差及拒绝原因。`result.json` 保存每臂目标、状态、Work、求解墙钟、行列非零元、模型复制/加行成本及累计进程峰值工作集；只有四臂均最优（`a=b` 时 B2 为不适用）才标记目标可比，否则总状态为 `partial_unknown_one_round`，不可排序下界。`audit_timing.json`、`diagnose_timing.json` 和外层 `supervision.json` 分别给出单独审计、诊断全进程及包括硬停止的墙钟；`shared_plus_arm_component_seconds` 仅是共享准备与该臂增量之和，不声称五臂单独并行完整运行。独立审计若是每次必须重复的步骤，应与每臂成本相加报告。

## 环境与命令

局部环境为 `build/research/round88-ot/venv/Scripts/python.exe`，来自捆绑 Python 3.12.14，仅在该 venv 安装 `gurobipy==13.0.2`；全局 Python 未改。先运行以下零求解资格：

```powershell
& .\build\research\round88-ot\venv\Scripts\python.exe -m unittest discover -s tests -p 'round88_ot*_test.py' -v
& .\build\research\round88-ot\venv\Scripts\python.exe scripts/round88_ot_diagnostic.py audit --help
```

真实审计的完整 D7 参数和已生成 manifest 见 `ot_qualification_d7_audit_v4/manifest.json`。PowerShell 中传给 `audit` 的 `--gamma-l/u` 必须作为引号包围的字符串传递，以免 shell 先行舍入十进制端点。独立审查及唯一 solver 时段许可后，才可用如下**尚未执行**命令运行真实 LP；整个子进程从启动前同一时钟计算 120 秒截止，超时 `supervision.json` 标记 `unknown_whole_process_deadline`，并核对启动前后 manifest SHA 与诊断结果所记 SHA，不能把未知状态当作算法失败或负面切口结果：

```powershell
& .\build\research\round88-ot\venv\Scripts\python.exe scripts/round88_ot_supervise.py --manifest results/unified_exact_round88/ot_qualification_d7_audit_v4/manifest.json --out-dir results/unified_exact_round88/ot_d7_diagnostic_001 --whole-process-limit-seconds 120
```

同型根/叶输入须先从 R87 归档取得 LP、原始实例、叶 ledger 和构建时 cutoff；不得用最终改善后的 UB 替换原 LP cutoff，不得用 Round50 模型或整数 witness 冒充 `x0`。Gurobi 设置为 13.0.2、Threads 1、Seed 0、Presolve Auto、FeasibilityTol/OptimalityTol 各 `1e−6`；不修改求解器容差和原 LP 其他行。正式算法的性能和证书仍需单独全程验证。
