"""Evidence-driven stage report; final scientific/editorial review remains explicit."""
from round137_common import *
import collections, math

LABELS=dict(S2="GI-TBC",S2R="GI-TBC-R",P="P",PS="PS",NO_AB="GI-TBC minus A/B",NO_CR="GI-TBC minus C_R",NO_CG="GI-TBC minus C_G",AM004="GI-TBC tau=.04",AM016="GI-TBC tau=.16")

def number(x):return 'null' if x is None else format(x,'.8g') if isinstance(x,(int,float)) else str(x)
def table(headers,rows):return '\n'.join(['| '+' | '.join(headers)+' |','|'+'---|'*len(headers),*['| '+' | '.join(map(number,r))+' |' for r in rows]])+'\n\n'

def main():
    summary=read(OUT/'reports/summary.json');assert summary['completed']==120 and not summary['missing']
    assert not budget()['unclosed']
    arms=read(OUT/'reports/arms.json');pairs=read(OUT/'reports/pairs.json');operations=read(OUT/'reports/operations.json')
    bypos={r['position']:r for r in arms};by={(r['role'],r['seed'],r['method']):r for r in arms}
    mainpairs=[p for p in pairs if p['comparison_kind'] in ['B1','B2']]
    stage=collections.defaultdict(list)
    for r in arms:stage[r['stage']].append(r)
    def cert(stage,method):return sum(r['certificate'] and r['performance_eligible'] for r in globals_rows if r['stage']==stage and r['method']==method)
    globals_rows=arms
    report='# Round137 GI-TBC scientific stage report\n\n'
    report+='All 120 registered positions are retained. This report closes the specified finite consolidation study; actual public recovery, Draft PR and final delivery have separate receipts. Prior R132/R134/R135 observations retain their original versions, proof policies and denominators.\n\n'
    report+='## Accepted method and scope\n\n'
    report+='GI-TBC means **Gini-interval tailored branch-and-cut**. The accepted configuration remains ms2 (historical S2), complete own H, M-B/VD-P shared states, uniform pair-only support, existing interval controller and R134 proof policy, AP off. The compatibility bare-CLI ENS-C identity remains. Explicit research-only single-group controls and actual post-preset AM threshold/readback are the minimal implementation changes; no instance/size/time dispatch is introduced. The zero-Optimize reference fixture matches the accepted R135 default-off matrix, while per-call current model contracts qualify the new runs. Current timings retain the actual newly instrumented PE/source identity.\n\n'
    candidate=read(OUT/'candidate_manifest.json')
    report+=table(['Item','Actual value'],[['Production source commit',candidate['source_commit']],['PE SHA256',candidate['production_PE_SHA']],['DLL SHA256',candidate['DLL_SHA']],['AM / depth / width','.08 /8 /1e-4'],['H / Gurobi Seeds','20260626 /0 main,1 limited repeat'],['Threads / affinity','1 /mask4'],['Physical conventions','Empty departure, loaded return/unloading, unique nonzero one-way service, prefix capacity, depot excluded']])
    report+='## Breadth, startup and adverse/open results\n\n'
    report+=table(['Panel','Method','Eligible certificates','Positions'],[[s,LABELS.get(m,m),cert(s,m),sum(r['method']==m for r in stage[s])] for s in ['B1','B2','B3','D2-main'] for m in ['P','PS','S2']])
    report+='The certificate/position rows count newly executed positions in each stage: B3 has four extra objective configurations per method. The complete weight comparison has six configurations per method after sharing the two actual rho1 B2 baselines; the paired summaries use those declared matching baselines. AM/mechanism views likewise differ from added-position counts, without adding independent inputs.\n\n'
    report+=table(['Panel / contrast','n','Classes','Directions','Both-certified denominator / geometric ratio'],[[s+'/'+c,v['n'],json.dumps(v['classes']),json.dumps(v['directions']),f'{v["both_certified_n"]} /{number(v["both_certified_geomean"])}'] for s in ['B1','B2','B3','D2-main'] for c,v in summary['stages'][s]['comparisons'].items()])
    report+='Geometric ratios condition on both methods certifying; they are not statistics for all open positions. Direction counts include nonmaterial differences, while substantive differences use the declared max(10s,10% of faster time) rule. Main Seed0, weight repeats and preselected Seed1 retain separate denominators.\n\n'
    adverse=[p for p in mainpairs if p['left']=='S2' and p['direction']=='Lose' and (p.get('material') or p['class']=='RIGHT_ONLY_CERTIFIED')]
    report+='Substantive comparator advantages and certificate reversals:\n\n'
    report+=table(['Panel / role','Comparator','Class','GI-TBC Tcert','Comparator Tcert','GI-TBC U/L','Comparator U/L'],[[p['comparison_kind']+'/'+p['role'],p['right'],p['class'],p['left_T_cert'],p['right_T_cert'],f'{number(p["left_U"])} /{number(p["left_L"])}',f'{number(p["right_U"])} /{number(p["right_L"])}'] for p in adverse]) if adverse else 'No substantive main-panel comparator time advantage or certificate reversal was observed under the declared rule; full nonmaterial values remain.\n\n'
    opened=[r for r in arms if r['stage'] in ['B1','B2'] and r['method']=='S2' and not (r['certificate'] and r['performance_eligible'])]
    report+='GI-TBC main-panel unresolved endpoints:\n\n'
    report+=table(['Role','n','U','L','Signed gap','Offline positive floor','Status'],[[r['role'],r['n'],r['U'],r['L'],r['signed_gap'],r['offline_problem_floor'],'open' if r['performance_eligible'] else 'ineligible'] for r in opened]) if opened else 'All GI-TBC main-panel positions were qualified-certified within this finite panel.\n\n'
    tradeoffs=[p for p in mainpairs if p['class']=='BOTH_OPEN' and not p['left_endpoint_dominates'] and not p['right_endpoint_dominates'] and abs(p['left_U_minus_right'])>1e-7 and abs(p['left_L_minus_right'])>1e-7]
    report+='Two-sided endpoint trade-offs (smaller gap alone is insufficient):\n\n'
    report+=table(['Role / contrast','Left U / L','Right U / L'],[[p['role']+f' {p["left"]}/{p["right"]}',f'{number(p["left_U"])} /{number(p["left_L"])}',f'{number(p["right_U"])} /{number(p["right_L"])}'] for p in tradeoffs]) if tradeoffs else 'No strict opposing-U/L main-panel trade-off under tolerance1e-7; complete endpoints remain in pairs.csv.\n\n'
    endpoint_dominance=[p for p in mainpairs if p['class']=='BOTH_OPEN' and (p['left_endpoint_dominates'] or p['right_endpoint_dominates'])]
    report+='Same-budget two-endpoint dominance among both-open pairs:\n\n'
    report+=table(['Role / contrast','Better finite endpoints','Left U / L','Right U / L'],
        [[p['role']+f' {p["left"]}/{p["right"]}',p['left'] if p['left_endpoint_dominates'] else p['right'],
          f'{number(p["left_U"])} /{number(p["left_L"])}',f'{number(p["right_U"])} /{number(p["right_L"])}'] for p in endpoint_dominance]) if endpoint_dominance else 'No strict paired endpoint dominance under tolerance1e-7 in the both-open main subset.\n\n'
    report+='These are feasible/qualified endpoint comparisons at the fixed budget; both-open certification direction remains UNDETERMINED. In particular a paid-start compact run may have a worse feasible objective and lower bound than cold P despite paying complete H. Such cases are retained as finite startup counterexamples, without inferring a distributional or eventual-proof-time ranking.\n\n'
    zero_p=by['N-X20-B',0,'P']
    assert zero_p['source_rejected'] and zero_p['independent_proof'] and not zero_p['native_proof_qualified']
    assert zero_p['certificate'] and zero_p['performance_eligible'] and zero_p['U']==zero_p['L']==0
    report+=(f'Current N-X20-B cold P retains its rejected native source and qualifies its own exact-zero certificate in {number(zero_p["T_cert"])} s through '
        'the independently finalized full-domain nonnegative floor. Three source_bound_witness_contradiction records refer to its one returned native call. '
        'No rejected native bound is revived, no other method supplies the proof, and no historical R132 exclusion is retroactively recounted under this current policy.\n\n')
    startup=[]
    for r in arms:
        if r['method']!='PS':continue
        other=by.get((r['role'],r['seed'],'S2'))
        if other:startup.append(dict(role=r['role'],seed=r['seed'],H_complete=r['H_complete'] and other['H_complete'],
            semantic_match=r['H_semantic_SHA']==other['H_semantic_SHA'],fleet_match=r['H_fleet_SHA']==other['H_fleet_SHA']))
    report+=f'Independent PS/GI-TBC startup comparisons: {len(startup)} matched role/Seed/objective configurations; complete H on both sides in {sum(x["H_complete"] for x in startup)}, matching semantic trace in {sum(x["semantic_match"] for x in startup)}, matching fleet in {sum(x["fleet_match"] for x in startup)}. These are independently paid runs, not transferred Starts. P/PS measures the complete startup package; PS/GI-TBC measures the subsequent complete algorithm conditional on each defined own H. No H-seed grid is justified without a concrete mismatch/sensitivity witness.\n\n'
    repeat_k15={(seed,method):by['K-15-S',seed,method] for seed in [0,1] for method in ['P','PS','S2']}
    assert all(r['performance_eligible'] and r['certificate']==(method=='S2') for (seed,method),r in repeat_k15.items())
    t0=repeat_k15[0,'S2']['T_cert'];t1=repeat_k15[1,'S2']['T_cert']
    assert abs(t0-t1)<max(10,.1*min(t0,t1))
    report+=(f'The preselected K-15-S Seed1 triplet preserves own certification only for GI-TBC, with Seed0/1 certificate costs {number(t0)}/{number(t1)} s '
        '(nonmaterial difference). All six feasible objectives agree, but compact own proof statuses remain open. The final compact L ordering reverses: '
        f'Seed0 P/PS={number(repeat_k15[0,"P"]["L"])}/{number(repeat_k15[0,"PS"]["L"])}, '
        f'Seed1 P/PS={number(repeat_k15[1,"P"]["L"])}/{number(repeat_k15[1,"PS"]["L"])}. '
        'This is one matched finite repeat, separate from the main panel and from the other three preselected roles; no runtime-distribution inference or cross-run certificate transfer follows.\n\n')
    repeat_uc={(seed,method):by['UC-B20-B',seed,method] for seed in [0,1] for method in ['P','PS','S2']}
    assert all(r['performance_eligible'] and r['certificate'] for r in repeat_uc.values())
    report+=(f'UC-B20-B retains all three own certificates at both Seeds. Its GI-TBC times are '
        f'{number(repeat_uc[0,"S2"]["T_cert"])}/{number(repeat_uc[1,"S2"]["T_cert"])} s and P '
        f'{number(repeat_uc[0,"P"]["T_cert"])}/{number(repeat_uc[1,"P"]["T_cert"])} s, while PS changes from '
        f'{number(repeat_uc[0,"PS"]["T_cert"])} to {number(repeat_uc[1,"PS"]["T_cert"])} s. '
        'The PS descriptive clock shift exceeds the declared threshold; the P/GI-TBC shifts do not. The within-role integrated-method advantage persists, but stable certificate status does not imply all runtimes are stable. No distributional claim or replacement of Seed0 follows.\n\n')
    repeat_rb={(seed,method):by['R-B20-S-T1',seed,method] for seed in [0,1] for method in ['P','PS','S2']}
    assert all(r['performance_eligible'] and r['certificate']==(method=='S2') for (seed,method),r in repeat_rb.items())
    a=repeat_rb[0,'S2']['T_cert'];b=repeat_rb[1,'S2']['T_cert'];assert abs(a-b)>=max(10,.1*min(a,b))
    report+=(f'R-B20-S-T1 repeats GI-TBC-only own certification at Seed0/1, with costs {number(a)}/{number(b)} s; their descriptive shift exceeds the substantive rule. '
        f'Seed1 PS reaches the same U={number(repeat_rb[1,"PS"]["U"])} as GI-TBC but remains open with its own L={number(repeat_rb[1,"PS"]["L"])}. '
        f'Cold P improves U from {number(repeat_rb[0,"P"]["U"])} to {number(repeat_rb[1,"P"]["U"])}, while its L falls from {number(repeat_rb[0,"P"]["L"])} to {number(repeat_rb[1,"P"]["L"])}. '
        'The stable certificate pattern does not imply stable clocks or ordered cross-Seed endpoints. No open proof time, transfer or runtime-distribution claim is inferred.\n\n')
    repeat_k35={(seed,method):by['K-35-U',seed,method] for seed in [0,1] for method in ['P','PS','S2']}
    assert all(r['performance_eligible'] and not r['certificate'] and r['T_cert'] is None for r in repeat_k35.values())
    report+=(f'K-35-U keeps all six own runs open. Its Seed1 GI-TBC U/L={number(repeat_k35[1,"S2"]["U"])}/{number(repeat_k35[1,"S2"]["L"])} '
        f'improve both endpoints over P {number(repeat_k35[1,"P"]["U"])}/{number(repeat_k35[1,"P"]["L"])} and PS {number(repeat_k35[1,"PS"]["U"])}/{number(repeat_k35[1,"PS"]["L"])}. '
        'Seed0 retains the opposed P/GI-TBC endpoint result. The compact two-endpoint relation also flips from P better than PS at Seed0 to PS better than P at Seed1. '
        f'GI-TBC improves its own U from {number(repeat_k35[0,"S2"]["U"])} to {number(repeat_k35[1,"S2"]["U"])} while its L weakens from {number(repeat_k35[0,"S2"]["L"])} to {number(repeat_k35[1,"S2"]["L"])}. '
        'No smaller-gap summary replaces these separate endpoints; no own proof or certificate time is transferred.\n\n')
    selected_roles=['K-15-S','UC-B20-B','R-B20-S-T1','K-35-U']
    repeated_counts={(seed,m):sum(by[role,seed,m]['performance_eligible'] and by[role,seed,m]['certificate'] for role in selected_roles) for seed in [0,1] for m in ['P','PS','S2']}
    assert all(repeated_counts[seed,m]=={'P':1,'PS':1,'S2':3}[m] for seed in [0,1] for m in ['P','PS','S2'])
    report+=table(['Method','Selected Seed0 certificates /4','Seed1 certificates /4'],[[LABELS[m],repeated_counts[0,m],repeated_counts[1,m]] for m in ['P','PS','S2']])
    report+='Proof-status counts agree on these preselected roles, while clocks and endpoint orderings can change. The limited repeat does not estimate a runtime distribution and does not replace the main Seed0 panel.\n\n'
    report+='## Physical resources and objective weights\n\n'
    resource_ops=[dict(r,maximum_utilization=r['maximum_duration']/r['T']) for r in operations if r['stage']=='B2']
    report+=table(['Base / T','Method','U','L','G / Pavg','Max duration / T','Returns'],[[r['role'],LABELS.get(r['method'],r['method']),r['U'],r['L'],f'{number(r["G"])} /{number(r["P_avg"])}',number(next(o for o in resource_ops if o['position']==r['position'])['maximum_utilization']),next(o for o in resource_ops if o['position']==r['position'])['returns']] for r in stage['B2']])
    report+='The eight configurations use four serialized shortage bases, all weights positive and rho1. The analytic floors are recomputed from the actual arrays and apply to every method. Dual T changes no other physical/objective field; the design uses depot radius and local supply/handling, not solver outcomes. Route utilization describes the attained feasible plans; it does not prove an optimum is resource-bound. Feasible-set inclusion orders true optimal values, but does not order these finite-budget U/L or runtime observations.\n\n'
    report+='B3 adds two weights at fixed n20/n35 physical configurations and shares only the actual matching rho1 baseline. The full G/Pavg/S and vehicle records retain how weight affects operating choices. Uncertified points are not an exact optimal trade-off curve. Fixed rho removes total weight-scale variation, not geography/relative weights/stock/fleet variation; n-stratified performance is not a causal size experiment.\n\n'
    weight_base=by['R-X35-S-T2',0,'S2'];weight_high=by['R-X35-S-T2-rho2',0,'S2']
    assert weight_base['performance_eligible'] and weight_high['performance_eligible']
    assert weight_base['input_SHA']==weight_high['input_SHA'] and weight_base['T']==weight_high['T']
    assert weight_high['G']<weight_base['G']-1e-7 and weight_high['P_avg']<weight_base['P_avg']-1e-7
    report+=(f'At the fixed n35 physical configuration, the rho2 saved GI-TBC plan has G/P_avg={number(weight_high["G"])}/{number(weight_high["P_avg"])}, '
        f'both below the rho1 saved plan values {number(weight_base["G"])}/{number(weight_base["P_avg"])}. '
        'This post hoc component dominance is a concrete primal-search witness, not an exact optimal weight frontier. All own endpoints and certificate/open identities remain unchanged; no solution, bound or Start crossed production runs.\n\n')
    report+='## AM, four mechanisms and the second Seed\n\n'
    for heading,panels in [('Seed0 main AM/mechanism comparisons',['C1','C2']),('Seed1 limited AM/mechanism repeats',['D2-AM','D2-mechanism'])]:
        report+='### '+heading+'\n\n'
        report+=table(['Panel / variant','Comparisons','Classes','Directions','Material wins / losses'],
            [[s+'/'+c,v['n'],json.dumps(v['classes']),json.dumps(v['directions']),f'{v["material_wins"]} /{v["material_losses"]}']
             for s in panels for c,v in summary['stages'][s]['comparisons'].items()])
    report+='AM uses actual post-preset split_threshold=.04/.08/.16. The finite AM and all-child C6 ledgers are joined by decision sequence; finite score gates, no-strict-improvement terminals, logical one/both-child infeasibility and other actions remain separate, and an empty join has no recorded child decision. Per-decision scores and tolerance-adjusted margins apply only where finite, never to logical infeasibility. The R135 source trajectories were read prospectively: their finite scores are far below the three thresholds; no split was forced. An unchanged action or unexposed finite gate is a scoped sensitivity result, not proof of all parameter robustness. Final materialized-leaf depth/width, decision-parent depth and probed-child depth are distinct observations. Depth 8 / minimum width 1e-4 remain fixed. Recorded guard rows are joined to retained scheduler-epoch geometry; source-rejection reset, missing leaves or other gates remain unknown. Eligible work may stop before its row, so missing rows do not prove no attempted test. Depth failure short-circuits width; width that would also fail is recorded separately from an actual width rejection. A zero-width proof without a recorded guard is not called a width trigger. Offline replay beyond a first divergent action is not a complete runtime counterfactual.\n\n'
    report+=table(['Role / Seed / method','Eligibility evaluations','Depth8 rejections','Width1e-4 rejections','Audit status'],
        [[f'{r["role"]} /{r["seed"]} /{r["method"]}',r['AM_limit_eligibility_evaluations'],r['AM_depth_limit_rejections'],r['AM_width_limit_rejections'],r['AM_limit_trigger_audit']]
         for r in arms if r['stage'] in ['C1','D2-AM'] or r['method']=='S2' and r['role'] in ['K-15-S','K-20-S','UC-B20-B','K-35-U']])
    report+='The four contrasts preserve own H and the physical problem: legal post-R130 full-root GI-TBC-R; deletion of only A/B; deletion of ordered supply and pair cover/conditional handling C_R; deletion of existing geometry/objective estimators and dedicated helpers C_G. Core state products, original domains, binary direction and integer final inventory remain. Continuous p/d stay implicitly integral without A/B. Old MR/MG were not selected and triples were not restored.\n\n'
    report+='Same-domain deletion weakens or preserves an ideal LP bound, with other auxiliaries reoptimized. Complete search follows different native paths, so root/Work/node improvements do not guarantee full-method benefits or endpoint dominance. Root scope/objective/cutoff and complete model/H/LP/MIP costs are retained. Contributions are conditional and cannot be added as speed-up percentages. The limited Seed1 repeats remain preselected checks rather than population runtime statistics or replacements for adverse Seed0 observations.\n\n'
    mechanisms=[p for p in pairs if p['comparison_kind'] in ['C2','D2-mechanism']]
    report+=table(['Contrast / role / Seed','Matched own H','Matched initial domain/objective/cutoff','Optimal-LP attribution exposed','Left-minus-full root LP'],
        [[f'{LABELS.get(p["left"],p["left"])} /{p["role"]} /{p["seed"]}',p['matched_own_H'],p['matched_initial_root_domain_objective_cutoff'],p['root_LP_attribution_exposed'],p['root_LP_left_minus_right']] for p in mechanisms])
    assert len(mechanisms)==24 and all(p['root_LP_attribution_exposed'] for p in mechanisms)
    assert all(abs(p['root_LP_left_minus_right'])<=1e-7 for p in mechanisms if p['left'] in ['NO_CR','NO_CG','S2R'])
    report+='All24 mechanism pairs meet common initial domain/objective/cutoff and complete-own-H conditions. A/B has visible initial-LP increments on K-15-S and K-20-S only (about.000121173 and.001324148); resource and geometry/objective groups show no initial objective increment above1e-7 on these four roles. Root-only reproduces the full initial LP. No visible initial-objective increment does not imply slack, inactive or redundant rows; the optimal face, later native search and final bounds can still differ.\n\n'
    report+='### Complete method clocks and nested cost diagnostics\n\n'
    mechanism_roles={(r['role'],r['seed']) for r in arms if r['stage'] in ['C2','D2-mechanism']}
    mechanism_methods={'S2','S2R','NO_AB','NO_CR','NO_CG'}
    cost_rows=[r for r in arms if (r['role'],r['seed']) in mechanism_roles and r['method'] in mechanism_methods]
    order={'K-15-S':0,'UC-B20-B':1,'K-20-S':2,'K-35-U':3}
    method_order={'S2':0,'S2R':1,'NO_AB':2,'NO_CR':3,'NO_CG':4}
    cost_rows.sort(key=lambda r:(r['seed'],order[r['role']],method_order[r['method']]))
    for seed,heading in [(0,'Seed0 complete costs'),(1,'Seed1 limited-repeat complete costs')]:
        report+='**'+heading+'**\n\n'
        selected=[r for r in cost_rows if r['seed']==seed]
        assert len(selected)==(20 if seed==0 else 10)
        report+=table(['Role / variant','Production s','Own certificate s','Postverification s','Total s'],
            [[r['role']+' / '+LABELS.get(r['method'],r['method']),r['T_produce'],r['T_cert'],r['T_verify'],r['T_total']] for r in selected])
        report+='The following values are nested diagnostic spans/counters; they are not additional budget charges.\n\n'
        report+=table(['Role / variant','H search span s (end status)','Canonical generation s: cumulative / first span','Explicit LP Runtime s: L0 / non-L0','MIP Runtime sum s','Gurobi Work sum','Native B&B nodes sum'],
            [[r['role']+' / '+LABELS.get(r['method'],r['method']),f'{number(r["H_seconds"])} ({r.get("H_phase_end_status")})',
              f'{number(r["model_build_seconds"])} / {number(r["root_model_construction_seconds"])}',
              f'{number(r["root_lp_seconds"])} / {number(r["child_lp_seconds"])}',r['native_MIP_seconds'],r['Work'],r['nodes']] for r in selected])
    report+='H search spans hga_start to decoded_descent_complete with matching labels and ordered events; it excludes earlier instance/configuration work and later log/final-candidate/Start handling. Its recorded end status is shown separately from complete-H qualification. The first canonical-model phase and cumulative artifact-generation timer overlap; neither includes all Gurobi loading, conversion, model management and Start preparation. L0 Runtime can include several explicit LP calls; MIP Runtime already includes its own internal relaxations/presolve/branching/callbacks. Work is not seconds, and summed native B&B nodes are neither outer interval nodes nor cross-call deduplicated nodes. Missing phase pairs stay null with their recorded status. Compact P/PS result counters have a distinct source when no paper ledger exists; zero explicit LP calls do not imply that a MIP had no root relaxation. No time residual is labelled net controller overhead.\n\n'
    k15_repeats={(seed,m):by['K-15-S',seed,m] for seed in [0,1] for m in ['S2','S2R','NO_AB','NO_CR','NO_CG']}
    for m in ['NO_AB','NO_CR','NO_CG']:
        a,b=k15_repeats[0,m]['T_cert'],k15_repeats[0,'S2']['T_cert']
        x,y=k15_repeats[1,m]['T_cert'],k15_repeats[1,'S2']['T_cert']
        assert abs(a-b)>=max(10,.1*min(a,b)) and abs(x-y)>=max(10,.1*min(x,y)) and (a<b)!=(x<y)
    report+=(f'All three K-15-S row-deletion time directions reverse in the preselected Seed1 repeat. Its full cost is {number(k15_repeats[1,"S2"]["T_cert"])} s, versus '
        f'{number(k15_repeats[1,"NO_AB"]["T_cert"])}/{number(k15_repeats[1,"NO_CR"]["T_cert"])}/{number(k15_repeats[1,"NO_CG"]["T_cert"])} s for A/B, resource and geometry/objective deletion. '
        'All six within-Seed comparisons are substantive: full beats A/B and geometry deletion at Seed0 but loses at Seed1; resource deletion wins at Seed0 and loses at Seed1. '
        'The corresponding MIP/Work/node counters, stable initial-LP patterns and matching own H delimit attribution. Two Seeds do not supply stable component rankings, an additive decomposition or evidence for selecting per-instance variants.\n\n')
    hard_mechanisms={r['method']:r for r in cost_rows if r['role']=='K-35-U' and r['seed']==0}
    assert set(hard_mechanisms)==mechanism_methods
    assert all(r['performance_eligible'] and not r['certificate'] and r['T_cert'] is None for r in hard_mechanisms.values())
    assert all(hard_mechanisms[m]['U']<hard_mechanisms['S2']['U']-1e-7 and hard_mechanisms[m]['L']<hard_mechanisms['S2']['L']-1e-7 for m in ['NO_AB','NO_CR','NO_CG'])
    report+='The K-35-U row-deletion pattern is consistent across all three groups: each deletion improves its own verified feasible objective and weakens its qualified final lower bound relative to full GI-TBC. All five variants remain open. Root-only has the same U and slightly higher final L. The four-role Seed0 outer-package check shows no substantive full-over-root certificate-cost advantage on the two easier certified roles; both harder roles remain open with root-only retaining the higher final L. These bounded adverse/limited incremental findings coexist with the integrated-method gains over compact controls and the separately preserved post-R130 history. No additive contribution or per-instance selection follows.\n\n'
    report+='Observed Seed0 mechanism decisions are recorded separately from native solver nodes and from the AM threshold panel:\n\n'
    report+=table(['Role / variant','Finite score gates','No-strict terminals','Logical infeasibility splits','Observed actions'],
        [[r['role']+' / '+LABELS.get(r['method'],r['method']),r['AM_class_counts'].get('FINITE_SCORE_GATE',0),
          r['AM_class_counts'].get('FINITE_TERMINAL_NO_STRICT',0),
          r['AM_class_counts'].get('LOGICAL_ONE_INFEASIBLE',0)+r['AM_class_counts'].get('LOGICAL_BOTH_INFEASIBLE',0),json.dumps(r['AM_actions'])]
         for r in cost_rows if r['seed']==0])
    report+='In particular A/B deletion on K-15-S/K-20-S reaches only the no-strict terminal, whereas full/C_R-deleted/C_G-deleted versions also have a finite native-target gate. The same configured policy may therefore realize different actions after a formulation change. No same-trajectory or MIP-only causal interpretation is inferred from a single-group switch.\n\n'
    report+='## Stage decision and next research\n\n'
    report+='Retain the accepted GI-TBC configuration, tau=.08, pair-only and AP off. This finite consolidation does not select a new mechanism or per-instance setting. Earlier R132 breadth, R134 confirmation and R135 mixed/negative AP results remain scientifically usable with their original identities. The fixed-denominator R133 original-objective gap precludes attributing all hard cases to a changing denominator; R132 strict service-coordinate evidence and R134 TC/AP comparisons are prior results, not unstudied gaps.\n\n'
    dual={m:by['R-X20-S-T1',0,m] for m in ['P','PS','S2']}
    opposed={m:by['K-35-U',0,m] for m in ['P','S2']}
    resource_hard=by['R-X35-S-T2',0,'S2']
    assert all(r['performance_eligible'] for r in [*dual.values(),*opposed.values(),resource_hard])
    assert dual['S2']['certificate'] and all(not dual[m]['certificate'] and abs(dual[m]['U']-dual['S2']['U'])<=1e-7 for m in ['P','PS'])
    assert all(not r['certificate'] for r in [*opposed.values(),resource_hard])
    assert opposed['P']['U']<opposed['S2']['U']-1e-7 and opposed['S2']['L']>opposed['P']['L']+1e-7
    witnesses=(f'R-X20-S-T1 has the same verified U={number(dual["S2"]["U"])} for all three methods, but only GI-TBC certifies; '
        f'K-35-U has P U/L={number(opposed["P"]["U"])}/{number(opposed["P"]["L"])} and GI-TBC {number(opposed["S2"]["U"])}/{number(opposed["S2"]["L"])}; '
        f'R-X35-S-T2 remains open for GI-TBC at U/L={number(resource_hard["U"])}/{number(resource_hard["L"])}, '
        f'and its saved rho1 incumbent is dominated in G/P_avg by the saved rho2 feasible plan at the same physical input/T '
        f'({number(weight_high["G"])}/{number(weight_high["P_avg"])} versus {number(weight_base["G"])}/{number(weight_base["P_avg"])})')
    report+='1. **Positive-objective primal/dual bottlenecks under physical resources.** Witnesses: '+witnesses+'. The first is a dual-proof gap without a missing best feasible objective, the second is an opposed primal/dual endpoint result, and the third retains both a substantial positive-resource gap and an offline witness that its own saved incumbent can improve. These post hoc comparisons do not replace production endpoints or transfer starts. Hypothesis: uniformly valid inventory/service/resource information can improve proof progress while a separate incumbent-search deficit persists on some hard configurations. Minimal next step: inspect saved root-to-final bound and route progress on one retained n35 dual-T pair and K-35-U; separate a primal deficit from a dual deficit before formulating one uniform structural modification. These are research witnesses chosen from the completed study, not new validation positions or a reason for immediate long convergence runs.\n\n'
    report+='2. **Integer inventory and original-objective epigraph information.** R133 J2/J3 retains a 1/4 original-objective gap at fixed S=3 even with the complete tiny joint-service hull; R134 threshold-count (TC) strengthening closes 3/16 on its stated reference but leaves 1/16; its two saved real roots show no reliable further objective increment. Hypothesis: joint integer stock/epigraph/resource information can matter beyond marginal state penalties and labelled service compatibility. Minimal next step: one full-universe valid witness/extension on the saved tiny reference, followed by an explicit real-domain validity interface before production. Do not transplant a four-station support bound after deleting outside suppliers.\n\n'
    hard_am=read(OUT/f'reports/AM/position_{opposed["S2"]["position"]:03}.json')
    assert len(hard_am)==1 and hard_am[0]['exposure_class']=='FINITE_TERMINAL_NO_STRICT' and not hard_am[0]['finite_score_gate']
    observed=hard_am[0]
    report+=(f'3. **AM child information versus complete proof cost.** Witness: K-35-U has decision-state U={number(float(observed["U"]))}, '
        f'parent bound {number(float(observed["B_p"]))} and child bounds {number(float(observed["B_L"]))}/{number(float(observed["B_R"]))}. '
        'The weaker side gives no strict minimum-bound improvement, so the rule schedules exact-close before a finite threshold comparison; the three Seed0 thresholds retain this terminal class and the final runs remain open. '
        'This is not a failed tau crossing. Together with the paired complete-cost records and prior R47/R52 examples, it motivates the hypothesis that structural child asymmetry can distinguish proof effort beyond a scalar two-sided improvement summary. '
        'Minimal next step: one bounded saved-state comparison using the same valid child information and exact coverage, explicitly separating eligibility/no-strict terminal logic from a proposed structural score or continuation. Do not use elapsed machine time to switch algorithm or leaf policy.\n\n')
    account=budget();report+='## Budget, manuscript and remaining facts\n\n'
    report+=f'New native outer computation: **{account["G1_seconds"]:.6f} s ({account["G1_seconds"]/3600:.6f} h)** out of 216000 s; remaining {account["remaining_G1_seconds"]:.6f} s. Planned caps total 174600 s, with 41400 s reserve. Nested H/LP/MIP/Work are not added. Pure verification/build/analysis/PDF/transport have separate measured clocks; elapsed repair delay is preserved in its own row rather than hidden or charged as a repeated solve. The first P postverification AP-contract compatibility error was corrected by pure replay; its producer/result/observations/launch/seal hashes and original production clock did not change. No native retry was used.\n\n'
    report+='No general stability grid is required merely because some components have limited contribution, gates do not change action, Seeds differ, or n35 remains open. The registered main comparisons and limited repeat checks answer the finite questions; unused budget is not a requirement to add tests. Actual source/qualification errors would still require a directed repair, not relabelling as a negative result.\n\n'
    report+='The maintained R135 body/model/algorithm appendices, supplement and references form the current formal draft, with new experiments organized by question. Actual PDF export/visual QA and final independent integration are recorded separately before delivery. Remaining author facts: HGA-TGBC current authors/affiliations/status; this paper\'s author order/affiliations; old CITI443 capture URL/date/selection provenance. No author fact is invented, and no email/submission is performed.\n'
    (OUT/'final_report.md').write_text(report,encoding='utf-8')
    conclusion=(f'GI-TBC retains the accepted shared inventory/service representation, pair-only resource strengthening, complete own startup and Gini-interval coverage. '
        f'On the twelve-input current breadth panel it certifies {cert("B1","S2")}/12, versus P {cert("B1","P")}/12 and PS {cert("B1","PS")}/12; the independent positive-resource panel certifies{cert("B2","S2")}/8, versus P {cert("B2","P")}/8 and PS {cert("B2","PS")}/8. '
        'Substantive comparator reversals, opposing primal/dual endpoints, finite AM/Seed exposure and any open positive-objective 35-station results delimit the conclusion. '
        'The bounded conditional mechanism results include reversals of all three K-15-S deletion-time directions in the preselected second Seed; they do not justify per-instance settings, additive speed-up attribution or a new default. We retain tau=.08 and AP off. '
        'The next study should target an actual positive-objective bottleneck and the established integer-stock/original-epigraph gap, rather than purchase a generic stability grid or relabel previous negative candidates.')
    write(OUT/'candidate_decision.json',dict(UTC=utc(),study_complete=True,decision='RETAIN_ACCEPTED_GI_TBC',
        source_commit=candidate['source_commit'],PE_SHA=candidate['production_PE_SHA'],
        default_AM=.08,AP=False,pair_only=True,new_production_mechanism=False,
        complete_positions=120,budget=account,paper_conclusion=conclusion,
        independent_final_review_and_actual_PDF_QA_separately_required=True))
    write(OUT/'reports/startup_pairs.json',startup)
    print(json.dumps(dict(decision='RETAIN_ACCEPTED_GI_TBC',native_seconds=account['G1_seconds'],adverse_main_pairs=len(adverse),open_GI_main=len(opened))))

if __name__=='__main__':main()
