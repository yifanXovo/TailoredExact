"""Read-only current-arm analysis, with explicit shared-control denominators."""
from round132_common import *
from round127_analysis import pair as inherited_pair,qualified
from round127_analysis import root as actual_root
from compare_round112_startup import reconstruct as H
import round108_reader as core
import csv,collections,copy,math,re,statistics

def csv_table(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,keys);w.writeheader()
        for r in rows:w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list,tuple)) else v for k,v in r.items()})

def disclosed_source_loss(a,l):
    """Keep an own-zero proof without relaxing frozen performance eligibility."""
    assert a.get('source_reduced') is True and a.get('native_proof_qualified') is False
    assert all(a.get(k) is True for k in ['formal_protocol_qualified','numbers_qualified','certificate_qualified'])
    assert a.get('own_exact_zero') is True and a.get('certificate') is True
    assert a.get('proof_evidence')==a.get('certificate_source')=='OWN_ZERO_CERTIFICATE'
    assert a['U']==a['L']==a['gap']==0 and a['raw_reconstructed_T_cert']==a['T_produce']
    d=core.portable(ROOT,l['destination']);ind=read(d/'independent_evidence.json');rejected=read(d/'claim_rejections.json')
    assert ind['own_U']==0 and ind['own_exact_zero'] and ind['own_physical_verified'] and ind['independent_floor0']
    zeros=[w for w in ind['witnesses'] if w['arm']==l['arm'] and w['physical_verified'] and w['G']==w['P']==w['F']==0]
    assert zeros and rejected['damaged_calls'] and rejected['rejections']
    assert all(r['call_rejected_as_a_whole'] and r['counterexample']['arm']==l['arm'] and
        r['counterexample']['F']==r['counterexample']['G']==0 for r in rejected['rejections'])
    return dict(line=a['line'],id=a['id'],seed=a['seed'],method=a['method'],
        own_physical_zero_certificate_retained=True,native_proof_qualified=False,
        source_reduced=True,formal_performance_evidence_eligible=False,
        raw_reconstructed_T_cert=a['raw_reconstructed_T_cert'],formal_performance_T_cert=None,
        T_produce=a['T_produce'],T_verify=a['T_verify'],T_total=a['T_total'],
        disposition='UNEVALUABLE formal performance; independent own-zero proof retained; not ordinary open',
        damaged_calls=rejected['damaged_calls'],rejected_bound_values=[r['value'] for r in rejected['rejections']],
        own_zero_witness_sequences=sorted({w.get('sequence') for w in zeros if w.get('sequence') is not None}),
        native_source_reliability_unresolved=True,no_native_retry=True,
        sources=[dict(path=p.relative_to(ROOT).as_posix(),SHA=sha(p)) for p in
            [d/'independent_evidence.json',d/'claim_rejections.json',d/'producer_receipt.json']])

def physical(p,d,a,witness=None):
    r=read(d/'result.json') if witness is None else witness
    fleet=core.full_fleet(ROOT,p,r);instance=core.evidence.instance(ROOT,p)
    assert abs(fleet['F']-a['U'])<=1e-7
    pickups=[];drops=[];returns=[];route_rows=[]
    for route in fleet['routes']:
        k=route['vehicle'];P=sum(op['pickup'] for op in route['operations']);D=sum(op['drop'] for op in route['operations']);load=0;peak=0
        # Operations are serialized by station id, not necessarily route order.
        operation={op['station']:op for op in route['operations']}
        for station in route['nodes'][1:-1]:
            op=operation.get(station,dict(pickup=0,drop=0));load+=op['pickup']-op['drop'];peak=max(peak,load)
            assert 0<=load<=p['Q_vector'][k]
        travel=sum(math.dist(instance['xy'][i],instance['xy'][j])/1.5 for i,j in zip(route['nodes'],route['nodes'][1:]))
        route_rows.append(dict(vehicle=k,stations=len(route['operations']),pickup=P,drop=D,return_load=load,peak_load=peak,Q=p['Q_vector'][k],
            travel_seconds=travel,handling_seconds=(p['pickup_seconds']+p['drop_seconds'])*P,total_seconds=travel+(p['pickup_seconds']+p['drop_seconds'])*P,T=p['T_seconds']))
        pickups.append(P);drops.append(D);returns.append(load)
    Omega=sum(instance['w'][1:]);assert Omega>0
    assert sum(fleet['Y'][1:])==sum(instance['b'][1:])-sum(returns)
    return dict(G_true=fleet['G'],P_true=fleet['P'],P_avg=fleet['P']/Omega,Omega=Omega,lambda_value=p['lambda'],rho=p['lambda']*Omega,
        final_inventory=fleet['Y'][1:],initial_inventory=instance['b'][1:],target=instance['D'][1:],
        total_initial_inventory=sum(instance['b'][1:]),total_final_inventory=sum(fleet['Y'][1:]),
        serviced_stations=sum(len(q['operations']) for q in fleet['routes']),pickups=pickups,drops=drops,return_loads=returns,route_resources=route_rows)

def parsed_log(path):
    text=path.read_text(encoding='utf-8',errors='replace')
    def one(pattern):
        found=re.findall(pattern,text)
        return found[0] if len(found)==1 else None
    before=one(r'Optimize a model with (\d+) rows, (\d+) columns and (\d+) nonzeros')
    after=one(r'Presolved: (\d+) rows, (\d+) columns, (\d+) nonzeros')
    root=one(r'Root relaxation: objective\s+([-+0-9.eE]+),\s*(\d+) iterations,\s*([-+0-9.eE]+) seconds \(([-+0-9.eE]+) work units\)')
    # The last printed root row is an observation, not an exact post-cut root
    # attribute. Its rounded Time column must not be labelled Work.
    root_rows=[(i+1,line) for i,line in enumerate(text.splitlines()) if re.match(r'^\s*0\s+\d+\s+',line)]
    return dict(path=path.relative_to(ROOT).as_posix(),SHA=sha(path),
        before_size=list(map(int,before)) if before else None,after_presolve_size=list(map(int,after)) if after else None,
        MIP_initial_root_relaxation_bound=float(root[0]) if root else None,root_iterations=int(root[1]) if root else None,
        initial_root_relaxation_seconds=float(root[2]) if root else None,initial_root_relaxation_Work=float(root[3]) if root else None,
        last_printed_zero_explored_row=dict(line=root_rows[-1][0],text=root_rows[-1][1]) if root_rows else None,
        MIP_post_root_cuts_bound=None,MIP_root_Work=None,
        missing_reason='unrecorded or not uniquely exposed by this actual log; never backfilled from terminal values')

def costs(p,d,a,heavy):
    r=read(d/'result.json');ledger_path=d/'external/paper_optimize_ledger.csv';ledger=core.rows(ledger_path) if ledger_path.exists() else []
    def summed(field,rows):
        if not rows:return 0. if a['native_Optimize']==0 else None
        try:return sum(float(q[field]) for q in rows)
        except (KeyError,ValueError):return None
    LP=[q for q in ledger if q['solve_kind']=='LP'];MIP=[q for q in ledger if q['solve_kind']!='LP']
    native_LP=core.rows(d/'external/lp_status_ledger.csv') if (d/'external/lp_status_ledger.csv').exists() else []
    first=next((q for q in native_LP if q['leaf_id']=='L0'),None)
    starts=[read(q) for q in (d/'external/native_logs').glob('*.round68.start.json')]
    if (d/'native.log.round112.start.json').exists():starts.append(read(d/'native.log.round112.start.json'))
    result=dict(native_Optimize=a['native_Optimize'],canonical_continuous_LP_bound=float(first['lower_bound']) if first and first['bound_available']=='1' else None,
        canonical_continuous_LP_interpretation='own paid S2R/S2 continuous LP, not a MIP-specific root relaxation',
        LP_calls=len(LP),MIP_calls=len(MIP) if ledger else a['native_Optimize'],child_LP_calls=sum(q['leaf_id']!='L0' for q in LP),
        target_MIP_calls=sum(q['solve_kind']!='MIP' for q in MIP),
        LP_native_seconds=summed('solver_runtime',LP),MIP_native_seconds=summed('solver_runtime',MIP) if ledger else r.get('gurobi_runtime'),
        LP_Work=summed('work',LP),MIP_Work=summed('work',MIP) if ledger else r.get('gurobi_work'),
        nodes=summed('nodes',ledger) if ledger else r.get('gurobi_node_count'),
        native_simplex_iterations=summed('simplex_iterations',ledger) if ledger else None,
        native_barrier_iterations=summed('barrier_iterations',ledger) if ledger else None,
        model_build_seconds=r.get('external_gini_tree_model_build_seconds') if ledger else r.get('gurobi_model_build_seconds'),
        model_read_seconds=r.get('external_gini_tree_model_read_seconds') if ledger else r.get('gurobi_model_read_seconds'),
        split_count=r.get('external_gini_tree_split_count') if ledger else None,
        actual_submitted_Starts=sum(bool(q.get('submitted')) for q in starts),
        Start_mapping_seconds=sum(q['mapping_validation_submission_seconds'] for q in starts) if starts and all('mapping_validation_submission_seconds' in q for q in starts) else None,
        native_exposed=a['native_Optimize']>0,Start_receipts=len(starts))
    result['Start_statuses']=[q.get('status','unknown') for q in starts]
    result['Start_exact_vectors_observed']=[q.get('exact_vector_observed_in_mipsol') for q in starts]
    result['Start_integer_vectors_observed']=[q.get('integer_vector_observed_in_mipsol') for q in starts]
    result['paid_compact_native_adoption']=a.get('native_adoption')
    result['Start_adoption_caveat']='Submission/readback alone do not prove native adoption; only retained actual log/callback evidence is reported.'
    phases=core.rows(d/'phases.csv') if (d/'phases.csv').exists() else []
    phase_times={q['event']:float(q['process_seconds']) for q in phases}
    Hcost=r.get('process_elapsed_at_exact_phase_start_seconds') if a['method']!='P' else 0.
    if a['method']!='P' and a['native_Optimize']==0:
        Hcost=None # Startup-zero has no exact-phase start; use recorded phases.
    result.update(H_plus_admission_seconds=Hcost,production_phase_times=phase_times,
        T_produce=a['T_produce'],T_verify=a['T_verify'],T_total=a['T_total'])
    if heavy:
        paths=sorted((d/'external/native_logs').glob('*.log'))
        if not paths and (d/'native.log').exists():paths=[d/'native.log']
        result['actual_call_logs']=[parsed_log(q) for q in paths]
        progress=r.get('gurobi_progress_path');p=core.portable(ROOT,progress) if progress else None
        last_zero=None
        if p is not None and p.is_file():
            for q in core.rows(p):
                if q.get('processed_nodes')=='0':last_zero=q
        result['last_recorded_zero_processed_node_callback']=last_zero
        result['zero_node_callback_scope']='Actual recorded callback row if present; no claim it is the exact end of native root processing.'
        m,c=actual_root(d) if ledger else (core.lp_model(d/'compact.lp') if (d/'compact.lp').exists() else None,None)
        result.update(root_rows=len(m['rows']) if m else None,root_columns=len(m['order']) if m else None,
            root_nonzeros=sum(len(t) for t,s,b in m['rows']) if m else None,
            root_W_present='W_SP' in m['types'] if m else None,
            root_scope=[c['lower_g'],c['upper_g']] if c else None,root_cutoff=c.get('cutoff') if c else None)
    return result

def summary(aa,pp):
    both=[q for q in pp if q['classification']=='BOTH_CERTIFIED'];ratios=[q['right_over_left_certification_ratio'] for q in both]
    return dict(problems=len({q['id'] for q in pp}),repeated_comparisons=len(pp),
        directions=dict(collections.Counter(q['direction'] for q in pp)),classes=dict(collections.Counter(q['classification'] for q in pp)),
        certificates={m:sum(qualified(a) and a['certificate'] for a in aa if a['method']==m) for m in sorted({a['method'] for a in aa})},
        both_certified_n=len(both),both_certified_intersection=[dict(id=q['id'],seed=q['seed']) for q in both],
        conditional_geometric_mean_right_over_left=math.exp(statistics.fmean(map(math.log,ratios))) if ratios else None,
        denominator_warning='Shared controls and repeated Seeds; no independence, population Win-rate or cap-imputed certification ratio')

def trajectory_index(d,heavy):
    names=['progress.csv','samples.jsonl','observations.json','native_claims.json',
        'independent_evidence.json','native.log','external/paper_optimize_ledger.csv',
        'external/lp_status_ledger.csv','external/paper_tree_events.csv',
        'external/split_decision_ledger.csv']
    rows=[]
    for name in names:
        p=d/name
        if p.exists():rows.append(dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,SHA=sha(p) if heavy else None))
    result=read(d/'result.json');extra=result.get('gurobi_progress_path')
    if extra:
        p=core.portable(ROOT,extra)
        if p.is_file():rows.append(dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,SHA=sha(p) if heavy else None,
            scope='actual compact native callback trajectory outside the arm directory; current-only carrier member'))
    return dict(sources=rows,no_interpolation=True,
        scope='Actual own-run trajectories and bound/cover sources; native call bounds are not automatically full-domain bounds. No endpoint backfill or common-time gap comparison is manufactured.')

def historical_physical():
    path=ROOT/'results/unified_exact_round131/review/final_independent_evidence.json'
    if not path.exists():path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(git('show',BASE+':'+path.relative_to(ROOT).as_posix()))
    reference=read(path);assert reference['status']=='PASS'
    rows=[];prior=read(ROOT/'results/unified_exact_round131/observations.json')['arms']
    roles=read(ROOT/'results/unified_exact_round131/input_manifest.json')['roles']
    for id in ['SC-C15-B','PB-C35-U']:
        p=next(x for x in roles if x['id']==id)
        a=next(x for x in prior if (x['id'],x['seed'],x['repeat'],x['method'])==(id,0,1,'S2'))
        old=next(x for x in reference['arm_evidence'] if (x['id'],x['seed'],x['repeat'],x['method'])==(id,0,1,'S2'))
        assert old['qualified']
        rows.append(dict(line='R131 historical final S2',id=id,seed=0,method='S2',
            inherited_from=path.relative_to(ROOT).as_posix(),inherited_source_SHA=sha(path),new_performance_observation=False,
            **physical(p,None,a,witness=old['final_complete_fleet'])))
    csv_table(OUT/'historical_physical_outcomes.csv',rows)
    write(OUT/'historical_physical_outcomes.json',dict(rows=rows,exact_small_dependency_only=True,
        no_historical_raw_carrier_restored=True,no_Optimize=True))

def same_H_and_scope():
    rows=[]
    for line,groups in [('D',read(OUT/'experiment_plan.json')['D']),('C',read(OUT/'C_experiment_plan.json')['groups'])]:
        for g in groups:
            if line=='D' and 'PS' not in g['methods']:continue
            camp=OUT/g['name'];launches=read(camp/'identity.json')['launches'];hs={};meta={};aa=read(camp/'reconstructed.json')['arms']
            native={l.get('comparison_method',l['method']):a['native_Optimize'] for a,l in zip(aa,launches)}
            for l in launches:
                method=l.get('comparison_method',l['method'])
                if method=='P':continue
                d=core.portable(ROOT,l['destination']);hs[method]=H(ROOT,l['panel'],d)
                calls=[x['payload'] for x in read(d/'observations.json') if x['payload']['kind']=='call' and x['payload'].get('leaf')=='L0']
                meta[method]=calls[0] if calls else None
            wanted=[['S2','PS']] if line=='D' else [['S2R-GEOM','S2R'],['S2R-SP','S2R']]
            for left,right in wanted:
                a,b=hs[left],hs[right];same=bool(a['complete'] and b['complete'] and a['fleet']==b['fleet'] and a['semantic_traces']==b['semantic_traces'])
                c,d=meta[left],meta[right];scope=bool(c and d and all(c[k]==d[k] for k in ['lower_g','upper_g','cutoff'])) if line=='C' else None
                rows.append(dict(line=line,id=g['role']['id'],seed=g['seed'],left=left,right=right,
                    complete_own_H_equal=same,left_complete_H=a['complete'],right_complete_H=b['complete'],
                    left_own_start_U=a['physical']['F'],right_own_start_U=b['physical']['F'],
                    C_actual_root_interval_cutoff_equal=scope,
                    both_native_backends_exposed=bool(native[left] and native[right]),
                    paid_H_backend_attribution_eligible=same and bool(native[left] and native[right]) and (line=='D' or scope),
                    interpretation='D is complete S2 package versus independently paid-H compact; C changes only the admitted expression on the same inclusive root. Equal Start rules alone never imply identical realized H.'))
    write(OUT/'same_H_and_scope.json',dict(records=rows,no_Optimize=True,no_cross_arm_information=True))

def run(partial=False,heavy=True):
    assert (OUT/'sequence_completion.json').exists(),'Defer complete raw-table decoding until the native sequence has finished'
    assert not budget()['unclosed'],'Defer complete raw-table decoding until native/qualification child receipts close'
    arms=[];pairs=[];cc=[];physical_rows=[];missing=[];trajectories=[];inputs=[];issues=[];source_losses=[]
    environment_path=OUT/'timing_environment_amendment.json'
    environment=read(environment_path)
    inputs.append(dict(path=environment_path.relative_to(ROOT).as_posix(),SHA=sha(environment_path)))
    sets=[('D',read(OUT/'experiment_plan.json')['D'])]
    if (OUT/'C_experiment_plan.json').exists():sets.append(('C',read(OUT/'C_experiment_plan.json')['groups']))
    for line,groups in sets:
        binding_path=OUT/('D_execution_binding.json' if line=='D' else 'C_execution_binding.json')
        binding=read(binding_path);plan_path=OUT/('experiment_plan.json' if line=='D' else 'C_experiment_plan.json')
        assert sha(plan_path)==binding['plan_SHA']
        inputs.extend(dict(path=p.relative_to(ROOT).as_posix(),SHA=sha(p)) for p in [binding_path,plan_path])
        for g in groups:
            camp=OUT/g['name'];rp=camp/'reconstructed.json'
            if not rp.exists():missing.append(dict(line=line,group=g['name']));continue
            ip=camp/'identity.json';assert sha(ip)==binding['groups'][g['name']]
            inputs.extend(dict(path=p.relative_to(ROOT).as_posix(),SHA=sha(p)) for p in [ip,rp])
            i=read(ip);aa=copy.deepcopy(read(rp)['arms']);assert len(aa)==len(i['launches'])
            for a,l in zip(aa,i['launches']):
                legacy_formal=a.pop('formal_performance',None)
                for key,expected in [('id',l['id']),('input_SHA',l['panel']['input_sha256']),('seed',l['seed']),('repeat',l['repeat']),('method',l['method'])]:
                    assert a[key]==expected,('sealed arm identity mismatch',line,g['name'],key,a.get(key),expected)
                assert core.portable(ROOT,a['destination'])==core.portable(ROOT,l['destination'])
                assert sha(ROOT/l['panel']['input_path'])==a['input_SHA']
                a.update(line=line,layer=l['panel'].get('layer') if line=='D' else 'C',group=g['number'],
                    method=l.get('comparison_method',l['method']),underlying_reader_method=l['method'],
                    formal_plan_member=True,raw_inherited_formal_performance_flag=legacy_formal,
                    formal_performance_evidence_eligible=qualified(a),nominal_source=p_source(l),
                    signed_gap=a['U']-a['L'] if a.get('U') is not None and a.get('L') is not None else None,
                    observed_horizon=a['T_produce'],censored=not a['certificate'] if qualified(a) else None,
                    raw_reconstructed_T_cert=a.get('T_cert'),raw_reconstructed_certificate=a.get('certificate'))
                loss=None
                if not qualified(a) and a.get('source_reduced'):
                    loss=disclosed_source_loss(a,l);source_losses.append(loss)
                    a.update(T_cert=None,performance_qualification_disposition=loss['disposition'])
                    inputs.extend(loss['sources'])
                else:
                    a['performance_qualification_disposition']='QUALIFIED' if qualified(a) else 'UNQUALIFIED_UNRESOLVED'
                assert a['T_cert']==(a['T_produce'] if qualified(a) and a['certificate'] else None)
                if line=='D':assert a['PE_SHA']==PE_SHA
                else:assert a['PE_SHA']==read(OUT/'research_build.json')['PE_SHA']
                d=Path(l['destination'])
                try:
                    assert qualified(a) or loss is not None,'Existing independent evidence is unqualified and unresolved'
                    assert all(isinstance(a.get(k),(int,float)) and math.isfinite(a[k]) for k in ['U','L'])
                    producer=d/'producer_receipt.json'
                    assert sha(producer)==a['producer_receipt_SHA']
                    clock=read(producer);begin=clock['t0_unix'];end=clock['t_produce_unix']
                    assert begin<=end
                    overlap=lambda stop:max(0.,min(end,stop)-max(begin,environment['old_waiter_creation_unix']))
                    lo=overlap(environment['old_waiter_stop_unix_lower']);hi=overlap(environment['old_waiter_stop_unix_upper'])
                    a.update(stage_waiter_lifetime_overlap_lower_seconds=lo,
                        stage_waiter_lifetime_overlap_upper_seconds=hi,
                        stage_waiter_lifetime_overlap=hi>0,
                        timing_environment_scope='possible boundary overlap with original waiter lifetime' if lo==0<hi else
                            'conservative overlap with original waiter lifetime; not parsing/CPU-contention/slowdown seconds' if lo>0 else
                            'no original-waiter lifetime overlap; ambient load not ruled out',
                        counterfactual_clean_machine_T_cert=None)
                    inputs.append(dict(path=producer.relative_to(ROOT).as_posix(),SHA=sha(producer)))
                    f=physical(l['panel'],d,a)
                    if loss is not None:assert f['G_true']==f['P_true']==0
                except (AssertionError,ValueError,KeyError,FileNotFoundError) as error:
                    issue=dict(line=line,group=g['number'],id=a['id'],seed=a['seed'],method=a['method'],error=repr(error))
                    issues.append(issue);a.update(derived_analysis_issue=issue,formal_protocol_qualified=False,objective_class='unevaluable',
                        formal_performance_evidence_eligible=False,
                        raw_reconstructed_T_cert=a.get('T_cert'),raw_reconstructed_certificate=a.get('certificate'),T_cert=None,certificate=False)
                    arms.append(a);continue
                a['objective_class']='zero' if f['G_true']==0 and f['P_true']==0 else 'positive'
                a['near_zero_positive_U']=0<a['U']<=1e-7
                a['objective_class_scope']='own attained physical objective, not an unproved classification of the optimum'
                a.update(G_true=f['G_true'],P_true=f['P_true'],P_avg=f['P_avg'],Omega=f['Omega'],rho=f['rho'])
                physical_rows.append(dict(line=line,id=a['id'],seed=a['seed'],method=a['method'],**f))
                cc.append(dict(line=line,id=a['id'],seed=a['seed'],method=a['method'],**costs(l['panel'],d,a,heavy)));arms.append(a)
                trajectories.append(dict(line=line,id=a['id'],seed=a['seed'],method=a['method'],**trajectory_index(d,heavy)))
            by={a['method']:a for a in aa};wanted=g['pairs'] if line=='D' else [['S2R-GEOM','S2R'],['S2R-SP','S2R']]
            for left,right in wanted:
                q=inherited_pair(g['role']['id'],by[left],by[right],kind=f'R132_{line}',seed=g['seed'])
                q.pop('legacy_materiality',None);q.update(line=line,layer=g['role'].get('layer') if line=='D' else 'C',group=g['number'],
                    V=g['role']['V'],objective_class=by[left]['objective_class'] if by[left]['objective_class']==by[right]['objective_class'] else 'mixed_attained_endpoints',
                    left_stage_waiter_lifetime_overlap=by[left].get('stage_waiter_lifetime_overlap'),
                    right_stage_waiter_lifetime_overlap=by[right].get('stage_waiter_lifetime_overlap'))
                if q['classification']=='BOTH_CERTIFIED':
                    dt=q['left_minus_right_seconds'];threshold=max(10.,.1*min(by[left]['T_cert'],by[right]['T_cert']))
                    q.update(material_threshold_seconds=threshold,materiality='LEFT_MATERIALLY_FASTER' if -dt>=threshold else 'RIGHT_MATERIALLY_FASTER' if dt>=threshold else 'TIME_CLOSE')
                pairs.append(q)
    if not partial:assert not missing,missing
    assert len(arms)==len({(a['line'],a['id'],a['seed'],a['method']) for a in arms})
    conflicts=[];problem_classes={};problem_class_records=[]
    for key in sorted({(a['line'],a['input_SHA']) for a in arms}):
        sub=[a for a in arms if (a['line'],a['input_SHA'])==key and qualified(a)];best_U=min((a['U'] for a in sub),default=None)
        for a in sub:
            if qualified(a) and a['L']>best_U+1e-7:conflicts.append(dict(line=a['line'],id=a['id'],seed=a['seed'],method=a['method'],own_L=a['L'],other_own_legal_U=best_U))
        zero=[a for a in sub if a.get('G_true')==0 and a.get('P_true')==0]
        positive=[a for a in sub if a['L']>1e-7]
        status='zero_proved_by_qualified_physical_zero' if zero else 'positive_under_qualified_lower_bound' if positive else 'unknown_optimum_class'
        problem_classes[key]=status
        witnesses=zero if zero else positive
        problem_class_records.append(dict(line=key[0],input_SHA=key[1],ids=sorted({a['id'] for a in sub}),
            problem_objective_class=status,evidence=[{k:a.get(k) for k in ['id','seed','method','producer_receipt_SHA','G_true','P_true','U','L']} for a in witnesses]))
    write(OUT/'cross_arm_consistency.json',dict(status='CONTRADICTION_REQUIRES_INVESTIGATION' if conflicts else 'PASS',conflicts=conflicts,
        no_incumbent_bound_or_certificate_transferred=True,scope='Read-only consistency only; every reported certificate remains based on its own physical fleet and qualified proof.'))
    assert not conflicts,conflicts
    for a in arms:a['problem_objective_class']=problem_classes[a['line'],a['input_SHA']]
    for q in pairs:
        statuses={a['problem_objective_class'] for a in arms if a['line']==q['line'] and a['id']==q['id']}
        assert len(statuses)==1
        q['problem_objective_class']=statuses.pop()
    write(OUT/'problem_objective_classification.json',dict(records=problem_class_records,
        scope='Descriptive problem-level status from already sealed qualified physical zeros or positive bounds under the numerical policy. Own attained-endpoint classes remain separate.',
        unknown_is_not_positive=True,near_zero_positive_is_not_zero=True,
        no_arm_U_L_T_cert_or_certificate_changed=True,no_information_supplied_to_production=True))
    strat={}
    for line in ['D','C']:
        aa=[a for a in arms if a['line']==line];pp=[p for p in pairs if p['line']==line]
        for left,right in sorted({(q['left'],q['right']) for q in pp}):
            for layer in sorted({q['layer'] for q in pp if q['left']==left and q['right']==right}):
                qq=[q for q in pp if (q['left'],q['right'],q['layer'])==(left,right,layer)]
                sub=[a for a in aa if a['layer']==layer and a['method'] in [left,right] and a['id'] in {q['id'] for q in qq}]
                strat[f'{line}:{layer}:{left}/{right}']=summary(sub,qq)
    grouped={}
    for line in ['D','C']:
        pp=[p for p in pairs if p['line']==line]
        for left,right in sorted({(q['left'],q['right']) for q in pp}):
            selected=[q for q in pp if (q['left'],q['right'])==(left,right)]
            dimensions=['id','V','objective_class','problem_objective_class']
            for dimension in dimensions:
                for value in sorted({str(q[dimension]) for q in selected}):
                    qq=[q for q in selected if str(q[dimension])==value]
                    relevant={(q['id'],q['seed']) for q in qq}
                    sub=[a for a in arms if a['line']==line and a['method'] in [left,right] and (a['id'],a['seed']) in relevant]
                    grouped[f'{line}:{left}/{right}:{dimension}={value}']=summary(sub,qq)
            if line=='D':
                for layer in ['K','X']:
                    for size in sorted({q['V'] for q in selected if q['layer']==layer}):
                        qq=[q for q in selected if q['layer']==layer and q['V']==size]
                        relevant={(q['id'],q['seed']) for q in qq}
                        sub=[a for a in arms if a['line']==line and a['method'] in [left,right] and (a['id'],a['seed']) in relevant]
                        grouped[f'D:{layer}:{left}/{right}:V={size}']=summary(sub,qq)
    Dcount=sum(a['line']=='D' for a in arms);Ccount=sum(a['line']=='C' for a in arms)
    dtext=f'The full new-input campaign has {Dcount}/60 sealed independently paid observations. '
    for layer in ['K','X']:
        key=f'D:{layer}:S2/P'
        if key in strat:
            s=strat[key];dtext+=f"In {layer}, S2/P qualified certificate counts are {s['certificates'].get('S2',0)}/{s['certificates'].get('P',0)} across {s['repeated_comparisons']} repeated comparisons on {s['problems']} problems; strict directions are {s['directions']}. "
    dtext+='These are finite within-mechanism and geography-transfer observations; same-problem Seeds are repeats, and both-open times remain censored. PS attribution is confined to its prospectively selected six-problem subset. Problem-level zero/positive/unknown status is distinguished from each arm\'s attained endpoint; a zero observation at35 stations does not establish positive-objective35 proof performance.'
    if source_losses:
        dtext+=f' There are {len(source_losses)} disclosed source-reduced own-zero observations: their legal own physical zero proofs and raw production clocks remain, but frozen performance eligibility excludes them, formal T_cert is null and affected comparisons are UNEVALUABLE. They are neither ordinary open results nor time Wins; the rejected native sources are not rehabilitated.'
    ctext=f'The cost panel has {Ccount}/24 sealed same-build workflows. '
    for method in ['S2R-GEOM','S2R-SP']:
        key=f'C:C:{method}/S2R'
        if key in strat:ctext+=f"{method} / S2R gives {strat[key]['directions']} across {strat[key]['repeated_comparisons']} repeated comparisons. "
    ctext+='Any native-process or cost change is not an ideal relaxation-strength increase; unexposed root/node fields remain unknown.'
    write(OUT/'source_loss_dispositions.json',dict(records=source_losses,
        policy='Frozen R127 source_reduced exclusion unchanged; R130 raw own-zero reconstruction retained separately',
        policy_scope='Reporting/clock reconciliation only; no eligibility relaxation, source repair, certificate transfer or production change',
        raw_reconstructed_files_unchanged=True,no_Optimize=True))
    result=dict(UTC=utc(),execution='PARTIAL' if missing else 'EVIDENCE_ISSUE_REQUIRES_INVESTIGATION' if issues else 'ALL_C_D_ARMS_SEALED',arms=arms,pairs=pairs,missing=missing,analysis_issues=issues,
        performance_qualified_observations=sum(qualified(a) for a in arms),disclosed_source_loss_observations=len(source_losses),
        raw_reconstructed_files_unchanged=True,heavy_static_analysis=heavy,no_Optimize=True)
    write(OUT/'observations.json',result);write(OUT/'stratified_summary.json',dict(strata=strat,problem_size_objective_strata=grouped,D_arms=Dcount,C_arms=Ccount,
        manuscript_D_statement=dtext,manuscript_C_statement=ctext,seed_repeats_not_independent=True,full_raw_signed_gaps_preserved=True))
    csv_table(OUT/'arms.csv',arms);csv_table(OUT/'pairs.csv',pairs);csv_table(OUT/'mechanism_costs.csv',cc);csv_table(OUT/'physical_outcomes.csv',physical_rows)
    if not partial:csv_table(OUT/'timing_environment_exposure.csv',[
        {k:a.get(k) for k in ['line','id','seed','method','group','producer_receipt_SHA',
            'stage_waiter_lifetime_overlap_lower_seconds','stage_waiter_lifetime_overlap_upper_seconds',
            'stage_waiter_lifetime_overlap','timing_environment_scope','counterfactual_clean_machine_T_cert']}
        for a in arms])
    write(OUT/'trajectory_index.json',dict(arms=trajectories,common_time_comparisons='not claimed; retained actual trajectories only'))
    write(OUT/'analysis_inputs.json',dict(inputs=inputs,runner_SHA=sha(__file__),issues=issues,no_Optimize=True,
        immutable_group_arm_input_Seed_and_destination_identity_checked=True))
    if not partial:assert (Dcount,Ccount,len(pairs))==(60,24,64)
    if not partial:assert not issues,issues
    if not partial:assert not budget()['unclosed'] and budget()['G1_seconds']<=144000,budget()
    if not partial:assert all(budget()['by_category'][k]<=limit for k,limit in LIMITS.items()),budget()
    if not partial:
        historical_physical();same_H_and_scope()
    write(OUT/'resource_accounting.json',dict(UTC=utc(),**budget(),active_not_yet_closed_excluded=True,
        delivery_plan=read(OUT/'delivery_cost_plan.json'),no_nested_cost_double_count=True))
    print(json.dumps(dict(D_arms=Dcount,C_arms=Ccount,pairs=len(pairs),missing=len(missing),heavy=heavy)))

def p_source(l):return l['panel'].get('source','known diagnostic role')
if __name__=='__main__':run(partial='--partial' in sys.argv,heavy='--light' not in sys.argv)
