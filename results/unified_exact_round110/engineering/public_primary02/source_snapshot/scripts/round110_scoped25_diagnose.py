"""Actual scoped-call pause facts; no recovery or native work."""
from round110_common import *
import round108_reader as core
from collections import Counter

if __name__=='__main__':
    from round100_idle import ensure_idle
    ensure_idle();production=check_identity();ident=read(OUT/'campaign/identity.json');launch=ident['launches'][24]
    d=Path(launch['destination']);r=read(d/'result.json');c=read(d/'completion.json');obs=read(d/'observations.json')
    assert c['returncode']==0 and c['stop_reason']=='normal_return' and c['within_cap']
    physical=core.full_fleet(ROOT,launch['panel'],r)
    events=[]
    for v in obs:
        e=v['payload'];q={k:x for k,x in e.items() if k!='routes'}
        q['available']=v['effective_available_seconds'];events.append(q)
    paths=[p for p in d.rglob('*') if p.is_file()]
    paths += [OUT/'fees/main09/launch.json',OUT/'fees/main09/receipt.json',OUT/'fees/main09/failure.txt',
        OUT/'campaign/identity.json',OUT/'candidate_identity.json',OUT/'production_identity.json',OUT/'evidence_policy.json',
        ROOT/'scripts/round110_scoped25_diagnose.py']
    out=OUT/'campaign/reader_recovery/scoped25_facts01';out.mkdir(parents=True,exist_ok=False)
    write(out/'facts.json',dict(key=[25,launch['id'],launch['seed'],launch['arm']],
        actual_events=events,physical=physical,normal_completion=c,
        recorded_kind_counts=dict(Counter(e['payload']['kind'] for e in obs)),
        bound_files={p.relative_to(ROOT).as_posix():sha(p) for p in paths},budget=budget(),
        recovery_applied=False,decision='HOLD_PENDING_CURRENT_SCOPED_MODEL_PROOF',Optimize=0,native_environment=0))
    print(json.dumps(dict(physical_U=physical['F'],events=events,budget=budget()),allow_nan=False))
