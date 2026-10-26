# D7 B1 cross 零求解资格

新脚本 `scripts/round88_ot_b1_cross.py` SHA256 `356c46b05d527f7b594633e65adc9031ed5da73653b839628dd8d00df0a1c006`；新测试 `tests/round88_ot_b1_cross_test.py` SHA256 `53fb170a7da65126f28c117277168d30b1b35d43329331e8d5caec21a3337b63`。冻结旧 OT 数学/诊断依赖未改，其哈希分别为 `2b8855609cf469098d050fcd9c89efac01b2cb41ee07f023b5a7b79f9ff71840`、`c1cb1776d1b1eef0f03977e00060c1690e5505517d0e4baa71feb3b672fa0756`。

**9/9** 项轻量无求解测试通过：拒绝 B2、错误缩放/G/q、错误系数或符号、低于数值余量的行；拒绝源 SHA、LP/input 字节漂移、父子输入/支持/cutoff/域身份错配；检验有理系数行 ID 与 union 精确去重、重复拒绝；mock 监督验证 Popen 前统一截止、超时 unknown、120 秒值不容修改、部分臂不能冒充完成。`py_compile` 通过。源实物的 v4 prepare 只做哈希、JSON、Fraction 重算及行库写入；脚本内部至行库写完为 `25.2090177` 秒，`exec_command` 外层完整 prepare 命令墙钟 `25.4755013` 秒（含进程及工具开销），优化调用 0。

v4 `load_prepared` 静态复核通过：manifest SHA256 `d1270dc11f1ed99c011028f0287f70b5bcccbbf4c56c6a8f602787f0ad311755`；行库 SHA256 `f35f924ea413fcc16a1b38b3be95d07ae9faeb430d801cded811c42358b7b9e7`；准备成本记录 SHA256 `123093da867b414b4d8a5c01a58e84a49b36d8b67c9a273eec4feadfe72198bd`。全部行由冻结源 raw 选择并重算：根 1184、子 1211、重合 52、并集 2343；共用输入/支持/target/cutoff，六臂输出目录尚未创建。v1/v2/v3 产物与对应测试失败/修正均保留，不作为执行入口。

**未运行真实 LP Optimize**。独立审查及协调者签署单次计算准入后，才可运行合同中的唯一命令；结果只用于 B1 行来源归因，不证明子模型仅缩窄 G，也不证明正式求解器提速。
