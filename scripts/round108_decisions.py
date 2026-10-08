"""Stdlib-only frozen comparisons. Caller must independently qualify certificates/values."""
import math

CLOSURE_TOL=1e-7
ZERO_TOL=1e-12
UNSEEN=('S12','B24','L48','N36')

def finite(v):return isinstance(v,(int,float)) and math.isfinite(v)

def qualified_numbers(a):
    good=bool(a.get('numbers_qualified')) and finite(a.get('U')) and finite(a.get('L'))
    if good:
        assert a['L']<=a['U']+CLOSURE_TOL,'contradictory bound: preserve error, never clip'
    return good

def relative(a):
    if not qualified_numbers(a):return None,'missing_or_unqualified_finite_U_L'
    if abs(a['U'])<=ZERO_TOL:return None,'original_zero_objective_tolerance'
    return (a['U']-a['L'])/abs(a['U']),None

def pair(candidate,control):
    c,p=candidate,control
    assert c.get('certificate_qualified') is True and p.get('certificate_qualified') is True,'unresolved certificate qualification'
    cc,pc=c['certificate'],p['certificate']
    value=dict(candidate=c['arm'],control=p['arm'],candidate_U=c.get('U'),candidate_L=c.get('L'),
        control_U=p.get('U'),control_L=p.get('L'),candidate_gap=c.get('gap'),control_gap=p.get('gap'),
        candidate_certified=cc,control_certified=pc,candidate_seconds=c.get('complete_seconds'),control_seconds=p.get('complete_seconds'),
        severe_regression=False,UB_improvement=None,gap_improvement=None,LB_change=None,certified_time_ratio=None,
        UB_ratio=None,gap_ratio=None,percentage_gap_path_applicable=False)
    good=qualified_numbers(c) and qualified_numbers(p)
    if good:
        value.update(UB_improvement=p['U']-c['U'],gap_improvement=p['gap']-c['gap'],LB_change=c['L']-p['L'],
            a_U=max(.001,.01*abs(p['U'])),a_gap=max(.001,.10*abs(p['gap'])))
        if abs(p['U'])>ZERO_TOL:value['UB_ratio']=c['U']/p['U']
        if p['gap']>CLOSURE_TOL and c['gap']>=0:
            value['gap_ratio']=c['gap']/p['gap'];value['percentage_gap_path_applicable']=True
        elif c['gap']<0 or p['gap']<0:
            value['gap_ratio_null_reason']='tiny_negative_signed_gap_retained_no_percentage_division'
    if cc and not pc:
        value['classification']='WIN';value['basis']='candidate_only_complete_certificate'
    elif pc and not cc:
        value.update(classification='LOSS',basis='control_only_complete_certificate',severe_regression=True)
    elif cc and pc:
        assert finite(c['complete_seconds']) and finite(p['complete_seconds']) and p['complete_seconds']>0
        diff=p['complete_seconds']-c['complete_seconds'];a=max(30.,.10*p['complete_seconds'])
        value.update(a_t=a,time_improvement=diff,certified_time_ratio=c['complete_seconds']/p['complete_seconds'],
            classification='WIN' if diff>=a else 'LOSS' if -diff>=a else 'TIE',basis='both_complete_certificate_time',
            severe_regression=c['complete_seconds']>=2*p['complete_seconds'] and -diff>=120)
    elif not good:
        value.update(classification='UNEVALUABLE',basis='both_uncertified_missing_qualified_finite_U_L')
    else:
        improve=value['UB_improvement']>=value['a_U'] or value['gap_improvement']>=value['a_gap']
        worsen=-value['UB_improvement']>=value['a_U'] or -value['gap_improvement']>=value['a_gap']
        value.update(classification='MIXED' if improve and worsen else 'WIN' if improve else 'LOSS' if worsen else 'TIE',
            basis='both_uncertified_absolute_materiality',
            material_UB_improvement=value['UB_improvement']>=value['a_U'],material_gap_improvement=value['gap_improvement']>=value['a_gap'],
            material_UB_worsening=-value['UB_improvement']>=value['a_U'],material_gap_worsening=-value['gap_improvement']>=value['a_gap'],
            severe_regression=-value['UB_improvement']>=max(.001,.05*abs(p['U'])) and
                -value['gap_improvement']>=max(.005,.25*abs(p['gap'])))
    value['evaluable']=value['classification']!='UNEVALUABLE'
    return value

def bridge(arms):
    data={(a['id'],a['arm']):a for a in arms}
    assert len(data)==6 and set(data)=={(r,m) for r in ['F2','C2'] for m in ['P-GRB','ENS-C','M-B']}
    assert len({a['PE_SHA'] for a in arms})==1 and len({a['DLL_SHA'] for a in arms})==1
    gates={}
    for role in ['F2','C2']:
        c,p=data[role,'M-B'],data[role,'P-GRB'];cmp=pair(c,p)
        percentage=qualified_numbers(c) and qualified_numbers(p) and p['gap']>CLOSURE_TOL and c['gap']>=0
        both_open=not c['certificate'] and not p['certificate']
        if role=='F2':
            passed=(c['certificate'] or both_open and percentage and c['U']<=1.01*p['U'] and c['gap']<=1.05*p['gap']) and not cmp['severe_regression']
        else:
            passed=c['certificate'] and not p['certificate'] or c['certificate'] and p['certificate'] and \
                p['complete_seconds']-c['complete_seconds']>=30 and c['complete_seconds']<=.9*p['complete_seconds'] or \
                both_open and percentage and c['U']<=.99*p['U'] and c['gap']<=.80*p['gap']
        gates[role]=dict(passed=bool(passed),percentage_path_applicable=bool(percentage),comparison=cmp)
    return dict(bridge_pass=all(x['passed'] for x in gates.values()),gates=gates,
        primary_benchmark='own current cold P-GRB',hidden_ENS_dominance_condition=False,
        resource_admission_only=True,statistical_significance_claim=False)

def selection(arms,bridge_decision,eligibility,cancelled=()):
    data={(a['id'],a['arm']):a for a in arms};pairs={}
    for role in ['F2','C2','S12','B24','L48','F5','N36']:
        if (role,'M-B') in data and (role,'P-GRB') in data:pairs[role]=pair(data[role,'M-B'],data[role,'P-GRB'])
    if not bridge_decision['bridge_pass']:
        stage='STOP_MB_REOPENING_AT_BRIDGE'
    else:
        same=len({a['PE_SHA'] for a in arms})==1 and len({a['DLL_SHA'] for a in arms})==1
        all_complete=len(arms)==21 and len(data)==21 and not cancelled
        all_eval=len(pairs)==7 and all(x['evaluable'] for x in pairs.values())
        no_severe=not any(x['severe_regression'] for x in pairs.values())
        f5='F5' in pairs and pairs['F5']['evaluable'] and pairs['F5']['classification']!='LOSS'
        unseen_all=all(eligibility.get(r,False) for r in UNSEEN)
        wins=sum(pairs[r]['classification']=='WIN' for r in UNSEEN if r in pairs)
        losses=sum(pairs[r]['classification']=='LOSS' for r in UNSEEN if r in pairs)
        stage='SELECT_MB_FOR_BROAD_EVALUATION' if all_complete and same and all_eval and no_severe and f5 and unseen_all and wins>=2 and losses<=1 else 'NO_NEW_UNIFORM_CANDIDATE_SELECTED'
    return dict(stage=stage,completed_formal_arms=len(arms),cancelled_arms=list(cancelled),primary_pairs=pairs,
        exact_four_unseen_eligibility=eligibility,unseen_WIN=sum(pairs[r]['classification']=='WIN' for r in UNSEEN if r in pairs),
        unseen_LOSS=sum(pairs[r]['classification']=='LOSS' for r in UNSEEN if r in pairs),default_ENS_changed=False,
        no_new_variant_started=True,broad_performance_stability_proved=False)

def early_impossible(arms):
    data={(a['id'],a['arm']):a for a in arms};pairs={}
    for role in ['F2','C2','S12','B24','L48','F5','N36']:
        if (role,'M-B') in data and (role,'P-GRB') in data:pairs[role]=pair(data[role,'M-B'],data[role,'P-GRB'])
    reasons=[]
    if any(p['severe_regression'] for p in pairs.values()):reasons.append('severe_regression_vs_P')
    if any(not p['evaluable'] for p in pairs.values()):reasons.append('UNEVALUABLE_pair_prevents_positive_selection')
    if 'F5' in pairs and pairs['F5']['classification']=='LOSS':reasons.append('F5_LOSS_vs_P')
    observed=[pairs[r] for r in UNSEEN if r in pairs]
    losses=sum(p['classification']=='LOSS' for p in observed)
    possible_wins=sum(p['classification']=='WIN' for p in observed)+4-len(observed)
    if losses>1:reasons.append('unseen_LOSS_limit_already_exceeded')
    if possible_wins<2:reasons.append('maximum_remaining_unseen_WIN_below_two')
    return dict(positive_selection_unreachable=bool(reasons),reasons=reasons,
        cancel_only_after_current_complete_three_arm_group=True)
