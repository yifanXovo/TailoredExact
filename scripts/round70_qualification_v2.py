"""Record the already completed build/test qualification; no optimizer launch."""
import ast,json
from pathlib import Path
import round70_research_v2 as run

def main():
    destination=run.OUT/'qualification.json'
    assert not destination.exists() and not (run.OUT/'active_run.lock').exists()
    entries=[json.loads(x) for x in (run.OUT/'preflight_processes.jsonl').read_text().splitlines()]
    completed=[e for e in entries if e['event']=='completion']
    assert len(completed)==3 and all(e['returncode']==0 for e in completed)
    for e in completed:assert run.sha(run.ROOT/e['output'])==e['sha256']
    tests=(run.BUILD/'tests.log').read_text()
    assert '100% tests passed, 0 tests failed out of 47' in tests
    assert run.sha(run.BUILD/'test_1.log')==run.sha(run.BUILD/'tests.log')
    files=[run.ROOT/'CMakeLists.txt']+[p for d in ['src','include','tests'] for p in (run.ROOT/d).rglob('*') if p.suffix in ['.cpp','.hpp','.h','.c','.cmake']]
    for p in (run.ROOT/'scripts').glob('*round70*.py'):ast.parse(p.read_text(encoding='utf-8'),filename=str(p))
    run.write(destination,dict(final_ctest_passed_tests=47,final_binary_sha256=run.sha(run.BUILD/'ExactEBRP.exe'),
        tests_sha256=run.sha(run.BUILD/'tests.log'),qualified_source={str(p.relative_to(run.ROOT)):run.sha(p) for p in files},
        configure_build_test_attempts=completed,preflight_total_wall_seconds=sum(e['wall_seconds'] for e in completed),
        new_descent_unit_optimizer_calls=0,round68_native_start_unit_optimizer_calls=3,
        real_cli_optimizer_calls=int(__import__('re').search(r'Round70DescentCliTests: real CLI certificate5/24; Optimize calls=(\d+)',tests)[1]),
        native_test_call_scope='Three calls explicitly counted in the Start qualification fixture; no invented total for all pre-existing native tests',
        inherited_ctest_tests=0,affinity_qualification_sha256=run.sha(run.OUT/'affinity_qualification.json'),
        script_sha256=run.sha(__file__)))
    print('Qualified47 fresh tests, source files',len(files),'binary',run.sha(run.BUILD/'ExactEBRP.exe'))

if __name__=='__main__':main()
