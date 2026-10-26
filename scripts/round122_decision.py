"""The single R122 stage rule, literal finite criteria from the user protocol."""
def decide(values,new_identity_valid,proof_risk=False,blockers=()):
    blockers=list(blockers)
    if not new_identity_valid:blockers.append('necessary_source_or_input_identity_invalid')
    arms=[a for v in values for a in v['arms']];pairs=[p for v in values for p in v['pairs']]
    positions={(v['group']['number'],a['arm']) for v in values for a in v['arms']}
    methods={'P-GRB','ENS-C','M-B','MB-D1'}
    expected_pairs={('MB-D1','P-GRB'),('M-B','P-GRB'),('ENS-C','P-GRB'),('MB-D1','M-B'),('MB-D1','ENS-C'),('M-B','ENS-C')}
    complete=len(values)==8 and {v['group']['number'] for v in values}==set(range(1,9)) and len(arms)==32 and len(pairs)==48 and len(positions)==32
    complete=complete and all({a['arm'] for a in v['arms']}==methods and {(p['candidate'],p['control']) for p in v['pairs']}==expected_pairs for v in values)
    complete=complete and all(a['formal_protocol_qualified'] and a['actually_executed'] for a in arms)
    fresh=[v for v in values if v['group']['number']<=6];seed=[v for v in values if v['group']['number'] in [7,8]]
    primary=[p for p in pairs if (p['candidate'],p['control'])==('MB-D1','P-GRB')]
    freshprimary=[p for v in fresh for p in v['pairs'] if (p['candidate'],p['control'])==('MB-D1','P-GRB')]
    seedprimary=[p for v in seed for p in v['pairs'] if (p['candidate'],p['control'])==('MB-D1','P-GRB')]
    exposures=[];gains=[];large=[]
    for v in fresh:
        e=next((e for e in v['mechanism'] if e['arm']=='MB-D1'),{})
        exposed=e.get('installed',0)>0 and e.get('actual_extended_Optimize',0)>0
        by={a['arm']:a for a in v['arms']}
        gain=any((p['candidate'],p['control'])==('MB-D1','M-B') and p['classification']=='WIN' for p in v['pairs'])
        gain=gain or by.get('MB-D1',{}).get('certificate',False) and not by.get('M-B',{}).get('certificate',False)
        exposures.append(exposed);gains.append(exposed and gain);large.append(exposed and v['group']['V'] in [35,50])
    d1=sum(bool(a['certificate']) for v in fresh for a in v['arms'] if a['arm']=='MB-D1')
    mb=sum(bool(a['certificate']) for v in fresh for a in v['arms'] if a['arm']=='M-B')
    conditions=dict(six_once_only_new_inputs=bool(new_identity_valid) and len(fresh)==6,
        six_new_D1_P_evaluable=len(freshprimary)==6 and all(p['evaluable'] for p in freshprimary),
        at_least_four_new_WIN_at_most_one_LOSS=sum(p['classification']=='WIN' for p in freshprimary)>=4 and sum(p['classification']=='LOSS' for p in freshprimary)<=1,
        at_least_three_new_D1_exposures=sum(exposures)>=3,at_least_one_V35_or_V50_exposure=any(large),
        at_least_two_exposed_material_M_B_gains_or_new_certificates=sum(gains)>=2,new_certificate_count_preserved=d1>=mb,
        both_Seed1_primary_evaluable_and_nonLOSS=len(seedprimary)==2 and all(p['evaluable'] and p['classification']!='LOSS' and not p['severe_regression'] for p in seedprimary),
        no_unresolved_proof_reliability_risk=not proof_risk)
    veto=dict(any_eight_primary_severe=any(p['severe_regression'] for p in primary),at_least_two_new_primary_LOSS=sum(p['classification']=='LOSS' for p in freshprimary)>=2)
    if proof_risk:stage='PROOF_RELIABILITY_PRIORITY'
    elif blockers or not complete:stage='BLOCKED'
    elif any(veto.values()):stage='DO_NOT_SELECT_D1_AS_PAPER_PRIMARY'
    elif all(conditions.values()):stage='FREEZE_D1_AS_PAPER_BENCHMARK_CANDIDATE'
    else:stage='BENCHMARK_MIXED_NO_NEW_PRIMARY_SELECTION'
    return dict(execution_stage='COMPLETE' if complete and not blockers else 'BLOCKED',stage=stage,conditions=conditions,veto=veto,
        formal_arms=len(arms),formal_pairs=len(pairs),formal_arm_denominator=32,formal_pair_denominator=48,
        new_problem_denominator=6,fixed_input_Seed1_blocks=2,new_certificate_counts=dict(D1=d1,M_B=mb),
        new_D1_exposed=sum(exposures),new_exposed_M_B_gains=sum(gains),blockers=list(blockers),default_ENS_changed=False,
        D0_not_promoted=True,MB_PC_stopped=True,no_automatic_further_batch=True,statistical_significance_claim=False)
