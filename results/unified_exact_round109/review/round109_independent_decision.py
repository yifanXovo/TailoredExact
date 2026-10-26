"""Independent R109 fixed panel, pair and stage arithmetic; Python stdlib only.

This module does not import the production reader/decision routines. Physical
and interval-cover qualification is the independent raw kernel's obligation.
Seed checks are repeated inputs, never additional main-panel observations.
"""
import math

ZERO=1e-12
CLOSURE=1e-7
PANEL=(
 ('G20-C1',20,2,'compact',1,'shortage','H',3600,900,('P-GRB','ENS-C','M-B')),
 ('G20-C2',20,2,'compact',2,'balanced','X',7200,900,('ENS-C','M-B','P-GRB')),
 ('G20-R1',20,2,'regional',1,'surplus','H',7200,900,('M-B','P-GRB','ENS-C')),
 ('G20-R2',20,2,'regional',2,'shortage','X',3600,900,('P-GRB','M-B','ENS-C')),
 ('G50-C1',50,4,'compact',1,'balanced','H',7200,1800,('M-B','ENS-C','P-GRB')),
 ('G50-C2',50,4,'compact',2,'surplus','X',18000,1800,('ENS-C','P-GRB','M-B')),
 ('G50-R1',50,4,'regional',1,'shortage','X',7200,1800,('P-GRB','ENS-C','M-B')),
 ('G50-R2',50,4,'regional',2,'balanced','H',18000,1800,('ENS-C','M-B','P-GRB')),
 ('G100-C1',100,8,'compact',1,'surplus','X',18000,3600,('M-B','P-GRB','ENS-C')),
 ('G100-C2',100,8,'compact',2,'shortage','H',7200,3600,('P-GRB','M-B','ENS-C')),
 ('G100-R1',100,8,'regional',1,'balanced','X',7200,3600,('M-B','ENS-C','P-GRB')),
 ('G100-R2',100,8,'regional',2,'surplus','H',18000,3600,('ENS-C','P-GRB','M-B')),
)
SEED_CHECKS=(('G20-C2',900,('P-GRB','M-B')),('G50-R1',1800,('M-B','P-GRB')),('G100-R2',3600,('P-GRB','M-B')))

def finite(x):return isinstance(x,(int,float)) and math.isfinite(x)
def good_numbers(a):
    good=a.get('numbers_qualified') is True and finite(a.get('U')) and finite(a.get('L'))
    if good and a['L']>a['U']+CLOSURE:raise AssertionError('independently qualified contradictory bound')
    return good

def pair(a,c):
    assert a.get('certificate_qualified') is True and c.get('certificate_qualified') is True
    if a['certificate'] and c['certificate'] and not all(finite(v.get('complete_seconds')) for v in (a,c)):
        def clock(v):
            if finite(v.get('complete_seconds')):return [v['complete_seconds'],v['complete_seconds']]
            lo,hi=v['complete_seconds_interval'];assert finite(lo) and finite(hi) and 0<lo<=hi
            return [lo,hi]
        ac,cc=clock(a),clock(c)
        corners=[pair(dict(a,complete_seconds=x),dict(c,complete_seconds=y)) for x in ac for y in cc]
        classes={p['classification'] for p in corners};severities={p['severe_regression'] for p in corners}
        invariant=len(classes)==len(severities)==1
        value=dict(corners[0],candidate_seconds=a['complete_seconds'],control_seconds=c['complete_seconds'],candidate_seconds_interval=ac,control_seconds_interval=cc,
            certified_time_ratio=None,certified_time_ratio_interval=[math.nextafter(ac[0]/cc[1],-math.inf),math.nextafter(ac[1]/cc[0],math.inf)],time_improvement=None,
            time_improvement_interval=[math.nextafter(cc[0]-ac[1],-math.inf),math.nextafter(cc[1]-ac[0],math.inf)],a_t=None if c['complete_seconds'] is None else max(30.,.1*c['complete_seconds']),
            a_t_interval=[max(30.,.1*cc[0]),max(30.,.1*cc[1])],entire_time_rectangle_classification_invariant=invariant,
            classification=next(iter(classes)) if invariant else 'UNEVALUABLE',severe_regression=next(iter(severities)) if invariant else None,evaluable=invariant,
            basis='unchanged inequalities independently invariant over entire bounded time rectangle' if invariant else 'interval crosses original time class or severity boundary')
        return value
    result=dict(id=a['id'],seed=a['seed'],candidate=a['arm'],control=c['arm'],classification=None,severe_regression=False,
        candidate_U=a.get('U'),control_U=c.get('U'),candidate_L=a.get('L'),control_L=c.get('L'),candidate_gap=a.get('gap'),control_gap=c.get('gap'),
        candidate_certified=a['certificate'],control_certified=c['certificate'],candidate_seconds=a['complete_seconds'],control_seconds=c['complete_seconds'],
        UB_improvement=None,gap_improvement=None,LB_change=None,a_U=None,a_gap=None,a_t=None,certified_time_ratio=None,UB_ratio=None,gap_ratio=None)
    good=good_numbers(a) and good_numbers(c)
    if good:
        du=c['U']-a['U'];dg=c['gap']-a['gap'];au=max(.001,.01*abs(c['U']));ag=max(.001,.10*abs(c['gap']))
        result.update(UB_improvement=du,gap_improvement=dg,LB_change=a['L']-c['L'],a_U=au,a_gap=ag)
        if abs(c['U'])>ZERO:result['UB_ratio']=a['U']/c['U']
        if c['gap']>CLOSURE and a['gap']>=0:result['gap_ratio']=a['gap']/c['gap']
    if a['certificate']!=c['certificate']:
        result.update(classification='WIN' if a['certificate'] else 'LOSS',severe_regression=bool(c['certificate']),basis='one_complete_certificate')
    elif a['certificate']:
        assert finite(a['complete_seconds']) and finite(c['complete_seconds']) and c['complete_seconds']>0
        dt=c['complete_seconds']-a['complete_seconds'];at=max(30.,.10*c['complete_seconds'])
        result.update(classification='WIN' if dt>=at else 'LOSS' if -dt>=at else 'TIE',severe_regression=a['complete_seconds']>=2*c['complete_seconds'] and -dt>=120,
            a_t=at,time_improvement=dt,certified_time_ratio=a['complete_seconds']/c['complete_seconds'],basis='both_complete_certificate_time')
    elif not good:result.update(classification='UNEVALUABLE',basis='both_uncertified_missing_finite_qualified_U_L')
    else:
        better=du>=au or dg>=ag;worse=-du>=au or -dg>=ag
        result.update(classification='MIXED' if better and worse else 'WIN' if better else 'LOSS' if worse else 'TIE',
            severe_regression=-du>=max(.001,.05*abs(c['U'])) and -dg>=max(.005,.25*abs(c['gap'])),basis='both_uncertified_absolute_materiality')
    result['evaluable']=result['classification']!='UNEVALUABLE'
    return result

def selection(arms,eligibility,unresolved=()):
    keys=[(a['id'],a['seed'],a['arm']) for a in arms];data=dict(zip(keys,arms))
    expected={(r[0],0,m) for r in PANEL for m in ('P-GRB','ENS-C','M-B')} | {(r,1,m) for r,_,methods in SEED_CHECKS for m in methods}
    main={};seed={};extra=[]
    for role,seedvalue,methods in [(r[0],0,('P-GRB','ENS-C','M-B')) for r in PANEL]+[(r,1,ms) for r,_,ms in SEED_CHECKS]:
        if (role,seedvalue,'M-B') in data and (role,seedvalue,'P-GRB') in data:
            target=main if seedvalue==0 else seed
            target[role]=pair(data[role,seedvalue,'M-B'],data[role,seedvalue,'P-GRB'])
        if seedvalue==0 and all((role,0,m) in data for m in methods):
            extra.extend([pair(data[role,0,'M-B'],data[role,0,'ENS-C']),pair(data[role,0,'ENS-C'],data[role,0,'P-GRB'])])
    complete=len(keys)==len(data)==42 and set(data)==expected
    same=len({a['PE_SHA'] for a in arms})==len({a['DLL_SHA'] for a in arms})==1
    qualified=all(a.get('certificate_qualified') is True for a in arms)
    all_eligible=set(eligibility)=={r[0] for r in PANEL} and all(eligibility.values())
    wins=sum(p['classification']=='WIN' for p in main.values());losses=sum(p['classification']=='LOSS' for p in main.values())
    main_evaluable=len(main)==12 and all(p['evaluable'] for p in main.values())
    seed_evaluable=len(seed)==3 and all(p['evaluable'] for p in seed.values())
    severe=sum(p['severe_regression'] is True for p in main.values())
    seed_severe=sum(p['severe_regression'] is True for p in seed.values())
    strata={}
    for name,roles in [(str(v),[r[0] for r in PANEL if r[1]==v]) for v in (20,50,100)]+[(g,[r[0] for r in PANEL if r[3]==g]) for g in ('compact','regional')]:
        strata[name]=sum(main[r]['classification']=='WIN' for r in roles if r in main)
    flips=[r for r,_,_ in SEED_CHECKS if r in seed and r in main and main[r]['classification']=='WIN' and seed[r]['classification']=='LOSS']
    nonloss=sum(p['classification']!='LOSS' for p in seed.values())
    reasons=[]
    if severe:reasons.append('SEVERE_P_REGRESSION')
    if losses>2:reasons.append('TOO_MANY_P_LOSSES')
    if wins<6:reasons.append('INSUFFICIENT_P_WINS')
    if any(n<1 for n in strata.values()):reasons.append('MISSING_STRATUM_GAIN')
    if seed_severe or nonloss<2 or flips:reasons.append('SEED_SENSITIVITY')
    if not main_evaluable or not seed_evaluable:reasons.append('UNEVALUABLE_COMPARISON')
    faults=list(unresolved)
    if not complete:faults.append('incomplete_or_wrong_exact42')
    if not same:faults.append('not_one_PE_DLL')
    if not qualified:faults.append('unresolved_certificate_scope')
    if not all_eligible:faults.append('ineligible_or_unresolved_exact12_at_freeze')
    stage='BLOCKED' if faults else 'BROAD_PANEL_NOT_SUPPORTED' if reasons else 'BROAD_PANEL_SUPPORT'
    return dict(stage=stage,reason_codes=reasons,blocking_reasons=faults,completed_formal_arms=len(arms),exact_main_denominator=12,exact_seed_groups=3,
        main_WIN=wins,main_LOSS=losses,main_severe_P_regressions=severe,main_pairs=main,seed1_pairs=seed,other_main_pairs=extra,
        stratum_WIN=strata,seed1_nonLOSS=nonloss,seed1_severe_regressions=seed_severe,seed0_WIN_to_seed1_LOSS=flips,
        conditions=dict(all42_complete=complete,same_PE_DLL=same,all12_eligible_at_freeze=all_eligible,all12_primary_evaluable=main_evaluable,
            minimum_six_main_WIN=wins>=6,maximum_two_main_LOSS=losses<=2,no_severe_main_P=not severe,
            all_size_geometry_strata_gain=all(n>=1 for n in strata.values()),all3_seed_evaluable=seed_evaluable,no_severe_seed_P=not seed_severe,
            minimum_two_seed_nonLOSS=nonloss>=2,no_WIN_to_LOSS_flip=not flips,no_unresolved_fault=not faults),
        no_hidden_ENS_veto=True,default_ENS_changed=False,independent_engine_performance_rerun=False)

def remaining_budget(paid_starts,paid_seconds,remaining_groups,overhead_seconds=0):
    """Reserve every still-required formal group; no predicted early stop credit."""
    assert isinstance(paid_starts,int) and paid_starts>=0 and finite(paid_seconds) and paid_seconds>=0
    required_starts=sum(1+len(methods) for cap,methods in remaining_groups)
    nominal=sum(cap*len(methods) for cap,methods in remaining_groups)
    assert finite(overhead_seconds) and overhead_seconds>=0
    seconds=nominal+overhead_seconds
    return dict(paid_starts=paid_starts,paid_outer_seconds=paid_seconds,remaining_formal_starts=required_starts,remaining_nominal_seconds=nominal,
        necessary_external_overhead_seconds=overhead_seconds,all_remaining_reserved_seconds=seconds,max_starts=72,max_outer_seconds=100000,
        starts_fit=paid_starts+required_starts<=72,seconds_fit=paid_seconds+seconds<=100000,
        passed=paid_starts+required_starts<=72 and paid_seconds+seconds<=100000,unknown_early_stop_savings_credited=False,native_wrapper_time_double_counted=False)
