ACCEPT：截至 F5 的资格三臂和全部十八正式臂已由独立 reader 重构；允许按冻结 P-GRB/ENS-C/M-B 顺序继续 N36 完整组三臂。无实际原始证据矛盾，尚未作统一 SELECT。

| F5 臂 | 本臂物理 U | 原始合格 L | signed gap | 完整时间 s | 完整证书 |
|---|---:|---:|---:|---:|---|
| M-B | 0.34502127087826651 | 0.28148981625708891 | 0.063531454621177597 | 5371.1998321001 | False |
| P-GRB | 0.41600391010214433 | 0.26873984570837478 | 0.14726406439376954 | 5371.1652424000 | False |
| ENS-C | 0.31394514744033886 | 0.28145380634442851 | 0.032491341095910342 | 5371.2148011000 | False |

M-B/P 是双未证绝对实质性 WIN：UB 改进 0.070982639223877819（门槛 0.0041600391010214437），gap 改进 0.083732609772591948（门槛 0.014726406439376956），无严重 P 退化。M-B/ENS 是 LOSS 且严重 ENS 退化：UB 恶化 0.03107612343792765，gap 恶化 0.031040113525267254，分别超过严重门槛 0.015697257372016944 / 0.0081228352739775855。该对照必须披露，冻结协议未将 ENS 严重退化加入 P 基准取消条件。

固定四角色 S12/B24/L48/N36 仍为已测 TIE/WIN/WIN，2 WIN、0 LOSS、最大最终 WIN=3；F5 为已知压力角色。所有 P primary 有效且无 severe，F5 非 LOSS，early-impossible=false。N36 保持未测固定第四角色，全部 21 臂和最终条件完成前不能 SELECT。

自身第一次 F5 audit01 的 extra source-label assertion 是读者缺陷：原 `GurobiBaseline.cpp:634` 在映射前调用 R100 已存在且内容相同的 `normalizeRound61Routes`。等 Q 类内先按原车号升序收集，再按服务站数降序 stable sort，赋给本类升序车号，空车省略；F5 的车 2/0 交换恰符合该规则。失败 source/command/root/exit1/receipt 和 diagnosis 均保留。第二次审计对所有 source/规范化车队独立核算，再逐项核验完整 x/conn/z/mode/p/d/load/ord/Y/state/G；全行、域、readback、目标与真实 G 均仍通过。24 个有限反例覆盖等 Q 置换、stable ties、空车、跨 Q/任意置换、改变路线/操作/向量及无效车号，实际 exit0，无 native 或算法更改。

本次 raw 审计实际 explicit-root 命令、source/hash/receipt 位于 `confirmation_F5_raw_audit02`，5,837,423 checks、exit0；全前缀 89 实际 Optimize/返回、61 模型、26 submitted Start。全部新车队/UB、原始 LP/MIP 范围、父子/最终覆盖、时序与返回日志均独立重建。

纠正预算为 42 starts / 31400.737309299933 外层秒；N36 全组预留 4 starts / 16320 秒，合计 46 starts / 47720.737309299933 秒，低于 48 / 80000。继续保存启动前手工补充 correction 检查。

Public/report tooling 仅做 source review：新 R98/R99/R102/R105/R106 小报告依赖可从固定 R107 delivery commit 精确取得；历史生产/PE 与当前身份、原有 multi-leaf 暴露均明确区分。未执行打包或公共恢复；最终公共 receipt 叙述须在实际 export/隔离恢复/独立重构完成后才成立。公共载体排除 PE/DLL，与当前 reviewer 的本地 PE 重哈希模式不同，之后隔离 math 模式须显式绑定历史运行 PE 身份并披露缺少二进制重哈希，禁止回读原工作树。

Reviewer 零 Optimize/LP solve/native environment/IIS/compiler，未修改生产/性能/冻结 decision。重 CPU 审查已结束，后续正式组期间保持空闲。
