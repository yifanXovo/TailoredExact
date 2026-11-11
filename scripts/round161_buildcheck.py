"""Serial delivery clean build, after all timed scientific calls have ended."""
from round161_common import *

def check():
    assert not budget()['unclosed']
    cmake=Path('D:/Program Files/Microsoft Visual Studio/2022/Professional/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe')
    ninja=cmake.parents[2]/'Ninja/ninja.exe';target=BUILD/'cmake_delivery'
    commands=[
        [cmake,'-S',ROOT,'-B',target,'-G','Ninja','-DCMAKE_MAKE_PROGRAM='+str(ninja),'-DCMAKE_CXX_COMPILER=D:/msys64/ucrt64/bin/g++.exe',
         '-DCMAKE_BUILD_TYPE=','-DEXACT_EBRP_ENABLE_GUROBI=ON','-DEXACT_EBRP_BUILD_ROUND161_RESEARCH=ON','-DGUROBI_ROOT=D:/gurobi1302/win64'],
        [cmake,'--build',target,'--target','ExactEBRP','Round161Research','--parallel','1']]
    for i,command in enumerate(commands):assert metered('cmake_delivery_'+str(i),'build',command,900)==0
    text=(target/'build.ninja').read_text();assert '-ffast-math' not in text and ' -O' not in text
    for name in ('measured_manifest.json','measured_manifest_RNP.json'):
        m=read(OUT/name);assert sha(m['research_PE'])==m['research_PE_SHA']
    write(OUT/'engineering/cmake_delivery.json',dict(PASS=True,UTC=utc(),commands=[list(map(str,c)) for c in commands],
        CMake_SHA=sha(cmake),CMakeLists_SHA=sha(ROOT/'CMakeLists.txt'),delivery_PE_SHA=sha(target/'Round161Research.exe'),
        default_production_PE_SHA=sha(target/'ExactEBRP.exe'),Optimize=0,performance_sample=False,measured_PEs_unchanged=True,
        inherited_GNU_policy=True,parallel_build_jobs=1))

if __name__=='__main__':check()
