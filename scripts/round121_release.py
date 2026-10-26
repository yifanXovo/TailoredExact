"""One bounded safe scientific carrier/export/empty-root current rebuild."""
from round121_common import ROOT,OUT,read,write,sha
from pathlib import Path
import argparse,ast,inspect,json,math,sys,time,types
import round120_release as inherited
import publication_security as security
ROUND='results/unified_exact_round121'
FORBIDDEN=inherited.FORBIDDEN
def closure(root):
    pending=['read_round121','round121_finish_report','round121_release',
        'round121_blocked_core','round121_blocked_report'];found=set()
    while pending:
        name=pending.pop();p=root/'scripts'/(name+'.py')
        if name in found or not p.is_file():continue
        found.add(name)
        for node in ast.walk(ast.parse(p.read_text(encoding='utf-8-sig'))):
            modules=[a.name for a in node.names] if isinstance(node,ast.Import) else [node.module] if isinstance(node,ast.ImportFrom) else []
            pending.extend(m for m in modules if m and (root/'scripts'/(m+'.py')).is_file())
    return {root/'scripts'/(n+'.py') for n in found}
def inventory(root):
    root=Path(root).resolve();out=root/ROUND;candidate=read(out/'candidate_identity.json');files=closure(root)
    files.update(root/n for n in candidate['source_bindings']);files.update(root/n for n in candidate['helpers'])
    files.update(root/'scripts'/n for n in ['publication_security.py','round121_precontract_review.py'])
    manifest=read(out/'input_manifest.json')
    for p in manifest['roles']+manifest['qualification_roles']:files.add(root/p['input_path'])
    files.update(p for p in (root/'reference/round121_confirmation').rglob('*') if p.is_file())
    # Exactly the safe fixed-source and small overlap authorities, never old
    # campaigns/carriers or contaminated HTML.
    for n in ['source/snapshot.json','source/source_station_table.csv','source/row_decisions.json','projection_contract.json','historical_input_hash_index.json','input_manifest.json']:
        files.add(root/'results/unified_exact_round116'/n)
    snapshot=read(root/'results/unified_exact_round116/source/snapshot.json');files.add(root/snapshot['station_response_path'])
    for round_number in [116,118]:
        m=read(root/f'results/unified_exact_round{round_number}/input_manifest.json')
        for p in m['roles']:
            if p['V']<=50:files.add(root/p['selection_path'])
    authorities={'preregistration.json','protocol.json','helper_paths.json','scope_contract.json','fixed_manifest.json'}
    files.update(p for p in (root/'results').glob('unified_exact_round*/*.json') if p.name in authorities and p.parent.name!='unified_exact_round121')
    for rn,names in [(117,['publication_policy.md','safe_restore.md','scope_contract.json']),
        (118,['input_manifest.json','paper_algorithm_spec.md','paper_claim_evidence_map.md']),
        (119,['final_report.md','mathematical_contract.md','stage_decision.json']),
        (120,['final_report.md','mathematical_contract.md','production_identity.json','candidate_identity.json','stage_decision.json','qualification_summary.md','safe_restore.md','delivery/restored_check_scope.json','review/extra_review.md'])]:
        for n in names:
            p=root/f'results/unified_exact_round{rn}'/n
            if p.exists():files.add(p)
    excluded={'compact_evidence','delivery','restored_reconstruction','local_only_prepublication'}
    later={'public_pack_receipt.json','public_dependency_closure.json','delivery_summary.md','preexisting_main_untracked_paths.txt'}
    for p in out.rglob('*'):
        if not p.is_file() or p.suffix.lower() in FORBIDDEN:continue
        rel=p.relative_to(out).as_posix()
        if rel in later or any(rel.startswith(n+'/') for n in excluded):continue
        if rel.startswith(('review/extra_review','engineering/public_export')):continue
        files.add(p)
    if (out/'public_dependency_closure.json').exists():files.add(out/'public_dependency_closure.json')
    for p in files:
        assert p.is_file() and p.resolve().is_relative_to(root) and p.suffix.lower() not in FORBIDDEN
        assert 'build' not in p.relative_to(root).parts and '__pycache__' not in p.parts
        assert p.stat().st_size<=security.MAX_MEMBER_BYTES
    return root,out,sorted(files)
def _inherited(fn,*args):
    namespace=dict(vars(inherited),ROOT=ROOT,OUT=OUT,ROUND=ROUND,inventory=inventory,closure=closure)
    if fn is inherited.pack:
        source=inspect.getsource(fn).replace('round120-current-safe-evidence-v1','round121-current-safe-evidence-v1')
        exec(compile(source,__file__+'::unchanged_safe_pack','exec'),namespace);return namespace['pack'](*args)
    return types.FunctionType(fn.__code__,namespace,fn.__name__)(*args)
def preflight(root):return _inherited(inherited.preflight,root)
def pack(root):return _inherited(inherited.pack,root)
def restore(root,commit,destination):return _inherited(inherited.restore,root,commit,destination)
def normalize(value,roots):
    if isinstance(value,dict):return {k:normalize(v,roots) for k,v in value.items()}
    if isinstance(value,list):return [normalize(v,roots) for v in value]
    if isinstance(value,str):
        for root in roots:
            prefix=str(root)
            for form in [prefix,prefix.replace('\\','/'),prefix.replace('/','\\')]:
                if value==form or value.startswith(form+'/') or value.startswith(form+'\\'):
                    return '<ROOT>'+value[len(form):].replace('\\','/')
    return value
def typed_equal(a,b,path=''):
    assert type(a) is type(b),('typed JSON mismatch',path,type(a).__name__,type(b).__name__)
    if isinstance(a,dict):
        assert a.keys()==b.keys(),('JSON keys differ',path)
        for k in a:typed_equal(a[k],b[k],path+'/'+k)
    elif isinstance(a,list):
        assert len(a)==len(b),('JSON array length differs',path)
        for i,(x,y) in enumerate(zip(a,b)):typed_equal(x,y,path+'/'+str(i))
    else:
        assert a==b,('JSON value differs',path)
        if isinstance(a,float) and a==0:assert math.copysign(1,a)==math.copysign(1,b),('zero sign changed',path)
def restored_check(root):
    tick=time.perf_counter();root=Path(root).resolve();assert ROOT==root
    opened=set();runtime=Path(sys.base_prefix).resolve()
    def boundary(event,args):
        if event!='open' or not isinstance(args[0],(str,bytes)):return
        v=args[0].decode() if isinstance(args[0],bytes) else args[0];p=Path(v).resolve()
        assert p.is_relative_to(root) or p.is_relative_to(runtime),('external file access',str(p))
        if p.is_relative_to(root):opened.add(p.relative_to(root).as_posix())
    sys.addaudithook(boundary)
    import read_round121 as reader
    from round121_decision import decide
    assert reader.ROOT==root
    measured=read(root/ROUND/'initialization_receipt.json')['worktree'];out=root/ROUND
    assert not (out/'restored_check.json').exists()
    if read(out/'stage_decision.json')['execution_stage']=='BLOCKED':
        from round121_blocked_core import reconstruct
        before={p.relative_to(root).as_posix():sha(p) for p in (out/'qualification').rglob('*') if p.is_file()}
        actual=json.loads(json.dumps(reconstruct(),allow_nan=False));expected=read(out/'blocked_current_core.json')
        typed_equal(normalize(actual,[root,measured]),normalize(expected,[root,measured]))
        typed_equal(actual['stage'],read(out/'stage_decision.json'))
        typed_equal(actual['formal_slots'],read(out/'all16_arms.json'))
        typed_equal(actual['pair_slots'],read(out/'all18_pairs.json'))
        after={p.relative_to(root).as_posix():sha(p) for p in (out/'qualification').rglob('*') if p.is_file()}
        assert before==after,'blocked replay must not mutate any expanded qualification evidence'
        assert not list(root.rglob('*.exe')) and not list(root.rglob('*.dll'))
        modules=[]
        for n,m in list(sys.modules.items()):
            p=getattr(m,'__file__',None)
            if not p:continue
            p=Path(p).resolve()
            if p.is_relative_to(runtime):continue
            assert p.is_relative_to(root),('external helper import',n,str(p))
            modules.append(dict(module=n,path=p.relative_to(root).as_posix()))
        write(out/'restored_check.json',dict(passed=True,scope='finite blocked current evidence only',
            execution_stage='BLOCKED',formal_arms=0,evaluable_pairs=0,planned_formal_slots=16,planned_pair_slots=18,
            all_typed_JSON_fields_and_blocked_stage_equal=True,
            qualification_actual_CLI=2,new_D1_native_record='UNAVAILABLE: not executed',
            regenerated_derived_sidecars=[],all_expanded_qualification_members_byte_unchanged=True,
            initial_unpack_hash_equality_distinct_from_reconstruction=True,scientific_carrier_immutable=True,
            normalization='complete measured/restored root path prefixes only; typed stored JSON; no field dropped or rounded',
            no_original_evidence_or_helper_fallback=True,native_PE_DLL_absent=True,
            file_access_boundary='Python open/module checks; not an OS sandbox; runtime prefix allowed',
            actual_opened_root_paths=sorted(opened),actual_local_modules=modules,Optimize=0,native_starts=0,
            engineering_seconds=time.perf_counter()-tick,receipt_does_not_attest_future_commits=True))
        print(json.dumps(dict(passed=True,stage='BLOCKED',formal_arms=0,evaluable_pairs=0,planned_slots=16,pair_slots=18)),flush=True)
        return
    before={p.relative_to(root).as_posix():sha(p) for p in (out/'campaign').rglob('*') if p.is_file()}
    values=[];groups=[]
    for n in range(1,6):
        dest=out/f'restored_reconstruction/group{n:02d}';assert not dest.exists()
        value=reader.rebuild_group(n,dest)
        actual=read(dest/'current_core.json');expected=read(out/f'reconstruction/group{n:02d}/current_core.json')
        typed_equal(json.loads(json.dumps(value,allow_nan=False)),actual)
        typed_equal(normalize(actual,[root,measured]),normalize(expected,[root,measured]))
        values.append(actual);groups.append(dict(group=n,arms=len(actual['arms']),pairs=len(actual['pairs']),rebuilt_SHA=sha(dest/'current_core.json'),every_typed_JSON_field_equal=True))
    stage=decide(values,True,proof_risk=any(v['adjudication']['rejections'] for v in values))
    typed_equal(stage,read(out/'stage_decision.json'))
    changed=[]
    for name,digest in before.items():
        path=root/name
        if sha(path)==digest:continue
        assert path.name=='round120_event_contract.json','unexpected expanded-member change'
        # Every changed member is a regenerated derived sidecar. Compare it to
        # the same mechanism embedded in the immutable expected core.
        parts=Path(name).parts;group=int(next(p for p in parts if p.startswith('group'))[-2:]);arm=path.parent.name.split('_',3)[-1]
        expected=read(out/f'reconstruction/group{group:02d}/current_core.json')
        saved=next(e for e in expected['mechanism'] if e['arm']==arm);saved=dict(saved);saved.pop('arm')
        typed_equal(normalize(read(path),[root,measured]),normalize(saved,[root,measured]))
        changed.append(dict(path=name,unpacked_SHA=digest,reconstructed_SHA=sha(path),only_root_prefix_paths_differ=True))
    assert not list(root.rglob('*.exe')) and not list(root.rglob('*.dll'))
    modules=[]
    for n,m in list(sys.modules.items()):
        p=getattr(m,'__file__',None)
        if not p:continue
        p=Path(p).resolve()
        if p.is_relative_to(runtime):continue
        assert p.is_relative_to(root),('external helper import',n,str(p));modules.append(dict(module=n,path=p.relative_to(root).as_posix()))
    write(out/'restored_check.json',dict(passed=True,groups=groups,formal_arms=16,pairs=18,all_typed_JSON_fields_and_stage_equal=True,
        normalization='only complete measured/restored root path component prefixes; no field removed/rounded; stored JSON arrays compared',
        regenerated_derived_sidecars=changed,all_other_compared_campaign_members_byte_unchanged=True,
        initial_unpack_hash_equality_distinct_from_derived_reconstruction=True,scientific_carrier_immutable=True,
        no_original_evidence_or_helper_fallback=True,native_PE_DLL_absent=True,file_access_boundary='Python open/module checks; not an OS sandbox; runtime prefix allowed',
        actual_opened_root_paths=sorted(opened),actual_local_modules=modules,Optimize=0,native_starts=0,engineering_seconds=time.perf_counter()-tick,
        receipt_does_not_attest_future_commits=True))
    print(json.dumps(dict(passed=True,arms=16,pairs=18,derived_sidecars_changed=len(changed))),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['preflight','pack','restore','restored-check']);p.add_argument('--root',required=True);p.add_argument('--commit');p.add_argument('--destination');a=p.parse_args()
    {'preflight':lambda:preflight(a.root),'pack':lambda:pack(a.root),'restore':lambda:restore(a.root,a.commit,a.destination),'restored-check':lambda:restored_check(a.root)}[a.mode]()
