"""Idle-only aggregation of entered complete arms; unentered positions stay explicit."""
import types
import round147_analyze as inherited
from round151_common import *
rows,table=inherited.rows,inherited.table
def collect():
    configure();current=os.environ.get('ROUND140_METERED_PARENT_LABEL')
    assert all(v['label']==current for v in budget()['unclosed'])
    matrix=dict(read(OUT/'confirmation_matrix.json'),batch='confirmation')
    records,counts,pending,unentered,trajectories=[],[],[],[],[]
    for group in matrix['groups']:
        launch=group['launch'];d=Path(launch['destination'])
        if not d.exists():
            unentered.append(dict(position=group['position'],role=launch['id'],method=launch['R151_method'],conditional=group['position']>=3));continue
        ledger=rows(d/'external/paper_optimize_ledger.csv')
        counts.append(dict(position=group['position'],role=launch['id'],method=launch['R151_method'],
            Optimize=len(ledger),returned=sum(v['optimize_return_code']=='0' for v in ledger),LP=sum(v['solve_kind']=='LP' for v in ledger)))
        if not (d/'verification_closeout.json').exists():pending.append(dict(position=group['position'],destination=str(d)));continue
        r=types.FunctionType(inherited.new_row.__code__,dict(vars(inherited),OUT=OUT,ROOT=ROOT))(matrix,group)
        r.update(round=151,evidence_kind='new_round151',method=launch['R151_method'],
            new_round151_charge_seconds=r.pop('new_round147_charge_seconds'),known=True,exposed=True,GD=False,PF149=False,Shared_S=False,AP=False)
        contract=read(d/'round151_control_audit.json');assert contract['PASS']
        r.update(cap_rows=max([m['cap_rows'] for m in contract['models']] or [0]),
            cap_nonzeros=max([m['cap_nonzeros'] for m in contract['models']] or [0]),
            root_cap_arithmetic_seconds=(contract['root'] or {}).get('arithmetic_seconds',0.))
        r['Native_total_simplex_iterations']=sum(float(v['simplex_iterations']) for v in ledger)
        r['target_path']=[dict(kind=v['solve_kind'],model_SHA=v['model_sha256'],runtime=float(v['solver_runtime']),
            Work=float(v['work']),native_log=Path(v['native_log']).name) for v in ledger if 'TARGET' in v['solve_kind']]
        best=math.inf
        for item in read(d/'observations.json'):
            e=item['payload']
            if e['kind']!='witness' or e['objective']>=best-1e-15:continue
            best=e['objective'];elapsed=item['effective_available_seconds'];assert 0<=elapsed<=r['T_produce']+.1
            trajectories.append(dict(role=r['role'],method=r['method'],seed=r['seed'],producer_seconds=elapsed,U=best,
                sequence=item['sequence'],committed_event_SHA=item['sha256'],source=e['source'],PE_SHA=r['PE_SHA'],
                raw_observation_SHA=sha(d/'observations.json'),clock='effective committed witness availability'))
        assert abs(best-r['U'])<=1e-8
        r['first_final_U_seconds']=min(v['producer_seconds'] for v in trajectories if v['role']==r['role'] and v['method']==r['method'] and abs(v['U']-r['U'])<=1e-10)
        records.append(r)
    comparisons=[]
    for role in ['N-B35-S','N-C20-U']:
        pair={r['method']:r for r in records if r['role']==role}
        if len(pair)<2:continue
        b,c=pair['B'],pair['C']
        for key in ['input_SHA','physical_T','lambda_value','cap','source_commit','PE_SHA','DLL_SHA','H_semantic_SHA','H_fleet_SHA']:
            assert b[key]==c[key],(role,key)
        item=dict(role=role,seed=0,same_PE=True,own_H_equal=True,timing_relation='same_round_serial',known=True,exposed=True)
        for prefix,r in [('B',b),('C',c)]:
            item.update({prefix+'_'+k:r[k] for k in ['U','L','signed_gap','relative_gap','certificate','T_produce','T_cert','T_verify','T_total','first_final_U_seconds']})
        item.update(delta_U=c['U']-b['U'],delta_L=c['L']-b['L'],delta_signed_gap=c['signed_gap']-b['signed_gap'],
            delta_relative_gap=c['relative_gap']-b['relative_gap'],U_improvement_percent=100*(b['U']-c['U'])/b['U'],
            L_improvement_percent=100*(c['L']-b['L'])/abs(b['L']) if b['L'] else None,
            certificate_time_change_percent=100*(c['T_cert']-b['T_cert'])/b['T_cert'] if b['certificate'] and c['certificate'] else None,
            total_cost_difference=c['T_total']-b['T_total'],no_open_cap_as_convergence_time=True)
        item['serious_double_open_regression']=bool(not b['certificate'] and not c['certificate'] and item['delta_U']>max(.001,.05*b['U']) and item['delta_signed_gap']>max(.005,.25*b['signed_gap']))
        comparisons.append(item)
    lp=[read(OUT/'LP'/f'N-B35-S_{tag}/result.json') for tag in ['C','P']]
    qualification=rows(OUT/'campaign_qualification/raw/R151_qualification_NB35_C/external/paper_optimize_ledger.csv')
    write(OUT/'reports/full.json',dict(UTC=utc(),formal_arms=records,comparisons=comparisons,pending=pending,unentered=unentered,
        all_entered_native_counts=counts,complete_Native_Optimize=sum(v['Optimize'] for v in counts),
        complete_Native_returned=sum(v['returned'] for v in counts),diagnostic_LP_Optimize=len(lp),
        diagnostic_LP_returned=sum((OUT/'LP'/f'N-B35-S_{tag}/return.json').exists() for tag in ['C','P']),
        qualification_Native_Optimize=len(qualification),qualification_Native_returned=sum(v['optimize_return_code']=='0' for v in qualification),
        repeated_baseline_Optimize=0,extra_quality_Optimize=0,same_PE_controls=True,all_own_H=True,unique_candidate='C'))
    p,c=[read(OUT/'LP'/f'N-B35-S_{tag}/result.json') for tag in ['P','C']]
    write(OUT/'reports/LP.json',dict(domains=lp,baseline_Optimize_new=0,C20_Optimize_new=0,all_variables_free=True,
        B=c['old_B_L'],P=p['L'],C=c['L'],P_minus_B=p['L']-c['old_B_L'],C_minus_P=c['L']-p['L'],C_minus_B=c['L']-c['old_B_L']))
    table(OUT/'reports/full.csv',records);table(OUT/'reports/comparisons.csv',comparisons)
    table(OUT/'reports/native_counts.csv',counts);table(OUT/'reports/verified_U_trajectories.csv',trajectories)
    print(json.dumps(dict(complete_arms=len(records),pending=pending,unentered=unentered,comparisons=comparisons)),flush=True)
def cost():
    configure();assert not budget()['unclosed'];b=budget();full=read(OUT/'reports/full.json')
    build=sum(read(p)['separately_reported_seconds'] for p in (OUT/'fees').glob('*/receipt.json') if read(p.parent/'launch.json')['kind']=='build')
    write(OUT/'cost_report.json',dict(UTC=utc(),charged_new_experiment_seconds=b['G1_seconds'],ceiling_seconds=14400,
        remaining_seconds=b['remaining_G1_seconds'],experiment=b,build_seconds=build,standalone_LP_Optimize=2,
        baseline_Optimize_new=0,C20_Optimize_new=0,complete_Native_Optimize=full['complete_Native_Optimize'],
        complete_Native_returned=full['complete_Native_returned'],qualification_Native_Optimize=full['qualification_Native_Optimize'],
        qualification_Native_returned=full['qualification_Native_returned'],
        includes_own_H_construction_all_solves_failures_and_necessary_verification=True,nested_Runtime_Work_not_added=True,
        old_fees_not_recharged=True,pure_theory_authoring_public_IO_and_build_separate=True,
        exact_clock_accounting_incomplete=True,unmetered_short_qualification_conservative_allowance='infra/external_costs.json'))
    print(json.dumps(b))
if __name__=='__main__':
    configure()
    if sys.argv[1]=='run':
        label=sys.argv[2] if len(sys.argv)>2 else 'complete_analysis'
        assert metered(label,'diagnostic',[PYTHON,'-B',__file__,'collect'],120,300)==0;cost()
    else:globals()[sys.argv[1]]()
