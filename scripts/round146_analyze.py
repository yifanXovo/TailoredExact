"""Idle-only evidence aggregation; no Optimize, Native load or new proof."""
import csv,re,shutil
from round146_common import *
def idle():assert not budget()['unclosed'],'Aggregation waits until serial timing is idle'
def rows(path):
    if not path.exists():return []
    with path.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def table(path,values):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in values for k in r)));w.writeheader();w.writerows(values)
def LP():
    idle();facts=[read(p) for p in sorted((OUT/'LP').glob('*/result.json'))];assert len(facts)==5 and all(r['qualified'] for r in facts)
    write(OUT/'reports/LP.json',dict(PASS=True,new_LPs=facts,new_Optimize=5,baseline_Optimize=0,
        strong_joint_unchanged_witnesses=['K-35-U','R-X20-S-T1'],complete_objective_and_matrix_matched=True,
        values_numerical_not_rational_optimality_certificates=True,selected_candidate='STOCK+GD-state'))
    table(OUT/'reports/LP.csv',[{k:r[k] for k in ['role','variant','old_L','L','gain','g','weighted_penalty','rows','columns','nonzeros','added_nonzeros','coefficient_generation_seconds','Runtime','Work','iterations']} for r in facts])
    lines=['# Finite matched LP decision','',
        'Five new continuous optimizations, with sealed baseline values and actual solutions reused. All use the complete original objective, penalty and constant, matrix, support, g domain and cutoff; Seed=0, Threads=1, affinity=4, serial. Actual compiled GD coefficients are independently checked as rational lower bounds and read back from Native. These are numerical LP optima, distinct from Native root-after-cuts bounds and complete certificates.','',
        '| Role | Carrier + GD-state | Old L | New L | Gain | G | Weighted penalty | GD NZ | Generation ms | Runtime s |',
        '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |']
    for r in facts:lines.append(f'| {r["role"]} | {r["carrier"]} | {r["old_L"]:.12g} | {r["L"]:.12g} | {r["gain"]:.12g} | {r["g"]:.12g} | {r["weighted_penalty"]:.12g} | {r["added_nonzeros"]} | {r["coefficient_generation_seconds"]*1000:.4g} | {r["Runtime"]:.4g} |')
    lines+=['','K20 gains beyond both BASE and the stronger R145 joint carrier. Its matched STOCK+GD value is higher than standalone GD and STOCK, supporting one uniform STOCK+GD candidate with STOCK as the same-PE reference. K35 and RX20 also gain on BASE. The existing joint optima of K35/RX20 satisfy both GD rows and therefore witness no additional numerical optimum value on those particular stronger models; they were not reoptimized.','',
        'Each actual production block uses two rows, no columns and no paid source LP. Measured coefficient generation is approximately 0.38–1.95 ms on these domains. Point separation alone was not used to claim any optimized increment. The more elaborate state-level Hoover extension was not opened because the direct original-variable question already has useful optimization information. No global/state parameter grid or full formulation factorial was run.']
    (OUT/'LP_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
def full():
    idle();full=[];qual=[];pending=[];failed=[];counts=[]
    previous=OUT/'reports/full.json'
    if previous.exists():
        snapshot=OUT/'stages'/sha(previous);snapshot.mkdir(parents=True,exist_ok=True);saved={}
        for name in ['reports/full.json','reports/new_arms.csv','reports/qualification.csv','reports/same_PE_pairs.csv','reports/all_entered_native_counts.csv','reports/verified_U_trajectories.csv','cost_report.json']:
            path=OUT/name
            if path.exists():
                dest=snapshot/Path(name).name
                if not dest.exists():shutil.copyfile(path,dest)
                assert sha(dest)==sha(path);saved[name]=dict(SHA256=sha(path),snapshot=dest.relative_to(ROOT).as_posix())
        write(snapshot/'bindings.json',dict(Optimize=0,Native_load=0,files=saved))
    for path in sorted(OUT.glob('*_matrix.json')):
        m=read(path)
        if 'batch' not in m:continue
        batch=m['batch'];isq=batch.startswith('qualification')
        for g in m['groups']:
            l=g['launch'];d=Path(l['destination']);fee=OUT/'fees'/f'{batch}_{g["position"]:03}';ledger=rows(d/'external/paper_optimize_ledger.csv')
            if ledger:
                assert all(r['optimize_return_code']=='0' for r in ledger)
                counts.append(dict(batch=batch,position=g['position'],arm_id=l['arm_id'],qualification=isq,
                    observed_Optimize=len(ledger),observed_returned=len(ledger),LP=sum(r['solve_kind']=='LP' for r in ledger),MIP=sum(r['solve_kind']!='LP' for r in ledger),source_solves=0))
            if not (d/'verification_closeout.json').exists():
                v=dict(batch=batch,position=g['position'],role=l['id'],method=l['R146_method'],destination=str(d))
                (failed if (fee/'receipt.json').exists() and read(fee/'receipt.json')['exit_code']!=0 else pending).append(v);continue
            a=read(d/'round135_endpoint.json');control=read(d/'round146_control_audit.json');audit=read(d/'audit.json')
            assert a['native_proof_qualified'] and a['performance_eligible'] and control['PASS'] and not audit['source_rejections']
            assert a['declared_calls']==a['returned_calls'];assert a['T_cert'] is None if not a['certificate'] else a['T_cert']==a['T_produce']
            terminal=next((r for r in reversed(ledger) if 'terminal' in r['native_log']),None)
            observations=[r['payload'] for r in read(d/'observations.json')];bylog={r['native_log_path']:r['call'] for r in observations if r['kind']=='call'}
            cid=bylog[terminal['native_log']] if terminal else None;quality=next((r for r in observations if r['kind']=='native_quality' and r['call']==cid),None)
            result=read(d/'result.json');p=l['panel'];identity=read(OUT/g['group']/'identity.json')
            r=dict(batch=batch,position=g['position'],role=l['id'],method=l['R146_method'],seed=l['seed'],formal_entered=not isq,
                input_SHA=p['input_sha256'],physical_T=p['T_seconds'],lambda_value=p['lambda'],cap=l['cap_seconds'],
                source_commit=identity['measured_source_commit'],PE_SHA=identity['candidate_binary_sha256'],DLL_SHA=identity['dll_sha256'],
                **{k:a[k] for k in ['U','L','certificate','signed_gap','relative_gap','T_produce','T_cert','T_verify','T_total','H_complete','H_semantic_SHA','H_fleet_SHA','declared_calls','returned_calls']},
                physical_G=audit['physical']['G'],physical_P=audit['physical']['P'],weighted_physical_penalty=a['U']-audit['physical']['G'],
                external_supported_final_L=a['L'],terminal_native_return_ObjBoundC=quality.get('ObjBoundC') if quality else None,
                terminal_native_return_ObjVal=quality.get('ObjVal') if quality else None,
                LP_calls=sum(v['solve_kind']=='LP' for v in ledger),target_calls=sum('TARGET' in v['solve_kind'] for v in ledger),terminal_calls=sum(v['solve_kind']=='MIP' for v in ledger),
                Native_total_Work=sum(float(v['work']) for v in ledger),Native_total_runtime=sum(float(v['solver_runtime']) for v in ledger),
                terminal_Work=float(terminal['work']) if terminal else 0.,terminal_nodes=float(terminal['nodes']) if terminal else 0.,
                initial_root_L=next((float(v['lower_bound']) for v in rows(d/'external/lp_status_ledger.csv') if v['leaf_id']=='L0'),None),
                actual_split_count=result['external_gini_tree_split_count'],performance_eligible=True,native_proof_qualified=True,
                GD_rows=max([x['GD_rows'] for x in control['models']] or [0]),GD_nonzeros=max([x['GD_nonzeros'] for x in control['models']] or [0]),
                coefficient_generation_seconds=(control['root_generation'] or {}).get('generation_seconds',0.),new_columns=0,paid_source_solves=0,
                destination=str(d),fee_outer_seconds=read(fee/'receipt.json')['outer_seconds'])
            if terminal:
                text=Path(terminal['native_log']).read_text(encoding='utf-8',errors='replace')
                root=re.findall(r'Root relaxation: objective ([-+\d.eE]+), ([\d,]+) iterations, ([-+\d.eE]+) seconds',text)
                if root:r.update(native_root_relaxation_objective=float(root[-1][0]),native_root_simplex_iterations=int(root[-1][1].replace(',','')),native_root_relaxation_seconds=float(root[-1][2]))
                rl=re.findall(r'^\s*0\s+\d+\s+[-+\d.eE]+\s+\d+\s+\d+\s+[-+\d.eE]+\s+([-+\d.eE]+)\s+',text,re.M)
                if rl:r['printed_root_after_cuts_bound']=float(rl[-1])
                size=re.findall(r'Optimize a model with ([\d,]+) rows, ([\d,]+) columns and ([\d,]+) nonzeros',text)
                if size:r.update(dict(zip(['terminal_rows','terminal_columns','terminal_nonzeros'],[int(v.replace(',','')) for v in size[-1]])))
            (qual if isq else full).append(r)
    role_order={'K-20-S':0,'R-X20-S-T1':1,'K-35-U':2,'R-B35-S-T2':3,'K-15-S':4,'R-X35-S-T2':5}
    method_order={'BASE':0,'STOCK':1,'STOCK_GD':2}
    full.sort(key=lambda r:(role_order.get(r['role'],99),r['seed'],method_order[r['method']]))
    pairs=[]
    for c in [r for r in full if r['method']=='STOCK_GD']:
        ref=next((r for r in full if r['method']=='STOCK' and (r['role'],r['seed'])==(c['role'],c['seed'])),None)
        if ref is None:continue
        for k in ['input_SHA','physical_T','lambda_value','cap','source_commit','PE_SHA','DLL_SHA','H_semantic_SHA','H_fleet_SHA']:assert c[k]==ref[k],(c['role'],k)
        pairs.append(dict(role=c['role'],seed=c['seed'],same_PE=True,own_H_equal=True,
            **{'STOCK_'+k:ref[k] for k in ['U','L','certificate','relative_gap','T_produce','T_cert','T_verify','T_total']},
            **{'GD_'+k:c[k] for k in ['U','L','certificate','relative_gap','T_produce','T_cert','T_verify','T_total']},
            **{'delta_'+k:c[k]-ref[k] for k in ['U','L','relative_gap','T_produce','T_verify','T_total']}))
    bridges=[]
    for c in [r for r in full if r['method']=='STOCK_GD']:
        ref=next((r for r in full if r['method']=='BASE' and (r['role'],r['seed'])==(c['role'],c['seed'])),None)
        if ref is None:continue
        for k in ['input_SHA','physical_T','lambda_value','cap','source_commit','PE_SHA','DLL_SHA','H_semantic_SHA','H_fleet_SHA']:assert c[k]==ref[k],(c['role'],k)
        bridges.append(dict(role=c['role'],seed=c['seed'],same_PE=True,own_H_equal=True,
            **{'BASE_'+k:ref[k] for k in ['U','L','certificate','relative_gap','T_produce','T_cert','T_verify','T_total']},
            **{'GD_'+k:c[k] for k in ['U','L','certificate','relative_gap','T_produce','T_cert','T_verify','T_total']},
            **{'delta_'+k:c[k]-ref[k] for k in ['U','L','relative_gap','T_produce','T_verify','T_total']}))
    report=dict(UTC=utc(),new_arms=full,qualification=qual,pairs=pairs,same_PE_BASE_bridges=bridges,pending=pending,failed_qualifications=failed,all_entered_native_counts=counts,
        all_entered_observed_Native_Optimize=sum(r['observed_Optimize'] for r in counts),all_entered_observed_Native_returned=sum(r['observed_returned'] for r in counts),
        standalone_LP_Optimize_separate=5,all_entered_preserved=True,budget=budget(),Optimize=0,Native_load=0)
    write(OUT/'reports/full.json',report)
    for name,data in [('new_arms',full),('qualification',qual),('same_PE_pairs',pairs),('all_entered_native_counts',counts)]:table(OUT/'reports'/f'{name}.csv',data)
    if bridges:table(OUT/'reports/same_PE_BASE_bridges.csv',bridges)
    write(OUT/'cost_report.json',dict(UTC=utc(),charged_new_experiment_seconds=budget()['G1_seconds'],experiment=budget(),ceiling_seconds=28800,
        includes_own_H_all_solves_qualification_failures_and_postverification=True,nested_H_LP_MIP_Work_not_added_again=True,
        exact_oracle_seconds_separate=read(OUT/'qualification_exact_rows.json')['seconds'],
        inventory_units_exact_seconds_separate=read(OUT/'qualification_units.json')['seconds'],
        build_seconds_separate=sum(read(p)['outer_seconds'] for p in (OUT/'fees').glob('*/receipt.json') if read(p.parent/'launch.json')['kind']=='build'),
        unmetered_authoring_readonly_probes_not_invented_as_measured_cost=True,standalone_LP_Optimize=5))
    print(json.dumps(dict(arms=len(full),health=len(qual),pending=len(pending),failed=len(failed),pairs=pairs)),flush=True)
def trajectories():
    idle();records=[]
    for a in read(OUT/'reports/full.json')['new_arms']:
        d=Path(a['destination']);best=math.inf
        for item in read(d/'observations.json'):
            e=item['payload']
            if e['kind']!='witness' or float(e['objective'])>=best-1e-15:continue
            best=float(e['objective']);t=float(item['effective_available_seconds']);assert 0<=t<=a['T_produce']+.1
            records.append(dict(role=a['role'],method=a['method'],seed=a['seed'],producer_seconds=t,U=best,sequence=item['sequence'],
                committed_event_SHA=item['sha256'],source=e['source'],PE_SHA=a['PE_SHA'],raw_observation_SHA=sha(d/'observations.json'),
                clock='effective committed availability on producer wall; separate from Native time and T_total'))
        assert abs(best-a['U'])<=1e-8
    table(OUT/'reports/verified_U_trajectories.csv',records)
if __name__=='__main__':globals()[sys.argv[1]]()
