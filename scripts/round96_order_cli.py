"""Four no-Optimize CLI identity/combination tests, all launches counted."""
import os
import subprocess
import time
from round96_prepare import ROOT, OUT, read, write, sha

def main():
    dest=OUT/'route_order_cli';dest.mkdir(exist_ok=False)
    binary=ROOT/'build/research/round96-route-order/ExactEBRP.exe'
    env=dict(os.environ);env['PATH']='D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;'+env.get('PATH','')
    cases=[('on',['--round96-route-order','true'],'research-round96-ensc-route-order'),
           ('off',[],'research-round83-vds-equal-net-exchange'),
           ('reject_lp',['--round96-route-order','true','--round90-lp-g-split','true'],None),
           ('reject_hact',['--round96-route-order','true','--round92-handling-activation','true'],None)]
    records=[]
    for label,extra,identity in cases:
        output=dest/(label+'.json')
        cmd=[str(binary),'--input',str(dest/'missing-input.txt'),'--method','gcap-frontier',
             '--algorithm-preset','research-round83-vds-equal-net-exchange',*extra,'--out',str(output)]
        write(dest/(label+'.launch.json'),dict(command=cmd,optimizer_calls=0,binary_sha256=sha(binary)))
        tick=time.perf_counter()
        with (dest/(label+'.stdout.log')).open('x') as so,(dest/(label+'.stderr.log')).open('x') as se:
            ret=subprocess.run(cmd,cwd=ROOT,env=env,stdout=so,stderr=se,timeout=10)
        receipt=dict(id=label,returncode=ret.returncode,wall_seconds=time.perf_counter()-tick,optimizer_calls=0)
        write(dest/(label+'.receipt.json'),receipt);assert ret.returncode!=0
        if identity:assert read(output)['algorithm_preset']==identity
        else:assert 'Round96 route order requires isolated' in (dest/(label+'.stderr.log')).read_text()
        records.append(receipt)
    write(dest/'passed.json',dict(passed=True,starts=4,optimizer_calls=0,records=records,binary_sha256=sha(binary)))

if __name__=='__main__':main()
