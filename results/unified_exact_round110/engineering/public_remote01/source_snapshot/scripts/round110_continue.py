"""Offline activation and next-only resumption request; never launches native work."""
from round110_common import *
import round110_campaign as campaign
import round110_evidence as evidence


def prepare(label, proposal_path, audit_path):
    from round100_idle import ensure_idle
    ensure_idle();production=check_identity();b=budget()
    assert not b['unclosed']
    proposal_path=ROOT/proposal_path;audit_path=ROOT/audit_path
    proposal=read(proposal_path);audit=read(audit_path)
    assert audit['decision']=='ACCEPT_CURRENT_CALL_REJECTION'
    assert audit['current_key']==proposal['key']
    ident=read(OUT/'campaign/identity.json');number=proposal['key'][0]
    launch=ident['launches'][number-1]
    side=ROOT/evidence.side_path(launch)
    write(side,dict(proposal,independent_audit_path=audit_path.relative_to(ROOT).as_posix(),independent_audit_SHA=sha(audit_path)))
    evidence.verify_rejection(ROOT,launch,Path(launch['destination']))
    records=campaign.records(OUT/'campaign')
    assert len(records)==number and all(r['audit_passed'] for r in records)
    assert all(not Path(v['destination']).exists() for v in ident['launches'][number:])
    reserve=campaign.full_remaining_reserve()
    assert b['remaining_starts']>=reserve['starts']
    assert b['remaining_outer_seconds']>=reserve['nominal_seconds']+reserve['overhead_seconds']
    d=OUT/'campaign/reader_recovery'/label;d.mkdir(parents=True,exist_ok=False)
    write(d/'request.json',dict(schema='round110-next-only-same-pe-resumption-v1',
        production_PE_SHA=production['production_PE_SHA'],DLL_SHA=DLL_SHA,
        campaign_identity_SHA=sha(OUT/'campaign/identity.json'),candidate_identity_SHA=sha(OUT/'candidate_identity.json'),
        current_rejection_path=side.relative_to(ROOT).as_posix(),current_rejection_SHA=sha(side),
        independent_audit_path=audit_path.relative_to(ROOT).as_posix(),independent_audit_SHA=sha(audit_path),
        original_summary_SHA=sha(OUT/'campaign/summary.jsonl'),original_summary_unchanged=True,
        performance_runner_SHA=sha(ROOT/'scripts/round110_campaign.py'),performance_helpers=campaign.helpers(),
        qualified_evidence_module_SHA=sha(ROOT/'scripts/round110_evidence.py'),qualified_reader_SHA=sha(ROOT/'scripts/round110_reader.py'),
        completed_native_numbers=[v['number'] for v in records],next_native_number=number+1,
        never_started_numbers=[v['number'] for v in ident['launches'][number:]],
        budget=b,remaining_fixed_reserve=reserve,
        no_online_UB_Start_cut_cache_transfer=True,no_raw_flag_or_clock_rewrite=True,
        no_performance_helper_change=True,no_solver_rerun=True,Optimize=0,native_environment=0))
    print(json.dumps(dict(request=(d/'request.json').relative_to(ROOT).as_posix(),budget=b,reserve=reserve)))


if __name__=='__main__':prepare(*sys.argv[1:])
