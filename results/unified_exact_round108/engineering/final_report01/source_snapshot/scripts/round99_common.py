"""Exclusive receipts and frozen build utilities; importing launches nothing."""
import hashlib,json,os,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/unified_exact_round99'
BUILD=ROOT/'build/research/round99-discrete-v2'
CMAKE=Path('D:/Program Files/Microsoft Visual Studio/2022/Professional/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe')
NINJA=Path('D:/Program Files/Microsoft Visual Studio/2022/Professional/Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
def bindings():
    paths=[ROOT/'CMakeLists.txt']+sorted((ROOT/'src').glob('*.cpp'))+sorted((ROOT/'src/hga_tgbc').glob('*.cpp'))+sorted((ROOT/'include').rglob('*.hpp'))
    return {p.relative_to(ROOT).as_posix():sha(p) for p in paths}
def env():
    e=dict(os.environ);e['PATH']='D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;'+e.get('PATH','');return e
def receipt(label,command,kind='engineering',cap=600,optimizer_calls=0):
    d=OUT/kind/label;d.mkdir(parents=True,exist_ok=False)
    write(d/'launch.json',dict(command=list(map(str,command)),kind=kind,cap=cap,planned_optimizer_calls=optimizer_calls,
        command_file_bindings={str(p):sha(p) for p in map(Path,map(str,command)) if p.is_file()}))
    start=time.perf_counter();reason='normal_return';code=None
    try:
        with (d/'stdout.log').open('x') as so,(d/'stderr.log').open('x') as se:
            run=subprocess.run(list(map(str,command)),cwd=ROOT,env=env(),stdout=so,stderr=se,timeout=cap)
        code=run.returncode
    except subprocess.TimeoutExpired:reason='whole_process_timeout'
    result=dict(exit_code=code,stop_reason=reason,outer_seconds=time.perf_counter()-start,
        planned_optimizer_calls=optimizer_calls,optimizer_calls=optimizer_calls if code==0 else None)
    write(d/'receipt.json',result);print(json.dumps(result),flush=True)
    if code!=0:raise RuntimeError(str(d)+': '+(d/'stdout.log').read_text()[-2500:]+(d/'stderr.log').read_text()[-2500:])
    return result
