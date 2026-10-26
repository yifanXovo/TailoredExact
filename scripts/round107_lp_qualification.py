"""Engineering-only semantic metadata regression against real canonical bytes."""
from round107_common import *

def run(name):
    d=OUT/'qualification'/name;d.mkdir(parents=True,exist_ok=False)
    files=[OUT/'qualification/cli01/external/models/L0_epoch_0_generation_1.lp']
    files+=sorted({Path(q['canonical_path']) for p in (OUT/'qualification/final03').rglob('requests.jsonl')
        for q in map(json.loads,p.read_text().splitlines()) if q['kind']=='LP' and q['verified_cutoff']>0})
    exe=BUILD/'Round107LpMetadataTests.exe'
    write(d/'plan.json',dict(layer='Pure canonical-byte parser regression, no solver',
        canonical_files={p.relative_to(ROOT).as_posix():sha(p) for p in files},
        source_SHA=sha(ROOT/'include/Round107LpMetadata.hpp'),test_SHA=sha(ROOT/'tests/round107_lp_metadata_tests.cpp'),
        Optimize=0,IIS=0,paid_starts=0))
    receipt(name+'_compile',['D:/msys64/ucrt64/bin/g++.exe','-std=c++17','-I',ROOT/'include',
        ROOT/'tests/round107_lp_metadata_tests.cpp','-o',exe],60,True)
    receipt(name+'_regression',[exe,*files],60,True)
    receipt(name+'_pure_build19',[BUILD/'Round107Tests.exe','pure',d/'scope'],60,True)
    write(d/'result.json',dict(passed=True,actual_F2_canonical=True,original_qualification_canonical_files=len(files),
        reordered_wrapped_signed_zero_terms=True,missing_malformed_nonfinite_rejected=True,
        Optimize=0,IIS=0,production_PE_SHA=sha(BUILD/'ExactEBRP.exe'),fixture_PE_SHA=sha(BUILD/'Round107Tests.exe')))
    print(json.dumps(dict(passed=True,canonical_files=len(files),Optimize=0)))

if __name__=='__main__':run(sys.argv[1])
