"""Frozen Round109 stage rules; pair mathematics is the audited R108 contract."""
from round108_decisions import relative,finite,qualified_numbers,CLOSURE_TOL,ZERO_TOL
from round109_interval_pairs import pair
from collections import Counter

def selection(arms,roles,eligibility,unresolved=()):
    keys=[(a['id'],a['seed'],a['arm']) for a in arms];data=dict(zip(keys,arms))
    expected={(r['id'],0,m) for r in roles for m in ['P-GRB','ENS-C','M-B']}
    seed_ids=['G20-C2','G50-R1','G100-R2']
    expected|={(id,1,m) for id in seed_ids for m in ['P-GRB','M-B']}
    block=list(unresolved)
    if len(arms)!=42 or len(keys)!=len(set(keys)) or set(keys)!=expected:block.append('INCOMPLETE_OR_DUPLICATE_42_ARMS')
    if len({a['PE_SHA'] for a in arms})!=1 or len({a['DLL_SHA'] for a in arms})!=1:block.append('IDENTITY_PAIRING_FAILURE')
    if not all(eligibility.get(r['id'],False) for r in roles):block.append('INPUT_ELIGIBILITY_FAILURE')
    main={r['id']:pair(data[r['id'],0,'M-B'],data[r['id'],0,'P-GRB']) for r in roles
        if (r['id'],0,'M-B') in data and (r['id'],0,'P-GRB') in data}
    seeds={id:pair(data[id,1,'M-B'],data[id,1,'P-GRB']) for id in seed_ids if (id,1,'M-B') in data and (id,1,'P-GRB') in data}
    counts=Counter(x['classification'] for x in main.values());seed_counts=Counter(x['classification'] for x in seeds.values())
    strata=dict(V={str(v):[r['id'] for r in roles if r['V']==v and main.get(r['id'],{}).get('classification')=='WIN'] for v in [20,50,100]},
        geometry={g:[r['id'] for r in roles if r['geometry']==g and main.get(r['id'],{}).get('classification')=='WIN'] for g in ['compact','regional']})
    flips=[id for id in seed_ids if main.get(id,{}).get('classification')=='WIN' and seeds.get(id,{}).get('classification')=='LOSS']
    reasons=[]
    if any(x['severe_regression'] for x in main.values()):reasons.append('SEVERE_P_REGRESSION')
    if counts['LOSS']>2:reasons.append('TOO_MANY_P_LOSSES')
    if counts['WIN']<6:reasons.append('INSUFFICIENT_P_WINS')
    if any(not wins for group in strata.values() for wins in group.values()):reasons.append('MISSING_STRATUM_GAIN')
    if flips or any(x['severe_regression'] for x in seeds.values()) or sum(x['classification']!='LOSS' for x in seeds.values())<2:
        reasons.append('SEED_SENSITIVITY')
    if len(main)!=12 or len(seeds)!=3 or any(not x['evaluable'] for x in list(main.values())+list(seeds.values())):reasons.append('UNEVALUABLE_COMPARISON')
    stage='BLOCKED' if block else 'BROAD_PANEL_NOT_SUPPORTED' if reasons else 'BROAD_PANEL_SUPPORT'
    return dict(stage=stage,reason_codes=reasons,blocking_reasons=block,completed_formal_arms=len(arms),main_denominator=12,seed_groups=3,
        main_primary_pairs=main,seed_primary_pairs=seeds,main_counts=dict(counts),seed_counts=dict(seed_counts),
        main_severe_P_regressions=sum(x['severe_regression'] is True for x in main.values()),
        seed_severe_P_regressions=sum(x['severe_regression'] is True for x in seeds.values()),stratum_WIN_roles=strata,
        Seed0_WIN_to_Seed1_LOSS=flips,exact_twelve_unmeasured_eligibility=eligibility,
        all42_completed_same_identity=not any(x in block for x in ['INCOMPLETE_OR_DUPLICATE_42_ARMS','IDENTITY_PAIRING_FAILURE']),
        default_ENS_changed=False,no_new_variant_started=True,no_best_of_two=True,statistical_significance_claim=False,
        broad_performance_stability_proved=False,full_paper_benchmark_completed=False)
