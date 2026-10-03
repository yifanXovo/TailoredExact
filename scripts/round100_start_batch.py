"""Exactly the completed development's nine non-P scopes, no Optimize."""
from round100_common import *
from round100_idle import ensure_idle
if __name__=='__main__':
    ensure_idle()
    from round100_start_audit import run
    q=read(OUT/'development01/identity.json')
    done=[json.loads(s) for s in (OUT/'development01/summary.jsonl').read_text().splitlines()]
    assert len(done)==12 and all(r['audit_passed'] for r in done)
    scopes=[a for a in q['launches'] if a['arm']!='P-GRB'];assert len(scopes)==9
    for a in scopes:run(a['destination'],f'dev_start_{a["number"]:02d}',{'ENS-C':'off','ENS-Q':'ens-q','M-B':'m-binary'}[a['arm']])
    print('finite model scopes=9, Optimize=0')
