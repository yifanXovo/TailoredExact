/goal

# TailoredExact 下一轮完整任务清单

## Round141：阈值计数析取、条件弦加强与目标界嵌入

**日期：2026-10-30。建议轮次：Round141；编号已占用时沿实际下一轮继续。**

## 0. 本轮目标与自主权

R140 可以验收。双侧 TC2 在五个匹配连续域上都比旧 TC＋stock 提高最优界，但没有形成稳定的完整算法提升；TC2 的 K35 双端回退，以及旧 TC＋stock 的混合结果和关键 Seed1 反转，支持两者保持 research-only。稳定 R137 GI-TBC 继续保留，不追加无结构新意的 TC2 面板、placement 或 Seed 网格。

本轮研究：**能否将“超过某个服务比例阈值的站点数”作为整数析取轴，利用两侧计数域重新加强 Gini 分子，再将合格子域下界嵌入原生整数模型，获得比单条全域 TC2 更有用的搜索信息？**

按以下顺序推进：

1. 在已保存 TC2 模型上完成有限 count 子域 LP，与 plain count、条件弦和原 Gini 中分比较。
2. 有信息时，实现一个根部计数析取的条件目标界候选；复用 R120 的证明注入思路，不重构整棵外层树。
3. 用必要 D0 对照区分 count links／共同下界和条件目标界的作用，检验完整算法价值。
4. 更新数学说明、紧凑实验表和研究决定。可以形成采用建议、research-only 或明确停止结论，不要求新方法必须成功。

**新增实验计算总上限为10小时。** Codex 可根据实际结果调整顺序、少量诊断域、统一选择规则及一个直接相关扩展；预算是上限。原则上只有一个统一完整主候选，不按角色选择不同机制，不机械补齐无信号配置。

所有未明确多 Seed 的新求解显式使用 **Gurobi Seed=0**；有限第二 Seed 为1。H seed 固定20260626并单列。计时求解单线程、串行，编译、重 I/O 和 PDF 导出错开。

算法应有统一的数学或结构依据：不按实例身份特判、不按大小准备两套算法、不以运行若干秒后切换方法或 leaf 作为算法步骤。根据实际支持、计数区间、解出的松弛点和证明信息作统一决策是允许的；实验 cap 与物理 T 不属于算法切换规则。重视可组织成文的实际收益，不要求每例最佳，也不接受重要角色或大范围严重回退。

---

## A. 实际起点与历史边界

### A1. 版本和工作区

| 项目 | 编写本 goal 时核实的参考 |
|---|---|
| 仓库 | yifanXovo/TailoredExact |
| R140 PR／状态 | #202，open／Draft，未合并 |
| R140 branch／head | codex/round140-two-sided-threshold-count；d00bcf41520bd5bbbdc81096165deba25eae8023 |
| R140 生产源码 | 81ab886e23220be97a858e66961056cef727d074 |
| R140 固定 science | 15e401f794bb53e31c5848e0edabf0b4153ca678 |
| R139 PR／head | #201；5a7159398591032b267d6bf98e5ffd4942f36944 |
| 稳定入口 | scripts/paper_s2.py → config/gi_tbc_round137.json |
| R138／R139／R140 研究入口 | paper_s2_stock_rlt.py；paper_s2_stock_placement.py；paper_s2_tc2.py |
| 活动树／新资产根 | E:\codes\ExactEBRP-work\worktrees\paper-current；E:\codes\ExactEBRP-work\ |
| 受保护原目录 | E:\codes\ExactEBRP |
| 建议 branch／结果目录 | codex/round141-count-disjunction；results/unified_exact_round141/ |

先读适用 AGENTS.md、WORKSPACE_POLICY.md，核实 refs、未提交内容、进程及资产。main 已吸收所需版本时从实际 main 继续，否则从已核实的 R140 分支继续并以其为临时 PR base；不等待前序 PR 合并，也不机械回退参考 SHA。

沿用自身 H、M-B/VD-P、pair-only、AM=.08、depth=8、minimum width=1e-4、AP off，及 R134 数值／证明政策。新研究的默认共同载体为 **stock BOTH＋旧 TC＋TC2**，即 R140 显式 tc2 配置；R140 launcher 的默认 tc 不是该载体，须显式指定并读回。全部稳定及历史研究入口保持原语义，新组件默认关闭。

### A2. 必须吸收的结论

- R140 实际新增14个正式完整位置：TC2五个 Seed0、旧 TC 八个 Seed0和一个关键 Seed1；另有2个资格位置、11个显式连续 LP。新增实验约6.064小时，无阻断工程问题。
- K35 的旧 TC／TC2 最终 U/L 分别为 .650438712/.568288526 与 .702148613/.541970377；TC2 虽然根 LP 更强，完整结果明显更弱。RB35-T2 的旧 TC Seed0 优势也未在 Seed1 保持。不继续寻找更有利 Seed。
- 全部16个新位置没有实际外层 split。K35 的 TC2 较早改善 incumbent，随后停滞；原生切平面和搜索开始阶段的界优势亦未保持。无需再把首次解延迟、几秒 target 开销或全 placement 网格当主问题。
- R50/R51 已研究变量家族优先级和稀疏 LP probing；R62 是单站服务阈值与车辆兼容；R88 是两站 CDF 运输包络；R120–R122 已有 Gini 轴的一 binary 条件目标界注入且完整表现混合。本轮的新问题是**全站比例计数轴、嵌套计数传播及条件分子弦**，不把 binary 注入或标准析取理论重命名为新发明。
- R66 已试完整 arc-load 表达，R68以后的 H、启动解与路线改进也有充分历史。本轮不另开一般性载荷建模或 primal 启发式重做。

### A3. 调整 R140 报告中的返库上界建议

本次验收已对 R138 K35 的旧 TC＋stock 保存点作零 Optimize 复核。原点有
\(R=(25.226452775,5.773547225,\approx0)\)，\(Q=(20,25,30)\)。
交换完整车辆0／2变量块，保留所有非车辆列和目标；再取该交换点的3/4与原点的1/4，得到

\[
R'=(6.306613194,5.773547225,18.919839581),\qquad
a'=(.324239517,.276789192,.632964241).
\]

该点同时满足 \(R_k\le Q_k\) 和 \(R_k\le Q_ka_k\)。原23624条行与10007个变量界的最大数值残差约 \(1.82\times10^{-12}\)，旧 TC／stock 表达与目标不变。原诊断封包 SHA256 为98176d441008d0263644702b73574f782377b78c5d0541fe092e4086940739c0。

这是同目标数值可行见证，不是异质车辆的一般对称性定理或精确有理最优证书；但已足以降低“仅补返库上界”产生该域最优值增量的预期。必要时做一次匹配 LP 确认即可，不围绕这一建议安排完整算法主线。也不重新恢复全部历史 raw。

---

## B. 数学合同：从整数计数到条件证明

### B1. 复用 TC2 的定义

仅统计站点。实际有限支持为 \(\mathcal Y_i\)，selector 满足
\(\sum_y s_{iy}=1\)，\(Y_i=\sum_y ys_{iy}\)，\(r_i=c_iY_i\)。
阈值为实际支持比例的不同正值
\(0=t_0<t_1<\cdots<t_M\)，\(\Delta_j=t_j-t_{j-1}\)。定义

\[
K_j=\sum_i\sum_{y:c_iy\ge t_j}s_{iy},\qquad
A=\sum_{i<l}|r_i-r_l|.
\]

整数 selector 下 \(K_j\) 为整数、随阈值非增，且

\[
A=\sum_j\Delta_j K_j(n-K_j).
\]

R140 已从库存区间
\(\max(0,B-\sum_kQ_k)\le\tau=\sum_iY_i\le B\)
及实际支持得到整数有效区间 \(\ell_j\le K_j\le u_j\)。沿用其上下计数构造、精确 dyadic 阈值和有向写入，不再重做该轮全部证明。

TC2 使用
\[
H_\Sigma\ge\sum_j\Delta_j[(n-\ell_j-u_j)K_j+\ell_ju_j],
\]
而每项的弦余量为
\[
K_j(n-K_j)-[(n-\ell_j-u_j)K_j+\ell_ju_j]
=(K_j-\ell_j)(u_j-K_j).
\]

这一余量解释计数域收紧的潜力，并不等于当前完整模型的目标误差。

### B2. 整数覆盖与嵌套传播

在当前父域 D 上，选择一个 \(\ell_j<u_j\) 的计数及整数
\(\ell_j\le m<u_j\)，分成

\[
D_0=D\cap\{K_j\le m\},\qquad
D_1=D\cap\{K_j\ge m+1\}.
\]

两侧覆盖父域全部整数解且互斥，允许某侧物理不可行。它们不是两个 Gini 区间，不加入原 Gini frontier 冒充该轴的子节点。

无需新的优化即可传播：

\[
D_0:\quad u_h'\leftarrow\min(u_h,m)\quad(h\ge j),
\]
\[
D_1:\quad \ell_h'\leftarrow\max(\ell_h,m+1)\quad(h\le j).
\]

其余界继承父域，随后在对应子域追加由新计数区间形成的聚合 TC2 行。证明来自 \(K_h\le K_j\)（\(h\ge j\)）及 \(K_h\ge K_j\)（\(h\le j\)）。出现 \(\ell_h'>u_h'\) 时按真实域不相容处理，不能人为夹成合法区间。

**保留父域旧 TC 和 TC2 行，再加子域行。** 整数有效的计数范围并不自动约束父 LP 的所有分数点，不能替换父行后无条件宣称松弛支配。子域行只在对应 count 域有效，不能直接复制回未受限父模型。

若 \(d=u_j-\ell_j\)，取
\(m_{\rm bal}=\ell_j+\lfloor d/2\rfloor\)，两侧最大区间宽为 \(\lfloor d/2\rfloor\)。
选中项的连续最坏弦余量由 \(\Delta_jd^2/4\) 降至至多 \(\Delta_jd^2/16\)。
这是该计数项的误差上界关系，不是完整 BRP 的四倍加速、目标界比例或全局 gap 定理。

### B3. 子域下界、cutoff补集与覆盖界

在子域 \(D_i\) 的改进模型 \(F\le c_i\) 上取得合格 LP 下界 \(\lambda_i\)，按既有保守政策形成

\[
\beta_i\le\min\{\lambda_i,c_i\}.
\]

证明：物理解若 \(F\le c_i\)，其合法 exact-g／辅助扩展落入子模型，故 \(F\ge\lambda_i\)；若 \(F>c_i\)，已有 \(F\ge c_i\)。因此 \(\beta_i\) 对相应物理子域有效。所有数值余量沿用原政策，不另设更松容差。

改进模型被合格证明不可行时，可用 \(c_i\) 的保守值作 floor；**这不等于整个物理子域不可行，不能据此删除该侧或固定 binary。** 只有确证完整子域为空时才可删侧。未合格返回、超时的 primal objective 或未验证 infeasible 状态不当作下界；保留已有合法父界并如实记录。

完整计数覆盖界是
\[
B_{\rm cover}=\min\{\beta_0,\beta_1\},
\]
不能取较强子界、均值或最佳 AM 分数。还需研究两侧不同下界的条件信息；即使该最小值不提升，条件 floor 也可能有用。

cutoff 补集论证只补全目标下界，不会把来源支持上的 \(\ell/u\) 自动推广到更大支持域。后续嵌入须保留来源域和支持的有效范围。

### B4. 一个 binary 的目标界嵌入及 D0 对照

选定一个计数析取后，在需要的原生整数模型上加入一个 binary \(b\)：

\[
K_j\le m+(u_j-m)b,\qquad
K_j\ge\ell_j+(m+1-\ell_j)b,
\]
\[
\boxed{F\ge\beta_0+(\beta_1-\beta_0)b.}\tag{D1}
\]

整数 b=0／1 分别对应两侧。每个原物理可行改进解按自身库存计数落入唯一一侧，并保有满足新行的合法扩展。K 由物理 Y 决定，不以某个虚辅助 g 值选择分组。F 必须是实际完整线性目标，包含 ObjCon。

必要对照 D0 保留同一 binary、两条 count links、选择／probe 流程，仅改成

\[
F\ge\min\{\beta_0,\beta_1\}.\tag{D0}
\]

D1 相对 D0 的包含关系明确。单独考察上述关于(K,F,b)的三条行，连续放松 b 时，该扩展给出以下两个**标量区间上图**的凸包：
\[
S_0=\{(K,F):\ell\le K\le m,\ F\ge\beta_0\},\quad
S_1=\{(K,F):m+1\le K\le u,\ F\ge\beta_1\}.
\]

投影同时保留 \(\ell\le K\le u\)。例如 \(\beta_1\ge\beta_0\) 时，其目标下界为
\[
F\ge\beta_0,\qquad
F\ge\beta_0+(\beta_1-\beta_0)\frac{K-m}{u-m}.
\]
反向时为
\[
F\ge\beta_1,\qquad
F\ge\beta_1+(\beta_0-\beta_1)\frac{m+1-K}{m+1-\ell}.
\]

这说明条件界可通过 K 对根松弛产生作用；它不是完整 BRP 凸包，也不意味着原生求解器实际选择 b 分支。默认 BranchPriority=0，不开发自定义 Native branching callback。

可用 \(\ell=0,u=4,m=1,\beta_0=0,\beta_1=2\) 作极小验证：
\((K,F,b)=(2,0,1/3)\) 满足连续 D0 而违反 D1；
\((2,1,1/2)\) 满足连续 D1，却不满足 binary D1，因为 K=2 强制 b=1、F至少为2。
保留标量见证范围，不将它写成完整 BRP 严格性定理。

---

## C. 已有离线信号与有限 LP 研究

### C1. 已完成的零 Optimize 筛查

R140 diagnostics_and_failures.zip 的 SHA256 为
2cb1ab936753ce9ac26ae1f970b070b2751190af79f6a80a8b0f5d254902bf5f。
对其中五个新 TC2 最优向量，按最大
\(\Delta_j(K_j^*-\ell_j)(u_j-K_j^*)\)
选择非退化计数，并用上述平衡中点分裂，结果如下：

| 角色 | 选中区间 | 父点 K* | m_bal | 包含父点的侧 | 该侧条件 TC2 对父点的违反量 |
|---|---:|---:|---:|---|---:|
| K20 | [0,18] | 7.143095898 | 9 | low | 19.095016971 |
| RB35-T2 | [0,31] | 5.386730572 | 15 | low | 15.834708171 |
| RX35-T2 | [0,30] | 4.016994676 | 15 | low | 9.716437111 |
| K35 | [2,33] | 8.839326581 | 17 | low | 19.770312837 |
| RX20-T1 | [0,16] | 10.385678900 | 8 | high | 28.646798498 |

这些点均满足各自原计数区间。plain 中点限制仍在某一侧保留父最优点，因而仅该限制不能提高两子界的最小值；重算条件弦则切掉了该侧保存点。这是点分离信号，表中是分子 H 的行违反量，**不是目标提升**。

K35 所选阈值为9700060735874915/9007199254740992；
其余四点所选阈值为18014398509481983/18014398509481984，显示时近似1，但不能用十进制1重建 membership。复核必要模型／向量身份和公式后推进新 LP，不再次把整轮消耗在静态代入。

### C2. 默认诊断设计

优先 K35、RB35-T2、K20 三个共同域，每域使用同一结构规则选一个阈值，比较最多两个整数 pivot：

\[
m_{\rm bal}=\ell+\lfloor(u-\ell)/2\rfloor,\qquad
m_{\rm lp}=\max\{\ell,\min(u-1,\lfloor K^*\rfloor)\}.
\]

相同 pivot 去重。每个 pivot 解 plain count 两侧 LP，以及保留父行并追加条件 TC2 的两侧 LP。基础规模最多
\(3\times2\times2\times2=24\)
个 LP；对每域最有信息的一个析取，再用同一来源 \(\beta\) 比较 D0／D1 的共同根 LP。缺失的 Gini 中分参照、必要 RX35 或实际 child 域可在诊断额度内补充或替换重复域。

共同域必须保持输入、目标、支持、g 区间、cutoff和合法U一致；只有矩阵及域身份匹配的旧 Gini 子界可以直接复用。报告原父界、两侧界、完整 cover、D0／D1 重优化值、构造与 LP 成本。不能用最终原生 ObjBound 或不同 cutoff 的缓存冒充共同子 LP 对照。

默认阈值评分是上述加权弦余量，确定 tie 规则。若有明显超出整数 \(\ell/u\) 的 K*，将其作为显式 count-range 违反单列，使用统一合法区间规则处理；不能把负余量或强行裁剪后的数值当成原点评分。固定 \(\ell=u\) 不生成 binary。整数内点 K* 不因“没有分数性”自动排除：条件弦仍可能切除 fractional selector 点。

在小诊断板之后冻结一个统一的 online pivot／选择规则。默认采用一个阈值、一个 pivot、两次 child LP；可依据诊断选择平衡中点或 LP-floor，但不能在完整测试时为每个实例使用其离线最优 pivot。在线若多探测一个候选，必须作为统一规则并计入全部成本，不铺全阈值强分支网格。

### C3. 进入完整候选的依据

以下任一有实际意义的结果可支持有限 pilot：

- qualified cover 界提升；
- cover 未提升，但 D1 相对 D0 的共同根 LP 目标提升；
- D1 在允许 fractional b 的投影中明确分离实际 D0／载体保存点，重优化目标不变，但低实现成本和结构解释支持有限完整检验；不能任意固定 b 后用行违反量代替投影分离。

仅有 \(\beta_0\ne\beta_1\)、单侧强界、很大的弦余量或一条新有效式不直接触发八配置。另将两侧 floor 与同载体已有的 Native 根／早期有效界对照：若两侧均明显低于这一水平，且D1没有实质LP增量或投影分离，就不因两侧数值不同启动完整面板。这是研究优先级依据，不是关于不同模型原生路径的全域冗余定理。若诊断未显示有用信息，可给出清晰边界并结束；无需为完成任务强制实现无信号候选。

还应避免把“用同一binary直接激活两条子TC2”当作已经成立的根加强。本次已对上述五点的平衡／LP-floor共10个组合做零Optimize筛查：以实际序列化父子行之差、各站selector单纯形最大值计算安全M后，全部仍可用fractional b满足links和两条条件行。它可能影响整数搜索，但当前没有父点分离信号；无新证据时不把这一表达机械扩成第二套生产面板。

---

## D. 最小正确实现

### D1. 根部一次、完整方法自付成本

有信号后，在自身 H 和正常根 LP 之后（根已获证关闭则直接结束）、首次需要原生 MIP 之前，为一个冻结计数析取取得两侧证明，并将 D1 行装入原生 artifact。仅在根选择一次；在来源范围内的后续 MIP artifact 可继承同一有效信息，不反复选择阈值或重启原生树。若原AM先拆分Gini root，这份root域有效信息仍可进入包含于来源域的子叶，不照搬R120“第一次MIP必须是L0”的旧限制。

新增独立研究开关和窄作用域proof类型，复用R120的数学／writer做法，不解除当前主线与旧round120_native_proof的禁配规则。没有非退化计数或正常根流程已关闭时记录未触发并沿用既有流程；selector读回异常须明示并定向处理，不为凑两次probe而伪造输入，也不把未实际接入误记为机制失败。

使用已经求得的根 LP selector primal，不新增一次相同 Optimize。现有 round127_root_lp.csv 是可失败的观察性输出；若原接口未可靠返回所需 selector，新增最小的正式读回字段，不把临时 CSV 当在线算法契约，也不误启用历史 R49 减列机制。

两次 count probe 使用独立 artifact／请求及明确局部作用域，不调用会直接更新 Gini scheduler 的普通子叶路径。子模型的 count 行和条件 TC2 必须进入有 SHA 的 canonical artifact；现有 Native 资格不接受仅通过 additional_linear_rows 临时注入的矩阵变更。

新增在线 probe 的构建、求解和验证计入本方法全过程，不导入诊断或别的方法的界、解、Start或树。实验总 cap 继续约束完整运行；不新增“probe运行k秒后切换模式”的算法规则。若全局预算用尽，按既有方式返回已有合法结果并记录未完成部分。

### D2. Count-aware 证据与域继承

现有 NativeEvidenceScope 主要识别 g 区间和 cutoff，单换 source ID 不足以表达 count 子域。需要最小局部扩展，明确绑定物理阈值、整数侧、父支持／域和 cutoff：

- 单侧下界或 infeasible 证据只对该 count 侧有效；另一侧的低目标可行见证不是其矛盾。
- 利用已独立验证的 final_inventory 和同一 dyadic membership 判断见证侧别；父域/global 使用必须经过完整两侧 cover 或合法条件行。
- 若通过 settings_json 保存 scope，确保 Native 参数读回后仍保留该信息；不能被既有 readback 覆盖。
- 沿用现有 source revocation／依赖失效，不把 count probe 当普通 Gini leaf。无需为此重写全局 frontier。

两条 count links、子域加强和目标 floor 绑定同一来源 root/domain/support。cutoff收紧、支持缩小且仍包含于来源域时可继承；域扩大或来源撤销时按既有政策失效。跨 artifact 使用同一精确阈值重新映射现存 selector，不能拿新的阈值数组下标替换旧证明的物理阈值。若子域重建了阈值网格，按实际阈值与冻结阈值的大小关系传播；冻结阈值即使不再出现在新网格中，仍定义同一个合法计数函数。

### D3. Start、writer与资格

Start 的 b 由独立验证的整数 Y 计算：K≤m取0，否则取1。不得按 LP K*、g 或默认0赋值。目标 floor 包含 ObjCon，并正确处理正／负 \(\beta_1-\beta_0\)；写入后的两个 binary 端点均不高估合格 floor，沿用有向系数和行缩放政策。

资格只覆盖真实新增风险：D0／D1矩阵和列类型、两个物理侧的 Start、条件行及常数、同侧／异侧见证、source失效、一个包含后继域和实际 Native 读回。验证必要 tiny／保存整数见证即可，不建立大而重复的测试系统。新开关关闭时保留稳定和旧研究语义。

原生可能消去 binary、在其上分支或仅利用行改善切平面；这些都可接受。没有实际证据时称“计数析取目标界嵌入”，不称“求解器按计数分支”或将全部性能归于 branching。

---

## E. 完整比较与条件扩展

### E1. 一个统一 D1 候选，先四角色

| 角色 | 站点／车辆 | 物理T | 目标 | cap秒 | 作用 |
|---|---:|---:|---|---:|---|
| K-15-S | 15／2 | 3600 | lambda=.15 | 600 | 保留已有快速获证收益 |
| K-20-S | 20／2 | 5400 | lambda=.15 | 1200 | 强根收益与额外proof开销 |
| K-35-U | 35／3 | 10800 | lambda=.15 | 2400 | TC2完整回退能否实质改善 |
| R-B35-S-T2 | 35／3 | 7200 | rho=1，lambda=1/Omega | 2400 | 计数新轴在困难场景上的价值 |

四位置名义 cap 合计6600秒。默认先做 K20／K35，顺序可据 qualification 调整。不要由极短窗口中没出现改善就认定整场无效。

### E2. 必要 D0 与三层比较

默认补 K20、K35 的完整 D0，名义cap3600秒；若 RB35-T2 驱动主要收益或机制结论，再补该角色，合计6000秒。D0 与 D1 使用相同载体、选择规则、links、条件化／probe和参数，只改变最后的 floor；各自独立运行并支付同样在线流程，不能免费读对方的子界。

三层比较分别回答：

| 比较 | 解释范围 |
|---|---|
| D1 vs D0 | 条件目标界的新增作用 |
| D0 vs R140 TC2载体 | count links、binary及共同cover floor的组合变化 |
| D1 vs稳定GI-TBC，并列stock／旧TC参考 | 新完整方法的实际价值及历史位置 |

D0 只覆盖重点归因角色，不强制全八配置。旧 R140 TC2只有五个完整 Seed0角色，不假称另外三格也已测；其余新角色可先与已有稳定／stock／旧TC比较，写明归因范围。

如果 D0 比 D1 更值得保留，允许一次有依据的统一候选调整，并复用已跑身份；从剩余额度重新安排，避免两种方法都机械铺八格。不得按实例使用不同配置。

### E3. 有信息时补余四配置

补 R-X20-S-T1（物理T4800，cap1200）、R-B35-S-T1（T4800，cap2400）、R-X35-S-T1（T4200，cap2400）、R-X35-S-T2（T6300，cap2400），均rho=1、lambda=1/Omega，站点／车辆分别20／2和35／3。

余四名义cap8400秒；主候选八配置合计15000秒。它们是六基础输入的八配置，不是八个新独立实例。若重要回退普遍且没有值得确认的收益，停止扩展。允许有解释力的混合边界，不把每例获胜设为门槛。

### E4. 公平口径及有限 Seed1

匹配旧参考须检查输入、物理参数、目标、cap、Seed、H语义、环境与成本；保留实际源／PE身份，不能把跨版本复用称同PE因果干预。必要新基线由余量补，不重跑健康旧面板。

继续分别报告 U、支持L、signed/relative gap、T_produce、T_cert、T_verify、T_total、Native返回bound与外部合并bound。open的T_cert留空，不以cap冒充收敛时间。probe、root、target和terminal的时间／Work用于解释，完整方法时钟包含它们。

仅当会影响采用或停止判断时，对一个关键角色做最多两方法的 Seed1确认，预算4800秒；选取能够回答该决策的参照，已有匹配结果可复用。默认没有全表双 Seed，也不以不利结果为由不断换Seed。

---

## F. 有限自主探索

首选只完成 B–E 的一个主问题。需要时可在同一诊断预算内尝试一次“计数限制反向收紧库存预算”，不默认叠加多个新机制：

在阈值 j，沿用 R140 forced-high集合 \(H_j\)、optional集合 \(O_j\)、基准最大库存 \(C_{0j}\) 和 optional 高侧最大库存增量 \(d_{ij}\)。低侧 \(K_j\le m\) 给出

\[
\tau\le C_{0j}+\sum_{r=1}^{m-|H_j|}d_{(r)j}^{\downarrow}.
\]

高侧 \(K_j\ge m+1\) 中，令每个 optional 的最小跨阈库存增量为
\(e_{ij}=\min\{y\in\mathcal Y_i:c_iy\ge t_j\}-\min\mathcal Y_i\)，则

\[
\tau\ge\sum_i\min\mathcal Y_i+
\sum_{r=1}^{\max(0,m+1-|H_j|)}e_{(r)j}^{\uparrow}.
\]

与原库存区间相交，至多重算一次必要 stock／TC2。数量超出 optional 范围按不相容或空和的正确情况处理。该步骤只产生必要库存界，不保证路线可行；记录它相对仅嵌套传播的增量。

这是一个条件备选，不要求动态规划、全资源状态枚举或固定点传播。也可选择更直接、同等低成本的相关扩展，说明数学有效性和与历史的区别。若主线无信号，允许以负结果收束，不强制转向逐车产品、全arc-flow、通用H优化、AM网格或第二轮大benchmark。

---

## G. 预算与停止规则

| 内容 | 规划上限 |
|---|---:|
| 同域LP、tiny、实现资格及必要短诊断 | 3600 s |
| 主候选四角色pilot | 6600 s |
| 主候选有依据时补余四角色 | 8400 s |
| 必要D0／有限比较，共享 | 6000 s |
| 单个关键角色的条件Seed1成组比较 | 4800 s |
| 匹配基线、必要修正和机动余量 | 6600 s |
| **总上限** | **36000 s＝10 h** |

典型pilot＋两个D0＋完整诊断额度为13800秒，约3.83小时；主候选八配置＋两个D0＋诊断为22200秒，约6.17小时。提前获证、pivot去重与条件停止会减少实际开销。可合理调剂分项，不要求用满额度，也不将R140未花完预算自动追加。

完整运行按外层全过程计费，嵌套H／probe／LP／MIP不重复累计；资格、失败求解和探索纳入新增实验预算。旧参考保留原成本但不算新计算。构建、离线分析、文稿和公开I/O单列实际开销。

数值／平台问题先利用已有机制做有界定向修复；真实正确性问题必须解决或停用受影响候选。普通表格、文字、文稿、交付metadata修改不触发无关重跑，不再开一轮全面数值工程。

完成标准是：数学主问题得到可审阅回答，所有进入的比较连同不利结果完整报告，版本和费用清楚，稳定入口保留；不是用满10小时、强制跑满八格或自动替换主线。

---

## H. 研究结论、论文内容与独立复核

最终区分三层：

1. **表达与证明：**整数计数覆盖、嵌套传播、条件弦、标量析取目标界各自新增什么；标准工具与本项目问题结构明确分开。
2. **松弛与作用：**plain计数分裂、条件弦、共同cover floor、条件floor分别有哪些同域证据；点分离、最优LP增量和实际原生行为不混淆。
3. **完整表现：**相对本载体及稳定GI-TBC的获证数、时间和U/L，额外probe成本是否值得，重要回退与采用决定是什么。

若条件界无增量，可指出是两侧弱界、源证明信息不足、已有cutoff／原生界支配，或完整搜索未受益等实际观察；不要空泛地以“继续调参”结尾。R137论文整理继续成立；本轮成功也不凭小面板或标准析取公式单独宣称达到某期刊标准。

更新受影响章节或独立研究附录，复用R137完整稿及R138–R140材料。保留推导、严格性边界、紧凑LP／完整表和局限；需要PDF时核查受影响页，不重写整篇。

昂贵完整运行前由非主要实现者检查关键数学与实际writer，收尾再独立核对整合。重点：

1. 阈值与真实支持一致，计数上下界有效，传播方向和integer cover正确。
2. 父行保留；条件行没有无条件泄漏；两子界取min，cutoff不可行不误当整侧不可行。
3. D1/D0和标量凸包推导正确，ObjCon、负delta及binary两个端点正确。
4. count域在Native资格、见证侧别、source依赖中真实存在，不污染Gini scheduler。
5. root数据来自可靠读回；Start按物理Y；跨artifact阈值身份和域范围正确。
6. 在线成本和D0共同部分完整；Seed0/H seed独立；旧参考及实际面板范围不夸大。
7. 6600＋8400主面板、D0共享额度与36000总额核算无重复，条件块没有变成必跑。
8. 历史R50/51、R62、R88、R120–122区别准确；已知同目标返库见证与新静态计数信号没有被忽略。

修正实质问题，提供简明复核结论；无需建立第二套庞大审计体系。

---

## I. 交付、Draft PR与有限收尾

交付本goal、最小代码／配置差异、数学及历史关系说明、实际诊断／完整比较清单、必要raw与汇总、计费、候选决定、增量稿、独立复核和续跑入口。可合并重复报告，内容完整比文件数量重要。新证据绑定实际源码／PE、输入、配置、Native参数和source domain，旧依赖指向固定提交及必要成员。

正常提交、推送研究分支，创建英文Draft PR，建议标题：

**Round141: embed conditional objective bounds from threshold-count disjunctions**

main未吸收R140时，以codex/round140-two-sided-threshold-count为临时base；已吸收时用实际main。读回base/head及交付状态。不自动merge、force-push、删除历史分支、发送邮件或投稿；待合并不阻塞研究验收。

必要新载体做一次有限公开读取核对，纯读/I/O建议累计30分钟内收束，不触发Optimize、编译或商业Native加载。区分本地科学／语义检查和公开字节／成员可读性；失败定向修复，不重开已验收旧轮的全历史恢复。

**显式继承WORKSPACE_POLICY两项要求：**所有新build/raw/temp/restore资产放在E:\codes\ExactEBRP-work；PR交付后，对本轮已完成、可重建的临时／重复对象做有限清理。满足相应证据保留与公开核对条件，保留唯一raw、失败、用户内容、必要PE/DLL和仍需使用的树；不删除旧轮。记录实际删除／保留和字节，零删除也可接受。

最终报告直接回答：计数析取是否比原Gini轴提供了新信息，条件弦与目标界是否真实起作用，完整方法是否受益，稳定入口如何保留，花费多少，还有哪一个最值得继续的问题。

---

## J. 最小资料索引

- R140 PR：https://github.com/yifanXovo/TailoredExact/pull/202
- R140固定科学记录：https://github.com/yifanXovo/TailoredExact/tree/15e401f794bb53e31c5848e0edabf0b4153ca678/results/unified_exact_round140
- 当前入口与工作区：WORKSPACE_POLICY.md；docs/current_mainline.md、round140_research.md、unified_exact_research_index.md；R137稳定launcher/profile。
- R140数学、结果与代码：mathematical_analysis.md、final_report.md、LP_report.md、candidate_decision.json；reports/LP.json、new_arms.csv、reused_arms.csv、control_paths.json；include/Round140Research.hpp、scripts/round140_lp.py及math／Native资格脚本。
- R140真实TC2点：固定science的artifacts/diagnostics_and_failures.zip，经carrier_manifest定位LP/*_tc2_stock的模型、additions、solution.json.gz；按需读必要成员。
- R138旧根与返库见证：固定science 1b19897ab5819ab3b7485ddc978954b45225f361 下的diagnostics封包，K35旧TC＋stock向量与对应canonical矩阵；完整移动x/conn/z/d/p/ord/mode/load车辆块，非车辆列不变。
- R120–R122：results/unified_exact_round120/mathematical_contract.md、对应D0/D1实现与evidence；R121确认和R122final_report。用于复用局部proof注入，保留原混合结果。
- Native与生命周期：src/PaperExternalGiniTree.cpp、GurobiBaseline.cpp、CplexBaseline.cpp、MipStartMapping.cpp；NativeEvidenceScope、见证journal、实际参数读回、source revocation、root LP接口。
- 历史区别：R50/R51 branching优先级、R62 threshold、R66 load-flow、R88 CDF。定向阅读相关结论，不批量恢复全部旧raw。

**本轮成功标准：用有限同域证据检验“计数域收紧能否变成有效的条件证明信息”，在信号成立时以最小根部嵌入检验完整收益；数学可信、工程严谨、成本适当、正反结论完整且稳定主线持续可用。**
