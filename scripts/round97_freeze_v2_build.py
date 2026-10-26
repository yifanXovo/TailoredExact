"""Bind the actual built/tested v2 source; no real qualification is implied."""
import ctypes
import json
import subprocess
from pathlib import Path
import round97_campaign_v2 as campaign
from round97_campaign_v2 import ROOT, OUT, BUILD, read, write, sha, ext


def main():
    ext.ensure_idle()
    assert not (OUT/'production_v2_identity.json').exists()
    engineering=OUT/'engineering'
    gates={}
    labels=['revision02_build01_configure','revision02_build01','revision02_micro_r9501',
            'revision02_micro_r9601','revision02_micro_r9701','revision02_reader_fixture01']
    for label in labels:
        folder=engineering/label
        receipt=read(folder/'receipt.json')
        assert receipt['exit_code']==0 and receipt['optimizer_calls']==0
        for name in ['receipt.json','launch.json','stdout.log','stderr.log']:
            path=folder/name
            gates[path.relative_to(ROOT).as_posix()]=sha(path)
    assert 'Round95 full-block source qualification ready' in (engineering/'revision02_micro_r9501/stdout.log').read_text()
    r96=json.loads((engineering/'revision02_micro_r9601/stdout.log').read_text())
    assert r96['order_F']==0 and r96['order_moves']>0 and r96['optimizer_calls']==0
    assert 'Round97 semantic micro checks passed; optimizer_calls=0' in (engineering/'revision02_micro_r9701/stdout.log').read_text()
    fixture=read(OUT/'revision02_reader_fixture.json')
    assert fixture['passed'] and fixture['optimizer_calls']==0
    assert fixture['reader_sha256']==sha(campaign.__file__)
    assert fixture['fixture_sha256']==sha(ROOT/'scripts/round97_v2_reader_fixture.py')
    assert len(fixture['witnesses'])==55 and fixture['event_start_matches_checked']==83 and fixture['hash_mutations_checked']==9
    paths=['results/unified_exact_round97/revision02_reader_fixture.json',
           'scripts/round97_v2_reader_fixture.py','scripts/round97_build_v2.py',
           'tests/round95_full_block_tests.cpp','tests/round96_route_order_tests.cpp',
           'tests/round97_native_closure_tests.cpp']
    for path in paths:gates[path]=sha(ROOT/path)
    for binary in ['Round95FullBlockTests.exe','Round96RouteOrderTests.exe','Round97NativeClosureTests.exe']:
        gates[(BUILD/binary).relative_to(ROOT).as_posix()]=sha(BUILD/binary)
    manifest=read(ROOT/'tmp/round97_revision02/manifest.json')
    assert manifest['applied']
    for path,expected in manifest['applied_source_hashes'].items():assert sha(ROOT/path)==expected,path
    current=campaign.bindings()
    old=read(OUT/'development01/identity.json')
    changes={p for p in set(current)|set(old['source_hashes']) if current.get(p)!=old['source_hashes'].get(p)}
    assert changes=={p for p in manifest['proposed_paths'] if p=='CMakeLists.txt' or p.startswith(('src/','include/'))}
    assert sha(ROOT/old['prereg']['candidate_binary'])==old['candidate_binary_sha256']
    cache=(BUILD/'CMakeCache.txt').read_text()
    assert 'CMAKE_BUILD_TYPE:STRING=\n' in cache and 'CMAKE_CXX_FLAGS:STRING=\n' in cache
    dll=Path('D:/gurobi1302/win64/bin/gurobi130.dll')
    api=ctypes.CDLL(str(dll));version=[ctypes.c_int() for _ in range(3)]
    api.GRBversion(*[ctypes.byref(v) for v in version])
    assert [v.value for v in version]==[13,0,2] and sha(dll)==old['dll_sha256']
    write(OUT/'production_v2_identity.json',dict(schema='round97-native-nonstart-v2-build',
        source_ref=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        source_hashes=current,binary_path=(BUILD/'ExactEBRP.exe').relative_to(ROOT).as_posix(),
        binary_sha256=sha(BUILD/'ExactEBRP.exe'),cmake_cache_sha256=sha(BUILD/'CMakeCache.txt'),
        compiler_version=subprocess.check_output(['D:/msys64/ucrt64/bin/g++.exe','--version'],text=True).splitlines()[0],
        build_type='',gurobi_dll_path=str(dll),gurobi_dll_sha256=sha(dll),gurobi_version=[v.value for v in version],
        micro_gates_passed=True,qualification_gate_hashes=gates,
        development01_analysis_sha256=sha(OUT/'development01_analysis/identity.json'),
        old_v1_binary_preserved=True,freeze_script_sha256=sha(__file__),
        real_v2_qualification_started=False,optimizer_calls=0))
    print('Frozen actual v2 build and passed micro/reader gates; real qualification still pending')


if __name__=='__main__':main()
