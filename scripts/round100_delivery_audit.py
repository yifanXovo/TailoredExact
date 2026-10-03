"""Read-only current bindings, budget and user-file audit; no native engine."""
import csv,time
from round100_common import *
from round100_campaign import helpers
from round100_idle import ensure_idle

def main():
    start=time.perf_counter();ensure_idle()
    campaigns=['development01','certification_CF01','certification_N201','holdout01']
    baseline=read(OUT/'baseline.json');user={p:sha(ROOT/p) for p in baseline['user_edit_sha256']}
    assert user==baseline['user_edit_sha256'],'preexisting user file changed'
    checks=[]
    for name in campaigns:
        identity=OUT/name/'identity.json';q=read(identity)
        assert q['source_hashes']==bindings() and q['helpers']==helpers()
        assert q['candidate_binary_sha256']==sha(BUILD/'ExactEBRP.exe')
        assert q['runner_sha256']==sha(ROOT/'scripts/round100_campaign.py')
        assert q['dll_sha256']==sha('D:/gurobi1302/win64/bin/gurobi130.dll')
        records=[json.loads(s) for s in (OUT/name/'summary.jsonl').read_text().splitlines()]
        assert len(records)==len(q['launches']) and all(r['audit_passed'] for r in records)
        for a,r in zip(q['launches'],records):
            assert sha(ROOT/a['panel']['input_path'])==a['panel']['input_sha256']
            assert r['completion']['returncode']==0 and r['completion']['stop_reason']=='normal_return'
        checks.append(dict(campaign=name,identity_sha256=sha(identity),complete_arms=len(records),
            certificates=sum(r['endpoint']['certificate'] for r in records),passed=True))
    summary=read(OUT/'complete_results_final/summary.json');protocol=read(OUT/'protocol.json')
    assert summary['actual_starts']<=protocol['max_billed_starts'] and summary['conservative_outer_solver_seconds']<=protocol['max_outer_seconds']
    assert summary['unknown_actual_outer_processes']==summary['failed_started_processes']==[]
    with (OUT/'complete_results_final/cost_failures.csv').open(newline='',encoding='utf-8') as f:costs=list(csv.DictReader(f))
    assert sum(int(r['experimental_starts']) for r in costs)==summary['actual_starts']==33
    assert sum(int(r['optimizer_calls']) for r in costs)==summary['actual_optimizer_calls']==99
    assert abs(sum(float(r['outer_seconds']) for r in costs)-summary['outer_solver_seconds'])<1e-6
    engineering=[]
    for folder in sorted((OUT/'engineering').iterdir()):
        if not folder.is_dir() or not (folder/'receipt.json').exists():continue
        r=read(folder/'receipt.json');count=r.get('optimizer_calls')
        if count is None:
            count=read(folder/'actual_calls_supplement.json')['actual_optimizer_calls']
        assert count==0
        engineering.append(dict(label=folder.name,outer_seconds=r['outer_seconds'],exit_code=r['exit_code'],
            stop_reason=r['stop_reason'],actual_optimizer_calls=count,receipt_sha256=sha(folder/'receipt.json')))
    write(OUT/'engineering_summary.json',dict(completed_timed_receipts=engineering,
        receipt_seconds=sum(r['outer_seconds'] for r in engineering),optimizer_calls=0,
        scope='pure engineering only, excluded from solver budget; failed measurement01 retained; other unmetered text/read operations are not included in this receipt-time sum'))
    write(OUT/'delivery_validation.json',dict(passed=True,optimizer_calls=0,current_production_bindings_unchanged=True,
        user_edit_sha256=user,campaigns=checks,actual_starts=summary['actual_starts'],actual_optimizer_calls=summary['actual_optimizer_calls'],
        charged_outer_seconds=summary['outer_solver_seconds'],budget_passed=True,
        binary_sha256=sha(BUILD/'ExactEBRP.exe'),dll_sha256=sha('D:/gurobi1302/win64/bin/gurobi130.dll'),
        source_phase_commit='b5d6d83bb8fc74682de6f1f6862c2e687712f4cf',audit_script_sha256=sha(__file__),
        read_only_audit_seconds=time.perf_counter()-start,
        scope='executor metadata/self-audit; not the independent review or a native-search reproduction'))
    print(json.dumps(dict(passed=True,arms=sum(c['complete_arms'] for c in checks),certificates=sum(c['certificates'] for c in checks),
        billed_starts=summary['actual_starts'],seconds=summary['outer_solver_seconds'],Optimize=0)))

if __name__=='__main__':main()
