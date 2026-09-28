"""Six frozen historical snapshots; old closure then order closure, 120 s each."""
import ctypes as ct
import os
import subprocess
import time
from round96_prepare import ROOT, OUT, read, write, sha, evidence

BIN=ROOT/'build/research/round96-multi-quantity/Round96RouteOrderDiagnostic.exe'

def main():
    started=time.perf_counter();cases=read(OUT/'fixed_route_cases.json')['cases']
    gate=read(OUT/'route_order_build_gate.json')
    assert gate['qualified'] and gate['binary_sha256']==sha(BIN)
    for path,value in gate['source_hashes'].items():assert sha(ROOT/path)==value
    batch=OUT/'route_order';batch.mkdir(exist_ok=False)
    env=dict(os.environ);env['PATH']='D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;'+env.get('PATH','')
    kernel=ct.WinDLL('kernel32',use_last_error=True);kernel.GetCurrentProcess.restype=ct.c_void_p
    kernel.SetProcessAffinityMask.argtypes=[ct.c_void_p,ct.c_size_t]
    assert kernel.SetProcessAffinityMask(kernel.GetCurrentProcess(),4)
    write(batch/'plan.json',dict(cases=[c['id'] for c in cases],processes=6,library_tasks_per_case=2,
        cap_per_process=120,maximum_seconds=720,optimizer_calls=0,binary_sha256=sha(BIN),runner_sha256=sha(__file__)))
    records=[]
    for case in cases:
        p=case['panel'];w=read(ROOT/case['witness_path'])
        assert sha(ROOT/case['witness_path'])==case['witness_sha256']
        routepath=OUT/'multi_quantity'/(case['id']+'.routes.txt')
        oldlaunch=read(OUT/'multi_quantity'/(case['id']+'.launch.json'))
        oldsummary=read(OUT/'multi_quantity'/case['id']/'summary.json')
        assert sha(routepath)==oldsummary['route_sha256']
        dest=batch/case['id'];command=list(map(str,[BIN,ROOT/p['instance_path'],routepath,p['T_seconds'],
            p['pickup_seconds'],p['drop_seconds'],p['lambda'],dest]))
        write(batch/(case['id']+'.launch.json'),dict(command=command,cap_seconds=120,optimizer_calls=0))
        tick=time.perf_counter()
        with (batch/(case['id']+'.stdout.log')).open('x') as so,(batch/(case['id']+'.stderr.log')).open('x') as se:
            try:
                ret=subprocess.run(command,cwd=ROOT,env=env,stdout=so,stderr=se,timeout=120)
                code=ret.returncode;reason='normal_return'
            except subprocess.TimeoutExpired:code=None;reason='diagnostic_timeout'
        receipt=dict(id=case['id'],exit_code=code,stop_reason=reason,wall_seconds=time.perf_counter()-tick,optimizer_calls=0)
        write(batch/(case['id']+'.completion.json'),receipt)
        assert code==0,'preserve failed paid prefix; no rerun'
        result=read(dest/'summary.json')
        assert result['input_sha256']==p['input_sha256'] and result['route_sha256']==sha(routepath)
        assert result['old_exhausted'] or result['old_zero']
        assert not result['old_failed'] and not result['verification_failed'] and not result['deadline']
        assert result['exhausted'] or result['zero']
        verified={}
        for kind in ['old','order']:
            v=read(dest/kind/'final.json');v['F']=v.get('F',v.get('objective'))
            check=evidence.physical_module.physical(p,v);assert check['original_T_feasible']
            assert abs(check['F']-result[kind+'_F'])<1e-7;verified[kind]=check
        assert result['order_F']<=result['old_F']+1e-12
        records.append(dict(receipt=receipt,result=result,verified=verified))
        write(batch/(case['id']+'.audit.json'),dict(passed=True,verified=verified))
    write(batch/'completed.json',dict(records=records,starts=6,optimizer_calls=0,elapsed_before_write=time.perf_counter()-started))

if __name__=='__main__':main()
