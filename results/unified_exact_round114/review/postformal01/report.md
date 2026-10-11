# Round114 独立 postformal 复核

结论：接受这份有限、真实的 BLOCKED 证据交付；G100 四方法采集未完成，ENS-C 与 M-B 仍为 INCOMPLETE_ATTRIBUTION。本签名认可当前证据、失败处理及离线报告修订的真实性，不授予 ENS 超 cap 结果、未启动方法或缺失配对任何性能资格。

P-GRB 是本轮唯一新增合格正式测量：独立 reader U=0.03994210048354935，L=8.782082104514013e-7，signed gap=0.039941222275338896，certificate=false，原 whole=3573.223369550775 秒。原 native readback U=0.03994210048354933 与 gap=0.039941222275338875 保留；两层浮点差在原 1e-7 一致性政策内，没有改写 raw。

ENS-C 原生 rc0、完整正常返回并保存必要证据，但原 whole=3605.688342700014 秒，比冻结的 3600 cap 超出 5.688342700013891 秒。其 process wall=3570.359999999986 秒、必要 audit inclusive=34.928690399974585 秒、whole 减 process=35.32834270002786 秒。这些 inclusive 时间证明当前完成路径未能满足 cap，不能当作可相减的算法因果分量。冻结 finish_arm 在写真实 whole 后实际 assert STOP；wrapper exit1。P-S 与 M-B 的 raw/launch 不存在，未启动。ENS 正式 U/L/gap/certificate 均 null；raw U=0.005528455284552843、raw L=2.20888241772054e-7 与独立 physical U=0.005528455284552848 只作诊断。

|核对项|独立实查结果|
|---|---|
|生产身份|206 生产源与 47 frozen performance helper SHA 全吻合；继承 PE 与 DLL SHA 未变；candidate/admission/campaign 绑定未变|
|P 调用|144 连续 NEJ1 committed events；1 declared/actual/journal-returned/verified-returned Optimize；0 explicit not_started；正常序列化及 cleanup|
|ENS 调用|23 连续 events；4 declared/actual/journal-returned/verified-returned Optimize，LP3 + terminal MIP1；0 partial MIP；env1/model3，全部 cleanup/参数 roundtrip|
|模型与 Start|所有 actual model/log SHA 与 argv/domain/cutoff/ledger 对齐；另行只读回放 ENS terminal 原模型 421423 rows、176866 ordered columns、实际 native Start CSV/readback，quantity I、800 direction B，通过|
|Start 数值限制|实际只读 replay 最大浮点 row/bound residual=1.779909553079051e-12，低于原 1e-6；不能把 sidecar 的 printed 0 当成精确有理数零残差|
|cover/claim|ENS 原 L0 连续 cover [0,0.1584580742872275]，1 open live leaf、5 scoped proofs、11 timeline rows；没有 actual atomic parent replacement；current damaged calls/rejections 均空|
|whole 关闭|own physical/floor evidence、raw-result/observations/completion SHA、claim/rejection/cohort/audit、metrics/progress/closeout 与原 whole 的 SHA/chronology 通过；prewhole pending 字段原样保留|
|资格 raw|两 H100 CLI 的关键文件与日志 SHA 逐一符合已签准入；资格 CLI 不计作性能测量|
|总费用|5 份 fee 均实际退出后 closed；资格 6 starts/189.472980260849 秒，正式 5 declared starts/7178.921706250752 秒，总 11/7368.394686511601；未执行 declared slots 不退款，没有 nested time 相加|

P 冷模型 SHA=c090f8eaa69e23343dddd24fc4d7a9dee1ab8b1885e26493c908099bfd1f6c2d，等于预注册原 compact reference。ENS primary/terminal 模型 SHA=dbd88b82003df5c251e35d999ee1b7ef30b53fc800c7aecacf2118e14bc7b44b；两 child lookahead 模型 SHA 在机器签名内绑定。ENS terminal 的 raw integer_domain_restored=0 没有被改成 1；其真实 MIP native log 记载 87456 integer columns，实际 Start CSV/原 typed LP 的有序列与类型另行核对通过。三个 LP log 未印 Variable types header，该缺失保留为 unknown，LP 身份由实际 ledger、journal scope/条件与 simplex 正常终局交叉核对；没有虚构 native header 数值。

我另用独立小型 stdlib 实现重算两臂最终路线：整数单向取放、station 只访问一次、各 prefix load 在 Q 内、inventory 在原容量内，travel 按输入坐标/1.5，时间按 station handling 加 depot return unloading。结果与 physical_completion 的 Y/D、最大时长一致：P 站22 Y6/D12（−6）、站55 Y18/D10（+8），总绝对差14，max duration=17920.573658299618；ENS 仅站19 Y11/D9（+2），max duration=17824.6158647965。最终 G/P/F 另用 Fraction 从整数 Y/D 和输入十进制 weights 重算，均在原浮点一致性阈值内。非负 objective floor0 成立，两臂均非严格 Y=D；没有 G100 own-zero/零最优证书。最佳 committed witness 分别为 seq143/seq22，原可用上界 2732.372561250697/3323.963134400081 秒；native 真正首次发现时间未知，没有 backfill。

原 admitted reader 的 cap assert 导致真实离线失败。第一次修订只将 cap eligibility 从保留的 chronology/normal/metrics/publication/digest 验证中分出，并把 false 传给原冻结 qualify_endpoint。第二次修订纠正 inherited formal_performance 注记，并明确 planned_formal_position / actually_executed：P true/true/true，ENS false/true/true，两未启动控制 false/true/false。最终 reader SHA=625692f6091a93c49bb08fbcd78ea4c9a74924da705cfafae22def74a0369ef1；原 SHA=825a493416f8380df4fd28cd657153d33531092d394d79291e623449321e48d6 仍由 candidate/admission 绑定，原字节、原失败及两次 diffs/检查保留。独立比较 intermediate reports 与最终 reports：仅明确的三个 metadata 列及 readerSHA 发生变化，其他 numeric/claim/pair/fee/clock 字段严格相等。

明确 E114 root 的最终 offline reader 已独立运行到 reconstructed_final02，实际 3.423341 秒、rc0、0 Optimize，与 reports_final 33 个核心 CSV/JSON 逐字段全等；没有 original-worktree fallback。第一次修订版也已实跑比较，3.398772 秒，现由最终版本承接。全部实际比较对象、命令/耗时及重建文件 SHA 在 signed_review.json；公开载体可排除重复 reconstructed 文件而保留签名中的比较记录。Start replay 实测7.287771500064991 秒，额外交叉核对与 metadata 比较分别0.5602053999900818/0.08936740003991872 秒。审查脚本的三次纯工程失败（语法、LP header 缺失假设、CSV 1800/1800.0 格式比较）和工具实际 wall 记录均保留在机器签名；另一次落盘命令在创建进程前被 Windows 参数长度上限拒绝，改用短只读快照及 apply_patch，拒绝没有产生子进程或改写文件。不记为 solver nominal/qualification 费用。未完整仪器化的审查编排 wall 未知。

旧 16 arm positions 中15 qualified、24 pair positions 中21 evaluable 的全部原有字段语义保留；只规范 CSV 数字格式及新增 evidence layer/恢复 clock 路径，原 identity、原 signed gap、certificate、whole 与分类没有变化。特别保留旧 tiny negative gap，R113 仍 BLOCKED，旧 G50 cold P 无 whole 仍不合格。新增6个 G100 pair 均 UNEVALUABLE，dU/dL/dGap 全 null。总层20 arm positions、16 qualified、30 pairs、21 evaluable、9 unevaluable；ENS W/W/L/W/U、M-B W/W/L/T/U，均4/5 eligible、INCOMPLETE_ATTRIBUTION。full25同H与未启动 backend exposure 缺失，不能由 ENS 诊断 UB 补齐。

本次是正式结束后明确授权的 offline 工程复核，0 native children、0 Optimize、0 qualification driver、0 build；未改 performance helpers、production、raw、clock、identity。只回放当前 ENS Start；旧 LP/旧完整载体未重新解析。所用 root reader 与严格 Start parser 是已审查的同源 stdlib 工具，其共享 parser 限制已披露。当前可用 witness 没有直接反驳 native claim，不推出“没有未来反例”或 Gurobi 内部唯一原因；没有 source-reduced 新臂。未使用本审查对尚未发生的 archive、empty-root restore、whole-goal 或 remote commit 作证明。固定组不重试，剩余预算不是续跑许可；本有限轮优先级3停止决策与保留默认 ENS、cold P benchmark、M-B research candidate 的范围一致。

