"""Direct next-only wrapper with explicit, signed offline record projection.

No production, native argv or native audit change. Raw summary/flags are never
written. The cache is verified before the first native call in this wrapper.
"""
from round110_common import *
import round110_campaign as frozen
import round110_evidence as evidence
import inspect, copy

_raw_records=frozen.records
RESUME_REQUEST=OUT/'campaign/reader_recovery/continue17_02/request.json'
RESUME_AUDIT=OUT/'review/continue17_02/audit.json'


def qualified_cache():
    ident=read(OUT/'campaign/identity.json');cache={};bindings_meta={}
    for launch in ident['launches']:
        if not evidence.has_rejection(ROOT,launch):continue
        side=ROOT/evidence.side_path(launch)
        proof=evidence.verify_rejection(ROOT,launch,Path(launch['destination']))
        cache[launch['number']]=dict(U=proof['own_U'],L=proof['qualified_L'],gap=proof['own_U'],
            certificate=proof['certificate_from_own_exact_zero'],
            source='separately_signed_own_physical_endpoint_and_own_full_domain_floor',
            status=read(Path(launch['destination'])/'result.json')['status'])
        bindings_meta[str(launch['number'])]=dict(side_path=side.relative_to(ROOT).as_posix(),side_SHA=sha(side),
            independent_audit_path=proof['independent_audit_path'],independent_audit_SHA=proof['independent_audit_SHA'])
    assert set(cache)=={15,17},'only the two actual independently proved current failures are admitted'
    return cache,bindings_meta


def projected_records(camp,cache):
    rows=copy.deepcopy(_raw_records(camp))
    if Path(camp)!=OUT/'campaign':return rows
    for row in rows:
        if row['number'] not in cache:continue
        row['original_raw_endpoint']=row['endpoint']
        row['endpoint']=copy.deepcopy(cache[row['number']])
        row['qualified_offline_audit_passed']=True
        row['original_raw_audit_passed']=row['audit_passed']
        row['explicit_signed_offline_projection']=True
    return rows


def derived_billed_source():
    source=inspect.getsource(frozen.billed)
    replacements=[
        ("all(r['audit_passed'] for r in previous)","all(r.get('qualified_offline_audit_passed',r['audit_passed']) for r in previous)"),
        ("[sys.executable,__file__,'billed',name,str(first),str(last),label]+(['--qualification'] if qualification else [])", "[sys.executable,*sys.argv]"),
        ("qualification=qualification,source_bindings=bindings(),helpers=helpers(),production_PE_SHA=production['production_PE_SHA'],DLL_SHA=DLL_SHA)",
         "qualification=qualification,source_bindings=bindings(),helpers=helpers(),production_PE_SHA=production['production_PE_SHA'],DLL_SHA=DLL_SHA,offline_projection=_projection_meta)"),
        ("arm_tick=time.perf_counter();check_identity();launch=identity['launches'][number-1]",
         "arm_tick=(_resumed_admission_tick if number==first else time.perf_counter());check_identity();launch=identity['launches'][number-1]"),
        ("    write(d/'process.json',dict(pid=os.getpid(),parent_pid=os.getppid()));code=0",
         "    (d/'source_snapshot/scripts/round110_resumed_campaign.py').write_bytes(_resume_source.read_bytes())\n    (d/'source_snapshot/derived_billed.py').write_text(_derived_source,encoding='utf-8')\n    write(d/'process.json',dict(pid=os.getpid(),parent_pid=os.getppid()));code=0")]
    for old,new in replacements:
        assert source.count(old)==1,('frozen function changed',old)
        source=source.replace(old,new)
    return source


def prepare(proposal_path,audit_path):
    from round100_idle import ensure_idle
    ensure_idle();production=check_identity();b=budget();assert not b['unclosed']
    proposal=read(ROOT/proposal_path);audit=read(ROOT/audit_path)
    assert proposal['key'][0]==17 and audit['decision']=='ACCEPT_CURRENT_CALL_REJECTION' and audit['current_key']==proposal['key']
    launch=read(OUT/'campaign/identity.json')['launches'][16]
    side=ROOT/evidence.side_path(launch)
    activated=dict(proposal,independent_audit_path=audit_path,independent_audit_SHA=sha(ROOT/audit_path))
    if side.exists():assert read(side)==activated,'existing current signed sidecar differs'
    else:write(side,activated)
    cache,meta=qualified_cache();rows=projected_records(OUT/'campaign',cache)
    assert len(rows)==17 and all(r.get('qualified_offline_audit_passed',r['audit_passed']) for r in rows)
    ident=read(OUT/'campaign/identity.json')
    assert all(not Path(v['destination']).exists() for v in ident['launches'][17:])
    reserve=frozen.full_remaining_reserve()
    assert b['remaining_starts']>=reserve['starts'] and b['remaining_outer_seconds']>=reserve['nominal_seconds']+reserve['overhead_seconds']
    source=derived_billed_source();d=RESUME_REQUEST.parent;d.mkdir(parents=True,exist_ok=False)
    (d/'derived_billed.py').write_text(source,encoding='utf-8')
    write(RESUME_REQUEST,dict(schema='round110-next-only-offline-projection-v1',
        production_PE_SHA=production['production_PE_SHA'],DLL_SHA=DLL_SHA,campaign_identity_SHA=sha(OUT/'campaign/identity.json'),
        candidate_identity_SHA=sha(OUT/'candidate_identity.json'),projection_bindings=meta,
        original_summary_SHA=sha(OUT/'campaign/summary.jsonl'),original_summary_unchanged=True,
        resumed_wrapper_path=Path(__file__).relative_to(ROOT).as_posix(),resumed_wrapper_SHA=sha(__file__),
        derived_billed_path=(d/'derived_billed.py').relative_to(ROOT).as_posix(),derived_billed_SHA=sha(d/'derived_billed.py'),
        performance_runner_SHA=sha(ROOT/'scripts/round110_campaign.py'),performance_helpers=frozen.helpers(),
        completed_native_numbers=[v['number'] for v in rows],next_native_number=18,
        never_started_numbers=[v['number'] for v in ident['launches'][17:]],budget=b,remaining_fixed_reserve=reserve,
        explicit_qualified_offline_endpoints={str(k):v for k,v in cache.items()},
        raw_false_audit_and_endpoint_preserved=True,no_native_supervisor_or_audit_change=True,
        direct_wrapper_processes=1,new_main06_tail_fee_starts=2,failed_main06_four_starts_remain_paid=True,
        first_arm_whole_clock_includes_resumed_projection_admission=True,
        superseded_request_path='results/unified_exact_round110/campaign/reader_recovery/continue17_01/request.json',
        superseded_reason='additional projection admission must be included in first resumed whole-arm clock; no native ran under01',
        no_online_UB_Start_cut_cache_transfer=True,no_solver_rerun=True,Optimize=0,native_environment=0))
    print(json.dumps(dict(request=RESUME_REQUEST.relative_to(ROOT).as_posix(),budget=b,reserve=reserve)))


def billed(name,first,last,label):
    resumed_admission_tick=time.perf_counter()
    from round100_idle import ensure_idle
    ensure_idle();check_identity()
    request=read(RESUME_REQUEST);audit=read(RESUME_AUDIT)
    assert audit['decision']=='ACCEPT_NEXT_ONLY_SAME_PE_RESUMPTION'
    assert audit['request_SHA']==sha(RESUME_REQUEST) and request['resumed_wrapper_SHA']==sha(__file__)
    assert name=='campaign' and request['next_native_number']<=first<=last<=42
    cache,meta=qualified_cache();assert meta==request['projection_bindings']
    source=derived_billed_source();assert source==(ROOT/request['derived_billed_path']).read_text(encoding='utf-8')
    if first==request['next_native_number']:assert sha(OUT/'campaign/summary.jsonl')==request['original_summary_SHA']
    frozen.records=lambda camp:projected_records(camp,cache)
    namespace=dict(vars(frozen));namespace.update(_resume_source=Path(__file__),_derived_source=source,
        _resumed_admission_tick=resumed_admission_tick,
        _projection_meta=dict(request_path=RESUME_REQUEST.relative_to(ROOT).as_posix(),request_SHA=sha(RESUME_REQUEST),
            independent_resumption_audit_path=RESUME_AUDIT.relative_to(ROOT).as_posix(),independent_resumption_audit_SHA=sha(RESUME_AUDIT),
            wrapper_SHA=sha(__file__),derived_billed_SHA=request['derived_billed_SHA'],projection_bindings=meta,
            rawsummary_read_only=True,no_online_transfer=True,first_whole_clock_includes_resumed_projection_admission=True))
    exec(compile(source,str(__file__)+'::derived_frozen_billed','exec'),namespace)
    namespace['billed'](name,first,last,label,False)


if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare(*sys.argv[2:])
    elif sys.argv[1]=='billed':billed(sys.argv[2],int(sys.argv[3]),int(sys.argv[4]),sys.argv[5])
    else:raise ValueError(sys.argv[1])
