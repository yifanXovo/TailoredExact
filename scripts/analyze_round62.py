"""Read-only result analysis; no optimizer or candidate generation."""
import csv
import json
import re
from pathlib import Path
from round62_research import ROOT,OUT,RAW,write

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def native_size(folder):
    # The historical text counter includes newly symbolic row labels as columns
    # and nonzeros. Actual Gurobi readback is authoritative for representation cost.
    for name in ['native_gurobi.log','plain_lp_gurobi.log']:
        path=folder/name
        if path.exists():
            m=re.search(r'Optimize a model with (\d+) rows, (\d+) columns and (\d+) nonzeros',path.read_text(errors='replace'))
            if m:return dict(zip(['rows','columns','nonzeros'],map(int,m.groups())))
    return {k:read(folder/'model_fingerprint.json')[k] for k in ['rows','columns','nonzeros']}
def table(p,rows):
    if not rows:return
    keys=list(dict.fromkeys(k for row in rows for k in row))
    with p.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,keys);w.writeheader();w.writerows(rows)

def completion(proof,point,include_service=False):
    """Exact continuous minimum event completion for the implemented dictionary.

    All individual rows define event intervals. Nesting propagates lower
    endpoints; clique feasibility is decided at their componentwise minimum.
    """
    event_names={n for row in proof['rows'] for n in row['coefficients'] if n.startswith(('r62lo_','r62hi_'))}
    intervals={n:[0.,1.] for n in event_names};nesting=[];conflicts=[]
    for row in proof['rows']:
        ev={n:c for n,c in row['coefficients'].items() if n in event_names}
        if row['name'].startswith('r62conflict_'):conflicts.append(row);continue
        if '_nested_' in row['name']:nesting.append(row);continue
        if len(ev)!=1:raise RuntimeError('unexpected definition row')
        n,c=next(iter(ev.items()))
        rhs=row['rhs']-sum(c2*point[n2] for n2,c2 in row['coefficients'].items() if n2 not in event_names)
        value=rhs/c;sense=row['sense'];low=(sense=='>' and c>0) or (sense=='<' and c<0)
        if sense=='=':intervals[n][0]=max(intervals[n][0],value);intervals[n][1]=min(intervals[n][1],value)
        elif low:intervals[n][0]=max(intervals[n][0],value)
        else:intervals[n][1]=min(intervals[n][1],value)
    for _ in range(len(event_names)):
        changed=False
        for row in nesting:
            strong=next(n for n,c in row['coefficients'].items() if c==1)
            weak=next(n for n,c in row['coefficients'].items() if c==-1)
            if intervals[weak][0]<intervals[strong][0]:intervals[weak][0]=intervals[strong][0];changed=True
        if not changed:break
    deficit=max((lo-hi for lo,hi in intervals.values()),default=0)
    violations=[dict(name=r['name'],violation=sum(c*intervals[n][0] for n,c in r['coefficients'].items())-r['rhs']) for r in conflicts]
    return dict(continuous_completion_feasible=deficit<=1e-7,definition_infeasibility=deficit,
        minimum_event_completion={n:v[0] for n,v in intervals.items()},
        maximum_conflict_violation=max((x['violation'] for x in violations),default=0),
        conflicts_violated=sum(x['violation']>1e-7 for x in violations),conflict_violations=violations)

def lp_analysis():
    rows=[];separations=[]
    for path in sorted(RAW.glob('lp*/*/*/lp_result.json')):
        folder=path.parent;stage,identity,mode=folder.parts[-3:];r=read(path);model=native_size(folder)
        rows.append(dict(stage=stage,id=identity,mode=mode,objective=r['objective'],work=r['work'],seconds=r['process_time_seconds'],
            rows=model['rows'],columns=model['columns'],nonzeros=model['nonzeros']))
        proof_path=folder/'canonical_model.lp.round62.json'
        base=folder.parent/'off'/'lp_variable_evidence.csv'
        if not proof_path.exists() or not base.exists():continue
        proof=read(proof_path)
        point={p['variable_name']:float(p['primal_value']) for p in csv.DictReader(base.open(newline=''))}
        if mode.startswith('projection'):
            violations=[r['rhs']-sum(c*point[n] for n,c in r['coefficients'].items()) for r in proof['rows']]
            result=dict(maximum_projection_violation=max(violations,default=0),projections_violated=sum(v>1e-7 for v in violations))
        else:result=completion(proof,point)
        separations.append(dict(stage=stage,id=identity,mode=mode,source=str(base.relative_to(ROOT)),**result))
    table(OUT/'lp_comparison.csv',rows);write(OUT/'frozen_lp_completion.json',separations)
    return rows

def performance():
    rows=[]
    exclusions={e['number']:e for e in read(OUT/'run_exclusions.json')} if (OUT/'run_exclusions.json').exists() else {}
    ledger=OUT/'processes.jsonl'
    if not ledger.exists():return []
    for e in (json.loads(s) for s in ledger.read_text().splitlines()):
        folder=ROOT/e['destination'];done=folder/'completion.json'
        if not done.exists():continue
        r=read(folder/'result.json') if (folder/'result.json').exists() else {}
        end=read(done);row=dict(charged=e['charged'],number=e['charged_number'],id=e['id'],stage=e['stage'],arm=e['arm'],cap=e['cap_seconds'],
            wall=end['wall_seconds'],returncode=end['returncode'],watchdog=end['watchdog'],within_budget=end['within_budget'],exe_sha256=e['executable_sha256'])
        exclusion=exclusions.get(e['charged_number'],{})
        row['performance_eligible']=not exclusion.get('exclude_performance',False)
        row['performance_exclusion_reason']=exclusion.get('reason','')
        if r:
            fixed=r.get('schema')=='round50-fixed-interval-result-v1'
            if fixed:r=dict(r,upper_bound=r['verified_upper_bound'],objective=r['final_incumbent'])
            for key in ['status','objective','lower_bound','upper_bound','gap','strict_certified_original_problem',
                'round62_external_stop_requested','round62_external_certificate','round62_control_upper_bound','round62_archive_upper_bound',
                'round62_archive_construction_seconds','external_gini_tree_optimize_count','external_gini_tree_lp_optimize_count',
                'round62_archive_evidence_persisted','external_gini_tree_backend_parameter_roundtrip_valid',
                'external_gini_tree_partial_mip_optimize_count','external_gini_tree_terminal_mip_optimize_count',
                'external_gini_tree_final_leaf_count','external_gini_tree_open_leaf_count','external_gini_tree_split_count',
                'external_gini_tree_cumulative_work','external_gini_tree_model_build_seconds']:
                row[key]=r.get(key)
            row['absolute_gap']=r['upper_bound']-r['lower_bound']
            row['gap_source']='reported'
            if row['gap'] is None:
                row['gap']=max(0,row['absolute_gap'])/abs(r['upper_bound']) if abs(r['upper_bound'])>1e-12 else None
                row['gap_source']='derived_from_final_original_bounds'
            row['scope']='fixed_F0_improving_domain' if fixed else 'full_original_problem'
            if fixed:
                row['fixed_interval_certificate']=r['certificate']
                for key in ['native_status','work','nodes','model_build_seconds','root_relaxation_bound','final_root_cut_bound','root_work','root_time_seconds']:
                    row[key]=r.get(key)
                model=native_size(folder)
                row.update(rows=model['rows'],columns=model['columns'],nonzeros=model['nonzeros'])
            else:
                native=folder/'external'/'paper_optimize_ledger.csv'
                if native.exists():
                    calls=list(csv.DictReader(native.open(newline='')))
                    row['work']=sum(float(c['work']) for c in calls)
                    row['nodes']=sum(float(c['nodes']) for c in calls)
                    row['optimizer_calls']=len(calls)
                    row['native_statuses']='|'.join(c['solve_kind']+':'+c['native_status'] for c in calls) or 'no native optimize'
                elif e['arm']=='P-GRB':
                    row.update(work=r.get('gurobi_work'),nodes=r.get('gurobi_node_count'),optimizer_calls=1,
                        native_statuses=r.get('gurobi_status_text'),native_model_fingerprint=r.get('gurobi_model_fingerprint'),
                        rows=r.get('gurobi_num_constrs'),columns=r.get('gurobi_num_vars'),nonzeros=r.get('gurobi_num_nzs'))
                    expected=int(e['command'][e['command'].index('--round24-expected-gurobi-model-fingerprint')+1])
                    row['official_PGRB_fingerprint_matches']=expected==r['gurobi_model_fingerprint']
                    assert row['official_PGRB_fingerprint_matches'],'official P-GRB identity mismatch'
                row['parameter_readback']={k:r.get('gurobi_'+k+'_effective') for k in ['threads','seed','presolve','mip_gap','mip_gap_abs']}
        rows.append(row)
    table(OUT/'runs.csv',rows);return rows

def native_points():
    checks=[]
    for group in sorted([*RAW.glob('mip*/*'),*RAW.glob('screen_v3/*')]):
        sample=group/'off'/'node_samples.csv'
        if not sample.exists():continue
        groups={}
        for r in csv.DictReader(sample.open(newline='')):
            key=(r['sample_kind'],r['root_callback_sequence'],r['node_bucket'],r['root_completion_status'])
            groups.setdefault(key,{})[r['variable']]=float(r['value'])
        for proof_path in sorted(group.glob('*/canonical_model.lp.round62.json')):
            mode=proof_path.parent.name;p=read(proof_path)
            for key,point in groups.items():
                if mode.startswith('projection'):
                    violations=[r['rhs']-sum(c*point[n] for n,c in r['coefficients'].items()) for r in p['rows']]
                    result=dict(maximum_violation=max(violations,default=0),violated=sum(v>1e-7 for v in violations))
                else:
                    c=completion(p,point);result={k:c[k] for k in ['continuous_completion_feasible','definition_infeasibility','maximum_conflict_violation','conflicts_violated']}
                checks.append(dict(stage=group.parent.name,id=group.name,mode=mode,sample=key,**result))
    write(OUT/'native_point_separation.json',checks)

def main():
    lps=lp_analysis();runs=performance();native_points()
    print('LPs',[(r['id'],r['mode'],round(r['objective'],10)) for r in lps])
    print('completed charged',sum(r['charged'] for r in runs))
    print('full results',[(r['id'],r['arm'],round(r['wall'],3),r.get('strict_certified_original_problem'),r.get('absolute_gap')) for r in runs if 'objective' in r])
if __name__=='__main__':main()
