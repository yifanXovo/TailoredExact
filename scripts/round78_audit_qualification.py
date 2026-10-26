"""Read-only qualification evidence check; writes one new immutable audit."""
import collections
import csv
import re
import sys
import time
from pathlib import Path
from round78_qualify import ROOT,OUT,read,write,sha

def main():
    version=sys.argv[1];started=time.perf_counter()
    destination=OUT/f'qualification_{version}_audit.json'
    assert not destination.exists()
    build=ROOT/'build/round78'/version;q=read(OUT/f'qualification_{version}.json')
    assert len(q['attempts'])==3
    for record in q['attempts']:assert sha(ROOT/record['log'])==record['log_sha256']
    text=(build/'tests.log').read_text(encoding='utf-8')
    passed='100% tests passed, 0 tests failed out of 60' in text
    assert passed==all(a['returncode']==0 for a in q['attempts'])
    ledger_records=[];logs=collections.Counter()
    for path in sorted(build.rglob('paper_optimize_ledger.csv')):
        with path.open(encoding='utf-8',newline='') as stream:rows=list(csv.DictReader(stream))
        ledger_records.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path),calls=len(rows)))
        for row in rows:
            assert int(row['optimize_return_code'])==0
            logs[Path(row['native_log'])]+=1
    native_dir=Path(re.search(r'Native qualification: 3 Optimize calls;.*evidence "([^"]+)"',text)[1].replace('\\\\','\\'))
    native_logs=[]
    for path in sorted(native_dir.glob('*.log')):
        count=path.read_text(encoding='utf-8',errors='replace').count('Optimize a model')
        if count:native_logs.append(dict(path=str(path),calls=count,sha256=sha(path)));logs[path]+=count
    assert sum(row['calls'] for row in native_logs)==3
    checked=[]
    for path,count in logs.items():
        contents=path.read_text(encoding='utf-8',errors='replace')
        assert contents.count('Optimize a model')==count,(str(path),count)
        assert 'Gurobi Optimizer version 13.0.2' in contents
        checked.append(dict(path=str(path),calls=count,sha256=sha(path)))
    total=sum(logs.values());ceiling=q['identity']['allowed_optimize_calls']
    assert total<=ceiling
    failed_cli=[]
    for path in build.glob('round78_balanced_cli_*/*/result.json'):
        result=read(path)
        if not result['strict_certified_original_problem']:
            failed_cli.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path),status=result['status'],
                reason=result.get('external_gini_tree_failure_reason'),UB=result['upper_bound']))
    if passed:assert not failed_cli
    oracle=re.search(r'Round78 balanced structural:.*',text)
    oracle=oracle[0] if oracle else None
    if passed:assert oracle
    report=dict(version=version,passed=passed,tests_total=60,tests_passed=len(re.findall(r'\d+/60 Test .*Passed',text)),
        source_commit=q['identity']['source_commit'],binary_sha256=sha(build/'ExactEBRP.exe'),
        actual_optimize_calls=total,allowed_optimize_calls=ceiling,ledgers=ledger_records,
        native_fixture_logs=native_logs,all_native_logs=checked,failed_cli=failed_cli,oracle=oracle,
        full_qualification_wall_seconds=sum(a['wall_seconds'] for a in q['attempts']),
        qualification_sha256=sha(OUT/f'qualification_{version}.json'),audit_script_sha256=sha(__file__),
        offline_audit_seconds=time.perf_counter()-started)
    write(destination,report)
    print({k:report[k] for k in ['version','passed','tests_passed','actual_optimize_calls','full_qualification_wall_seconds','oracle']})

if __name__=='__main__':main()
