"""Pure aggregation of LP retention, complete clocks, Native size and decisions."""
import csv,re
from round144_common import *
def idle():assert not budget()['unclosed'],'heavy aggregation waits for all timed producers'
def rows(path):
    if not path.exists():return []
    with path.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def table(path,values):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in values for k in r)));w.writeheader();w.writerows(values)
def LP():
    idle();facts=[];native=read(OUT/'qualification_native_transport.json')
    for q in native['facts']:
        p=OUT/'LP'/f'{q["role"]}_base';r=read(p/'result.json')
        assert r['qualified'] and sha(p/'source.mps')==r['source_SHA'] and sha(p/'compact.mps')==r['compact_SHA']
        facts.append(dict(role=r['role'],old_L=r['old_L'],RN_L=r['source']['L'],Fraction_PC_L=r['compact']['L'],compiled_PC_L=q['L'],
            RN_gain=r['source_gain'],compiled_PC_gain=q['L']-r['old_L'],compiled_retention_fraction=q['retention_fraction'],compiled_loss=q['retention_loss'],
            RN_columns=r['source']['columns']-q['columns'],RN_rows=r['source']['rows']-(q['rows']-1),PC_rows=1,PC_nonzeros=r['PC_nonzeros'],
            RN_Runtime=r['source']['Runtime'],PC_Runtime=q['Runtime'],RN_Work=r['source']['Work'],PC_Work=q['Work'],
            RN_iterations=r['source']['iterations'],PC_iterations=q['iterations'],original_columns=q['columns'],original_rows=q['rows']-1,
            source_SHA=r['source_SHA'],compiled_compact_SHA=q['model_SHA'],Seed=0,Threads=1))
    child=read(OUT/'LP/R-X20-S-T1_actual_high_child/result.json')
    write(OUT/'reports/LP.json',dict(PASS=True,matched_roots=facts,actual_descendant=child,standalone_LP_Optimize=7,
        matched_complete_objectives_scopes_cutoffs_support_and_old_matrices=True,LP_values_numerical_not_rational_optimality_certificates=True,
        arbitrary_descendant_equivalence_not_claimed=True))
    table(OUT/'reports/LP.csv',facts)
    print(json.dumps(facts),flush=True)
def full():
    idle();full=[];qual=[];pending=[];failed=[];native_counts=[]
    for path in sorted(OUT.glob('*_matrix.json')):
        matrix=read(path)
        if 'batch' not in matrix:continue
        batch=matrix['batch'];isq=batch.startswith('qualification')
        for g in matrix['groups']:
            l=g['launch'];d=Path(l['destination']);fee=OUT/'fees'/f'{batch}_{g["position"]:03}'
            observed=rows(d/'external/paper_optimize_ledger.csv')
            if observed:
                logs=[r['native_log'] for r in observed]
                assert len(logs)==len(set(logs)) and all(Path(p).is_file() for p in logs)
                assert all(r['optimize_return_code']=='0' for r in observed)
                native_counts.append(dict(batch=batch,position=g['position'],arm_id=l['arm_id'],
                    qualification=isq,proof_qualified=(d/'verification_closeout.json').exists(),
                    observed_Optimize=len(observed),observed_returned=len(observed),
                    LP=sum(r['solve_kind']=='LP' for r in observed),
                    MIP=sum(r['solve_kind']!='LP' for r in observed),
                    source_calls=sum('round144_source' in p for p in logs),
                    authority='Actual paper_optimize_ledger rows and corresponding returned Native logs'))
            if not (d/'verification_closeout.json').exists():
                v=dict(batch=batch,position=g['position'],role=l['id'],method=l['R144_method'],destination=str(d))
                if (fee/'receipt.json').exists() and read(fee/'receipt.json')['exit_code']!=0:
                    v['failure_reason']='Unqualified source/producer/lifecycle or failed postverification; original stderr retained'
                    if (d/'result.json').exists():v['raw_failure_reason']=read(d/'result.json').get('external_gini_tree_failure_reason')
                    failed.append(v)
                else:pending.append(v)
                continue
            a=read(d/'round135_endpoint.json');control=read(d/'round144_control_audit.json');audit=read(d/'audit.json')
            assert a['native_proof_qualified'] and a['performance_eligible'] and control['PASS'] and not audit['source_rejections']
            assert a['declared_calls']==a['returned_calls']
            assert a['T_cert'] is None if not a['certificate'] else a['T_cert']==a['T_produce']
            ledger=rows(d/'external/paper_optimize_ledger.csv');terminal=next((r for r in reversed(ledger) if 'terminal' in r['native_log']),None)
            observations=[r['payload'] for r in read(d/'observations.json')];bylog={r['native_log_path']:r['call'] for r in observations if r['kind']=='call'}
            cid=bylog[terminal['native_log']] if terminal else None
            quality=next((r for r in observations if r['kind']=='native_quality' and r['call']==cid),None)
            result=read(d/'result.json');p=l['panel'];identity=read(OUT/g['group']/'identity.json')
            r=dict(batch=batch,position=g['position'],role=l['id'],method=l['R144_method'],seed=l['seed'],formal_entered=not isq,
                input_SHA=p['input_sha256'],physical_T=p['T_seconds'],lambda_value=p['lambda'],cap=l['cap_seconds'],
                source_commit=identity['measured_source_commit'],PE_SHA=identity['candidate_binary_sha256'],DLL_SHA=identity['dll_sha256'],
                **{k:a[k] for k in ['U','L','certificate','signed_gap','relative_gap','T_produce','T_cert','T_verify','T_total','H_complete','H_semantic_SHA','H_fleet_SHA','declared_calls','returned_calls']},
                external_merged_final_L=a['L'],terminal_native_return_ObjBoundC=quality.get('ObjBoundC') if quality else None,
                terminal_native_return_ObjVal=quality.get('ObjVal') if quality else None,
                LP_calls=sum(v['solve_kind']=='LP' for v in ledger),target_calls=sum('TARGET' in v['solve_kind'] for v in ledger),terminal_calls=sum(v['solve_kind']=='MIP' for v in ledger),
                Native_total_Work=sum(float(v['work']) for v in ledger),Native_total_runtime=sum(float(v['solver_runtime']) for v in ledger),
                terminal_Work=float(terminal['work']) if terminal else 0.,terminal_nodes=float(terminal['nodes']) if terminal else 0.,
                root_L=next((float(v['lower_bound']) for v in rows(d/'external/lp_status_ledger.csv') if v['leaf_id']=='L0'),None),
                AM_action_sequence=';'.join(v['selected_action'] for v in rows(d/'external/adaptive_mass_decision_ledger.csv')),
                actual_split_count=result['external_gini_tree_split_count'],performance_eligible=True,native_proof_qualified=True,destination=str(d))
            source=control['source']
            if source:r.update(source_preparation_seconds=source.get('total_preparation_seconds',0.),source_Runtime=source.get('Runtime',0.),source_Work=source.get('Work',0.),
                source_L=source.get('source_objective'),source_RN_columns=source.get('source_RN_columns',0),source_solves=source['source_solves'],PC_emitted=source.get('PC_emitted',False),formal_RN_columns=0)
            else:r.update(source_preparation_seconds=0.,source_solves=0,PC_emitted=False,
                formal_RN_columns=max((f['RN_columns'] for f in control['models']),default=0))
            if terminal:
                text=Path(terminal['native_log']).read_text();pres=re.findall(r'Presolved: ([\d,]+) rows, ([\d,]+) columns, ([\d,]+) nonzeros',text)
                if pres:r.update(presolved_rows=int(pres[-1][0].replace(',','')),presolved_columns=int(pres[-1][1].replace(',','')),presolved_nonzeros=int(pres[-1][2].replace(',','')))
                root=re.findall(r'Root relaxation: objective ([-+\d.eE]+), ([\d,]+) iterations, ([\d.]+) seconds',text)
                if root:r.update(native_root_relaxation_objective=float(root[-1][0]),native_root_simplex_iterations=int(root[-1][1].replace(',','')),native_root_relaxation_seconds=float(root[-1][2]))
                root_lines=re.findall(r'^\s*0\s+\d+\s+[-+\d.eE]+\s+\d+\s+\d+\s+[-+\d.eE]+\s+([-+\d.eE]+)\s+',text,re.M)
                if root_lines:r['printed_root_after_cuts_bound']=float(root_lines[-1])
            (qual if isq else full).append(r)
    pairs=[]
    for c in [r for r in full if r['method']=='RNP']:
        off=next((r for r in full if r['method']=='OFF' and (r['role'],r['seed'])==(c['role'],c['seed'])),None)
        if not off:continue
        for k in ['input_SHA','physical_T','lambda_value','cap','source_commit','PE_SHA','H_semantic_SHA','H_fleet_SHA']:assert c[k]==off[k],(c['role'],k)
        pairs.append(dict(role=c['role'],seed=c['seed'],same_PE=True,own_H_equal=True,off_U=off['U'],RNP_U=c['U'],off_L=off['L'],RNP_L=c['L'],
            off_certificate=off['certificate'],RNP_certificate=c['certificate'],off_gap=off['relative_gap'],RNP_gap=c['relative_gap'],
            **{'delta_'+k:c[k]-off[k] for k in ['U','L','relative_gap','T_produce','T_verify','T_total']},off_T_cert=off['T_cert'],RNP_T_cert=c['T_cert']))
    bridges=[]
    for rn in [r for r in full if r['method']=='RN']:
        c=next(r for r in full if r['method']=='RNP' and (r['role'],r['seed'])==(rn['role'],rn['seed']))
        for k in ['input_SHA','physical_T','lambda_value','cap','source_commit','PE_SHA','DLL_SHA','H_semantic_SHA','H_fleet_SHA']:
            assert c[k]==rn[k],(c['role'],'RN bridge',k)
        assert c['formal_RN_columns']==0 and rn['formal_RN_columns']>0
        bridges.append(dict(role=c['role'],seed=c['seed'],same_PE=True,own_H_equal=True,
            RNP_U=c['U'],RN_U=rn['U'],RNP_L=c['L'],RN_L=rn['L'],RNP_gap=c['relative_gap'],RN_gap=rn['relative_gap'],
            RNP_formal_RN_columns=0,RN_formal_RN_columns=rn['formal_RN_columns'],
            **{'delta_RNP_minus_RN_'+k:c[k]-rn[k] for k in ['U','L','relative_gap','T_produce','T_verify','T_total','terminal_Work','terminal_nodes']},
            causal_column_count_isolation_not_claimed=True))
    write(OUT/'reports/full.json',dict(UTC=utc(),new_arms=full,qualification=qual,pairs=pairs,RN_bridges=bridges,failed_qualifications=failed,pending=pending,
        all_entered_native_counts=native_counts,all_entered_observed_Native_Optimize=sum(r['observed_Optimize'] for r in native_counts),
        all_entered_observed_Native_returned=sum(r['observed_returned'] for r in native_counts),
        standalone_LP_Optimize_separate=7,reader_only_recoveries_Optimize=0,all_entered_preserved=True,budget=budget(),Optimize=0))
    table(OUT/'reports/new_arms.csv',full);table(OUT/'reports/qualification.csv',qual);table(OUT/'reports/same_PE_pairs.csv',pairs)
    table(OUT/'reports/same_PE_RN_bridges.csv',bridges)
    table(OUT/'reports/all_entered_native_counts.csv',native_counts)
    write(OUT/'cost_report.json',dict(UTC=utc(),charged_new_experiment_seconds=budget()['G1_seconds'],experiment=budget(),ceiling_seconds=28800,
        outer_fees_including_failed_readers_and_all_required_postverification=True,nested_H_LP_MIP_Work_not_added_again=True,
        offline_arithmetic_seconds=sum(read(p).get('seconds',0) for p in [OUT/'math/fixtures.json',OUT/'math/offline_rank_PC.json',OUT/'math/local_floor_witness.json'] if p.exists()),
        build_seconds_separate=sum(read(p)['outer_seconds'] for p in (OUT/'fees').glob('*/receipt.json') if read(p.parent/'launch.json')['kind']=='build'),
        all_entered_observed_Native_Optimize=sum(r['observed_Optimize'] for r in native_counts),
        failed_qualification_observed_Native_Optimize=sum(r['observed_Optimize'] for r in native_counts if r['qualification'] and not r['proof_qualified']),
        standalone_LP_Optimize_separate=7,reader_only_recoveries_Optimize=0))
    print(json.dumps(dict(arms=len(full),qualified_health=len(qual),failed_qualifications=len(failed),pending=len(pending),pairs=pairs)),flush=True)
if __name__=='__main__':globals()[sys.argv[1]]()
