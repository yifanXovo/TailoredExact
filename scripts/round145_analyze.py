"""Pure aggregation of LP retention, complete clocks, Native size and decisions."""
import csv,re
from round145_common import *
def idle():assert not budget()['unclosed'],'heavy aggregation waits for all timed producers'
def rows(path):
    if not path.exists():return []
    with path.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def table(path,values):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in values for k in r)));w.writeheader();w.writerows(values)

def LP():
    idle();facts=[]
    for path in sorted((OUT/'LP').glob('*/result.json')):
        r=read(path);assert r['qualified'] and sha(path.parent/'model.mps')==r['model_SHA']
        facts.append(r)
    compact=[read(p) for p in sorted((OUT/'compact').glob('*/result.json'))]
    assert len(facts)==9 and len(compact)==2
    write(OUT/'reports/LP.json',dict(PASS=True,source_LPs=facts,compiled_compact_LPs=compact,
        new_source_Optimize=9,new_compact_Optimize=2,reused_RN_baselines_Optimize=0,
        complete_objective_and_old_matrix_scope_matched=True,values_numerical_not_rational_optimality_certificates=True,
        strong_old_carrier='RN + physical STOCK + TC + TC2',source_choice='BASE + RN + NC1/NC2 + TS1..4'))
    table(OUT/'reports/LP.csv',[{k:r[k] for k in ['role','variant','L','inherited_RN_L','gain_over_RN','g','weighted_penalty','rows','columns','nonzeros','Runtime','Work','iterations']} for r in facts])
    table(OUT/'reports/compact.csv',compact)
    lines=['# Round145 finite matched LP decision','',
        'RN baselines are reused from sealed R144 production-capped sources; no baseline reoptimization. Every new optimization uses Seed0, Threads1, affinity4, serial timing and the complete original objective, old matrix, finite bounds, cutoff, support and g domain. Values are qualified numerical continuous optima, not Native MIP roots or rational certificates.','',
        '| Role | Addition to RN | Complete objective | Gain over RN | G | Weighted penalty | Runtime s | Rows / columns / NZ |',
        '| --- | --- | --- | --- | --- | --- | --- | --- |']
    for r in facts:lines.append(f'| {r["role"]} | {r["variant"]} | {r["L"]:.12g} | {r["gain_over_RN"]:.12g} | {r["g"]:.12g} | {r["weighted_penalty"]:.12g} | {r["Runtime"]:.6g} | {r["rows"]} / {r["columns"]} / {r["nonzeros"]} |')
    lines+=['','K35 joint exceeds strong old O by0.00528600043315; O+joint matches joint to numerical precision. This is nested same-objective numerical information gain, not a global formulation dominance claim. NC and TS each improve K35; the joint exceeds NC alone by1.7431164196e-5. RX20 NC alone has zero objective increment, while TS gives the whole measured0.00657748754 joint increment; an NC-violating TS optimum is not a claim that all TS optima violate NC. K20, previously a no-PC RN-P role, now gains0.02765978722. No second no-PC role LP is needed to choose the candidate.','',
        '| Role | Compiled transported compact objective | Joint-source loss | Increment retained | PC NZ / RN columns |',
        '| --- | --- | --- | --- | --- |']
    for r in compact:lines.append(f'| {r["role"]} | {r["L"]:.12g} | {r["root_retention_loss"]:.12g} | {r["NC_TS_increment_retained_fraction"]:.12g} | {r["PC_nonzeros"]} / 0 |')
    lines+=['','Actual compiled interval arithmetic, full added-block row list, exact Fraction box-validity checks and Native coefficient/RHS readback are retained. NC/TS add6 source rows and zero columns beyond RN. One original-variable PC and zero RN columns remain in each formal compact model. The two compact LPs use the diagnostic actual floating source; production R140-down NC and outward TS rows have their own compiled oracle/readback, and the short actual production health confirms K20 objective agreement to≈5e-16.','',
        'The11 new standalone LPs comprise6 cells of the two-role NC/TS/joint diagnostic, strong O and nested O+joint, one former no-PC joint source and2 compiled compact solves. Saved primal/dual matrices retain all activities, signed coefficients, count ranges, quality and source costs. The initial baseline_residual labeling error was corrected from saved old points and matrices with zero Optimize; the amendment and original helper hashes are preserved.','',
        'Decision: route B, one uniform BASE+RN+NC+TS source projected once after current own H/initial root. No old stock/count add-on source, all-threshold products, repeat separation, floor grid or second full route A panel is opened.']
    (OUT/'LP_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('PASS 9 source + 2 compact LPs; route B information and actual transport retention')
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
                v=dict(batch=batch,position=g['position'],role=l['id'],method=l['R145_method'],destination=str(d))
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
            r=dict(batch=batch,position=g['position'],role=l['id'],method=l['R145_method'],seed=l['seed'],formal_entered=not isq,
                input_SHA=p['input_sha256'],physical_T=p['T_seconds'],lambda_value=p['lambda'],cap=l['cap_seconds'],
                source_commit=identity['measured_source_commit'],PE_SHA=identity['candidate_binary_sha256'],DLL_SHA=identity['dll_sha256'],
                **{k:a[k] for k in ['U','L','certificate','signed_gap','relative_gap','T_produce','T_cert','T_verify','T_total','H_complete','H_semantic_SHA','H_fleet_SHA','declared_calls','returned_calls']},
                physical_G=audit['physical']['G'],physical_P=audit['physical']['P'],weighted_physical_penalty=a['U']-audit['physical']['G'],
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
                source_L=source.get('source_objective'),source_RN_columns=source.get('source_RN_columns',0),source_solves=source['source_solves'],PC_emitted=source.get('PC_emitted',False),formal_RN_columns=0,
                PC_nonzeros=max((f.get('PC_nonzeros',0) for f in control['models']),default=0))
            else:r.update(source_preparation_seconds=0.,source_solves=0,PC_emitted=False,
                formal_RN_columns=max((f['RN_columns'] for f in control['models']),default=0))
            r['observed_source_minus_formal_first_root_L']=(r['source_L']-r['root_L']) if source and r.get('source_L') is not None and r.get('root_L') is not None else None
            if terminal:
                text=Path(terminal['native_log']).read_text();pres=re.findall(r'Presolved: ([\d,]+) rows, ([\d,]+) columns, ([\d,]+) nonzeros',text)
                if pres:r.update(presolved_rows=int(pres[-1][0].replace(',','')),presolved_columns=int(pres[-1][1].replace(',','')),presolved_nonzeros=int(pres[-1][2].replace(',','')))
                root=re.findall(r'Root relaxation: objective ([-+\d.eE]+), ([\d,]+) iterations, ([\d.]+) seconds',text)
                if root:r.update(native_root_relaxation_objective=float(root[-1][0]),native_root_simplex_iterations=int(root[-1][1].replace(',','')),native_root_relaxation_seconds=float(root[-1][2]))
                root_lines=re.findall(r'^\s*0\s+\d+\s+[-+\d.eE]+\s+\d+\s+\d+\s+[-+\d.eE]+\s+([-+\d.eE]+)\s+',text,re.M)
                if root_lines:r['printed_root_after_cuts_bound']=float(root_lines[-1])
            (qual if isq else full).append(r)
    pairs=[]
    for c in [r for r in full if r['method']=='RNJP']:
        off=next((r for r in full if r['method']=='OFF' and (r['role'],r['seed'])==(c['role'],c['seed'])),None)
        if not off:continue
        for k in ['input_SHA','physical_T','lambda_value','cap','source_commit','PE_SHA','H_semantic_SHA','H_fleet_SHA']:assert c[k]==off[k],(c['role'],k)
        pairs.append(dict(role=c['role'],seed=c['seed'],same_PE=True,own_H_equal=True,off_U=off['U'],RNJP_U=c['U'],off_L=off['L'],RNJP_L=c['L'],
            off_certificate=off['certificate'],RNJP_certificate=c['certificate'],off_gap=off['relative_gap'],RNJP_gap=c['relative_gap'],
            **{'delta_'+k:c[k]-off[k] for k in ['U','L','relative_gap','T_produce','T_verify','T_total']},off_T_cert=off['T_cert'],RNJP_T_cert=c['T_cert']))
    bridges=[]
    for rn in [r for r in full if r['method']=='RNP']:
        c=next(r for r in full if r['method']=='RNJP' and (r['role'],r['seed'])==(rn['role'],rn['seed']))
        for k in ['input_SHA','physical_T','lambda_value','cap','source_commit','PE_SHA','DLL_SHA','H_semantic_SHA','H_fleet_SHA']:
            assert c[k]==rn[k],(c['role'],'RN bridge',k)
        assert c['formal_RN_columns']==0 and rn['formal_RN_columns']==0
        bridges.append(dict(role=c['role'],seed=c['seed'],same_PE=True,own_H_equal=True,
            RNJP_U=c['U'],RNP_U=rn['U'],RNJP_L=c['L'],RNP_L=rn['L'],RNJP_gap=c['relative_gap'],RNP_gap=rn['relative_gap'],
            RNJP_formal_RN_columns=0,RNP_formal_RN_columns=rn['formal_RN_columns'],
            **{'delta_RNJP_minus_RNP_'+k:c[k]-rn[k] for k in ['U','L','relative_gap','T_produce','T_verify','T_total','terminal_Work','terminal_nodes']},
            causal_column_count_isolation_not_claimed=True))
    write(OUT/'reports/full.json',dict(UTC=utc(),new_arms=full,qualification=qual,pairs=pairs,RNP_bridges=bridges,failed_qualifications=failed,pending=pending,
        all_entered_native_counts=native_counts,all_entered_observed_Native_Optimize=sum(r['observed_Optimize'] for r in native_counts),
        all_entered_observed_Native_returned=sum(r['observed_returned'] for r in native_counts),
        standalone_LP_Optimize_separate=11,reader_only_recoveries_Optimize=0,all_entered_preserved=True,budget=budget(),Optimize=0))
    table(OUT/'reports/new_arms.csv',full);table(OUT/'reports/qualification.csv',qual);table(OUT/'reports/same_PE_pairs.csv',pairs)
    table(OUT/'reports/same_PE_RNP_bridges.csv',bridges)
    table(OUT/'reports/all_entered_native_counts.csv',native_counts)
    write(OUT/'cost_report.json',dict(UTC=utc(),charged_new_experiment_seconds=budget()['G1_seconds'],experiment=budget(),ceiling_seconds=28800,
        outer_fees_including_failed_readers_and_all_required_postverification=True,nested_H_LP_MIP_Work_not_added_again=True,
        offline_arithmetic_seconds=read(OUT/'qualification_exact_writer.json')['seconds']+sum(read(p)['outer_seconds'] for p in (OUT/'ordinary_steps').glob('saved_point_NC_PC*receipt.json')),
        untimed_identity_probe_imports_and_authoring_not_invented_as_measured_cost=True,
        build_seconds_separate=sum(read(p)['outer_seconds'] for p in (OUT/'fees').glob('*/receipt.json') if read(p.parent/'launch.json')['kind']=='build'),
        all_entered_observed_Native_Optimize=sum(r['observed_Optimize'] for r in native_counts),
        failed_qualification_observed_Native_Optimize=sum(r['observed_Optimize'] for r in native_counts if r['qualification'] and not r['proof_qualified']),
        standalone_LP_Optimize_separate=11,reader_only_recoveries_Optimize=0))
    print(json.dumps(dict(arms=len(full),qualified_health=len(qual),failed_qualifications=len(failed),pending=len(pending),pairs=pairs)),flush=True)

if __name__=='__main__':globals()[sys.argv[1]]()
