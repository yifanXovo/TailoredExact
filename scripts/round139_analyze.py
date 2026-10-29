"""Pure sealed-run summaries. No live raw decoding, optimizer or native library."""
from round139_common import *
import collections,csv,re
import round108_reader as core
from round138_analyze import csv_write

def native_records(d,p,method,seed):
    observations=read(d/'observations.json');witnesses=[]
    call_by_log={Path(v['payload']['native_log_path']):v['payload']['call'] for v in observations if v['payload']['kind']=='call'}
    runtime_by_log={Path(v['native_log']):float(v['solver_runtime']) for v in csv.DictReader((d/'external/paper_optimize_ledger.csv').open(newline=''))}
    for observed in observations:
        e=observed['payload']
        if e['kind']!='witness':continue
        physical=core.full_fleet(ROOT,p,e)
        assert abs(physical['F']-e['objective'])<=1e-7
        assert abs(physical['G']-e['G'])<=1e-7 and abs(physical['P']-e['P'])<=1e-7
        witnesses.append(dict(sequence=e['sequence'],call=e['call'],source=e['source'],improving=bool(e['improving']),
            F=physical['F'],G=physical['G'],P=physical['P'],physical_verified=True,
            first_observed_seconds=observed['first_observed_seconds'],effective_available_seconds=observed['effective_available_seconds'],
            discovery_timestamp_recorded=False))
    native=[]
    for path in sorted((d/'external/native_logs').glob('*mip.gurobi.log')):
        cid=call_by_log.get(path);assert cid is not None,('unbound native diagnostic log',path)
        text=path.read_text();events=[]
        for line in text.splitlines():
            if not re.match(r'^[H*]',line):continue
            tokens=line.split();tm=re.search(r'\s([0-9.]+)s\s*$',line)
            incumbent=None
            if tm and len(tokens)>=8 and tokens[-3].endswith('%'):
                try:incumbent=float(tokens[-5])
                except ValueError:pass
            same=[w['sequence'] for w in witnesses if w['call']==cid and incumbent is not None and abs(w['F']-incumbent)<=1e-6]
            other=[w['sequence'] for w in witnesses if w['call']!=cid and incumbent is not None and abs(w['F']-incumbent)<=1e-6]
            events.append(dict(line=line,approx_native_seconds=float(tm[1]) if tm else None,
                rounded_native_incumbent=incumbent,same_call_numeric_witness_matches=same,other_call_numeric_witness_matches=other))
        start_lines=[line for line in text.splitlines() if 'MIP start' in line or 'previous solve' in line]
        starts=[float(m[1]) for line in start_lines for m in [re.search(r'objective\s+([-+0-9.eE]+)',line)] if m]
        submitted_path=path.with_name(path.name+'.round68.start.json')
        submitted=read(submitted_path) if submitted_path.exists() else None
        initial_start=submitted['objective'] if submitted and submitted.get('submitted') else None
        final=re.search(r'Best objective\s+([-+0-9.eE]+)',text)
        native.append(dict(call=cid,path=str(path),SHA=sha(path),terminal='terminal' in path.name,
            native_solver_seconds=runtime_by_log[path],native_initial_submitted_Start_objective=initial_start,
            initial_Start_source_SHA=sha(submitted_path) if initial_start is not None else None,
            logged_Start_objectives=starts,initial_at_zero_is_known_input_not_discovery=True,
            native_final_logged_objective=float(final[1]) if final else None,Start_lines=start_lines,
            root=next((line for line in text.splitlines() if line.startswith('Root relaxation:')),None),events=events))
    return dict(role=p['id'],method=method,seed=seed,witnesses=witnesses,native=native,
        witness_sources=dict(collections.Counter(w['source'] for w in witnesses)),
        saved_MIPSOL_witness_vectors=sum('MIPSOL' in w['source'] for w in witnesses),
        scope='All saved witness vectors independently physically replayed, including H, before-call, MIPSOL and final vectors where present. Same-call rounded-objective matching is numeric consistency, not an exact discovery clock or unique vector identity; other-call numeric coincidences are separate. Controller observation/publication times remain separate.')

def full():
    assert not budget()['unclosed'],'never analyze live raw'
    rows=[];qualification=[];missing=[];operations=[];details=[]
    for path in sorted(OUT.glob('*_matrix.json')):
        matrix=read(path);batch=matrix['batch']
        for group in matrix['groups']:
            l=group['launch'];d=Path(l['destination'])
            if not (d/'verification_closeout.json').exists():
                missing.append(dict(batch=batch,position=group['position'],role=l['id'],method=l['placement'],seed=l['seed']));continue
            e=read(d/'round135_endpoint.json');audit=read(d/'audit.json');physical=audit['physical'];result=read(d/'result.json')
            assert e['native_proof_qualified'] and e['performance_eligible'] and not audit['source_rejections']
            assert e['T_cert'] is None if not e['certificate'] else e['T_cert']==e['T_produce']
            ledger=list(csv.DictReader((d/'external/paper_optimize_ledger.csv').open(newline='')))
            am=list(csv.DictReader((d/'external/adaptive_mass_decision_ledger.csv').open(newline='')))
            lp=list(csv.DictReader((d/'external/lp_status_ledger.csv').open(newline='')))
            obs=read(d/'observations.json');calls={v['payload']['call']:v['payload'] for v in obs if v['payload']['kind']=='call'}
            qualities=[v['payload'] for v in obs if v['payload']['kind']=='native_quality']
            terminal=next((r for r in reversed(ledger) if 'terminal' in r['native_log']),None)
            tq=None
            if terminal:
                cid=next(cid for cid,c in calls.items() if c['native_log_path']==terminal['native_log'])
                tq=next((v for v in qualities if v['call']==cid),None)
            row=dict(batch=batch,position=group['position'],role=l['id'],method=l['placement'],seed=l['seed'],
                input_SHA=l['panel']['input_sha256'],PE_SHA=e['PE_SHA'],source_commit=e['source_commit'],
                physical_T=l['panel']['T_seconds'],lambda_value=l['panel']['lambda'],cap=l['cap_seconds'],
                certificate=e['certificate'],U=e['U'],L=e['L'],signed_gap=e['U']-e['L'],relative_gap=e['relative_gap'],
                T_produce=e['T_produce'],T_cert=e['T_cert'],T_verify=e['T_verify'],T_total=e['T_total'],
                G=physical['G'],P=physical['P'],H_complete=e['H_complete'],H_semantic_SHA=e['H_semantic_SHA'],H_fleet_SHA=e['H_fleet_SHA'],
                LP_calls=sum(r['solve_kind']=='LP' for r in ledger),target_calls=sum('target' in r['native_log'] for r in ledger),
                terminal_calls=sum('terminal' in r['native_log'] for r in ledger),
                LP_seconds=sum(float(r['solver_runtime']) for r in ledger if r['solve_kind']=='LP'),
                target_seconds=sum(float(r['solver_runtime']) for r in ledger if 'target' in r['native_log']),
                terminal_seconds=sum(float(r['solver_runtime']) for r in ledger if 'terminal' in r['native_log']),
                Work=sum(float(r['work']) for r in ledger),nodes=sum(float(r['nodes']) for r in ledger),
                first_AM_action=am[0]['selected_action'] if am else None,
                AM_action_sequence=[v['selected_action'] for v in am],
                AM_parent_bound_sequence=[float(v['B_p']) for v in am],
                root_L=next((float(v['lower_bound']) for v in lp if v['leaf_id']=='L0'),None),
                terminal_native_return_ObjBoundC=tq['ObjBoundC'] if tq else None,
                terminal_native_return_ObjVal=tq['ObjVal'] if tq else None,
                external_merged_final_L=e['L'],
                model_build_seconds=result.get('external_gini_tree_model_build_seconds'),
                artifact_generations=result.get('external_gini_tree_canonical_artifact_generation_count'),
                explicit_discards=result.get('external_gini_tree_explicit_leaf_model_discard_count'),
                retained_reuse=[int(v['in_memory_model_reused']) for v in ledger],
                destination=str(d),performance_eligible=e['performance_eligible'],native_proof_qualified=e['native_proof_qualified'])
            (qualification if batch=='qualification' else rows).append(row)
            operations += [dict(batch=batch,position=group['position'],role=l['id'],method=l['placement'],seed=l['seed'],**v) for v in ledger]
            details.append(dict(batch=batch,position=group['position'],role=l['id'],method=l['placement'],seed=l['seed'],AM=am,
                LP=lp,artifact_epochs=[dict(call=c['call'],leaf=c['leaf'],SHA=c['model_sha256'],alpha=c['lower_g'],beta=c['upper_g'],cutoff=c['cutoff']) for c in calls.values()]))
    inherited=[]
    for b in read(OUT/'baseline_reuse.json')['positions']:
        for method,key in [('base','base'),('both','both')]:
            old=b[key];r=dict(role=b['role'],method=method,seed=0,reused=True,
                measured_source=b['BASE_measured_source' if method=='base' else 'BOTH_measured_source'],
                position=b['base_position' if method=='base' else 'both_position'],destination=old['destination'],
                certificate=old['certificate']=='True',input_SHA=old['input_SHA'],PE_SHA=old['PE_SHA'],cap=int(old['cap']),
                native_proof_qualified=old['native_proof_qualified']=='True',performance_eligible=old['performance_eligible']=='True')
            for k in ['U','L','T_produce','T_cert','T_verify','T_total','G','P_avg','relative_gap']:
                r[k]=float(old[k]) if old.get(k) else None
            r['signed_gap']=r['U']-r['L'];inherited.append(r)
            old_endpoint=read(Path(old['destination'])/'round135_endpoint.json')
            for key in ['H_complete','H_semantic_SHA','H_fleet_SHA']:
                r[key]=old_endpoint[key]
    pairs=[]
    for r in rows:
        for baseline in ['base','both']:
            matches=[a for a in inherited if (a['role'],a['method'],a['seed'])==(r['role'],baseline,r['seed'])]
            if not matches:continue
            b=matches[0];pair=dict(role=r['role'],seed=r['seed'],reference=baseline,candidate=r['method'],batch=r['batch'],
                base_U=b['U'],new_U=r['U'],delta_U=r['U']-b['U'],base_L=b['L'],new_L=r['L'],delta_L=r['L']-b['L'],
                base_signed_gap=b['signed_gap'],new_signed_gap=r['signed_gap'],base_certificate=b['certificate'],new_certificate=r['certificate'],
                base_T_cert=b['T_cert'],new_T_cert=r['T_cert'])
            assert r['H_complete'] and b['H_complete']
            assert r['H_semantic_SHA']==b['H_semantic_SHA'] and r['H_fleet_SHA']==b['H_fleet_SHA'],('initial H differs',r['role'],r['method'],baseline)
            pair['identical_initial_H_semantics_and_fleet']=True
            if b['certificate'] and r['certificate']:
                pair['time_difference']=r['T_cert']-b['T_cert'];pair['time_threshold']=max(10.,.1*min(r['T_cert'],b['T_cert']))
                pair['substantive_time_difference']=abs(pair['time_difference'])>=pair['time_threshold']
            pairs.append(pair)
    csv_write(OUT/'reports/new_arms.csv',rows);csv_write(OUT/'reports/qualification_arms.csv',qualification)
    csv_write(OUT/'reports/reused_arms.csv',inherited);csv_write(OUT/'reports/pairs.csv',pairs);csv_write(OUT/'reports/native_calls.csv',operations)
    write(OUT/'reports/control_paths.json',dict(positions=details,Optimize=0))
    write(OUT/'reports/full.json',dict(UTC=utc(),new_arms=rows,reused_arms=inherited,qualification=qualification,pairs=pairs,
        missing=missing,complete=not missing,budget=budget(),known_panel_configurations=8,known_base_inputs=6,
        all_entered_positions_retained=True,no_censored_time_imputation=True,Optimize=0))
    print(json.dumps(dict(completed=len(rows),qualification=len(qualification),missing=missing,
        endpoints=[{k:r[k] for k in ['role','method','seed','certificate','U','L','T_cert','first_AM_action']} for r in rows]),ensure_ascii=False))

def selected_vectors():
    assert not budget()['unclosed'];out=[]
    for b in read(OUT/'baseline_reuse.json')['positions']:
        if b['role'] not in ['K-20-S','R-B35-S-T2']:continue
        for method in ['base','both']:
            out.append(native_records(Path(b[method]['destination']),b['panel'],method,0))
    for path in sorted(OUT.glob('*_matrix.json')):
        if path.name=='qualification_matrix.json':continue
        for g in read(path)['groups']:
            l=g['launch'];d=Path(l['destination'])
            if l['id'] in ['K-20-S','R-B35-S-T2'] and (d/'verification_closeout.json').exists():
                out.append(native_records(d,l['panel'],l['placement'],l['seed']))
    write(OUT/'reports/native_trajectories_and_witnesses.json',dict(UTC=utc(),positions=out,Optimize=0,
        timing='Rounded native-log model-objective clock; observation timestamps are not discovery times; no exact allocation of causal time benefits',
        validation='Every saved witness vector in selected sealed runs replayed independently on physical routes/loads/handling/original objective'))
    print(f'{len(out)} selected sealed trajectories and all saved witness vectors independently replayed')

if __name__=='__main__':globals()[sys.argv[1]]()
