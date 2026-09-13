"""Read completed records only; full audits/indexing run between optimizer queues."""
import argparse
import csv
import json
import math
import re
from collections import Counter
from pathlib import Path
import analyze_round62 as inherited
from report_round62 import compare
import round64_research as run
run.bind()
ROOT,OUT,RAW=run.ROOT,run.OUT,run.RAW
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def rows(p):return list(csv.DictReader(p.open(encoding='utf-8-sig',newline='')))
def table(name,records):inherited.table(OUT/name,records)
def summary():
    inherited.ROOT=ROOT;inherited.OUT=OUT;inherited.RAW=RAW
    results=inherited.performance();entries=run.runner.entries()
    by_number={r['number']:r for r in results if r['charged']};calls=[]
    for e in entries:
        folder=ROOT/e['destination'];done=folder/'completion.json'
        if not done.exists():continue
        r=read(folder/'result.json') if (folder/'result.json').exists() else {}
        count=0;attempts=0;native=folder/'external/paper_optimize_ledger.csv'
        if e['charged']:
            if (folder/'native_calls.csv').exists():count=len(rows(folder/'native_calls.csv'))
            elif native.exists():
                records=rows(native);attempts=len(records)
                count=sum(bool(c['native_status']) or int(c['optimize_return_code'])!=-1 for c in records)
            elif e['arm']=='P-GRB':count=1
            elif r.get('external_gini_tree_optimize_count')==0:count=0
            elif r.get('schema')=='round50-fixed-interval-result-v1':count=1
            else:count=None
        calls.append(dict(number=e['charged_number'],charged=e['charged'],id=e['id'],arm=e['arm'],stage=e['stage'],
            optimizer_calls=count,backend_attempts=attempts or count,build_freeze=e.get('build_freeze')))
        if not e['charged']:continue
        result=by_number[e['charged_number']];result['optimizer_calls']=count;result['backend_attempts']=attempts or count
        result['build_freeze']=e.get('build_freeze');result['kind']=e['kind']
        result['performance_eligible']=result['performance_eligible'] and e['kind']=='performance' and result['returncode']==0 and result['within_budget'] and result.get('status') not in ['failed','engine_failed']
        mode=e['command'][e['command'].index('--round64-shared-mode')+1] if '--round64-shared-mode' in e['command'] else 'off'
        result['shared_mode']=mode;result['startup']='HGA-current-process' if e['arm']=='K1-H' or e['arm'].startswith('warm-') else 'official-default' if e['arm']=='P-GRB' else 'simple-current-process'
        if r and result.get('scope')=='full_original_problem':
            if count==0:result['native_statuses']='no native optimize';result['work']=0;result['nodes']=0
            result['initial_upper_bound']=r.get('initial_upper_bound')
            result['heuristic_seconds']=r.get('primal_heuristic_seconds',r.get('heuristic_elapsed_seconds'))
    table('runs.csv',results);table('optimizer_calls.csv',calls)
    charged=[e for e in entries if e['charged']]
    budget=dict(charged=len(charged),maximum=72,native_micro=sum(e['kind']=='native-micro' for e in charged),
        completed=sum(e['charged_number'] in by_number for e in charged),optimizer_calls=sum(c['optimizer_calls'] or 0 for c in calls),
        unknown_call_counts=[c['number'] for c in calls if c['charged'] and c['optimizer_calls'] is None],
        by_kind=dict(Counter(e['kind'] for e in charged)),by_cap=dict(Counter(str(e['cap_seconds']) for e in charged)),
        incomplete=[e['charged_number'] for e in charged if e['charged_number'] not in by_number],
        over_budget=[r['number'] for r in by_number.values() if not r['within_budget'] or r['watchdog']],
        failed=[r['number'] for r in by_number.values() if r['returncode'] or (r.get('status') or '').endswith('_failed') or r.get('status')=='failed'])
    assert budget['charged']<=72 and budget['native_micro']<=4;run.write(OUT/'budget.json',budget)
    groups={}
    for r in results:
        if r['charged'] and r['performance_eligible'] and r.get('scope'):
            groups.setdefault((r['id'],r['stage'],r['cap'],r['scope'],r['exe_sha256']),{})[r['arm']]=r
    comparisons=[]
    for group in groups.values():
        for base in ['off','cold-off','single-off','warm-off','K1-H','P-GRB']:
            if base not in group:continue
            for arm,candidate in group.items():
                if arm!=base and (base in ['K1-H','P-GRB'] or base=='off' or arm.rsplit('-',1)[0]==base.rsplit('-',1)[0]):
                    comparisons.append(compare(group[base],candidate))
        for prefix in ['','cold-','warm-','single-']:
            for a,b in [('q','sep'),('t','sep'),('sep','joint')]:
                if prefix+a in group and prefix+b in group:comparisons.append(compare(group[prefix+a],group[prefix+b]))
    links=OUT/'comparison_links.json'
    if links.exists():
        for link in read(links):
            if link['baseline'] in by_number and link['candidate'] in by_number:
                a,b=by_number[link['baseline']],by_number[link['candidate']]
                assert a['id']==b['id'] and a['performance_eligible'] and b['performance_eligible']
                pair=compare(a,b);pair['link_reason']=link['reason'];comparisons.append(pair)
    table('pairs.csv',comparisons)
    text=['# Round64 automatically generated endpoints\n',
          'Wall includes the complete charged process. Uncertified wall is budget use, not solution time. Fixed-F0 and full original-problem certificates have separate scopes.\n',
          '| # | Role | Stage | Arm | Cap | Wall | Certificate | UB | LB | Absolute gap | Work | Calls |',
          '|---|---|---|---|---:|---:|---|---:|---:|---:|---:|---:|']
    for r in results:
        if not r['charged'] or not r.get('scope'):continue
        cert=r.get('fixed_interval_certificate',r.get('strict_certified_original_problem'))
        vs=[r['number'],r['id'],r['stage'],r['arm'],r['cap'],r['wall'],cert,r['upper_bound'],r['lower_bound'],r['absolute_gap'],r.get('work'),r.get('optimizer_calls')]
        def fmt(v):return f'{v:.9g}' if isinstance(v,float) else str(v) if v is not None else 'unavailable'
        text.append('| '+' | '.join(fmt(v) for v in vs)+' |')
        print(r['number'],r['id'],r['arm'],round(r['wall'],3),cert,r['absolute_gap'])
    (OUT/'measured_tables.md').write_text('\n'.join(text)+'\n',encoding='utf-8');print('budget',budget)
    return results

def audit_contracts():
    parameters=[];outer=[];lifecycle=[];shapes=[]
    for e in run.runner.entries():
        folder=ROOT/e['destination']
        if not e['charged'] or not (folder/'completion.json').exists() or not (folder/'result.json').exists():continue
        r=read(folder/'result.json');native=folder/'external/paper_optimize_ledger.csv';calls=rows(native) if native.exists() else []
        for c in calls:lifecycle.append(dict(number=e['charged_number'],id=e['id'],arm=e['arm'],**c))
        applicable=True
        if r.get('schema')=='round50-fixed-interval-result-v1':valid=all(x['zero_gap_roundtrip']=='1' for x in rows(folder/'certificate_ledger.csv'))
        elif e['arm']=='P-GRB':valid=all(r.get('gurobi_'+n+'_effective')==v for n,v in [('threads',1),('seed',0),('presolve',-1),('mip_gap',0),('mip_gap_abs',0)])
        else:
            applicable=bool(calls) or r.get('external_gini_tree_optimize_count',0)>0
            valid=r.get('external_gini_tree_backend_parameter_roundtrip_valid') if applicable else None
        parameters.append(dict(number=e['charged_number'],id=e['id'],arm=e['arm'],applicable=applicable,valid=valid))
        if applicable:assert valid,'native parameter readback failed'
        decision=folder/'external/adaptive_mass_decision_ledger.csv'
        if decision.exists():
            decisions=rows(decision)
            for d in decisions:
                assert int(d['K0'])==1 and abs(float(d['tau'])-.08)<1e-14
                if 'infeasible' not in d['deterministic_reason']:
                    l,rr=float(d['g_L']),float(d['g_R']);assert 0<=l<=1 and 0<=rr<=1
                    assert math.isclose(float(d['S_AM']),min(l,rr)*(l+rr)/2,rel_tol=1e-10,abs_tol=1e-12)
            outer.append(dict(number=e['charged_number'],id=e['id'],arm=e['arm'],decisions=len(decisions),tau=.08,K0=1))
        for p in folder.glob('**/*.log'):
            content=p.read_text(encoding='utf-8',errors='replace')
            size=re.search(r'Optimize a model with (\d+) rows, (\d+) columns and (\d+) nonzeros',content)
            if not size:continue
            presolved=re.search(r'Presolved: (\d+) rows, (\d+) columns, (\d+) nonzeros',content)
            root=re.search(r'Root relaxation: objective ([\d.eE+\-]+), (\d+) iterations, ([\d.]+) seconds',content)
            shapes.append(dict(number=e['charged_number'],id=e['id'],arm=e['arm'],path=str(p.relative_to(ROOT)),
                **dict(zip(['rows','columns','nonzeros'],map(int,size.groups()))),
                presolved_rows=int(presolved[1]) if presolved else None,presolved_columns=int(presolved[2]) if presolved else None,
                presolved_nonzeros=int(presolved[3]) if presolved else None,root_objective=float(root[1]) if root else None,
                root_iterations=int(root[2]) if root else None,root_seconds=float(root[3]) if root else None))
    table('parameter_verification.csv',parameters);table('outer_contract_verification.csv',outer)
    table('native_lifecycle.csv',lifecycle);table('native_model_shapes.csv',shapes)

def index():
    records=[]
    for e in run.runner.entries():
        for p in sorted((ROOT/e['destination']).rglob('*')):
            if p.is_file():records.append(dict(number=e['charged_number'],charged=e['charged'],id=e['id'],arm=e['arm'],path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=run.sha(p)))
    table('evidence_index.csv',records);print('indexed',len(records),'local files')
def main():
    p=argparse.ArgumentParser();p.add_argument('--audit',action='store_true');p.add_argument('--index',action='store_true');a=p.parse_args();summary()
    if a.audit:audit_contracts()
    if a.index:index()
if __name__=='__main__':main()
