"""Compact actual Round59 results without promoting diagnostic certificates."""
import csv
import json
import math
from pathlib import Path
from round59_research import ROOT, OUT, RAW, sha, write

def csvwrite(path, rows):
    if not rows: return
    fields=list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)

def full_rows():
    rows=[]
    panel={r['id']:r for r in json.loads((OUT/'panel.json').read_text())['panel']}
    expected={r['instance_id']:r['expected_gurobi_model_fingerprint'] for r in json.loads((ROOT/'results/gf_citibike443_k1_vs_pgrb_round58/pgrb_expected_fingerprints.json').read_text())['entries']}
    expected.update({k:r['gurobi_model_fingerprint'] for k,r in json.loads((ROOT/'results/gf_small_hard_light_round39/gurobi_fingerprints.json').read_text())['instances'].items()})
    for launch in sorted(RAW.glob('screen*/*/*/launch.json')):
        ident=json.loads(launch.read_text()); dest=launch.parent
        if (dest.parent/'invalidated.json').exists(): continue
        if not (dest/'result.json').exists() or not (dest/'completion.json').exists(): continue
        r=json.loads((dest/'result.json').read_text())
        if ident['arm']=='P-GRB':
            assert r['gurobi_model_fingerprint']==expected[panel[ident['id']]['scenario_id']], str(dest)
        c=json.loads((dest/'completion.json').read_text()) if (dest/'completion.json').exists() else {}
        v=r.get('verification',{})
        valid=bool(v.get('original_solution_feasible') and v.get('original_objective_recomputed') and not v.get('errors'))
        ub=v.get('objective') if valid else None
        lb=r.get('lower_bound')
        cert=r.get('strict_certificate_class')=='engineering_exact_original_problem_optimal'
        if cert and (not valid or lb is None or abs(ub-lb)>1e-7*max(1,abs(ub))):
            raise RuntimeError('certificate mismatch '+str(dest))
        ops=dest/'external/paper_optimize_ledger.csv'
        calls=list(csv.DictReader(ops.open())) if ops.exists() else []
        mip=[x for x in calls if x['solve_kind']!='LP']
        lp=[x for x in calls if x['solve_kind']=='LP']
        if ident['arm']=='F0-Single-S' and (len(mip)>1 or any(x['leaf_id']!='L0' for x in calls)):
            raise RuntimeError('single-MIP lifecycle violated '+str(dest))
        init=dest/'external/initial_decomposition_ledger.csv'
        initrows=list(csv.DictReader(init.open())) if init.exists() else []
        initrow=initrows[0] if initrows else {}
        absolute=max(0,ub-lb) if valid and lb is not None else None
        row=dict(id=ident['id'],arm=ident['arm'],cap=ident['cap'],certificate=cert,
            status=r.get('status'),valid_ub=valid,LB=lb,UB=ub,absolute_gap=absolute,
            relative_gap=absolute/abs(ub) if absolute is not None and ub!=0 else (0 if absolute==0 else None),
            process_seconds=r.get('final_process_wall_time_seconds'),
            watchdog_wall_seconds=c.get('wall_seconds'),watchdog=c.get('watchdog'),
            certificate_seconds=r.get('final_process_wall_time_seconds') if cert else None,
            startup_seconds=r.get('incumbent_generation_time_seconds'),
            initial_U=initrow.get('U_proof_launch'),anchor_U=initrow.get('U_anchor_launch'),
            initial_gamma_upper=initrow.get('active_upper'),
            splits=r.get('external_gini_tree_split_count'),lp_calls=len(lp),
            mip_calls=(1 if r.get('gurobi_runtime',0)>0 else 0) if ident['arm']=='P-GRB' else len(mip),
            native_mip_start_attempted=r.get('global_gini_tree_native_mip_start_attempted'),
            native_mip_start_submitted=r.get('global_gini_tree_native_mip_start_submitted'),
            native_hints='not_requested_no_adapter_path',
            canonical_model_build_seconds=r.get('external_gini_tree_model_build_seconds'),
            lp_work=sum(float(x['work']) for x in lp),
            mip_work=r.get('gurobi_work') if ident['arm']=='P-GRB' else sum(float(x['work']) for x in mip),
            lp_native_seconds=sum(float(x['solver_runtime']) for x in lp),
            mip_native_seconds=r.get('gurobi_runtime') if ident['arm']=='P-GRB' else sum(float(x['solver_runtime']) for x in mip),
            iterations=r.get('gurobi_iter_count') if ident['arm']=='P-GRB' else sum(float(x['simplex_iterations']) for x in calls),
            nodes=r.get('gurobi_node_count') if ident['arm']=='P-GRB' else sum(float(x['nodes']) for x in calls),
            work=sum(float(x['work']) for x in calls) if calls else r.get('gurobi_work'),
            max_route_travel=max(v.get('route_travel_time',[0]),default=0),
            executable_sha256=ident['executable_sha256'],result_sha256=sha(dest/'result.json'),
            artifact_dir=str(dest.relative_to(ROOT)),failure=r.get('external_gini_tree_failure_reason'))
        rows.append(row)
    csvwrite(OUT/'full_instance_results.csv',rows)
    lifecycle=[];bound_trace=[]
    for row in rows:
        dest=ROOT/row['artifact_dir']
        for filename,target in [('paper_optimize_ledger.csv',lifecycle),('global_bound_trace.csv',bound_trace)]:
            path=dest/'external'/filename
            if path.exists():
                records=list(csv.DictReader(path.open()))
                if filename=='global_bound_trace.csv' and records:
                    # Keep original event values, not an invented continuous
                    # trajectory. Full traces remain in local raw artifacts.
                    indices={0,len(records)-1};seen=set()
                    for i,event in enumerate(records):
                        kind=event['event_type']
                        if kind not in seen:indices.add(i);seen.add(kind)
                    for checkpoint in [1,5,10,30,60,90,117]:
                        eligible=[i for i,x in enumerate(records) if float(x['process_elapsed_seconds'])<=checkpoint]
                        if eligible:indices.add(eligible[-1])
                    records=[dict(records[i],sampling_scope='selected_events_not_complete_gap_integral') for i in sorted(indices)]
                target.extend(dict(id=row['id'],arm=row['arm'],cap=row['cap'],**x) for x in records)
    csvwrite(OUT/'full_native_call_ledger.csv',lifecycle)
    csvwrite(OUT/'full_global_bound_events.csv',bound_trace)
    return rows

def diagnostics():
    rows=[]
    for launch in sorted(RAW.glob('diagnostic_*/*/*/launch.json')):
        ident=json.loads(launch.read_text());dest=launch.parent
        rp=dest/('lp_result.json' if ident['stage'].endswith(('_roots','_hga_lp')) else 'result.json')
        if not rp.exists() or not (dest/'completion.json').exists(): continue
        r=json.loads(rp.read_text())
        row=dict(id=ident['id'],arm=ident['arm'],stage=ident['stage'],scope='restricted_state_only',cap=ident['cap'],**r)
        row['artifact_dir']=str(dest.relative_to(ROOT));row['result_sha256']=sha(rp)
        row['model_identity_scope']='current_K1_F0' if ident['stage'].startswith('diagnostic_current_') else 'legacy_harness_excluded_from_current_attribution'
        row['display_arm']='F0-minus-pack_connectivity_retained' if ident['arm']=='Compact' else ident['arm']
        if ident['arm']=='Compact': row['model_identity_scope']='pack_removal_ablation_not_original_compact'
        if ident['arm']=='OriginalCompact': row['model_identity_scope']='official_compact_origin_SHA_bound_plus_interval_cutoff'
        rows.append({k:v for k,v in row.items() if not isinstance(v,(dict,list))})
    csvwrite(OUT/'fixed_state_results.csv',rows)
    return rows

def analyze():
    full=full_rows();fixed=diagnostics()
    pairs=[]
    for left,right in [('P-GRB','K1-H'),('K1-H','K1-S'),('K1-S','F0-Single-S')]:
        for id,cap in sorted({(r['id'],r['cap']) for r in full}):
            a=next((r for r in full if r['id']==id and r['cap']==cap and r['arm']==left),None)
            b=next((r for r in full if r['id']==id and r['cap']==cap and r['arm']==right),None)
            if not a or not b: continue
            pairs.append(dict(id=id,left=left,right=right,left_certificate=a['certificate'],right_certificate=b['certificate'],
                left_LB=a['LB'],right_LB=b['LB'],left_UB=a['UB'],right_UB=b['UB'],
                left_gap=a['relative_gap'],right_gap=b['relative_gap'],
                certified_time_ratio=b['process_seconds']/a['process_seconds'] if a['certificate'] and b['certificate'] else None,
                left_process=a['process_seconds'],right_process=b['process_seconds'],
                common_cap=a['cap'],both_capped=not a['certificate'] and not b['certificate']))
    csvwrite(OUT/'paired_results.csv',pairs)
    print(json.dumps(dict(full_rows=len(full),fixed_rows=len(fixed),certificates={a:sum(r['certificate'] for r in full if r['arm']==a) for a in sorted({r['arm'] for r in full})})))

if __name__=='__main__': analyze()
