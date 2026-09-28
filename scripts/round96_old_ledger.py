"""Small optimizer-free mechanism extraction. Does not replay large journals."""
import csv
from collections import Counter
from pathlib import Path
from round96_prepare import ROOT, OUT, read,write,sha

def rows(p):
    with p.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))

def main():
    summary=read(ROOT/'results/unified_exact_round94/formal_evidence_summary_v4.json')
    sources=[dict(role=r['role'],arm=r['arm'],destination=ROOT/r['destination']) for r in summary['rows'] if r['arm']!='P-GRB']
    d6=read(ROOT/'results/unified_exact_round90/runner_lp_g_d6_tail/identity.json')
    sources += [dict(role='D6',arm=r['arm'],destination=Path(r['destination'])) for r in d6['launches']]
    result=[]
    for src in sources:
        ext=src['destination']/'external';logs={};manifest={}
        for name in ['round90_lp_g_split_choice.csv','c6_split_decision_ledger.csv','native_target_ledger.csv','paper_optimize_ledger.csv','paper_leaf_ledger.csv','split_decision_ledger.csv','adaptive_mass_decision_ledger.csv']:
            p=ext/name
            if p.exists(): logs[name]=rows(p);manifest[name]=dict(path=str(p),sha256=sha(p),rows=len(logs[name]))
        # Preserve exact small event ledgers and their headers, without causal inference.
        choices=logs.get('round90_lp_g_split_choice.csv',[])
        calls=logs.get('paper_optimize_ledger.csv',[])
        result.append(dict(role=src['role'],arm=src['arm'],manifest=manifest,
            proposal_count=sum(r['phase']=='proposal' for r in choices),
            phases=dict(Counter(r['phase'] for r in choices)),
            realized_statuses=dict(Counter(r['completion_status'] for r in choices if r['phase']=='realized')),
            optimize_kinds=dict(Counter(r['solve_kind'] for r in calls)),
            optimize_native_seconds=sum(float(r['solver_runtime']) for r in calls),
            ledgers=logs))
    write(OUT/'old_ledger_mechanisms_v2.json',dict(optimizer_calls=0,rows=result,
        caveat='Proposals, child LPs, AM, native targets and atomic replacement differ; times do not identify a causal tree-size effect.'))

if __name__=='__main__':main()
