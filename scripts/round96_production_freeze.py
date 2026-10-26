"""One-shot new-build identity for primal OFF/ON/P; no optimizer invocation."""
import ctypes as ct
import subprocess
from round96_prepare import ROOT,OUT,read,write,sha

def main():
    binary=ROOT/'build/research/round96-route-order/ExactEBRP.exe'
    cli=read(OUT/'route_order_cli/passed.json');assert cli['passed'] and cli['binary_sha256']==sha(binary)
    assert read(OUT/'route_order_production_build.receipt.json')['exit_code']==0
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    paths=subprocess.check_output(['git','ls-files','src','include','CMakeLists.txt'],cwd=ROOT,text=True).splitlines()
    for path in paths:
        import hashlib
        original=subprocess.check_output(['git','show',commit+':'+path],cwd=ROOT)
        assert hashlib.sha256(original).hexdigest()==sha(ROOT/path),path
    dll=ROOT.__class__('D:/gurobi1302/win64/bin/gurobi130.dll');api=ct.CDLL(str(dll))
    vals=[ct.c_int() for _ in range(3)];api.GRBversion(*[ct.byref(x) for x in vals])
    version=[x.value for x in vals];assert version==[13,0,2]
    cache=ROOT/'build/research/round96-route-order/CMakeCache.txt'
    assert 'CMAKE_BUILD_TYPE:STRING=\n' in cache.read_text()
    write(OUT/'production_build_identity.json',dict(source_ref=commit,binary_path=binary.relative_to(ROOT).as_posix(),
        binary_sha256=sha(binary),source_hashes={path:sha(ROOT/path) for path in paths},
        gurobi_dll_path=str(dll),gurobi_dll_sha256=sha(dll),gurobi_version=version,
        cmake_cache_sha256=sha(cache),compile_flags='blank build type; no fast-math; same gcc toolchain',
        primal_rule_sha256=sha(OUT/'route_order_admission.md'),plan_sha256=sha(OUT/'primal_followup_plan.md'),
        cli_gate_sha256=sha(OUT/'route_order_cli/passed.json'),optimizer_calls=0,
        scope='New common OFF/ON/P build, distinct from frozen R90 LP-G external confirmation. No performance claim.'))

if __name__=='__main__':main()
