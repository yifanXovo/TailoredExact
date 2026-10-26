from round102_common import *
from round100_idle import ensure_idle
import sys
if __name__=='__main__':
    ensure_idle();d=OUT/'diagnostics'/sys.argv[1];d.mkdir(parents=True,exist_ok=False);records=[]
    for p in read(OUT/'development_inputs.json')['roles']:
        role=p['id'];old=ROOT/'results/unified_exact_round101/diagnostics/lp01'/role
        result=d/(role+'.json');cmd=[BUILD/'Round102ServiceDiagnostic.exe',ROOT/p['input_path'],p['T_seconds'],60,60,old/'matrix.txt',old/'raw.point',result]
        tick=time.perf_counter();r=subprocess.run(list(map(str,cmd)),cwd=ROOT,env=env(),capture_output=True,text=True,timeout=60)
        assert r.returncode==0,(r.stdout,r.stderr);q=read(result)
        records.append(dict(role=role,outer_seconds=time.perf_counter()-tick,dp_seconds=q['seconds'],rows=len(q['rows']),
            reliable_violations=[r['violation_lower'] for r in q['rows']],proof_values=[[p['upper'] for p in r['proofs']] for r in q['rows']]))
    write(d/'summary.json',dict(records=records,Optimize_calls=0,binary_sha256=sha(BUILD/'Round102ServiceDiagnostic.exe'),source_hashes=bindings()))
    print(json.dumps(records))
