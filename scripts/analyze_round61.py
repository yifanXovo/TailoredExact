"""Recompute compact Round61 tables and independent physical witness checks."""
import ast
import csv
import json
import math
import re
import shutil
from pathlib import Path
from round61_research import ROOT, OUT, RAW, panel, entries, sha, write

def read(path): return json.loads(path.read_text(encoding='utf-8'))
def rows(path):
    with path.open(encoding='utf-8',newline='') as f: return list(csv.DictReader(f))
def table(name,records):
    if not records: return
    fields=list(dict.fromkeys(k for row in records for k in row))
    with (OUT/name).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(records)

def physical(p,witness):
    text=(ROOT/p['instance_path']).read_text(encoding='utf-8')
    def vec(name):
        m=re.search(r'(?m)^\s*'+name+r'\s*=\s*(\[[^\n]*\])',text)
        return ast.literal_eval(m[1]) if m else []
    initial=vec('initial'); target=vec('target'); capacity=vec('capacities'); weights=vec('weights')
    points=vec('points'); n=len(initial)-1
    if not weights: weights=[0]+[1]*n
    if abs(max(weights[1:])-10)<=1e-6: weights=[v/10 for v in weights]
    # All frozen real instances use the parser's 1.5m/s Euclidean convention.
    if not points: raise RuntimeError('independent verifier needs explicit supported distance parser')
    head=text.splitlines()[0]; Q=ast.literal_eval(head[head.index('['):])
    y=list(initial); visited=set(); vehicles=set(); durations=[]; total_pickup=0; total_drop=0
    for route in witness['routes']:
        k=route['vehicle']; assert 0<=k<len(Q) and k not in vehicles; vehicles.add(k)
        nodes=route['nodes']; assert nodes[0]==nodes[-1]==0
        raw_ops=route['operations']; ops={}
        for op in raw_ops:
            i,pick,drop=(op['station'],op['pickup'],op['drop']) if isinstance(op,dict) else op
            assert i not in ops; ops[i]=(pick,drop)
        assert set(nodes[1:-1])==set(ops)
        travel=sum(math.hypot(points[a][0]-points[b][0],points[a][1]-points[b][1])/1.5
                   for a,b in zip(nodes,nodes[1:]))
        load=0; pickup=0; dropped=0
        for i in nodes[1:-1]:
            assert 1<=i<=n and i not in visited; visited.add(i)
            a,b=ops[i]; assert a>=0 and b>=0 and (a==0)!=(b==0) and int(a)==a and int(b)==b
            load+=a-b; assert 0<=load<=Q[k]; pickup+=a; dropped+=b
            y[i]+=b-a; assert 0<=y[i]<=capacity[i]
        duration=travel+(float(p['pickup_seconds'])+float(p['drop_seconds']))*pickup
        if 'duration' in route: assert abs(duration-route['duration'])<=1e-5
        durations.append(duration); total_pickup+=pickup;total_drop+=dropped
    ratios=[y[i]/target[i] for i in range(1,n+1)]; S=sum(ratios)
    H=sum(abs(a-b) for i,a in enumerate(ratios) for b in ratios[i+1:])
    G=H/(n*S) if S else 0; P=sum(weights[i]*abs(y[i]/target[i]-1) for i in range(1,n+1))
    F=G+float(p['lambda'])*P; reported=witness.get('F',witness.get('objective'))
    assert reported is not None and abs(F-reported)<1e-7,(F,reported)
    if 'inventory' in witness: assert y==witness['inventory']
    return dict(F=F,G=G,P=P,stations=len(visited),pickup=total_pickup,drop=total_drop,
                maximum_duration=max(durations,default=0),original_T_feasible=max(durations,default=0)<=float(p['T_seconds'])+1e-7)

def main():
    p=panel(); quality=[]; candidate_events=[]; performance=[]; oracle=[]; witness_checks=[]; artifacts=[]
    for e in entries():
        dest=ROOT/e['destination']; completion=dest/'completion.json'
        if not completion.exists(): continue
        done=read(completion)
        if done['returncode']!=0: continue
        identity=e['id']; prefix=dict(stage=e['stage'],id=identity,arm=e['arm'])
        if (dest/'quality.csv').exists():
            for row in rows(dest/'quality.csv'):
                row=dict(prefix,**row)
                if row['method']=='LEGACY60':
                    row['derived_stop_reason']='evaluation_limit_512' if int(row['quantity_evaluations'])==512 else 'no_strict_single_operation_improvement'
                quality.append(row)
        if (dest/'oracle_result.json').exists(): oracle.append(dict(prefix,**read(dest/'oracle_result.json')))
        rp=dest/'result.json'
        if rp.exists() and e['kind'] in ['performance','native-micro']:
            r=read(rp); fixed=r.get('schema')=='round50-fixed-interval-result-v1'
            archive_paths=list(dest.glob('**/archive_witness.json'))
            au=min((read(a)['F'] for a in archive_paths),default=None)
            U=r.get('verified_upper_bound',r.get('upper_bound',r.get('objective')))
            L=r.get('lower_bound',0); final=min(U,au) if au is not None else U
            cert=r.get('certificate',False) if fixed else r.get('strict_certified_original_problem',False)
            mode=e['command'][e['command'].index('--round61-candidate-mode')+1] if '--round61-candidate-mode' in e['command'] else 'off'
            row=dict(prefix,mode=mode,scope=e.get('scope'),cap=e['cap_seconds'],certificate=bool(cert),
                U_native=U if fixed else None,U_reported=U,U_archive=au,U_usable=final,LB=L,
                absolute_gap=max(0,final-L),native_gap=max(0,U-L),work=r.get('work',r.get('gurobi_work',r.get('external_gini_tree_total_work'))),
                wall_seconds=done['wall_seconds'],process_seconds=r.get('process_time_seconds',r.get('runtime_seconds')),
                root_seconds=r.get('root_time_seconds'),first_native_incumbent_seconds=r.get('first_incumbent_time_seconds'),
                submitted=r.get('round60_candidates_submitted'),mapped=r.get('round60_candidates_mapped'),
                native_status=r.get('native_status',r.get('status')),within_budget=done['within_budget'],
                executable_sha256=e['executable_sha256'],model_sha256=sha(dest/'canonical_model.lp') if fixed else None)
            progress=dest/'mip_progress.csv'
            if progress.exists() and fixed:
                tr=rows(progress); good=[float(q['time_seconds']) for q in tr if q.get('incumbent_available')=='1' and float(q['incumbent'])<=U+1e-7]
                row['native_final_UB_first_observed']=min(good) if good else None
                row['proof_tail_seconds']=max(0,r['solver_time_seconds']-min(good)) if good and cert else None
                ext=[float(q['time_seconds']) for q in tr if q.get('bound_available')=='1' and au is not None and float(q['best_bound'])>=au-1e-7]
                row['external_archive_bound_crossing_solver_seconds']=min(ext) if ext else None
            performance.append(row)
        for event_file in dest.glob('**/*candidate_events.csv'):
            candidate_events.extend(dict(prefix,file=str(event_file.relative_to(ROOT)),**row) for row in rows(event_file))
        if identity in p:
            for witness in dest.glob('**/*witness.json'):
                physical_result=physical(p[identity],read(witness))
                witness_checks.append(dict(prefix,file=str(witness.relative_to(ROOT)),sha256=sha(witness),**physical_result))
                target=OUT/'witnesses'/e['stage']/identity/str(e['arm']).replace('+','_')/witness.name
                target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(witness,target)
            if rp.exists() and 'routes' in read(rp):
                r=read(rp)
                if r['routes']:
                    witness_checks.append(dict(prefix,file=str(rp.relative_to(ROOT)),sha256=sha(rp),**physical(p[identity],r)))
        for path in dest.glob('*'):
            if path.is_file() and path.suffix in ['.json','.csv','.lp']:
                artifacts.append(dict(path=str(path.relative_to(ROOT)),bytes=path.stat().st_size,sha256=sha(path)))
    table('candidate_quality.csv',quality);table('performance.csv',performance);table('candidate_events.csv',candidate_events)
    table('oracle_results.csv',oracle);table('witness_verification.csv',witness_checks);table('local_artifacts.csv',artifacts)
    pairs=[]
    groups={}
    for r in performance: groups.setdefault((r['stage'],r['id']),{})[r['mode']]=r
    for (stage,identity),arms in groups.items():
        if 'off' not in arms: continue
        a=arms['off']
        for mode,b in arms.items():
            if mode=='off': continue
            assert a['executable_sha256']==b['executable_sha256'],'mismatched paired builds'
            if a['model_sha256']: assert a['model_sha256']==b['model_sha256'],'mismatched fixed F0'
            delta=a['absolute_gap']-b['absolute_gap']; dt=a['wall_seconds']-b['wall_seconds']
            rel=delta/max(a['absolute_gap'],1e-15); rt=dt/a['wall_seconds']; decision='below_predeclared_threshold'
            if a['certificate']!=b['certificate']: decision='certificate_gain' if b['certificate'] else 'certificate_loss'
            elif a['certificate'] and b['certificate']:
                if dt>=10 and rt>=.1:decision='meaningful_faster_certificate'
                elif dt<=-10 and rt<=-.1:decision='meaningful_slower_certificate'
            elif delta>=.001 and rel>=.05:decision='meaningful_gap_improvement'
            elif delta<=-.001 and rel<=-.05:decision='meaningful_gap_regression'
            pairs.append(dict(stage=stage,id=identity,comparison='off_vs_'+mode,
                effective_submission=mode=='submit' and (b.get('submitted') or 0)>0,
                interpretation='archive_only_mapping_diagnostic' if mode=='submit' and not b.get('mapped') else 'qualified_mode_comparison',
                gap_reduction=delta,relative_gap_reduction=rel,UB_contribution=a['U_usable']-b['U_usable'],
                LB_contribution=b['LB']-a['LB'],wall_reduction=dt,relative_wall_reduction=rt,decision=decision))
    table('paired_results.csv',pairs)
    pub=[]
    for identity in ['D6','D7']:
        off=RAW/'publication'/identity/'prefix-off';on=RAW/'publication'/identity/'prefix-on'
        if not off.exists() or not on.exists():continue
        a=read(off/'prefix_costs.json');b=read(on/'prefix_costs.json')
        common=lambda path:[(x['generation'],x['best_fitness'],x['strict_improvement']) for x in rows(path/'prefix_generations.csv')]
        assert common(off)==common(on) and a['decoder_calls']==b['decoder_calls']
        assert read(off/'PREFIX_witness.json')['sha256']==read(on/'PREFIX_witness.json')['sha256']
        pub.append(dict(id=identity,logical_prefix_equal=True,**{'OFF_'+k:v for k,v in a.items()},**{'ON_'+k:v for k,v in b.items()},delta_total_seconds=b['total_seconds']-a['total_seconds']))
    table('publication_costs.csv',pub)
    ledger=entries(); complete=[read(ROOT/e['destination']/'completion.json') for e in ledger if (ROOT/e['destination']/'completion.json').exists()]
    write(OUT/'budget_audit.json',dict(charged=sum(e['charged'] for e in ledger),maximum=72,
        native_micro=sum(e['kind']=='native-micro' for e in ledger),native_micro_maximum=4,
        failed=sum(c['returncode']!=0 for c in complete),watchdogs=sum(c['watchdog'] for c in complete),
        completed=len(complete),started=len(ledger),remaining=72-sum(e['charged'] for e in ledger)))
    print('analyzed',len(quality),'quality rows,',len(performance),'native rows,',len(oracle),'oracle rows')

if __name__=='__main__':main()
