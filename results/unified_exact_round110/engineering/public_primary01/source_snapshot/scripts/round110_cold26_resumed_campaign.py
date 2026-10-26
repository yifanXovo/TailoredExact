"""Next-only same-PE wrapper after signed current P26 adjudication.

Signed byte gates keep the large exact matrix arithmetic offline. The first
arm clock includes all cache admission. Frozen native supervisor is reused.
"""
from round110_common import *
import round110_campaign as frozen
import round110_resumed_campaign as prior
import round110_scoped_resumed_campaign as scoped_prior
import round110_scoped_evidence as evidence
import round110_cold_runtime as cold_runtime

RESUME_REQUEST=OUT/'campaign/reader_recovery/continue26_01/request.json'
RESUME_AUDIT=OUT/'review/continue26_01/audit.json'


def qualified_cache():
    ident=read(OUT/'campaign/identity.json');cache={};meta={}
    for number in [15,17,25,26]:
        launch=ident['launches'][number-1];side=ROOT/evidence.side_path(launch);d=Path(launch['destination'])
        proof=(evidence.verify_signed_scope_binding(ROOT,launch,d) if number==25 else
            cold_runtime.verify_signed_cold_binding(ROOT,launch,d) if number==26 else evidence.verify_rejection(ROOT,launch,d))
        cache[number]=dict(U=proof['own_U'],L=proof['qualified_L'],gap=proof['own_U'],certificate=proof['certificate_from_own_exact_zero'],
            source='separately_signed_own_physical_endpoint_and_own_full_domain_floor',status=read(d/'result.json')['status'])
        meta[str(number)]=dict(side_path=side.relative_to(ROOT).as_posix(),side_SHA=sha(side),
            independent_audit_path=proof['independent_audit_path'],independent_audit_SHA=proof['independent_audit_SHA'])
    assert {v['number'] for v in ident['launches'] if evidence.has_rejection(ROOT,v)}==set(cache)
    return cache,meta


def derived_billed_source():
    source=scoped_prior.derived_billed_source()
    old="    (d/'source_snapshot/scripts/round110_scoped_resumed_campaign.py').write_bytes(_resume_source.read_bytes())"
    new="    (d/'source_snapshot/scripts/round110_cold26_resumed_campaign.py').write_bytes(_resume_source.read_bytes())\n    (d/'source_snapshot/scripts/round110_cold_runtime.py').write_bytes(_cold_source.read_bytes())\n    (d/'source_snapshot/scripts/round110_scoped_resumed_campaign.py').write_bytes(_scoped_prior_source.read_bytes())"
    assert source.count(old)==1;return source.replace(old,new)


def prepare(proposal_path,audit_path):
    from round100_idle import ensure_idle
    ensure_idle();production=check_identity();b=budget();assert not b['unclosed']
    proposal=read(ROOT/proposal_path);audit=read(ROOT/audit_path)
    assert proposal['key']==[26,'G100-C1',0,'P-GRB'] and audit['decision']=='ACCEPT_CURRENT_CALL_REJECTION'
    assert audit['current_key']==proposal['key']
    ident=read(OUT/'campaign/identity.json');launch=ident['launches'][25];side=ROOT/evidence.side_path(launch)
    activated=dict(proposal,independent_audit_path=audit_path,independent_audit_SHA=sha(ROOT/audit_path))
    if side.exists():assert read(side)==activated
    else:write(side,activated)
    cache,meta=qualified_cache();rows=prior.projected_records(OUT/'campaign',cache)
    assert len(rows)==26 and all(v.get('qualified_offline_audit_passed',v['audit_passed']) for v in rows)
    assert all(not Path(v['destination']).exists() for v in ident['launches'][26:])
    reserve=frozen.full_remaining_reserve();assert reserve==dict(starts=23,nominal_seconds=48600,overhead_seconds=840)
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
        scoped_resumed_wrapper_path='scripts/round110_scoped_resumed_campaign.py',scoped_resumed_wrapper_SHA=sha(ROOT/'scripts/round110_scoped_resumed_campaign.py'),
        scoped_evidence_path='scripts/round110_scoped_evidence.py',scoped_evidence_SHA=sha(ROOT/'scripts/round110_scoped_evidence.py'),
        cold_runtime_path='scripts/round110_cold_runtime.py',cold_runtime_SHA=sha(ROOT/'scripts/round110_cold_runtime.py'),
        current_primary_entry_path='scripts/round110_scoped_reader.py',current_primary_entry_SHA=sha(ROOT/'scripts/round110_scoped_reader.py'),
        cold_readback_path='results/unified_exact_round110/campaign/reader_recovery/cold26_readback01/readback.json',
        cold_readback_execution_path='results/unified_exact_round110/engineering/cold26_readback01',
        cold_runtime_gate_path='results/unified_exact_round110/campaign/reader_recovery/cold26_runtime_gate01/runtime_gate.json',
        cold_runtime_gate_execution_path='results/unified_exact_round110/engineering/cold26_runtime_gate01',
        full_matrix_arithmetic_kept_in_offline_reader=True,runtime_gate_rehashes_all_signed_proof_bytes=True,
        performance_runner_SHA=sha(ROOT/'scripts/round110_campaign.py'),performance_helpers=frozen.helpers(),
        completed_native_numbers=[v['number'] for v in rows],next_native_number=27,never_started_numbers=[v['number'] for v in ident['launches'][26:]],
        budget=b,remaining_fixed_reserve=reserve,explicit_qualified_offline_endpoints={str(k):v for k,v in cache.items()},
        raw_audit_flags_and_endpoint_preserved=True,no_native_supervisor_or_audit_change=True,
        direct_wrapper_processes=1,new_main09_tail02_fee_starts=2,failed_main09_four_starts_remain_paid=True,failed_main09_tail01_three_starts_remain_paid=True,
        first_arm_whole_clock_includes_resumed_projection_admission=True,no_online_UB_Start_cut_cache_transfer=True,
        superseded_request_paths=['results/unified_exact_round110/campaign/reader_recovery/continue25_04/request.json'],
        superseded_reason='actual normal-return P26 cross-arm native lower contradiction; signed current cold proof is now required before never-started27',
        no_solver_rerun=True,Optimize=0,native_environment=0))
    print(json.dumps(dict(request=RESUME_REQUEST.relative_to(ROOT).as_posix(),budget=b,reserve=reserve)),flush=True)


def billed(name,first,last,label):
    admission_tick=time.perf_counter()
    from round100_idle import ensure_idle
    ensure_idle();check_identity();request=read(RESUME_REQUEST);audit=read(RESUME_AUDIT)
    assert audit['decision']=='ACCEPT_NEXT_ONLY_SAME_PE_RESUMPTION' and audit['request_SHA']==sha(RESUME_REQUEST)
    assert request['resumed_wrapper_SHA']==sha(__file__)
    for stem in ['prior_resumed_wrapper','scoped_resumed_wrapper','scoped_evidence','cold_runtime','current_primary_entry']:
        assert request[stem+'_SHA']==sha(ROOT/request[stem+'_path'])
    assert name=='campaign' and request['next_native_number']<=first<=last<=42
    cache,meta=qualified_cache();assert meta==request['projection_bindings']
    source=derived_billed_source();assert source==(ROOT/request['derived_billed_path']).read_text(encoding='utf-8')
    if first==27:assert sha(OUT/'campaign/summary.jsonl')==request['original_summary_SHA']
    frozen.records=lambda camp:prior.projected_records(camp,cache)
    namespace=dict(vars(frozen));namespace.update(_resume_source=Path(__file__),_derived_source=source,
        _scoped_source=ROOT/request['scoped_evidence_path'],_prior_source=ROOT/request['prior_resumed_wrapper_path'],
        _cold_source=ROOT/request['cold_runtime_path'],_scoped_prior_source=ROOT/request['scoped_resumed_wrapper_path'],
        _resumed_admission_tick=admission_tick,_projection_meta=dict(request_path=RESUME_REQUEST.relative_to(ROOT).as_posix(),request_SHA=sha(RESUME_REQUEST),
            independent_resumption_audit_path=RESUME_AUDIT.relative_to(ROOT).as_posix(),independent_resumption_audit_SHA=sha(RESUME_AUDIT),
            wrapper_SHA=sha(__file__),derived_billed_SHA=request['derived_billed_SHA'],projection_bindings=meta,
            scoped_evidence_SHA=request['scoped_evidence_SHA'],cold_runtime_SHA=request['cold_runtime_SHA'],
            prior_resumed_wrapper_SHA=request['prior_resumed_wrapper_SHA'],scoped_resumed_wrapper_SHA=request['scoped_resumed_wrapper_SHA'],
            rawsummary_read_only=True,no_online_transfer=True,first_whole_clock_includes_resumed_projection_admission=True))
    exec(compile(source,str(__file__)+'::derived_frozen_billed','exec'),namespace)
    namespace['billed'](name,first,last,label,False)


if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare(*sys.argv[2:])
    elif sys.argv[1]=='billed':billed(sys.argv[2],int(sys.argv[3]),int(sys.argv[4]),sys.argv[5])
    else:raise ValueError(sys.argv[1])
