"""Bounded actual scoped25 reader execution; no performance rebuild or solver."""
from round110_common import *
import round110_scoped_evidence as evidence
import round108_reader as core

if __name__=='__main__':
    if sys.argv[1]=='runtime-only':
        import round110_scoped_resumed_campaign as resumed
        label=sys.argv[2];tick=time.perf_counter();cache,meta=resumed.qualified_cache();elapsed=time.perf_counter()-tick
        assert set(cache)=={15,17,25} and cache[25]['U']==cache[25]['L']==0. and cache[25]['certificate']
        assert elapsed<15.,'actual admission cost does not fit a conservative within-cap reserve'
        out=OUT/'campaign/reader_recovery'/label;out.mkdir(parents=True,exist_ok=False)
        write(out/'runtime_gate.json',dict(cache=cache,projection_bindings=meta,actual_cache_admission_seconds=elapsed,
            scoped_gate='all signed current raw/model/vector bytes rehashed; no scoped matrix arithmetic',
            full_scoped_arithmetic_remains_offline=True,wrapper_SHA=sha(ROOT/'scripts/round110_scoped_resumed_campaign.py'),
            scoped_evidence_SHA=sha(ROOT/'scripts/round110_scoped_evidence.py'),Optimize=0,native_environment=0))
        print(json.dumps(dict(actual_cache_admission_seconds=elapsed,Optimize=0,native_environment=0)),flush=True);sys.exit(0)
    label=sys.argv[1];ident=read(OUT/'campaign/identity.json');launch=ident['launches'][24];d=Path(launch['destination'])
    proof=evidence.verify_rejection(ROOT,launch,d);j=evidence.journal(ROOT,launch,d)
    ep=evidence.endpoint(ROOT,launch,ident,d,j,True,None);arm=ep['arm']
    assert arm['U']==arm['L']==arm['gap']==0. and arm['certificate'] and arm['raw_audit_passed'] is False
    assert arm['complete_seconds'] is None and arm['complete_seconds_interval']==proof['time']['interval']
    assert j['started']==4 and j['returned']==3 and j['returned_ids']=={1,2,3} and j['calls'][4]['returned_journal_missing']
    assert [q['call'] for q in ep['cover']['scoped_proofs']]==[1,2,3]
    assert all(q['call']==4 and q['native_bound_mathematically_qualified'] is False for q in ep['rejected_raw_native_chronology'])
    assert ep['cover']['native_call4_closure_withdrawn'] and all(q['L']==0. for q in j['trace'])
    seen=False
    for row in ep['cover']['timeline']:
        seen=seen or row['event_type'].startswith('native_') or 'terminal_mip' in row['event_source']
        if seen:assert row['raw_native_claim_mathematically_qualified'] is False and row['necessary_dependent_native_closure_withdrawn']
    assert sha(d/'audit.json')==proof['raw_bindings'][(d/'audit.json').relative_to(ROOT).as_posix()]
    out=OUT/'campaign/reader_recovery'/label;out.mkdir(parents=True,exist_ok=False)
    write(out/'readback.json',dict(arm=arm,journal_started=j['started'],journal_returned=j['returned'],
        preserved_LP_proofs=ep['cover']['scoped_proofs'],rejected_claims=ep['rejected_raw_native_chronology'],
        current_raw_cover=ep['cover'],chronological_cover=ep['chronological_cover'],
        independently_proved_actual_native_returns_without_journal=j['independently_proved_actual_native_returns'],
        native_raw_flags_preserved=True,Optimize=0,native_environment=0,
        primary_entry_SHA=sha(ROOT/'scripts/round110_scoped_reader.py'),scoped_evidence_SHA=sha(ROOT/'scripts/round110_scoped_evidence.py')))
    print(json.dumps(dict(arm=arm,preserved_LP_calls=[1,2,3],rejected_call=4,actual_Optimize=4,Optimize=0,native_environment=0)),flush=True)
    if len(sys.argv)>2:
        assert sys.argv[2]=='--prepare'
        import round110_scoped_resumed_campaign as resumed
        resumed.prepare(*sys.argv[3:])
