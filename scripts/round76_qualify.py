"""Bounded serial qualification; never replace a failed build/test revision."""
import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from contextlib import nullcontext
import round70_affinity as affinity

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/unified_exact_round76'
CMAKE=Path('D:/Program Files/Microsoft Visual Studio/2022/Professional/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin')
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,value): Path(path).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def read(path): return json.loads(Path(path).read_text(encoding='utf-8'))

def main():
    version=sys.argv[1]
    assert version in ['v1','v2']
    build=ROOT/'build/round76'/version
    assert not build.exists(),'Never replace a prior qualification attempt'
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT).decode().strip()=='codex/round76-physical-route-closure'
    assert not subprocess.check_output(['git','status','--porcelain','--','src','include','tests','CMakeLists.txt','scripts/round76_qualify.py','scripts/round76_audit_qualification.py'],cwd=ROOT).strip(),'Commit measured source first'
    for stage in ['unified_exact_round72/campaign','unified_exact_round73','unified_exact_round74/campaign','unified_exact_round76/startup']:
        assert not (ROOT/'results'/stage/'active_run.lock').exists()
    lock=OUT/'qualification_active.lock'
    fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.close(fd)
    build.mkdir(parents=True)
    identity=dict(source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),
        source={str(p.relative_to(ROOT)):sha(p) for folder in ['src','include','tests']
                for p in sorted((ROOT/folder).rglob('*')) if p.is_file()},
        cmake_sha256=sha(ROOT/'CMakeLists.txt'),plan_sha256=sha(OUT/'plan.md'),
        qualification_script_sha256=sha(__file__),version=version,
        implementation_plan_sha256=sha(OUT/'implementation_plan.md'),
        allowed_optimize_calls=150)
    write(OUT/f'qualification_{version}_launch.json',identity)
    env=dict(os.environ);env['PATH']='D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;'+env.get('PATH','')
    commands=[
        ('configure',60,[str(CMAKE/'cmake.exe'),'-S',str(ROOT),'-B',str(build),'-G','MinGW Makefiles',
            '-DCMAKE_BUILD_TYPE=Release','-DCMAKE_CXX_COMPILER=D:/msys64/ucrt64/bin/g++.exe',
            '-DCMAKE_MAKE_PROGRAM=D:/msys64/ucrt64/bin/mingw32-make.exe',
            '-DEXACT_EBRP_ENABLE_GUROBI=ON','-DGUROBI_ROOT=D:/gurobi1302/win64']),
        ('build',600,[str(CMAKE/'cmake.exe'),'--build',str(build),'-j','4']),
        ('tests',600,[str(CMAKE/'ctest.exe'),'--test-dir',str(build),'--output-on-failure','-V','-j','1'])]
    records=[]
    try:
        for phase,cap,command in commands:
            record=dict(version=version,phase=phase,command=command,started_unix=time.time(),whole_phase_cap=cap)
            with (OUT/'qualification_processes.jsonl').open('a',encoding='utf-8') as stream:stream.write(json.dumps(record)+'\n')
            start=time.perf_counter();killed=False
            with affinity.inherited_core() if phase=='tests' else nullcontext(None) as binding:
                with (build/(phase+'.log')).open('w',encoding='utf-8') as stream:
                    proc=subprocess.Popen(command,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT)
                    record['pid']=proc.pid
                    if binding:
                        record['affinity']=binding;record['child_affinity']=affinity.read_masks(proc.pid)
                        assert record['child_affinity']['process_mask']==4
                    write(OUT/f'qualification_{version}_active.json',record)
                    try: code=proc.wait(timeout=cap)
                    except subprocess.TimeoutExpired:
                        killed=True
                        # Only the owned, still-running qualification process tree.
                        subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'],capture_output=True)
                        proc.wait();code=proc.returncode
            record.update(returncode=code,whole_tree_timeout=killed,wall_seconds=time.perf_counter()-start,
                log=str((build/(phase+'.log')).relative_to(ROOT)),log_sha256=sha(build/(phase+'.log')))
            if binding:
                record['restored_affinity']=affinity.read_masks()
                assert record['restored_affinity']==binding['before']
            records.append(record);write(OUT/f'qualification_{version}.json',dict(identity=identity,attempts=records))
            print(json.dumps({k:record[k] for k in ['version','phase','returncode','wall_seconds','whole_tree_timeout']}),flush=True)
            if code or killed:
                print((build/(phase+'.log')).read_text(encoding='utf-8',errors='replace')[-5000:],flush=True)
                raise SystemExit(code or 1)
        print('Qualification finished; inspect every test and actual native call before startup admission.',flush=True)
    finally:
        lock.unlink()

if __name__=='__main__':main()
