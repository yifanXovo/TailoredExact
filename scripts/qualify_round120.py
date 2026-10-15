"""Predeclared serial qualification: 11 children, no hidden search grid."""
from round120_common import *
from round120_prepare import resolve,EXPORTER,DIAGNOSTIC
from round120_campaign import supervised,finish_producer,execute
from round120_evidence import ArmModels,extension,event_chain
import round114_audit as audit
import round118_call_logs as logs
import round108_reader as core
from round114_claims import reconcile
from round120_math_audit import coefficients,run as mathematical_audit
import traceback

def child_creation(child):
    import ctypes
    api=ctypes.WinDLL('kernel32',use_last_error=True)
    class FileTime(ctypes.Structure):_fields_=[('low',ctypes.c_ulong),('high',ctypes.c_ulong)]
    values=[FileTime() for _ in range(4)]
    assert api.GetProcessTimes(ctypes.c_void_p(int(child._handle)),*[ctypes.byref(v) for v in values])
    return ((values[0].high<<32)+values[0].low)/1e7-11644473600
def run_child(fee,n,kind,command,cap):
    from round100_idle import ensure_idle
    ensure_idle();assert all(Path(v).exists() for v in command[:1])
    prefix=fee/f'{n:02d}_{kind}';tick=time.perf_counter()
    write(str(prefix)+'_before.json',dict(command=command,outer_cap=cap,child_binary_SHA=sha(command[0]),reserved_before_native_start=True))
    with Path(str(prefix)+'_stdout.txt').open('x',encoding='utf-8') as f:
        child=subprocess.Popen(command,cwd=ROOT,env=environment(),stdout=f,stderr=subprocess.STDOUT)
        write(str(prefix)+'_PID.json',dict(pid=child.pid,parent_pid=os.getpid(),actual_creation_unix=child_creation(child),command=command))
        try:rc=child.wait(timeout=cap)
        except subprocess.TimeoutExpired:
            child.kill();child.wait();write(str(prefix)+'_return.json',dict(exit_code=child.returncode,forced_timeout=True,outer_seconds=time.perf_counter()-tick));raise
    write(str(prefix)+'_return.json',dict(exit_code=rc,outer_seconds=time.perf_counter()-tick,actual_exit_observed=True,returned_unix=time.time()))
    assert rc==0,(kind,rc,str(prefix)+'_stdout.txt')

def micro(l,i):
    d=Path(l['destination']);r=read(d/'result.json');j=audit.journal(ROOT,l,d,read(d/'observations.json'))
    assert r['algorithm_preset']=='qualification-round120-empty-seed-mb-d1'
    assert '--round120-qualification-empty-seed' in l['command'] and '--round119-proof-contraction' not in l['command']
    context=ArmModels()
    try:
        for cid,c in j['calls'].items():
            fact,m=context.model_contract(ROOT,l['panel'],core.portable(ROOT,c['model_path']),'MB-D1');context.model_scope_contract(c,m,l['panel'])
        with extension():view=logs.build(ROOT,l,d,j,r)
    finally:context.clear()
    with extension(),logs.activate(view):
        chain=audit.return_chain(ROOT,l,d,j,r,read(d/'completion.json'))
        claims=audit.claims_for(l,j,chain,r);ind=audit.independent(ROOT,l,d,j,r,read(d/'completion.json'),chain)
        adjudication=reconcile(claims,ind['witnesses']);assert not adjudication['rejections'],'PROOF_RELIABILITY_PRIORITY'
        tables=core.evidence.controller_tables(d,r);j['returned_native_proofs']=core.returned_native_proofs(ROOT,j,tables)
        cover=core.complete_cover(d,ind['own_U'],j,tables,(l['panel']['V']-1)/l['panel']['V'])
        mechanism=event_chain(ROOT,l,d,j)
        core.start_reader.ROOT=ROOT
        submitted=[(p,read(p)) for p in sorted((d/'external/native_logs').glob('*.round68.start.json')) if read(p).get('submitted')]
        for digest in {q['model_sha256'] for p,q in submitted}:
            path=next(core.portable(ROOT,c['model_path']) for c in j['calls'].values() if c['model_sha256']==digest)
            records=core.start_reader.audit_model(path,[(p,q) for p,q in submitted if q['model_sha256']==digest],'m-binary')
            assert max(q['maximum_absolute_residual'] for q in records)<=1e-7
    assert mechanism['installed']==1 and mechanism['actual_extended_Optimize']>=1
    assert abs(ind['own_U']-1.2)<=1e-7 and r['external_gini_tree_all_relevant_leaves_closed']
    assert j['returned']==j['started'] and mechanism['extra_proof_triggered_interrupts']==0
    write(d/'micro_qualification.json',dict(passed=True,actual_Optimize=j['started'],all_actual_returns=True,
        mechanism=mechanism,cover=cover,own_U=ind['own_U'],original_problem_certificate=True,nonzero_original_optimum=1.2,
        independent_physical_argument='V8 targets/weights1 and total stock2 imply integer Y totals0/1/2. Original F values are1.2,1.925,1.65,2.075; pickup2 with legal loaded return attains1.2.',
        artificial_information='explicit same-run legal empty fleet only, no injected proof/bound/historical route',
        formal_H_performance=False,new_valid_proof_triggered_interrupt=False))
    return mechanism

def diagnostics_TSV(exports):
    rows=[]
    for e in exports:
        d=Path(e['destination']);folder=d/'external';pair=read(folder/'round120_root_pair.json')
        events=[json.loads(s) for s in (folder/'round120_events.jsonl').read_text().splitlines()]
        installation=next(x for x in events if x['kind']=='root_formulation_installed')
        D1=core.portable(ROOT,installation['path']);D0=folder/'round120_D0.lp'
        coefficients(D0);coefficients(D1)
        assert len([x for x in events if x['kind']=='paid_root_LP_returned'])==2
        assert not [x for x in events if x['kind']=='extended_native_returned']
        lines=core.rows(folder/'paper_optimize_ledger.csv');assert len(lines)==3 and all(x['solve_kind']=='LP' for x in lines)
        # These actual returned LPs are retained with their complete own matrices
        # and all bound/scope/cutoff identities, never copied into a formal run.
        write(folder/'diagnostic_source_receipt.json',dict(own_paid_proof_pair=pair,actual_Optimize=3,integer_Optimize=0,
            original_H_complete=True,original_LP_ledger_SHA=sha(folder/'paper_optimize_ledger.csv'),
            D0_SHA=sha(D0),D1_SHA=sha(D1),no_formal_feedback=True))
        rows.append('\t'.join([e['id'],str(D0),str(D1),repr(pair['beta0']),repr(pair['beta1']),str(OUT/'qualification/diagnostics'/e['id']),'120']))
    (OUT/'qualification/diagnostics.tsv').write_text('\n'.join(rows)+'\n',encoding='utf-8')

def billed(label):
    # All children/Optimize slots and caps are frozen before this wrapper.
    plan=read(OUT/'qualification_plan.json');assert plan['children']==11
    fee,tick=fee_begin(label,11,3000,True,dict(starts=15,seconds=33960));code=1;actual=0
    try:
        from round100_idle import ensure_idle
        ensure_idle();identity();assert read(OUT/'prospective_helper_freeze.json')['helpers']==helpers()
        actual+=1;run_child(fee,actual,'zero_native_matrix_Start',plan['steps'][0]['command'],300)
        native_contract=Path(plan['steps'][0]['command'][2])
        finite=read(native_contract/'round120_physical_embedding.json');assert finite['passed']
        for p in native_contract.glob('*.lp.round120.json'):coefficients(Path(str(p)[:-len('.round120.json')]))
        resolve()
        i=read(OUT/'qualification/chain/identity.json');l=i['launches'][0]
        actual+=1;start=time.perf_counter();startunix=time.time();supervised(l,i,start);finish_producer(l,start,startunix);chain=micro(l,i)
        exports=read(OUT/'argv_freeze.json')['qualification_exports']
        for e in exports:
            actual+=1;run_child(fee,actual,'paid_proof_export_'+e['id'],e['command'],120)
        diagnostics_TSV(exports)
        actual+=1;run_child(fee,actual,'six_full_LP_diagnostics',plan['steps'][4]['command'],850)
        mathematical_audit();information=read(OUT/'qualification/math_and_LP_information.json')
        # Complete the final-PE CLI qualification even when the LP information
        # gate later stops formal performance. No method is selected here.
        h=read(OUT/'qualification/h100/identity.json')
        for l in h['launches']:
            actual+=1;execute(l,h)
            write(fee/f'{actual:02d}_H100_after.json',dict(arm=l['arm'],producer_receipt_SHA=sha(Path(l['destination'])/'producer_receipt.json'),
                total_receipt_SHA=sha(Path(l['destination'])/'arm_total_receipt.json')))
        import compare_round112_startup as comparison
        H=comparison.compare(ROOT,h['launches'][0]['panel'],{l['arm']:Path(l['destination']) for l in h['launches'] if l['arm']!='P-GRB'})
        write(OUT/'qualification/full_H_comparison.json',H);assert all(x['qualified'] for x in H['comparisons'])
        assert actual==11 and time.perf_counter()-tick<=3000
        decision='ACCEPT' if information['at_least_one_complete_LP_nonredundant'] and not information['any_diagnostic_unresolved'] else \
            'STOP_NO_NEW_RELAXATION_INFORMATION' if information['both_complete_LPs_reliably_redundant'] else 'BLOCKED'
        write(OUT/'review/performance_admission.json',dict(decision=decision,candidate_identity_SHA=sha(OUT/'candidate_identity.json'),
            final_PE_SHA=sha(PE),DLL_SHA=sha(DLL),helpers=helpers(),source_bindings=bindings(),
            original_R119_tail_supplement_SHA=sha(OUT/'qualification/old_tail_supplement.json'),
            zero_Optimize_full_physical_matrices_types_Starts=finite,micro=chain,
            H100_actual_six_final_PE_CLI_positions=True,full_H_equal=True,LP_information_SHA=sha(OUT/'qualification/math_and_LP_information.json'),
            paid_fee_label=label,fee_close_required_before_formal=True,no_formal_feedback=True,not_performance_superiority=True))
        code=0
    except BaseException:
        (fee/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:fee_pending(fee,tick,True,code,actual)
if __name__=='__main__':billed(sys.argv[1])
