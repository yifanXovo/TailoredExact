# Round96 进展报告（阶段1完成，整轮未完成）

ENS-C仍是保护默认，LP-G未晋升。原P-GRB是主benchmark。此文件将随本轮推进更新；阶段PR不是研究目标或总体性能目标达成。

已完成：

- 核对本地/远端R95 `bfa4c90f19e19b922f831c7ee97affe1785aff98` 和draft PR157；建立R96分支，保护三个用户修改和全部历史raw。
- [完整数学/算法底稿](mathematical_algorithm.md)补足LP-G稳定分点、同epoch缓存、target后终结与epoch失效的有限性链；[旧账本说明](old_ledger_report.md)分开提案、双子LP、AM、target、原子分裂与终端调用，没有重跑D6。
- 在任何新结果前提交冻结生成规则，保留全部[六个外部输入](external_inputs.json)，V20/V30/V50各二；[18臂协议](external_protocol.md)总cap59400秒，主seed0，原compact参考均零Optimize导出；166个R90源码blob、冻结binary和实际目标/时长系数已核。派生行与writer的数值边界见[numerical_scope.md](numerical_scope.md)，不作任意实数精确声明。
- [长尾数量诊断](fixed_route_report.md)：六个真实R87快照，共1198.5997414进程秒；D7早期与F5早期有合法改善，D7终态/U6仍unknown；F5终态取得完整固定路线数量域数值最优性证书，而P另有更好见证，证明其进一步改善必须超出固定路线集合。
- [三/四站数量原型](multi_quantity_decision.md)：C++可运行、微型突破两站停点，但真实六例在完整两站闭包后均零收益，拒绝生产接入；完整批次54.389762秒。没有以微型成功冒充端到端收益。

尚未完成：LP-G六角色三臂正式确认；进一步区分F5顺序/归属/服务集合的结构诊断；路线结构原型及真实资格、必要OFF/ON/P完整长配对；如有价值的独立原型验证；最终全费用、认证/删失分析及总体决定。因此尚不能回答LP-G是否泛化，也不能宣称长尾最终快于P-GRB。

截至阶段1：1次native micro、6次数量MIP诊断、1次C++微型资格进程、6次真实C++原型诊断，共14次试验进程启动，其中Gurobi Optimize 7次。另有6次零Optimize原compact参考导出及configure/build，分别属于建模/构建成本；保守启动口径把六次导出也计入72次上限，则已20次、余52次。内部任务与native秒不重复相加。native micro上限4次，目前仅1次。

证据包[stage1_evidence.zip](stage1_evidence.zip)保存151个原始文件，逐memberSHA核验；[索引](stage1_archive.json)绑定模型、完整解向量、见证、原生日志、枚举/质量对照和原compact参考。原raw留本地不覆盖。外部输入与原型源码各自冻结，LP-G确认完全不混入新primal模块。

复现/下一步见[恢复说明](RESUME.md)。本阶段未合并任何PR，未更改ENS默认、Gurobi配置或数值容差。
