"""Record the result-selected stopping decision and compact reviewable report."""
from round139_common import *
from round139_documents import table
import copy

def main():
    assert not budget()['unclosed'];full=read(OUT/'reports/full.json');assert full['complete'] and len(full['new_arms'])==6
    rows=full['new_arms'];by={(r['role'],r['method']):r for r in rows+full['reused_arms']}
    role='R-B35-S-T2';assert (by[role,'mip-only']['U'],by[role,'mip-only']['L'])==(by[role,'both']['U'],by[role,'both']['L'])
    assert read(OUT/'review/selection_review.json')['decision']=='ACCEPT'
    decision=dict(schema='round139-placement-stage-decision-v1',UTC=utc(),study_complete=True,
        study_complete_scope='Entered scientific comparisons and decision; publication/PR/cleanup are separate delivery steps',
        decision='RETAIN_EXISTING_BOTH_RESEARCH_ONLY_STOP_ASYMMETRIC_EXPANSION',selected_uniform_candidate='both',
        retained_candidate_identity='R138 BOTH; original V1 primary, accepted V2 bridge/entry/Seed1 identities retained',
        stable_entry='scripts/paper_s2.py -> config/gi_tbc_round137.json',new_default_promotion=False,
        entered_pilot_cells=12,new_pilot_positions=6,reused_pilot_cells=6,
        asymmetrically_tested_configurations=3,inherited_full_panel_configurations=8,inherited_base_inputs=6,
        all_new_Gurobi_Seeds=0,H_seed=20260626,formal_nominal_new_caps=8400,
        qualification_nominal_caps=360,total_limit_seconds=57600,charged_seconds=budget()['G1_seconds'],
        full_results_SHA=sha(OUT/'reports/full.json'),selection_review_SHA=sha(OUT/'review/selection_review.json'),
        pilot_discussion='LP-only takes immediate exact-close on all three roles, as BOTH does. K15 certifies in 122.078543 s: it loses BOTH\'s 33.818227 s speed but differs from BASE 112.769303 s by only 9.309240 s, below the 11.276930 s substantive threshold. K20 remains open at cap1200 despite the stronger outer LP and exact-close. RB35-T2 partially recovers U relative to BOTH (.362136827 vs .401200218), but is worse than BASE (.344642626), and its L (.218392595) is below both BASE (.218985950) and BOTH (.229181600). It does not combine their advantages. MIP-only certifies K15/K20 in 34.697528/100.706893 s, with no substantive difference from BOTH. RB35-T2 exactly reproduces BOTH\'s U and L. Neither asymmetric placement supplies a useful complete-method improvement over the existing choices.',
        extension_discussion='D3 uses the already complete, comparable eight-configuration BOTH panel rather than running five unmotivated new asymmetric positions. The remaining five roles have only inherited BASE/BOTH results. The new asymmetric configurations remain research controls, with no eight-role performance claim. This is a result-selected stopping decision on the known panel, not an unseen validation set. D4 introduces no new Seed1 solves: the retained BOTH candidate already has matching accepted paired BASE/BOTH Seed1 on K20 and RB35-T2. Those old results remain separately labelled context; neither LP-only nor MIP-only is represented as having Seed1 evidence. E adds no TC pilot: placement now answers the main question, and the accepted root TC+stock synergy alone does not establish additional practical value.',
        decision_paragraph='Keep the stable Round137 GI-TBC entry unchanged. Retain the existing uniform BOTH formulation as research-only, and stop expanding the two asymmetric placements in this round. Native-only placement preserves the main K15/K20 proof gains but does not reduce the important RB35-T2 upper-bound regression. LP-only does not preserve those proof gains and does not improve both RB35-T2 endpoints over the stable baseline. There is no basis here to promote a new placement or to select placement by instance or size.',
        mechanism_conclusion='The study separates formulation strength, controller decisions and complete performance. Stronger explicit LPs can erase marginal child improvement and change AM from native-target to exact-close. Conversely, MIP-only initially uses the BASE LP and target action, then stock native bounds change the next parent-relative decision. In this finite panel, the main proof gains survive with native-side strengthening but not with outer-LP-only strengthening. Rebuild, retained-model and Start histories are part of each intervention; the four cells do not allocate additive causal runtime shares. The RB35-T2 regression remains a native-search/placement boundary, not an initial-H quality difference or a universal first-solution delay.',
        remaining_question='The remaining algorithmic question is how a uniform valid resource expression can preserve native proof progress without degrading incumbent quality. A focused future experiment could control the paid pre-native model state on the same terminal matrix and Start, or test one structurally motivated resource expression. It should keep separate identities and costs. The present evidence does not call for an AM grid, more general stability auditing, or another numerical/platform repair.',
        conditional_blocks=dict(D1_new_fixed_terminal_diagnostics=0,D2='6 new complete positions; 6 reused cells',
            D3='Existing BOTH eight-role panel reused; no new asymmetric extension',D4='4 old BASE/BOTH Seed1 positions reused as labelled context; 0 new',E='0 new exploration solves'))
    write(OUT/'candidate_decision.json',decision)
    old=ROOT/'results/unified_exact_round138';seed=read(old/'reports/seed1.json');matrix=read(old/'seed1_matrix_frozen.json');reused=[]
    for g in matrix['groups']:
        l=g['launch'];p=l['panel'];assert l['seed']==1 and sha(ROOT/p['input_path'])==p['input_sha256']
        reference=next(r for r in read(OUT/'baseline_reuse.json')['positions'] if r['role']==l['id'])['panel']
        for key in ['input_sha256','T_seconds','lambda','Q_vector','pickup_seconds','drop_seconds','cap_seconds']:
            assert p[key]==reference[key],(l['id'],key)
        identity=read(old/g['group']/'identity.json');r=copy.deepcopy(next(r for r in seed['arms'] if r['role']==l['id'] and r['method']==l['method']))
        r.update(original_method=r['method'],method='base (R138)' if l['method']=='BASE' else 'both (R138 V2)',
            reused=True,new_R139_Optimize=0,science_commit='1b19897ab5819ab3b7485ddc978954b45225f361',
            measured_source_commit=identity['measured_source_commit'],identity_SHA=sha(old/g['group']/'identity.json'))
        reused.append(r)
    write(OUT/'reports/seed1.json',dict(UTC=utc(),arms=reused,Optimize=0,new_R139_Optimize=0,
        original_report_SHA=sha(old/'reports/seed1.json'),original_matrix_SHA=sha(old/'seed1_matrix_frozen.json'),
        selection_rationale='Inherited R138 result-selected limited paired Seed1 on K20 and RB35-T2; this round makes no new Seed1 measurement and no Seed1 claim for either asymmetric placement.',
        discussion='The old K20 proof gain persists on Seed1 (BOTH 90.234798 s; BASE open). The old RB35-T2 U direction reverses: BASE .359553680 versus BOTH .322244842. These separately preserved V2/Seed1 results describe known search sensitivity, do not replace adverse primary Seed0, and are not a distribution estimate or independent holdout.'))
    counts={}
    for name in ['qualification','pilot']:
        path=OUT/'qualification'/f'{name}_actual.json';j=read(path)
        models=[m for p in j['positions'] for m in p['checks']]
        counts[name]=dict(actual_report_SHA=sha(path),unique_artifact_paths=len({m['path'] for m in models}),
            unique_canonical_SHA256s=len({m['SHA'] for m in models}),used_calls=len(models))
    write(OUT/'qualification/identity_count_clarification.json',dict(Optimize=0,counts=counts,
        original_admitted_receipts_unchanged=True,
        scope='The legacy unique_actual_models field counts distinct artifact paths within a batch, not distinct mathematical matrices or SHA256 values. Calls, immutable artifact paths and canonical SHA256 identities are distinct denominators.'))
    b=budget();report='# Round139：库存乘积加强的放置位置与完整求解收益\n\n'
    report+='结论：**停止扩大两种非对称 placement；R138 BOTH 继续 research-only，R137 GI-TBC 保持稳定入口。** 六个新增完整运行和四个资格运行均封存，通过原有完整物理／H／Start／证明审读及新增矩阵检查。新增实验计费 %.6f 秒（%.6f 小时），上限 57,600 秒。\n\n'%(b['G1_seconds'],b['G1_seconds']/3600)
    report+='## 1. 三角色四格的实际结果\n\n'
    report+='以下12格均有实际完整运行：6格复用已验收BASE/BOTH，6格为本轮新增。不是12个新实例，也不是非对称配置的八角色面板。单位为原目标和完整获证秒数；open的T_cert为null，不用cap填补。\n\n'
    report+=table(['角色','placement','验证 U','支持 L','T_cert (s)'],[[role,method,by[role,method]['U'],by[role,method]['L'],by[role,method]['T_cert']] for role in ['K-15-S','K-20-S','R-B35-S-T2'] for method in ['base','both','lp-only','mip-only']])
    report+=decision['pilot_discussion']+'\n\n'
    report+='## 2. 已确认的机制关系\n\n'
    report+='库存RLT的整数有效性、cutoff补集下界min{ell,c}、同域max合并和完整覆盖均沿用原证明政策；LP证据没有冒充原生MIP返回bound。外层LP加强可使父界提升超过左子界提升，令AM边际收益归零。K20 BASE/Stock的第一步分别为native-target/exact-close；MIP-only第一步仍为BASE的native-target，随后stock原生界将父界提升到0.2048257788389711，高于缓存左LP界0.19607825994917552，再进入exact-close。完整收益不能归因于省去约0.33秒target，也不能归因初始H不同。\n\n'
    report+='两种非对称配置在角色转换前显式discard并重新生成不可变artifact，保留原LP证据SHA和有效下界，cutoff epoch仍按旧政策失效。实际LP／target／terminal均按声明放行；00/11小型桥接保持历史canonical SHA。原生模型复用标志、实际Start和日志完整保留，不声称跨改变矩阵迁移了basis或搜索树。\n\n'
    report+=decision['mechanism_conclusion']+'\n\n'
    report+='## 3. 采用、停止与剩余问题\n\n'+decision['decision_paragraph']+'\n\n'+decision['extension_discussion']+'\n\n'+decision['remaining_question']+'\n\n'
    report+='## 4. 成本、身份与证据范围\n\n'
    report+=table(['计费类别','实际秒数'],[['新增完整方法外层',b['by_category']['native']],['资格、Native读回及失败',b['by_category']['diagnostic']],['新增实验合计',b['G1_seconds']],['剩余上限',b['remaining_G1_seconds']]])
    report+='D2名义cap合计8400秒；四个cap90资格位置另计360秒名义额度。D3没有新增五格，D4没有新增Seed1，E没有探索求解。嵌套H／LP／MIP／Work不重复计费；原始基线在比较中保留原完整成本，不虚构新增费用。构建、独立postverification、文稿／公开I/O的实际单独开销见cost_report.json；人工阅读与交互编辑不编造精度。\n\n'
    report+='全部新求解显式Gurobi Seed0，H seed=20260626，单线程串行，TC/AP off，物理T与resource rho=1保留冻结值。首次source commit触发的自动Git维护已在正式pilot前停止；受影响cap90资格时间不用作性能证据。三个不足1秒的资格脚本／Python环境失败均保留且计费，未发生Optimize；没有重复原生运行来修复纯读器。\n\n'
    report+='R138 V1主测、V2修复、Seed1兼构建确认及原载体保持身份。新生产source为6b22433f525df4d1a6ce48a70b5b6414a53aa73b，实际源码／PE／DLL／配置／输入哈希见candidate_manifest.json、candidate_build.json与各batch matrix。Native中间日志是rounded模型目标；所选 K20／RB35-T2 八个封存运行中的所有保存见证按原物理模型重算，并按call区分数值匹配，不把发布时间当首次发现时间。\n\n'
    report+='详细数学见mathematical_analysis.md；实际共同矩阵、旧调用、Start及日志见reports/inherited_mechanisms.json；所有新端点／阶段成本／AM序列与父界见reports/；精确行重数与Native读回见qualification/；原完整审读及追加本地语义检查见local_semantic_check.json。论文增量为manuscript.md/PDF。独立复核见review/。公开载体字节／成员可读性与本地科学语义检查分开记录；本轮不重开R137全public语义恢复或已通过的R138载体检查。\n\n'
    report+='交付后的实际Draft PR、base/head、固定science提交、公开读取、清理和保留项见final_delivery_report.md与RESUME.md；此科学报告本身不把尚未完成的交付步骤写成PASS。\n'
    (OUT/'final_report.md').write_text(report,encoding='utf-8',newline='\n')
    print(decision['decision'])

if __name__=='__main__':main()
