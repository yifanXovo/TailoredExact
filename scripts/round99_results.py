"""Read-only compact endpoints, native evidence and nonduplicated fee ledger.

Usage: round99_results.py exclusive_output_label campaign [campaign ...].
Never invokes Gurobi or reconstructs missing performance artifacts.
"""
import csv,json,re,sys,shutil
from round99_common import *

def csv_write(path,rows):
    if not rows:return
    fields=list(dict.fromkeys(k for row in rows for k in row))
    with Path(path).open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def csv_read(path):
    with Path(path).open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))

def native_log(path):
    lines=path.read_text(encoding='utf-8',errors='replace').splitlines();r={}
    for line in lines:
        m=re.search(r'Optimize a model with (\d+) rows, (\d+) columns and (\d+) nonzeros',line)
        if m:r.update(generated_rows=int(m[1]),generated_columns=int(m[2]),generated_nonzeros=int(m[3]))
        m=re.search(r'Variable types: (\d+) continuous, (\d+) integer \((\d+) binary\)',line)
        if m:
            prefix='generated' if 'generated_integer' not in r else 'internal_visible'
            r.update({prefix+'_continuous':int(m[1]),prefix+'_integer':int(m[2]),prefix+'_binary':int(m[3])})
        m=re.search(r'Presolved: (\d+) rows, (\d+) columns, (\d+) nonzeros',line)
        if m:r.update(internal_visible_rows=int(m[1]),internal_visible_columns=int(m[2]),internal_visible_nonzeros=int(m[3]))
        m=re.search(r'Root relaxation: objective ([\d.eE+-]+), (\d+) iterations, ([\d.]+) seconds \(([\d.]+) work units\)',line)
        if m:r.update(root_relaxation=float(m[1]),root_iterations=int(m[2]),root_seconds=float(m[3]),root_work=float(m[4]))
    cuts={};in_cuts=False;root_rows=[];incumbents=[]
    for no,line in enumerate(lines,1):
        if line.startswith('Cutting planes:'):in_cuts=True;continue
        if in_cuts:
            m=re.match(r'\s+(.+?): (\d+)$',line)
            if m:cuts[m[1]]=int(m[2]);continue
            if line.strip():in_cuts=False
        # Gurobi's table is rounded, call-relative evidence only.
        if not line.endswith('s'):continue
        tokens=line.split()
        if len(tokens)<7:continue
        try:
            seconds=float(tokens[-1][:-1]);bound=float(tokens[-4]);inc=float(tokens[-5])
        except ValueError:continue
        if tokens[0] in ['H','*']:
            incumbents.append(dict(line=no,seconds_rounded=seconds,incumbent_rounded=inc,bound_rounded=bound,raw=line))
        else:
            try:explored=int(tokens[0])
            except ValueError:continue
            if explored==0:root_rows.append(dict(line=no,seconds_rounded=seconds,bound_rounded=bound,incumbent_rounded=inc,raw=line))
    r.update(cuts=json.dumps(cuts,sort_keys=True),last_observed_root_bound=root_rows[-1]['bound_rounded'] if root_rows else None,
        last_observed_root_row_seconds=root_rows[-1]['seconds_rounded'] if root_rows else None,
        first_native_incumbent_rounded=incumbents[0]['incumbent_rounded'] if incumbents else None,
        first_native_incumbent_seconds_rounded=incumbents[0]['seconds_rounded'] if incumbents else None,
        log_sha256=sha(path),scope='production optimize log; rounded call-relative table; root completion not inferred')
    return r,incumbents,root_rows

def extract(label,campaigns):
    target=OUT/label;target.mkdir(exist_ok=False)
    rows=[];cost=[];calls=[];logs=[];history=[];startups=[];receipts=[];interrupted=[];audited=[];physical=[]
    for name in campaigns:
        camp=OUT/name;q=read(camp/'identity.json')
        rec=[json.loads(s) for s in (camp/'summary.jsonl').read_text().splitlines()]
        manifest=camp/'interruption_manifest.json'
        if manifest.exists():
            im=read(manifest);assert im['original_identity_sha256']==sha(camp/'identity.json')
            assert len(rec)==im['passed_prefix'] and [r['number'] for r in rec]==list(range(1,len(rec)+1))
            assert im['interrupted_number']==len(rec)+1
            launch=q['launches'][im['interrupted_number']-1];d=Path(launch['destination'])
            ic=read(d/'interruption_receipt.json');ia=read(d/'interrupted_audit.json')
            assert ia['passed'] and sha(d/'interruption_receipt.json')==im['interruption_receipt_sha256']
            assert not (d/'completion.json').exists() and not (d/'result.json').exists()
            events=read(d/'interrupted_observations.json')
            assert sum(v['payload']['kind']=='call' for v in events)==ic['optimizer_calls']==ia['native_calls_started']
            assert all(not Path(q['launches'][n-1]['destination']).exists() for n in im['never_started_numbers'])
            interrupted.append(dict(campaign=name,number=ic['number'],role=ic['role'],arm=ic['arm'],
                input_sha256=launch['panel']['input_sha256'],cap=launch['cap_seconds'],
                exact_actual_outer_seconds=None,charged_outer_seconds=ic['charged_outer_seconds'],
                last_verified_process_seconds=ic['last_verified_process_seconds'],optimizer_calls=ic['optimizer_calls'],
                calls_returned=ic['calls_returned'],audit_passed=True,**ic['checkpoint_endpoint']))
            cost.append(dict(category='interrupted_formal',label=f'{name}/{ic["number"]}/{ic["role"]}/{ic["arm"]}',
                experimental_starts=1,optimizer_calls=ic['optimizer_calls'],outer_seconds=None,
                charged_outer_seconds=ic['charged_outer_seconds'],failed=True,stop_reason=ic['stop_reason']))
            dest=target/'interrupted'/f'{name}_{ic["number"]:02d}';dest.mkdir(parents=True)
            for filename in ['interruption_receipt.json','interrupted_audit.json']:
                shutil.copy2(d/filename,dest/filename)
        else:assert len(rec)==len(q['launches']), 'only completed or explicit interrupted-prefix campaigns'
        for r in rec:
            launch=q['launches'][r['number']-1];d=Path(r['destination']);p=launch['panel'];c=r['completion']
            audit=read(d/'audit.json');e=r['endpoint'];assert r['audit_passed'] and audit['passed']
            result=read(d/'result.json');prefix=dict(campaign=name,number=r['number'],role=r['id'],arm=r['arm'])
            audited.append((prefix,p,audit))
            rows.append(dict(prefix,V=p['V'],M=p['M'],Q=json.dumps(p['Q_vector']),T=p['T_seconds'],cap=launch['cap_seconds'],
                input_sha256=p['input_sha256'],binary_sha256=q['candidate_binary_sha256'],audit_passed=True,
                stop_reason=c['stop_reason'],outer_seconds=c['process_wall_seconds'],end_to_end_seconds=c['end_to_end_seconds'],
                certificate=e['certificate'],U=e['U'],L=e['L'],gap=e['gap'],
                relative_gap=e['gap']/max(abs(e['U']),1e-12) if e['U'] is not None else None,
                optimizer_calls=audit['native_calls_started'],receipt_sha256=sha(d/'completion.json'),audit_sha256=sha(d/'audit.json'),
                endpoint_source=e['source'],status=e['status'],splits=result.get('external_gini_tree_split_count'),
                lp_calls=result.get('external_gini_tree_lp_optimize_count',0),partial_mip_calls=result.get('external_gini_tree_partial_mip_optimize_count',0),
                terminal_mip_calls=result.get('external_gini_tree_terminal_mip_optimize_count',1 if r['arm']=='P-GRB' else 0),
                model_build_seconds=result.get('external_gini_tree_model_build_seconds'),
                work=result.get('gurobi_work' if r['arm']=='P-GRB' else 'external_gini_tree_work'),
                nodes=result.get('gurobi_node_count' if r['arm']=='P-GRB' else 'external_gini_tree_nodes'),
                iterations=result.get('gurobi_iter_count' if r['arm']=='P-GRB' else 'external_gini_tree_simplex_iterations')))
            cost.append(dict(category='full_'+name,label=f'{name}/{r["number"]}/{r["id"]}/{r["arm"]}',experimental_starts=1,
                optimizer_calls=audit['native_calls_started'],outer_seconds=c['process_wall_seconds'],failed=False,stop_reason=c['stop_reason']))
            ledger=d/'external/paper_optimize_ledger.csv'
            if ledger.exists():calls.extend(dict(prefix,**v) for v in csv_read(ledger))
            logfile=[d/'native.log'] if r['arm']=='P-GRB' else sorted((d/'external/native_logs').glob('*.gurobi.log'))
            for path in logfile:
                item,incs,roots=native_log(path)
                logs.append(dict(prefix,path=path.relative_to(ROOT).as_posix(),**item))
                history.extend(dict(prefix,source='rounded_native_incumbent',path=path.relative_to(ROOT).as_posix(),**v) for v in incs)
            observations=read(d/'observations.json')
            witness_by_sequence={w['sequence']:w for w in audit.get('witnesses',[])}
            for v in observations:
                ev=v['payload'];kind=ev['kind']
                if kind not in ['bound','witness']:continue
                history.append(dict(prefix,source='committed_'+kind,sequence=ev['sequence'],call=ev['call'],
                    available_seconds=v['effective_available_seconds'],U=ev.get('objective',ev.get('F')),G=ev.get('G'),
                    native_bound=ev.get('native_bound'),global_bound=ev.get('global_bound'),global_available=ev.get('global_available')))
                if kind=='witness':
                    w=witness_by_sequence[ev['sequence']]
                    physical.append(dict(prefix,input_path=p['input_path'],input_sha256=p['input_sha256'],
                        T=p['T_seconds'],lambda_value=.15,pickup_seconds=60,drop_seconds=60,
                        available_seconds=v['effective_available_seconds'],event_sha256=v['sha256'],
                        independently_audited_F=w['F'],independently_audited_G=w['G'],
                        independently_audited_P=w['P'],event=ev))
            if r['arm']!='P-GRB':
                initial=d/'external/initial_witness.json';w=read(initial)
                startup_events=[v for v in observations if v['payload']['kind']=='witness' and v['payload']['call']==0]
                assert len(startup_events)==1
                startups.append(dict(prefix,objective=w['objective'],witness_sha256=sha(initial),
                    physical_available_seconds=startup_events[0]['effective_available_seconds'],
                    exact_cost_scope='witness availability includes startup and preceding overhead; pure startup timing in retained phase ledgers'))
            # Compact independent-audit witness output and all endpoint receipts.
            folder=target/'endpoints'/f'{name}_{r["number"]:02d}_{r["id"]}_{r["arm"]}';folder.mkdir(parents=True)
            for filename in ['completion.json','audit.json']:
                shutil.copy2(d/filename,folder/filename)
            if e['U'] is not None:
                write(folder/'physical_witness.json',dict(input_path=p['input_path'],input_sha256=p['input_sha256'],
                    F=result.get('objective'),U=e['U'],routes=result['routes'],source_result=d.relative_to(ROOT).as_posix()+'/result.json',source_sha256=sha(d/'result.json')))
            else:
                write(folder/'no_physical_UB.json',dict(U=None,L=e['L'],status=e['status'],source_result_sha256=sha(d/'result.json')))
        batch=camp/'reference_batch_receipt.json'
        if batch.exists():
            b=read(batch);assert b['passed'] and b['optimizer_calls']==0
            cost.append(dict(category='reference_batch',label=name+'/reference_batch',experimental_starts=1,
                optimizer_calls=0,outer_seconds=b['outer_seconds'],failed=False,stop_reason=b['stop_reason']))
        else:
            for folder in sorted((camp/'reference').iterdir()):
                c=read(folder/'completion.json')
                if c.get('copy_only'):continue
                cost.append(dict(category='reference',label=name+'/reference/'+folder.name,experimental_starts=1,
                    optimizer_calls=0,outer_seconds=c['outer_seconds'],failed=c['returncode']!=0,stop_reason='normal_return'))
    pairs=[]
    for name in campaigns:
        for role in sorted({r['role'] for r in rows if r['campaign']==name}):
            group={r['arm']:r for r in rows if r['campaign']==name and r['role']==role}
            comparisons=[(a,b) for b in group if b not in ['P-GRB','ENS-C'] for a in ['P-GRB','ENS-C']]
            comparisons += [('R1','M-B'),('Q-I','R2'),('R1','Q-I'),('M-B','R2'),('M-B','M-BL')]
            for ref,candidate in comparisons:
                if ref not in group or candidate not in group:continue
                a,b=group[ref],group[candidate];both=a['certificate'] and b['certificate']
                delta=b['end_to_end_seconds']-a['end_to_end_seconds'] if both else None
                ratio=b['end_to_end_seconds']/a['end_to_end_seconds'] if both else None
                pairs.append(dict(campaign=name,role=role,reference=ref,candidate=candidate,reference_certified=a['certificate'],candidate_certified=b['certificate'],
                    censoring='both_certified' if both else 'reference_only' if a['certificate'] else 'candidate_only' if b['certificate'] else 'both_unproved',
                    certified_time_delta=delta,certified_time_ratio=ratio,material_time_change=bool(both and abs(delta)>=30 and abs(ratio-1)>=.1),
                    severe_time_regression=bool(both and delta>=120 and ratio>=1.25),reference_U=a['U'],candidate_U=b['U'],
                    reference_L=a['L'],candidate_L=b['L'],reference_gap=a['gap'],candidate_gap=b['gap'],
                    reference_relative_gap=a['relative_gap'],candidate_relative_gap=b['relative_gap'],
                    eventual_time_order_known=both or bool(b['certificate'] and b['end_to_end_seconds']<a['end_to_end_seconds'])
                        or bool(a['certificate'] and a['end_to_end_seconds']<b['end_to_end_seconds']),
                    time_delta_upper_bound=b['end_to_end_seconds']-a['end_to_end_seconds'] if b['certificate'] and not a['certificate'] else None,
                    time_delta_lower_bound=b['end_to_end_seconds']-a['end_to_end_seconds'] if a['certificate'] and not b['certificate'] else None,
                    material_one_sided_time_advantage=bool(b['certificate'] and not a['certificate'] and
                        a['end_to_end_seconds']-b['end_to_end_seconds']>=30 and b['end_to_end_seconds']/a['end_to_end_seconds']<=.9),
                    material_one_sided_time_regression=bool(a['certificate'] and not b['certificate'] and
                        b['end_to_end_seconds']-a['end_to_end_seconds']>=30 and b['end_to_end_seconds']/a['end_to_end_seconds']>=1.1),
                    material_budget_U_change=bool(a['U'] is not None and b['U'] is not None and
                        abs(b['U']-a['U'])>=.001 and abs(b['U']-a['U'])/max(abs(a['U']),1e-12)>=.01),
                    material_budget_gap_change=bool(abs(b['gap']-a['gap'])>=.001 and
                        abs(b['gap']-a['gap'])/max(abs(a['gap']),1e-12)>=.1)))
    # Receipt batches are finite, known scopes; failed micro01 never reached Env or optimize.
    for category in ['qualification','diagnostic_receipts']:
        root=OUT/category
        if not root.exists():continue
        for folder in sorted(root.iterdir()):
            if not folder.is_dir() or not (folder/'receipt.json').exists():continue
            c=read(folder/'receipt.json');durable=OUT/'diagnostics'/folder.name/'calls.jsonl'
            count=sum(json.loads(s)['kind']=='start' for s in durable.read_text().splitlines()) if durable.exists() else c.get('optimizer_calls')
            if folder.name=='micro01':
                assert 'FileExistsError' in (folder/'stderr.log').read_text();count=0
            if folder.name in ['native_scope_followup01','native_scope_followup02']:
                assert 'solver or build process active' in (folder/'stderr.log').read_text();count=0
            if folder.name=='native_scope_followup03':
                assert 'different native engines' in (folder/'stderr.log').read_text();count=0
            if folder.name=='final_actual_start01':
                stderr=(folder/'stderr.log').read_text()
                assert 'foreign solver or build process active' in stderr and 'line 9, in main' in stderr
                assert read(folder/'actual_calls_supplement.json')['actual_optimizer_calls']==0
                count=0
            assert count is not None,(folder,count)
            cost.append(dict(category=category,label=folder.name,experimental_starts=1,optimizer_calls=count,outer_seconds=c['outer_seconds'],
                failed=c['exit_code']!=0,stop_reason=c['stop_reason']))
    # Reliable F* is learned only from audited numerical certificates; this is
    # a retrospective lookup of independently audited physical witness events.
    fstar={}
    for r in rows:
        if r['certificate']:
            h=r['input_sha256']
            if h in fstar:assert abs(fstar[h]-r['U'])<=1e-7
            fstar[h]=r['U']
    discoveries=[]
    for prefix,p,audit in audited:
        known=fstar.get(p['input_sha256'])
        qualified=[w for w in audit.get('witnesses',[]) if known is not None and abs(w['F']-known)<=1e-7]
        first=min(qualified,key=lambda w:w['available']) if qualified else None
        discoveries.append(dict(prefix,reliable_numerical_Fstar=known,first_qualified_witness_available_seconds=first['available'] if first else None,
            sequence=first.get('sequence') if first else None,call=first.get('call') if first else None,
            scope='retrospective physical audit, numerical tolerance1e-7; availability conservative, not native search instant'))
    csv_write(target/'runs.csv',rows);csv_write(target/'pairs.csv',pairs);csv_write(target/'cost_failures.csv',cost)
    csv_write(target/'interrupted_runs.csv',interrupted);csv_write(target/'optimal_discovery.csv',discoveries)
    with (target/'physical_witness_events.jsonl').open('x',encoding='utf-8') as f:
        for item in physical:f.write(json.dumps(item,ensure_ascii=False,allow_nan=False)+'\n')
    csv_write(target/'native_calls.csv',calls);csv_write(target/'native_structure.csv',logs);csv_write(target/'trajectories.csv',history);csv_write(target/'startup.csv',startups)
    write(target/'summary.json',dict(actual_starts=sum(c['experimental_starts'] for c in cost),actual_optimizer_calls=sum(c['optimizer_calls'] for c in cost),
        outer_solver_seconds=None if any(c['outer_seconds'] is None for c in cost) else sum(c['outer_seconds'] for c in cost),
        measured_known_outer_solver_seconds=sum(c['outer_seconds'] for c in cost if c['outer_seconds'] is not None),
        conservative_outer_solver_seconds=sum(c.get('charged_outer_seconds',c['outer_seconds']) for c in cost),
        unknown_actual_outer_processes=[c['label'] for c in cost if c['outer_seconds'] is None],
        failed_started_processes=[c['label'] for c in cost if c['failed']],
        campaigns=campaigns,no_double_count_internal_calls=True,source_sha256=sha(__file__)))
    print(json.dumps(read(target/'summary.json')))

if __name__=='__main__':extract(sys.argv[1],sys.argv[2:])
