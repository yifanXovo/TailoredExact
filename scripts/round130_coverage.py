"""One saved R129 B20 coverage example; never used by a formal producer."""
from round130_common import *
import csv

def run():
    prior=WORK/'worktrees/round129/results/unified_exact_round129'
    a=next(x for x in csv.DictReader((prior/'arms.csv').open()) if x['id']=='UC-B20-B' and x['seed']=='0' and x['method']=='MS2')
    d=Path(a['destination']);ext=d/'external'
    records={n:list(csv.DictReader((ext/n).open())) for n in ['paper_tree_events.csv','paper_leaf_ledger.csv','split_decision_ledger.csv','initial_decomposition_ledger.csv','lp_status_ledger.csv','paper_optimize_ledger.csv']}
    write(OUT/'R129_B20_coverage_example.json',dict(source_round=129,input='UC-B20-B',seed=0,method='MS2',
        initial_H_objective=read(ext/'initial_witness.json')['objective'],
        source_files={n:sha(ext/n) for n in records},source_saved_arm=str(d),records=records,
        only_old_read_only_example=True,formal_Start_or_optimum_injection=False))
    lines=['# Saved R129 B20 coverage example','',
        'This is the original E2 MS2 Seed0 diagnostic, not a Round130 formal observation. Its own H already attains F=0.5773330699702928; that feasible witness alone proves no optimality. Three subsequent natural splits and their actual closure sources provide the coverage. No old solution or bound enters a Round130 producer.','']
    for n in ['initial_decomposition_ledger.csv','split_decision_ledger.csv','paper_leaf_ledger.csv']:
        rows=records[n];lines+=['## '+n,'']
        if rows:
            keys=list(rows[0]);keep=[k for k in keys if not any(s in k.lower() for s in ['path','file','sha','seconds','runtime'])]
            lines+=['| '+' | '.join(keep)+' |','| '+' | '.join('---' for _ in keep)+' |']
            lines+=['| '+' | '.join(str(r[k]).replace('|','/') for k in keep)+' |' for r in rows]
        lines+=['']
    lines+=['The detailed immutable tree events, LP dispositions, root scope, all closed-side reasons and final terminal are indexed in R129_B20_coverage_example.json. Infeasibility of a model containing a semantic proof-closure row is interpreted only on its stated improving domain and original numerical policy; it is not inclusive-root physical infeasibility. Split exposure does not establish its net computational contribution.','']
    (OUT/'R129_B20_coverage_example.md').write_text('\n'.join(lines),encoding='utf-8')
    print('OLD_COVERAGE_EXAMPLE_WRITTEN_WITHOUT_OPTIMIZE')
if __name__=='__main__':run()
