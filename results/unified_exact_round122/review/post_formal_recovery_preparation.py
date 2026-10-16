"""Finite engineering tests and source equivalence; never reads formal raw."""
from pathlib import Path
import ast,contextlib,copy,datetime,hashlib,os,time,types
import post_formal_independent as current
from independent_review_round122 import sha,save_receipt

REVIEW=Path(__file__).resolve().parent
OLD='5a12806c87c4c84c9118cec14141d6cda1db2c5b2df19f2b105caa2b565bc03c'
def dump(node):return ast.dump(node,include_attributes=False)
def funcs(path):return {n.name:n for n in ast.parse(path.read_text(encoding='utf-8-sig')).body if isinstance(n,ast.FunctionDef)}

def run():
    start=time.perf_counter();preserved=REVIEW/'post_formal_independent_pre_recovery.py';source=REVIEW/'post_formal_independent.py'
    assert sha(preserved)==OLD
    before=funcs(preserved);after=funcs(source)
    unchanged=[n for n in before if n in after and dump(before[n])==dump(after[n])]
    science=['require','real','validate_arm','independent_pair','independent_stage','editorial_arm','normalize','typed_equal','memory_tests','actual_d1_model_review']
    assert unchanged==science
    # The whole all32/all48 scientific body is retained, with only an extra
    # original-byte callback and a recovery-scope evidence field in its receipt.
    body=copy.deepcopy(after['_review']);body.name='review';body.args=copy.deepcopy(before['review'].args)
    remove=[i for i,n in enumerate(body.body) if isinstance(n,ast.Expr) and ast.unparse(n)=='assert_originals()']
    assert len(remove)==1;body.body.pop(remove[0])
    result=next(n for n in ast.walk(body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='result' for t in n.targets))
    recovery_fields=[q for q in result.value.keywords if q.arg=='recovery_evidence']
    assert len(recovery_fields)==1 and ast.unparse(recovery_fields[0].value)=='recovery_scope'
    result.value.keywords=[q for q in result.value.keywords if q.arg!='recovery_evidence']
    assert dump(body)==dump(before['review'])
    clock=copy.deepcopy(after['clocks_and_seals'])
    owner=next(n for n in clock.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='owner')
    assert ast.unparse(owner)=='owner = raw.rd(owner_receipt_path(l))'
    original_owner=next(n for n in before['clocks_and_seals'].body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='owner')
    owner.value=copy.deepcopy(original_owner.value)
    assert dump(clock)==dump(before['clocks_and_seals'])
    # Invoke existing invented pair/stage/typed-data cases only.
    finite=current.memory_tests();cases=list(finite['cases'])
    # Required-sealed gate runs against invented in-memory metadata paths.
    metadata={}
    class Virtual:
        def __init__(self,path):self.path=path
        def __truediv__(self,name):return Virtual(self.path+'/'+str(name))
        def __str__(self):return self.path
        def exists(self):return self.path in metadata
    out=Virtual('fixture')
    for n in range(1,9):
        metadata[f'fixture/fees/formal{n:02d}/receipt.json']=dict(exit_code=1 if n==8 else 0,actual_exit_observed=True)
        metadata[f'fixture/reconstruction/group{n:02d}/current_core.json']={}
    for name in ['all32_arms.json','all48_pairs.json','stage_decision.json','major_negative_results.json','mechanism_account.json','resource_summary.json','proof_reliability.json']:
        metadata['fixture/'+name]={}
    for label in ['postseal08a','continue08d1']:metadata[f'fixture/fees/{label}/receipt.json']=dict(exit_code=0,actual_exit_observed=True)
    metadata['fixture/recovery/group08/group_closeout.json']=dict(passed=True)
    ns=dict(OUT=out,read=lambda p:metadata[str(p)],require=current.require)
    exec(compile(ast.Module(body=[after['required_sealed']],type_ignores=[]),'independent invented metadata','exec'),ns)
    ns['required_sealed']();cases.append('complete_fixed_recovery_metadata_gate')
    base=copy.deepcopy(metadata)
    mutations=[('original_failure_must_stay_failed',lambda:metadata['fixture/fees/formal08/receipt.json'].__setitem__('exit_code',0)),
        ('no_unclosed_continuation',lambda:metadata.pop('fixture/fees/continue08d1/receipt.json')),
        ('failed_continuation_not_complete',lambda:metadata['fixture/fees/continue08d1/receipt.json'].__setitem__('exit_code',1)),
        ('all_eight_cores_required',lambda:metadata.pop('fixture/reconstruction/group08/current_core.json')),
        ('all48_report_required',lambda:metadata.pop('fixture/all48_pairs.json')),
        ('actual_exit_required',lambda:metadata['fixture/fees/formal08/receipt.json'].__setitem__('actual_exit_observed',False)),
        ('recovery_closeout_required',lambda:metadata['fixture/recovery/group08/group_closeout.json'].__setitem__('passed',False))]
    for name,change in mutations:
        metadata.clear();metadata.update(copy.deepcopy(base));change()
        try:ns['required_sealed']()
        except current.InvalidEvidence:cases.append(name)
        else:raise AssertionError('invalid invented metadata accepted '+name)
    # Exact owner selection: no other position can inherit the continuation PID.
    for group in range(1,9):
        for number,method in enumerate(current.METHODS,1):
            l=dict(group_number=group,number=number,arm=method,seed=1 if group in (7,8) else 0)
            expected=current.OUT/'fees'/('continue08d1' if group==8 and number==4 and method=='MB-D1' else f'formal{group:02d}')/'receipt.json'
            assert current.owner_receipt_path(l)==expected
    cases.append('only_exact_original_ordinal4_wrapper_owner')
    # Exercise independent path view with fake original open/stat; no disk IO.
    original_open,original_stat=Path.open,Path.stat;trace=[]
    def fake_open(path,*args,**kw):trace.append(('open',str(path)));return str(path)
    def fake_stat(path,*args,**kw):trace.append(('stat',str(path)));return str(path)
    view_ns=dict(Path=Path,contextlib=contextlib,os=os,hashlib=hashlib,OUT=current.OUT,
        read=lambda path:{},require=current.require,RECOVERED_SIDECARS=current.RECOVERED_SIDECARS,
        original_P_files=lambda pr,opener:trace.append(('physical_original_check',opener is fake_open)),sha=lambda path:'unchanged')
    exec(compile(ast.Module(body=[after['sealed_recovery_paths']],type_ignores=[]),'independent in-memory path routing','exec'),view_ns)
    d=current.OUT/'campaign/group08/raw/03_PB-C50-S_S1_P-GRB';view=current.OUT/'recovery/group08/p_sidecars'
    Path.open,Path.stat=fake_open,fake_stat
    try:
        with view_ns['sealed_recovery_paths'](dict(recovered_sidecars={'audit.json':'unchanged'})) as check:
            for name in current.RECOVERED_SIDECARS:
                assert (d/name).open('rb')==str(view/name)
                assert (d/name).stat()==str(view/name)
            assert (d/'result.json').open('rb')==str(d/'result.json')
            sibling=Path(str(d)+'-other/audit.json');assert sibling.open('rb')==str(sibling)
            for name in ['audit.json','result.json','new/unmapped.json']:
                for mode in ['w','a','x','r+','wb']:
                    try:(d/name).open(mode)
                    except current.InvalidEvidence:pass
                    else:raise AssertionError('original write accepted')
            check()
        assert Path.open is fake_open and Path.stat is fake_stat
        assert (d/'audit.json').open('rb')==str(d/'audit.json')
    finally:Path.open,Path.stat=original_open,original_stat
    assert ('physical_original_check',True) in trace
    cases+=['exact13_derived_sidecar_read_stat_mapping','unmapped_raw_and_component_boundary_retained',
        '15_original_raw_write_modes_rejected','physical_original_manifest_uses_unrouted_open','path_methods_restored_after_view']
    result=dict(decision='PENDING',scope='Post-formal reviewer recovery engineering adaptation prepared and finite in-memory tests executed; actual all32/all48 review not run.',
        UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),reviewer='independent executor /root/contract_review',
        script_SHA=sha(source),pre_recovery_source_SHA=sha(preserved),preparation_script_SHA=sha(__file__),
        scientific_functions_AST_identical=science,entire_scientific_review_body_reverse_AST_identical=True,
        clocks_and_seals_AST_identical_except_exact_owner_path=True,
        original_reviewer_source_preserved=preserved.name,engineering_changes=['Preserved failed formal08 plus successful postseal08a/continue08d1 fee and group-closeout gates',
            'Exact old/new adapter, prerecord, actual re-audit and independent admission identity chain',
            'Only original ordinal4 D1 child owner uses continue08d1 wrapper; all other owners remain original formal wrapper',
            'Independent read-only derived P sidecar path view; original physical bytes and failure stay checked through unrouted open',
            'Actual continuation wrapper OS birth/import clock and admission-before-launch chronology checks',
            'Recovery evidence identities appended to independent receipt; no changed pair/stage/physical/model/Start rule'],
        cases=cases,test_count=len(cases),production_pair_or_decide_called=False,production_recovery_adapter_imported=False,
        actual_formal_review='PENDING_REQUIRED_ALL_EIGHT_SEALED_GROUPS_AND_REPORTS',formal_raw_read=False,
        native_starts=0,Optimize=0,raw_or_measured_helper_edits=0,seconds=time.perf_counter()-start)
    save_receipt('post_formal_recovery_preparation.json',result)

if __name__=='__main__':run()
