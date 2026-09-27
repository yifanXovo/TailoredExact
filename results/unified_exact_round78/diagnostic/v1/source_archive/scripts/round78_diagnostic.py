"""One frozen compile and three bounded zero-Optimize prototype processes."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import round70_affinity as affinity
import round78_audit as replay
from round75_startup import normalize,route_hash
from round76_qualify import ROOT,read,write,sha
OUT=ROOT/'results/unified_exact_round78'

def main():
    version=sys.argv[1];assert version in ['v1','v2']
    dest=OUT/'diagnostic'/version;build=ROOT/'build/round78/diagnostic'/version
    assert not dest.exists() and not build.exists(),'Never replace a diagnostic attempt'
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT).decode().strip()=='codex/round78-balanced-block-descent'
    measured=['include/Round78BalancedRelocation.hpp','src/Round78BalancedRelocation.cpp',
        'tests/round78_balanced_diagnostic.cpp','scripts/round78_diagnostic.py','scripts/round78_audit.py']
    assert not subprocess.check_output(['git','status','--porcelain','--',*measured],cwd=ROOT).strip(),'Commit measured prototype first'
    assert not (ROOT/'results/unified_exact_round77/campaign/active_run.lock').exists()
    q=read(ROOT/'results/unified_exact_round76/qualification_v1.json')['identity']
    for name,digest in q['source'].items():assert sha(ROOT/name)==digest,name
    assert sha(ROOT/'CMakeLists.txt')==q['cmake_sha256']
    dest.mkdir(parents=True);build.mkdir(parents=True)
    panel={p['id']:p for p in read(ROOT/'results/unified_exact_round71/protocol.json')['panel']}
    exe=build/'balanced_diagnostic.exe';compiler=Path('D:/msys64/ucrt64/bin/g++.exe')
    library=ROOT/'build/round76/v1/libexact_ebrp_core.a'
    command=list(map(str,[compiler,'-O3','-DNDEBUG','-std=c++17','-DEXACT_EBRP_ENABLE_GUROBI=1',
        '-I',ROOT/'include',ROOT/measured[1],ROOT/measured[2],library,'-o',exe,
        '-lkernel32','-luser32','-lgdi32','-lwinspool','-lshell32','-lole32','-loleaut32','-luuid','-lcomdlg32','-ladvapi32']))
    launches=[dict(id='structural',command=[str(exe),'structural',str(dest/'local_raw/structural')],
        destination=str((dest/'local_raw/structural').relative_to(ROOT)),cap=30)]
    sources=[];witnesses={}
    for key in ['D6','D7']:
        p=panel[key];assert sha(ROOT/p['instance_path'])==p['input_sha256']
        wp=ROOT/'results/unified_exact_round76/startup/local_raw'/key/'JDS-C/hga.csv.closure.csv.final.json'
        w=normalize(read(wp));witnesses[key]=w;replay.physical.ROOT=ROOT
        assert replay.physical.physical(p,w)['original_T_feasible']
        rp=dest/(key+'_routes.txt');lines=[str(len(w['routes']))]
        for r in w['routes']:
            ops={op['station']:op for op in r['operations']};lines.append(f"{r['vehicle']} {len(r['nodes'])-2}")
            lines.extend(f"{i} {ops[i]['pickup']} {ops[i]['drop']}" for i in r['nodes'][1:-1])
        rp.write_text('\n'.join(lines)+'\n',encoding='utf-8')
        folder=dest/'local_raw'/key
        launches.append(dict(id=key,input=p,destination=str(folder.relative_to(ROOT)),cap=60,
            command=list(map(str,[exe,'fixed',ROOT/p['instance_path'],p['T_seconds'],p['pickup_seconds'],
                p['drop_seconds'],p['lambda'],rp,folder]))))
        sources.append(dict(id=key,witness_path=str(wp.relative_to(ROOT)),witness_sha256=sha(wp),
            route_sha256=route_hash(w),diagnostic_route_input_sha256=sha(rp)))
    identity=dict(version=version,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),
        prototype_sources={name:sha(ROOT/name) for name in measured},plan_sha256=sha(OUT/'plan.md'),
        qualified_core_source=q['source_commit'],core_library_sha256=sha(library),
        qualified_core_identity_sha256=sha(ROOT/'results/unified_exact_round76/qualification_v1.json'),
        compiler_sha256=sha(compiler),compile_command=command,compile_cap=60,launches=launches,sources=sources,
        physical_reader_sha256=sha(replay.physical.__file__),inherited_closure_replay_sha256=sha(ROOT/'scripts/round76_startup.py'),
        scope='Fixed-witness structural diagnostic only; no native call or formal solver input')
    write(dest/'identity.json',identity)
    env=dict(os.environ);env['PATH']='D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;'+env.get('PATH','')
    started=time.perf_counter();records=[];compile_record=None;failure=None
    lock=dest/'active_run.lock';fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.close(fd)
    def save():write(dest/'summary.json',dict(compile=compile_record,records=records,failure=failure,
        total_driver_seconds=time.perf_counter()-started,optimizer_calls=0))
    try:
        began=time.perf_counter();killed=False
        with (build/'compile.log').open('w',encoding='utf-8') as log:
            proc=subprocess.Popen(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
            try:proc.wait(timeout=60)
            except subprocess.TimeoutExpired:
                killed=True;subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'],capture_output=True);proc.wait()
        compile_record=dict(returncode=proc.returncode,wall_seconds=time.perf_counter()-began,
            whole_tree_timeout=killed,log_sha256=sha(build/'compile.log'))
        write(dest/'compile.json',compile_record);save();print(json.dumps(dict(compile=compile_record)),flush=True)
        assert proc.returncode==0 and not killed,'Compile failed; inspect preserved log'
        identity['binary_sha256']=sha(exe);write(dest/'identity.json',identity)
        for launch in launches:
            folder=ROOT/launch['destination'];folder.mkdir(parents=True)
            write(folder/'launch.json',dict(launch,started_unix=time.time(),identity_sha256=sha(dest/'identity.json')))
            began=time.monotonic();killed=False
            with affinity.inherited_core() as binding:
                with (folder/'stdout.log').open('w',encoding='utf-8') as stdout,(folder/'stderr.log').open('w',encoding='utf-8') as stderr:
                    proc=subprocess.Popen(launch['command'],cwd=ROOT,env=env,stdout=stdout,stderr=stderr)
                    child=affinity.read_masks(proc.pid);assert child['process_mask']==4
                    write(folder/'affinity.json',dict(binding=binding,child=child,pid=proc.pid))
                    try:code=proc.wait(timeout=max(.001,launch['cap']-.2-(time.monotonic()-began)))
                    except subprocess.TimeoutExpired:proc.kill();proc.wait();code=proc.returncode;killed=True
            completion=dict(returncode=code,wall_seconds=time.monotonic()-began,watchdog=killed,restored_affinity=affinity.read_masks())
            write(folder/'completion.json',completion);record=dict(id=launch['id'],completion=completion,valid=False);records.append(record);save()
            assert code==0 and not killed and completion['wall_seconds']<=launch['cap'],(launch['id'],completion)
            assert completion['restored_affinity']==binding['before']
            assert read(folder/'result.json')['optimizer_calls']==0
            assert all('Optimize a model' not in (folder/name).read_text(encoding='utf-8',errors='replace') for name in ['stdout.log','stderr.log'])
            if launch['id']=='structural':
                audit=dict(passed=read(folder/'result.json')['passed'],oracle_cases=[json.loads(s) for s in (folder/'structural.jsonl').read_text(encoding='utf-8').splitlines()],optimizer_calls=0)
                assert audit['passed'] and len(audit['oracle_cases'])==7
            else:audit=replay.audit(panel[launch['id']],folder,witnesses[launch['id']])
            write(folder/'audit.json',audit);record.update(valid=True,audit=audit);save()
            print(json.dumps(dict(id=launch['id'],completion=completion,result=read(folder/'result.json'),valid=True)),flush=True)
    except Exception as error:
        failure=repr(error);raise
    finally:save();lock.unlink()

if __name__=='__main__':main()
