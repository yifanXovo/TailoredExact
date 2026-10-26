"""Full-precision tables and scientific supplement from sealed evidence only."""
from round135_common import *
import collections
def number(v):
    if v is None:return '-'
    if isinstance(v,float):return format(v,'.17g')
    return str(v)
def table(headers,rows):
    return '| '+' | '.join(headers)+' |\n|'+'|'.join('---' for _ in headers)+'|\n'+''.join('| '+' | '.join(number(v) for v in r)+' |\n' for r in rows)
def fragment(name):
    lines=(OUT/name).read_text(encoding='utf-8').splitlines()
    if lines and lines[0].startswith('#'):lines=lines[1:]
    return '\n'.join(('#'+x if x.startswith('## ') else '##'+x if x.startswith('# ') else x) for x in lines)
def main():
    old=ROOT/'results/unified_exact_round134'
    arms=read(old/'reports/C/arms.json');pairs=read(old/'reports/C/pairs.json')
    weights=read(old/'reports/D/six_points.json');current=read(OUT/'reports/arms.json')
    newpairs=read(OUT/'reports/pairs.json');decision=read(OUT/'candidate_decision.json')
    assert decision['study_complete'] and not budget()['unclosed']
    text='# Supplement: complete evidence and formulation analysis\n\n'
    text+='This supplement retains complete numerical observations and separates evidence versions. C means a qualified certificate; O means open. No open cap is substituted for a certification time. Displayed bounds are original-objective values; gap is signed U-L. Full-precision CSV/JSON files and finite raw carriers are the numerical authorities.\n\n'
    text+='## S1. R134 final implementation: every method position\n\n'
    text+=table(['Position / problem','Seed / repeat','method','proof','U','L','production seconds'],
        [[f"C{r['position']:02} {r['role']}",f"{r['seed']} / {r['repeat']}",r['method'],
        'independent zero' if r['independent_proof'] else 'native/outer' if r['certificate'] else 'O',
        r['U'],r['L'],r['T_produce']] for r in arms])
    text+='\n## S2. R134 complete cost and paired outcomes\n\n'
    text+=table(['Position','production','postverification','total','certification'],
        [[f"C{r['position']:02}",r['T_produce'],r['T_verify'],r['T_total'],r['T_cert']] for r in arms])
    text+='\n'+table(['Problem / Seed / repeat','comparison','class','direction','substantive','S2/control cert seconds'],
        [[f"{r['role']} / {r['seed']} / {r['repeat']}",f"{r['left']}/{r['right']}",r['class'],r['direction'],r['material'],
        f"{number(r.get('left_T_cert'))} / {number(r.get('right_T_cert'))}"] for r in pairs])
    text+='\nEvery adverse direction is retained. In particular X-35-B favors independently paid-start compact at both Seeds. R134 C01 had one failed postreader metadata access, repaired read-only using the same sealed native run. Its real verification delay remains in the costs. Native-source rejection remains visible even when an independent zero argument certifies the original problem.\n\n'
    text+='## S3. Six within-instance weight points\n\n'
    text+=table(['Problem','lambda','effective rho','G','P average','F','U-L','certificate'],
        [[r['role'],r['lambda_value'],r['rho'],r['G'],r['P_avg'],r['F'],r['signed_gap'],r['certificate']] for r in weights])
    text+='\nThe same-feasible-set relations use accepted original-objective errors. Station inventories, target-under/equal/over counts, every vehicle operation, returns, prefix peaks and durations remain in the fixed R134 operations tables. No new weight run is added here.\n\n'
    text+='## S4. AP: preregistration, every entered position and stage decision\n\n'
    text+='The plan fixes seven inputs, 16 pairs and 32 arms: ten first-stage arms with 8,760 cap-seconds and 22 conditional arms with 14,760 cap-seconds. The two methods use the same PE and complete S2 algorithm; only the AP flag differs. Seeds, repeat orders, caps and inputs are fixed in experiment_plan.json and both matrix manifests before results. D13 uses the original physical input and T=3,600; historical subinterval times are not new whole-method controls.\n\n'
    text+=decision['study_scope_paragraph']+'\n\n'
    text+=table(['Position / problem','Seed / repeat','variant','C/O','U','L','U-L','production'],
        [[f"{r['stage']}{r['position']:02} {r['role']}",f"{r['seed']} / {r['repeat']}",r['method'],'C' if r['certificate'] else 'O',
        r['U'],r['L'],r['signed_gap'],r['T_produce']] for r in current])
    text+='\n'+table(['Position','postverification','total','Work','nodes','root LP / child LP / MIP seconds','splits / target MIP'],
        [[f"{r['stage']}{r['position']:02}",r['T_verify'],r['T_total'],r['Work'],r['nodes'],
        ' / '.join(number(r[k]) for k in ('root_lp_seconds','child_lp_seconds','native_MIP_seconds')),
        f"{r['splits']} / {r['target_MIP']}"] for r in current])
    text+='\n'+table(['Problem / Seed / repeat','class','AP-S2 cert seconds','AP-S2 U','AP-S2 L','AP-S2 gap'],
        [[f"{r['role']} / {r['seed']} / {r['repeat']}",r['class'],r.get('left_minus_right_seconds'),
        r['AP_U_minus_S2'],r['AP_L_minus_S2'],r['AP_gap_minus_S2']] for r in newpairs])
    text+='\n'+decision['paper_results_paragraph']+'\n\n'+decision['paper_conclusion_paragraph']+'\n\n'
    text+='## S5. Two incremental AP LPs\n\n'
    roots=read(OUT/'reports/roots.json')
    text+=table(['Root','S2 reused','IND reused','AP new','AP-IND','AP construction / LP seconds','rows / columns / nonzeros'],
        [[r['role'],r['L0_reused'],r['L_IND_reused'],r['L_AP'],r['delta_AP_IND'],
        f"{number(r['construct_AP_seconds'])} / {number(r['native_runtime'])}",
        ' / '.join(str(r['after'][k]) for k in ('rows','columns','nonzeros'))] for r in roots])
    text+='\n'+table(['Root','AP slack','primal row violation','bound violation','dual violation','max row residual'],
        [[r['role'],r['AP_slack'],r['quality']['ConstrVio'],r['quality']['BoundVio'],
        r['quality']['DualVio'],r['quality']['ConstrResidual']] for r in roots])
    text+='\nEach LP adds only the production-audited AP row to the inherited domain, frees all integer types and reoptimizes all auxiliaries. The old S2/IND optima are reused. No new integer solve, cutoff search or TC variation enters this fixed-root comparison. The construction column times Gurobipy row insertion and update; total model export and process costs remain in the qualification and fee records. All production C++ construction is included in the complete-method clocks. Saved physical Start checks are retained. Native OPTIMAL and residuals are numerical observations, not rational optimality proofs.\n\n'
    text+='## S6. AP validity, projection and the tested VD-J antecedent\n\n'+fragment('ap_math_and_history.md')+'\n\n'
    text+='## S7. Retained threshold-count research\n\n'+fragment('threshold_count_supplement.md')+'\n\n'
    text+='## S8. Source provenance\n\n'+fragment('data_provenance.md')+'\n\n'
    text+='## S9. Literature scope and exact remaining author facts\n\n'+fragment('literature_scope.md')+'\n\n'
    text+='## S10. Historical evidence and finite reproduction\n\n'
    text+='R132 breadth retains 17/24 S2, 9/24 P and 4/12 PS qualified certificates under its original policy. R133 retains fourteen exposed qualification positions and its four-pair old/new bridge. R134 retains S2 12/14, P 9/14 and PS 2/4 across 32 method positions. These layers are neither pooled as independent input samples nor relabelled by later source policies. Full older tables remain at their fixed commits, including the [R134 scientific evidence](https://github.com/yifanXovo/TailoredExact/tree/29adc14cf2089442298b409ba2bc06963e77bc14/results/unified_exact_round134), and the R132/R133 citations recorded there.\n\n'
    text+='Current reproduction replays all entered R135 positions and the two AP root coefficient/residual records from exact source-byte and raw carriers. It invokes no Optimize, compiler or vendor DLL. Historical whole campaigns and unentered conditional positions are not reconstructed. Source/PE/DLL/input identity, all ordinary outcomes, failed attempts and measured costs remain separate from the authorship and journal-format checks required before actual submission.\n'
    text+='\n## S11. Maintained historical controls and equivalent-expression proofs\n\n'+fragment('historical_controls_supplement.md')+'\n'
    (OUT/'supplement.md').write_text(text,encoding='utf-8')
    print('Complete supplement written from retained R134 and all entered R135 evidence')
if __name__=='__main__':main()
