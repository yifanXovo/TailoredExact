# 独立阈值状态重映射资格

结论：实际 canonical 列/Y 域上的独立零求解重映射测试通过；源码保留完整语义行并在每个 request 重新映射，未发现正确性阻塞。选定原生共享会话只暴露 FULL 复用，**没有原生 B_THRESHOLD 缺列→可用转换**。此结论不得写成原生阈值转换已发生。

脚本为 `review/independent_threshold_remap.py`，只使用 Python 标准库，不调用生产 mapper、求解器或编译器。结果为 `review/threshold_remap01/result.json`，SHA-256 `db8cf9cc6d3c51cc317dadf907a3e6416b54b5faf366e1f55db03ead1e3e6357`；同目录保存 exclusive launch/process/receipt。Optimize、native、compile、production rows 和 solver fee starts 均为 0。每个实际输入文件的 SHA 保存于结果，当前 source 对选定 `qualification/identity.json` 的绑定一致。

实际 final03/scope/terminal/round107 原始变量表和 original.lp 给出：request_2 的 Y1/Y2/Y4 固定为 1，Y3 为 1..3；request_3 的 Y1/Y2/Y4 为 0..4，Y3 为 0..3。独立检查每个整数 Y 范围恰有对应二进制 state 列，三份 original.lp 都匹配 requests.jsonl 的 canonical SHA。选定语义日志只有一条 FULL 行，逐 request 的 row_0.csv/remap.csv 与独立语义映射完全一致；request_3 的 2 次跨 request 物理缓存命中和 1 次 FULL remap 获得复核，全部 FULL 系数始终有列。

反例另建一个有全局物理证明的有界 B 算术 fixture，使用相同 station 名称、容量 5 和 initial=(3,3,0,1)，Q=3，操作=(+2,+1,-3)。三站和 depot 构成边长 3 的正方形，每个 pickup/drop 各 1 秒，T=19.9；六个原操作顺序全部因前缀或时长不合法，最短闭合 travel=12，严格额外 pickup 预算为 12+2×(3+1)-19.9=0.1>0。原操作总 pickup 为 3；任一严格阈值扩大量使 pickup 至少 4，需要的时长已超过 T。此 fixture 有效性为独立算术层，**不同于 T=100 的选定原生 fixture**。

把该 fixture 的完整语义阈值行独立映射到实际 request_2、再映射到实际 request_3。request_3 恢复旧域缺失的 `state_1_0`、`state_2_0`、`state_2_2`，继续省略 Y3 上界以外的 `state_3_4`、`state_3_5`。新域一热库存 (1,2,3,1)，归属 z1=z2=z3=1 时，旧截短行活动值为 5，完整当前重映射为 6，rhs=5；前者漏拒绝，后者正确拒绝。该库存只主张当前 selector/Y 域合法，未声称满足原生完整 LP 或在原生 MIPSOL 出现。人为移除仍在当前 Y 域内的 `state_2_2` 会明确报错。直接沿用旧列号也会改变实际变量名，例如旧 `state_1_1` 的列在新表中属于 `state_g_1_0`。

源码复核：`Round106Events.cpp` 的 B_THRESHOLD 先枚举 0..capacity 的完整阈值系数；`R107State::add` 先把整个 cut 交给 `R107PhysicalSession::remember`，再依据当前 index 映射；构造每个新 R107State 时遍历完整 `evidence.rows` 并重新 add。缺失 state 只在当前经过审计的整数 Y 域以外允许省略，当前域内缺列是 ERROR；原始全局语义行没有被旧叶的省略操作截短。本结果属于独立算术资格、实际原始域/列 replay 与静态源码绑定三个证据层，原生 FULL 复用作为独立事实保留。
