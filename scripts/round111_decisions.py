"""Layered finite confirmation rules using the unchanged interval comparator."""
from round109_decisions import relative,finite,qualified_numbers,CLOSURE_TOL,ZERO_TOL
from round109_interval_pairs import pair as inherited_pair
from collections import Counter

LAYER='R110_MAIN_36_PLUS_R111_SEED_6'

def pair(a,c):
    if any(v.get('formal_protocol_qualified') is False for v in (a,c)):
        return dict(candidate=a['arm'],control=c['arm'],classification='UNEVALUABLE',evaluable=False,
            severe_regression=None,basis='CURRENT_COMPLETE_CLOCK_OR_CORRECTNESS_UNQUALIFIED')
    value=inherited_pair(a,c)
    if not value['evaluable']:value['comparison_failure']='INSUFFICIENT_COMPARISON'
    return value

def selection(main,seed,roles,inherited_qualified=True,unresolved=()):
    old={(a['id'],a['arm']):a for a in main};new={(a['id'],a['arm']):a for a in seed}
    primary={r['id']:pair(old[r['id'],'M-B'],old[r['id'],'P-GRB']) for r in roles}
    ens={r['id']:pair(old[r['id'],'M-B'],old[r['id'],'ENS-C']) for r in roles}
    expected={ (r,m) for r in ('G20-C2','G50-R1','G100-R2') for m in ('M-B','P-GRB') }
    seeds={r:pair(new[r,'M-B'],new[r,'P-GRB']) for r in ('G20-C2','G50-R1','G100-R2') if all((r,m) in new for m in ('M-B','P-GRB'))}
    complete=len(seed)==len(new)==6 and set(new)==expected
    mc=Counter(v['classification'] for v in primary.values());sc=Counter(v['classification'] for v in seeds.values())
    strata=dict(V={str(n):[r['id'] for r in roles if r['V']==n and primary[r['id']]['classification']=='WIN'] for n in (20,50,100)},
        geometry={g:[r['id'] for r in roles if r['geometry']==g and primary[r['id']]['classification']=='WIN'] for g in ('compact','regional')})
    flips=[r for r,v in seeds.items() if primary[r]['classification']=='WIN' and v['classification']=='LOSS']
    faults=list(unresolved)
    if not inherited_qualified:faults.append('R110_MAIN36_IDENTITY_OR_QUALIFICATION_NOT_IMPORTABLE')
    if not complete:faults.append('FIXED_SIX_CURRENT_OBSERVATIONS_INCOMPLETE')
    if any(v.get('formal_protocol_qualified') is not True or v.get('certificate_qualified') is not True for v in seed):
        faults.append('CURRENT_COMPLETE_CLOCK_OR_CORRECTNESS_UNQUALIFIED')
    if any(v['PE_SHA']!=main[0]['PE_SHA'] or v['DLL_SHA']!=main[0]['DLL_SHA'] for v in seed):faults.append('PRODUCTION_IDENTITY_FAILURE')
    reasons=[]
    if mc['WIN']<6:reasons.append('INSUFFICIENT_MAIN_P_WINS')
    if mc['LOSS']>2:reasons.append('TOO_MANY_MAIN_P_LOSSES')
    if any(v['severe_regression'] is True for v in primary.values()):reasons.append('SEVERE_MAIN_P_REGRESSION')
    if any(not wins for group in strata.values() for wins in group.values()):reasons.append('MISSING_MAIN_SIZE_OR_GEOMETRY_WIN')
    evaluable=len(seeds)==3 and all(v['evaluable'] for v in seeds.values())
    if complete and not evaluable and not faults:reasons.append('INSUFFICIENT_COMPARISON')
    if any(v['severe_regression'] is True for v in seeds.values()):reasons.append('SEVERE_SEED_P_REGRESSION')
    nonloss=sum(v['evaluable'] and v['classification']!='LOSS' for v in seeds.values())
    if complete and evaluable and nonloss<2:reasons.append('INSUFFICIENT_SEED_NONLOSS')
    if flips:reasons.append('SEED0_WIN_TO_CURRENT_SEED1_LOSS')
    return dict(stage='BLOCKED' if faults else 'CONFIRMATION_NOT_SUPPORTED' if reasons else 'CONFIRMATION_SUPPORT',
        evidence_layer=LAYER,reason_codes=[] if faults else reasons,blocking_reasons=faults,unassessed_performance_conditions=reasons if faults else [],
        main_denominator=12,completed_current_formal_arms=len(seed),current_qualified_formal_arms=sum(v.get('formal_protocol_qualified') is True for v in seed),
        current_six_complete=complete,current_three_seed_pairs_evaluable=evaluable,main_primary_pairs=primary,main_MB_ENS_pairs=ens,
        seed_primary_pairs=seeds,main_counts=dict(mc),seed_counts=dict(sc),main_severe_P_regressions=sum(v['severe_regression'] is True for v in primary.values()),
        seed_severe_P_regressions=sum(v['severe_regression'] is True for v in seeds.values()),evaluable_seed_nonLOSS=nonloss,
        Seed0_WIN_to_Seed1_LOSS=flips,Seed0_WIN_to_current_Seed1_LOSS=flips,stratum_WIN_roles=strata,inherited_main36_qualified=inherited_qualified,
        old_round110_stage='BLOCKED',old_all42_valid_formal=False,all42_measured_under_new_wrapper=False,cross_wrapper_exact_speedup=False,
        new_independent_samples_added=0,default_ENS_changed=False,no_hidden_ENS_veto=True,statistical_guarantee=False,full_paper_benchmark_completed=False)
