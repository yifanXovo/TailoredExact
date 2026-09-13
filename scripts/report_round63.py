"""Compact Round63 reporting. No solver; run full mode between timed queues."""
import argparse
import csv
import json
from pathlib import Path
import analyze_round63 as analysis
import round63_research as run
run.bind_runner()
ROOT,OUT,RAW=run.ROOT,run.OUT,run.RAW

def read(path):return json.loads(path.read_text(encoding='utf-8'))
def rows(path):return list(csv.DictReader(path.open(encoding='utf-8-sig',newline='')))
def value(x):
    if x is None:return '—'
    if isinstance(x,bool):return 'yes' if x else 'no'
    if isinstance(x,float):return f'{x:.6g}'
    return str(x)
def markdown(headers,data):
    return '| '+' | '.join(headers)+' |\n| '+' | '.join('---' for _ in headers)+' |\n'+''.join('| '+' | '.join(value(x) for x in r)+' |\n' for r in data)

def compact_tables(runs):
    result=['# Automatically generated measured tables\n',
        'Process wall includes setup and finalization. Uncertified wall is budget use, not time to solution. Fixed-F0 certificates have narrower scope than full original-problem certificates.\n']
    stages=list(dict.fromkeys(r['stage'] for r in runs if r.get('scope')))
    for stage in stages:
        selected=[r for r in runs if r.get('scope') and r['stage']==stage]
        result+=['\n## '+stage+'\n',markdown(['#','id','arm','cap','wall s','certificate','UB','LB','absolute gap','Work','calls','eligible'],[
            [r['number'],r['id'],r['arm'],r['cap'],r['wall'],r.get('fixed_interval_certificate',r.get('strict_certified_original_problem')),
             r['upper_bound'],r['lower_bound'],r['absolute_gap'],r.get('work'),r.get('optimizer_calls',1),r['performance_eligible']] for r in selected])]
    if (OUT/'pairs.csv').exists():
        result+=['\n## Predeclared dual-threshold decisions\n',markdown(['id','scope','baseline #','candidate #','baseline','candidate','decision'],[
            [p[k] for k in ['id','scope','baseline_number','candidate_number','baseline','candidate','decision']] for p in rows(OUT/'pairs.csv')])]
    (OUT/'measured_tables.md').write_text('\n'.join(result),encoding='utf-8')

def strength_tables():
    summary=[];supports=[]
    for path in sorted(RAW.glob('strength*/*/probe_result.json')):
        d=read(path);identity=path.parent.name;separated=rows(path.parent/'separation.csv')
        summary.append(dict(id=identity,**d))
        for arm in ['F0','explicit','simple','closure']:
            relevant=[r for r in separated if r['arm']==arm]
            if not relevant:continue
            # Closure's last completed inspected point, never assume closed.
            if arm=='closure':
                last=max(int(r['query']) for r in relevant);relevant=[r for r in relevant if int(r['query'])==last]
            for r in relevant:supports.append(dict(id=identity,**r))
    analysis.table('strength_summary.csv',summary);analysis.table('strength_supports.csv',supports)
    text=['# Resource strength diagnostics\n',markdown(['id','F0 LP','simple LP','explicit LP','last closure LP','closed','optimizer calls','maxflows','separation s','process s'],[
        [d[k] for k in ['id','F0','simple','explicit','closure','closed','optimizer_calls','maxflow_calls','separation_seconds','process_seconds']] for d in summary]),
        '\nAll values concern the original objective in the fixed F0 diagnostic LP. A residual violation at an optimal LP proves extra feasible-region strength; objective equality alone does not mean the extension is implied.\n',
        markdown(['id','sample','vehicle','proper/support size','max raw normalized violation','whole-set violation','max singleton violation'],[
            [r[k] for k in ['id','arm','vehicle','support_size','maximum_violation','all_violation','max_singleton_violation']] for r in supports])]
    (OUT/'strength_tables.md').write_text('\n'.join(text),encoding='utf-8')
    coupling=[]
    for path in sorted(RAW.glob('**/coupling_result.json')):
        d=read(path);coupling.append(dict(id=path.parent.name,**d))
    if coupling:analysis.table('coupling_summary.csv',coupling)

def audit_parameters():
    checked=[]
    for e in run.runner.entries():
        folder=ROOT/e['destination']
        if not e['charged'] or not (folder/'result.json').exists():continue
        r=read(folder/'result.json')
        if 'objective' not in r and r.get('schema')!='round50-fixed-interval-result-v1':continue
        fixed=r.get('schema')=='round50-fixed-interval-result-v1'
        if fixed:
            ledger=rows(folder/'certificate_ledger.csv')
            good=bool(ledger) and all(c['zero_gap_roundtrip']=='1' for c in ledger)
        elif e['arm']=='P-GRB':
            good=all(r.get('gurobi_'+n+'_effective')==v for n,v in [('threads',1),('seed',0),('presolve',-1),('mip_gap',0),('mip_gap_abs',0)])
        else:good=r.get('external_gini_tree_backend_parameter_roundtrip_valid')
        checked.append(dict(number=e['charged_number'],id=e['id'],arm=e['arm'],roundtrip_valid=good,
            evidence=str((folder/'result.json').relative_to(ROOT))))
    run.write(OUT/'parameter_verification.json',checked)
    return checked

def audit_outer_contract():
    records=[]
    for e in run.runner.entries():
        folder=ROOT/e['destination'];ledger=folder/'external/adaptive_mass_decision_ledger.csv'
        if not (folder/'completion.json').exists() or not ledger.exists():continue
        decisions=rows(ledger)
        for d in decisions:
            assert int(d['K0'])==1 and abs(float(d['tau'])-.08)<1e-14
        result=read(folder/'result.json')
        records.append(dict(number=e['charged_number'],id=e['id'],arm=e['arm'],
            actual_adaptive_decisions=len(decisions),actual_tau=.08 if decisions else None,
            inherited_compatibility_rho=result.get('c6_normalized_split_threshold'),
            distinction='first-class controller uses split_threshold; compatibility C6 rho is not its tau',
            evidence=str(ledger.relative_to(ROOT))))
    run.write(OUT/'outer_contract_verification.json',records)

def evidence_index():
    # Hash once after performance, never compete with optimizer timing. Keep
    # logs/binaries local; submit sparse rows and physically checked witnesses.
    index=[]
    for e in run.runner.entries():
        folder=ROOT/e['destination']
        for p in sorted(folder.rglob('*')):
            if not p.is_file():continue
            index.append(dict(number=e['charged_number'],id=e['id'],stage=e['stage'],arm=e['arm'],
                path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=run.sha(p)))
        for p in folder.glob('**/*.cuts.jsonl'):
            target=OUT/'cut_evidence'/str(e['charged_number'] or 'build')/p.relative_to(folder)
            target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(p.read_bytes())
    analysis.table('evidence_index.csv',index)
    return index

def main():
    p=argparse.ArgumentParser();p.add_argument('--index',action='store_true');a=p.parse_args()
    runs=analysis.summarize();compact_tables(runs);strength_tables();checked=audit_parameters();audit_outer_contract()
    print('parameter records',len(checked),'unverified',[r['number'] for r in checked if not r['roundtrip_valid']])
    if a.index:print('indexed',len(evidence_index()),'local files')
if __name__=='__main__':main()
