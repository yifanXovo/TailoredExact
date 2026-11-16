"""Independent R169 post-return audit; standard library, no optimization.

Consumes the actual C++ commit receipts plus new invocation/completion schema.
Does not create historical supervisor/observation/producer-seal receipts.
The NEJ1 value is the C++ producer's publication/close marker, sampled after
the JSON close and hash and before writing the commit file. Commit-file close
and external first-seen times were not separately measured and remain unknown.
"""
from pathlib import Path
import argparse,ast,collections,contextlib,copy,hashlib,inspect,json,math,re,sys,time,types
from fractions import Fraction as F
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
import round108_reader as core
import round118_call_logs as call_logs
import compare_round112_startup as startup
import round86_native_evidence as commits
import round135_ap_audit as ap_audit
from round169_common import OUT,read,write,sha,bind,utc
TOL=1e-7

def pure_definitions(file,names,globals_):
    """Reuse exact pure definitions without importing historical campaign modules."""
    path=ROOT/'scripts'/file;tree=ast.parse(path.read_text(encoding='utf-8-sig'),filename=str(path))
    selected=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names]
    assert {n.name for n in selected}==set(names)
    namespace=dict(globals_,__name__=file[:-3],__file__=str(path))
    exec(compile(ast.Module(body=selected,type_ignores=[]),str(path),'exec'),namespace)
    return types.SimpleNamespace(**namespace)

proof=pure_definitions('round135_read.py',[
    'strict_global_bound','strict_bound_context','quality_predicate','validate_event_lifecycle',
    'expected_settings','_journal','_legacy_view','_same_domain','reconcile',
    'independent_source_checks','_claims','emitter_scope_policy','no_improver_shortcut_analysis',
    'native_release_lifecycle'],dict(globals(),startup=startup))
models=pure_definitions('round111_seed_audit.py',['ArmModels'],dict(globals(),
    PARSER_VERSION='round108-one-line-lp-v1',CONTRACT_VERSION='round111-original-model-contract-index-v1'))

def accepted_H(p,d):
    h=startup.reconstruct(ROOT,p,d)
    initial=read(d/'hga.csv.exchange/initial.json');final=read(d/'hga.csv.exchange/final.json')
    choice=final if final['F']<initial['F']-1e-10 else initial
    h['physical']=core.full_fleet(ROOT,p,choice)
    h['fleet']=startup.fleet_key(p,choice['routes'])
    h['actual_base_strict_acceptance']='final_F < initial_F - 1e-10'
    return h

def committed(path,cap):
    raw=path.read_bytes();assert raw.endswith(b'\n')
    fields=raw.decode('ascii').split();assert len(fields)==5 and fields[0]=='NEJ1'
    seq,t,size=int(fields[1]),float(fields[2]),int(fields[3])
    assert path.name==f'event_{seq}.commit' and math.isfinite(t) and 0<=t<=cap
    data=path.with_suffix('.json').read_bytes()
    assert len(data)==size and hashlib.sha256(data).hexdigest()==fields[4]
    e=json.loads(data);assert e['schema']==1 and e['sequence']==seq
    return dict(sequence=seq,data_close_seconds=t,first_observed_seconds=None,
        effective_available_seconds=t,sha256=fields[4],payload=e,
        availability_basis='actual_C++_producer_publication_close_marker_after_JSON_close_hash_before_commit_write_not_external_first_observation')

def journal(launch,d):
    paths=sorted((d/'journal').glob('event_*.commit'),key=lambda p:int(p.stem.split('_')[1]))
    records=[committed(p,launch['cap_seconds']) for p in paths]
    assert [r['sequence'] for r in records]==list(range(1,len(records)+1))
    assert len(list((d/'journal').glob('event_*.json')))==len(records)
    # Reuse the unchanged lifecycle/parameter/physical/local/global predicates.
    # Only the old external-observation receipt accessor is replaced by the
    # verified actual new runner receipt interpretation above.
    def actual_receipt(path,observed,cap):
        assert observed is None
        return committed(path,cap)
    fn=types.FunctionType(proof._journal.__code__,dict(vars(proof),ROOT=ROOT,
        commits=types.SimpleNamespace(receipt=actual_receipt)))
    return fn(launch,d,records),records

def phases(d,cap):
    # Child paths isolate logs but retain the one process-wide sequence/clock.
    files=[d/'phases.csv']+sorted((d/'primal').glob('*/phases.csv'))
    allrows=[]
    for p in files:
        for row in core.rows(p):allrows.append(dict(row,file=p.relative_to(ROOT).as_posix()))
    allrows.sort(key=lambda r:int(r['sequence']))
    assert allrows[0]['event']=='process_entry' and allrows[-1]['event']=='process_exit'
    assert allrows[-1]['status']=='complete' and allrows[-1]['detail']=='rc=0'
    previous=-1
    for seq,row in enumerate(allrows):
        assert int(row['sequence'])==seq,'missing or duplicate process-wide phase event'
        t=float(row['process_seconds']);assert previous<=t<=cap;previous=t
        assert abs(float(row['nominal_deadline_remaining_seconds'])-(cap-t))<.02
        assert abs(float(row['work_deadline_remaining_seconds'])-(cap-t-6))<.02
    return allrows

def full_H(p,d):
    selected=read(d/'primal/selection.json');out=[]
    expected=['base'] if selected['mode']=='off' else ['base',('M_s1' if selected['mode']=='multistart' else 'C_s1'),
        ('M_s2' if selected['mode']=='multistart' else 'C_s2')]
    assert selected['calls']==len(expected)
    for name in expected:
        folder=d/'primal'/name;meta=read(folder/'path.json');q=dict(p,**{'lambda':meta['search_lambda']})
        trace=d if name=='base' else folder
        # This frozen reconstruction checks all 25 seed traces and true physical
        # closure snapshots, using the original base-H's binary64 acceptance.
        h=accepted_H(q,trace)
        assert h['complete'] and meta['complete'] and meta['descent_seeds_completed']==25
        f=read(folder/'fleet.json');physical=core.full_fleet(ROOT,p,dict(f,objective=meta['F']))
        assert startup.fleet_key(p,f['routes'])==h['fleet']
        assert abs(physical['F']-meta['F'])<TOL
        assert sha(folder/'fleet.json')==meta['fleet_SHA256']
        order_raw=(folder/'initial_random_orders.txt').read_bytes()
        order_semantic=order_raw.replace(b'\r\n',b'\n')
        assert hashlib.sha256(order_semantic).hexdigest()==meta['initial_random_orders_SHA256']
        assert len(order_semantic.splitlines())==24
        assert meta['effective_seed']==20260626+(0 if name=='base' else int(name[-1]))
        wanted_lambda=p['lambda']*(.5 if name=='C_s1' else 2 if name=='C_s2' else 1)
        assert meta['search_lambda']==wanted_lambda and meta['evaluation_lambda']==p['lambda']
        out.append(dict(path=name,effective_seed=meta['effective_seed'],search_lambda=meta['search_lambda'],
            original_F=physical['F'],full_H_complete=h['complete'],seed_ids=h['seed_ids'],
            physical=physical,canonical_fleet=h['fleet'],fleet_file=bind(folder/'fleet.json'),
            initial_orders_LF_semantic_SHA256=meta['initial_random_orders_SHA256'],
            initial_orders_file_byte_SHA256=hashlib.sha256(order_raw).hexdigest(),
            H_seconds=meta['H_seconds'],path_seconds=meta['path_seconds'],decoded_checks=meta['decoded_checks']))
    chosen=next(x for x in out if x['path']==selected['selected'])
    best=out[0]
    for x in out[1:]:
        if x['original_F']<best['original_F']-1e-10:best=x
    assert best['path']==chosen['path']
    return dict(selection=selected,paths=out,selected=chosen,
        complete_arm_initialization=all(x['full_H_complete'] for x in out),expected_arm_calls=len(expected),
        necessary_H_complete_native_field_is_H_panel_gate_only=True)

def audit(position):
    tick=time.perf_counter()
    matrix=read(OUT/'matrix_execution_frozen.json');registered=next(x for x in matrix['positions'] if x['position']==position)
    d=Path(registered['directory']);inv=read(d/'invocation.json');completion=read(d/'completion.json');result=read(d/'result.json')
    assert inv['argv']==registered['argv'] and inv['PE']['SHA256']==registered['PE_SHA256']
    assert completion['rc']==0 and not completion['affinity'].get('wrapper_killed')
    assert completion['process_outer_seconds']<=registered['cap']+2
    assert completion['result']['SHA256']==sha(d/'result.json')
    assert result['process_return_code']==0 and result['process_shutdown_margin_seconds']==6
    assert result['nominal_process_wall_budget_seconds']==registered['cap']
    assert result['process_wall_time_comparable'] is True
    assert result['overall_deadline_started_at_process_entry'] is True
    assert result['algorithm_preset']=='research-round99-ensc-discrete-structure-m-binary'
    candidate=read(OUT/'candidate_manifest.json')
    assert inv['PE']['SHA256']==candidate['PE']['SHA256'] and inv['DLL']['SHA256']==candidate['DLL']['SHA256']
    for name,digest in candidate['source_hashes'].items():assert sha(ROOT/name)==digest,name
    p=next(x for x in read(OUT/'h_panel_frozen.json')['roles'] if x['id']==registered['role'])
    p=dict(p,cap_seconds=registered['cap']);assert sha(ROOT/p['input_path'])==p['input_sha256']
    launch=dict(id=p['id'],arm='M-B',method='S2',arm_id=d.name,version='candidate',seed=0,
        configuration=dict(MIPFocus=0,Cuts=-1),command=inv['argv'],cap_seconds=registered['cap'],panel=p)
    js,records=journal(launch,d)
    assert not js['failure'] and not js['unreturned_ids']
    legacy,kinds=proof._legacy_view(js,launch,d)
    phase=phases(d,registered['cap'])
    physical=core.full_fleet(ROOT,p,result);assert abs(physical['F']-result['upper_bound'])<TOL
    h=full_H(p,d)
    initial=[r['payload'] for r in records if r['payload']['kind']=='witness' and r['payload']['call']==0]
    assert len(initial)==1
    assert startup.fleet_key(p,initial[0]['routes'])==h['selected']['canonical_fleet']
    assert abs(initial[0]['objective']-h['selected']['original_F'])<TOL
    assert abs(result['initial_heuristic_UB']-h['selected']['original_F'])<TOL
    data=core.evidence.instance(ROOT,p);context=models.ArmModels();contracts=[]
    core.start_reader.ROOT=ROOT
    try:
        emitter=proof.emitter_scope_policy(launch,dict(source_hashes=candidate['source_hashes']))
        for cid,call in js['calls'].items():
            path=core.portable(ROOT,call['model_path']);fact,model=context.model_contract(ROOT,p,path,'M-B')
            ap=ap_audit.contract(model,data,False);scope=context.model_scope_contract(call,model,p)
            shortcut=proof.no_improver_shortcut_analysis(launch,call,model,emitter,physical['F'])
            assert not shortcut['model_scope_issue']
            contracts.append(dict(call=cid,model=fact,scope=scope,AP=ap,solve_kind=kinds[cid],
                no_improver_shortcut_check=shortcut))
        view=call_logs.build(ROOT,launch,d,legacy,result,model_parser=lambda path:context.data(path)[1][0])
        actual=view['actual'];ledger=view['ledger']
        assert set(actual)==js['actual_started_ids'] and len(actual)==len(ledger)
        assert result['external_gini_tree_optimize_count']==len(actual)
        assert result['external_gini_tree_lp_optimize_count']==sum(row['solve_kind']=='LP' for row in ledger)
        proof.native_release_lifecycle(result,js)
        assert result['external_gini_tree_backend_parameter_roundtrip_valid']
        starts=[(path,read(path)) for path in sorted((d/'external/native_logs').glob('*.round68.start.json')) if read(path).get('submitted')]
        start_checks=[]
        for digest in sorted({v['model_sha256'] for _,v in starts}):
            path=next(core.portable(ROOT,c['model_path']) for c in js['calls'].values() if c['model_sha256']==digest)
            start_checks.extend(core.start_reader.audit_model(path,[(sp,v) for sp,v in starts if v['model_sha256']==digest],'m-binary'))
        controller=core.evidence.controller_tables(d,result)
        chain=dict(actual=actual,ledger=ledger,logs=[dict(call=b['call'],text=view['views'][b['call']]['text']) for b in view['bindings']])
        own=js['witnesses']+[dict(physical,source='actual_new_runner_return_result',input_SHA=p['input_sha256'],
            physical_verified=True,available=completion['process_outer_seconds'])]
        quality=proof.independent_source_checks(launch,js,kinds,chain,result,own)
        claims=proof._claims(launch,js,chain,result);rejection=proof.reconcile(claims,own)
        assert not rejection['rejections'] and not js['source_rejections']
        with call_logs.activate(view),proof.strict_bound_context():
            legacy['returned_native_proofs']=core.returned_native_proofs(ROOT,legacy,controller)
            chronological=core.chronological_cover(legacy,controller,physical['F'])
            cover=core.complete_cover(d,physical['F'],legacy,controller,(p['V']-1)/p['V'])
        L=cover['L'];U=physical['F'];certificate=cover['all_relevant_closed'] and U-L<=TOL
        assert abs(L-result['lower_bound'])<=TOL and L<=U+TOL
        assert certificate==result['strict_certified_original_problem']
        required=['root_coverage_valid','parent_child_coverage_valid','all_leaf_bounds_valid','leaf_bounds_monotone',
            'global_bound_monotone','feasibility_consistency_gate']
        assert all(result['external_gini_tree_'+name] is True for name in required)
        native_seconds=sum(float(row['solver_runtime']) for row in ledger)
        out=dict(schema='round169-independent-new-runner-postreturn-audit-v1',UTC=utc(),passed=True,
            position=position,role=p['id'],research_arm=registered['arm'],Optimize_run_by_reviewer=0,
            no_historical_supervisor_receipts_fabricated=True,external_first_observation_not_recorded=True,
            commit_availability_basis='C++ producer publication/close marker: sampled after JSON close+hash and before commit-file write; commit-file close and external first-seen were not separately measured; raw byte/sequence/hash verified',
            input=bind(ROOT/p['input_path']),actual_invocation=bind(d/'invocation.json'),completion=completion,
            U=U,L=L,absolute_gap=U-L,relative_gap=(U-L)/max(abs(U),1e-12),certificate=certificate,
            certificate_basis='qualified_complete_original_interval_cover_closed' if certificate else 'qualified_complete_original_interval_cover_open',
            true_final_physical=physical,full_paid_H=h,Start_checks=start_checks,models=contracts,
            journal_events=len(records),actual_Optimize=len(actual),LP=sum(k=='LP' for k in kinds.values()),
            MIP=sum(k!='LP' for k in kinds.values()),Native_seconds=native_seconds,
            actual_call_log_bindings=view['bindings'],actual_native_quality=quality,
            qualified_cover=cover,chronological_cover=chronological,phase_event_count=len(phase),
            phase_files=sorted({r['file'] for r in phase}),audit_seconds=time.perf_counter()-tick,
            raw_bytes_unchanged=True)
        return out
    finally:context.clear()

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('positions',nargs='+',type=int);args=ap.parse_args()
    for n in args.positions:
        target=OUT/f'review/complete_audit_{n:02}.json'
        attempt_start=time.perf_counter();attempt_epoch=time.time();ok=False;error=None
        try:
            value=audit(n);write(target,value)
            ok=True
            print(json.dumps(dict(position=n,PASS=True,U=value['U'],L=value['L'],certificate=value['certificate'],Optimize=value['actual_Optimize'],seconds=value['audit_seconds'])),flush=True)
        except Exception as e:
            error=repr(e)
            write(OUT/f'review/complete_audit_{n:02}_failure.json',dict(UTC=utc(),error=repr(e),Optimize_run_by_reviewer=0))
            raise
        finally:
            path=OUT/'review/complete_audit_attempts.json'
            attempts=read(path) if path.is_file() else []
            attempts.append(dict(position=n,start_epoch=attempt_epoch,UTC=utc(),PASS=ok,error=error,
                audit_inclusive_seconds=time.perf_counter()-attempt_start,Optimize=0))
            write(path,attempts)
