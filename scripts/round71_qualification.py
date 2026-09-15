"""Record the completed qualification, including both independently counted CLIs."""
import ast,csv,json,re
from pathlib import Path
import round71_research as run

def main():
    destination=run.OUT/'qualification.json'
    assert not destination.exists() and not (run.OUT/'active_run.lock').exists()
    entries=[json.loads(x) for x in (run.OUT/'preflight_processes.jsonl').read_text(encoding='utf-8').splitlines()]
    completed=[e for e in entries if e['event']=='completion']
    assert len(completed)==3 and all(e['returncode']==0 for e in completed)
    for e in completed:assert run.sha(run.ROOT/e['output'])==e['sha256']
    tests=(run.BUILD/'tests.log').read_text(encoding='utf-8')
    assert '100% tests passed, 0 tests failed out of 49' in tests
    assert run.sha(run.BUILD/'test_1.log')==run.sha(run.BUILD/'tests.log')
    cli=[]
    for name in ['Round70DescentCliTests','Round71InterrouteCliTests']:
        match=re.search(name+r': real CLI certificate5/24; Optimize calls=(\d+); artifacts=([^\r\n]+)',tests)
        assert match
        folder=Path(match[2]);ledger=folder/'external/paper_optimize_ledger.csv'
        count=len(list(csv.DictReader(ledger.open(encoding='utf-8-sig'))))
        assert count==int(match[1]) and count>0
        result=run.read(folder/'result.json')
        assert result['strict_certified_original_problem'] and abs(result['upper_bound']-5/24)<=1e-7
        cli.append(dict(name=name,artifacts=str(folder),optimizer_calls=count,
            ledger_sha256=run.sha(ledger),result_sha256=run.sha(folder/'result.json')))
    cross=re.search(r'Inter-route checks=(\d+) accepted moves=(\d+); no optimizer calls',tests)
    assert cross and int(cross[1])>0 and int(cross[2])>0
    files=[run.ROOT/'CMakeLists.txt']+[p for d in ['src','include','tests'] for p in (run.ROOT/d).rglob('*')
        if p.suffix in ['.cpp','.hpp','.h','.c','.cmake']]
    for p in (run.ROOT/'scripts').glob('*round71*.py'):ast.parse(p.read_text(encoding='utf-8'),filename=str(p))
    run.write(destination,dict(final_ctest_passed_tests=49,final_binary_sha256=run.sha(run.BUILD/'ExactEBRP.exe'),
        tests_sha256=run.sha(run.BUILD/'tests.log'),qualified_source={str(p.relative_to(run.ROOT)):run.sha(p) for p in files},
        configure_build_test_attempts=completed,preflight_total_wall_seconds=sum(e['wall_seconds'] for e in completed),
        new_interroute_unit_optimizer_calls=0,unit_cross_route_checks=int(cross[1]),unit_cross_route_moves=int(cross[2]),
        round68_native_start_unit_optimizer_calls=3,native_cli_tests=cli,
        total_qualification_native_optimizer_calls=3+sum(x['optimizer_calls'] for x in cli),
        native_test_call_scope='Round68 unchanged fixture asserts runtime count3; both actual CLI ledgers independently counted. Other tests have no native Optimize entry.',
        inherited_ctest_tests=0,affinity_qualification_sha256=run.sha(run.OUT/'affinity_qualification.json'),
        affinity_qualification_inherited_from='results/unified_exact_round70/revision2/affinity_qualification.json',
        new_affinity_qualification_runs=0,script_sha256=run.sha(__file__)))
    print('Qualified49 new tests, native calls',3+sum(x['optimizer_calls'] for x in cli),
        'source files',len(files),'binary',run.sha(run.BUILD/'ExactEBRP.exe'))

if __name__=='__main__':main()
