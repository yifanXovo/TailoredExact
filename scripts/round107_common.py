"""Exclusive Round107 receipts. Import performs no native work."""
from round103_common import ROOT,CMAKE,NINJA,sha,read,write,bindings,env
from pathlib import Path
import json,os,subprocess,sys,time
OUT=ROOT/'results/unified_exact_round107'
BUILD=ROOT/'build/research/round107-frontier-v1'
PYTHON=Path('D:/msys64/ucrt64/bin/python.exe')
DLL=Path('D:/gurobi1302/win64/bin/gurobi130.dll')
def budget():
    launches=list((OUT/'fees').glob('*/launch.json'));receipts=list((OUT/'fees').glob('*/receipt.json'))
    starts=sum(read(p)['conservative_process_starts'] for p in launches)
    starts+=sum(read(p)['additional_conservative_starts'] for p in (OUT/'fee_corrections').glob('*.json'))
    seconds=sum(read(p)['outer_seconds'] for p in receipts)
    return dict(paid_starts=starts,paid_outer_seconds=seconds,remaining_starts=72-starts,remaining_outer_seconds=80000-seconds,
                unclosed=[str(p.parent.relative_to(ROOT)) for p in launches if not (p.parent/'receipt.json').exists()])
def receipt(label,command,cap=600,engineering=False,children=0):
    from round100_idle import ensure_idle
    ensure_idle();b=budget()
    if b['unclosed']:
        control=OUT/'campaign_control/cli_and_development03'
        assert engineering and b['unclosed']==['results/unified_exact_round107/fees/cli_and_development03'] and \
            (control/'02_CLI_after.json').exists() and not (control/'03_formal_before.json').exists(),b
    if not engineering:assert b['remaining_starts']>=1+children and b['remaining_outer_seconds']>=cap
    d=OUT/('engineering' if engineering else 'fees')/label;d.mkdir(parents=True,exist_ok=False)
    write(d/'launch.json',dict(command=list(map(str,command)),cap_seconds=cap,engineering=engineering,
        command_file_SHA={str(p):sha(p) for p in map(Path,map(str,command)) if p.is_file()},
        conservative_process_starts=0 if engineering else 1+children,declared_children=children,budget_before=b,
        source_bindings=bindings(),started_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())))
    tick=time.perf_counter();code=None;reason='normal_return'
    with (d/'stdout.log').open('x') as so,(d/'stderr.log').open('x') as se:
        p=subprocess.Popen(list(map(str,command)),cwd=ROOT,env=env(),stdout=so,stderr=se)
        write(d/'process.json',dict(pid=p.pid,parent_pid=os.getpid()))
        try:code=p.wait(timeout=cap)
        except subprocess.TimeoutExpired:
            reason='whole_process_timeout';subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],stdout=se,stderr=se);p.wait()
    v=dict(exit_code=code,outer_seconds=time.perf_counter()-tick,stop_reason=reason,engineering=engineering,
           conservative_process_starts=0 if engineering else 1+children)
    write(d/'receipt.json',v);print(json.dumps(v),flush=True)
    if code!=0:raise RuntimeError(str(d)+': '+(d/'stdout.log').read_text()[-2500:]+(d/'stderr.log').read_text()[-2500:])
    return v
if __name__=='__main__':
    label,cap,kind=sys.argv[1:4];args=sys.argv[4:];children=0
    if args and args[0].startswith('--children='):children=int(args.pop(0).split('=',1)[1])
    receipt(label,args,float(cap),kind=='engineering',children)
