"""Finite serial paid native qualification; no formal-arm evidence handoff."""
from round106_common import *
import csv

def historical(role):
    root=Path('E:/r106-recovery/r105-02')
    mode=read(root/f'results/unified_exact_round105/modes/{role}_01/manifest.json')['modes'][0]
    candidate=root/mode['source'];folder=candidate.parent
    return ROOT/mode['panel']['input_path'],candidate,folder/'master_1.lp',folder/'start.mst',mode

def run():
    dest=OUT/'qualification/replay01';dest.mkdir(parents=True,exist_ok=False)
    c2=historical('C2');f2=historical('F2');jobs=[]
    jobs.append(dict(label='inherited_native',cap=300,command=[BUILD/'Round105Tests.exe','native',dest/'inherited_native']))
    for label,h,cap,strategy in [('C2_A',c2,30,'struct'),('F2_B',f2,30,'struct'),('inner_deadline',c2,12,'core')]:
        inp,x,model,start,m=h;p=m['panel'];d=dest/label
        jobs.append(dict(label=label,cap=cap+10,command=[BUILD/'Round106Research.exe','replay',inp,p['T_seconds'],p['pickup_seconds'],p['drop_seconds'],p['lambda'],d,cap,strategy,model,x,start]))
    inp,x,model,start,m=c2;p=m['panel']
    jobs.append(dict(label='C2_contracts',cap=30,command=[BUILD/'Round106Research.exe','contracts',inp,p['T_seconds'],p['pickup_seconds'],p['drop_seconds'],p['lambda'],dest/'C2_contracts',20,model,x,start,start]))
    assert len(jobs)==5
    write(dest/'plan.json',dict(jobs=[dict(j,command=list(map(str,j['command']))) for j in jobs],
        declared_children=5,production_binary_sha256=sha(BUILD/'ExactEBRP.exe'),research_binary_sha256=sha(BUILD/'Round106Research.exe'),
        inherited_test_binary_sha256=sha(BUILD/'Round105Tests.exe'),DLL_sha256=sha(DLL),source_bindings=bindings(),
        layer='offline retained-model native replay and scripted audited-vector contracts',production_handoff=False))
    for n,j in enumerate(jobs,1):
        command=list(map(str,j['command']));write(dest/f'{n:02d}_before.json',dict(command=command,started_unix=time.time(),
            input_file_SHA={str(p):sha(p) for p in map(Path,command) if p.is_file()}))
        tick=time.perf_counter()
        with (dest/f'{n:02d}_stdout.log').open('x') as so,(dest/f'{n:02d}_stderr.log').open('x') as se:
            ret=subprocess.run(command,cwd=ROOT,env=env(),stdout=so,stderr=se,timeout=j['cap'])
        write(dest/f'{n:02d}_after.json',dict(exit_code=ret.returncode,outer_seconds=time.perf_counter()-tick))
        assert ret.returncode==0,(j['label'],(dest/f'{n:02d}_stderr.log').read_text())
    deadline=read(dest/'inner_deadline/round106/summary.json')
    assert deadline['master_calls']==1 and deadline['iis_calls']+deadline['oracle_calls']>0
    assert deadline['inner_cancelled'] and deadline['outer_cancelled'] and not deadline['certified'],deadline
    for label,family in [('C2_A','A_MST'),('F2_B','B_')]:
        d=dest/label/'round106';events=[json.loads(s) for s in (d/'events.jsonl').read_text().splitlines()]
        assert any(e['submitted_lazy_rows'] for e in events)
        cuts=list(csv.DictReader((d/'lazy.csv').open(newline='')))
        assert any(c['family'].startswith(family) and int(c['api_return'])==0 for c in cuts)
    write(dest/'qualification.json',dict(passed=True,actual_callback_inner_deadline=True,
        C2_A_native_submitted=True,F2_B_native_submitted=True,production_handoff=False))
    print(json.dumps(dict(passed=True,children=5)))

if __name__=='__main__':run()
