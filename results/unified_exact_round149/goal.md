/goal

# TailoredExact 下一轮完整任务

## Round149：将惩罚下界反馈到状态乘积松弛——已有信息的有效传播与完整算法价值

**日期：2026-11-03。建议轮次 Round149；编号已占用时沿实际下一轮继续。**

## 0. 目标与执行原则

R148 可以完整验收：共同分母仿射族有效，五个匹配 LP 都提高了优化值；但其“一条根行＋一次追加根 LP”的完整实现使 RB35 的物理 U 恶化约10.58%、signed gap 恶化约29.52%，因此维持研究用途、不晋升。当前没有需要再开一轮处理的重大工程故障。R137 GI-TBC 继续是稳定版本；R147 独立 GD，即 D＝GI-TBC＋GD、STOCK off，继续保留有限统一增强候选定位。

本轮只研究一个明确缺口：**原模型已隐含的惩罚下界，经自身 incumbent cutoff 推出更紧的 Gini 上界后，是否应反馈到 VD-P 状态乘积松弛？这种表达强化能否带来有价值的完整算法收益？**

前置审查已在五个保存 GD LP 点上发现严格分离，并核实标量 G 上界本身已被旧连续模型隐含。生产第一版建议只强化 VD-P 上端行，保留原 proof-root 区间与 AM 几何；不额外求一个根 LP，不同时开展 Shared-S、AM 强制分裂、STOCK/RN 组合或动态 incumbent 重建。

新增实验外层总上限 **18000秒＝5小时**，可提前收束，不要求用满。默认 **Gurobi Seed=0、Threads=1**；H seed 独立固定为 **20260626**。计时运行串行，与编译、重 I/O、PDF 导出错开；完整臂支付自身 H、构造、全部求解和必要验证。沿用现有 R134 证明政策与已通过的数值标准，不为 tiny gap 追求字面零差。

算法保持统一、数学依据明确：不按实例名、规模或已知输赢打补丁，不以运行若干秒切换算法。根据有效界、支持包含、是否实际收紧来省略行是允许的。实验 cap 不是算法切换规则。Codex 可依据观察调整顺序、有限诊断、实现方式和预算分配；目标是论文可解释的实质收益与可接受取舍，不要求逐例最优，也不以局部好结果掩盖重要严重回退。

---

## A. 起点、身份与工作区

| 项目 | 编写时核实的参考 |
|---|---|
| 仓库／前序 PR | yifanXovo/TailoredExact；#210，Open Draft，未合并 |
| R148 branch／head | codex/round148-shared-denominator-gd；c2130a0f3f915d1f6b2f7fcc4c383913db33e47c |
| R148 fixed science | 25765c21d63e7b04133f1e7dbe2dfd53c38f476f |
| R147 head／fixed science | b0481ad63d557b1ec36994a74bfb372793f40d7f；a0673b683c645d35de829fa101a55cc9fc4774c7 |
| R146 fixed science | 8ec2aebe46398485019623d9b18a3e30617d4997 |
| R148 实际生产源码 | d5868014c8868cdc305e6ed798bf0d5c86a1bda9 |
| 现有 PE／SHA256 | E:\codes\ExactEBRP-work\build-cache\round148\ExactEBRP.exe；4beb12f8a3de992691fc4ae229fdaff43e35ef00ce29f9f2bd3cb139af792ac2 |
| Native DLL／SHA256 | D:\gurobi1302\win64\bin\gurobi130.dll；9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88 |
| 编写时 main | b2b940c1e517a72e226ec60fc49ff19651737632 |
| 稳定入口／配置 | scripts/paper_s2.py；config/gi_tbc_round137.json |
| D 入口／配置 | scripts/paper_s2_gd_only.py；config/gi_tbc_gd_round147.json |
| 活动树／新增资产根 | E:\codes\ExactEBRP-work\worktrees\paper-current；E:\codes\ExactEBRP-work |
| 受保护原目录 | E:\codes\ExactEBRP |
| 建议 branch／结果目录 | codex/round149-penalty-product-feedback；results/unified_exact_round149/ |

先读适用 AGENTS.md、WORKSPACE_POLICY.md，检查 refs、用户修改、活动进程、封存 raw 和可复用 PE。main 已吸收所需内容则从实际 main 继续，否则从核实后的 R148 继续并选相应临时 PR base；不等待合并，不机械回退上述 SHA。

载体继续采用完整 own-H、M-B/VD-P、pair-only、AM=.08、depth=8、minimum width=1e-4、AP off、原物理 T 与目标。本轮候选暂称 **D+PF（penalty feedback）**，Shared-S off、STOCK off；名称和入口可以按仓库规范调整。记录生产源码、PE、包装层、科学结果与交付 commit 的各自身份。

---

## B. 已有结论、历史边界与前置证据

### B1. R148 实际完成了什么

| 保存模型位置 | 旧 GD LP | 加一条 Shared-S 后 LP | 增加 |
|---|---:|---:|---:|
| K20 base | .236010302342 | .238279588751 | .002269286408 |
| K20 joint | .239052184675 | .241511748078 | .002459563403 |
| K20 STOCK | .251016109922 | .255570495817 | .004554385894 |
| K35 base | .204187028164 | .209568159043 | .005381130879 |
| RX20 base | .365004645621 | .381636295279 | .016631649658 |

这是三个物理实例上的五个模型，不是五个独立实例。全部是同域重新优化后的增量；新点仍有 Shared-S 分离，不等于已证实继续加行的收益。

四个正式完整臂均为同一 R148 新 PE、Seed0、每臂 cap2400，均未获证：

| 角色 | D 的 U／支持 L／gap% | D+Shared-S 的 U／支持 L／gap% |
|---|---|---|
| K35 | .676798845196／.545729444783／19.366079 | .679917519727／.558283855657／17.889473 |
| RB35-T2 | .335883588950／.219663876370／34.601188 | .371420783400／.220898439927／40.526096 |

K35 是界与 primal 的取舍；RB35 严重回退支持停止当前一行实现，不需要追加 Seed、更多行或剩余 full panel 才能验收。关闭的是这一完整实现，未否定整个仿射族。

总新增外层费用9670.619385001秒，build 45.500213800秒单列；28个 complete/qualification Native call 全部返回，另有5个诊断 LP。资格 reader 曾不能解释两个根 LP，已基于原 producer 修复；closed reentry 与 URL 分隔符问题也已定向处理。不要重跑旧资格或把这些已结问题改造成新的工程任务。

### B2. 不重复历史问题

- R137 已有机制、参数与多角色测试。R147 D 在 K35/RB35 的 U 收益约3.13%/2.54%，但 K20 未获证、K35 的 L 曾下降，不能称为广泛稳健或历史最强。
- K20 的 STOCK／STOCK+GD 约94.261／74.916秒获证仍是强证据。R140 旧 TC+STOCK 的 Seed0 K35 U/L≈.650438712/.5682885263、RB35≈.3190804927/.2339272621，比 D 更好；相关 Seed1 负结果及源码／PE／V2运输差异一并保留，不把它们当作纯 Seed 干预。
- R47 已有 AM 的 eta/mu 研究和调参；R48/R49 的 formulation／primal-dual rescue 已测；R52 更正后是三个严重 false-retain，且存在真正 correct-retain 负锚：major_root 父节点 Work≈843.456 已获证，强制 midpoint Work≈2651.321 仍 capped。R130/R137 已有 root-only；本轮不再开 AM 阈值面板。
- R120–R122 已有子域标量界向父域仿射表达、单 binary 条件下界。R119 已测动态 incumbent crossing 后中断／收缩／重建的代价；本轮固定根信息、只强化产品块，与这种动态方案不同。
- R131 已有一次 budget→domain 预处理，明确尚未把随后得到的 penalty floor 反馈到产品上界；本轮检验这一返回传播，不能把旧域收紧再命名为新机制。
- R88 pair-CDF、R133 整数目标缺口、R144 RN-P、R145 严格互补／根值保留继续是历史背景，不要求新候选逐格打败全部旧方案。

新审查还发现：R148 D 的 K35 与 RB35 强子 LP 界分别是

\[
.545266780934=.383728302362+.161538478571,
\qquad
.313861187073=.222744904476+.091116282597.
\]

右侧为该子域 G 下端点加全局连续库存惩罚下界。因此不能仅凭左右子界不对称，就声称 AM 丢弃了新的非平凡条件信息。强制分裂仍可作为独立搜索研究预案，但当前有更直接的表达缺口。

### B3. 已完成的零求解筛查

独立审查脚本从实际 MPS、目标系数、Y 盒与库存约束计算连续惩罚最小值，用精确 primal=dual 核对，再将 p 下取整、beta 上取整。实际矩阵已核实 e/r、总库存、cutoff、one-hot 与产品求和关系；不是只观察几个点猜测标量上界冗余。

| R146 保存 GD 模型 | 已加权惩罚下界 p0 | 收紧上界 beta0 | 新乘积包络最大违反量 |
|---|---:|---:|---:|
| K20 base | .147656133333 | .627556624469 | .012393577181 |
| K20 joint | .147656133333 | .627556624469 | .012479518480 |
| K20 STOCK | .147656133333 | .627556624469 | .013399673148 |
| K35 base | .161538478571 | .605918126153 | .008976900807 |
| RX20 base | .209859195562 | .543194722528 | .041801627451 |

这些旧点本来全部满足 G≤beta0，却违反收紧后的乘积包络。筛查也在 R148 Shared-S 新点上发现剩余缺口，但本轮直接载体仍是 D，不自动做二者组合。

此表只证明保存点分离；没有新 Optimize，没有新的 LP 最优值或运行收益。所有值绑定原保存域和原 own-U，不能把历史 beta0 免费注入新的完整臂。附件不可得时，按 C 节和固定公开 R146 carrier 重建即可，不必重跑旧面板。

---

## C. 数学构造与非重复性

### C1. 从原目标得到有效 G 上界

以正式模型的 epigraph 列 g 表示 Gini 上界，区分原物理目标与 Native epigraph 目标：

\[
F_{\rm phys}=G_{\rm true}(Y)+p(Y),\qquad
p(Y)=\lambda P(Y)=\sum_i\omega_i|c_iY_i-1|,
\quad \omega_i\ge0,\ c_i>0.
\]

整数可行 completion 的 epigraph 语义为 g≥G_true；Native 中 e_i≥|c_iY_i−1|，其目标

\[
f_{\rm native}=g+\sum_i\omega_i e_i\ge g+p(Y).
\]

omega 使用实际目标中的已加权系数；不能忘乘或重复乘 lambda。非最小 g/e completion 的 Native 目标不必等于物理目标。下述连续 LP 界推导只需惩罚、资源与 cutoff 关系，不假定其分数点已有 g≥G_true。实际目标常数、比例和 scope 按正式 writer 核对。

取根域必要连续库存集合

\[
\mathcal R_0=
\{Y:\ell_i\le Y_i\le u_i,\quad B^-\le\sum_iY_i\le B\}.
\]

它包含当前改善域全部物理库存，并包含旧连续模型的库存投影。盒界来自同一根物理／支持域；忽略支持中的洞、路由和整数性是有效放松，不把放松最优库存当作物理解。令

\[
p_*=\min_{Y\in\mathcal R_0}\sum_i\omega_i|c_iY_i-1|,
\qquad 0\le\underline p\le p_*.
\tag{1}
\]

本臂自身 H 给出已验证 U0，原改善模型有 g+Σomega_i e_i≤U0，于是

\[
g\le U_0-\underline p,\qquad
\boxed{\beta_0=\min\{\gamma_U^0,\operatorname{up}(U_0-\underline p)\}.}
\tag{2}
\]

逻辑根仍可保持原区间 [0,gamma_U^0]；beta0 是当前 cutoff 下合法的产品包络参数，不必把整个调度根改小。后续更紧 cutoff 不破坏该根界。这里只使用已付 own-H 信息，不调用新的 primal oracle。

由于 (1) 的盒、资源与惩罚关系已在旧 LP 中成立，精确数学下单独加 g≤beta0 不提高其最优值。真正待测的是该标量信息向乘积块的传播。不能把本轮包装为发现了一个原模型不知道的 penalty inequality。

### C2. p* 可用有限资源分配计算，不需要 LP 求解

先逐站取

\[
Y_i^0=\operatorname{clip}(1/c_i,[\ell_i,u_i]).
\]

若总和在 [B−,B] 内即为最优。总和超过 B 时，从 Y0 向下分配所需减少量，按每单位成本 omega_i c_i 从小到大，最多减到 ell_i；低于 B− 时同理向上分配到 u_i。每个方向离开该站局部最优点后成本线性，故该贪心是连续单资源分配的最优解；复杂度 O(n log n)。固定站和零权重按同一规则处理；空库存域沿已有不可行语义。

为了让生产实现不依赖大有理数，可用任意实际非负乘子 mu、nu 形成对偶下界：

\[
d(\mu,\nu)=\mu B^- -\nu B+
\sum_i\min_{\ell_i\le y\le u_i}
\{\omega_i|c_iy-1|+(\nu-\mu)y\}.
\tag{3}
\]

弱对偶保证 d≤p*。每个 min 只需端点和位于盒内的折点 1/c_i；水填最后一档的边际成本可提供乘子。诊断可用精确算术验证 primal=dual；生产可先固定实际 binary64 乘子，再沿用可靠的向外舍入计算 d 的下界，取 underline p=max(0,d_lower)。排序的微小近似不会使一个合格对偶下界失效。

没有必要把精确 Fraction oracle 变成线上大依赖。若已有合格 interval/resource lower 能得到同样的 floor，优先复用；只用逐站独立最小值也有效，但会遗漏 K20/RB/RX 的总库存短缺信息，不能与本轮前置结果混称。

### C3. 将 beta0 反馈到当前实际 VD-P 块

实际状态列为 s_iy，乘积列为 t_iy（正式名称 state_i_y、state_g_i_y）。当前每站满足

\[
\sum_y s_{iy}=1,\qquad
\sum_y t_{iy}=g,\qquad
\gamma_Ls_{iy}\le t_{iy}\le\gamma_Us_{iy}.
\tag{4}
\]

在整数 one-hot 状态下，t_iy=g s_iy。保留旧行，在根模型上统一加入

\[
\boxed{t_{iy}\le\beta_0s_{iy}\quad\text{对全部现有状态}.}
\tag{5}
\]

各站求和得到 g≤beta0；由其他状态的上界又得到

\[
t_{iy}=g-\sum_{z\ne y}t_{iz}
\ge g-\beta_0(1-s_{iy}).
\tag{6}
\]

故只加 (5) 即在该 one-hot 产品块内实现上端点收紧；无需再显式写全部互补下 facet 或新列。旧下端点行继续保留。子域有效上端取 min(gamma_U_child,beta0)，若原上端已更小就不加重复强化。

对任意满足原 cutoff 的整数模型点，(2) 成立，且 t=g s，因此 (5) 有效，包括合格的非最小 epigraph completion。物理可行解使用原来的 exact-G 延拓也自然保留。无需为本机制改变 Start 目标或强制把所有 Start 改为某个特定 G completion。

若某子域 gamma_L>beta0，其 cutoff 改善集为空，可由现有模型／覆盖语义处理；不能把它说成物理原问题整体不可行，也不能用 epsilon 在 proof cover 中挖洞。root beta0 冻结后无需随每个新 incumbent 再计算、重启或追加 LP。

### C4. 强弱关系与严格例

旧松弛记为 Q。由 C1，Q∩{g≤beta0}=Q；加入 (5) 后 Q_PF⊆Q，原最小化 LP 值非降。

严格性不能只靠这条包含关系。取一站两个状态，旧区间 [0,1]，beta0=.6，并取

\[
s_1=s_2=.5,\quad g=.5,\quad t_1=.4,\ t_2=.1.
\]

它满足旧 one-hot/product-sum 块及 g≤.6；但 t1=.4>.6×.5=.3，违反新上端 facet。因此标量界已冗余，并不意味着它在乘积表达中的系数也已充分传播。B3 给出完整保存模型中的实际分离证据。

这没有证明每个实际 LP 的最优值都严格提高：原最优面可能还有未被排除的点。也不证明完整 MIP 更快；R148 已是反例。标准乘积凸化／bound propagation 不是本轮新发现的通用理论。项目价值是 BRP 的可计算 floor、当前松弛中的具体传播缺口、可验证的强弱关系及其完整算法后果。

---

## D. 最小生产实现与定向资格

优先采用默认 OFF 的独立 profile／flag，在 D 的首次正式模型生成时：

**自身 H → 取得当前根盒、库存与惩罚系数 → 计算一次合格 p 下界和 beta0 → 将 (5) 装入首次正式模型 → 原有根 LP／probe／target／terminal。**

不需要“先求旧根 LP、再加行重求”的流程。历史解只供诊断，线上界来自当前臂自己的数据。第一版不改变 proof-root/AM midpoint，其他 gamma 相关行沿原版本；这会保留部分尚未传播的信息，但使本轮干预清晰且较小。若实际代码支持等价地更新新 artifact 内原上端行，可选择它来减少冗余行，但不覆盖旧 immutable 证据。

实现要点：

- **域与单位：**p 已加权、beta 向上安全取值；root own-U、物理输入、支持／盒与资源 scope 对应。子模型只继承兼容、更小的域和不放宽的 cutoff；不在扩大支持或换目标的模型间继承。
- **数值方向：**对行 t−beta s≤0，beta 向上放宽才安全。零 floor 或无收紧时正常省略。tiny 系数运输沿实际 writer／Native 语义处理，可安全放宽或省略整条新增行，不照搬 R148 对 RHS 系数向下的符号逻辑。负 beta 若与合格 own-H 不一致，先定位 scope／算术，不能静默截成零。
- **实际行组：**若运输规则省略新增行，记录实际提交集合；C3 的完整包络等价只适用于完整提交或已由旧行支配的状态组，实际优化增量按提交矩阵判断。
- **模型与缓存：**在首次求解前完成 immutable 模型更新，登记 final SHA 与继承的 GD expected，不再 embed 一次 GD。任何已经构造的 backend/cache 仅在实际需要时按既有方法失效；不为本轮新建通用缓存系统。
- **费用与规模：**无新增列、source solve 或额外根重优化；最多每现有状态一条两项行。数学计算预计较轻，但行构造、读回、presolve 与分支成本必须实测，不能称为“零成本”。
- **资格：**集中验证实际加权 floor、连续资源 primal/dual、正／零 floor、舍入方向、首模型真实行、兼容子域、OFF、完整和非最小 epigraph Start。已有资源／物理／R134 资格直接复用；针对一个实际路径和必要边界即可，不再买全套旧资格。

生产源码有变化就登记新 PE；关键完整增量比较采用同一新 PE 的 D 与 D+PF。新 reader 按记录的 base/final SHA 重建上下文，不按文件后缀猜模型；特别是零 GD 行边界，不照搬 R148 的 source-LP／排除第一根LP适配，因为本轮首次求解前已装入 PF。遇到有限工程问题，定向修复并收束，不扩成全面数值重写。

---

## E. 实验顺序与条件进入

### E1. 三个 base-D 匹配 LP＋一个标量界对照

核心位置为 B3 的 K20 base、K35 base、RX20 base，覆盖固定库存导致 floor、总库存短缺及不同目标系数。复用其完整旧 GD 模型与合格旧最优证据，目标、常数、cutoff、盒、库存、支持及全部旧行保持一致；只加 (5) 后重新优化。不固定旧点的其他变量。

另选一个代表域（默认 K35，也可根据实际选择 RX20）只加入 g≤beta0，作为数值对照。理论上冗余，预期其最优值在旧质量容差内一致；若出现实质差异，先核实 domain／目标／数值质量，不把它包装成新数学收益。

因此默认是**3个产品反馈 LP＋1个 bound-only LP**，旧 baseline 不重求。记录原／新 LP 目标与合格界、p 下界／beta、行数／NZ、构造／读回／Native／外层成本、目标分解、约束质量。诊断结果按浮点 LP 合格证据报告，不冒称精确有理最优证明。

如果 RB35 的压力选择需要先看其实际根域，优先复用 R148 D 已封存的正式根模型和合格 LP bound；只有证据不足以组成同域对照时才补一个原 D LP，再做反馈 LP。最多增加这一组必要位置，不自动把 joint、STOCK 或全部 Shared-S 新点都重求。

如切掉旧点而新最优值未升，检查替代最优点并记录。p* 对所选连续资源放松已最优，不通过反复迭代同一个 floor 制造“加强”。确有独立搜索假设时可以安排一个有限 full pair 澄清；须运行前说明它能回答什么，不能以零 LP 收益自动进入所有完整面板。

### E2. 冻结一个候选，选择首个完整配对

根据真实优化增量和计算成本选择角色，不能只按违反行数或最大点违反量排序。默认 K35 的 LP 增量清楚则先测 K35；若信号主要来自 K20，则先测 K20；若只在 RX20 有用，不据此自动付两个困难角色。

| 角色 | 站点／车辆 | 物理 T／目标 | 新臂 | 每臂 cap | 核心问题 |
|---|---:|---|---|---:|---|
| K35 | 35／3 | T10800，lambda=.15 | 同新 PE 的 D、D+PF | 2400s | 固定站 floor 的产品传播是否改善困难 U/L 取舍 |
| K20 | 20／2 | T5400，lambda=.15 | 同新 PE 的 D、D+PF | 1200s | 库存短缺传播能否改善 D 的证明短板 |
| RX20-T1 | 20／2 | T4800，rho=1，原 lambda=1/Omega | 同新 PE 的 D、D+PF | 1200s | 易获证角色的证书成本与行为是否保持 |

这些是候选菜单，不是默认全跑。完整新臂各自产生 own-H、计算自己的 p/beta；不能注入旧 LP、旧 beta 或别臂 incumbent。两臂物理实例、T、目标、H seed、Gurobi 参数及 cap 匹配，串行运行；已进入的合格困难臂不因途中输赢临时停掉或加时。

### E3. 条件反差／保留收益对照

首对显示可继续的实质价值时，优先考虑 **RB35-T2，35站／3车，物理T7200、rho=1、原lambda=1/Omega，D／D+PF 各cap2400**。它的 floor 有资源短缺成分，且检验 D 已有重要 incumbent 收益是否被保住。不能只报告根 LP 更好就绕过这个关键取舍并宣称全面推荐。

必要时选择尚未进入的 K20／RX20 作证明对照；若它已足够回答剩余问题，可以替代第二个困难配对。只有一个会改变结论的具体未决问题时，再使用一组有限澄清容量。每次完整 paired comparison 对新 PE 使用真实匹配控制；历史结果保留为背景，不免费冒充当轮控制。

默认不增加 Seed，不补 P-GRB 网格、新大实例、长时收敛或 Shared-S/STOCK/RN/AM 因子矩阵。少量可由已有日志回答的问题先离线处理。负结果可结束本轮，不自动追加 D 广泛确认作为第二条付费任务。

---

## F. 判断口径与结果分支

分别报告：数学有效性／块严格性、实际旧点分离、固定域优化值增量、完整 own-H 算法收益。初始 LP、Native root-after-cuts、终端外部支持 L 分开。

完整臂给出 U、支持 L、signed gap=U−L、relative gap、T_produce／T_cert／T_verify／T_total；开放臂不填证书时间，不把 cap 附近总时差叫收敛加速。读取已有 witness 轨迹、Work、simplex、节点、AM target／split 记录说明实际变化，不新增全面归因系统。保留 AM 几何不代表后续 target 或 Native 搜索路径必然相同。

采用决定可以是：

1. **表达严格但优化增量不足：**保存资源界→产品表达的关系与替代最优点证据，结束有限实验，不要求一定发明新算法。
2. **LP 有益而完整收益不足／重要回退：**保留研究实现与原因边界，不晋升，也不启动更多动态传播或因子组合救援。
3. **完整收益实质且取舍可接受：**推荐一个统一 D+PF 有限论文增强候选，说明已测范围、费用和未解问题；稳定默认的广泛替换另行决定。

不要求每例全胜。重要回退按原统一口径正面检查；例如双开放角色，U 损失超过 max(.001,5%·U_D)，且 signed-gap 损失超过 max(.005,25%·gap_D)，属于明确的严重信号。这是实验评价参考，不是线上算法阈值，也不是唯一质量判断。轻微延迟或小幅可解释取舍不自动否定整体价值。

本轮不自动替换 R137 默认或合并。未形成新候选不影响稳定主线的论文组织；共同分母族和本轮传播结果都按实质选择进入正文或附录，不以研究轮次数量充当贡献。

---

## G. 预算与计费

| 阶段容量 | 上限 |
|---|---:|
| 定向资格、资源算术、3个产品 LP＋1个标量对照及必要 RB 匹配位置 | 1800s |
| 首个完整 D／D+PF 配对 | 4800s |
| 条件反差／保留收益配对 | 4800s |
| 至多一组有明确判别价值的证明／澄清配对 | 4800s |
| 失败、必要验证超出窗口与外层开销共用余量 | 1800s |
| **总上限** | **18000s＝5h** |

可在总额内调剂，表中不是三组完整实验都必须运行。K20／RX20 的每对名义容量为2400秒，实际早获证按真实费用；不能把释放容量与原名义额度重复计算。启动下一项前预留完整 cap 和必要验证余量。若首个 LP 或 full pair 已回答问题，停止即可。

所有新 own-H、算术／构造、求解、资格、失败和必要后验验证按外层计入一次，内部 H/LP/MIP 时间与 Work 不再次相加。旧结果不重新收费。纯离线数学推导／文稿、公开纯 I/O、必要编译单列；有计量不完备的步骤诚实披露测量基础，不用补跑搜索追求秒级账面精确。

---

## H. 文稿与独立复核

形成一节可并入文稿的内容：可计算惩罚 floor → cutoff 隐含的 scalar G bound → 原产品块未充分传播 → 严格例与实际模型点 → 匹配 LP → 完整费用与取舍。明确哪些是标准凸化工具、哪些是本问题的表达与证据；不要将简单的 U−p 算术包装成新通用理论或 OR 级成果保证。

昂贵完整运行前，由非主要实现者检查数学与实际矩阵；收尾做一次独立复核，重点是：

1. floor 的已加权单位、连续资源放松与物理包含、对偶方向、保守 beta 正确；未把原模型隐含信息称为新 scalar inequality。
2. (4) 的实际求和关系成立，全组上 facet 的推导正确；Start、子域 cutoff 与原 proof cover 保留。
3. 首次正式模型真实含本轮行，新 SHA／旧 GD expected／缓存对应；没有隐瞒额外 source 或根重优化。
4. 实验只买新的优化或完整比较信息，三实例／五旧模型不混淆，同新 PE 控制成立，历史强结果与 AM 负锚未遗漏。
5. 预算顺序和结论分支合理，无隐性矩阵扩张、重复收费或负结果后自动追加第二任务。

发现实质问题就定向修正；复核通过后收束，不因已合格浮点残差、小时间差或文稿措辞再开求解。

---

## I. 交付、Draft PR 与有限清理

交付本 goal、数学与阶段报告、必要实现／profile、匹配 LP 与实际进入的完整实验、成本与身份索引、采用决定、论文段落、独立复核及 RESUME。文件可合并，不按数量验收。关键原始证据、失败、旧 carrier 引用和本轮费用完整保留。

正常提交、推送，创建英文 Draft PR，建议标题：

**Round149: propagate penalty floors into state-product envelopes**

按实际吸收状态选择 main 或核实后的 R148 临时 base，读回 base/head、Draft 和交付状态。不自动 merge、force-push 或删除旧分支；不因等待合并阻塞研究。

只打包必要新增证据，旧大包用 fixed commit／成员 hash 引用。一次有限公开字节／成员恢复即可，纯 I/O 建议累计30分钟内收束，不触发 Optimize、编译或商业 Native。附件不可取时按 J 节公开来源与公式恢复，不重跑旧性能面板。

**显式继承 WORKSPACE_POLICY：**新增 build/raw/temp/restore 全部在 E:\codes\ExactEBRP-work；保护 E:\codes\ExactEBRP 与用户修改。交付后只清理已完成、可重建、已由公开 carrier 和实际恢复覆盖的本轮临时／重复对象；保留唯一 raw、失败、必要 PE/DLL、活动树和旧历史。记录删除／保留及字节，零删除可接受。

---

## J. 最小资料索引

- PR：https://github.com/yifanXovo/TailoredExact/pull/210
- R148 fixed science：https://github.com/yifanXovo/TailoredExact/tree/25765c21d63e7b04133f1e7dbe2dfd53c38f476f/results/unified_exact_round148
- R148：final_report.md、mathematical_analysis.md、LP_report.md、candidate_decision.json、candidate_manifest.json、cost_report.json、RESUME.md、carrier_manifest.json；reports/full.json 与 verified_U_trajectories.csv。
- R148 diagnostics ZIP：SHA256 036b2d97a966077820bf66df6d8af401b3972e6ca9baeb8a5a1755fdaec9e75d；路径 artifacts/diagnostics_qualification_failures.zip。
- R148 D 完整原始包：artifacts/campaign_k35_001.zip，SHA256 43e3ba967fbba9837ff965ce8adbd27beea8b82182758f9ec7b55f04570dd478；artifacts/campaign_rb35_001.zip，SHA256 8449e435e25a7dbaebd05b0426a3a2c232ef67881800e7104b7e34a86dab132d。
- R146 fixed science：https://github.com/yifanXovo/TailoredExact/tree/8ec2aebe46398485019623d9b18a3e30617d4997/results/unified_exact_round146
- R146 artifacts/diagnostics_and_failures.zip，SHA256 ab7bd4e2139c403623f1a82558c0d6ab0ce25fbb524947338b7f8c910cc66a6b；含 LP/K-20-S_base_GD、K-20-S_joint_GD、K-20-S_stock_GD、K-35-U_base_GD、R-X20-S-T1_base_GD 的 model.mps、compiled_rows.json、solution.json.gz。
- 实现：src/IntervalRowFactory.cpp、src/CplexBaseline.cpp 的当前 VD-P／resource pack；src/PaperExternalGiniTree.cpp 的 round127 root 与 AM；include/Round146Research.hpp、Round144Research.hpp、Round143Research.hpp 的行运输／SHA／Native readback；R148 的 root append 仅作接口参考，本轮不照搬其额外 LP。
- 历史：R47–R52 corrected AM、R119–R122 动态域／子域界传播、R130/R137 root-only、R133 integer objective、R138–R147最终报告；docs/current_mainline.md、docs/unified_exact_research_index.md、WORKSPACE_POLICY.md。
- 本次交付：TailoredExact_Round148_Stage_Review.md；TailoredExact_Round149_Review_Evidence.zip。附件 math_recompute.py/.json 可用 --archive 指向 R148 diagnostics ZIP、--old-archive 指向 R146 diagnostics ZIP；只做离线系数、矩阵、资源 dual 与点筛查，不加载求解器。实际产物名称可按仓库规范调整。

**成功标准：确认已有惩罚信息是否在当前产品表达中被有效传播，给出有效性、真实 LP 与完整算法三层清楚结论；有用则保留一个统一候选，无用则准确结束该实现，本轮都能形成可验收的论文研究结果。**
