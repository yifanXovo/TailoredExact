"""Explicit post-seal accepted-H repair; frozen helpers and native argv stay intact.

Import installs nothing. The arm command changes only the verifier entry point;
the H/PS checks are replaced inside that verifier after a sealed producer stops.
All native production and the entire original verifier otherwise run unchanged.
"""
from round133_common import *
import contextlib, inspect, traceback
import round133_campaign as campaign
import round133_read as reader

POLICY='ACTUAL_STRICT_CONSIDER_ACCEPTED_H_POSTSEAL_ONLY_V1'
FROZEN={
    'scripts/round133_common.py':'80c6951d3fbd368853fd2c447b34c82dda0d422097614ab707579ea74a0757d0',
    'scripts/round133_campaign.py':'85a0867c981368f1ee7a161155626c120422d482f5f2eaffeca020b80d780807',
    'scripts/round133_read.py':'933af994bf3def115d9870c33f409709d5509a1b42f7b0546645691ce1b7c80a',
    'scripts/round133_small_native.py':'1f0a8bd4026614182a60d5bf4a99f98ea44de8d462d0f8603e5a01ed797d59b1',
    'scripts/compare_round112_startup.py':'9fb8ecf86c75239dc68ebb1983d9f26bb7a99c49ff8d21fe618dbd9ea6c2dbd2',
}
AMENDMENT=OUT/'plans/postverify_handoff_repair_amendment.json'
GATE=OUT/'review/postverify_handoff_repair_admission.json'
REPAIR=OUT/'repair/postverify_handoff'
FIXTURE_DRIVER=ROOT/'scripts/round133_postverify_repair_tests.py'
_VERIFY=reader.verify
_RECONSTRUCT=reader.startup.reconstruct
_START_AUDIT=reader.compact_start.start_audit
_WRITE=reader.write

def source_contract(path):
    """Read only the actual reused main source, with its existing object binding."""
    code=Path(path).read_text(encoding='utf-8-sig')
    fragments={
        'strict_acceptance':'if (!out.found || v.objective < out.verification.objective - 1e-10) {',
        'accepted_routes_assignment':'out.routes = routes;',
        'exchange_input':'const auto balanced = ebrp::runRound83ExchangeDescent(instance, opt, out.routes, trace_directory);',
        'exchange_consider':'consider(balanced.routes, "round83_equal_net_exchange_physical_descent");',
    }
    for name,fragment in fragments.items():assert fragment in code,(name,path)
    assert code.count(fragments['strict_acceptance'])==1
    assert code.count(fragments['exchange_consider'])==1
    return dict(path=str(path),SHA=sha(path),fragments=fragments,
        acceptance='F_final < F_initial - 1e-10 using the serialized verified binary64 objectives')

def accepted_endpoint(initial_F,final_F):
    """Exactly main.cpp's comparison, including subtraction and strictness."""
    assert type(initial_F) in (float,int) and type(final_F) in (float,int)
    assert math.isfinite(initial_F) and math.isfinite(final_F)
    return 'final.json' if final_F < initial_F - 1e-10 else 'initial.json'

def select_exchange(root,p,d):
    """Called only in postverification, never by the producer or its checks."""
    folder=Path(d)/'hga.csv.exchange'
    before=read(folder/'initial.json');after=read(folder/'final.json')
    before_phys=reader.core.full_fleet(root,p,before)
    after_phys=reader.core.full_fleet(root,p,after)
    # The exact serialized doubles originate in writeRound61Witness's
    # independently verified 17-digit snapshots. Physical checks stay separate.
    assert abs(before_phys['F']-before['F'])<=reader.TOL
    assert abs(after_phys['F']-after['F'])<=reader.TOL
    assert after_phys['F']<=before_phys['F']+reader.TOL
    name=accepted_endpoint(before['F'],after['F'])
    accepted=after if name=='final.json' else before
    physical=after_phys if name=='final.json' else before_phys
    return dict(accepted_witness=accepted,accepted_physical=physical,
        exchange_final_physical=after_phys,
        accepted_fleet=reader.startup.fleet_key(p,accepted['routes']),
        exchange_final_fleet=reader.startup.fleet_key(p,after['routes']),
        selection=dict(accepted_snapshot=name,initial_F=before['F'],final_F=after['F'],
            binary64_cutoff=before['F']-1e-10,
            comparison='final_F < initial_F - 1e-10',
            initial_SHA=sha(folder/'initial.json'),final_SHA=sha(folder/'final.json'),
            no_fleet_relabel_or_journal_rewrite=True))

def reconstruction_source():
    original=inspect.getsource(_RECONSTRUCT)
    old="final=read(base/'final.json');physical=core.full_fleet(root,p,final)"
    new="selection=repair_selection(root,p,d)\n    final=selection['accepted_witness'];physical=selection['accepted_physical']"
    assert original.count(old)==1
    return original,original.replace(old,new)

def reconstruct_accepted(root,p,d):
    # Only the endpoint chosen at the top changes. In particular the complete
    # semantic-trace loop still reads the real final.json, and all 25 seeds,
    # closure physical checks, and optional PS startup checks remain untouched.
    _,source=reconstruction_source()
    namespace=dict(vars(reader.startup),repair_selection=select_exchange)
    exec(compile(source,__file__+'::accepted_H_reconstruct','exec'),namespace)
    value=namespace['reconstruct'](root,p,d)
    selected=select_exchange(root,p,d)
    assert value['fleet']==selected['accepted_fleet']
    value.update(exchange_final_physical=selected['exchange_final_physical'],
        exchange_final_fleet=selected['exchange_final_fleet'],accepted_H_selection=selected['selection'])
    return value

def assert_startup_handoff(root,p,d):
    selected=select_exchange(root,p,d)
    startup_path=Path(d)/'result.json.round112.startup.json'
    seed=read(startup_path);physical=reader.core.full_fleet(root,p,seed)
    assert abs(physical['F']-selected['accepted_physical']['F'])<=reader.TOL
    assert reader.startup.fleet_key(p,seed['routes'])==selected['accepted_fleet'], 'PS startup differs from actual accepted H handoff'
    return dict(startup_SHA=sha(startup_path),accepted_H_selection=selected['selection'],
        exact_capacity_assigned_fleet_equal=True,physical=physical)

def start_audit_accepted(root,p,d):
    # No original Start predicates are removed: all columns, numeric rows,
    # domains, integrality, readback and objective still pass the frozen audit.
    result=_START_AUDIT(root,p,d)
    return dict(result,actual_accepted_H_handoff=assert_startup_handoff(root,p,d))

def handoff_receipt(root,launch,d):
    """Cold P has no H artifacts and keeps the complete original P audit."""
    if launch['arm']=='P-GRB':
        return dict(effective_adapter_H_applied=False,accepted_H_selection=None,
            accepted_H_fleet=None,exchange_final_fleet=None,exchange_final_physical=None)
    selected=select_exchange(root,launch['panel'],d)
    return dict(effective_adapter_H_applied=True,accepted_H_selection=selected['selection'],
        accepted_H_fleet=selected['accepted_fleet'],exchange_final_fleet=selected['exchange_final_fleet'],
        exchange_final_physical=selected['exchange_final_physical'])

def frozen_bindings():
    for name,digest in FROZEN.items():assert sha(ROOT/name)==digest,name
    return dict(FROZEN)

def amendment_bindings():
    frozen_bindings()
    build_path=OUT/'candidate_build.json';build=read(build_path)
    roles={}
    for role,source in [('production',ROOT/'src/main.cpp'),('research',WORK/'build-cache/round132/main.cpp')]:
        obj=Path(build['binaries'][role]['main_object']['path'])
        binding=obj.parent/'main_binding.json'
        assert sha(obj)==build['binaries'][role]['main_object']['SHA']
        assert sha(source)==read(binding)['source'],('source bytes of reused main object',role)
        roles[role]=dict(source_contract(source),object_path=str(obj),object_SHA=sha(obj),
            existing_main_binding=str(binding),existing_main_binding_SHA=sha(binding))
    return dict(frozen_helpers=frozen_bindings(),adapter_SHA=sha(__file__),
        fixture_driver_SHA=sha(FIXTURE_DRIVER),candidate_build_SHA=sha(build_path),main_roles=roles,
        compact_start_audit_SHA=sha(ROOT/'scripts/round112_audit.py'),
        witness_writer_SHA=sha(ROOT/'src/Round61Candidates.cpp'),
        exchange_source_SHA=sha(ROOT/'src/Round83BlockExchange.cpp'))

def admission(stage):
    amendment=read(AMENDMENT);gate=read(GATE)
    assert gate['decision']=='ACCEPT' and gate['policy']==POLICY
    assert gate['amendment_SHA']==sha(AMENDMENT) and gate['adapter_SHA']==sha(__file__)
    assert amendment['policy']==POLICY and amendment['bindings']==amendment_bindings()
    assert sha(OUT/'candidate_manifest.json')==amendment['candidate_manifest_SHA']
    assert stage in amendment['stages']
    assert sha(OUT/'plans'/f'{stage}_matrix_frozen.json')==amendment['matrix_SHA'][stage]
    return dict(path=str(GATE),SHA=sha(GATE),amendment_SHA=sha(AMENDMENT),policy=POLICY)

def validate_effective_receipt(d,launch,identity_SHA,gate,attempt_root=REPAIR):
    """A closeout alone cannot pass the amended management/aggregation gate."""
    d=Path(d);attempt_root=Path(attempt_root)
    names=('audit.json','verification_closeout.json','arm_total_receipt.json','round133_endpoint.json')
    assert all((d/name).is_file() for name in names),'postverify-metadata-incomplete: missing sealed verifier output'
    outputs={name:sha(d/name) for name in names};accepted=[];incomplete=[]
    for binding_path in sorted(attempt_root.glob('*/binding.json')):
        binding=read(binding_path)
        if binding['launch']['destination']!=launch['destination']:continue
        success_path=binding_path.parent/'success.json'
        if not success_path.is_file():incomplete.append(str(binding_path.parent));continue
        success=read(success_path)
        assert binding['launch']==launch and binding['identity_SHA']==identity_SHA,'postverify effective identity mismatch'
        assert binding['gate']==gate and binding['adapter_SHA']==sha(__file__),'postverify effective policy mismatch'
        assert binding['reader_SHA']==FROZEN['scripts/round133_read.py']
        assert binding['original_verify_source_SHA']==hashlib.sha256(inspect.getsource(_VERIFY).encode()).hexdigest()
        assert binding['producer_receipt_SHA']==sha(d/'producer_receipt.json')
        assert binding['producer_seal_SHA']==sha(d/'producer_seal.json')
        if binding['old_failure_SHA'] is not None:
            assert sha(d/'round133_verification_failure.json')==binding['old_failure_SHA'],'original failed audit was changed'
        assert success['binding_SHA']==sha(binding_path) and success['passed'] is True
        assert success['Optimize']==success['native_starts']==0
        assert success['old_failure_preserved'] and success['original_producer_seal_preserved']
        assert success['outputs']==outputs,'postverify effective output hash mismatch'
        applied=launch['arm']!='P-GRB'
        assert success['effective_adapter_H_applied'] is applied
        for key in ('accepted_H_selection','accepted_H_fleet','exchange_final_fleet','exchange_final_physical'):
            assert (success[key] is not None) is applied,('postverify effective H availability',key)
        accepted.append(dict(binding_path=str(binding_path),binding_SHA=sha(binding_path),
            success_path=str(success_path),success_SHA=sha(success_path),outputs=outputs,
            effective_adapter_H_applied=applied,identity_SHA=identity_SHA))
    assert len(accepted)==1,('postverify-metadata-incomplete: exactly one bound success receipt required',str(d),incomplete)
    return accepted[0]

def validate_management_group(group,gate):
    path=OUT/group['group']/'identity.json';assert sha(path)==group['identity_SHA']
    identity=read(path);launch=identity['launches'][0];assert launch==group['launch']
    return validate_effective_receipt(Path(launch['destination']),launch,group['identity_SHA'],gate)

@contextlib.contextmanager
def postseal_functions(d,failure_path):
    """Install only after the native producer has sealed and stopped."""
    d=Path(d);producer=read(d/'producer_receipt.json')
    assert producer['native_stopped_no_reentry'] is True
    assert producer['producer_seal_SHA']==sha(d/'producer_seal.json')
    assert read(d/'producer_seal.json')['native_stopped_no_reentry'] is True
    previous=(reader.startup.reconstruct,reader.compact_start.start_audit,reader.write)
    assert previous[0] is _RECONSTRUCT and previous[1] is _START_AUDIT
    def repair_write(path,value):
        # Preserve the failed original derived record byte-for-byte. A new
        # failure gets a distinct attempt-local name, with no raw overwrite.
        target=Path(path)
        if target==d/'round133_verification_failure.json':target=Path(failure_path)
        return _WRITE(target,value)
    try:
        reader.startup.reconstruct=reconstruct_accepted
        reader.compact_start.start_audit=start_audit_accepted
        reader.write=repair_write
        yield
    finally:
        reader.startup.reconstruct,reader.compact_start.start_audit,reader.write=previous

def verify_repaired(launch,identity,label):
    gate=admission(identity['stage']);d=Path(launch['destination'])
    assert not (d/'verification_closeout.json').exists(),'sealed verification is immutable'
    producer=read(d/'producer_receipt.json');seal_path=d/'producer_seal.json'
    assert producer['native_stopped_no_reentry'] and producer['producer_seal_SHA']==sha(seal_path)
    assert read(seal_path)['native_stopped_no_reentry'] is True
    attempt=REPAIR/label;attempt.mkdir(parents=True,exist_ok=False)
    old_failure=d/'round133_verification_failure.json'
    old_SHA=sha(old_failure) if old_failure.exists() else None
    before=dict(UTC=utc(),gate=gate,adapter_SHA=sha(__file__),reader_SHA=sha(ROOT/'scripts/round133_read.py'),
        original_verify_source_SHA=hashlib.sha256(inspect.getsource(_VERIFY).encode()).hexdigest(),
        producer_receipt_SHA=sha(d/'producer_receipt.json'),producer_seal_SHA=sha(seal_path),
        old_failure_SHA=old_SHA,launch=launch,identity_SHA=sha(OUT/f'campaign/{identity["stage"]}_{launch["group_number"]:02d}'/'identity.json'),
        Optimize=0,native_producer_changed=False,actual_verification_clock_not_backdated=True)
    write(attempt/'binding.json',before)
    tick=time.perf_counter()
    try:
        with postseal_functions(d,attempt/'verification_failure.json'):
            value=_VERIFY(launch,identity)
        handoff=handoff_receipt(ROOT,launch,d)
        original,corrected=reconstruction_source()
        write(attempt/'success.json',dict(UTC=utc(),passed=True,binding_SHA=sha(attempt/'binding.json'),
            original_reconstruct_source_SHA=hashlib.sha256(original.encode()).hexdigest(),
            corrected_reconstruct_source_SHA=hashlib.sha256(corrected.encode()).hexdigest(),
            **handoff,
            outputs={name:sha(d/name) for name in ['audit.json','verification_closeout.json','arm_total_receipt.json','round133_endpoint.json']},
            pure_postverification_seconds=time.perf_counter()-tick,Optimize=0,native_starts=0,
            T_produce=producer['T_produce'],old_failure_preserved=not old_SHA or sha(old_failure)==old_SHA,
            original_producer_seal_preserved=sha(seal_path)==before['producer_seal_SHA']))
        assert not old_SHA or sha(old_failure)==old_SHA
        validate_effective_receipt(d,launch,before['identity_SHA'],gate)
        return value
    except BaseException as error:
        write(attempt/'failed.json',dict(UTC=utc(),error=repr(error),traceback=traceback.format_exc(),
            seconds=time.perf_counter()-tick,Optimize=0,native_starts=0,binding_SHA=sha(attempt/'binding.json'),
            old_failure_preserved=not old_SHA or sha(old_failure)==old_SHA))
        raise

@contextlib.contextmanager
def deferred_verifier(label):
    """Producer-visible H/PS functions remain exactly the frozen originals."""
    previous=reader.verify
    assert previous is _VERIFY
    try:
        reader.verify=lambda launch,identity:verify_repaired(launch,identity,label)
        yield
    finally:reader.verify=previous

def arm(stage,position,label):
    admission(stage)
    assert os.environ.get('ROUND133_METERED_PARENT_LABEL')==label,'main agent must launch the finite outer meter'
    with deferred_verifier(label):campaign.execute_arm(stage,position,label)

def repair(stage,position,label):
    admission(stage)
    assert os.environ.get('ROUND133_METERED_PARENT_LABEL')==label
    manifest=campaign._admission(stage,OUT/'plans'/f'{stage}_matrix_frozen.json')
    group=manifest['groups'][position-1];assert group['position']==position
    identity_path=OUT/group['group']/'identity.json';assert sha(identity_path)==group['identity_SHA']
    identity=read(identity_path);launch=identity['launches'][0];d=Path(launch['destination'])
    assert (d/'producer_seal.json').exists() and (d/'producer_receipt.json').exists()
    tick=time.perf_counter()
    try:value=verify_repaired(launch,identity,label)
    finally:write(OUT/'cost_segments'/label/'verification.json',dict(kind='pure postverification repair; existing sealed raw only',seconds=time.perf_counter()-tick,native_Optimize=0))
    print(json.dumps(dict(stage=stage,position=position,arm=value['arm'],Optimize=0)),flush=True)

def run(stage,stop_after=None):
    # The established scheduler/caps remain; the explicit child entry loads the
    # adapter, and a management gate precedes each existing-closeout skip.
    gate=admission(stage)
    source=inspect.getsource(campaign.run)
    old="[PYTHON,ROOT/'scripts/round133_campaign.py','arm',stage,group['position'],label]"
    new="[PYTHON,ROOT/'scripts/round133_postverify_repair.py','arm',stage,group['position'],label]"
    assert source.count(old)==1
    skip="if (destination/'verification_closeout.json').exists():continue"
    checked_skip="if (destination/'verification_closeout.json').exists():\n            validate_management_group(group,effective_gate)\n            continue"
    assert source.count(skip)==1
    source=source.replace(old,new).replace(skip,checked_skip)
    namespace=dict(vars(campaign),validate_management_group=validate_management_group,effective_gate=gate)
    exec(compile(source,__file__+'::explicit_repair_children','exec'),namespace)
    return namespace['run'](stage,stop_after)

def rebuild(stage):
    gate=admission(stage)
    manifest=campaign._admission(stage,OUT/'plans'/f'{stage}_matrix_frozen.json')
    checked=[]
    for group in manifest['groups']:
        d=Path(group['launch']['destination'])
        if (d/'verification_closeout.json').exists():checked.append(validate_management_group(group,gate))
        else:assert not (d/'round133_endpoint.json').exists(),'postverify-metadata-incomplete: endpoint without closeout'
    # No table accepts an endpoint before this effective-policy check. A missing
    # success receipt stops here, with no native retry and no mixed-policy table.
    reader.rebuild(stage)
    write(OUT/'reports'/stage/'postverify_repair_management_gate.json',dict(UTC=utc(),
        policy=POLICY,admission=gate,matrix_SHA=sha(OUT/'plans'/f'{stage}_matrix_frozen.json'),
        all_sealed_formal_arms_effective_policy_checked=True,checked=checked,
        reports={name:sha(OUT/'reports'/stage/name) for name in ('arms.json','pairs.json')},
        Optimize=0,native_starts=0))

if __name__=='__main__':
    parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest='action',required=True)
    for action in ('arm','repair'):
        command=sub.add_parser(action);command.add_argument('stage',choices=['D1','D3']);command.add_argument('position',type=int);command.add_argument('label')
    command=sub.add_parser('run');command.add_argument('stage',choices=['D1','D3']);command.add_argument('--stop-after',type=int)
    command=sub.add_parser('rebuild');command.add_argument('stage',choices=['D1','D3'])
    options=parser.parse_args()
    if options.action=='arm':arm(options.stage,options.position,options.label)
    elif options.action=='repair':repair(options.stage,options.position,options.label)
    elif options.action=='run':run(options.stage,options.stop_after)
    else:rebuild(options.stage)
