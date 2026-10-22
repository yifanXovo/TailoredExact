"""One saved R129 B20 coverage example; never used by a formal producer."""
from round130_common import *
import csv
import round108_reader as core

def run():
    prior=WORK/'worktrees/round129/results/unified_exact_round129'
    a=next(x for x in csv.DictReader((prior/'arms.csv').open()) if x['id']=='UC-B20-B' and x['seed']=='0' and x['method']=='MS2')
    d=Path(a['destination']);ext=d/'external'
    records={n:list(csv.DictReader((ext/n).open())) for n in ['paper_tree_events.csv','paper_leaf_ledger.csv','split_decision_ledger.csv','initial_decomposition_ledger.csv','lp_status_ledger.csv','paper_optimize_ledger.csv']}
    calls={}
    for event in read(d/'observations.json'):
        c=event['payload']
        if c['kind']!='call' or c['leaf'] in calls:continue
        m=core.lp_model(Path(c['model_path']))
        penalty=[rhs for terms,sense,rhs in m['rows'] if sense=='>=' and len(terms)==20 and all(n.startswith('e_') for n,v in terms)]
        lower=max(penalty) if penalty else None
        La=c['lower_g']+.15*lower if lower is not None else None
        calls[c['leaf']]=dict(scope=[c['lower_g'],c['upper_g']],cutoff=c['cutoff'],model_SHA=c['model_sha256'],
            sentinel_rows=sum(not t and s=='<=' and b==-1 for t,s,b in m['rows']),penalty_lower=lower,
            analytic_region_lower=La,analytic_minus_cutoff=La-c['cutoff'] if La is not None else None)
    write(OUT/'R129_B20_coverage_example.json',dict(source_round=129,input='UC-B20-B',seed=0,method='MS2',
        initial_H_objective=read(ext/'initial_witness.json')['objective'],
        source_files={n:sha(ext/n) for n in records},source_saved_arm=str(d),records=records,actual_call_models=calls,
        only_old_read_only_example=True,formal_Start_or_optimum_injection=False))
    lines=['# Saved R129 B20 coverage example','',
        'This is the original E2 MS2 Seed0 diagnostic, not a Round130 formal observation. Its own H already attains F=0.5773330699702928; that feasible witness alone proves no optimality. Three subsequent natural splits and their actual closure sources provide the coverage. No old solution or bound enters a Round130 producer.','']
    lines+=['The root is `[0,0.5773330699702928]` with the same-run linear cutoff `F_model<=0.5773330699702928`. Its complete LP lower bound is 0.4790764218520756.','',
        '| Natural split parent | Split point | Actual trigger |','| --- | ---: | --- |']
    leaves={r['leaf_id']:r for r in records['paper_leaf_ledger.csv']}
    for r in records['split_decision_ledger.csv']:
        if r['split']!='1':continue
        midpoint=leaves[r['parent_id']+'.0']['gamma_U']
        lines.append(f"| {r['parent_id']} | {midpoint} | {r['reason']} |")
    lines+=['','| Final coverage member | True-G interval | Actual disposition/source | Proof-closure row |','| --- | --- | --- | ---: |']
    for r in leaves.values():
        if r['status'] not in ['empty','closed']:continue
        fact=calls[r['leaf_id']]
        lines.append(f"| {r['leaf_id']} | [{r['gamma_L']}, {r['gamma_U']}] | {r['status']}: {r['closure_source']} | {fact['sentinel_rows']} |")
    sentinel=[(leaf,fact) for leaf,fact in calls.items() if fact['sentinel_rows']]
    premises='; '.join(f"{leaf}: penalty floor {fact['penalty_lower']:.17g}, L_a-c={fact['analytic_minus_cutoff']:.17g}" for leaf,fact in sentinel)
    lines+=['','The two models containing the semantic closure row must be interpreted through their retained interval penalty lower bound and cutoff, rather than as inclusive physical infeasibility. Exact `L_a>c` excludes `F<=c`; exact equality excludes strict improvement only; a bound slightly below c retains that bound under the original numerical policy. The actual binary64 premises are '+premises+'. Both differences are positive here. The JSON preserves their full values. The other empty side has no such row. The remaining terminal MIP returns OPTIMAL with bound 0.5773330699702926; the tiny signed gap is retained.','']
    lines+=['The detailed immutable tree events, LP dispositions, root scope, all closed-side reasons and final terminal are indexed in R129_B20_coverage_example.json. Infeasibility of a model containing a semantic proof-closure row is interpreted only on its stated improving domain and original numerical policy; it is not inclusive-root physical infeasibility. Split exposure does not establish its net computational contribution.','']
    (OUT/'R129_B20_coverage_example.md').write_text('\n'.join(lines),encoding='utf-8')
    print('OLD_COVERAGE_EXAMPLE_WRITTEN_WITHOUT_OPTIMIZE')
if __name__=='__main__':run()
