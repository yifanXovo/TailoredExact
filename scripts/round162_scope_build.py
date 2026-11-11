"""Compile and run the new C++ scope interface test, using an offline paid source."""
from round162_common import *
from round153_build import COMPILER,SYSTEM

def check():
    assert not budget()['unclosed'];m=read(OUT/'complete_candidate_manifest.json');target=BUILD/'scope_qualification';target.mkdir(exist_ok=False)
    source=ROOT/'tests/round162_scope_tests.cpp';digest=sha(source)
    assert metered('compile_scope_test','build',[COMPILER,*m['flags'],'-c',source,'-o',target/'test.o'],300)==0
    objects={**m['objects'],**m['added_objects']};reused=[p for p in objects if Path(p).stem!='main']
    for p in reused:assert sha(p)==objects[p]
    executable=target/'Round162ScopeTests.exe'
    command=[COMPILER,target/'test.o',*reused,m['archive']['path'],DLL,*SYSTEM,'-o',executable]
    assert metered('link_scope_test','build',command,180)==0 and sha(source)==digest
    folder=OUT/'inputs/N-B35-S';p=read(folder/'source.json')['panel']
    args=[executable,folder/'instance.txt',p['T_seconds'],p['pickup_seconds'],p['drop_seconds'],p['lambda'],folder/'parent.txt',
        OUT/'runs/N-B35-S_C_MIP_v1',OUT/'qualification/scope']
    assert metered('scope_interface','verification',args,120)==0
    write(OUT/'engineering/scope_test_build.json',dict(UTC=utc(),PASS=True,PE_SHA256=sha(executable),source_SHA256=digest,
        source=source.relative_to(ROOT).as_posix(),source_CPP_manifest=sha(OUT/'complete_candidate_manifest.json'),Optimize=0))

if __name__=='__main__':check()
