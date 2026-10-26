"""Bind a completed C++ order micro and its exact diagnostic executable."""
import json
import subprocess
from round96_prepare import ROOT, OUT, sha, read, write

def main():
    folder=ROOT/'build/research/round96-multi-quantity'
    receipt=read(OUT/'route_order_micro.receipt.json')
    build=read(OUT/'route_order_build_v2.receipt.json')
    assert receipt['exit_code']==0 and build['exit_code']==0
    text=(OUT/'route_order_micro.log').read_text(encoding='utf-8-sig').strip()
    micro=json.loads(text)
    assert micro['initial_F']==micro['pair_F']==micro['old_F'] and micro['order_F']==0
    assert micro['order_moves']>0 and micro['quantities']>0 and micro['optimizer_calls']==0
    paths=subprocess.check_output(['git','ls-files','src','include','CMakeLists.txt'],cwd=ROOT,text=True).splitlines()
    paths += ['tests/round96_route_order_tests.cpp','tests/round96_route_order_diagnostic.cpp',
              'scripts/round96_order_diagnostic.py','scripts/round96_order_gate.py',
              'results/unified_exact_round96/route_order_protocol.md']
    cache=(folder/'CMakeCache.txt').read_text()
    assert 'CMAKE_BUILD_TYPE:STRING=\n' in cache
    write(OUT/'route_order_build_gate.json',dict(qualified=True,micro_result=micro,
        binary_sha256=sha(folder/'Round96RouteOrderDiagnostic.exe'),test_sha256=sha(folder/'Round96RouteOrderTests.exe'),
        source_hashes={path:sha(ROOT/path) for path in paths},cmake_cache_sha256=sha(folder/'CMakeCache.txt'),
        micro_receipt_sha256=sha(OUT/'route_order_micro.receipt.json'),
        build_receipt_sha256=sha(OUT/'route_order_build_v2.receipt.json'),production_integrated=False,
        optimizer_calls=0))

if __name__=='__main__':main()
