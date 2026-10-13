"""A bounded qualification batch, with the real event chain before H100."""
from round119_common import *
import subprocess,traceback,copy,csv,json
from round119_prepare import resolve
from round119_campaign import supervised,finish_producer,execute
from round119_evidence import ArmModels,extension,event_chain
import round114_audit as audit
import round118_call_logs as logs
import round108_reader as core
from round114_claims import reconcile

def micro(l,i):
    tick=time.perf_counter();unix=time.time();supervised(l,i,tick);finish_producer(l,tick,unix)
    d=Path(l['destination']);r=read(d/'result.json');observations=read(d/'observations.json')
    assert r['algorithm_preset']=='qualification-round119-empty-seed-mb-pc'
    assert '--round119-qualification-empty-seed' in l['command'] and l['panel']['V']==8
    j=audit.journal(ROOT,l,d,observations);context=ArmModels()
    try:
        for cid,c in j['calls'].items():
            fact,m=context.model_contract(ROOT,l['panel'],core.portable(ROOT,c['model_path']),'MB-PC')
            context.model_scope_contract(c,m,l['panel'])
        view=logs.build(ROOT,l,d,j,r)
    finally:context.clear()
    with extension(),logs.activate(view):
        chain=audit.return_chain(ROOT,l,d,j,r,read(d/'completion.json'))
        claims=audit.claims_for(l,j,chain,r);ind=audit.independent(ROOT,l,d,j,r,read(d/'completion.json'),chain)
        adjudication=reconcile(claims,ind['witnesses']);assert not adjudication['rejections'],'PROOF_RELIABILITY_PRIORITY'
        controller=core.evidence.controller_tables(d,r)
        j['returned_native_proofs']=core.returned_native_proofs(ROOT,j,controller)
        cover=core.complete_cover(d,ind['own_U'],j,controller,(l['panel']['V']-1)/l['panel']['V'])
        source=event_chain(ROOT,l,d,j,controller,view)
        core.start_reader.ROOT=ROOT
        submitted=[(p,read(p)) for p in sorted((d/'external/native_logs').glob('*.round68.start.json')) if read(p).get('submitted')]
        for digest in {q['model_sha256'] for p,q in submitted}:
            model=next(core.portable(ROOT,c['model_path']) for c in j['calls'].values() if c['model_sha256']==digest)
            core.start_reader.audit_model(model,[(p,q) for p,q in submitted if q['model_sha256']==digest],'m-binary')
    assert source['strict_requests']>=1 and source['committed']>=1 and any(c['next_Optimize_calls'] for c in source['contracts']),'actual complete contraction chain not exposed'
    assert abs(ind['own_U']-1.2)<=1e-7 and r['external_gini_tree_all_relevant_leaves_closed']
    assert any(x['kind']=='native_returned' and x['status']=='INTERRUPTED' for x in [json.loads(z) for z in (d/'external/round119_events.jsonl').read_text().splitlines()])
    write(d/'micro_qualification.json',dict(passed=True,event_contract=source,complete_actual_rows_and_Starts=True,
        scope_models=cover,own_U=ind['own_U'],positive_original_optimum=1.2,original_problem_certificate=True,
        physical_argument='B=2, all eight D=w=1: integer Y totals 0/1/2; F is 1.2/1.925/1.65/2.075. Pickup2 and loaded return Q2 attains 1.2. Paid right LP bound remains native evidence',
        artificial_initial_information='explicit legal empty fleet only; no artificial bound or historical route',
        not_formal_H_performance=True,actual_Optimize=j['started'],all_returns=j['returned']==j['started']))
    return source

def finite_logs():
    # Reuse the actual safe two-call/epoch/log reader tests in a new output dir.
    import qualify_round118 as old
    q=OUT/'qualification/finite_logs';q.mkdir(parents=True,exist_ok=False);cases=[]
    old.log_cases(q,cases)
    write(q/'summary.json',dict(passed=True,cases=cases,Optimize=0,fixtures_not_observations=True))

def billed(label):
    fee,tick=fee_begin(label,5,1200,True,dict(starts=16,seconds=36480));code=1;actual=0
    try:
        from round100_idle import ensure_idle
        ensure_idle();identity();assert read(OUT/'prospective_helper_freeze.json')['helpers']==helpers()
        # Final PE source/flags are frozen before any native exporter or solve.
        finite_logs()
        args=[str(EXPORTER),str(OUT/'qualification/reference.tsv'),str(OUT/'qualification/native_contract'),str(ROOT/'reference/round119_qualification/micro_enumeration.txt')]
        with (fee/'exporter_stdout.log').open('x') as stdout,(fee/'exporter_stderr.log').open('x') as stderr:
            child=subprocess.Popen(args,cwd=ROOT,env=environment(),stdout=stdout,stderr=stderr);actual+=1
            write(fee/'exporter_launch.json',dict(pid=child.pid,command=args,started_unix=time.time(),Optimize=0))
            rc=child.wait(timeout=240);write(fee/'exporter_return.json',dict(exit_code=rc,returned_unix=time.time(),Optimize=0))
            assert rc==0,'actual native finite/matrix/Start exporter failed'
        resolve()
        i=read(OUT/'qualification/chain/identity.json');actual+=1;source=micro(i['launches'][0],i)
        # The complete chain must pass before spending the real H100 positions.
        h=read(OUT/'qualification/h100/identity.json')
        for n,l in enumerate(h['launches'],1):
            actual+=1;execute(l,h)
            write(fee/f'H100_{n}_after.json',dict(arm=l['arm'],producer_receipt_SHA=sha(Path(l['destination'])/'producer_receipt.json'),
                total_receipt_SHA=sha(Path(l['destination'])/'arm_total_receipt.json')))
        import compare_round112_startup as comparison
        import inspect
        warm={l['arm']:Path(l['destination']) for l in h['launches'] if l['arm']!='P-GRB'}
        source_text=inspect.getsource(comparison.compare).replace("values['P-S']","values['M-B']").replace("name=='P-S'","name=='M-B'").replace("control='P-S'","control='M-B'")
        namespace=dict(vars(comparison));exec(compile(source_text,__file__+'::MB_PC_complete_H_comparison','exec'),namespace)
        H=namespace['compare'](ROOT,h['launches'][0]['panel'],warm)
        write(OUT/'qualification/full_H_comparison.json',H)
        assert all(x['qualified'] for x in H['comparisons'])
        assert time.perf_counter()-tick<=1200
        write(OUT/'review/performance_admission.json',dict(decision='ACCEPT',candidate_identity_SHA=sha(OUT/'candidate_identity.json'),
            final_PE_SHA=sha(PE),DLL_SHA=sha(DLL),helpers=helpers(),source_bindings=bindings(),
            complete_real_interrupted_contraction_and_new_domain_solve=True,micro=source,
            H100_actual_three_final_PE_CLI_positions_once=True,full_25_seed_H_equal=True,
            disabled_four_profile_native_matrices_and_complete_Starts=True,preflight_replay_SHA=sha(OUT/'preflight_replay.json'),
            paid_fee_label=label,fee_close_required_before_formal=True,not_performance_superiority=True))
        code=0
    except BaseException:
        (fee/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:fee_pending(fee,tick,True,code,actual)
if __name__=='__main__':billed(sys.argv[1])
