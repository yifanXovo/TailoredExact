"""Idle-only aggregation of entered same-new-PE PF pairs and original trajectories."""
import types
import round147_analyze as inherited
from round149_common import *
rows,table=inherited.rows,inherited.table


def new_row(matrix,group):
    r=types.FunctionType(inherited.new_row.__code__,dict(vars(inherited),OUT=OUT,ROOT=ROOT))(matrix,group)
    launch=group['launch'];d=Path(launch['destination']);control=read(d/'round149_control_audit.json')
    r.update(round=149,evidence_kind='new_round149',method=launch['R149_method'],PF=control['enabled'],
        PF_rows=max([m['PF_rows'] for m in control['models']] or [0]),
        new_round149_charge_seconds=r.pop('new_round147_charge_seconds'),extra_root_LP=0)
    meta=control['root']
    r.update(root_penalty_lower=meta['penalty_lower'] if meta else None,
        root_beta=meta['beta'] if meta else None,root_own_cutoff=meta['own_cutoff'] if meta else None)
    ledger=rows(d/'external/paper_optimize_ledger.csv')
    r['Native_total_simplex_iterations']=sum(float(v['simplex_iterations']) for v in ledger)
    r['target_path']=[dict(kind=v['solve_kind'],model_SHA=v['model_sha256'],runtime=float(v['solver_runtime']),
        Work=float(v['work']),native_log=Path(v['native_log']).name) for v in ledger if 'TARGET' in v['solve_kind']]
    return r


def full():
    configure();current=os.environ.get('ROUND140_METERED_PARENT_LABEL')
    assert all(v['label']==current for v in budget()['unclosed'])
    formal=[];qualification=[];pending=[];counts=[]
    for path in sorted(OUT.glob('*_matrix.json')):
        matrix=read(path)
        for group in matrix['groups']:
            d=Path(group['launch']['destination'])
            ledger=rows(d/'external/paper_optimize_ledger.csv')
            counts.append(dict(batch=matrix['batch'],position=group['position'],Optimize=len(ledger),
                returned=sum(v['optimize_return_code']=='0' for v in ledger)))
            if not (d/'verification_closeout.json').exists():
                pending.append(dict(batch=matrix['batch'],position=group['position'],method=group['launch']['R149_method']))
            else:
                row=new_row(matrix,group)
                (qualification if matrix['batch'].startswith('qualification') else formal).append(row)
    comparisons=[]
    for candidate in formal:
        if candidate['method']!='D_PF':continue
        control=next(v for v in formal if v['role']==candidate['role'] and v['seed']==candidate['seed'] and v['method']=='D')
        for key in ['input_SHA','physical_T','lambda_value','cap','source_commit','PE_SHA','DLL_SHA','H_semantic_SHA','H_fleet_SHA']:
            assert control[key]==candidate[key],(candidate['role'],key)
        c=dict(role=candidate['role'],seed=candidate['seed'],same_new_PE=True,own_H_equal=True,
            timing_relation='same_round_serial',identical_host_load_not_claimed=True)
        for prefix,r in [('D',control),('PF',candidate)]:
            c.update({prefix+'_'+k:r[k] for k in ['U','L','signed_gap','relative_gap','certificate','T_produce','T_cert','T_verify','T_total']})
        c.update(delta_U=candidate['U']-control['U'],delta_L=candidate['L']-control['L'],
            delta_signed_gap=candidate['signed_gap']-control['signed_gap'],
            delta_relative_gap=candidate['relative_gap']-control['relative_gap'],
            U_improvement_percent=100*(control['U']-candidate['U'])/control['U'],
            L_improvement_percent=100*(candidate['L']-control['L'])/abs(control['L']),
            no_open_cap_as_convergence=True)
        c['serious_double_open_regression']=bool(not candidate['certificate'] and not control['certificate'] and
            c['delta_U']>max(.001,.05*control['U']) and c['delta_signed_gap']>max(.005,.25*control['signed_gap']))
        comparisons.append(c)
    write(OUT/'reports/full.json',dict(formal_arms=formal,qualification_arms=qualification,pending=pending,
        comparisons=comparisons,all_entered_native_counts=counts,all_own_H=True,same_new_PE_controls=True,
        complete_Native_Optimize=sum(v['Optimize'] for v in counts),
        complete_Native_returned=sum(v['returned'] for v in counts),
        extra_root_LP=0,baseline_LP_Optimize_new=0,diagnostic_LP_Optimize=4))
    table(OUT/'reports/full.csv',formal);table(OUT/'reports/comparisons.csv',comparisons)
    print(json.dumps(dict(entered_formal=len(formal),comparisons=comparisons,pending=pending)))


def trajectories():
    records=[]
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


def stage():full();trajectories()


def run(label):
    configure();assert metered('analysis_'+label,'diagnostic',[PYTHON,'-B',__file__,'stage'],60,120)==0


if __name__=='__main__':
    if sys.argv[1]=='run':run(sys.argv[2])
    else:globals()[sys.argv[1]]()
