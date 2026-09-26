"""Print or replay exactly one recorded Round61 launch into a new directory.

Default is read-only. --run explicitly executes the selected experiment. A
different compiler/build can use --allow-different-build, which marks the replay
as a reproduction rather than another member of the original matched pair.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time
from round61_research import ROOT, BUILD, entries, panel, sha, write

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--charged-number',required=True,type=int)
    parser.add_argument('--out',required=True,type=Path)
    parser.add_argument('--run',action='store_true')
    parser.add_argument('--allow-different-build',action='store_true')
    args=parser.parse_args()
    matches=[e for e in entries() if e['charged_number']==args.charged_number]
    if len(matches)!=1: raise RuntimeError('select exactly one charged launch')
    e=matches[0];dest=args.out.resolve()
    if dest.exists(): raise RuntimeError('output already exists; refusing to overwrite')
    # Manifest path may have been created on a different checkout/OS.
    old=e['command'][0].replace('\\','/')
    oldroot=old.split('/build/')[0] if '/build/' in old else None
    if oldroot is None:
        source_scripts=[str(a).replace('\\','/') for a in e['command'] if '/scripts/' in str(a).replace('\\','/')]
        if not source_scripts:raise RuntimeError('recorded checkout root cannot be identified')
        oldroot=source_scripts[0].split('/scripts/')[0]
    olddest=e['destination'].replace('\\','/')
    cmd=[]
    for arg in e['command']:
        a=str(arg).replace('\\','/')
        if a.startswith(oldroot+'/'+olddest): a=str(dest)+a[len(oldroot+'/'+olddest):]
        elif a.startswith(oldroot): a=str(ROOT)+a[len(oldroot):]
        cmd.append(a)
    if e['kind']=='proof-construction':
        # This solver-free batch reads historical points but must write the
        # replay's proof artifacts into its new output directory.
        cmd+=['--out',str(dest)]
    if e['id'] in panel():
        p=panel()[e['id']]
        assert sha(ROOT/p['instance_path'])==p['input_sha256'],'input identity changed'
    same=Path(cmd[0]).is_file() and sha(cmd[0])==e['executable_sha256']
    archived=ROOT/'results/gf_transfer_block_native_time_round61/local_raw/paired_executables'/e['executable_sha256']/Path(cmd[0]).name
    if not same and archived.exists() and sha(archived)==e['executable_sha256']:
        cmd[0]=str(archived);same=True
    if not same and not args.allow_different_build: raise RuntimeError('binary differs; rebuild recorded source or explicitly allow a reproduction build')
    if not same:
        for flag in ['--round24-executable-sha256','--round24-manifest-executable-sha256']:
            if flag in cmd:cmd[cmd.index(flag)+1]=sha(cmd[0])
    print(json.dumps(dict(command=cmd,cap_seconds=e['cap_seconds'],same_recorded_binary=same),ensure_ascii=False,indent=2))
    if not args.run:return
    dest.mkdir(parents=True)
    write(dest/'replay_launch.json',dict(original=e,command=cmd,executable_sha256=sha(cmd[0]),same_recorded_binary=same))
    env=dict(os.environ);env['PATH']='D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;'+env.get('PATH','')
    start=time.monotonic();watchdog=False
    with (dest/'stdout.log').open('w') as stdout,(dest/'stderr.log').open('w') as stderr:
        proc=subprocess.Popen(cmd,cwd=ROOT,env=env,stdout=stdout,stderr=stderr)
        try: code=proc.wait(timeout=e['cap_seconds']+10)
        except subprocess.TimeoutExpired:proc.kill();proc.wait();code=proc.returncode;watchdog=True
    seconds=time.monotonic()-start
    write(dest/'replay_completion.json',dict(returncode=code,wall_seconds=seconds,watchdog=watchdog,within_budget=seconds<=e['cap_seconds']))
    raise SystemExit(code)

if __name__=='__main__':main()
