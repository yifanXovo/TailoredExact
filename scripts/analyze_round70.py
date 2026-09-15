"""Round68 audit copied with a narrow qualified pre-proof deadline branch.

All ordinary model/witness/bound checks remain unchanged; historical file is
untouched. A startup-only result uses the full-domain nonnegative bound, never
a fabricated tree or certificate. See round70_startup_deadline.py.
"""
import csv,json,math,re,shutil,hashlib
import analyze_round61 as physical_module
import round70_research_v2 as run
import round70_startup_deadline as startup_deadline

physical_module.ROOT=run.ROOT
def rows(p):
    return list(csv.DictReader(p.open(encoding='utf-8-sig',newline=''))) if p.exists() else []
def table(name,records):
    if not records:return
    fields=list(dict.fromkeys(k for r in records for k in r))
    with (run.OUT/name).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(records)
def practical_classification(candidate,reference):
    """Frozen practical thresholds; a label is not a per-point admission veto."""
    if candidate['certificate']!=reference['certificate']:
        return 'certificate_gain' if candidate['certificate'] else 'certificate_loss'
    if candidate['certificate']:
        delta=candidate['wall']-reference['wall'];relative=abs(delta)/reference['wall']
        small=int(candidate['V'])<=12 and max(candidate['wall'],reference['wall'])<60
        material=(2,.20) if small else (10,.15);severe=(5,.50) if small else (30,.50)
    else:
        delta=candidate['signed_absolute_gap']-reference['signed_absolute_gap']
        if reference['signed_absolute_gap']<=1e-7:return 'near_zero_gap_requires_separate_review'
        relative=abs(delta)/reference['signed_absolute_gap'];material=(.001,.10);severe=(.01,.50)
    size='severe' if abs(delta)>severe[0] and relative>severe[1] else (
        'material' if abs(delta)>material[0] and relative>material[1] else 'below_practical_threshold')
    return size+('_improvement' if delta<0 else '_regression') if size!='below_practical_threshold' else size
def tree_coverage(folder,leaves,p):
    """Recompute interval union from retained tree rows, independent of flags."""
    by_id={l['leaf_id']:l for l in leaves};assert len(by_id)==len(leaves)
    roots=[l for l in leaves if not l['parent_id']]
    initial=[l for l in rows(folder/'external/initial_decomposition_ledger.csv') if l['active']=='1']
    def endpoints(l):return float(l['gamma_L']),float(l['gamma_U'])
    expected=sorted((float(l['active_lower']),float(l['active_upper'])) for l in initial)
    actual=sorted(endpoints(l) for l in roots)
    witness=run.read(folder/'external/initial_witness.json')
    initial_U=witness.get('F',witness.get('objective'))
    # With nonnegative penalty, every incumbent-improving solution has
    # G<=F<=U. Also nonnegative ratios imply G<=(n-1)/n, including S=0.
    assert float(p['lambda'])>=0
    mathematical_upper=min(float(initial_U),(int(p['V'])-1)/int(p['V']))
    assert expected and abs(expected[0][0])<1e-10
    assert expected[-1][1]>=mathematical_upper-1e-10,'initial original-problem Gini range omitted'
    for left,right in zip(expected,expected[1:]):assert abs(left[1]-right[0])<1e-10
    for interval in initial:
        assert abs(float(interval['U_proof_launch'])-initial_U)<1e-7
    assert len(expected)==len(actual)
    for x,y in zip(expected,actual):assert max(abs(a-b) for a,b in zip(x,y))<1e-10
    for l in leaves:
        lo,hi=endpoints(l);assert 0<=lo<=hi and math.isfinite(hi)
        if l['parent_id']:assert l['parent_id'] in by_id
        assert l['status']!='coalesced','unexpected coalescence requires explicit audit'
        if l['status']=='replaced':
            children=sorted((x for x in leaves if x['parent_id']==l['leaf_id']),key=endpoints)
            assert children,'uncovered replaced parent'
            segments=[endpoints(x) for x in children]
            if l['single_child_contraction_parent']=='1':
                assert l['strict_infeasible_half_verified']=='1'
                segments.append((float(l['contracted_infeasible_gamma_L']),float(l['contracted_infeasible_gamma_U'])))
                segments.sort()
            assert abs(segments[0][0]-lo)<1e-10 and abs(segments[-1][1]-hi)<1e-10
            for a,b in zip(segments,segments[1:]):assert abs(a[1]-b[0])<1e-10
    return dict(tree_rows=len(leaves),roots=len(roots),replaced=sum(l['status']=='replaced' for l in leaves),
                independently_recomputed_interval_union=True,initial_range_covers_G_le_verified_F=True)
def analyze():
    assert not (run.OUT/'active_run.lock').exists(),'Full evidence audit must run between optimizer queues'
    records=[];witnesses=[];calls_all=[];models=[];coverage=[];native_statistics=[];incumbent_events=[]
    for e in run.runner.entries():
        folder=run.ROOT/e['destination']
        if not e['charged'] or not (folder/'completion.json').exists():continue
        done=run.read(folder/'completion.json');p=run.panel()[e['id']]
        if done['returncode'] or done['watchdog'] or not done['within_budget'] or not (folder/'result.json').exists():
            records.append(dict(number=e['charged_number'],id=e['id'],arm=e['arm'],kind=e['kind'],failure=True,
                failure_reason='process_exit_watchdog_budget_or_missing_result',wall=done['wall_seconds']));continue
        r=run.read(folder/'result.json');cert=r['strict_certified_original_problem']
        for path in [folder/'result.json',*folder.glob('external/*witness.json')]:
            witness=run.read(path)
            if 'routes' not in witness:continue
            check=physical_module.physical(p,witness);assert check['original_T_feasible']
            if 'verification' in witness and 'final_inventories' in witness['verification']:
                # The independent route routine checks inventory in its direct format.
                physical_module.physical(p,dict(witness,inventory=witness['verification']['final_inventories']))
            dest=run.OUT/'witnesses'/str(e['charged_number'])/path.name
            run.write(dest,{k:witness[k] for k in ['objective','F','routes','verification','inventory'] if k in witness})
            witnesses.append(dict(number=e['charged_number'],path=str(dest.relative_to(run.OUT)),sha256=run.sha(dest),**check))
        UB=float(r['upper_bound']);LB=float(r['lower_bound']);assert math.isfinite(UB) and math.isfinite(LB)
        assert LB<=UB+1e-7,(e['id'],e['arm'],'inconsistent bounds',LB,UB)
        assert abs(UB-r['objective'])<=1e-7
        if cert:assert UB-LB<=1e-7
        calls=rows(folder/'external/paper_optimize_ledger.csv')
        if e['arm']=='P-GRB':
            for n,v in [('threads',1),('seed',0),('presolve',-1),('mip_gap',0),('mip_gap_abs',0)]:
                assert r['gurobi_'+n+'_effective']==v
                assert r['gurobi_'+n+'_set_return_code']==r['gurobi_'+n+'_get_return_code']==0
            assert r['gurobi_native_domain_audit_passed'] and r['gurobi_lifecycle_valid']
            assert r['gurobi_model_fingerprint']==run.read(run.OUT/'fingerprints.json')[e['id']]['fingerprint']
            assert r['gurobi_obj_bound_c_available'] and LB==r['gurobi_obj_bound_c']
            assert not r['gurobi_hga_start_requested']
            log=(folder/'native.log').read_text(encoding='utf-8',errors='replace')
            assert not re.search(r'(?m)^\s*Heuristics\s+[-+\d.]',log)
        else:
            if startup_deadline.matches(r):
                from package_round70 import route_hash
                deadline_check=startup_deadline.check(folder,p,r,run,__import__(__name__),route_hash)
                coverage.append(dict(number=e['charged_number'],id=e['id'],arm=e['arm'],**deadline_check))
            else:
                assert r['external_gini_tree_root_coverage_valid'] and r['external_gini_tree_parent_child_coverage_valid']
            assert not r['external_gini_tree_internal_budget_scheduling']
            assert not (folder/'external/optional_budget.csv').exists()
            if calls:assert r['external_gini_tree_backend_parameter_roundtrip_valid']
            for call in calls:
                if call['solve_kind']=='LP':assert call['integer_domain_restored']=='1'
            leaves=rows(folder/'external/paper_leaf_ledger.csv')
            if leaves:coverage.append(dict(number=e['charged_number'],id=e['id'],arm=e['arm'],**tree_coverage(folder,leaves,p)))
            active=[l for l in leaves if l['status'] not in ['replaced','coalesced']]
            if active:assert LB<=min(UB,min(float(l['lower_bound']) for l in active))+1e-7
        for c in calls:
            calls_all.append(dict(number=e['charged_number'],id=e['id'],arm=e['arm'],**c))
            log_path=run.ROOT/c['native_log']
            native_text=log_path.read_text(encoding='utf-8',errors='replace')
            dimensions=re.search(r'Optimize a model with (\d+) rows, (\d+) columns and (\d+) nonzeros',native_text)
            lp_bound=re.search(r'Optimal objective\s+([-+\d.eE]+)',native_text)
            for line_number,line in enumerate(native_text.splitlines(),1):
                event=None
                if re.match(r'^\s*[H*]\s*\d',line):
                    fields=line.split()
                    if len(fields)>=7 and fields[-1].endswith('s'):
                        event=dict(event='printed_search_incumbent',native_objective=float(fields[-5]),
                            rounded_native_seconds=float(fields[-1][:-1]))
                else:
                    matched=re.search(r'(Loaded user MIP start with objective|Found heuristic solution: objective)\s+([-+\d.eE]+)',line)
                    if matched:event=dict(event=matched[1],native_objective=float(matched[2]),rounded_native_seconds=None)
                if event:
                    incumbent_events.append(dict(number=e['charged_number'],id=e['id'],arm=e['arm'],
                        leaf_id=c['leaf_id'],solve_kind=c['solve_kind'],native_log=c['native_log'],line=line_number,
                        raw_line=line,scope='Native telemetry; no independent intermediate vector retained',**event))
            native_statistics.append(dict(number=e['charged_number'],id=e['id'],arm=e['arm'],
                leaf_id=c['leaf_id'],solve_kind=c['solve_kind'],model_sha256=c['model_sha256'],
                original_rows=dimensions[1] if dimensions else None,original_columns=dimensions[2] if dimensions else None,
                original_nonzeros=dimensions[3] if dimensions else None,
                logged_LP_optimum=float(lp_bound[1]) if lp_bound and c['solve_kind']=='LP' else None))
        phases=rows(folder/'phases.csv')
        elapsed=lambda name:next((float(x['process_seconds']) for x in phases if x['event']==name),None)
        hga=r.get('hga_wall_time_seconds',0)
        initial_signature=None;initial_objective=None
        if (folder/'external/initial_witness.json').exists():
            initial=run.read(folder/'external/initial_witness.json')
            initial_objective=initial.get('F',initial.get('objective'))
            semantic=dict(objective=initial_objective,routes=[{k:v for k,v in x.items()
                if k in ['vehicle','nodes','operations']} for x in initial['routes']])
            initial_signature=hashlib.sha256(json.dumps(semantic,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        count_lp=sum(c['solve_kind']=='LP' for c in calls)
        rec=dict(number=e['charged_number'],id=e['id'],arm=e['arm'],stage=e['stage'],kind=e['kind'],
            input_sha256=p['input_sha256'],V=p['V'],M=p['M'],Q=p['Q'],T=p['T_seconds'],
            executable_sha256=e['executable_sha256'],cap=e['cap_seconds'],wall=done['wall_seconds'],
            internal_wall=r['final_process_wall_time_seconds'],certificate=cert,status=r['status'],UB=UB,LB=LB,
            signed_absolute_gap=UB-LB,relative_gap=(UB-LB)/abs(UB) if UB else None,
            gap_note='within numerical tolerance' if abs(UB-LB)<=1e-7 else 'open',
            hga_seconds=hga,exact_start=elapsed('exact_phase_start'),
            initial_objective=initial_objective,initial_route_signature=initial_signature,
            lp_calls=count_lp,mip_calls=(1 if e['arm']=='P-GRB' else len(calls)-count_lp),
            splits=r.get('external_gini_tree_split_count',0),failure=False,result_sha256=run.sha(folder/'result.json'),
            artifact_dir=e['destination'])
        records.append(rec)
        model_paths=list(folder.glob('external/**/*.lp'))
        if (folder/'compact.lp').exists():model_paths.append(folder/'compact.lp')
        for model in model_paths:
            # This is inexpensive on the small panel; run analysis between queues.
            text=model.read_text(encoding='utf-8',errors='strict')
            gen=text.partition('Generals\n')[2].partition('Binaries\n')[0]
            binary=text.partition('Binaries\n')[2].partition('End')[0]
            if e['arm'] in ['VD-S','VD-P']:
                assert 'r64_q_balance_' not in text and 'r63f_' not in text
                assert 'state_g_' in text and 'bit_' not in text
                assert re.search(r'(?m)^\s*load_\d+_\d+\s*$',gen)
                assert re.search(r'(?m)^\s*state_\d+_\d+\s*$',binary)
                assert 'state_code_' not in text
            models.append(dict(number=e['charged_number'],path=str(model.relative_to(run.ROOT)),sha256=run.sha(model),
                bytes=model.stat().st_size,arc_q='r64_q_balance_' in text,log_code_variables=len(re.findall(r'(?m)^\s*state_code_\d+_\d+\s*$',binary)),onehot_binaries=len(re.findall(r'(?m)^\s*state_\d+_\d+\s*$',binary))))
    table('runs.csv',records);table('witness_checks.csv',witnesses);table('native_calls.csv',calls_all);table('models.csv',models)
    table('coverage_checks.csv',coverage)
    table('native_statistics.csv',native_statistics)
    table('native_incumbent_events.csv',incumbent_events)
    pairs=[]
    for c in records:
        if c.get('failure') or c['arm'] not in ['VD-S','VD-P']:continue
        for b in records:
            references=['K1-R','P-GRB','VD-P'] if c['arm']=='VD-S' else ['K1-R','P-GRB']
            if b.get('failure') or b['id']!=c['id'] or b['cap']!=c['cap'] or b['stage']!=c['stage'] or b['arm'] not in references:continue
            pairs.append(dict(id=c['id'],cap=c['cap'],candidate_arm=c['arm'],candidate_number=c['number'],reference_number=b['number'],reference=b['arm'],
                candidate_certificate=c['certificate'],reference_certificate=b['certificate'],
                wall_delta=c['wall']-b['wall'],UB_delta=c['UB']-b['UB'],LB_delta=c['LB']-b['LB'],
                signed_gap_delta=c['signed_absolute_gap']-b['signed_absolute_gap'],paired_build=c['executable_sha256']==b['executable_sha256'],
                practical_classification=practical_classification(c,b),
                bound_tradeoff='mixed' if (c['UB']-b['UB'])*(c['LB']-b['LB'])>1e-14 else 'aligned_or_unchanged'))
            pairs[-1]['same_paid_initial_routes']=c['initial_route_signature']==b['initial_route_signature'] if b['arm']!='P-GRB' else None
    table('pairs.csv',pairs)
    revisions=[run.read(p) for p in sorted(run.OUT.glob('resource_plan_update_*.json'))]
    reference_runs=[run.read(run.ROOT/e['destination']/'completion.json') for e in run.runner.entries()
                    if not e['charged'] and (run.ROOT/e['destination']/'completion.json').exists()]
    run.write(run.OUT/'resource_status.json',dict(charged_completed=len(records),performance=sum(r.get('kind')=='performance' for r in records),
        native_micro=sum(r.get('kind')=='native-micro' for r in records),actual_wall_seconds=sum(r['wall'] for r in records),
        experiment_optimizer_calls=sum(r.get('lp_calls',0)+r.get('mip_calls',0) for r in records),
        **run.read(run.OUT/'qualification.json'),
        reference_build_only_runs=len(reference_runs),reference_build_wall_seconds=sum(x['wall_seconds'] for x in reference_runs),
        initial_performance_limit=run.read(run.OUT/'protocol.json')['maximum_performance'],
        revised_performance_limit=max([run.read(run.OUT/'protocol.json')['maximum_performance']]+[
            r.get('revised_performance_total',0) for r in revisions]),
        approved_worst_case_experiment_seconds=run.read(run.OUT/'protocol.json')['worst_case_seconds'],
        failures=sum(r.get('failure',False) for r in records)))
    for r in records:print(r['id'],r['arm'],r.get('certificate'),round(r['wall'],3),r.get('UB'),r.get('LB'),'HGA',r.get('hga_seconds'))
if __name__=='__main__':analyze()
