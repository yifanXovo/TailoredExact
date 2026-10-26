"""Same saved raw-point separator replay, zero Optimize, exclusive output."""
import sys,shutil
from round101_common import *
if __name__=='__main__':
    d=OUT/'diagnostics'/sys.argv[1];d.mkdir(parents=True,exist_ok=False);records=[]
    roles={p['id']:p for p in read(OUT/'development_inputs.json')['roles']}
    for old in read(OUT/'diagnostics/lp01/summary.json')['records']:
        id=old['role'];p=roles[id];source=OUT/'diagnostics/lp01'/id;target=d/(id+'.json')
        cmd=[BUILD/'Round101FleetDiagnostic.exe',ROOT/p['input_path'],p['T_seconds'],p['pickup_seconds'],p['drop_seconds'],source/'matrix.txt',source/'raw.point',target]
        tick=time.perf_counter();ret=subprocess.run(list(map(str,cmd)),cwd=ROOT,env=env(),capture_output=True,text=True,timeout=120);seconds=time.perf_counter()-tick
        assert ret.returncode==0,(ret.stdout,ret.stderr);new=read(target);prior=read(source/'raw.separation.json')
        def rows(v):return [(r['proof']['events'],r['proof']['rank'],r['columns'],r['activity_lower'],r['violation_lower']) for r in v['rows']]
        assert rows(prior)==rows(new),'mathematical output changed in cost-only revision'
        records.append(dict(role=id,old_seconds=old['raw_separator_seconds'],new_seconds=seconds,selected_rows_equal=True,candidates=new['candidates'],proofs=new['proofs']))
    write(d/'summary.json',dict(passed=True,optimizer_calls=0,records=records,source_hashes=bindings(),binary_sha256=sha(BUILD/'Round101FleetDiagnostic.exe')))
    print(json.dumps(records))
