"""Independent original-route, budget and submitted numerical projection audit; no optimizer."""
import ast, csv, json, math, shutil, re, hashlib
from decimal import Decimal, localcontext
from pathlib import Path
import verify_round64 as prior
import round65_research as run
from types import SimpleNamespace
ROOT,OUT,RAW=run.ROOT,run.OUT,run.RAW
prior.run=run
prior.physical_module.ROOT=ROOT
def rows(p):
    # The retained v2 micro exposed MinGW append tellp()==0 on a nonempty file.
    # Skip only exact repeated header records; source fixed before production.
    return [r for r in csv.DictReader(p.open(encoding='utf-8-sig',newline='')) if not all(k==v for k,v in r.items())] if p.exists() else []
def table(name,records):
    if not records:return
    with (OUT/name).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in records for k in r)));w.writeheader();w.writerows(records)

def hga_logical_digest(items):
    logical=[{key:row[key] for key in ['generation','best_fitness','strict_improvement']} for row in items]
    return hashlib.sha256(json.dumps(logical,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def source_hash_matches(path,expected):
    # Git may convert inherited C++ text between LF and CRLF on checkout.
    # Frozen evidence/driver bytes remain exact; permit no other source change.
    data=path.read_bytes()
    if hashlib.sha256(data).hexdigest()==expected:return True
    binding=run.read(run.OUT/'source_checkout_binding.json')['sources'].get(str(path.relative_to(ROOT)))
    return bool(binding and binding['measured_sha256']==expected and
        hashlib.sha256(data.replace(b'\r\n',b'\n')).hexdigest()==binding['lf_sha256'])

def timing_reference(identity):
    reference=run.read(run.OUT/'hga_timing_build.json')['reference_trajectories'][identity]
    original=ROOT/reference['path'];control=RAW/original.relative_to(run.RAW)
    items=rows(control)
    assert hga_logical_digest(items)==reference['logical_sha256']
    if control==original:assert run.sha(control)==reference['sha256']
    return control,items
def main():
    records=[];runs=[];proofs=[];prefix=[];costs=[];lifecycle=[];coverage=[];references=[];native=[];frontiers=[]
    physical_panel=run.panel()
    prior.run=SimpleNamespace(panel=lambda:physical_panel,sha=run.sha)
    entries=run.runner.entries()
    assert any((ROOT/e['destination']/'completion.json').exists() for e in entries if e['charged']), \
        'No completed local raw campaign found. Use --submitted for compact PR evidence.'
    for e in entries:
        if not e['charged']:continue
        folder=ROOT/e['destination'];completion=folder/'completion.json'
        if not completion.exists():continue
        done=run.read(completion);p=run.panel().get(e['id'])
        if not p:
            cmd=e['command']; arg=lambda n:cmd[cmd.index(n)+1]
            p=dict(instance_path=arg('--input'),T_seconds=arg('--T'),pickup_seconds=arg('--pickup-time'),drop_seconds=arg('--drop-time'),**{'lambda':arg('--lambda')})
            p['input_sha256']=run.sha(ROOT/p['instance_path'])
        physical_panel[e['id']]=p
        result_path=folder/'result.json'
        if not result_path.exists():
            runs.append(dict(number=e['charged_number'],id=e['id'],arm=e['arm'],failure=True,wall=done['wall_seconds']));continue
        r=run.read(result_path)
        if e['kind']=='hga-timing-diagnostic':
            timing=run.read(folder/'hga_timing.json')
            assert timing['optimizer_calls']==0 and timing['evidence_persisted']
            assert r['diagnostic_scope']=='hga_timing_only_no_optimizer'
            assert all(math.isfinite(v) and v>=0 for k,v in timing.items() if k.endswith('seconds'))
            if e['stage']=='timing_decoder_v5':assert timing['decoder_seconds']>0
            _,a=timing_reference(e['id'])
            b=rows(folder/'hga.csv');keys=['generation','best_fitness','strict_improvement']
            assert len(a)==len(b) and all(all(x[k]==y[k] for k in keys) for x,y in zip(a,b)),('diagnostic HGA prefix changed',e['id'])
        for path in [result_path,*folder.glob('**/*witness.json')]:
            witness=run.read(path)
            if 'routes' not in witness:continue
            checked=prior.physical_module.physical(p,witness);assert checked['original_T_feasible']
            records.append(dict(number=e['charged_number'],id=e['id'],arm=e['arm'],path=str(path.relative_to(ROOT)),**checked))
            dest=OUT/'witnesses'/str(e['charged_number'])/path.relative_to(folder)
            dest.parent.mkdir(parents=True,exist_ok=True)
            run.write(dest,{k:witness[k] for k in ['objective','F','routes','verification'] if k in witness})
        calls=rows(folder/'external/paper_optimize_ledger.csv');budget=rows(folder/'external/optional_budget.csv')
        native.extend(dict(number=e['charged_number'],id=e['id'],arm=e['arm'],**c) for c in calls)
        if e['arm']=='P-GRB':
            for name,value in [('threads',1),('seed',0),('presolve',-1),('mip_gap',0),('mip_gap_abs',0)]:
                assert r.get('gurobi_'+name+'_effective')==value
                assert r.get('gurobi_'+name+'_set_return_code')==r.get('gurobi_'+name+'_get_return_code')==0
            required=['gurobi_native_domain_audit_passed','gurobi_lifecycle_valid','gurobi_obj_bound_c_available',
                      'verified_incumbent_objective_available','verified_incumbent_original_problem_feasible','verified_incumbent_objective_consistent']
            assert all(r.get(k) is True for k in required)
            assert r['gurobi_optimize_return_code']==0 and math.isfinite(r['gurobi_obj_bound_c']) and r['lower_bound']==r['gurobi_obj_bound_c']
            assert '--plain-baseline' in e['command'] and not r['gurobi_hga_start_requested']
            expected=int(e['command'][e['command'].index('--round24-expected-gurobi-model-fingerprint')+1])
            assert r['gurobi_model_fingerprint']==expected
            log=(folder/'native.log').read_text(encoding='utf-8',errors='replace')
            assert 'Non-default parameters:' in log and not re.search(r'(?m)^\s*Heuristics\s+[-+\d.]',log)
            references.append(dict(number=e['charged_number'],id=e['id'],fingerprint=expected,parameter_readbacks=True,
                              original_domain=True,no_HGA_or_starts=True,default_heuristics=True,LB_source='ObjBoundC',
                              native_LB=r['gurobi_obj_bound_c'],strict_original_certificate=r['strict_certified_original_problem']))
        else:
            assert not r.get('external_gini_tree_warm_start_enabled',False)
            assert r.get('external_gini_tree_warm_start_submitted_count',0)==0
        ow=cw=os=cs=0
        command=e['command'];arg=lambda n,default:command[command.index(n)+1] if n in command else default
        seed=float(arg('--round65-seed-credit',30));call_cap=30 if arg('--round65-controller','credit10')=='credit-seed' else 10
        for b in budget:
            optional=b['kind']=='optional';w=float(b['work']);t=float(b['seconds']);assert w>=0 and t>=0
            if optional:
                assert float(b['grant_work'])<=max(0,min(call_cap,seed+.1*cw-ow))+1e-6
                assert float(b['grant_seconds'])<=max(0,min(15,seed+.1*cs-os))+1e-6
            if optional:ow+=w;os+=t
            else:cw+=w;cs+=t
            for actual,expected in [(ow,b['optional_work']),(cw,b['core_work']),(os,b['optional_seconds']),(cs,b['core_seconds'])]:
                assert abs(actual-float(expected))<1e-6
            costs.append(dict(number=e['charged_number'],id=e['id'],arm=e['arm'],**b))
        proj=folder/'external/projection';aux=rows(proj/'calls.csv');proof=rows(proj/'proof_calls.csv');uses=rows(proj/'row_use.csv')
        launches={c['call']:c for c in proof if c['status']=='launch'}
        for c in proof:
            if c['status']!='launch':
                before=launches[c['call']]
                assert all(c[k]==before[k] for k in ['leaf','gamma_L','gamma_U','cutoff'])
                if c['status'] not in ['2','3']:assert float(c['bound'])==float(before['bound']),'unknown proof leaked a partial objective'
        for item in rows(proj/'main_shapes.csv'):
            if item['mode']=='proof':assert int(item['attached'])==0
            lifecycle.append(dict(number=e['charged_number'],id=e['id'],arm=e['arm'],**item))
        for call in calls:
            if call['solve_kind']=='LP':assert call['integer_domain_restored']=='1'
        if calls:assert r['external_gini_tree_backend_parameter_roundtrip_valid']
        phases=rows(folder/'phases.csv');phase=lambda name:next((float(x['process_seconds']) for x in phases if x['event']==name),None)
        leaves=rows(folder/'external/paper_leaf_ledger.csv')
        if leaves:
            relevant=[l for l in leaves if l['status'] not in ['replaced','coalesced']]
            minimum=min((float(l['lower_bound']) for l in relevant),default=0)
            assert float(r['lower_bound'])<=min(float(r['upper_bound']),minimum)+1e-7,'global bound exceeds complete-frontier minimum'
            for parent in leaves:
                if parent['status']!='replaced':continue
                spans=[(float(c['gamma_L']),float(c['gamma_U'])) for c in leaves if c['parent_id']==parent['leaf_id']]
                if parent['strict_infeasible_half_verified']=='1':spans.append((float(parent['contracted_infeasible_gamma_L']),float(parent['contracted_infeasible_gamma_U'])))
                assert spans,('replaced parent has no coverage evidence',e['charged_number'],parent['leaf_id'])
                spans.sort();end=float(parent['gamma_L'])
                for lo,hi in spans:assert abs(lo-end)<=1e-7;end=hi
                assert abs(end-float(parent['gamma_U']))<=1e-7
            frontiers.append(dict(number=e['charged_number'],id=e['id'],complete_frontier_minimum=minimum,
                                  reported_LB=r['lower_bound'],parent_child_coverage=True))
        for event in rows(folder/'external/paper_tree_events.csv'):
            if event['event']=='optional_unknown_parent_retained':
                parent=next(l for l in leaves if l['leaf_id']==event['leaf_id'])
                assert parent['status']!='replaced'
                assert any(c['leaf_id']==event['leaf_id'] and c['solve_kind']!='LP' for c in calls) or done['wall_seconds']>=e['cap_seconds']-4
                coverage.append(dict(number=e['charged_number'],id=e['id'],leaf=event['leaf_id'],event='unknown_parent_retained',core_observed=any(c['leaf_id']==event['leaf_id'] and c['solve_kind']!='LP' for c in calls)))
        for call in calls:
            if call['solve_kind']=='LP' and call['native_status'] not in ['OPTIMAL','INFEASIBLE']:
                later=calls[calls.index(call)+1:]
                assert not any(c['leaf_id']==call['leaf_id'] and c['solve_kind']=='LP' for c in later)
                coverage.append(dict(number=e['charged_number'],id=e['id'],leaf=call['leaf_id'],event='incomplete_LP_no_repeat',core_observed=any(c['solve_kind']!='LP' for c in later)))
        result=dict(number=e['charged_number'],id=e['id'],arm=e['arm'],stage=e['stage'],cap=e['cap_seconds'],
            build=e['build_freeze'],executable_sha256=e['executable_sha256'],wall=done['wall_seconds'],status=r['status'],
            certificate=r.get('strict_certified_original_problem',False),
            UB=r.get('upper_bound',r.get('objective',r.get('F'))),LB=r.get('lower_bound'),
            native_calls=len(calls) if calls else (1 if e['arm']=='P-GRB' else 0),
            mip_calls=1 if e['arm']=='P-GRB' else sum(c['solve_kind']!='LP' for c in calls),aux_calls=len(aux),
            proof_calls=sum(c['status']=='launch' for c in proof),optional_work=ow,core_work=cw,optional_seconds=os,core_seconds=cs,
            splits=r.get('external_gini_tree_split_count'),failure=done['returncode']!=0 or 'failed' in r['status'])
        result.update(initial_UB=r.get('initial_upper_bound'),hga_seconds=r.get('incumbent_generation_time_seconds'),
                      first_LP_request=phase('first_lp_optimize_launch'),
                      proof_failure=(proj/'failures.txt').exists(),
                      startup_witness_present=(folder/'external/initial_witness.json').exists(),
                      witness_audit_failure=any('witness audit persistence failed' in n for n in r.get('notes',[])))
        result.update(controller=arg('--round65-controller','credit10'),release_load=arg('--round65-release-load','false'))
        initial=folder/'external/initial_witness.json'
        if initial.exists():
            initial_value=run.read(initial)
            result['initial_UB']=initial_value.get('objective',initial_value.get('F'))
        else:
            decomposition=rows(folder/'external/initial_decomposition_ledger.csv')
            if decomposition:result['initial_UB']=float(decomposition[0]['U_proof_launch'])
        result['gap']=result['UB']-result['LB'] if result['LB'] is not None else None
        result['optimizer_calls']=result['native_calls']+result['aux_calls']+result['proof_calls']
        result['optional_account_present']=bool(budget)
        result['main_native_work']=sum(float(c['work']) for c in calls) if calls else r.get('gurobi_work',0)
        result['main_native_seconds']=sum(float(c['solver_runtime']) for c in calls) if calls else r.get('gurobi_runtime',0)
        result['total_accounted_optimizer_work']=ow+cw if budget else result['main_native_work']
        runs.append(result)
        if (proj/'physical.json').exists():
            data=run.read(proj/'physical.json');text=(ROOT/p['instance_path']).read_text(encoding='utf-8');header=text.splitlines()[0]
            capacities=ast.literal_eval(header[header.index('['):]);prior.check_resource_physics(e['id'],data,capacities)
            matrix=prior.resource_matrix(data,capacities)
            station_cap=ast.literal_eval(next(t.split('=',1)[1] for t in text.splitlines() if t.startswith('capacities')))
            for path in proj.glob('row_*.json'):
                row=run.read(path);assert row['scope']=='physical_global' and row['identity']==data['identity']
                with localcontext() as ctx:
                    ctx.prec=80;D=Decimal.from_float;z={};v={}
                    for name,y in row['multipliers'].items():
                        eq,a,b=matrix[name];assert eq=='1' or y>=0
                        # Each multiplier must belong to exactly the declared vehicle block.
                        assert all(int(n.split('_')[1])==row['vehicle'] for n in [*a,*b])
                        for n,c in a.items():z[n]=z.get(n,Decimal(0))+D(y)*D(c)
                        for n,c in b.items():v[n]=v.get(n,Decimal(0))+D(y)*D(c)
                    beta=Decimal(0)
                    for n,a in z.items():
                        family,k,i,j=n.split('_');k,i,j=int(k),int(i),int(j)
                        u=capacities[k] if family=='q' else data['upper'][i][j]
                        beta+=min(Decimal(0),a*D(float(u)))
                    corrected=beta
                    for n,a in v.items():
                        stored=D(row['coefficients'].get(n,0.));assert abs(stored-a)<Decimal('1e-10')
                        parts=n.split('_');family,k,i=parts[:3];k,i=int(k),int(i)
                        u=1 if family=='x' else capacities[k] if family=='load' else station_cap[i]
                        corrected+=min(Decimal(0),(stored-a)*D(float(u)))
                    assert D(row['rhs'])<=corrected+Decimal('1e-40'),(path,row['rhs'],corrected)
                activity=math.fsum(c*row['point'][n] for n,c in row['coefficients'].items())
                assert abs(activity-row['activity'])<1e-8 and row['rhs']-activity>1e-7
                proofs.append(dict(number=e['charged_number'],id=e['id'],vehicle=row['vehicle'],signature=row['signature'],support=len(row['coefficients']),violation=row['violation'],finite_bound_and_rounding_verified=True))
                target=OUT/'projection_evidence'/str(e['charged_number']);target.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(path,target/path.name);shutil.copyfile(proj/'physical.json',target/'physical.json')
                if (proj/'representation.json').exists():shutil.copyfile(proj/'representation.json',target/'representation.json')
            known={run.read(p)['signature'] for p in proj.glob('row_*.json')}
            assert all(u['signature'] in known for u in uses)
    for identity in ['C5','C7','C2']:
        base=RAW/'reliability_v1'/identity/'off';on=RAW/'reliability_v1'/identity/'reliable'
        if not (on/'completion.json').exists():continue
        a=rows(base/'hga.csv');b=rows(on/'hga.csv');keys=['generation','best_fitness','strict_improvement']
        assert a and b
        count=min(len(a),len(b));assert all(all(x[k]==y[k] for k in keys) for x,y in zip(a,b))
        prefix.append(dict(id=identity,baseline_generations=len(a)-1,candidate_generations=len(b)-1,matched_prefix=count,
                           final_fitness_equal=a[-1]['best_fitness']==b[-1]['best_fitness']))
    table('runs.csv',runs);table('witness_verification.csv',records);table('projection_verification.csv',proofs);table('hga_prefix_verification.csv',prefix)
    table('optional_call_costs.csv',costs);table('main_model_lifecycle.csv',lifecycle);table('unknown_coverage_checks.csv',coverage)
    table('reference_contract_verification.csv',references);table('native_calls.csv',native)
    table('frontier_reduction_checks.csv',frontiers)
    print('runs',len(runs),'witnesses',len(records),'projection rows',len(proofs),'HGA pairs',len(prefix))
def submitted():
    """Replay the same independent audit using only the compact submitted evidence."""
    import tempfile
    global OUT,RAW
    original_out,original_raw=OUT,RAW
    original_entries=run.runner.entries
    expected=(OUT/'runs.csv').read_bytes()
    ledger=original_entries()
    receipt=run.read(OUT/'audit_receipt.json')
    assert receipt['ledger_sha256']==run.sha(OUT/'processes.jsonl')
    assert receipt['local_artifact_index_sha256']==run.sha(OUT/'local_artifact_index.csv')
    assert receipt['source_checkout_binding_sha256']==run.sha(OUT/'source_checkout_binding.json')
    assert sum(e['charged'] for e in ledger)==receipt['charged_launches']<=72
    assert sum(e['kind']=='native-micro' for e in ledger)==receipt['native_micros']<=4
    binding=run.read(OUT/'confirmation_freeze.json')
    for path,key in [(OUT/'active_build.json','build'),(OUT/'protocol.json','protocol'),
                     (ROOT/'scripts/round65_research.py','driver'),(OUT/'main_policy.json','policy')]:
        assert run.sha(path)==binding[key],('confirmation binding changed',path)
    # The selection hash must be an actual chronological prefix of the retained
    # write-ahead ledger, before either confirmation was optimized.
    policy=run.read(OUT/'main_policy.json');prefix=hashlib.sha256();selection_count=None
    for count,line in enumerate((OUT/'processes.jsonl').read_bytes().splitlines(keepends=True),1):
        prefix.update(line)
        if prefix.hexdigest()==policy['selection_ledger_sha256']:
            selection_count=count;break
    assert selection_count is not None,'selection ledger is not a retained prefix'
    assert not any(e['charged'] and e['id'] in binding['confirmations'] for e in ledger[:selection_count])
    previous_last=-1
    for identity in binding['confirmations']:
        confirmed=[e for e in ledger if e['charged'] and e['id']==identity]
        assert len(confirmed)==len(binding['arms']) and {e['arm'] for e in confirmed}==set(binding['arms'])
        assert min(e['charged_number'] for e in confirmed)>previous_last
        previous_last=max(e['charged_number'] for e in confirmed)
        assert all(e['cap_seconds']==binding['cap'] for e in confirmed)
    active=run.read(OUT/run.read(OUT/'active_build.json')['file'])
    checkout=run.read(OUT/'source_checkout_binding.json')
    assert checkout['build']==run.read(OUT/'active_build.json')
    assert set(checkout['sources'])==set(active['source_files'])
    assert all(checkout['sources'][name]['measured_sha256']==expected for name,expected in active['source_files'].items())
    for path,expected_hash in active['source_files'].items():
        assert source_hash_matches(ROOT/path,expected_hash),('measured C++ source changed',path)
    for freeze_path in OUT.glob('build_freeze_*.json'):
        freeze=run.read(freeze_path)
        assert run.sha(OUT/'tests'/('tests_'+freeze['version']+'.log'))==freeze['tests_sha256']
    for timing_file in [OUT/'hga_timing_build.json',OUT/'hga_decoder_timing_build.json']:
        if not timing_file.exists():continue
        timing=run.read(timing_file)
        assert timing['solver_build']==run.read(OUT/'active_build.json')
        assert run.sha(ROOT/timing['source'])==timing['source_sha256']
        instrumentation=timing.get('instrumentation',{})
        if instrumentation:
            assert timing['decoder_counter_enabled']
            assert source_hash_matches(ROOT/instrumentation['source'],instrumentation['original_sha256'])
            assert source_hash_matches(ROOT/instrumentation['runner_source'],instrumentation['runner_source_sha256'])
    (ROOT/'build').mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='round65-submission-',dir=ROOT/'build') as directory:
        scratch=Path(directory)
        assert scratch.resolve().is_relative_to((ROOT/'build').resolve())
        new_raw=scratch/'raw';new_out=scratch/'audit';new_out.mkdir()
        native=rows(OUT/'native_calls.csv');costs=rows(OUT/'optional_call_costs.csv');shapes=rows(OUT/'main_model_lifecycle.csv')
        rewritten=[]
        for e in ledger:
            if not e['charged']:continue
            number=str(e['charged_number']);saved=run.read(OUT/'receipts'/(number+'.json'))
            assert saved['launch']==e
            folder=new_raw/(ROOT/e['destination']).relative_to(original_raw)
            folder.mkdir(parents=True,exist_ok=True)
            for source in [OUT/'receipts'/number,OUT/'witnesses'/number]:
                if source.exists():shutil.copytree(source,folder,dirs_exist_ok=True)
            result=run.read(folder/'result.json') if (folder/'result.json').exists() else {}
            result.update(saved['result'])
            if result:run.write(folder/'result.json',result)
            run.write(folder/'completion.json',saved['completion'])
            proof=OUT/'projection_evidence'/number
            if proof.exists():shutil.copytree(proof,folder/'external/projection',dirs_exist_ok=True)
            for source,name in [(native,'paper_optimize_ledger.csv'),(costs,'optional_budget.csv'),
                                (shapes,'projection/main_shapes.csv')]:
                subset=[{k:v for k,v in row.items() if k not in ['number','id','arm']} for row in source if row['number']==number]
                if subset:
                    target=folder/'external'/name;target.parent.mkdir(parents=True,exist_ok=True)
                    with target.open('w',encoding='utf-8',newline='') as f:
                        writer=csv.DictWriter(f,fieldnames=list(subset[0]));writer.writeheader();writer.writerows(subset)
            rewritten.append(dict(e,destination=str(folder.relative_to(ROOT))))
        try:
            OUT,RAW=new_out,new_raw
            run.runner.entries=lambda:rewritten
            main()
            assert (new_out/'runs.csv').read_bytes()==expected,'compact audit disagrees with full campaign summary'
            print('Submitted route, projection, budget, coverage and reference evidence reproduces runs.csv exactly.')
        finally:
            OUT,RAW=original_out,original_raw;run.runner.entries=original_entries

if __name__=='__main__':
    import sys
    if '--submitted' in sys.argv:submitted()
    else:main()
