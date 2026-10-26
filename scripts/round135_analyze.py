"""Pure aggregation, complete registered denominators, no optimization."""
from round135_common import *
import collections, inspect
import round134_analyze as inherited
csv_write=inherited.csv_write

def gather(stage):
    # The inherited qualification reader deliberately preserves method=S2.
    # Variant is the sole AP switch and is taken from the frozen launch.
    source=inspect.getsource(inherited.gather).replace("endpoint=d/'round134_endpoint.json'","endpoint=d/'round135_endpoint.json'")
    ns=dict(vars(inherited),OUT=OUT);exec(compile(source,__file__+'::gather','exec'),ns)
    rows,missing,ops=ns['gather'](stage)
    matrix=read(OUT/f'{stage}_matrix_frozen.json')
    for row in rows:
        launch=matrix['groups'][row['position']-1]['launch']
        row['method']=launch['variant']
        d=Path(launch['destination']);audit=read(d/'audit.json')
        contracts=[r['model']['AP_contract'] for r in audit['model_contracts']]
        assert contracts and all(r['enabled']==(row['method']=='AP') for r in contracts)
        row['AP_models_audited']=sum(x['AP_rows'] for x in contracts)
        row['state_coefficients_audited']=sum(x['state_coefficients_checked'] for x in contracts)
        ledger=d/'external/paper_optimize_ledger.csv'
        calls=inherited.core.rows(ledger) if ledger.exists() else []
        row['native_solver_seconds']=sum(float(x['solver_runtime']) for x in calls)
        row['root_lp_seconds']=sum(float(x['solver_runtime']) for x in calls if x['solve_kind']=='LP' and x['leaf_id']=='L0')
        row['child_lp_seconds']=sum(float(x['solver_runtime']) for x in calls if x['solve_kind']=='LP' and x['leaf_id']!='L0')
        row['native_MIP_seconds']=sum(float(x['solver_runtime']) for x in calls if x['solve_kind']!='LP')
    for op in ops:op['method']=matrix['groups'][op['position']-1]['launch']['variant']
    write(OUT/f'reports/{stage}/arms.json',rows);csv_write(OUT/f'reports/{stage}/arms.csv',rows)
    write(OUT/f'reports/{stage}/operations.json',ops)
    write(OUT/f'reports/{stage}/completion.json',dict(expected=len(matrix['groups']),completed=len(rows),missing=missing,
        certification_counts=dict(collections.Counter(r['method'] for r in rows if r['certificate'])),
        full_production_caps_not_imputed=True,variant_from_frozen_launch=True))
    return rows,missing,ops

def main():
    C,cm,_=gather('C');D,dm,_=gather('D');groups=collections.defaultdict(dict)
    for r in C+D:groups[r['role'],r['seed'],r['repeat']][r['method']]=r
    pairs=[]
    for key,methods in groups.items():
        if set(methods)!={'AP','S2'}:continue
        a,b=methods['AP'],methods['S2'];p=inherited.pair(a,b)
        eps=1e-7
        p.update(AP_U_minus_S2=a['U']-b['U'],AP_L_minus_S2=a['L']-b['L'],
            AP_gap_minus_S2=a['signed_gap']-b['signed_gap'],
            AP_full_time=a['T_produce'],S2_full_time=b['T_produce'],
            AP_T_verify=a['T_verify'],S2_T_verify=b['T_verify'],
            AP_certificate=a['certificate'],S2_certificate=b['certificate'])
        p['AP_endpoint_pareto_better']=(a['U']<=b['U']+eps and a['L']>=b['L']-eps and
            (a['U']<b['U']-eps or a['L']>b['L']+eps))
        p['S2_endpoint_pareto_better']=(b['U']<=a['U']+eps and b['L']>=a['L']-eps and
            (b['U']<a['U']-eps or b['L']>a['L']+eps))
        pairs.append(p)
    write(OUT/'reports/pairs.json',pairs);csv_write(OUT/'reports/pairs.csv',pairs)
    write(OUT/'reports/arms.json',C+D);csv_write(OUT/'reports/arms.csv',C+D)
    roots=[read(OUT/'roots'/role/'LP/result.json') for role in ('K-20-S','K-35-U')]
    write(OUT/'reports/roots.json',roots)
    done=[f"{r['stage']}{r['position']:02}" for r in C+D]
    summary=dict(UTC=utc(),stage1=dict(planned=10,completed=len(C),missing=cm),
        stage2=dict(planned=22,completed=len(D),not_entered=dm),
        completed_positions=done,registered_total=32,completed=len(C+D),complete_pairs=len(pairs),
        certificate_counts=dict(collections.Counter(r['method'] for r in C+D if r['certificate'])),
        directions=dict(collections.Counter(r['direction'] for r in pairs)),
        direction_counts_include_micro_and_nonmaterial_differences=True,
        material_certified_time=dict(AP_favorable=sum(r['material'] is True and r['direction']=='Win' for r in pairs),
            AP_adverse=sum(r['material'] is True and r['direction']=='Lose' for r in pairs)),
        pair_classes=dict(collections.Counter(r['class'] for r in pairs)),budget=budget(),
        root_IND_gain_retained=all(r['preserves_IND_gain'] for r in roots),
        only_one_candidate=True,all_entered_adverse_and_open_retained=True,not_random_holdout=True)
    write(OUT/'reports/summary.json',summary)
    print(json.dumps(dict(stage1=summary['stage1'],stage2=summary['stage2'],pairs=len(pairs),budget=summary['budget']['G1_seconds'])))
if __name__=='__main__':main()
