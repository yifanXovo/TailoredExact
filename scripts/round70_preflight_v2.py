"""Record configure/build/test attempts before opening Round70 experiments."""
import argparse, datetime, hashlib, json, os, subprocess, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/unified_exact_round70/revision2'
BUILD=ROOT/'build/round70_v2'
CMAKE=Path('D:/Program Files/Microsoft Visual Studio/2022/Professional/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe')
CTEST=CMAKE.with_name('ctest.exe')

def main(action):
    assert not (OUT/'active_run.lock').exists()
    assert not (ROOT/'results/unified_exact_round69/active_run.lock').exists()
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT).decode().strip()=='codex/round70-vds-descent'
    BUILD.mkdir(parents=True,exist_ok=True)
    commands={
        'configure':[CMAKE,'-S',ROOT,'-B',BUILD,'-G','MinGW Makefiles',
            '-DCMAKE_MAKE_PROGRAM=D:/msys64/ucrt64/bin/mingw32-make.exe',
            '-DCMAKE_CXX_COMPILER=D:/msys64/ucrt64/bin/g++.exe',
            '-DCMAKE_BUILD_TYPE=Release','-DEXACT_EBRP_ENABLE_GUROBI=ON',
            '-DGUROBI_ROOT=D:/gurobi1302/win64'],
        'build':[CMAKE,'--build',BUILD,'--parallel','4'],
        'test':[CTEST,'--test-dir',BUILD,'--parallel','1','--verbose',
            '--output-on-failure','--timeout','120']}
    ledger=OUT/'preflight_processes.jsonl'
    entries=[json.loads(s) for s in ledger.read_text(encoding='utf-8').splitlines()] if ledger.exists() else []
    number=1+sum(e['event']=='launch' and e['action']==action for e in entries)
    log=BUILD/f'{action}_{number}.log'
    assert not log.exists()
    command=list(map(str,commands[action]))
    launch=dict(event='launch',action=action,attempt=number,command=command,
        started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        output=str(log.relative_to(ROOT)),experiment_launch=False)
    with ledger.open('a',encoding='utf-8') as f:f.write(json.dumps(launch)+'\n')
    env=dict(os.environ)
    env['PATH']='D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;'+env.get('PATH','')
    started=time.perf_counter()
    with log.open('wb') as stream:
        completed=subprocess.run(command,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT)
    result=dict(event='completion',action=action,attempt=number,
        returncode=completed.returncode,wall_seconds=time.perf_counter()-started,
        output=str(log.relative_to(ROOT)),sha256=hashlib.sha256(log.read_bytes()).hexdigest(),
        experiment_launch=False)
    with ledger.open('a',encoding='utf-8') as f:f.write(json.dumps(result)+'\n')
    if action=='test' and completed.returncode==0:
        (BUILD/'tests.log').write_bytes(log.read_bytes())
        (OUT/'tests.log').write_bytes(log.read_bytes())
    print(json.dumps(result),flush=True)
    print('\n'.join(log.read_text(encoding='utf-8',errors='replace').splitlines()[-18:]),flush=True)
    raise SystemExit(completed.returncode)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['configure','build','test'])
    main(parser.parse_args().action)
