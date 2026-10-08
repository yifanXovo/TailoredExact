"""Run only the named stdlib evidence tools, with exclusive actual receipts.

This is engineering accounting, never solver/start accounting. A running
performance executable or compiler prevents the operation. The measured tool
source and its pure reader dependencies are snapshotted before execution, so a
failed reader attempt can be retained before any repair.
"""
import argparse, hashlib, json, os, subprocess, time
from pathlib import Path

ALLOWED={'round108_reader.py','round108_reader_counterexamples.py','round108_public.py','round108_report.py'}
DEPS=['round108_reader.py','round108_scopes.py','round108_decisions.py','round107_reader.py',
      'round99_pure_start_audit.py','round99_common.py','round108_public.py','round108_report.py']

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,value):
    with Path(path).open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
def run(source_root,receipt_root,label,script,args,timeout):
    assert script in ALLOWED
    if os.name=='nt':
        state=subprocess.check_output(['tasklist','/FO','CSV','/NH'],text=True).lower()
        assert not any('"'+n.lower()+'"' in state for n in ['ExactEBRP.exe','gurobi_cl.exe','g++.exe','cc1plus.exe','ninja.exe'])
    source_root=Path(source_root).resolve();receipt_root=Path(receipt_root).resolve()
    directory=receipt_root/'results/unified_exact_round108/engineering'/label
    directory.mkdir(parents=True,exist_ok=False);snapshots=[]
    for name in sorted(set(DEPS+[script,'round108_engineering.py'])):
        path=source_root/'scripts'/name
        if not path.exists():continue
        data=path.read_bytes();target=directory/'source_snapshot/scripts'/name;target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as f:f.write(data)
        snapshots.append(dict(path=path.as_posix(),sha256=hashlib.sha256(data).hexdigest(),snapshot=target.relative_to(receipt_root).as_posix()))
    command=[os.sys.executable,str(source_root/'scripts'/script),*args]
    launch=dict(command=command,cwd=str(source_root),explicit_source_root=str(source_root),receipt_root=str(receipt_root),
        sources=snapshots,engineering=True,conservative_solver_starts=0,Optimize=0,IIS=0,route_oracle=0)
    write(directory/'launch.json',launch);begin=time.perf_counter()
    with (directory/'stdout.log').open('xb') as stdout,(directory/'stderr.log').open('xb') as stderr:
        child=subprocess.Popen(command,cwd=source_root,stdout=stdout,stderr=stderr)
        write(directory/'process.json',dict(pid=child.pid,wrapper_pid=os.getpid()))
        timed_out=False
        try:code=child.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out=True;child.kill();code=child.wait()
    receipt=dict(command=command,cwd=str(source_root),source_root=str(source_root),engineering=True,
        seconds=time.perf_counter()-begin,exit_code=code,timed_out=timed_out,
        stdout_SHA=sha(directory/'stdout.log'),stderr_SHA=sha(directory/'stderr.log'),
        launch_SHA=sha(directory/'launch.json'),sources=snapshots,conservative_solver_starts=0,Optimize=0,IIS=0,route_oracle=0)
    write(directory/'receipt.json',receipt)
    print(json.dumps(receipt,allow_nan=False));return code

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source-root',required=True);p.add_argument('--receipt-root',required=True)
    p.add_argument('--label',required=True);p.add_argument('--script',required=True);p.add_argument('--timeout',type=float,default=1800)
    p.add_argument('args',nargs=argparse.REMAINDER);a=p.parse_args();args=a.args[1:] if a.args[:1]==['--'] else a.args
    raise SystemExit(run(a.source_root,a.receipt_root,a.label,a.script,args,a.timeout))
