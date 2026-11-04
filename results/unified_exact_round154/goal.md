/goal

# TailoredExact 下一轮完整任务

## Round154：面向证明目标的整数定价与独立库存下界接入

日期：2026-11-05（Asia/Shanghai）。

完整执行本轮研究、必要实现、实验、复核和 Draft PR 交付。先读取当前实际状态及 R153 证据，再根据观察推进；不要只完成一个初始试探后把本轮核心问题留给下一轮。允许局部重构、新辅助变量、新的数学强化和有依据的额外探索，保持已冻结稳定主线和历史证据可用。

## 0. 目标、自由度与预算

本轮有两个独立目标：

1. 针对 K35 / N-C20 已确认有价值但未解清的整数目标 completion，用原坐标的目标阈值残差 MILP 检验能否更有效证明真正影响完整 hull 下界的价格门槛；若有效，将其接入现有完整 Q 耦合链并实质深化。
2. 将 R153 的同一自付费 root floor 作为独立证明下界接入 GI-TBC，区分库存下界本身的价值与把 floor 写进 Native 模型、改变 AM/搜索过程的效果。此副线已有独立依据，不以新残差 oracle 成功为前提。

新增实验总容量为 144000 秒（40h）。这是可调拨上限，没有最低运行时长；目标是获得足以判断下一步的证据。预算充裕且关键问题有明确改善办法时，进行一轮实质深化；已有充分区间、对照或结构结论时可以提前收束。无需保证正面结果、每例获胜或本轮替换默认算法。

统一数学规则优先。拒绝按实例编号、大小或历史输赢打补丁，也不采用“运行 k 秒后切换组件”的内部算法步骤；允许有数学依据的自适应、确定性节点/迭代预算、模型与实现优化，以及正常的整个算法总时限。离线研究比较可使用时间上限。默认 Gurobi Seed=0、Threads=1，完整 own-H 使用 seed=20260626。

保持 R134 已接受的数值资格与证书政策；有具体有效性问题时定向处理，不因已合格 tiny 差或未出现的假想风险扩成新数值工程轮次。实验、编译及大规模 I/O 串行安排，避免互相污染计时。

## A. 起点与必须继承的事实

工作区使用 E:\codes\ExactEBRP-work\worktrees\paper-current，按实际远端吸收状态从 main 或经核实的 R153 临时 base 继续。检查当前分支、用户修改、AGENTS.md / WORKSPACE_POLICY.md 后开始。

本次审查身份：

- 仓库：yifanXovo/TailoredExact。
- R153 PR：#215，Open Draft；branch codex/round153-coupled-objective-hull。
- 审查 head：ffcfb59899611cbefa1cfe0d739cba5f9b6e5fe5。
- R153 fixed science：7d64c14faac43c6f410d435dd73b5ba5e49f2f30。
- 实测生产 source：36d085cc7012690b8ab38d7ace70f487f54aec7e。
- PE SHA256：44e593db8e3442925ce7dbd7bc16c077e79ab1646c7507b72541d8e697b996f7。
- Gurobi DLL SHA256：9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88。
- main 审查时仍为 b2b940c1e517a72e226ec60fc49ff19651737632；稳定科学主线仍为 R137 GI-TBC，固定 science e735c3447eb1443713c700942d873de1783a4a26。

R153 已验收为有价值的有限研究阶段。它补齐 R145 NC1/NC2/TS1–4、R152 合格行并集和 direct-g 参考；已经做过分母分区、同方向延长、近最优/中点选势、CDF MIP、整数流 Lagrangian、支持回放、大列池及必要最终 RMP refresh。不要将它写成只有几次短定价，也不要从头重建同一轮探索。

| 域 | 当前完整 Q 参考上界（数值） | 完整 hull 已知区间 | 已有列 / 支持行 |
|---|---:|---|---:|
| N-B35-S | .39297895351863926 | [.3960430527066062, .39604655895626023] | 575 / 9 |
| K-35-U | .2788644539329308 | [.2828596948801659, .28732616330431715] | 33882 / 82 |
| N-C20-U | .17476912471357817 | [.18332184845553887, .1899568005655939] | 54210 / 53 |

NB35 的整个 hull 增量已几乎由便宜 total-objective floor 捕获，不再为对称性重做长价。K35、NC20 的已证新增量分别至少约 .00399524、.00855272，尚有 .00446647、.00663495 的 hull 区间。三域参考边际均已有合法共同库存分布，Pe−H 处于数值噪声内；不再把投影不相容或 penalty slack 当作已观察到的主要解释。

R153 完整候选 J 的规则为当前 own-H 后、当前 root 域上做一次自付费库存 floor，NodeLimit=4096、原价格绝对 gap 1e-4，然后添加 total-objective floor 行。完整四对结果为：NB35/RB35 的 L 提高而 U/gap 变差；K35 的 U/绝对 gap 改善而 L 变弱；NC20 同证书、小幅时间成本。J 继续 research-only/default OFF。

R153 own-floor 分别约为 NB35 .3959564087240911、K35 .23294169799100467、RB35 .14243319962421927、NC20 近零；helper 外层分别约 14.6321、1.5182、9.7448、1.1603 秒。只有 NB35 的这个已知 floor 超过对应 B 终端 L。其他角色仍适合检验统一规则的成本与搜索副作用，不能预期它们终端 L 因同一个 floor 必然提高。

## B. 有限历史排重与本轮证明目标

### B1. 明确继承，不把旧式改名成新贡献

先核必要邻近历史，不重跑旧大矩阵：

- 早期 formulation_snapshot / PR58 已有 exact-S parametric cutoff toy；小域可枚举，较大域的 S 覆盖过大。旧 Dinkelbach 分支因未实现有限精确证书被排除，不是本轮残差 MILP 的实测负面结论。
- IntervalRowFactory.cpp / CplexBaseline.cpp 已有 SP 乘积及交叉相乘的 incumbent objective estimator。乘正分母、参数阈值、McCormick 都不是新一般理论。
- R133 已有整数目标严格差及 balancing 结构；R152/153 已完成 Theta=H+Gamma、169 行严格例和 hard-resource 排除角点解释。本轮直接引用其准确范围。
- R104 OC-SHADOW 未将诊断界用于正式 LB/cutoff/stopping；R139 改 LP/AM；R144/145 是原变量投影行接入 Native。它们不等同于本轮仅在已有证明账本消费自付 floor，但其负面与成本结论保留。
- R153 的 CDF、分母分区、整数流、双列交换和大列池已试；不将自动重开这些网格作为默认研究。

本轮新实验身份是：对任意 signed state potentials，以状态级精确 S-product 构造原坐标残差 oracle，在完整整数域上提供可中断的合格价格下界，并检验对实际 hull 证明目标的用处。无需恢复旧未证的 Dinkelbach benchmark，也不预先声称新 oracle 的 LP 支配 RN 或更快。

### B2. 先挑有直接证明空间的方向

沿用 R153 的完整自由 Q、全部原支持、硬库存上下界、Gini 上界、真实列与 C_Q 证书。读回最近的候选方向及大池筛查，输出有限的“目标值—所需 price 门槛—已知 ceiling—成本”表。

对固定方向，现有证书为

\[
L=C_Q+\min(a_K,L_m).
\]

设累计 hull lower 为 L_*，希望证明到 zeta，则需

\[
\tau=\zeta-C_Q,\qquad \zeta\le C_Q+a_K.
\]

若已有真实库存价格 upper U_m，则

\[
C_Q+\min(a_K,U_m)
\]

是该单一证书的可能上限。若它已低于目标，不再盲目延长该方向。这个 ceiling 不是完整 hull 上界，也不否定不同支持行的联合效果。发现新真库存 price<tau，只说明该固定证明目标不可达，并提供列；不能据此否定整个 hull。

K35 最近 near-optimal 方向仍有接近当前 RMP upper 的直接空间，可作为首选。NC20 旧近闭合方向的直接余量仅约 1.1e-6，不再追该方向的小 gap；优先从当前 54210 列池选择有足够空间的更新方向。允许少量新的近最优/稳定化选势，但每次要说明改变了哪个已观察瓶颈。

## C. 主研究：原坐标的目标阈值残差定价

### C1. 精确对象与正、零库存分支

对正分母库存，定义

\[
S(Y)=\sum_i c_iY_i>0,\quad
A(Y)=\sum_{i<j}|c_iY_i-c_jY_j|,\quad
G(Y)=A(Y)/(nS(Y)),
\]

\[
f(Y)=\max\{\gamma_L,G(Y)\},\quad
D(Y)=\sum_i d_i(Y_i),\quad
p(Y)=\beta f(Y)+D(Y),\quad \beta\ge0.
\]

R 为同一个完整必要库存域：原单站支持、Bminus<=sum Y<=B、物理 Gupper 等均保留。c_i 和 signed d 使用实际声明系数。设安全的正分母界为 0<l<=S<=u。若域允许全零库存，单独保留

\[
p(0)=\beta\gamma_L+\sum_i d_i(0).
\]

不能将零状态混进除法，也不能因 beta=0 去掉资源或 Gupper。

对任意目标 tau：

\[
R_\tau(Y)
=S(Y)[p(Y)-\tau]
=\max\left\{
S(Y)(\beta\gamma_L+D(Y)-\tau),\
\frac{\beta}{n}A(Y)+S(Y)(D(Y)-\tau)
\right\}.
\]

这一恒等式允许以整数残差证明目标价格；没有依赖迭代极限或光滑收敛率。标准分式参数化思想明确归属，不作为新通用定理。

### C2. 状态级精确 lift

保留完整 one-hot x_iy，定义 Y_i=sum_y y x_iy、S=sum c_iY_i，并引入

\[
z_{iy}=Sx_{iy}.
\]

可用完整四条二进制乘积线性化：

\[
lx_{iy}\le z_{iy}\le ux_{iy},\qquad
S-u(1-x_{iy})\le z_{iy}\le S-l(1-x_{iy}).
\]

同时保留每站 sum_y z_iy=S。令 W=sum_iy d_i(y) z_iy，则整数状态上 W=S D。用 a_ij>=±(c_iY_i-c_jY_j)、A=sum a_ij，并保留 A<=n gamma_U S。

残差模型最小化 q，满足

\[
q\ge W+(\beta\gamma_L-\tau)S,\qquad
q\ge \frac{\beta}{n}A+W-\tau S.
\]

q 必须允许负值。beta>=0 保证绝对值 epigraph 有达到真实 A 的扩展，且更大的辅助 A 不会制造低于真实残差的整数解；Gupper 行的最小扩展保持每个原合法库存。不要把非最小 auxiliary completion 当成价格真值。

沿用合理的 station anchoring 与尺度处理：若 d_i(y)=a_i+tilde_d_i(y)，则 W-τS 可写 sum tilde_d z+(sum a_i-τ)S。记录实际变换，避免 signed 系数抵消造成错误的 guard。

可加入便宜且明确有效的资源乘积：

\[
Bminus\cdot S\le \sum_{iy}y z_{iy}\le B\cdot S.
\]

允许根据小域/实际观察使用更强的有限界、RLT 或模型复用；先说明作用，不默认展开新的变体矩阵。旧 RN oracle 作为保留的有效对照/信息来源。

### C3. 与旧 aggregate SP 表达的准确关系

这段可直接作为本轮理论起点，但需核实际写入系数。令

\[
a_i=\min_y d_i(y),\ b_i=\max_y d_i(y),\
a=\sum_i a_i,\ b=\sum_i b_i,\ D=\sum_{iy}d_i(y)x_{iy}.
\]

由状态 lift 得

\[
a(S-l)\le W-lD\le b(S-l),
\]

\[
a(u-S)\le uD-W\le b(u-S).
\]

因为 z-lx>=0、ux-z>=0，且每站的和分别为 S-l、u-S。这正好蕴含 S∈[l,u]、D∈[a,b] 上 W=S D 的四条 aggregate McCormick，signed d 同样成立。

严格性例：两站，Y1∈{1,2,3}、Y2=1、c1=c2=1，d1=(0,1,2)、d2=0。在 Y1=2 的 one-hot 点上，S=3、D=1，aggregate 矩形 [2,4]×[0,2] 容许 W=2，而状态 lift 强制 W=3。

范围限定：这是产品块相对上述 Cartesian 成本界的关系，不是对完整 Q 或 normalized RN oracle 的支配定理。若 hard-total DP 给出更紧 D 界，状态 lift 不自动蕴含那些更紧 aggregate McCormick；有用时保留相应紧界/乘积行。

一个小反例说明该限定：Y1,Y2∈{0,1}、Y1+Y2=1、c=(1,2)、d_i(y)=y；取 x_i1=.5、S=1.5，各站 z_i1=.5、z_i0=1，状态 lift 可行而 W=1。真实 hard-total 使 D=1，紧 aggregate 产品要求 W=S=1.5。加入上述 total-product 行可排除此点。不要把这条限定遗漏后声称无条件支配。

### C4. 从残差下界恢复价格下界

若残差求解给出合格 lower ell（已在残差单位支付运输/Native 数值误差），则对整个正分母域

\[
m_+\ge \tau+
\begin{cases}
\ell/u,&\ell\ge0,\\
\ell/l,&\ell<0.
\end{cases}
\]

证明来自 p(Y)=tau+R_tau(Y)/S(Y) 及正分母界。下界无需残差达到最优；ell>=0 已可证明 m_+>=tau。转换使用安全方向，不把原 price guard 的常数原样搬进残差模型。

完整价格将该正分支 lower 与合法零状态取 min，再与覆盖全域的既有 DP/同方向合格 lower 取 max。未知/未返回调用不提供新界；保留既有信息，不因新形式弱而降低累计 lower。

在同一 R、beta、d 下，跨目标可复用

\[
R_{\tau'}(Y)=R_\tau(Y)-(\tau'-\tau)S(Y),
\]

\[
\min_{Y\in R,\ S(Y)>0}R_{\tau'}(Y)\ge
\ell_\tau-\max\{(\tau'-\tau)l,(\tau'-\tau)u\}.
\]

右侧是可以保留的运输下界，不要求另一调用原始返回的 lower 自动满足它。可按需要使用这类廉价运输，避免每换 tau 都从空白开始；不要让参数搜索成为无意义的密集网格。任意返回库存均按原 p(Y)、资源和真实 G 重算后，才成为 price upper/合法列。残差 incumbent、q 或 model status 本身不是原价格真值。

## D. 实验顺序与实质深化

### D1. 只资格新增接口

先用既有有限小域做目标化资格：枚举合法库存，核真值扩展、signed d、beta=0、gamma_L>0、正/零分支、负 q、正/负 residual lower 转换及几种 tau。核实际模型行/界、LP/MIP 证据和目标尺度；至少覆盖一个非最小 A/completion 情形。

独立复核 C2–C4 与新 coefficient transport 后再进入昂贵试验。沿用既有文件/模型读取、数值界和 scope 接口，不重铺 R153 全部旧边界测试。可用有限 Fraction 控制补证上述块关系，不需为已有理论重做大样本。

### D2. 固定方向的有用对照

优先 K35 与 NC20 各一个有足够 ceiling 的真实方向，必要时各加一个具有结构反差的方向。冻结 Q、R、beta、d、目标 tau、初始真库存信息和比较口径后，再看新结果。

比较原 normalized oracle 与 residual oracle 在同一原价格证明任务上的：

- 合格原 price lower/true upper、是否达到目标；
- 转回同一 C_Q/a_K 后的实际 hull lower，而不只比较 residual 数值；
- 构造、LP/MIP、真实库存验证及必要读写的外层费用；
- LP 规模、根松弛、Native bound/搜索工作，及 denominator/成本界对转换的影响。

优先复用身份、初始信息、平台和口径可比的旧记录；若无法形成公平成本对照，只补必要 current control。继承的数学 lower 与本次新取得的性能要分开。对不同目标/不同方向，不拼接成一条单调收敛轨迹。

开始可以用可解释的短窗口筛模型强弱，但给有希望的方向一次真正的长证明机会，参考 3600–7200 秒级离线窗口。更长或不同分配可在总额内调整。至少说明延长究竟可跨过哪个 price/hull 门槛；不因原 Native bound 仍有移动就自动无限延长。

### D3. 接回完整 Q 耦合与支持行

若新方法给出有用价格界、目标证明或列，则复用现有 33882/54210 列池、合格 supports、原 Q 及所有累计界，更新方向并继续完整耦合。不得缩小真实支持来制造易解问题。

继续使用

\[
L_\Gamma=C_Q+\min(a_K,L_m),\qquad
\beta g-\pi^\top s\ge L_m,
\]

以及完整 Q/所有边际/真实 completion 合格的 RMP primal upper。不要用 RMP ObjVal 代替合格 lower，或将有限 supports LP 的 upper 当成完整 hull upper。

对新行做必要的完整自由 Q 回放；如果已有合格点/对偶足以证明同值则复用。若最后又加了列，完成必要的一次 RMP refresh。仅在没有新增列、保存信息足够时跳过，不让“最后几列未评估”成为下一轮假问题。

K35 可先争取 1e-4 量级 hull 区间。NC20 按其 .00855 已证增量和实际研究问题选择目标，通常 1e-4 量级已具有判断力，不机械继承 1e-5 作为必须完成条件。精度高于资格不确定性，变更理由记录清楚；不通过放宽到比有意义增量更宽来宣布解决。

如必要，允许有依据的方向选择/轻量状态产品深化；避免重新默认做全分区、CDF、flow、primal-pool 网格。若新 oracle 也没有实际改善，在完成一轮针对性比较/深化后，量化剩余瓶颈并明确是否暂缓这条库存定价路线，而不是自动续开同型任务。

## E. 独立副线：证明下界与搜索评分分开

### E1. 数学机会与接入原则

命名研究候选 E：稳定 GI-TBC 加自付费外部库存证明下界。初始使用与 R153 J 相同的 root floor producer、NodeLimit=4096、price gap 1e-4；主要改变是 floor 的消费位置。

先从 R153 保存数据核 scope 和机会。NB35 上的 max(B终端L, own_floor) 可给出约 .3959564 的数学潜力，但这只是保存结果上的机会计算：不能作为 E 实测结果、免费 floor、或未付费的新算法 gap。

E 保留原 Native 模型及其 cutoff 行、原 native/LP 下界供搜索排序和 AM 评价。floor 不写入 Native 行，也不把同一个常数代入所有父子界而人为压平 AM 增益。利用已有 scope/coverage/证书账本记录新证明来源，用于合法的剪枝、全局终止和结果下界；不另建一套大型账本框架。

若 ell 对整个潜在改进域有效，可与原全球 proof lower 取 max。一般 frontier 情况必须按覆盖范围处理：

\[
L_{\rm proof}=\min_{j\in\mathcal F}\max(L_j,\ell_j),
\]

未被 floor 覆盖的叶仍使用原界，关闭区域和覆盖完整性沿用现有制度。不能把首个 canonical artifact 的局部 floor 自动当成全局 floor。

若 floor 只在 F<=U0 的 incumbent 域内有效，需结合域外 F>=U0 的已证事实，先形成 min(U0,ell) 的整体界，再合并。继承到后代时核同数据/系数、支持收缩、Gini 区间和 cutoff 范围；复用 R153 已有检查。

E 仍支付全部 own-H、floor、构造及验证，使用当前自身域。证明界触发合法提前终止/剪枝，以及已付费用带来的时间差，都可能改变轨迹，因此不承诺与 B 的墙钟轨迹相同。若希望同时改 producer，作为另外注明的变化，不与本次 placement 单因素对照混写。

### E2. 为什么值得一个有限对照

R153 原始 AM 记录显示：NB35 / RB35 的 B 首次进入 native-target；J 的父界与左子界同被 floor 抬到几乎相同，首步进入 exact-close，右子界仍不同。这支持“接入方式改变求解路径”的判断，但还不能把 U 损失唯一归因于 AM。

因此本轮重点是同一有效 floor 在 E 接入下能否保留下界收益，并减少已有搜索回退；不是给所有组件重新做归因矩阵，也不按角色决定是否开 floor。

实现后定向检查：当前 own-H/source；在同一域、cutoff 和 incumbent 输入下 formal Native 行与 B 一致；proof scope/coverage、原 AM/排序输入身份、合法停止，以及来源拒绝时保留原 B 信息。通常无需重测已通过的所有 helper/进程边界。稳定入口、已有 J 和旧研究配置保留。

### E3. 预先冻结完整比较

在查看 E 完整结果前冻结同一 PE/匹配执行链、输入与配置。沿用 R153 的四个角色、原 lambda/T/车辆/容量及 pair-only AM=.08、depth=8、minimum width=1e-4：

- N-B35-S：B / E 各 2400 秒，另加同 PE 的 R153 J-row 2400 秒作为直接 placement 对照。
- K-35-U：B / E 各 2400 秒。
- R-B35-S-T1：B / E 各 2400 秒；保留 lambda=.055125275219827186、T=4800。
- N-C20-U：B / E 各 1200 秒。

完整窗口容量为 19200 秒（5h20m）；费用与验证余量另按总表预留，不将窗口和子费用重复相加。其余 J 旧结果保留为历史参考，不为对称性重新跑四组 J。

新 C++ 行为需要时构建一次匹配 PE；不为轮次编号强制编译。每臂独立 own-H，Seed0/Threads1，不共享历史 floor、列、incumbent 或另一臂 H。按既有生产/验证口径报告 U、supported L、gap、T_produce、T_verify、T_cert，open 的 T_cert 为空。

各角色用于完整评价统一候选：K35/RB35 的当前 floor 已被 B 终端 L 超过，NC20 是证书控制。允许正常性能取舍；无有效性问题或严重广泛回退时，不因一个普通损失删掉预定角色。若候选资格未通过，不买无意义完整面板；E 不因残差主线未成功而自动取消。

可以用 6h 决定槽对一个关键问题加长：例如 B/E/J 各 7200 秒，或将该容量投给能实质改变 hull 判断的长证明。选择及理由先写清。没有默认多 Seed、P-GRB 大网格或所有角色多时限扩张。

## F. 阶段判断与论文组织

本轮应形成完整而有限的判断：

1. residual oracle 的整数等价、块表达关系和证书转换是否正确；它在真实 signed 方向上是否改善证明成本或有效界。
2. K35/NC20 整个 hull 的已知值域缩小多少；原价格求解、方向选择、列池和完整路由 Q 各留下什么限制。
3. E 能否以可接受成本获得稳定的证明收益；同 PE NB35 B/E/J 的实测与 AM/模型记录支持何种机制解释。
4. 下一步该继续该 oracle、深化有证据的结构问题，还是将本条库存研究暂时收束并转向完整路由/装卸耦合等剩余限制。不要把初始 LP 的若干增量自动等同于完整算法收益。

已有 Theta=H+Gamma、hard-resource 共同分布、169 行固定边际严格例和本轮产品块关系可以组成连贯理论段落。标准参数化、McCormick、列生成、bound ledger 明确归属，论文贡献落在针对本问题得到的结构、可计算性与实际效果上；不预先承诺 OR 层次。

稳定 GI-TBC 的论文整理可同步，不等待研究支线正面。E 若仅有有限支持则保留 research-only；不按实例混合 B/E/J，也不为了“新主线”自动替换默认算法。

## G. 预算与计量

| 阶段容量 | 秒 | 用途 |
|---|---:|---|
| 历史排重、当前目标与可复用证据 | 7200 | 先消除已知无效工作 |
| 残差模型/运输实现与定向资格 | 10800 | 建立正确新接口 |
| 固定方向的匹配定价对照 | 28800 | 证明目标与成本比较 |
| 完整 Q 耦合与实质定价深化 | 36000 | 主要值域推进 |
| 结构关系或证书/方向选择深化 | 7200 | 根据已观察瓶颈调整 |
| E 接入及必要资格 | 7200 | 独立算法机会 |
| 条件完整比较窗口 | 19200 | 8 个 B/E 臂＋NB35 一条 J |
| 决定型长证明或完整长窗 | 21600 | 解决一个重要剩余判断 |
| 失败、验证与外层余量 | 6000 | 实际一次计费 |
| **总上限** | **144000＝40h** | **可调拨，不要求花满** |

按外层记录新增构造、DP、LP/MIP、own-H、价格、失败与必要验证。Nested Runtime/Work/helper 不重复计。纯理论与代码写作、文稿、公开 I/O、必要编译单列；继续披露实际口径和缺项，不为补秒级计量重跑性能。启动完整臂或长价前预留其窗口和验证容量。

## H. 复核与交付

昂贵实验前，由非主要实现者复核域等价、signed/zero/negative-q、residual运输、目标 ceiling、旧参考排重，以及 E 证明界/搜索输入的分工。最终复核实际保存数据、数学、scope、身份、费用、原始失败和论文主张。独立复核用于关闭实际问题，不扩为无限资格清单。

交付的信息应足够复现判断，文件可合并：

- 实际 goal、preanalysis/历史排重与方向目标表；
- residual 理论、块关系、实际模型与资格、固定方向及耦合结果；
- E 设计、身份与完整结果（若进入），准确机制归因；
- 费用、版本、论文小节、独立最终复核及 RESUME；
- 当前未决问题和明确建议，不把未知写成负面或把有限正例写成普遍支配。

使用正常提交/push，创建英文 Draft PR，建议标题：

Round154: target integer pricing proofs and separate proof bounds from search

按实际吸收状态选择 main 或核实的 R153 临时 base，读回 base/head/Draft。无需等待上一 PR merge；不自动 merge、force-push 或删除分支。

## I. 工作区与公开恢复

显式继承 WORKSPACE_POLICY：所有新增 build/raw/temp/restore 位于 E:\codes\ExactEBRP-work；保护 E:\codes\ExactEBRP、用户修改、活动树和旧历史。已有已验证解释器/运行库可在原位置只读复用。

PR 后做本轮有限收尾：只清理本轮已完成、可重建且被公开恢复覆盖的临时/重复对象；保留唯一原始证据、失败、必要 PE/DLL 与当前需要的树。记录实际删除/保留，零删除可以接受；不进行全历史清理。

新载体只打包新增必要证据；R153 的 12 个大包、旧 inputs/source 按固定 commit/member hash 引用，避免重复打包 4.7GB 成员。对新增公开载体做一次有限恢复，不触发旧 producer、编译或性能重跑。旧目录中 RUNNING/FAILED 等历史状态文件不代表当前有活动任务，不自动恢复它们。

## J. 最小来源索引

- PR215：https://github.com/yifanXovo/TailoredExact/pull/215
- R153 fixed science：https://github.com/yifanXovo/TailoredExact/tree/7d64c14faac43c6f410d435dd73b5ba5e49f2f30/results/unified_exact_round153
- 核心：goal.md、final_report.md、mathematical_analysis.md、deepening_plan.md、candidate_decision.json、reports/scientific_table.json、reports/complete_pairs.json、reports/coupled_iterations.csv、reports/pricing_results.json、review/k35_endpoint_assessment.md、review/nc20_endpoint_assessment.md、review/final_scientific_review.md、cost_report.json、source_manifest.json、reuse_index.json、RESUME.md。
- 实现：scripts/round153_coupled.py、pricing.py、stabilize.py、reference.py、refine.py、checkpoint.py、online.py、include/Round153Research.hpp；上述简称均带 round153_ 前缀。原稳定与验证接口参见 docs/current_mainline.md、WORKSPACE_POLICY.md。
- 历史：PR58 fixed ff381ac9da9b56be730dc4768455e861187e5c13 下 results/gf_tailored_bc_formulation_snapshot_round/alternative_formulation_rejection_notes.csv、alternative_formulation_equivalence_test.csv 及 scripts/run_tailored_bc_formulation_snapshot_round.py；src/IntervalRowFactory.cpp 的 SP/cross-multiplied estimator、src/CplexBaseline.cpp；R104/139/144/145 的接入边界；R133 joint_objective_gap_note；R152/153 的完整对象与严格例。
- 经典理论：Dinkelbach (1967), On Nonlinear Fractional Programming, Management Science 13(7):492–498, https://doi.org/10.1287/mnsc.13.7.492。此处使用参数残差恒等式，不引用光滑/连续条件下收敛率作为本项目整数求解保证。原 Q 耦合沿用 Dantzig–Wolfe 和既有 R153 对偶修正推导。
- 外部验收附件：TailoredExact_Round153_Stage_Review.md、TailoredExact_Round154_Review_Evidence.zip，包含独立完整臂/支持 LP/RMP/价格审查、历史排重及新残差/块关系推导。附件不可取时，可按固定原档及本文公式继续，无需等待或重跑旧性能。

**成功标准：以准确历史和完整域为基础，实质检验一种面向有用证明门槛的定价方式，并独立判断有效库存下界能否以更合适的接入方式服务统一 GI-TBC；最终给出可放入论文、可决定后续方向的完整证据。**
