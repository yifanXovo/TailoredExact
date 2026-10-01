"""Verify committed compact results and original physical routes; no Gurobi."""
import csv
from round98_common import *
import analyze_round61 as physical

def main():
    physical.ROOT=ROOT
    target=OUT/'compact_evidence01'
    with (target/'witness_index.csv').open(newline='',encoding='utf-8') as f:index=list(csv.DictReader(f))
    with (OUT/'complete_results/runs.csv').open(newline='',encoding='utf-8') as f:runs=list(csv.DictReader(f))
    assert len(index)==len(runs)==30
    by_key={(r['campaign'],int(r['number'])):r for r in runs}
    for row in index:
        path=ROOT/row['bundle'];assert sha(path)==row['bundle_sha256']
        b=read(path);r=by_key[b['campaign'],b['number']]
        assert sha(ROOT/b['panel']['input_path'])==r['input_sha256']==row['input_sha256']
        checked=physical.physical(b['panel'],b['physical_witness'])
        assert checked['original_T_feasible'] and abs(checked['F']-float(r['U']))<1e-7
        e=b['qualified_endpoint'];assert abs(e['L']-float(r['L']))<1e-12
        assert e['certificate']==(r['certificate']=='True')
        assert b['original_audit']['passed']==(r['original_audit_passed']=='True')
        if b['exact_recovery']:assert b['number']==14 and b['campaign']=='development02'
    paid=read(target/'paid_receipts.json');summary=read(OUT/'complete_results/summary.json')
    assert len(paid)==summary['actual_starts']==75
    assert sum(int(p['cost']['optimizer_calls']) for p in paid)==summary['actual_optimizer_calls']==194
    assert abs(sum(float(p['cost']['outer_seconds']) for p in paid)-summary['outer_solver_seconds'])<1e-7
    print('PASS: 30 physical endpoint witnesses, qualified result correspondence, 75 receipts / 194 Optimize. Zero native launches.')

if __name__=='__main__':main()
