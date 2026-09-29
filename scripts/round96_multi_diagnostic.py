"""Six predeclared real witness cases, each exactly three finite library tasks.

Per case: direct rays; full-pair closure; rays after full-pair closure.
120s external diagnostic protection, never a production neighborhood switch.
"""
import ctypes as ct
import os
import subprocess
import time
from pathlib import Path
from round96_prepare import ROOT, OUT, read, write, sha, evidence

BIN=ROOT/'build/research/round96-multi-quantity/Round96MultiQuantityDiagnostic.exe'

def main():
    start=time.perf_counter();cases=read(OUT/'fixed_route_cases.json')['cases']
    gate=read(OUT/'multi_quantity_build_gate.json')
    assert gate['qualified'] is True and gate['binary_sha256']==sha(BIN)
    for path,value in gate['source_hashes'].items():assert sha(ROOT/path)==value
    batch=OUT/'multi_quantity';batch.mkdir(exist_ok=False)
    env=dict(os.environ);env['PATH']='D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;'+env.get('PATH','')
    kernel=ct.WinDLL('kernel32',use_last_error=True);kernel.GetCurrentProcess.restype=ct.c_void_p
    kernel.SetProcessAffinityMask.argtypes=[ct.c_void_p,ct.c_size_t]
    assert kernel.SetProcessAffinityMask(kernel.GetCurrentProcess(),4)
    records=[]
    write(batch/'plan.json',dict(cases=[c['id'] for c in cases],processes=6,library_tasks_per_case=3,
        cap_per_process=120,maximum_seconds=720,optimizer_calls=0,binary_sha256=sha(BIN),runner_sha256=sha(__file__)))
    for case in cases:
        p=case['panel'];w=read(ROOT/case['witness_path']);assert sha(ROOT/case['witness_path'])==case['witness_sha256']
        text=[str(len(w['routes']))]
        for route in w['routes']:
            text.append(f'{route["vehicle"]} {len(route["nodes"])-2}')
            ops={o['station']:o for o in route['operations']}
            for i in route['nodes'][1:-1]:
                o=ops[i];text.append(f'{i} {o["pickup"]} {o["drop"]}')
        routepath=batch/(case['id']+'.routes.txt');routepath.write_text('\n'.join(text)+'\n')
        dest=batch/case['id'];command=list(map(str,[BIN,ROOT/p['instance_path'],routepath,p['T_seconds'],
            p['pickup_seconds'],p['drop_seconds'],p['lambda'],dest]))
        write(batch/(case['id']+'.launch.json'),dict(command=command,cap_seconds=120,optimizer_calls=0))
        tick=time.perf_counter()
        with (batch/(case['id']+'.stdout.log')).open('x') as so,(batch/(case['id']+'.stderr.log')).open('x') as se:
            try:
                ret=subprocess.run(command,cwd=ROOT,env=env,stdout=so,stderr=se,timeout=120)
                code=ret.returncode;reason='normal_return'
            except subprocess.TimeoutExpired:code=None;reason='diagnostic_timeout'
        wall=time.perf_counter()-tick
        receipt=dict(id=case['id'],exit_code=code,stop_reason=reason,wall_seconds=wall,optimizer_calls=0)
        write(batch/(case['id']+'.completion.json'),receipt)
        assert code==0, 'stop after failed or incomplete diagnostic; preserve paid prefix'
        result=read(dest/'summary.json')
        assert result['input_sha256']==p['input_sha256'] and result['route_sha256']==sha(routepath)
        assert result['pair_exhausted'] and result['direct']['exhausted'] and result['after_pair']['exhausted']
        verified={}
        for kind in ['direct','pair','after_pair']:
            v=read(dest/(kind+'.json')); v['F']=v.get('F',v.get('objective'))
            checked=evidence.physical_module.physical(p,v);assert checked['original_T_feasible']
            expected=result['pair_F'] if kind=='pair' else result[kind]['F'];assert abs(checked['F']-expected)<1e-7
            verified[kind]=checked
        assert result['direct']['F']<=result['initial_F']+1e-12
        assert result['after_pair']['F']<=result['pair_F']+1e-12
        records.append(dict(receipt=receipt,result=result,verified=verified))
        write(batch/(case['id']+'.audit.json'),dict(passed=True,verified=verified))
    write(batch/'completed.json',dict(records=records,starts=6,optimizer_calls=0,
        elapsed_before_write=time.perf_counter()-start))

if __name__=='__main__':main()
