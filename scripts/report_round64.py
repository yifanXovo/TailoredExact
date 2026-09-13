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
        semantic_failure=result.get('status')=='failed' or str(result.get('status','')).endswith('_failed')
        result['performance_eligible']=result['performance_eligible'] and e['kind']=='performance' and result['returncode']==0 and result['within_budget'] and not semantic_failure
        mode=e['command'][e['command'].index('--round64-shared-mode')+1] if '--round64-shared-mode' in e['command'] else 'off'
        result['shared_mode']=mode;result['startup']='HGA-current-process' if e['arm']=='K1-H' or e['arm'].startswith('warm-') else 'official-default' if e['arm']=='P-GRB' else 'verified-empty-routes'
        if r and result.get('scope')=='full_original_problem':
            if count==0:result['native_statuses']='no native optimize';result['work']=0;result['nodes']=0
            initial=folder/'external/initial_witness.json'
            result['initial_upper_bound']=read(initial)['objective'] if initial.exists() else r.get('initial_upper_bound')
            if result['initial_upper_bound'] is None and (folder/'ub_events.csv').exists():
                startup=[v for v in rows(folder/'ub_events.csv') if v['source']=='native_hga_tgbc_initial' and v['accepted']=='true' and v['verifier_passed']=='true']
                if len(startup)==1:result['initial_upper_bound']=float(startup[0]['objective'])
            heuristic=folder/'heuristic.csv'
            result['heuristic_seconds']=sum(float(h['runtime']) for h in rows(heuristic)) if heuristic.exists() else None
    table('runs.csv',results);table('optimizer_calls.csv',calls)
    charged=[e for e in entries if e['charged']]
    budget=dict(charged=len(charged),maximum=72,native_micro=sum(e['kind']=='native-micro' for e in charged),
        completed=sum(e['charged_number'] in by_number for e in charged),optimizer_calls=sum(c['optimizer_calls'] or 0 for c in calls),
        charged_wall_seconds=sum(r['wall'] for r in by_number.values()),
        build_only_launches=sum(not e['charged'] for e in entries),
        build_only_failures=[dict(id=r['id'],stage=r['stage'],arm=r['arm'],returncode=r['returncode']) for r in results if not r['charged'] and r['returncode']],
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
            for a,b in [('q','sep'),('t','sep'),('sep','joint'),('q','qcap'),('joint','qcap')]:
                if prefix+a in group and prefix+b in group:comparisons.append(compare(group[prefix+a],group[prefix+b]))
    links=OUT/'comparison_links.json'
    if links.exists():
        for link in read(links):
            if link['baseline'] in by_number and link['candidate'] in by_number:
                a,b=by_number[link['baseline']],by_number[link['candidate']]
                assert a['id']==b['id'] and a['performance_eligible'] and b['performance_eligible']
                pair=compare(a,b);pair.update(link_reason=link['reason'],baseline_stage=a['stage'],candidate_stage=b['stage']);comparisons.append(pair)
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
    parameters=[];outer=[];lifecycle=[];shapes=[];references=[]
    for e in run.runner.entries():
        folder=ROOT/e['destination']
        if not e['charged'] or not (folder/'completion.json').exists() or not (folder/'result.json').exists():continue
        r=read(folder/'result.json');native=folder/'external/paper_optimize_ledger.csv';calls=rows(native) if native.exists() else []
        for c in calls:lifecycle.append(dict(number=e['charged_number'],id=e['id'],arm=e['arm'],**c))
        applicable=True
        if r.get('schema')=='round50-fixed-interval-result-v1':valid=all(x['zero_gap_roundtrip']=='1' for x in rows(folder/'certificate_ledger.csv'))
        elif e['arm']=='P-GRB':
            valid=all(r.get('gurobi_'+n+'_effective')==v and r.get('gurobi_'+n+'_set_return_code')==0 and r.get('gurobi_'+n+'_get_return_code')==0 for n,v in [('threads',1),('seed',0),('presolve',-1),('mip_gap',0),('mip_gap_abs',0)])
            required=['gurobi_native_domain_audit_passed','gurobi_lifecycle_valid',
                'gurobi_obj_bound_c_available','verified_incumbent_objective_available',
                'verified_incumbent_original_problem_feasible','verified_incumbent_objective_consistent']
            assert all(r.get(k) is True for k in required),'official reference evidence incomplete'
            assert r['gurobi_optimize_return_code']==0 and math.isfinite(r['gurobi_obj_bound_c'])
            assert r['lower_bound']==r['gurobi_obj_bound_c']
            assert '--plain-baseline' in e['command'] and not r['gurobi_hga_start_requested']
            expected=int(e['command'][e['command'].index('--round24-expected-gurobi-model-fingerprint')+1])
            assert r['gurobi_model_fingerprint']==expected
            references.append(dict(number=e['charged_number'],id=e['id'],arm=e['arm'],
                compact_fingerprint=expected,original_domain_lifecycle_verified=True,
                bound_source='Gurobi_ObjBoundC',native_bound=r['gurobi_obj_bound_c'],
                original_incumbent_verified=True,default_heuristics_preserved=True,
                strict_certificate=r['strict_certified_original_problem'],
                legacy_model_correctness_field=r.get('model_correctness_failure_reason')))
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
    table('reference_contract_verification.csv',references)

def trajectories():
    endpoints=[];accepted=[];trace_compaction=[];native=[];native_bounds=[];costs=[]
    for e in run.runner.entries():
        folder=ROOT/e['destination'];result=folder/'result.json'
        if not e['charged'] or not (folder/'completion.json').exists() or not result.exists():continue
        r=read(result)
        if r.get('schema')=='round50-fixed-interval-result-v1' or e['kind'] not in ['performance','native-micro']:continue
        pre=dict(number=e['charged_number'],id=e['id'],arm=e['arm'],stage=e['stage'])
        final=r.get('upper_bound',r.get('objective'));certificate=r.get('strict_certified_original_problem',False)
        if final is None:continue
        phases=rows(folder/'phases.csv') if (folder/'phases.csv').exists() else []
        first_feasible=next((float(p['process_seconds']) for p in phases if p['event']=='initial_model_data_preprocessing_complete' and 'empty-route incumbent independently verified' in p['detail']),None)
        # The common parser may verify empty routes, but the official native
        # P-GRB receives no algorithm incumbent/cutoff from that preprocessing.
        if e['arm']=='P-GRB':first_feasible=None
        process_end=next((float(p['process_seconds']) for p in phases if p['event']=='process_exit'),None)
        verified=[]
        ub=folder/'ub_events.csv'
        if ub.exists():
            for v in rows(ub):
                if v['accepted']=='true' and v['verifier_passed']=='true':
                    verified.append((float(v['time_seconds']),float(v['objective']),'accepted_UB_event'))
        trace=folder/'external/global_bound_trace.csv'
        if trace.exists():
            trace_rows=rows(trace);last_key=None;state=None;groups=0
            for v in trace_rows:
                key=tuple((k,value) for k,value in v.items() if k not in ['process_elapsed_seconds','exact_phase_elapsed_seconds'])
                if key!=last_key:
                    state=dict(pre,**v,same_state_observations=0)
                    accepted.append(state);groups+=1;last_key=key
                state['same_state_observations']+=1
                state['last_observed_process_seconds']=v['process_elapsed_seconds']
                state['last_observed_exact_phase_seconds']=v['exact_phase_elapsed_seconds']
                if v['event_type'] in ['exact_tree_initialization','incumbent_improvement','round62_archive_ub_improvement']:
                    verified.append((float(v['process_elapsed_seconds']),float(v['verified_global_upper_bound']),v['event_type']))
            trace_compaction.append(dict(pre,source=str(trace.relative_to(ROOT)),sha256=run.sha(trace),
                raw_observations=len(trace_rows),consecutive_semantic_states=groups,
                rule='all non-time fields exact; preserve first/last times and count of every consecutive state'))
        best_times=[t for t,u,source in verified if u<=final+1e-9]
        zero_times=[t for t,u,source in verified if u==0]
        first_best=min(best_times) if best_times else None
        endpoints.append(dict(pre,final_UB=final,final_LB=r.get('lower_bound'),certificate=certificate,
            first_verified_feasible_process_seconds=first_feasible,
            first_accepted_final_UB_process_seconds=first_best,
            first_accepted_exact_zero_process_seconds=min(zero_times) if zero_times else None,
            process_exit_seconds=process_end,
            after_accepted_final_UB_to_exit_seconds=process_end-first_best if certificate and process_end is not None and first_best is not None else None,
            timing_scope='internal process clock; accepted original witness; native discovery separately rounded'))
        ledger=folder/'external/paper_optimize_ledger.csv'
        calls=rows(ledger) if ledger.exists() else []
        for c in calls:
            nodes=float(c['nodes']);seconds=float(c['solver_runtime']);work=float(c['work'])
            costs.append(dict(pre,leaf=c['leaf_id'],kind=c['solve_kind'],native_status=c['native_status'],
                seconds=seconds,work=work,nodes=nodes,simplex_iterations=float(c['simplex_iterations']),
                call_work_per_node_including_root=work/nodes if nodes>0 else None,
                call_seconds_per_node_including_root=seconds/nodes if nodes>0 else None))
        logs=[Path(c['native_log']) for c in calls if c['native_log']]
        if e['arm']=='P-GRB':
            logs.append(folder/'native.log')
            nodes=float(r['gurobi_node_count']);seconds=float(r['gurobi_runtime']);work=float(r['gurobi_work'])
            costs.append(dict(pre,leaf='original-compact',kind='MIP',native_status=r['gurobi_status_text'],
                seconds=seconds,work=work,nodes=nodes,simplex_iterations=float(r['gurobi_iter_count']),
                call_work_per_node_including_root=work/nodes if nodes>0 else None,
                call_seconds_per_node_including_root=seconds/nodes if nodes>0 else None))
        for path in logs:
            if not path.exists():continue
            for i,line in enumerate(path.read_text(encoding='utf-8',errors='replace').splitlines(),1):
                tokens=line.split()
                if len(tokens)>=6 and tokens[-1].endswith('s') and (tokens[-3].endswith('%') or tokens[-3]=='-') and re.match(r'^\s*(?:[H*]\s*)?\d+\s+\d+\s+',line):
                    try:bound=float(tokens[-4]);t=float(tokens[-1][:-1])
                    except ValueError:pass
                    else:
                        if math.isfinite(bound):
                            try:incumbent=float(tokens[-5])
                            except ValueError:incumbent=None
                            native_bounds.append(dict(pre,path=str(path.relative_to(ROOT)),line=i,
                                solver_seconds_integer_precision=t,native_bound_rounded=bound,
                                native_incumbent_rounded=incumbent,raw_line=line,
                                scope='complete compact native bound, rounded' if e['arm']=='P-GRB' else 'per-call model bound, rounded; not the complete outer global LB'))
                found=re.search(r'^Found heuristic solution: objective ([-+\d.eE]+)',line)
                if found:
                    u=float(found[1]);native.append(dict(pre,path=str(path.relative_to(ROOT)),line=i,native_incumbent_rounded=u,
                        solver_seconds_integer_precision=None,native_value_at_most_final_original_UB_with_rounding=u<=final+5e-7,
                        raw_line=line,scope='native model objective, not verified original F; heuristic line has no timestamp'))
                    continue
                if not line.startswith(('H','*')):continue
                tokens=line.split()
                if len(tokens)<6 or not tokens[-1].endswith('s'):continue
                try:u=float(tokens[-5]);t=float(tokens[-1][:-1])
                except ValueError:continue
                native.append(dict(pre,path=str(path.relative_to(ROOT)),line=i,native_incumbent_rounded=u,
                    solver_seconds_integer_precision=t,native_value_at_most_final_original_UB_with_rounding=u<=final+5e-7,
                    raw_line=line,scope='native model objective and per-call log precision; original route/F verified only at extraction'))
    table('primal_timing.csv',endpoints);table('global_bound_trajectories.csv',accepted)
    table('global_bound_trace_compaction.csv',trace_compaction)
    table('native_bound_observations.csv',native_bounds)
    table('native_incumbent_observations.csv',native);table('native_call_costs.csv',costs)

def index():
    records=[]
    for e in run.runner.entries():
        for p in sorted((ROOT/e['destination']).rglob('*')):
            if p.is_file():records.append(dict(number=e['charged_number'],charged=e['charged'],id=e['id'],arm=e['arm'],path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=run.sha(p)))
    table('evidence_index.csv',records);print('indexed',len(records),'local files')
def main():
    p=argparse.ArgumentParser();p.add_argument('--audit',action='store_true');p.add_argument('--index',action='store_true');a=p.parse_args();summary()
    if a.audit:audit_contracts();trajectories()
    if a.index:index()
if __name__=='__main__':main()
