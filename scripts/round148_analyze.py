"""Idle-only aggregation of real new-PE pairs; old results are context only."""
import types
import csv
import round147_analyze as inherited
from round148_common import *
configure()
rows,table=inherited.rows,inherited.table


def idle():
    current=os.environ.get('ROUND140_METERED_PARENT_LABEL')
    assert all(r['label']==current for r in budget()['unclosed'])


def new_row(matrix,group):
    r=types.FunctionType(inherited.new_row.__code__,dict(vars(inherited),OUT=OUT,ROOT=ROOT))(matrix,group)
    launch=group['launch'];d=Path(launch['destination']);control=read(d/'round148_control_audit.json')
    r.update(round=148,evidence_kind='new_round148',method=launch['R148_method'],
        shared_S=control['enabled'],shared_S_rows=max([m['shared_S_rows'] for m in control['models']] or [0]),
        new_round148_charge_seconds=r.pop('new_round147_charge_seconds'),
        actual_root_after_strengthening_L=r['initial_root_L'])
    selection=control['selection']
    if selection:
        r.update(initial_root_L=selection['source_L'],online_separation=selection['violation'],
            online_generation_seconds=selection['generation_seconds'],online_row_kind=selection['kind'],
            online_row_nonzeros=len(selection['row']['terms']),
            online_RHS_coefficient_loss_bound=control['exact_actual_slope_RHS_loss_bound'])
    ledger=rows(d/'external/paper_optimize_ledger.csv')
    r['Native_total_simplex_iterations']=sum(float(x['simplex_iterations']) for x in ledger)
    r['target_path']=[dict(kind=x['solve_kind'],model_SHA=x['model_sha256'],
        runtime=float(x['solver_runtime']),Work=float(x['work']),native_log=Path(x['native_log']).name)
        for x in ledger if 'TARGET' in x['solve_kind']]
    return r


def full():
    configure();idle()
    formal=[];qualification=[];pending=[];counts=[]
    for path in sorted(OUT.glob('*_matrix.json')):
        m=read(path)
        for g in m['groups']:
            d=Path(g['launch']['destination']);ledger=rows(d/'external/paper_optimize_ledger.csv')
            counts.append(dict(batch=m['batch'],position=g['position'],Optimize=len(ledger),
                returned=sum(x['optimize_return_code']=='0' for x in ledger)))
            if not (d/'round148_control_audit.json').exists():
                pending.append(dict(batch=m['batch'],position=g['position'],method=g['launch']['R148_method']))
            else:
                row=new_row(m,g)
                (qualification if m['batch'].startswith('qualification') else formal).append(row)
    comparisons=[]
    for candidate in formal:
        if candidate['method']!='D_SHARED_S':continue
        control=next(r for r in formal if r['role']==candidate['role'] and r['seed']==candidate['seed'] and r['method']=='D')
        for key in ['input_SHA','physical_T','lambda_value','cap','source_commit','PE_SHA','DLL_SHA','H_semantic_SHA','H_fleet_SHA']:
            assert control[key]==candidate[key],(candidate['role'],key)
        c=dict(role=candidate['role'],seed=candidate['seed'],same_new_PE=True,own_H_equal=True,
            timing_relation='same_round_serial',identical_host_load_not_claimed=True)
        for prefix,r in [('D',control),('shared_S',candidate)]:
            c.update({prefix+'_'+k:r[k] for k in ['U','L','signed_gap','relative_gap','certificate','T_produce','T_cert','T_verify','T_total']})
        c.update(delta_U=candidate['U']-control['U'],delta_L=candidate['L']-control['L'],
            delta_signed_gap=candidate['signed_gap']-control['signed_gap'],
            delta_relative_gap=candidate['relative_gap']-control['relative_gap'],
            U_improvement_percent=100*(control['U']-candidate['U'])/control['U'],
            L_improvement_percent=100*(candidate['L']-control['L'])/abs(control['L']),
            no_open_cap_as_convergence=True)
        comparisons.append(c)
    lp=[read(p) for p in sorted((OUT/'LP').glob('*/iteration*/result.json'))]
    cost=budget()
    write(OUT/'reports/full.json',dict(UTC=utc(),formal_arms=formal,qualification_arms=qualification,
        comparisons=comparisons,pending=pending,all_entered_native_counts=counts,
        complete_Native_Optimize=sum(x['Optimize'] for x in counts),
        complete_Native_returned=sum(x['returned'] for x in counts),
        standalone_LP_Optimize=len(lp),baseline_Optimize=0,source_solves=0,
        all_entered_preserved=True,budget=cost))
    write(OUT/'reports/LP.json',dict(PASS=all(r['qualified'] for r in lp),results=lp,
        models=5,physical_instances=3,one_row_each=True,extra_LP_iterations=0))
    for name,value in [('complete_arms',formal),('qualification_arms',qualification),('comparisons',comparisons),('LP',lp)]:
        table(OUT/'reports'/f'{name}.csv',value)
    write(OUT/'cost_report.json',dict(UTC=utc(),charged_new_experiment_seconds=cost['G1_seconds'],
        ceiling_seconds=18000,experiment=cost,build_seconds_separate=cost['separately_reported_seconds'],
        standalone_LP_Optimize=len(lp),complete_Native_Optimize=sum(x['Optimize'] for x in counts),
        complete_Native_returned=sum(x['returned'] for x in counts),
        includes_all_own_H_construction_solves_qualification_failures_necessary_verification=True,
        nested_H_LP_MIP_Runtime_Work_not_added=True,historical_cost_not_recharged=True,
        pure_math_authoring_and_public_IO_separate=True,
        unmetered_independent_review_observations='infra/external_costs.json',
        conservative_unmeasured_review_overhead_reserve_seconds=5.))
    print(json.dumps(dict(formal=len(formal),qualification=len(qualification),pending=pending,comparisons=comparisons,budget=cost)))


def trajectories():
    idle();records=[]
    for r in read(OUT/'reports/full.json')['formal_arms']:
        d=Path(r['destination']);best=math.inf
        for item in read(d/'observations.json'):
            e=item['payload']
            if e['kind']!='witness' or e['objective']>=best-1e-15:continue
            best=e['objective'];elapsed=item['effective_available_seconds']
            assert 0<=elapsed<=r['T_produce']+.1
            records.append(dict(role=r['role'],method=r['method'],seed=r['seed'],producer_seconds=elapsed,
                U=best,sequence=item['sequence'],committed_event_SHA=item['sha256'],source=e['source'],
                PE_SHA=r['PE_SHA'],raw_observation_SHA=sha(d/'observations.json'),clock='effective committed witness availability'))
        assert abs(best-r['U'])<=1e-8
    table(OUT/'reports/verified_U_trajectories.csv',records)


def stage():
    full();trajectories()


if __name__=='__main__':globals()[sys.argv[1]]()
