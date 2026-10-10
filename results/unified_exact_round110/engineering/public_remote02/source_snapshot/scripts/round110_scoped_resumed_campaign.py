"""Next-only direct wrapper after the independently reviewed scoped25 fault.

Reuse the frozen supervisor and prior admitted clock policy. Added proof/cache
admission is included in the first arm clock; raw audit flags remain untouched.
"""
from round110_common import *
import round110_campaign as frozen
import round110_resumed_campaign as prior
import round110_scoped_evidence as evidence
import copy

RESUME_REQUEST=OUT/'campaign/reader_recovery/continue25_04/request.json'
RESUME_AUDIT=OUT/'review/continue25_04/audit.json'


def qualified_cache():
    ident=read(OUT/'campaign/identity.json');cache={};meta={}
    for number in [15,17,25]:
        launch=ident['launches'][number-1];side=ROOT/evidence.side_path(launch)
        proof=(evidence.verify_signed_scope_binding(ROOT,launch,Path(launch['destination'])) if number==25
            else evidence.verify_rejection(ROOT,launch,Path(launch['destination'])))
        cache[number]=dict(U=proof['own_U'],L=proof['qualified_L'],gap=proof['own_U'],certificate=proof['certificate_from_own_exact_zero'],
            source='separately_signed_own_physical_endpoint_and_own_full_domain_floor',status=read(Path(launch['destination'])/'result.json')['status'])
        meta[str(number)]=dict(side_path=side.relative_to(ROOT).as_posix(),side_SHA=sha(side),
            independent_audit_path=proof['independent_audit_path'],independent_audit_SHA=proof['independent_audit_SHA'])
    assert {v['number'] for v in ident['launches'] if evidence.has_rejection(ROOT,v)}==set(cache)
    return cache,meta


def derived_billed_source():
    source=prior.derived_billed_source()
    old="    (d/'source_snapshot/scripts/round110_resumed_campaign.py').write_bytes(_resume_source.read_bytes())"
    new="    (d/'source_snapshot/scripts/round110_scoped_resumed_campaign.py').write_bytes(_resume_source.read_bytes())\n    (d/'source_snapshot/scripts/round110_scoped_evidence.py').write_bytes(_scoped_source.read_bytes())\n    (d/'source_snapshot/scripts/round110_resumed_campaign.py').write_bytes(_prior_source.read_bytes())"
    assert source.count(old)==1;return source.replace(old,new)


def prepare(proposal_path,audit_path):
    from round100_idle import ensure_idle
    ensure_idle();production=check_identity();b=budget();assert not b['unclosed']
    proposal=read(ROOT/proposal_path);audit=read(ROOT/audit_path)
    assert proposal['key']==[25,'G100-C1',0,'M-B'] and audit['decision']=='ACCEPT_CURRENT_SCOPED_CALL_REJECTION'
    assert audit['current_key']==proposal['key']
    launch=read(OUT/'campaign/identity.json')['launches'][24];side=ROOT/evidence.side_path(launch)
    activated=dict(proposal,independent_audit_path=audit_path,independent_audit_SHA=sha(ROOT/audit_path))
    if side.exists():assert read(side)==activated
    else:write(side,activated)
    cache,meta=qualified_cache();rows=prior.projected_records(OUT/'campaign',cache)
    assert len(rows)==25 and all(v.get('qualified_offline_audit_passed',v['audit_passed']) for v in rows)
    ident=read(OUT/'campaign/identity.json');assert all(not Path(v['destination']).exists() for v in ident['launches'][25:])
    reserve=frozen.full_remaining_reserve()
    assert reserve==dict(starts=24,nominal_seconds=52200,overhead_seconds=840)
    assert b['remaining_starts']>=reserve['starts'] and b['remaining_outer_seconds']>=reserve['nominal_seconds']+reserve['overhead_seconds']
    source=derived_billed_source();d=RESUME_REQUEST.parent;d.mkdir(parents=True,exist_ok=False)
    (d/'derived_billed.py').write_text(source,encoding='utf-8')
    write(RESUME_REQUEST,dict(schema='round110-next-only-offline-projection-v1',
        production_PE_SHA=production['production_PE_SHA'],DLL_SHA=DLL_SHA,campaign_identity_SHA=sha(OUT/'campaign/identity.json'),
        candidate_identity_SHA=sha(OUT/'candidate_identity.json'),projection_bindings=meta,
        original_summary_SHA=sha(OUT/'campaign/summary.jsonl'),original_summary_unchanged=True,
        resumed_wrapper_path=Path(__file__).relative_to(ROOT).as_posix(),resumed_wrapper_SHA=sha(__file__),
        derived_billed_path=(d/'derived_billed.py').relative_to(ROOT).as_posix(),derived_billed_SHA=sha(d/'derived_billed.py'),
        prior_resumed_wrapper_path='scripts/round110_resumed_campaign.py',prior_resumed_wrapper_SHA=sha(ROOT/'scripts/round110_resumed_campaign.py'),
        scoped_evidence_path='scripts/round110_scoped_evidence.py',scoped_evidence_SHA=sha(ROOT/'scripts/round110_scoped_evidence.py'),
        current_primary_entry_path='scripts/round110_scoped_reader.py',current_primary_entry_SHA=sha(ROOT/'scripts/round110_scoped_reader.py'),
        scoped_readback_path='results/unified_exact_round110/campaign/reader_recovery/scoped25_readback03/readback.json',
        scoped_readback_execution_path='results/unified_exact_round110/engineering/scoped25_readback03',
        scoped_runtime_gate_path='results/unified_exact_round110/campaign/reader_recovery/scoped25_runtime_gate01/runtime_gate.json',
        scoped_runtime_gate_execution_path='results/unified_exact_round110/engineering/scoped25_runtime_gate01',
        full_scoped_arithmetic_kept_in_offline_reader=True,runtime_scoped_gate_rehashes_all_signed_proof_bytes=True,
        performance_runner_SHA=sha(ROOT/'scripts/round110_campaign.py'),performance_helpers=frozen.helpers(),
        completed_native_numbers=[v['number'] for v in rows],next_native_number=26,never_started_numbers=[v['number'] for v in ident['launches'][25:]],
        budget=b,remaining_fixed_reserve=reserve,explicit_qualified_offline_endpoints={str(k):v for k,v in cache.items()},
        raw_false_audit_and_endpoint_preserved=True,no_native_supervisor_or_audit_change=True,
        direct_wrapper_processes=1,new_main09_tail_fee_starts=3,failed_main09_four_starts_remain_paid=True,
        first_arm_whole_clock_includes_resumed_projection_admission=True,no_online_UB_Start_cut_cache_transfer=True,
        superseded_request_paths=['results/unified_exact_round110/campaign/reader_recovery/continue25_01/request.json',
            'results/unified_exact_round110/campaign/reader_recovery/continue25_02/request.json',
            'results/unified_exact_round110/campaign/reader_recovery/continue25_03/request.json'],
        superseded_reason='before any native continuation, correct actual failure/dependent-cover labels and keep the measured70–73 second exact arithmetic offline; cheap signed-byte gate preserves frozen cap and first admission tick',
        no_solver_rerun=True,Optimize=0,native_environment=0))
    print(json.dumps(dict(request=RESUME_REQUEST.relative_to(ROOT).as_posix(),budget=b,reserve=reserve)),flush=True)


def billed(name,first,last,label):
    admission_tick=time.perf_counter()
    from round100_idle import ensure_idle
    ensure_idle();check_identity();request=read(RESUME_REQUEST);audit=read(RESUME_AUDIT)
    assert audit['decision']=='ACCEPT_NEXT_ONLY_SAME_PE_RESUMPTION' and audit['request_SHA']==sha(RESUME_REQUEST)
    assert request['resumed_wrapper_SHA']==sha(__file__) and request['prior_resumed_wrapper_SHA']==sha(ROOT/request['prior_resumed_wrapper_path'])
    assert request['scoped_evidence_SHA']==sha(ROOT/request['scoped_evidence_path'])
    assert name=='campaign' and request['next_native_number']<=first<=last<=42
    cache,meta=qualified_cache();assert meta==request['projection_bindings']
    source=derived_billed_source();assert source==(ROOT/request['derived_billed_path']).read_text(encoding='utf-8')
    if first==26:assert sha(OUT/'campaign/summary.jsonl')==request['original_summary_SHA']
    frozen.records=lambda camp:prior.projected_records(camp,cache)
    namespace=dict(vars(frozen));namespace.update(_resume_source=Path(__file__),_derived_source=source,
        _scoped_source=ROOT/request['scoped_evidence_path'],_prior_source=ROOT/request['prior_resumed_wrapper_path'],
        _resumed_admission_tick=admission_tick,_projection_meta=dict(request_path=RESUME_REQUEST.relative_to(ROOT).as_posix(),request_SHA=sha(RESUME_REQUEST),
            independent_resumption_audit_path=RESUME_AUDIT.relative_to(ROOT).as_posix(),independent_resumption_audit_SHA=sha(RESUME_AUDIT),
            wrapper_SHA=sha(__file__),derived_billed_SHA=request['derived_billed_SHA'],projection_bindings=meta,
            scoped_evidence_SHA=request['scoped_evidence_SHA'],prior_resumed_wrapper_SHA=request['prior_resumed_wrapper_SHA'],
            rawsummary_read_only=True,no_online_transfer=True,first_whole_clock_includes_resumed_projection_admission=True))
    exec(compile(source,str(__file__)+'::derived_frozen_billed','exec'),namespace)
    namespace['billed'](name,first,last,label,False)


if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare(*sys.argv[2:])
    elif sys.argv[1]=='billed':billed(sys.argv[2],int(sys.argv[3]),int(sys.argv[4]),sys.argv[5])
    else:raise ValueError(sys.argv[1])
