"""Exact-dyadic row/mapping/support replay and physical-witness checks.
This is execution-team validation. No native Optimize, never during performance.
"""
import sys,json,hashlib,time
from pathlib import Path
from fractions import Fraction as F
from round102_common import *
from round102_support import support,exact
from round101_verify_certificates import replay_contract
from round100_idle import ensure_idle
import analyze_round61 as physical

def main(label,campaigns):
    ensure_idle();physical.ROOT=ROOT;tick=time.perf_counter()
    seen=set();certs=[];witnesses={};checks=0
    for name in campaigns:
        q=read(OUT/name/'identity.json');done=[json.loads(x) for x in (OUT/name/'summary.jsonl').read_text().splitlines()]
        assert len(done)==len(q['launches']) and all(x['audit_passed'] for x in done)
        for launch in q['launches']:
            panel=launch['panel'];folder=Path(launch['destination']);h=panel['input_sha256']
            def retain(w):
                checked=physical.physical(panel,w);assert checked['original_T_feasible']
                signature=tuple((route['vehicle'],tuple((op['station'],op['pickup'],op['drop']) if isinstance(op,dict) else tuple(op) for op in route['operations'])) for route in w['routes'])
                witnesses.setdefault(h,{})[signature]=w['routes']
            for obs in read(folder/'observations.json'):
                if obs['payload']['kind']=='witness':retain(obs['payload'])
            if (folder/'result.json').exists():
                r=read(folder/'result.json')
                if r.get('routes'):retain(dict(routes=r['routes'],F=r['upper_bound']))
            for file in sorted((folder/'external/native_logs').glob('*.round102.certificates.jsonl')):
                binding=read(Path(str(file).replace('.certificates.jsonl','.contract.json')))
                assert binding['input_sha256']==h
                contract=binding['column_contract'];c=contract['resource'];replay_contract(c)
                for line in file.read_text().splitlines():
                    row=json.loads(line);expected={};rhs=F(0)
                    for p in row['proofs']:
                        key=hashlib.sha256(json.dumps([c,p],sort_keys=True).encode()).hexdigest()
                        if key not in seen:
                            replay=support(c,p['vehicle'],p['weights'])
                            # Exact dyadic resource comparisons can be tighter
                            # than C++ downward arithmetic: only <= is required.
                            assert replay['upper']<=p['upper'],(file,p['upper'],replay['upper'])
                            seen.add(key)
                        rhs+=F(p['upper'],1024)
                        for i,w in enumerate(p['weights'][1:],1):
                            for j,a in zip(contract['service_columns'][p['vehicle']][i],w):
                                if a:assert j not in expected;expected[j]=F(a,1024)
                    assert exact(row['rhs'])>=rhs
                    assert len(row['columns'])==len(expected)
                    assert {j:exact(a) for j,a,v in row['columns']}==expected
                    act=sum((exact(a)*exact(v) for j,a,v in row['columns']),F(0))
                    assert exact(row['activity_lower'])<=act
                    assert 0<exact(row['violation_lower'])<=act-exact(row['rhs'])
                    assert row['node']==0 and row['api_code'] in [-1,0]
                    certs.append((h,row,c,file))
    for h,row,c,file in certs:
        for routes in witnesses[h].values():
            operations={r['vehicle']:{(op['station'] if isinstance(op,dict) else op[0]):((op['pickup'],op['drop']) if isinstance(op,dict) else (op[1],op[2])) for op in r['operations']} for r in routes}
            activity=0
            for p in row['proofs']:
                ops=operations.get(p['vehicle'],{})
                for i,(a,b,g) in enumerate(p['weights'][1:],1):
                    pickup,drop=ops.get(i,(0,0));activity+=a*pickup+b*drop+g*bool(pickup or drop)
            assert F(activity,1024)<=exact(row['rhs']),(file,activity,row['rhs'])
            checks+=1
    records=[]
    for file in sorted({x[3] for x in certs}):
        r=[x[1] for x in certs if x[3]==file]
        records.append(dict(path=file.relative_to(ROOT).as_posix(),sha256=sha(file),rows=len(r),API0=sum(x['api_code']==0 for x in r)))
    write(OUT/'diagnostics'/label/'summary.json',dict(passed=True,Optimize=0,certificates=len(certs),distinct_supports=len(seen),
        physical_row_witness_checks=checks,unique_physical_witnesses={h:len(w) for h,w in witnesses.items()},records=records,
        seconds=time.perf_counter()-tick,script_sha256=sha(__file__),scope='Actual signed dyadic rows, global lower-contract containment, complete integer support upper replay, original physical routes; no independent native search or later full vector reconstruction'))
    print(json.dumps(dict(passed=True,certificates=len(certs),checks=checks,Optimize=0)))

if __name__=='__main__':main(sys.argv[1],sys.argv[2:])
