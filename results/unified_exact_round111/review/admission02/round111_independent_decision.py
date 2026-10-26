"""Independent layered stage arithmetic; no production decision import."""
from collections import Counter
import math

LAYER = 'R110_MAIN_36_PLUS_R111_SEED_6'
EXPECTED = [('G20-C2','P-GRB',900),('G20-C2','M-B',900),
            ('G50-R1','M-B',1800),('G50-R1','P-GRB',1800),
            ('G100-R2','P-GRB',3600),('G100-R2','M-B',3600)]


def pair(pair_function,a,c):
    if any(v.get('formal_protocol_qualified') is not True for v in (a,c)):
        return dict(id=a['id'],seed=1,candidate=a['arm'],control=c['arm'],classification='UNEVALUABLE',evaluable=False,
                    severe_regression=None,basis='CURRENT_COMPLETE_OBSERVATION_UNQUALIFIED')
    if any(v.get('certificate_qualified') is not True for v in (a,c)):
        return dict(id=a['id'],seed=1,candidate=a['arm'],control=c['arm'],classification='UNEVALUABLE',evaluable=False,
                    severe_regression=None,basis='CURRENT_CORRECTNESS_OR_SCOPE_UNQUALIFIED')
    result = pair_function(a,c)
    if not result['evaluable']:
        result['comparison_failure'] = 'INSUFFICIENT_COMPARISON'
    return result


def selection(pair_function,main,seed,roles,inherited_qualified,unresolved=()):
    data = {(v['id'],v['seed'],v['arm']):v for v in main}
    assert len(main) == len(data) == 36 and all(v['seed'] == 0 for v in main)
    primary,ens = {},{}
    for rid in roles:
        primary[rid] = pair_function(data[rid,0,'M-B'],data[rid,0,'P-GRB'])
        ens[rid] = pair_function(data[rid,0,'M-B'],data[rid,0,'ENS-C'])
    current = {(v['id'],v['arm']):v for v in seed}
    expected_keys = {(rid,arm) for rid,arm,_ in EXPECTED}
    complete = len(seed) == len(current) == 6 and set(current) == expected_keys
    same_identity = bool(seed) and all(v.get('PE_SHA') == main[0]['PE_SHA'] and v.get('DLL_SHA') == main[0]['DLL_SHA'] for v in seed)
    seed_pairs = {}
    for rid in ('G20-C2','G50-R1','G100-R2'):
        if all((rid,m) in current for m in ('M-B','P-GRB')):
            seed_pairs[rid] = pair(pair_function,current[rid,'M-B'],current[rid,'P-GRB'])
    main_counts = Counter(v['classification'] for v in primary.values())
    seed_counts = Counter(v['classification'] for v in seed_pairs.values())
    strata = {}
    for size in (20,50,100):
        strata[str(size)] = [rid for rid,r in roles.items() if r['V'] == size and primary[rid]['classification'] == 'WIN']
    for geometry in ('compact','regional'):
        strata[geometry] = [rid for rid,r in roles.items() if r['geometry'] == geometry and primary[rid]['classification'] == 'WIN']
    main_severe = sum(v['severe_regression'] is True for v in primary.values())
    seed_severe = sum(v['severe_regression'] is True for v in seed_pairs.values())
    nonloss = sum(v['evaluable'] and v['classification'] != 'LOSS' for v in seed_pairs.values())
    flips = [rid for rid,v in seed_pairs.items() if primary[rid]['classification'] == 'WIN' and v['classification'] == 'LOSS']
    faults = list(unresolved)
    if not inherited_qualified:
        faults.append('R110_MAIN36_IDENTITY_OR_QUALIFICATION_NOT_IMPORTABLE')
    if not complete:
        faults.append('FIXED_SIX_CURRENT_OBSERVATIONS_INCOMPLETE')
    if seed and not same_identity:
        faults.append('CURRENT_PRODUCTION_IDENTITY_DIFFERS_FROM_INHERITED_MAIN')
    unqualified = [dict(number=v.get('number'),id=v['id'],arm=v['arm'],complete_seconds=v.get('complete_seconds'),
                        cap_seconds=v.get('cap_seconds'),reason=v.get('formal_protocol_failure','CURRENT_OBSERVATION_UNQUALIFIED'))
                   for v in seed if v.get('formal_protocol_qualified') is not True or v.get('certificate_qualified') is not True]
    if unqualified:
        faults.append('CURRENT_COMPLETE_CLOCK_OR_CORRECTNESS_UNQUALIFIED')
    reasons = []
    if main_counts['WIN'] < 6:
        reasons.append('INSUFFICIENT_MAIN_P_WINS')
    if main_counts['LOSS'] > 2:
        reasons.append('TOO_MANY_MAIN_P_LOSSES')
    if main_severe:
        reasons.append('SEVERE_MAIN_P_REGRESSION')
    if any(not v for v in strata.values()):
        reasons.append('MISSING_MAIN_SIZE_OR_GEOMETRY_WIN')
    evaluable = len(seed_pairs) == 3 and all(v['evaluable'] for v in seed_pairs.values())
    if complete and not evaluable and not unqualified:
        reasons.append('INSUFFICIENT_COMPARISON')
    if seed_severe:
        reasons.append('SEVERE_SEED_P_REGRESSION')
    if complete and evaluable and nonloss < 2:
        reasons.append('INSUFFICIENT_SEED_NONLOSS')
    if flips:
        reasons.append('SEED0_WIN_TO_CURRENT_SEED1_LOSS')
    stage = 'BLOCKED' if faults else 'CONFIRMATION_NOT_SUPPORTED' if reasons else 'CONFIRMATION_SUPPORT'
    return dict(stage=stage,evidence_layer=LAYER,reason_codes=reasons if not faults else [],blocking_reasons=list(dict.fromkeys(faults)),
                unassessed_performance_conditions=reasons if faults else [],main_denominator=12,completed_current_formal_arms=len(seed),
                current_qualified_formal_arms=sum(v.get('formal_protocol_qualified') is True and v.get('certificate_qualified') is True for v in seed),
                current_six_complete=complete,current_three_seed_pairs_evaluable=evaluable,evaluable_current_seed_pairs=sum(v['evaluable'] for v in seed_pairs.values()),
                main_primary_pairs=primary,main_MB_ENS_pairs=ens,seed_primary_pairs=seed_pairs,main_counts=dict(main_counts),seed_counts=dict(seed_counts),
                main_severe_P_regressions=main_severe,seed_severe_P_regressions=seed_severe,evaluable_seed_nonLOSS=nonloss,
                Seed0_WIN_to_current_Seed1_LOSS=flips,stratum_WIN_roles=strata,unqualified_current_observations=unqualified,
                inherited_main36_qualified=inherited_qualified,old_round110_stage='BLOCKED',old_all42_valid_formal=False,
                all42_measured_under_new_wrapper=False,cross_wrapper_exact_speedup=False,new_independent_samples_added=0,
                default_ENS_changed=False,no_hidden_ENS_veto=True,statistical_guarantee=False,full_paper_benchmark_completed=False)
