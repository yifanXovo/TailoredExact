"""Idle-only complete B/D aggregation; every entered call and witness retained."""
import types
import round147_analyze as inherited
from round150_common import *
rows, table = inherited.rows, inherited.table


def collect():
    configure()
    current = os.environ.get('ROUND140_METERED_PARENT_LABEL')
    assert all(v['label']==current for v in budget()['unclosed'])
    matrix = read(OUT/'confirmation_matrix.json')
    matrix = dict(matrix,batch='confirmation')
    records, counts, pending, trajectories = [], [], [], []
    for group in matrix['groups']:
        launch = group['launch']
        d = Path(launch['destination'])
        ledger = rows(d/'external/paper_optimize_ledger.csv')
        counts.append(dict(position=group['position'],role=launch['id'],method=launch['R150_method'],
            Optimize=len(ledger),returned=sum(v['optimize_return_code']=='0' for v in ledger),
            LP=sum(v['solve_kind']=='LP' for v in ledger)))
        if not (d/'verification_closeout.json').exists():
            pending.append(dict(position=group['position'],destination=str(d),entered=d.exists()))
            continue
        r = types.FunctionType(inherited.new_row.__code__,dict(vars(inherited),OUT=OUT,ROOT=ROOT))(matrix,group)
        r.update(round=150,evidence_kind='new_round150',method=launch['R150_method'],
            new_round150_charge_seconds=r.pop('new_round147_charge_seconds'),
            known=True,exposed=True,used_in_GD_selection=False,PF=False,Shared_S=False,AP=False)
        r['Native_total_simplex_iterations'] = sum(float(v['simplex_iterations']) for v in ledger)
        r['target_path'] = [dict(kind=v['solve_kind'],model_SHA=v['model_sha256'],runtime=float(v['solver_runtime']),
            Work=float(v['work']),native_log=Path(v['native_log']).name) for v in ledger if 'TARGET' in v['solve_kind']]
        assert read(d/'round149_control_audit.json')['enabled'] is False
        assert read(d/'round147_control_audit.json')['GD']==(r['method']=='D')
        best = math.inf
        observations = read(d/'observations.json')
        for item in observations:
            e = item['payload']
            if e['kind']!='witness' or e['objective']>=best-1e-15:
                continue
            best = e['objective']
            elapsed = item['effective_available_seconds']
            assert 0<=elapsed<=r['T_produce']+.1
            trajectories.append(dict(role=r['role'],method=r['method'],seed=r['seed'],producer_seconds=elapsed,
                U=best,sequence=item['sequence'],committed_event_SHA=item['sha256'],source=e['source'],
                PE_SHA=r['PE_SHA'],raw_observation_SHA=sha(d/'observations.json'),
                clock='effective committed witness availability'))
        assert abs(best-r['U'])<=1e-8
        r['first_final_U_seconds'] = min(v['producer_seconds'] for v in trajectories
            if v['role']==r['role'] and v['method']==r['method'] and abs(v['U']-r['U'])<=1e-10)
        records.append(r)
    comparisons = []
    for role in ['N-C20-U','N-B35-S']:
        pair = {r['method']:r for r in records if r['role']==role}
        if len(pair)<2:
            continue
        b,d = pair['B'],pair['D']
        for key in ['input_SHA','physical_T','lambda_value','cap','source_commit','PE_SHA','DLL_SHA','H_semantic_SHA','H_fleet_SHA']:
            assert b[key]==d[key],(role,key)
        c = dict(role=role,seed=0,same_PE=True,own_H_equal=True,timing_relation='same_round_serial',
            identical_host_load_not_claimed=True,known=True,exposed=True,used_in_GD_selection=False)
        fields = ['U','L','signed_gap','relative_gap','certificate','T_produce','T_cert','T_verify','T_total','first_final_U_seconds']
        for prefix,r in [('B',b),('D',d)]:
            c.update({prefix+'_'+k:r[k] for k in fields})
        c.update(delta_U=d['U']-b['U'],delta_L=d['L']-b['L'],
            delta_signed_gap=d['signed_gap']-b['signed_gap'],delta_relative_gap=d['relative_gap']-b['relative_gap'],
            U_improvement_percent=100*(b['U']-d['U'])/b['U'],
            L_improvement_percent=100*(d['L']-b['L'])/abs(b['L']),
            certificate_speedup_percent=100*(b['T_cert']-d['T_cert'])/b['T_cert'] if b['certificate'] and d['certificate'] else None,
            total_cost_difference=d['T_total']-b['T_total'],no_open_cap_as_convergence_time=True)
        c['serious_double_open_regression'] = bool(not b['certificate'] and not d['certificate'] and
            c['delta_U']>max(.001,.05*b['U']) and c['delta_signed_gap']>max(.005,.25*b['signed_gap']))
        comparisons.append(c)
    lp = [read(OUT/'LP'/f'{role}_CPF/result.json') for role in ROLES]
    write(OUT/'reports/full.json',dict(UTC=utc(),formal_arms=records,comparisons=comparisons,pending=pending,
        all_entered_native_counts=counts,complete_Native_Optimize=sum(v['Optimize'] for v in counts),
        complete_Native_returned=sum(v['returned'] for v in counts),diagnostic_LP_Optimize=len(lp),
        diagnostic_LP_returned=sum((OUT/'LP'/f'{role}_CPF/return.json').exists() for role in ROLES),
        repeated_baseline_Optimize=0,extra_quality_Optimize=0,optional_clarification_entered=False,
        same_PE_controls=True,all_own_H=True,CPF_full_entered=False))
    write(OUT/'reports/LP.json',dict(domains=lp,baseline_Optimize_new=0,all_variables_free=True))
    history = read(ROOT/'results/unified_exact_round147/candidate_decision.json')['B_to_D']
    old_manifest = read(ROOT/'results/unified_exact_round147/candidate_manifest.json')
    write(OUT/'reports/R147_selection.json',dict(fixed_science='a0673b683c645d35de829fa101a55cc9fc4774c7',
        source_commit=old_manifest['source_commit'],PE_SHA=old_manifest['production_PE_SHA'],
        comparisons=history,known_roles=4,Seed=0,reoptimized=False,new_charge_seconds=0,
        current_round_matched_control=False,old_source_PE_identity_retained=True))
    table(OUT/'reports/full.csv',records)
    table(OUT/'reports/comparisons.csv',comparisons)
    table(OUT/'reports/native_counts.csv',counts)
    table(OUT/'reports/verified_U_trajectories.csv',trajectories)
    print(json.dumps(dict(formal=len(records),pending=pending,comparisons=comparisons)))


def cost():
    configure()
    assert not budget()['unclosed']
    b = budget()
    full = read(OUT/'reports/full.json')
    write(OUT/'cost_report.json',dict(UTC=utc(),charged_new_experiment_seconds=b['G1_seconds'],
        ceiling_seconds=14400,remaining_seconds=b['remaining_G1_seconds'],experiment=b,
        build_seconds=0,no_new_build=True,standalone_LP_Optimize=3,extra_quality_Optimize=0,
        baseline_Optimize_new=0,complete_Native_Optimize=full['complete_Native_Optimize'],
        complete_Native_returned=full['complete_Native_returned'],
        includes_all_own_H_arithmetic_construction_solves_qualification_failures_necessary_verification=True,
        nested_Runtime_Work_not_added=True,old_fees_not_recharged=True,
        pure_offline_theory_authoring_and_public_IO_separate=True,
        manual_qualification_timing='Disclosed conservative allowances in infra/external_costs.json',
        external_costs='infra/external_costs.json',optional_clarification_nominal_capacity_spent=0))
    print(json.dumps(b))


if __name__=='__main__':
    if sys.argv[1]=='run':
        configure()
        assert metered('complete_analysis','diagnostic',[PYTHON,'-B',__file__,'collect'],120,300)==0
        cost()
    else:
        globals()[sys.argv[1]]()
