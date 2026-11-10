"""Delivery-only clean CMake build; never a performance sample or Optimize."""
from round160_common import *

def check():
    configure()
    cmake=Path('D:/Program Files/Microsoft Visual Studio/2022/Professional/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe')
    ninja=cmake.parents[2]/'Ninja/ninja.exe'
    target=BUILD/'cmake_delivery';logs=OUT/'engineering/cmake_delivery'
    logs.mkdir(parents=True,exist_ok=True)
    commands=[
        [cmake,'-S',ROOT,'-B',target,'-G','Ninja','-DCMAKE_MAKE_PROGRAM='+str(ninja),
         '-DCMAKE_CXX_COMPILER=D:/msys64/ucrt64/bin/g++.exe','-DCMAKE_BUILD_TYPE=',
         '-DEXACT_EBRP_ENABLE_GUROBI=ON','-DEXACT_EBRP_BUILD_ROUND160_RESEARCH=ON',
         '-DGUROBI_ROOT=D:/gurobi1302/win64'],
        [cmake,'--build',target,'--target','ExactEBRP','Round160Research','--parallel','1']]
    for i,cmd in enumerate(commands):
        with (logs/f'{i}.log').open('wb') as stream:
            subprocess.run(list(map(str,cmd)),cwd=ROOT,env=meter.environment(),stdout=stream,stderr=subprocess.STDOUT,check=True)
    build=(target/'build.ninja').read_text()
    link=next(line for line in build.splitlines() if line.startswith('build ExactEBRP.exe:'))
    assert 'gurobi130.lib' in link.lower() or 'gurobi130.dll' in link.lower(),link
    assert '-ffast-math' not in build and ' -O' not in build
    frozen=read(OUT/'candidate_manifest.json')
    assert sha(frozen['production_PE'])==frozen['production_PE_SHA']
    assert all(sha(ROOT/name)==digest for name,digest in frozen['source_hashes'].items())
    write(OUT/'engineering/cmake_delivery.json',dict(UTC=utc(),PASS=True,commands=[list(map(str,c)) for c in commands],
        CMake_SHA=sha(cmake),CMakeLists_SHA=sha(ROOT/'CMakeLists.txt'),ExactEBRP_SHA=sha(target/'ExactEBRP.exe'),
        Round160Research_SHA=sha(target/'Round160Research.exe'),production_link=link,
        new_Optimize=0,performance_sample=False,measured_production_PE_unchanged=True,
        change='CMake import-library dependency only; C++ and frozen measured PE unchanged',
        no_optimization_or_fast_math_override=True))

if __name__=='__main__':check()
