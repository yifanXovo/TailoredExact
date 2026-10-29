"""Compact scientific report from entered, qualified comparisons and reviewed decision."""
from round140_common import *
from round140_tables import table,ROLE_ORDER

def main():
    assert not budget()['unclosed']
    full=read(OUT/'reports/full.json');d=read(OUT/'candidate_decision.json');lp=read(OUT/'reports/LP.json')
    assert full['complete'] and d['study_complete'] and not d['new_default_promotion']
    assert read(OUT/'review/selection_review.json')['decision']=='ACCEPT'
    new=sorted(full['new_arms'],key=lambda a:(ROLE_ORDER.index(a['role']),a['method'],a['seed']))
    roles=[r for r in ROLE_ORDER if any(a['role']==r and a['seed']==0 for a in new)];rows=full['reused_arms']+new
    main_rows=[]
    for role in roles:
        for method in ['base','both','TC_STOCK','TC2_STOCK']:
            matches=[a for a in rows if a['role']==role and a['method']==method and a['seed']==0]
            if matches:
                a=matches[0];main_rows.append([role,method,a['U'],a['L'],a['T_cert']])
    b=budget();text='# Round140：库存上下界、双侧阈值计数与完整算法\n\n'
    text+=d['decision_paragraph_zh']+'\n\n'
    text+='本轮保留旧 TC 聚合行并增加 TC2，库存下预算与真实有限支持共同提供站点计数下界；共享 stock 乘积行仍统一放入 LP 与 target/terminal MIP。稳定 R137 入口与 R138/R139 入口保持原样。标准凹弦、cardinality 与 McCormick/RLT 工具本身不作为新理论。\n\n'
    text+='## 结构与严格性范围\n\n'
    text+='数学有效性和实现含义见 mathematical_analysis.md。473 个阈值经“下降收益激活”和“补集库存损失预算”两种构造独立核对。精确有理见证即使 q=gs、J=g*tau 完全一致，旧 TC 与 stock 仍可满足而 TC2 被分离；另一个精确点证明 TC2 单行不能无条件替代旧 TC。12 个建议库存排列均有可行容量2路线，但未冒充完整 cutoff 矩阵严格见证或新的整数闭 gap 结论。\n\n'
    text+='## 有限同域 LP\n\n'
    text+=table(['角色','STK L','STK+TC L','STK+TC+TC2 L','TC2 增量'],[[a['role'],a['stock']['L'],a['tc_stock']['L'],a['tc2_stock']['L'],a['tc2_stock']['L']-a['tc_stock']['L']] for a in lp['roles']])
    text+='主面板为9次新增显式连续 LP；四角色旧 STK/TC+STK 直接复用匹配域记录，RB35-T2 的旧 TC 对照真实补齐。每个共同域的原目标、支持、cutoff、g端点和合法U一致。保存点违反量不代替重新优化的界增量，显式连续LP也不冒充Native MIP根或完整方法。RB35-T2/RX35-T2没有forced-high，界增量由库存下预算产生；RX20所有q=0，其微小增量来自旧零下界弦未使用的forced-high支持信息。\n\n'
    precision=OUT/'reports/LP_precision.json'
    if precision.exists():
        p=read(precision);text+=f'另做2次RX20有限精度确认，FeasibilityTol/OptimalityTol均为1e-9，Seed0、单线程，TC2数值增量为 {p["delta"]:.12g}；主面板和完整方法参数、原结果身份均保持不变。\n\n'
    text+='两条聚合行相对STK不增加列。完整精度 G、H_sum、J、tau、U、ell/u分布、q/forced分解、负系数和常数、构造成本、Native参数及矩阵/解SHA见 reports/LP.json 与封存记录。\n\n'
    text+='## 实际完整算法比较\n\n'
    text+=table(['角色','方法','验证 U','支持 L','T_cert 秒'],main_rows)
    text+=d['complete_discussion_zh']+'\n\n'
    text+=table(['角色','方法','Seed','signed U-L','relative gap'],
        [[a['role'],a['method'],a['seed'],a['signed_gap'],a['relative_gap']] for a in new])
    text+=table(['角色','方法','Seed','T_produce','T_verify','T_total'],
        [[a['role'],a['method'],a['seed'],a['T_produce'],a['T_verify'],a['T_total']] for a in new])
    text+='上表列出全部新增正式完整位置；qualification 单列于原始记录，不进入性能样本。各角色的物理T、目标权重与cap见 reports/new_arms.csv 的独立列，匹配旧参照的全部成本与gap见 reports/reused_arms.csv。\n\n'
    text+='open 的 T_cert 为空，未以cap填充或虚构精确加速比。U/L、signed/relative gap和T_produce/T_cert/T_verify/T_total均在CSV中分别保留；Native返回ObjBoundC和外部合并L也分别报告。每个完整方法从自身H独立启动，不注入其他方法/Seed/诊断的解、界、Start或树；旧参照保留原完整成本与V1/V2身份。\n\n'
    text+='## 可观察机制与条件块\n\n'+d['mechanism_discussion_zh']+'\n\n'+d['conditional_discussion_zh']+'\n\n'
    if (OUT/'reports/seed1.json').exists():
        seed=read(OUT/'reports/seed1.json')
        ordered=sorted(seed['arms'],key=lambda a:['BASE','STOCK','TC_STOCK'].index(a['method']))
        text+=table(['角色','方法','Seed','验证U','支持L','T_cert秒'],
            [[a['role'],a['method'],a['seed'],a['U'],a['L'],a['T_cert']] for a in ordered])
        text+='两项Seed1参照保留原BASE／V2 STOCK的源码、PE及完整时钟，新的TC_STOCK使用本轮PE。这是匹配完整方法比较，不能称为同PE干预；原参照和新运行的生产／验证／总时钟见 reports/seed1_arms.csv。有利确认不覆盖任何Seed0不利结果。\n\n'
    text+='完整运行中的实际LP、target、terminal均由同一canonical writer写入声明的TC/TC2行；域/cutoff/epoch/SHA及原变量类型、H/Start映射和严格证明政策保持。改进域f<=c的LP界仍按min{ell,c}回到完整域，frontier覆盖与原Native证据资格没有放宽。新行改变控制/搜索路径，不提供按行分摊的因果运行时间。\n\n'
    text+='返库产品备选只做离线筛查：四个旧stock点在所记录的数值残差容差内均有W扩展。K35为B=326、tau=295、回库31；旧TC+stock某车R>Q先是线性上界缺失，不能归为产品收益。没有另开第三条完整benchmark支线。\n\n'
    current_path=OUT/'math/return_product_current_points.json'
    if current_path.exists():
        current=read(current_path)
        def obstruction(a):
            return '逐车R界' if not a['return_bounds_feasible'] else ('产品投影' if a['product_signal_beyond_linear_bounds'] else '该点无阻断')
        text+='本轮五个新TC2+stock连续LP最优向量另作零Optimize投影检查，数值残差容差明确为1e-7，先判逐车R界，再判W区间和；数值通过不声称保存二进制向量精确有理可行。这仍是保存点信息，不能代替重新优化的目标增量，也不证明全域冗余。\n\n'
        text+=table(['角色','首个阻断','Bg-J'],[[a['role'],obstruction(a),a['target']] for a in current['cases']])
    text+='## 成本与证据\n\n'
    text+=table(['计费内容','实际秒数'],[['完整方法外层',b['by_category']['native']],['资格/LP/Native读回及失败',b['by_category']['diagnostic']],['新增实验合计',b['G1_seconds']],['剩余额度',b['remaining_G1_seconds']]])
    text+=f'新增实验合计 {b["G1_seconds"]:.6f} 秒（{b["G1_seconds"]/3600:.6f} 小时），上限43200秒。嵌套H/LP/MIP/Work不重复累计。所有实际进入的open/不利结果、资格与失败均保留；纯离线、构建、验证、文稿和公开I/O按实际已测范围单列，不给人工阅读编造精度。完整方法的验证时间独立报告，计费按外层扣除明确分段的纯后验审读。\n\n'
    text+='全部新增主求解显式Seed0、H seed独立20260626，单线程串行；有限Seed1如有则保留单独冻结身份。唯一LP脚本失败发生在Optimize之前，Path类型修正后以独立标签重试；singleton空行问题在资格前修复，前一预审build不进入性能结果。\n\n'
    text+='另有一次纯后验reader在归因组注册但未结束时被提前调用，因缺少closeout退出，Optimize及Native加载均为0；该ordinary失败及显式封存子集修正保留。最终全组本地检查在所有Native位置结束后执行，未重跑原生算法。\n\n'
    text+='candidate_manifest、batch matrices及source_publication绑定实际源码/PE/DLL、输入、配置、Native参数和helper。原完整物理/H/Start/证明reader、实际行检查与本地语义检查分开保存；公开只读是新载体字节/成员可读性，不冒充科学重放，不重开R137-R139历史验收。独立复核见review/；数学及论文增量见mathematical_analysis.md、manuscript.md/PDF。实际Draft PR、base/head、固定science、公开读取、有限清理及保留资产状态见最终交付记录和RESUME.md。\n\n'
    text+='## 最值得继续的问题\n\n'+d['remaining_question_zh']+'\n'
    (OUT/'final_report.md').write_text(text,encoding='utf-8',newline='\n')
    print(d['decision'])

if __name__=='__main__':main()
