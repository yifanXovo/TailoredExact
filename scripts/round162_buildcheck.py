"""Serial clean default/research build after all timed solver calls have exited."""
from round162_common import *

def check():
    assert not budget()['unclosed']
    cmake=Path('D:/Program Files/Microsoft Visual Studio/2022/Professional/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe')
    ninja=cmake.parents[2]/'Ninja/ninja.exe';target=BUILD/'cmake_delivery'
    commands=[
        [cmake,'-S',ROOT,'-B',target,'-G','Ninja','-DCMAKE_MAKE_PROGRAM='+str(ninja),'-DCMAKE_CXX_COMPILER=D:/msys64/ucrt64/bin/g++.exe',
         '-DCMAKE_BUILD_TYPE=','-DEXACT_EBRP_ENABLE_GUROBI=ON','-DEXACT_EBRP_BUILD_ROUND162_RESEARCH=ON','-DGUROBI_ROOT=D:/gurobi1302/win64'],
        [cmake,'--build',target,'--target','ExactEBRP','Round162Research','--parallel','1']]
    for i,command in enumerate(commands):assert metered('cmake_delivery_'+str(i),'build',command,900)==0
    text=(target/'build.ninja').read_text();assert '-ffast-math' not in text and ' -O' not in text
    manifest=read(OUT/'build_v6.json');assert sha(manifest['research_PE'])==manifest['research_PE_SHA']
    # The stable public entry/profile and its main C++ dispatcher are unchanged.
    protected=['src/main.cpp','scripts/paper_s2.py','config/gi_tbc_round137.json','config/paper_s2.json']
    for path in protected:assert git('show',BASE+':'+path)==(ROOT/path).read_bytes(),path
    assert metered('default_CLI_help','build',[target/'ExactEBRP.exe','--help'],30)==0
    write(OUT/'engineering/cmake_delivery.json',dict(PASS=True,UTC=utc(),commands=[list(map(str,c)) for c in commands],
        CMake_SHA256=sha(cmake),CMakeLists_SHA256=sha(ROOT/'CMakeLists.txt'),delivery_research_PE_SHA256=sha(target/'Round162Research.exe'),
        default_production_PE_SHA256=sha(target/'ExactEBRP.exe'),Optimize=0,performance_sample=False,measured_PE_unchanged=True,
        stable_entry_byte_checks=protected,inherited_GNU_policy=True,parallel_build_jobs=1,
        default_off='EXACT_EBRP_BUILD_ROUND162_RESEARCH defaults OFF; stable CLI has no new enabled path'))

if __name__=='__main__':check()
