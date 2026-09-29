"""Read-only final identity/completeness audit. No solver/build or rewriting raw."""
import json
import time
from pathlib import Path
import round96_external as external
import round96_primal as primal
from round96_prepare import ROOT,OUT,read,write,sha

def main():
    tick=time.perf_counter();external.ensure_idle();primal.build_identity()
    assert external.source_bindings()==read(OUT/'external/identity.json')['bindings']
    assert sha(ROOT/external.BIN)==external.SHA
    records=[];normal=0;interrupted=0
    for campaign,count in [('external_v2',18),('primal_v2',12)]:
        identity=read(OUT/campaign/'identity.json')
        rows=[json.loads(s) for s in (OUT/campaign/'summary.jsonl').read_text().splitlines()]
        assert [r['number'] for r in rows]==list(range(1,count+1))
        for row,launch in zip(rows,identity['launches']):
            dest=Path(row['destination']);original=read(dest/'launch.json')
            for key in ['number','id','arm','command','cap_seconds','hard_stop_seconds','destination','panel']:
                assert original[key]==launch[key], (campaign,row['number'],key)
            assert sha(ROOT/launch['panel']['input_path'])==launch['panel']['input_sha256']
            audit_path=ROOT/row['audit_path'] if 'audit_path' in row else dest/'audit.json'
            audit=read(audit_path);assert row['audit_passed'] and audit['passed']
            assert row['completion']==read(dest/'completion.json') and row['endpoint']==audit['endpoint']
            assert row['completion']['within_cap']
            reason=row['completion']['stop_reason']
            if reason=='normal_return':normal+=1
            else:
                assert campaign=='external_v2' and row['number']==16 and reason=='whole_run_hard_stop'
                assert audit['administrative_hard_stop'] and not row['endpoint']['certificate']
                assert not (dest/'result.json').exists();interrupted+=1
            records.append(dict(campaign=campaign,number=row['number'],role=row['id'],arm=row['arm'],
                audit_path=audit_path.relative_to(ROOT).as_posix(),audit_sha256=sha(audit_path),
                completion_sha256=sha(dest/'completion.json'),launch_sha256=sha(dest/'launch.json'),
                certificate=row['endpoint']['certificate'],stop_reason=reason))
    assert (normal,interrupted)==(29,1)
    cost=read(OUT/'cost_report_complete/summary.json')
    assert (cost['completed_conservative_starts'],cost['native_calls'],cost['native_micro'])==(67,115,2)
    numeric=[]
    for name,count in [('derived_numeric_external_v2_complete.json',36),('derived_numeric_primal_v2_complete.json',28)]:
        result=read(OUT/name);assert result['passed'] and len(result['records'])==count
        assert all(r['changed_rows']==0 for r in result['records'])
        numeric.append(dict(path=name,sha256=sha(OUT/name),models=count))
    assert not read(OUT/'external/raw/16_H6_LP-G/audit.json')['passed']
    assert not read(OUT/'primal/raw/03_F5_ORDER-ON/audit.json')['passed']
    artifacts=['final_report.md','mathematical_algorithm.md','numerical_scope.md','old_ledger_report.md',
        'fixed_route_report.md','fixed_route_audit.json','route_order_admission.md','route_order_oracle.json',
        'primal_final_decision.md','primal_startup_comparison.json','h6_interruption_review.md','h6_review.md',
        'reproduce.md','external_report_complete/arms.csv','external_report_complete/pairs.csv',
        'primal_report_complete/arms.csv','primal_report_complete/pairs.csv',
        'external_v2/summary.jsonl','primal_v2/summary.jsonl','cost_report_complete/summary.json']
    write(OUT/'final_audit.json',dict(passed=True,optimizer_calls=0,paid_starts=0,
        normal_formal_returns=normal,administrative_hard_stops=interrupted,records=records,numeric=numeric,
        artifacts=[dict(path=p,sha256=sha(OUT/p)) for p in artifacts],
        source_sha256=sha(__file__),wall_seconds=time.perf_counter()-tick,
        scope='Identity and completeness checks over already independently audited evidence; not a new optimization or an independent-agent review.'))
    print(json.dumps(dict(passed=True,formal_arms=len(records),normal=normal,hard_stops=interrupted,
                         paid_starts=67,native_calls=115)))

if __name__=='__main__':main()
