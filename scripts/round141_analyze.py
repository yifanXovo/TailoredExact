"""Compact sealed results and matched-reference identities; never starts Native."""
from round141_common import *
from round141_lp import projected_floor
from round141_math import membership
import csv,gzip,re
import round108_reader as core

ROLE_ORDER=['K-15-S','K-20-S','K-35-U','R-X20-S-T1','R-B35-S-T1','R-B35-S-T2','R-X35-S-T1','R-X35-S-T2']

def require_idle():
    own=os.environ.get('ROUND140_METERED_PARENT_LABEL')
    assert all(p['label']==own and p['kind']=='offline' for p in budget()['unclosed']), 'timed/native/build work is live'
    ordinary=os.environ.get('ROUND141_ORDINARY_PARENT_LABEL')
    assert all(p.parent.name==ordinary or (p.parent/'receipt.json').exists()
        for p in (OUT/'ordinary_steps').glob('*/launch.json')), 'another ordinary process is pending'

def csv_write(path,rows):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    keys=list(dict.fromkeys(k for row in rows for k in row))
    with path.open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=keys);writer.writeheader();writer.writerows(rows)

def first_integer_matrix(destination):
    d=Path(destination)
    events=[json.loads(s) for s in (d/'external/round141_events.jsonl').read_text().splitlines()]
    first=next(r for r in events if r['kind']=='floor_installed')
    payloads=[r['payload'] for r in read(d/'observations.json')]
    call=next(r for r in payloads if r['kind']=='call' and r['model_sha256']==first['SHA'])
    path=core.portable(ROOT,call['model_path']);assert sha(path)==first['SHA']
    names=[];section=False
    for line in path.read_text().splitlines():
        if line.strip()=='Subject To':section=True;continue
        if line.strip()=='Bounds':break
        if section and line.strip() and not line.lstrip().startswith('\\'):names.append(line.split(':',1)[0].strip())
    assert names[-1]=='r141_objective_floor' and names.count('r141_objective_floor')==1
    model=core.lp_model(path);floor=model['rows'].pop()
    return model,dict(SHA=first['SHA'],base_SHA=first['base_SHA'],floor_row=floor)

def LP():
    require_idle()
    actual=[];position_rows=[]
    for path in sorted((OUT/'LP').glob('*/result.json')):
        record=read(path)
        assert record['LP_Optimize']==1 and record['MIP_Optimize']==0
        assert record['Seed']==0 and record['Threads']==1 and record['status']==2 and record['qualified']
        assert record['native_identity']['sha256']==DLL_SHA and len(record['native_identity']['loaded_engine_modules'])==1
        assert sha(path.parent/'model.mps')==record['canonical_SHA']
        assert sha(path.parent/'solution.json.gz')==record['solution_SHA']
        actual.append(dict(result_path=path.relative_to(ROOT).as_posix(),result_SHA=sha(path),record=record))
        position_rows.append(dict(actual_position=len(actual),result_path=path.relative_to(ROOT).as_posix(),
            result_SHA=sha(path),**{k:record.get(k) for k in ['label','role','variant','pivot_kind','pivot','side',
                'threshold','ell','u','Seed','Threads','cap_seconds','status','qualified','L','beta',
                'construction_seconds','optimize_wall_seconds','Runtime','Work','canonical_SHA','solution_SHA',
                'writer_SHA','math_SHA','source_rev','source_dirty']},**record['quality']))
    assert len(actual)==39
    write(OUT/'reports/LP_positions.json',dict(positions=actual,LP_Optimize=39,MIP_Optimize=0,
        all_canonical_and_solution_hashes_rechecked=True,Optimize_in_this_reader=0))
    csv_write(OUT/'reports/LP_positions.csv',position_rows)
    comparison=read(OUT/'child_comparison.json');rows=[];projections=[]
    gini={}
    for spec in read(OUT/'gini_plan.json')['positions']:
        gini.setdefault(spec['role'],{})[spec['side']]=read(OUT/'LP'/spec['label']/'result.json')
    for role in comparison['roles']:
        for case in role['cases']:
            row=dict(role=role['role'],pivot_kind=case['pivot_kind'],pivot=case['pivot'],parent_L=role['parent']['L'],parent_beta=role['parent']['beta'])
            for variant in ['plain','conditional']:
                for side in ['low','high']:
                    solve=case['sides'][variant][side]
                    row[variant+'_'+side+'_L']=solve['L'];row[variant+'_'+side+'_beta']=solve['beta']
                row[variant+'_cover']=case[variant+'_cover'];row[variant+'_raw_cover']=case[variant+'_raw_cover']
                row[variant+'_construction_seconds']=sum(v['construction_seconds'] for v in case['sides'][variant].values())
                row[variant+'_LP_seconds']=sum(v['optimize_wall_seconds'] for v in case['sides'][variant].values())
            row.update(gini_low_L=gini[role['role']]['low']['L'],gini_high_L=gini[role['role']]['high']['L'],
                gini_cover=min(v['beta'] for v in gini[role['role']].values()),
                selected_for_projection=case['pivot']==role['selected_pivot'])
            rows.append(row)
        specs=[s for s in read(OUT/'projection_plan.json')['positions'] if s['role']==role['role']]
        values={s['variant']:(s,read(OUT/'LP'/s['label']/'result.json')) for s in specs}
        spec,original=values['d0'];_,conditional=values['d1']
        point=json.load(gzip.open(OUT/'LP'/spec['label']/'solution.json.gz','rt'))
        add=read(OUT/'domains'/spec['role']/'additions.json');K=math.fsum(point[k] for k in membership(add,spec['threshold']))
        projected=projected_floor(K,spec['ell'],spec['u'],spec['pivot'],*spec['betas'])
        projections.append(dict(role=role['role'],threshold=spec['threshold'],pivot=spec['pivot'],ell=spec['ell'],u=spec['u'],
            beta0=spec['betas'][0],beta1=spec['betas'][1],D0_L=original['L'],D1_L=conditional['L'],
            D1_increment=conditional['L']-original['L'],D0_point_K=K,D1_projected_floor_at_D0=projected,
            projection_violation=projected-original['L'],
            D0_seconds=original['construction_seconds']+original['optimize_wall_seconds'],
            D1_seconds=conditional['construction_seconds']+conditional['optimize_wall_seconds']))
    write(OUT/'reports/LP.json',dict(rows=rows,projection=projections,Seed=0,Threads=1,
        LP_Optimize=len(actual),MIP_Optimize=0,all_continuous=True,parent_TC_TC2_retained=True,
        actual_positions='reports/LP_positions.json',all_canonical_and_solution_hashes_rechecked=True,
        actual_source_cutoff_matching=read(OUT/'gini_match.json'),numerical_not_rational_solver_certificates=True))
    csv_write(OUT/'reports/LP.csv',rows);csv_write(OUT/'reports/projection.csv',projections)

def full():
    require_idle()
    rows=[];qualification=[];missing=[];failures=[]
    for matrix_path in sorted(OUT.glob('*_matrix.json')):
        matrix=read(matrix_path)
        if 'batch' not in matrix:continue
        batch=matrix['batch'];is_qualification=batch.startswith('qualification')
        for group in matrix['groups']:
            launch=group['launch'];d=Path(launch['destination'])
            if not (d/'verification_closeout.json').exists():
                item=dict(batch=batch,position=group['position'],role=launch['id'],method=launch['method'],seed=launch['seed'],
                    state='SEALED_UNQUALIFIED' if (d/'producer_seal.json').exists() else 'NOT_STARTED',
                    destination=str(d),is_qualification=is_qualification)
                (failures if item['state']=='SEALED_UNQUALIFIED' else missing).append(item);continue
            arm=read(d/'round135_endpoint.json');audit=read(d/'audit.json')
            assert arm['native_proof_qualified'] and arm['performance_eligible'] and not audit['source_rejections']
            chain=read(d/'round141_chain_audit.json');assert chain['PASS']
            assert arm['T_cert'] is None if not arm['certificate'] else arm['T_cert']==arm['T_produce']
            ledger=list(csv.DictReader((d/'external/paper_optimize_ledger.csv').open(newline='')))
            terminal=next((r for r in reversed(ledger) if 'terminal' in r['native_log']),None)
            events=[json.loads(s) for s in (d/'external/round141_events.jsonl').read_text().splitlines()]
            probes=[r for r in events if r['kind']=='count_probe_returned']
            raw=read(d/'result.json');raw=raw[0] if isinstance(raw,list) else raw
            controls=read(d/'round141_control_audit.json');identity=read(OUT/group['group']/'identity.json')
            observed=[row['payload'] for row in read(d/'observations.json')]
            call_by_log={row['native_log_path']:row['call'] for row in observed if row['kind']=='call'}
            terminal_call=call_by_log[terminal['native_log']] if terminal else None
            quality=next((row for row in observed if row['kind']=='native_quality' and row['call']==terminal_call),None)
            am=core.rows(d/'external/adaptive_mass_decision_ledger.csv')
            lp=core.rows(d/'external/lp_status_ledger.csv')
            p=launch['panel'];record=dict(batch=batch,position=group['position'],role=launch['id'],method=launch['method'],seed=launch['seed'],
                formal_entered=not is_qualification,legacy_formal_performance_flag=arm.get('formal_performance'),
                input_SHA=p['input_sha256'],physical_T=p['T_seconds'],lambda_value=p['lambda'],cap=launch['cap_seconds'],
                source_commit=identity['measured_source_commit'],PE_SHA=identity['candidate_binary_sha256'],DLL_SHA=identity['dll_sha256'],
                **{k:arm[k] for k in ['U','L','certificate','signed_gap','relative_gap','T_produce','T_cert','T_verify','T_total','H_complete','H_semantic_SHA','H_fleet_SHA']},
                external_merged_final_L=arm['L'],
                terminal_native_return_ObjBoundC=quality['ObjBoundC'] if quality else None,
                terminal_native_return_ObjVal=quality['ObjVal'] if quality else None,
                LP_calls=sum(r['solve_kind']=='LP' and not r['leaf_id'].startswith('round141_count_') for r in ledger),
                count_LP_calls=sum(r['leaf_id'].startswith('round141_count_') for r in ledger),
                target_calls=sum('TARGET' in r['solve_kind'] for r in ledger),terminal_calls=sum(r['solve_kind']=='MIP' for r in ledger),
                root_LP_seconds=sum(float(r['solver_runtime']) for r in ledger if r['solve_kind']=='LP' and r['leaf_id']=='L0'),
                root_LP_Work=sum(float(r['work']) for r in ledger if r['solve_kind']=='LP' and r['leaf_id']=='L0'),
                Gini_LP_seconds=sum(float(r['solver_runtime']) for r in ledger if r['solve_kind']=='LP' and not r['leaf_id'].startswith('round141_count_')),
                count_LP_seconds=sum(float(r['solver_runtime']) for r in ledger if r['leaf_id'].startswith('round141_count_')),
                target_seconds=sum(float(r['solver_runtime']) for r in ledger if 'TARGET' in r['solve_kind']),
                target_Work=sum(float(r['work']) for r in ledger if 'TARGET' in r['solve_kind']),
                terminal_seconds=sum(float(r['solver_runtime']) for r in ledger if r['solve_kind']=='MIP'),
                probe_construction_seconds=sum(r['construction_seconds'] for r in probes),probe_total_seconds=sum(r['total_seconds'] for r in probes),
                probe_Work=sum(r['Work'] for r in probes),Native_total_Work=sum(float(r['work']) for r in ledger),
                terminal_Work=float(terminal['work']) if terminal else 0,terminal_nodes=float(terminal['nodes']) if terminal else 0,
                root_L=next((float(r['lower_bound']) for r in lp if r['leaf_id']=='L0'),None),
                first_AM_action=am[0]['selected_action'] if am else None,
                AM_action_sequence=';'.join(v['selected_action'] for v in am),
                actual_split_count=raw['external_gini_tree_split_count'],pair_ready=controls['outcome']['pair_ready'],
                root_threshold=controls['choice']['threshold_units']+'*2^'+str(controls['choice']['threshold_exponent']) if controls['choice'] else None,
                root_pivot=controls['choice']['pivot'] if controls['choice'] else None,
                root_SHA=controls['choice']['root_SHA'] if controls['choice'] else None,
                probe0_SHA=probes[0]['model_SHA'] if probes else None,probe1_SHA=probes[1]['model_SHA'] if len(probes)>1 else None,
                beta0=controls['pair']['beta0'] if controls['pair'] else None,beta1=controls['pair']['beta1'] if controls['pair'] else None,
                scope_count_proof_binding=True,destination=str(d))
            if terminal:
                text=Path(terminal['native_log']).read_text();match=re.search(r'Best objective\s+([-+0-9.eE]+), best bound\s+([-+0-9.eE]+)',text)
                if match:record.update(printed_terminal_ObjVal=float(match[1]),printed_terminal_ObjBound=float(match[2]))
            (qualification if is_qualification else rows).append(record)
    old=read(ROOT/'results/unified_exact_round140/reports/full.json')
    pinned=git('show',SCIENCE140+':results/unified_exact_round140/reports/full.json')
    assert json.loads(pinned)==old
    roles={r['role']:r['panel'] for r in read(ROOT/'results/unified_exact_round140/baseline_reuse.json')['positions']}
    reused=[]
    for record in old['new_arms']+old['reused_arms']:
        if record.get('seed',0)!=0:continue
        if record.get('method') not in ['base','both','TC_STOCK','TC2_STOCK']:continue
        panel=roles[record['role']]
        reused.append(dict(record,physical_T=panel['T_seconds'],lambda_value=panel['lambda'],
            reference_science_commit=SCIENCE140,reused_new_Optimize=0,
            source_identity_policy='Original PE/source/clocks retained; cross-version method comparison, not same-PE intervention'))
    rows.sort(key=lambda r:(ROLE_ORDER.index(r['role']),r['method'],r['seed']))
    pairs=[];conditional_pairs=[]
    for candidate in rows:
        for reference in reused:
            if (candidate['role'],candidate['seed'])!=(reference['role'],reference.get('seed',0)):continue
            assert candidate['input_SHA']==reference['input_SHA']
            assert candidate['physical_T']==reference['physical_T'] and candidate['lambda_value']==reference['lambda_value']
            assert candidate['cap']==reference['cap']
            assert candidate['H_semantic_SHA']==reference['H_semantic_SHA'] and candidate['H_fleet_SHA']==reference['H_fleet_SHA']
            pairs.append(dict(role=candidate['role'],candidate=candidate['method'],reference=reference['method'],seed=candidate['seed'],
                delta_U=candidate['U']-reference['U'],delta_L=candidate['L']-reference['L'],
                candidate_certificate=candidate['certificate'],reference_certificate=reference['certificate'],
                delta_T_produce=candidate['T_produce']-reference['T_produce'],delta_T_total=candidate['T_total']-reference['T_total'],
                T_produce_threshold=max(10.,.1*min(candidate['T_produce'],reference['T_produce'])),
                T_total_threshold=max(10.,.1*min(candidate['T_total'],reference['T_total'])),
                same_input_physics_objective_cap_seed_H=True,same_PE=False))
        if candidate['method']=='D1':
            controls=[r for r in rows if r['method']=='D0' and r['role']==candidate['role'] and r['seed']==candidate['seed']]
            for control in controls:
                for key in ['input_SHA','physical_T','lambda_value','cap','source_commit','PE_SHA','H_semantic_SHA','H_fleet_SHA']:
                    assert candidate[key]==control[key],('D0/D1 common component mismatch',key,candidate['role'])
                exposed=candidate['pair_ready'] and control['pair_ready']
                d1_floor=d0_floor=None
                if exposed:
                    for key in ['root_SHA','root_pivot','probe0_SHA','probe1_SHA','beta0','beta1']:
                        assert candidate[key]==control[key],('D0/D1 proof component mismatch',key,candidate['role'])
                    d1_matrix,d1_floor=first_integer_matrix(candidate['destination'])
                    d0_matrix,d0_floor=first_integer_matrix(control['destination'])
                    assert d1_matrix==d0_matrix and d1_floor['base_SHA']==d0_floor['base_SHA'],('D0/D1 first integer matrix differs beyond floor',candidate['role'])
                conditional_pairs.append(dict(role=candidate['role'],seed=candidate['seed'],same_PE=True,
                    same_paid_proof_matrices_and_values=exposed,D1_U=candidate['U'],D0_U=control['U'],D1_L=candidate['L'],D0_L=control['L'],
                    first_integer_matrices_equal_except_floor=True if exposed else None,D1_first_integer=d1_floor,D0_first_integer=d0_floor,
                    attribution_scope='exposed floor-row comparison' if exposed else 'unexposed or incomplete pair: report fallback outcome, not a failed mechanism',
                    D1_T_produce=candidate['T_produce'],D0_T_produce=control['T_produce'],D1_T_total=candidate['T_total'],D0_T_total=control['T_total'],
                    delta_U=candidate['U']-control['U'],delta_L=candidate['L']-control['L'],
                    delta_T_produce=candidate['T_produce']-control['T_produce'],delta_T_total=candidate['T_total']-control['T_total'],
                    D1_terminal_Work=candidate['terminal_Work'],D0_terminal_Work=control['terminal_Work'],
                    D1_terminal_nodes=candidate['terminal_nodes'],D0_terminal_nodes=control['terminal_nodes']))
    write(OUT/'reports/full.json',dict(UTC=utc(),new_arms=rows,qualification=qualification,reused_arms=reused,
        pairs=pairs,conditional_pairs=conditional_pairs,failures=failures,unstarted=missing,all_entered_preserved=True,budget=budget(),Optimize=0,
        clocks='Registered producer + mandatory complete pure reader; later independent science reviews/chain audits are separately measured',
        formal_scope='Preregistered full-cap research comparisons; legacy R108 formal_performance classification is retained, not used to classify current stages'))
    csv_write(OUT/'reports/new_arms.csv',rows);csv_write(OUT/'reports/qualification.csv',qualification)
    csv_write(OUT/'reports/reused_arms.csv',reused)

if __name__=='__main__':globals()[sys.argv[1]]()
