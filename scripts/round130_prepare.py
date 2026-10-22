"""Build the read-only exporter and freeze original-byte structural checks."""
from round130_common import *
from round130_build import FLAGS,CHANGED

def exporter():
    args=[COMPILER,*FLAGS,ROOT/'scripts/round130_export.cpp',*[BUILD/(s+'.o') for s in CHANGED],ARCHIVE,'-o',EXPORTER]
    assert metered('build_exporter_01','build',args)==0
    write(OUT/'exporter_identity.json',dict(path=str(EXPORTER),SHA=sha(EXPORTER),Optimize=0,source_SHA=sha(ROOT/'scripts/round130_export.cpp')))

def freeze():
    assert not (OUT/'E3_frozen.json').exists()
    assert read(OUT/'qualification/zero_qualification.json')['passed']
    assert read(OUT/'qualification/native_qualification.json')['passed']
    build=read(OUT/'E3_build.json')
    assert build['source_bindings']==source_bindings() and build['PE_SHA']==sha(E3)
    assert sha(E2)==E2_SHA and sha(DLL)==DLL_SHA
    write(OUT/'E3_frozen.json',dict(build,UTC=utc(),exporter_SHA=sha(EXPORTER),predecessor_PE_SHA=E2_SHA,final_qualification_pending=False,
        scientific_identity='S2 = E2 --round127-mode ms2; E3 only adds off-by-default s2-root and PS evidence readback',
        protocol_SHA=sha(OUT/'experiment_manifest.json'),input_manifest_SHA=sha(OUT/'input_manifest.json'),
        qualification_complete=True,algorithm_or_parameters_may_change_after_formal=False))
if __name__=='__main__':{'exporter':exporter,'freeze':freeze}[sys.argv[1]]()
