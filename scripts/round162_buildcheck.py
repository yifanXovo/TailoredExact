"""Serial clean default/research build after all timed solver calls have exited."""
from round162_common import *

def check(prefix='cmake_delivery'):
    assert not budget()['unclosed']
    cmake=Path('D:/Program Files/Microsoft Visual Studio/2022/Professional/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe')
    ninja=cmake.parents[2]/'Ninja/ninja.exe';target=BUILD/'cmake_delivery';default=BUILD/'cmake_default'
    commands=[
        [cmake,'-S',ROOT,'-B',default,'-G','Ninja','-DCMAKE_MAKE_PROGRAM='+str(ninja),'-DCMAKE_CXX_COMPILER=D:/msys64/ucrt64/bin/g++.exe',
         '-DCMAKE_BUILD_TYPE=','-DEXACT_EBRP_ENABLE_GUROBI=OFF','-DEXACT_EBRP_BUILD_ROUND162_RESEARCH=OFF'],
        [cmake,'--build',default,'--target','ExactEBRP','--parallel','1'],
        [cmake,'-S',ROOT,'-B',target,'-G','Ninja','-DCMAKE_MAKE_PROGRAM='+str(ninja),'-DCMAKE_CXX_COMPILER=D:/msys64/ucrt64/bin/g++.exe',
         '-DCMAKE_BUILD_TYPE=','-DEXACT_EBRP_ENABLE_GUROBI=ON','-DEXACT_EBRP_BUILD_ROUND162_RESEARCH=ON','-DGUROBI_ROOT=D:/gurobi1302/win64'],
        [cmake,'--build',target,'--target','ExactEBRP','Round162Research','Round162ScopeTests','--parallel','1']]
    for i,command in enumerate(commands):assert metered(prefix+'_'+str(i),'build',command,900)==0
    for folder in (default,target):
        text=(folder/'build.ninja').read_text();assert '-ffast-math' not in text and ' -O' not in text
    manifest=read(OUT/'build_v6.json');assert sha(manifest['research_PE'])==manifest['research_PE_SHA']
    # Existing entry/profile bytes stay fixed. main.cpp now exposes the guarded,
    # default-off research family; it cannot truthfully be called unchanged.
    protected=['scripts/paper_s2.py','config/gi_tbc_round137.json','config/paper_s2.json']
    for path in protected:assert git('show',BASE+':'+path)==(ROOT/path).read_bytes(),path
    current=(ROOT/'src/main.cpp').read_text();old=git('show',BASE+':src/main.cpp').decode()
    assert 'round162-physical-completion' in current and 'round162-physical-completion' not in old
    for key in ('Round127Research.hpp','PaperExternalGiniTree.hpp'):
        assert key in current and key in old
    assert metered('default_CLI_help','build',[default/'ExactEBRP.exe','--help'],30)==0
    assert metered('gurobi_CLI_help','build',[target/'ExactEBRP.exe','--help'],30)==0
    write(OUT/'engineering/cmake_delivery.json',dict(PASS=True,UTC=utc(),commands=[list(map(str,c)) for c in commands],
        CMake_SHA256=sha(cmake),CMakeLists_SHA256=sha(ROOT/'CMakeLists.txt'),delivery_research_PE_SHA256=sha(target/'Round162Research.exe'),
        default_no_solver_PE_SHA256=sha(default/'ExactEBRP.exe'),gurobi_production_PE_SHA256=sha(target/'ExactEBRP.exe'),
        scope_test_PE_SHA256=sha(target/'Round162ScopeTests.exe'),
        Optimize=0,performance_sample=False,measured_PE_unchanged=True,
        stable_entry_byte_checks=protected,inherited_GNU_policy=True,parallel_build_jobs=1,
        default_off='EXACT_EBRP_BUILD_ROUND162_RESEARCH defaults OFF; stable CLI has no new enabled path'))

if __name__=='__main__':check(*sys.argv[1:])
