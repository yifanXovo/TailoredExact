"""Serial, receipted build; no Optimize. Never overwrite a build log label."""
import json, os, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/unified_exact_round97'
BUILD=ROOT/'build/research/round97-native-closure'
CMAKE=Path('D:/Program Files/Microsoft Visual Studio/2022/Professional/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe')
NINJA=Path('D:/Program Files/Microsoft Visual Studio/2022/Professional/Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe')
def run(label,command):
    dest=OUT/'engineering'/label;dest.mkdir(parents=True,exist_ok=False)
    env=dict(os.environ);env['PATH']='D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;'+env.get('PATH','')
    (dest/'launch.json').write_text(json.dumps(dict(command=list(map(str,command)),optimizer_calls=0),indent=2))
    t=time.perf_counter()
    with (dest/'stdout.log').open('w') as out,(dest/'stderr.log').open('w') as err:
        result=subprocess.run(list(map(str,command)),cwd=ROOT,env=env,stdout=out,stderr=err)
    receipt=dict(exit_code=result.returncode,wall_seconds=time.perf_counter()-t,optimizer_calls=0)
    (dest/'receipt.json').write_text(json.dumps(receipt,indent=2));print(receipt,flush=True)
    if result.returncode:
        print((dest/'stdout.log').read_text()[-12000:]);print((dest/'stderr.log').read_text()[-12000:]);sys.exit(result.returncode)
if __name__=='__main__':
    label=sys.argv[1]
    if not (BUILD/'CMakeCache.txt').exists():
        run(label+'_configure',[CMAKE,'-S',ROOT,'-B',BUILD,'-G','Ninja','-DCMAKE_CXX_COMPILER=D:/msys64/ucrt64/bin/g++.exe',
            '-DCMAKE_MAKE_PROGRAM='+str(NINJA),'-DEXACT_EBRP_ENABLE_GUROBI=ON','-DGUROBI_ROOT=D:/gurobi1302/win64','-DCMAKE_BUILD_TYPE='])
    run(label,[CMAKE,'--build',BUILD,'--target',*(sys.argv[2:] or ['ExactEBRP']),'--parallel','4'])
