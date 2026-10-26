"""Exercise the actual offline current-call projection after signed rejection."""
from round110_common import *
import round110_evidence as evidence
import round108_reader as core

if __name__=='__main__':
    number=int(sys.argv[1]);label=sys.argv[2]
    ident=read(OUT/'campaign/identity.json');launch=ident['launches'][number-1];d=Path(launch['destination'])
    proof=evidence.verify_rejection(ROOT,launch,d)
    journal=evidence.journal(ROOT,launch,d)
    endpoint=evidence.endpoint(ROOT,launch,ident,d,journal,True,None)
    assert endpoint['arm']['U']==proof['own_U'] and endpoint['arm']['L']==0.
    assert endpoint['arm']['certificate']==proof['certificate_from_own_exact_zero']
    assert endpoint['arm']['complete_seconds'] is None
    assert endpoint['arm']['complete_seconds_interval']==proof['time']['interval']
    assert all(v['L']==0. for v in journal['trace'])
    assert all(v['native_bound_mathematically_qualified'] is False for v in endpoint['rejected_raw_native_chronology'])
    assert core.sha(d/'audit.json')==proof['raw_bindings'][(d/'audit.json').relative_to(ROOT).as_posix()]
    out=OUT/'campaign/reader_recovery'/label;out.mkdir(parents=True,exist_ok=False)
    write(out/'readback.json',dict(arm=endpoint['arm'],rejected_claims=len(endpoint['rejected_raw_native_chronology']),
        journal_started=journal['started'],journal_returned=journal['returned'],
        native_raw_flags_preserved=True,Optimize=0,native_environment=0,
        reader_SHA=sha(ROOT/'scripts/round110_reader.py'),evidence_SHA=sha(ROOT/'scripts/round110_evidence.py')))
    print(json.dumps(read(out/'readback.json')))
