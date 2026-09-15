"""Serial isolated build and actual test batch; retain every attempted revision."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/unified_exact_round73'
CMAKE = Path('D:/Program Files/Microsoft Visual Studio/2022/Professional/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin')

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')

def main():
    version = sys.argv[1]
    assert version in ['v1', 'v2', 'v3', 'v4', 'v5']
    build = ROOT / 'build/round73' / version
    assert not build.exists(), 'Never replace a prior build/test revision'
    assert subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT).decode().strip() == 'codex/round73-joint-insertion'
    for old in ['unified_exact_round71', 'unified_exact_round72/campaign', 'unified_exact_round73']:
        assert not (ROOT / 'results' / old / 'active_run.lock').exists()
    build.mkdir(parents=True)
    identity = dict(source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),
        source={str(p.relative_to(ROOT)):sha(p) for folder in ['src','include','tests']
                for p in sorted((ROOT/folder).rglob('*')) if p.is_file()},
        cmake_sha256=sha(ROOT/'CMakeLists.txt'),plan_sha256=sha(OUT/'plan.md'),
        qualification_script_sha256=sha(__file__),version=version)
    write(OUT/f'qualification_{version}_launch.json',identity)
    env=dict(os.environ);env['PATH']='D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;'+env.get('PATH','')
    commands = [
        ('configure', [str(CMAKE/'cmake.exe'), '-S', str(ROOT), '-B', str(build), '-G', 'MinGW Makefiles',
            '-DCMAKE_BUILD_TYPE=Release', '-DCMAKE_CXX_COMPILER=D:/msys64/ucrt64/bin/g++.exe',
            '-DCMAKE_MAKE_PROGRAM=D:/msys64/ucrt64/bin/mingw32-make.exe',
            '-DEXACT_EBRP_ENABLE_GUROBI=ON','-DGUROBI_ROOT=D:/gurobi1302/win64']),
        ('build', [str(CMAKE/'cmake.exe'),'--build',str(build),'-j','4']),
        ('tests', [str(CMAKE/'ctest.exe'),'--test-dir',str(build),'--output-on-failure','-V','-j','1'])]
    records=[]
    for phase,command in commands:
        record=dict(version=version,phase=phase,command=command,started_unix=time.time())
        with (OUT/'qualification_processes.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(record)+'\n')
        start=time.perf_counter()
        with (build/(phase+'.log')).open('w',encoding='utf-8') as stream:
            result=subprocess.run(command,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT)
        record.update(returncode=result.returncode,wall_seconds=time.perf_counter()-start,
            log=str((build/(phase+'.log')).relative_to(ROOT)),log_sha256=sha(build/(phase+'.log')))
        records.append(record);write(OUT/f'qualification_{version}.json',dict(identity=identity,attempts=records))
        print(json.dumps({k:record[k] for k in ['version','phase','returncode','wall_seconds']}),flush=True)
        if result.returncode:
            print((build/(phase+'.log')).read_text(encoding='utf-8',errors='replace')[-3500:],flush=True)
            raise SystemExit(result.returncode)
    print('All configured tests passed; inspect test evidence and count native calls before admission.',flush=True)

if __name__=='__main__':main()
