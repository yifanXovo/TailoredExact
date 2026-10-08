ACCEPT：资格三臂与规定的桥接六臂已独立从原始证据重建，桥接资源门槛通过。没有发现实际原始证据矛盾。此结论允许下一组完整 S12 三臂按冻结协议进入，尚不构成统一候选 SELECT。

|角色|方法|独立 U|独立 L|signed gap|完整秒|完整证书|
|---|---|---:|---:|---:|---:|---|
|F2|P-GRB|0.8659435203229896|0.76388592095673125|0.10205759936625836|1171.012409900|否|
|F2|ENS-C|0.8659435203229896|0.86594352032298905|5.5511151231257827e-16|539.537072400|是|
|F2|M-B|0.8659435203229896|0.86594351746076648|2.8622231251773655e-09|715.969628100|是|
|C2|ENS-C|0.21679306527176725|0.18969161668595802|0.027101448585809235|1770.988063300|否|
|C2|M-B|0.19463481569156238|0.19066918386459006|0.0039656318269723212|1771.156645800|否|
|C2|P-GRB|0.19830284858382413|0.18663809196048231|0.011664756623341821|1771.028845000|否|

F2 M-B 对 P 为 WIN，来源是候选完整证书；对 ENS 为 LOSS，完整时间增加 176.432555700 秒。C2 M-B 对 P 的 UB ratio=0.9815028734158034、gap ratio=0.3399669581649799，按预定百分比资源门槛通过；对 P 与 ENS 的绝对 materiality 分类均为 WIN。主比较没有 severe regression。

独立脚本 `b12b8bd5581963b6aa1e61321c935abbf54c0b424ce5d47020e9fc553117c449`，实际 exit 0，52.140504900 秒，1,122,989 项检查；读取根目录 `E:/codes/ExactEBRP-round108`，审计 JSON SHA `ddd9cbf31c5f3ff1571be8718315cc7100fe588d738fdbb614b2c32a1f711350`。使用自己的原输入/物理/LP parser，未采用主 reader 的 endpoint、certificate、cover 或 decision 重建；先独立判定，再与修正后纯决策函数和当前主 reader 六臂/pair/gate/fees 对照，结果一致。脚本强制 --root，保存的绝对路径映射到该 root，无原工作树 fallback；可选 --dll 只重新哈希明确指定的当前 DLL 字节。

精确核对 21 个实际模型、33 个成功返回的 native 调用、12 个完整 Start 与各列/各行/物理向量。F2 三个成对区间均仅 80 个 p/d 的 I→C 和 40 个原 A/B 行；C2 三个成对区间均仅 180 个 p/d 的 I→C 和 60 个原 A/B 行。LP/native 证据逐返回或 committed callback 进入时间序列，真实 G 的完整区间 partition 逐段建立 min(proof bound, cutoff) 证据。终端 log 的最后 bound 经同 call/model/leaf/log/返回序列验证后可用，不把 callback 最大值误当全部终端证据。原共享行模式用变量 Bounds 编码 G 域是合法路径。微小 signed gap 保留；未用 U 裁剪发布的最终 L。

C2 原始 overall_global_deadline 与 round31_c6_external_gini_tree_time_limit 是合法预算终止，成功返回且完整开放 cover 保留；不伪造为证书。六个 ENS/M-B 资格/桥接树均保持根父叶，子 LP 是 speculative lookahead，不能作为真实 active-leaf split 的证据。

修正计费已支付 26 保守 starts、8008.932306300 outer 秒；完整 21 臂预计 46 starts。下一完整 S12 组占 4 starts，预留后 30，wrapper outer cap 2820 秒。冻结 wrapper 自带 budget 没有读 supplemental corrections，主代理仍须在启动前做实际修正计数检查；不重算或改写原始回执，不重复加入 native runtime。

主 reader 的四次失败是终端 bound 漏证、冗余 G 行要求、合法 deadline 标签/拼写误拒绝；随后 log-path 绑定强化。独立 reader 的三次失败分别是首 witness 前空 min、native interrupted 字符串大小写、receipt 字段名，失败源/命令/exit 回执均保留。它们是 reader 工程缺陷，不是 solver 重跑或原始测量修补。当前 25 个合成有限例另通过，绑定 reader SHA `61e5acec734139d82c984a457f620a991664500f45d5ac6078cad7e96642e5d9`。

当前生产 PE SHA `4647ee9f146a010ae4bc48f191ec12d4b9113e167b8eeccf0e43a3764e0a8ee0`，DLL SHA `9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88`；candidate、两协议、输入 manifest、所有来源与真实 argv 的完整绑定在 bridge_review01.json 中。后续任何取消都禁止 SELECT；不得用桥接结果推断四个封存确认角色。所有独立工作零 Optimize、零 LP 求解、零 IIS、零 native load、零 build、零生产编辑。
