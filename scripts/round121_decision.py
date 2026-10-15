"""The user's frozen finite candidate/resource decision, no optimization."""
def decide(values,new_identity_valid,proof_risk=False,blockers=()):
    arms=[a for v in values for a in v['arms']];pairs=[p for v in values for p in v['pairs']]
    complete=len(values)==5 and len(arms)==16 and len(pairs)==18 and all(a['formal_protocol_qualified'] and a['actually_executed'] for a in arms)
    primary=[p for p in pairs if p['candidate']=='MB-D1' and p['control']=='P-GRB']
    fresh=[v for v in values if v['group']['number'] in [2,4,5]]
    freshprimary=[p for v in fresh for p in v['pairs'] if p['candidate']=='MB-D1' and p['control']=='P-GRB']
    d1=sum(bool(a['certificate']) for a in arms if a['arm']=='MB-D1');mb=sum(bool(a['certificate']) for a in arms if a['arm']=='M-B')
    exposures=[];gain=[]
    for v in fresh:
        e=next((e for e in v['mechanism'] if e['arm']=='MB-D1'),{})
        exposed=e.get('installed',0)>0 and e.get('actual_extended_Optimize',0)>0
        exposures.append(exposed)
        gain.append(exposed and any(p['candidate']=='MB-D1' and p['control']=='M-B' and p['classification']=='WIN' for p in v['pairs']))
    conditions=dict(three_once_only_postfreeze_new_inputs=bool(new_identity_valid) and len(fresh)==3,
        all_three_new_primary_evaluable=len(freshprimary)==3 and all(p['evaluable'] for p in freshprimary),
        new_primary_at_least_two_WIN_at_most_one_LOSS=sum(p['classification']=='WIN' for p in freshprimary)>=2 and sum(p['classification']=='LOSS' for p in freshprimary)<=1,
        at_least_two_new_D1_native_exposures=sum(exposures)>=2,exposed_new_material_M_B_gain_or_new_certificate=any(gain),
        all_five_primary_evaluable=len(primary)==5 and all(p['evaluable'] for p in primary),
        no_severe_primary_risk=not any(p['severe_regression'] for p in primary),D1_certificate_count_preserved=d1>=mb,
        both_fixed_Seed1_blocks_complete=all(any(v['group']['number']==n and v['group']['seed']==1 and all(a['formal_protocol_qualified'] for a in v['arms']) for v in values) for n in [1,3]))
    veto=dict(any_of_five_severe_D1_P=any(p['severe_regression'] for p in primary),two_or_more_new_D1_P_LOSS=sum(p['classification']=='LOSS' for p in freshprimary)>=2,D1_fewer_certificates_than_M_B=d1<mb)
    if proof_risk:stage='PROOF_RELIABILITY_PRIORITY'
    elif blockers or not complete:stage='BLOCKED'
    elif any(veto.values()):stage='STOP_FROZEN_D1_CONFIRMATION'
    elif all(conditions.values()):stage='ADVANCE_FROZEN_D1_TO_PAPER_BENCHMARK'
    else:stage='RETAIN_D1_AS_DEVELOPMENT_COMPONENT'
    return dict(execution_stage='COMPLETE' if complete and not blockers else 'BLOCKED',stage=stage,conditions=conditions,veto=veto,
        formal_arms=len(arms),formal_pairs=len(pairs),certificate_counts=dict(D1=d1,M_B=mb),new_problem_denominator=3,known_role_Seed1_blocks=2,
        blockers=list(blockers),default_ENS_changed=False,D0_not_promoted=True,no_automatic_further_batch=True,statistical_significance_claim=False)
