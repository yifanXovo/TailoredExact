"""Apply the five frozen selection conditions once to all retained observations."""
from round129_common import *
from round127_analysis import qualified

def decide():
    obs=read(OUT/'observations.json');aa=obs['arms'];pp=obs['pairs'];dd=obs['differences']
    m=read(OUT/'input_manifest.json');new=[p['id'] for p in m['new_roles']];protect=m['protection_role']['id']
    a={(x['id'],x['seed'],x['method']):x for x in aa}
    p={(x['id'],x['seed'],x['left'],x['right']):x for x in pp}
    d={(x['id'],x['seed']):x for x in dd}
    def cert(id,s,method):return qualified(a[id,s,method]) and bool(a[id,s,method]['certificate'])
    complete=len(aa)==30 and len(pp)==30 and all(qualified(x) for x in aa) and all(x['classification']!='UNEVALUABLE' for x in pp)
    counts={str(s):{method:sum(cert(id,s,method) for id in new) for method in ['P','MB','MS2']} for s in [0,1]}
    both={method:sum(all(cert(id,s,method) for s in [0,1]) for id in new) for method in ['P','MB','MS2']}
    missed={str(s):{method:sum(cert(id,s,'P') and qualified(a[id,s,method]) and not bool(a[id,s,method]['certificate']) for id in new) for method in ['MB','MS2']} for s in [0,1]}
    rule1=all(counts[str(s)]['MS2']>=counts[str(s)]['MB'] for s in [0,1]) and both['MS2']>=both['MB']
    rule2=all(missed[str(s)]['MS2']<=missed[str(s)]['MB'] for s in [0,1])
    protection=[]
    for s in [0,1]:
        mb,ms=a[protect,s,'MB'],a[protect,s,'MS2'];bc=cert(protect,s,'MB');sc=cert(protect,s,'MS2')
        tcmb,tcms=mb['T_cert'],ms['T_cert']
        loss=tcms-tcmb if bc and sc else None
        protection.append(dict(seed=s,MB_certified=bc,MS2_certified=sc,certificate_retained=not bc or sc,
            MB_T_cert=tcmb,MS2_T_cert=tcms,MS2_minus_MB_seconds=loss,
            slow_at_least_max30_or25pct=bool(bc and sc and loss>=max(30,.25*tcmb))))
    rule3=all(x['certificate_retained'] for x in protection) and not all(x['slow_at_least_max30_or25pct'] for x in protection)
    evidence=[]
    for id in new:
        seeds=[]
        for s in [0,1]:
            sm=p[id,s,'MS2','MB'];sp=p[id,s,'MS2','P'];diff=d[id,s]
            both_cert=sm['classification']=='BOTH_CERTIFIED'
            mb,ms=a[id,s,'MB'],a[id,s,'MS2']
            saving=mb['T_cert']-ms['T_cert'] if both_cert else None
            material=both_cert and saving>=max(10,.1*mb['T_cert'])
            single=sm['classification']=='LEFT_ONLY_CERTIFIED'
            exposure=diff['component_interpretation_eligible'] and diff['triple_deletion_exposed']
            seeds.append(dict(seed=s,MS2_MB_class=sm['classification'],MS2_MB_direction=sm['direction'],
                MS2_P_class=sp['classification'],MS2_P_direction=sp['direction'],
                triple_deletion_exposed=diff['triple_deletion_exposed'],component_interpretation_eligible=diff['component_interpretation_eligible'],
                zero_or_no_backend=not diff['MS2_root_exposed'],MS2_saving_seconds=saving,
                material_gain_threshold=max(10,.1*mb['T_cert']) if both_cert else None,
                both_certified_material_gain=bool(material),MS2_only_certified=single,
                rule4_seed_signal=bool(exposure and (material or single)),rule5_seed_win=sp['direction']=='Win'))
        evidence.append(dict(id=id,seeds=seeds,rule4_both_Seeds=all(x['rule4_seed_signal'] for x in seeds),
            rule5_both_Seeds=all(x['rule5_seed_win'] for x in seeds)))
    rule4=any(x['rule4_both_Seeds'] for x in evidence);rule5=any(x['rule5_both_Seeds'] for x in evidence)
    conditions={str(k):v for k,v in enumerate([rule1,rule2,rule3,rule4,rule5],1)}
    proof_issues=[dict(id=x['id'],seed=x['seed'],method=x['method'],issue='source_reduced') for x in aa if x.get('source_reduced')]
    if proof_issues:tag='PROOF_OR_IDENTITY_ISSUE_REQUIRES_DECISION'
    elif not complete:tag='PARTIAL_NECESSARY_EVIDENCE_MISSING'
    elif not (rule1 and rule2 and rule3):tag='RETAIN_FULL_MB_SIMPLIFICATION_NOT_CONFIRMED'
    elif not (rule4 and rule5):tag='INSUFFICIENT_NEW_DIRECT_SUPPORT_RETAIN_MB'
    else:tag='RECOMMEND_UNIFORM_MS2_AS_PAPER_CANDIDATE'
    descriptions={
        '1':'Retain per-Seed and both-Seed new-problem certification counts relative to MB',
        '2':'Add no per-Seed P-certified/method-open risk relative to MB',
        '3':'Retain every protected MB certificate and avoid a large slowdown at both Seeds',
        '4':'One new input has eligible triple deletion and material MS2/MB support at both Seeds',
        '5':'One new input gives direct MS2/P certification Wins at both Seeds'}
    value=dict(UTC=utc(),execution='COMPLETE' if complete else 'PARTIAL',tag=tag,conditions=conditions,
        condition_descriptions=descriptions,proof_or_identity_issue_observations=proof_issues,
        new_certificate_counts_by_Seed=counts,new_both_Seed_certified_problem_counts=both,
        new_P_certified_method_open_by_Seed=missed,protection=protection,new_input_evidence=evidence,
        rule4_supporting_new_inputs=[x['id'] for x in evidence if x['rule4_both_Seeds']],
        rule5_supporting_new_inputs=[x['id'] for x in evidence if x['rule5_both_Seeds']],
        candidate_mapping=dict(binary='original E2',PE_SHA=E2_SHA,full_MB_mode='--round127-mode mb',uniform_MS2_mode='--round127-mode ms2',
            difference='omit only all triple support cover/conditional rows for every input; retain full frozen remainder'),
        current_paper_identity_and_defaults_changed=False,old_MB_tables_relabelled=False,
        all_fixed_results_retained=True,extra_experiments_to_get_favorable_result=0,
        decision_scope='finite research recommendation, not statistical significance, population dominance or V50/V60 final validation',
        authorities=dict(observations_SHA=sha(OUT/'observations.json'),protocol_SHA=sha(OUT/'experiment_manifest.json')))
    write(OUT/'scientific_decision.json',value)
    text='# Round129 finite candidate selection\n\nExecution: **'+value['execution']+'**. Decision: **`'+tag+'`**.\n\n'
    text+=('All five conditions were frozen before generation and evaluated on the complete qualified fixed panel. ' if complete else 'All five conditions were frozen before generation. Necessary qualified evidence remains incomplete, so the recorded conditions do not authorize promotion. ')
    text+='Four new problems supply the prospective denominator; PB-C20-B is a separate protection role. Seed repeats and shared comparisons are not independent new problems.\n\n'
    text+='| Condition | Requirement | Result |\n| --- | --- | --- |\n'+''.join(f'| {k} | {descriptions[k]} | {v} |\n' for k,v in conditions.items())+'\n'
    text+='Certificate counts by Seed: `'+json.dumps(counts)+'`. Both-Seed-certified problem counts: `'+json.dumps(both)+'`. P-certified/method-open counts: `'+json.dumps(missed)+'`.\n\n'
    text+='New inputs meeting condition 4: `'+json.dumps(value['rule4_supporting_new_inputs'])+'`; condition 5: `'+json.dumps(value['rule5_supporting_new_inputs'])+'`. Full per-Seed support, protection losses and all reverse directions are retained in the JSON decision, arms/pairs and support table.\n\n'
    def support_reason(x):
        if not (x['component_interpretation_eligible'] and x['triple_deletion_exposed']):return 'unexposed or unmatched component scope'
        if x['MS2_only_certified']:return 'MS2-only certificate'
        if x['MS2_MB_class']=='BOTH_CERTIFIED':
            saving=x['MS2_saving_seconds'];threshold=x['material_gain_threshold']
            return f'both certified; saving {saving:.3f}s versus required {threshold:.3f}s'
        return x['MS2_MB_class']
    text+='| New input | Seed0 condition-4 evidence | Seed1 condition-4 evidence | Condition5 at both Seeds |\n| --- | --- | --- | --- |\n'
    for x in evidence:
        text+=f"| {x['id']} | {support_reason(x['seeds'][0])} | {support_reason(x['seeds'][1])} | {x['rule5_both_Seeds']} |\n"
    text+='\nDisplayed times are rounded; all threshold decisions use the unrounded authority.\n\n'
    if tag=='RECOMMEND_UNIFORM_MS2_AS_PAPER_CANDIDATE':
        text+='Recommend one uniform MS2 configuration as the sole method candidate for the next paper revision. Its exact version map is original E2 `--round127-mode mb` to original E2 `--round127-mode ms2`, with only triple support omitted for every input. Adoption requires the user\'s choice: repository defaults, current full-M-B paper identity and historical tables remain intact. A migrated paper must replace every claimed main-method performance table with measurements of that same MS2 version, including the R122 larger roles and R126/R127/R128 historical layers if retained as main-method evidence; old MB numbers cannot be relabelled. This finite panel does not establish V50/V60 safety. No migration experiment is executed here.\n'
    elif tag in ['RETAIN_FULL_MB_SIMPLIFICATION_NOT_CONFIRMED','INSUFFICIENT_NEW_DIRECT_SUPPORT_RETAIN_MB']:
        text+='Retain full frozen M-B / GI-TBC as the sole paper method. The confirmation ends with these fixed data; gains on the development K2 or on the protected role cannot replace missing new support or offset certification risk. No instance-specific selection, threshold tuning, extra Seed/input, dynamic triple selection or fusion is executed.\n'
    elif tag=='PROOF_OR_IDENTITY_ISSUE_REQUIRES_DECISION':text+='A retained source qualification discrepancy requires an explicit decision before scientific promotion. The affected observations are recorded in the JSON authority; do not reinterpret them as ordinary open algorithms or remove them.\n'
    else:text+='Necessary qualified evidence is incomplete, so the five-rule scientific recommendation is not promoted. Retain full M-B pending resolution of the explicitly identified missing evidence; do not count an engineering qualification failure as an ordinary open algorithm.\n'
    text+='\nDeletion of valid rows at an identical scope preserves the physical integer optimum and can only weaken or preserve the mathematical optimal LP lower bound. Certification time has no corresponding monotonicity. This decision uses complete certificates and producer clocks, with null open times and ratios only on both-certified intersections.\n'
    (OUT/'candidate_decision.md').write_text(text,encoding='utf-8')
    print(json.dumps(dict(execution=value['execution'],tag=tag,conditions=conditions,certificate_counts=counts)))

if __name__=='__main__':decide()
