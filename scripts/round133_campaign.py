"""Freeze and execute fixed Round133 positions using the original supervisor.

No optimization on import, prepare or status. Only an explicit admitted `run`
or `arm` action can launch a native process. Every arm has its own destination,
complete producer clock, H/Start state and immutable source plan.
"""
from round133_common import *
import copy, inspect, shutil, traceback, types
import round130_campaign as inherited
import round115_campaign as producer
import round90_lp_g_g3 as supervisor
from round121_campaign import finish_producer
from round113_progress import OptionalPublisher

def _candidate(path):
    value=read(path)
    required=['source_commit','source_hashes','production_PE','production_PE_SHA',
              'research_PE','research_PE_SHA','DLL','DLL_SHA']
    assert all(k in value for k in required), ('candidate manifest fields',required)
    assert value['DLL_SHA']==DLL_SHA and sha(value['DLL'])==DLL_SHA
    for name in ('production','research'):
        assert sha(value[name+'_PE'])==value[name+'_PE_SHA']
    for name,digest in value['source_hashes'].items():assert sha(ROOT/name)==digest,name
    return value

def _source_plan(row):
    binding=row['source_binding']
    raw=git('show',binding['commit']+':'+binding['freeze_path'])
    actual=hashlib.sha256(raw).hexdigest()
    transport=dict(commit=binding['commit'],path=binding['freeze_path'],Git_SHA256=actual,
        registered_manifest_SHA256=binding['freeze_SHA256'],Git_bytes=len(raw),transform='identity')
    if actual!=binding['freeze_SHA256']:
        # The recorded R132 local metadata is CRLF, while its pinned Git blob
        # is LF. Authorize only this observed exact byte transform, not a local
        # file fallback or arbitrary JSON reformatting. Models/raw are excluded.
        assert b'\r' not in raw,'unregistered source-manifest byte transport'
        transformed=raw.replace(b'\n',b'\r\n')
        assert hashlib.sha256(transformed).hexdigest()==binding['freeze_SHA256'],'source manifest identity or content differs'
        assert json.loads(raw)==json.loads(transformed),'transport changed complete JSON semantics'
        transport.update(transform='pinned_Git_LF_to_registered_local_CRLF',registered_manifest_bytes=len(transformed),
                         complete_JSON_semantics_equal=True,model_input_raw_or_Start_bytes_transformed=False)
    freeze=json.loads(raw)
    plan=freeze[binding['plans_key']][binding['plan_index_zero_based']]
    launch=plan['launches'][binding['launch_index_zero_based']]
    assert launch['command']==row['source_argv'] and launch['destination']==row['source_destination']
    plan['_round133_source_transport_identity']=transport
    return plan,launch

def _copy_reference(row,source_launch,camp):
    if row['method'] not in ('P','PS'):return None
    source=Path(source_launch['destination']).parents[1]/'reference'/row['role']
    assert source.is_dir(), ('required small original reference missing; restore only this member',source)
    reference=read(source/'build.json')
    assert reference==row['source_canonical_reference']
    assert sha(source/'original.lp')==reference['canonical_sha256']
    target=camp/'reference'/row['role'];target.mkdir(parents=True,exist_ok=False)
    for name in ('original.lp','build.json'):
        shutil.copyfile(source/name,target/name)
        assert sha(target/name)==sha(source/name)
    write(target/'inherited_binding.json',dict(source_commit=row['source_binding']['commit'],
          source=str(source),files={n:sha(target/n) for n in ('original.lp','build.json')},
          Optimize=0,copy_only=True,actual_current_compact_hash_must_still_match=True))
    return reference

def helper_bindings():
    # Record every imported local Python module rather than guess which old
    # source-extracted supervisor helper might affect a current run.
    import round133_read
    paths={Path(module.__file__).resolve() for module in list(sys.modules.values())
           if getattr(module,'__file__',None) and str(module.__file__).endswith('.py')}
    return {path.relative_to(ROOT).as_posix():sha(path) for path in sorted(paths)
            if path.parent==ROOT/'scripts'}

def prepare(stage,plan_path,candidate_path):
    plan_path,candidate_path=Path(plan_path),Path(candidate_path)
    plan=read(plan_path);candidate=_candidate(candidate_path)
    expected_count,expected_cap=(14,15600) if stage=='D1' else (8,7200)
    assert len(plan['arms'])==expected_count and sum(q['cap_seconds'] for q in plan['arms'])==expected_cap
    assert plan['serial_native'] and plan['threads']==plan['mip_threads']==1
    frozen=OUT/'plans'/f'{stage}_matrix_frozen.json'
    assert not frozen.exists(),'frozen plan is immutable'
    groups=[]
    for row in plan['arms']:
        assert row['results'] is None and (row['candidate_identity_pending'] or row['version']!='candidate')
        original_plan,original_launch=_source_plan(row)
        group=f'campaign/{stage}_{row["position"]:02d}'
        camp=OUT/group;camp.mkdir(parents=True,exist_ok=False)
        destination=camp/'raw'/row['arm_id']
        cmd=[arg.replace(row['destination'],str(destination)) for arg in row['argv']]
        assert str(destination) in cmd[cmd.index('--out')+1]
        if row['version']=='candidate':
            role='research' if row['method'] in ('S2R','GEOM') else 'production'
            pe=candidate[role+'_PE'];digest=candidate[role+'_PE_SHA']
            source_hashes=candidate['source_hashes'];source_commit=candidate['source_commit']
        else:
            assert stage=='D3' and row['version'] in ('original','original_E3','E3','old')
            pe=str(ORIGINAL_E3);digest=ORIGINAL_PE_SHA
            assert sha(pe)==digest
            source_hashes=original_plan['source_hashes'];source_commit=original_plan['measured_source_commit']
        cmd[0]=str(pe)
        for flag in ('--round24-executable-sha256','--round24-manifest-executable-sha256'):
            if flag in cmd:cmd[cmd.index(flag)+1]=digest
        panel=copy.deepcopy(row['panel']);panel['reference']=copy.deepcopy(row['source_canonical_reference'])
        assert sha(panel['input_path'])==panel['input_sha256']
        panel['panel_kind']=f'Round133 {stage} exposed regression/qualification'
        _copy_reference(row,original_launch,camp)
        launch=dict(number=1,group_number=row['position'],global_launch_number=row['position'],
            id=row['role'],arm='P-GRB' if row['method']=='P' else 'P-S' if row['method']=='PS' else 'M-B',
            method=row['method'],seed=row['seed'],repeat=row['repeat'],binary_layer=row['binary_layer'],
            version=row['version'],panel=panel,panel_kind=panel['panel_kind'],destination=str(destination),
            cap_seconds=row['cap_seconds'],hard_stop_seconds=row['hard_stop_seconds'],command=cmd,
            configuration=copy.deepcopy(row['expected_configuration']['configuration']),
            expected_configuration=copy.deepcopy(row['expected_configuration']),arm_id=row['arm_id'])
        common=copy.deepcopy(row['source_binding']['source_prereg_common']);common['gurobi_seed']=row['seed']
        identity=dict(schema='round133-own-complete-lifecycle-v1',prereg=dict(common=common,candidate_binary=str(pe),candidate_binary_sha256=digest),
            prereg_sha256=sha(plan_path),runner_sha256=sha(__file__),source_hashes=source_hashes,
            candidate_binary_sha256=digest,dll_sha256=DLL_SHA,measured_source_commit=source_commit,
            delivery_base_commit=BASE,launches=[launch],references={row['role']:panel['reference']},
            candidate_manifest_path=str(candidate_path),candidate_manifest_SHA=sha(candidate_path),
            source_plan_binding=row['source_binding'],source_frozen_argv=row['source_argv'],
            source_manifest_transport_identity=original_plan['_round133_source_transport_identity'],
            original_draft_argv=row['argv'],raw_path_adapter=dict(before=row['destination'],after=str(destination)),
            no_cross_arm_information=True,raw_schema=1,stage=stage)
        write(camp/'identity.json',identity)
        groups.append(dict(position=row['position'],arm_id=row['arm_id'],group=group,
                           identity_SHA=sha(camp/'identity.json'),launch=launch))
    bound=helper_bindings()
    manifest=dict(schema='round133-frozen-serial-matrix-v1',UTC=utc(),stage=stage,
        source_draft_path=str(plan_path),source_draft_SHA=sha(plan_path),
        candidate_manifest_path=str(candidate_path),candidate_manifest_SHA=sha(candidate_path),
        groups=groups,helpers=bound,full_arm_count=expected_count,full_arm_cap_sum_seconds=expected_cap,
        serial=True,own_H_and_Start=True,cross_arm_information=False,Optimize=0)
    write(frozen,manifest)
    print(json.dumps(dict(stage=stage,frozen=str(frozen),SHA=sha(frozen),arms=expected_count,Optimize=0)))
    return manifest

def supervised(launch,identity,tick):
    """Exactly the established R90/R115/R130 producer, with current bindings."""
    destination=Path(launch['destination']);publisher=OptionalPublisher(launch)
    checked=types.FunctionType(producer.production_check.__code__,dict(vars(producer),ROOT=ROOT))
    def tracked_popen(*args,**kwargs):
        child=subprocess.Popen(*args,**kwargs)
        try:
            actual=process_birth(child.pid)
            assert actual is not None
            write(destination/'child_process_origin.json',dict(pid=child.pid,parent_pid=os.getpid(),
                  actual_creation_unix=actual['creation_unix'],creation_filetime=actual['creation_filetime'],
                  command=launch['command'],seed=launch['seed'],source_commit=identity['measured_source_commit'],
                  PE_SHA=identity['candidate_binary_sha256'],creation_from_live_OS_handle=True))
        except BaseException:
            child.kill();child.wait();raise
        return child
    process_api=types.SimpleNamespace(**dict(vars(subprocess),Popen=tracked_popen))
    namespace=dict(vars(supervisor),ROOT=ROOT,CAMPAIGN=destination.parents[1],atomic_status=publisher,
                   _arm_tick=tick,production_check=checked,subprocess=process_api)
    try:return producer.supervisor_function(namespace)(launch,identity['prereg'],identity)
    finally:
        if destination.is_dir():write(destination/'progress_publication_receipt.json',dict(publisher.receipt(),
            necessary_write_before_production=True,global_namespace_modified=False))

def _admission(stage,manifest_path):
    gate=read(OUT/'review'/f'{stage}_admission.json')
    assert gate['decision']=='ACCEPT' and gate['matrix_SHA']==sha(manifest_path)
    manifest=read(manifest_path)
    assert sha(manifest['candidate_manifest_path'])==manifest['candidate_manifest_SHA']
    _candidate(manifest['candidate_manifest_path'])
    for name,digest in manifest['helpers'].items():assert sha(ROOT/name)==digest,name
    if stage=='D3':
        from round133_read import legacy_scope_gate
        legacy_scope_gate()
    return manifest

def execute_arm(stage,position,label):
    """Called by one metered outer; never calls another meter or arm."""
    from round133_read import verify
    manifest_path=OUT/'plans'/f'{stage}_matrix_frozen.json'
    manifest=_admission(stage,manifest_path)
    group=manifest['groups'][int(position)-1]
    assert group['position']==int(position)
    camp=OUT/group['group'];assert sha(camp/'identity.json')==group['identity_SHA']
    identity=read(camp/'identity.json');launch=identity['launches'][0];destination=Path(launch['destination'])
    if (destination/'verification_closeout.json').exists():
        raise AssertionError('sealed arm is read-only; use reader, never repeat Optimize')
    if not destination.exists():
        tick,creation=inherited.process_origin()
        assert sha(launch['command'][0])==identity['candidate_binary_sha256']
        assert sha(ROOT/launch['panel']['input_path'])==launch['panel']['input_sha256']
        supervised(launch,identity,tick)
        finish_producer(launch,tick,creation)
    else:
        assert (destination/'producer_receipt.json').exists() and (destination/'producer_seal.json').exists(), 'unsealed interrupted native needs explicit disposition'
    started=time.perf_counter()
    try:value=verify(launch,identity)
    finally:
        write(OUT/'cost_segments'/label/'verification.json',dict(kind='non-native postproduction complete audit, including retained failures',
              seconds=time.perf_counter()-started,native_Optimize=0))
    write(OUT/'runtime_status.json',dict(UTC=utc(),stage=stage,last_sealed=launch['arm_id'],
          position=position,producer_seal_SHA=sha(destination/'producer_seal.json'),
          verification_closeout_SHA=sha(destination/'verification_closeout.json')))
    print(json.dumps(dict(stage=stage,position=position,arm=value['arm'])),flush=True)

def run(stage,stop_after=None):
    manifest_path=OUT/'plans'/f'{stage}_matrix_frozen.json'
    manifest=_admission(stage,manifest_path)
    kind='D' if stage=='D1' else 'D3'
    for group in manifest['groups']:
        if stop_after is not None and group['position']>stop_after:break
        launch=group['launch'];destination=Path(launch['destination'])
        if (destination/'verification_closeout.json').exists():continue
        label=f'{stage}_{group["position"]:02d}_01'
        assert not (OUT/'fees'/label).exists(), 'inspect existing PID/failure; no automatic Optimize retry'
        result=metered(label,kind,[PYTHON,ROOT/'scripts/round133_campaign.py','arm',stage,group['position'],label],
                       reservation=launch['cap_seconds'],timeout=launch['cap_seconds']+1800)
        assert result==0, ('arm failed; retain all evidence and stop serial sequence',label,result)
    print('ROUND133_SERIAL_SEQUENCE_RETURNED',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest='action',required=True)
    prep=sub.add_parser('prepare');prep.add_argument('stage',choices=['D1','D3']);prep.add_argument('--plan',type=Path,required=True);prep.add_argument('--candidate-manifest',type=Path,required=True)
    arm=sub.add_parser('arm');arm.add_argument('stage',choices=['D1','D3']);arm.add_argument('position',type=int);arm.add_argument('label')
    run_parser=sub.add_parser('run');run_parser.add_argument('stage',choices=['D1','D3']);run_parser.add_argument('--stop-after',type=int)
    args=parser.parse_args()
    if args.action=='prepare':prepare(args.stage,args.plan,args.candidate_manifest)
    elif args.action=='arm':execute_arm(args.stage,args.position,args.label)
    else:run(args.stage,args.stop_after)
