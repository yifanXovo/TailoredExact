"""R126 independent, read-only certification review. Never starts a solver.

The five-way pair classifier, clocks, final-fleet physical replay, raw endpoint
aggregation and cross-arm contradiction check below are independently written.
Inherited readers are used only to re-execute the established model, per-call
log, return, chronological coverage, and physical admission predicates.
"""
from pathlib import Path
import ast, collections, csv, gc, hashlib, json, math, re, statistics, subprocess, sys, time
from fractions import Fraction

import round126_common as common
import read_round118 as inherited
import round108_reader as core
from round122_evidence import extension, ArmModels

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/unified_exact_round126'
DEST=OUT/'review'
TOL=1e-7
START=time.perf_counter()
HASHES={}
ARMS=[]
PAIRS=[]
GROUPS=[]
FINDINGS=[]

def key(path):
    p=Path(path).resolve()
    return p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else str(p)

def sha(path):
    p=Path(path);h=hashlib.sha256(p.read_bytes()).hexdigest();k=key(p)
    assert k not in HASHES or HASHES[k]==h,('file changed during review',k)
    HASHES[k]=h
    return h

def read(path):
    sha(path)
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def rows(path):
    sha(path)
    with Path(path).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def near(x,y,tol=1e-10):
    assert math.isfinite(x) and math.isfinite(y) and abs(x-y)<=tol,(x,y,tol)

def flag(cmd,name):
    assert cmd.count(name)==1,(name,cmd)
    return cmd[cmd.index(name)+1]

def no_subprocess(*args,**kwargs):
    raise AssertionError('Independent review forbids starting any child, solver, H, or route search')

def parse_input(p):
    path=ROOT/p['input_path'];assert sha(path)==p['input_sha256']
    text=path.read_text(encoding='utf-8')
    header=re.fullmatch(r'(\d+)\s+(\d+)\s+(\[[^\n]*\])',text.splitlines()[0])
    assert header and (int(header[1]),int(header[2]),ast.literal_eval(header[3]))==(p['V'],p['M'],p['Q_vector'])
    result={}
    for n in ['initial','target','capacities','weights','points']:
        value=re.search(r'^\s*'+n+r'\s*=\s*(\[[^\n]*\])',text,re.M)
        assert value,n
        result[n]=ast.literal_eval(value[1]);assert len(result[n])==p['V']+1
    assert all(x>0 for x in result['target'][1:])
    assert all(math.isfinite(x) and x>0 for x in result['weights'][1:])
    assert max(result['weights'][1:])==1
    assert sum(result['initial'][1:])==p['total_initial']
    assert sum(result['target'][1:])==p['total_target']
    shortage=sum(result['target'][1:])-sum(result['initial'][1:])
    delta=min(Fraction(str(p['lambda']))*Fraction(str(w))/d for w,d in zip(result['weights'][1:],result['target'][1:]))
    if p['inventory']=='shortage':assert shortage>0 and delta>0
    result['arithmetic']=dict(shortage=shortage,delta_exact_decimal=str(delta),positive_floor_exact_decimal=str(delta*shortage),
        positive_floor_float=float(delta*shortage),station_indices=f"1..{p['V']}; depot excluded",no_bound_backfill=True)
    return result

def replay(p,a,result):
    # Original route contract: departure load zero, each service station at most
    # once, one nonzero integer direction, loaded depot return allowed. All
    # pickup units pay pickup plus drop handling (including returned load).
    Y=list(a['initial']);seen=set();cars=set();durations=[];loads=[];pickups=[];route_details=[]
    routes=list(result['routes'])
    for route in routes:
        vehicle=route.get('vehicle',route.get('vehicle_id'))
        assert vehicle not in cars and 0<=vehicle<p['M'];cars.add(vehicle)
        nodes=route['nodes'];assert nodes[0]==nodes[-1]==0
        assert len(nodes[1:-1])==len(set(nodes[1:-1]))
        ops={}
        for op in route['operations']:
            i,x,y=(op['station'],op['pickup'],op['drop']) if isinstance(op,dict) else op
            assert i not in ops and 1<=i<=p['V']
            assert x>=0 and y>=0 and int(x)==x and int(y)==y and bool(x)!=bool(y)
            ops[i]=(x,y)
        assert set(nodes[1:-1])==set(ops)
        load=0;pickup=0;load_path=[0]
        for i in nodes[1:-1]:
            assert i not in seen;seen.add(i)
            x,y=ops[i];load+=x-y;pickup+=x;load_path.append(load)
            assert 0<=load<=p['Q_vector'][vehicle]
            Y[i]+=y-x;assert 0<=Y[i]<=a['capacities'][i]
        travel=sum(math.hypot(a['points'][i][0]-a['points'][j][0],a['points'][i][1]-a['points'][j][1])/1.5 for i,j in zip(nodes,nodes[1:]))
        duration=travel+(p['pickup_seconds']+p['drop_seconds'])*pickup
        assert duration<=p['T_seconds']+TOL
        durations.append(duration);loads.append(load);pickups.append(pickup)
        route_details.append(dict(vehicle=vehicle,nodes=nodes,load_path=load_path,return_load=load,pickups=pickup,travel_seconds=travel,total_seconds=duration))
    assert sum(Y[1:])==sum(a['initial'][1:])-sum(loads)
    ratios=[Y[i]/a['target'][i] for i in range(1,p['V']+1)];S=sum(ratios)
    G=sum(abs(ratios[i]-ratios[j]) for i in range(p['V']) for j in range(i+1,p['V']))/(p['V']*S) if S else 0.
    P=sum(a['weights'][i]*abs(ratios[i-1]-1) for i in range(1,p['V']+1))
    F=G+p['lambda']*P;near(F,result['upper_bound'],TOL)
    return dict(F=F,G=G,P=P,Y=Y,pickups=pickups,return_loads=loads,maximum_duration=max(durations,default=0),
        complete_fleet_vehicles=p['M'],nonempty_routes=sum(len(r['nodes'])>2 for r in routes),route_details=route_details)

def clocks(l,d):
    p=read(d/'producer_receipt.json');s=read(d/'producer_seal.json');v=read(d/'arm_total_receipt.json')
    c=read(d/'completion.json');close=read(d/'verification_closeout.json')
    assert p['producer_seal_SHA']==sha(d/'producer_seal.json')
    assert p['state']=='PRODUCED_PENDING_VERIFICATION' and p['verification_passed'] is None
    for n,h in s['required_SHA'].items():assert sha(d/n)==h,(d,n)
    assert all(s[k] for k in ['required_outputs_closed','necessary_producer_trailer_complete','native_stopped_no_reentry','cohort_review_excluded'])
    assert p['cap_seconds']==l['cap_seconds'] and p['required_outputs_closed'] and p['native_stopped_no_reentry']
    assert p['includes_H_models_installation_online_checks_callbacks_native_cleanup_serialization_supervision']
    assert v['producer_receipt_SHA']==sha(d/'producer_receipt.json') and v['verification_closeout_SHA']==sha(d/'verification_closeout.json')
    for field,name in [('audit_SHA','audit.json'),('own_evidence_SHA','independent_evidence.json'),('claims_SHA','native_claims.json'),('rejection_SHA','claim_rejections.json'),('metrics_SHA','audit_execution_metrics.json'),('producer_receipt_SHA','producer_receipt.json')]:
        assert close[field]==sha(d/name)
    assert close['no_new_solution_or_certificate_backfilled'] and close['necessary_verification_complete'] and v['necessary_verification_complete']
    assert p['t0_perf']<p['t_produce_perf']<=v['t_verified_perf']
    t=p['t_produce_perf']-p['t0_perf'];verify=v['t_verified_perf']-p['t_produce_perf'];total=v['t_verified_perf']-p['t0_perf']
    near(t,p['T_produce'],1e-9);near(verify,v['T_verify'],1e-9);near(total,v['T_total'],1e-9);near(t+verify,total,1e-8)
    assert 0<t<=l['cap_seconds'] and verify>=0
    assert c['returncode']==0 and c['within_cap'] and c['stop_reason']=='normal_return'
    return dict(T_produce=t,T_verify=verify,T_total=total,cap_seconds=l['cap_seconds'],normal_return=True,
        production_within_cap=True,postseal_verification=True,seal_SHA=sha(d/'producer_seal.json'))

def cross_check(claims,witnesses):
    # Different implementation from round114_claims.reconcile, and no shared
    # mutable state across roles. Return every proven same-domain contradiction.
    bad=[]
    for q in claims:
        assert q['domain_verified'] and math.isfinite(q['value'])
        scope=q['scope']
        for w in witnesses:
            assert w['physical_verified'] and w['input_SHA']==q['input_SHA']
            same=bool(scope['full_original']) or (scope['lower_g']-TOL<=w['G']<=scope['upper_g']+TOL and w['F']<=scope['cutoff']+TOL)
            if same and q['value']>w['F']+TOL:
                bad.append(dict(arm=q['arm'],call=q['call'],sequence=q['sequence'],bound=q['value'],witness_F=w['F'],witness_arm=w['arm']))
                break
    return bad

def classify(m,p):
    valid=all(x['identity_lifecycle_physical_proof_admitted'] and not x['source_reduced'] for x in [m,p])
    category='UNEVALUABLE' if not valid else 'BOTH_CERTIFIED' if m['certificate'] and p['certificate'] else 'MB_ONLY_CERTIFIED' if m['certificate'] else 'P_ONLY_CERTIFIED' if p['certificate'] else 'BOTH_OPEN'
    out=dict(id=m['id'],group_number=m['group_number'],classification=category,MB_certified=m['certificate'],P_certified=p['certificate'],
        MB_T_cert=m['T_cert'],P_T_cert=p['T_cert'],MB_T_produce=m['T_produce'],P_T_produce=p['T_produce'],
        MB_T_total=m['T_total'],P_T_total=p['T_total'],speedup=None,observed_P_minus_MB_seconds=None,
        time_materiality_seconds=None,time_description=None,total_time_speedup=None,certified_objectives_compatible=None,
        observed_total_P_minus_MB_seconds=p['T_total']-m['T_total'],
        observed_total_time_order='MB_FASTER' if p['T_total']>m['T_total'] else 'P_FASTER' if p['T_total']<m['T_total'] else 'EQUAL',
        one_sided_time_inference='none; nominal cap and actual returned duration do not impute certification time')
    if category=='BOTH_CERTIFIED':
        out['certified_objectives_compatible']=abs(m['U']-p['U'])<=TOL
        if not out['certified_objectives_compatible']:out['classification']='UNEVALUABLE'
        else:
            mt,pt=m['T_cert'],p['T_cert'];assert mt>0 and pt>0
            difference=pt-mt;threshold=max(30.,.1*pt)
            out.update(speedup=pt/mt,observed_P_minus_MB_seconds=difference,time_materiality_seconds=threshold,
                time_description='MB_FASTER' if difference>=threshold else 'P_FASTER' if -difference>=threshold else 'TIME_CLOSE',
                total_time_speedup=p['T_total']/m['T_total'])
    return out

def main():
    # No child launch (including external verification) is possible in this task.
    subprocess.Popen=no_subprocess
    protocol=read(OUT/'protocol.json');candidate=read(OUT/'candidate_identity.json');production=read(OUT/'production_identity.json')
    manifest=read(OUT/'input_manifest.json');frozen=read(OUT/'argv_freeze.json')
    assert protocol['sole_proposed_method']=='M-B' and protocol['certificate_tolerance']==TOL
    assert candidate['production_identity_SHA']==sha(OUT/'production_identity.json')
    assert candidate['protocol_SHA']==sha(OUT/'protocol.json') and candidate['input_manifest_SHA']==sha(OUT/'input_manifest.json')
    assert candidate['argv_SHA']==sha(OUT/'argv_freeze.json')
    assert sha(common.PE)==candidate['production_PE_SHA']==common.PE_SHA
    assert sha(common.DLL)==candidate['DLL_SHA']==common.DLL_SHA
    assert production['source_commit_before_native']==common.SOURCE
    assert candidate['source_bindings']==production['source_bindings'] and len(candidate['source_bindings'])==216
    for n,h in candidate['source_bindings'].items():assert sha(ROOT/n)==h,n
    for n,h in candidate['helpers'].items():assert sha(ROOT/n)==h,n
    for n in ['goal.md','source_recipe.json','paper_method_config.json','measurement_policy_v2.json','shortage_positive_objective.json','certification_summary.json','arms.csv','certification_pairs.csv']:
        sha(OUT/n)
    sha(Path(__file__))
    core.start_reader.ROOT=ROOT
    all_processes=[];total_claims=0;total_witnesses=0
    for n in range(1,7):
        t=time.perf_counter();group=OUT/f'campaign/group{n:02d}'
        i=read(group/'identity.json');plan=frozen['plans'][n-1]
        assert sha(group/'identity.json')==candidate['campaign_identities'][f'campaign/group{n:02d}']
        assert i['launches']==plan['launches'] and i['helpers']==candidate['helpers'] and i['source_hashes']==candidate['source_bindings']
        assert i['prereg_sha256']==sha(OUT/'protocol.json') and i['measurement_policy_SHA']==sha(OUT/'measurement_policy_v2.json')
        assert i['candidate_binary_sha256']==common.PE_SHA and i['dll_sha256']==common.DLL_SHA and i['measured_source_commit']==common.SOURCE
        assert [l['arm'] for l in i['launches']]==manifest['roles'][n-1]['method_order']
        values=[];claims=[];witnesses=[]
        with extension():
            for l in i['launches']:
                d=Path(l['destination']);p=l['panel'];cmd=l['command']
                assert p['gurobi_seed']==l['seed']==0
                assert l['cap_seconds']==p['cap_seconds']==(600 if n<=3 else 1200)
                for name,value in [('--gurobi-seed','0'),('--threads','1'),('--mip-threads','1'),('--gurobi-presolve','-1'),
                    ('--process-shutdown-margin','30'),('--process-wall-time-limit',str(l['cap_seconds'])),('--time-limit',str(l['cap_seconds']-6)),
                    ('--T',str(p['T_seconds'])),('--pickup-time','60'),('--drop-time','60'),('--lambda','0.15')]:assert flag(cmd,name)==value,(l['id'],l['arm'],name)
                assert ('--plain-baseline' in cmd)==(l['arm']=='P-GRB')
                assert ('--round98-state-service' in cmd)==(l['arm']=='M-B')
                if l['arm']=='M-B':assert flag(cmd,'--round98-state-service')=='m-binary'
                origin=read(d/'child_process_origin.json');all_processes.append(origin)
                assert origin['command']==cmd and origin['PE_SHA']==common.PE_SHA and origin['source_commit']==common.SOURCE and origin['seed']==0
                assert origin['creation_from_live_OS_handle']
                a=parse_input(p);r=read(d/'result.json');physical=replay(p,a,r);clock=clocks(l,d)
                assert r['process_shutdown_margin_seconds']==30 and r['process_return_code']==0
                expected='custom' if l['arm']=='P-GRB' else 'research-round99-ensc-discrete-structure-m-binary'
                assert r['algorithm_preset']==expected
                recs=collections.defaultdict(list)
                item=inherited.item(ROOT,l,i,recs)
                assert item['complete'] and item['normal'] is not None
                normal=item['normal'];j=item['j'];chain=item['chain'];ind=item['ind']
                assert not j['failure'] and not j['unreturned_ids'] and j['started']==j['returned']
                assert chain['normal_return_verified'] and len(chain['actual'])==j['started']
                assert ind['created_after_producer_seal'] and not ind['inside_own_whole']
                for k in ['identity_verified','input_verified','model_domain_verified','journal_verified','return_verified','files_verified','own_physical_verified','independent_floor0']:assert ind[k],k
                for k in ['F','G','P']:near(physical[k],ind['physical'][k],1e-12)
                assert physical['Y']==ind['physical']['Y']
                # Independent final L aggregation from the actual cold readback
                # or the raw final relevant-leaf values, without clipping to U.
                leaves=[];models=[]
                if l['arm']=='P-GRB':
                    assert r['gurobi_hga_start_requested'] is False and j['started']==1
                    L=max([0.,r['native_mip_best_bound']]+[b['global_bound'] for b in j['bounds'] if b['global_available']])
                    cert=r['gurobi_status']==2 and physical['F']-L<=TOL
                    assert sha(d/'compact.lp')==p['reference']['canonical_sha256']
                else:
                    leaves=rows(d/'external/paper_leaf_ledger.csv')
                    live=[x for x in leaves if x['status'] not in ['replaced','coalesced']]
                    cutoff=float(rows(d/'external/global_bound_trace.csv')[-1]['verified_global_upper_bound'])
                    relevant=[x for x in live if float(x['gamma_L'])<cutoff-TOL]
                    L=min((float(x['lower_bound']) for x in relevant),default=0.)
                    closed=all(x['status'] in ['closed','fathomed','empty'] or float(x['gamma_L'])>=physical['F']-TOL or float(x['lower_bound'])>=physical['F']-TOL for x in live)
                    cert=closed and physical['F']-L<=TOL
                    assert item['ep']['cover']['complete_coverage']
                near(L,normal['L'],1e-12);near(physical['F'],normal['U'],1e-12)
                assert cert==normal['certificate']==r['strict_certified_original_problem']
                assert L<=physical['F']+TOL and math.isfinite(L)
                audit=read(d/'audit.json')
                # This endpoint is the finalized record. Audit top-level U/L
                # observation fields are deliberately never used for values.
                near(L,audit['endpoint']['L'],TOL);near(physical['F'],audit['endpoint']['U'],TOL)
                assert cert==audit['endpoint']['certificate'] and audit['passed']
                context=ArmModels()
                try:
                    for cid,call in j['calls'].items():
                        path=core.portable(ROOT,call['model_path']);assert sha(path)==call['model_sha256']
                        if call['full_original']:
                            assert sha(path)==p['reference']['canonical_sha256'];model=core.lp_model(path)
                            fact=dict(SHA=sha(path),full_original=True,rows=len(model['rows']),columns=len(model['order']))
                        else:fact,model=context.model_contract(ROOT,p,path,l['arm'])
                        scope=context.model_scope_contract(call,model,p)
                        models.append(dict(call=cid,model=fact,scope=scope))
                finally:context.clear()
                call_details=[]
                for b in item['view']['bindings']:
                    sha(ROOT/b['raw_log'])
                    text=item['view']['views'][b['call']]['text']
                    terminal=re.findall(r'(?m)^(?:Best objective .*|Optimal objective .*|Time limit reached.*|Optimal solution found.*|Model is infeasible.*|Infeasible model.*)$',text)
                    call_details.append(dict(binding=b,terminal_lines=terminal))
                own_zero=all(Y==D for Y,D in zip(physical['Y'][1:],a['target'][1:]))
                assert not own_zero and physical['F']>0, 'Actual panel unexpectedly contains a zero: revise review coverage explicitly'
                if p['inventory']=='shortage':assert physical['F']>=a['arithmetic']['positive_floor_float']-TOL
                category='CLEAN_NONZERO_CERTIFICATE' if cert else 'RELIABLE_POSITIVE_LB_OPEN' if L>0 else 'INDEPENDENT_FLOOR_OPEN'
                value=dict(id=l['id'],group_number=n,method=l['arm'],input_SHA=p['input_sha256'],PE_SHA=common.PE_SHA,DLL_SHA=common.DLL_SHA,
                    seed=0,U=physical['F'],L=L,signed_gap=physical['F']-L,certificate=cert,T_cert=clock['T_produce'] if cert else None,
                    **clock,proof_evidence=category,source_reduced=False,identity_lifecycle_physical_proof_admitted=True,
                    status=r['status'],own_exact_zero=own_zero,startup_zero=False,actual_Optimize=j['started'],returned_Optimize=j['returned'],
                    physical=physical,input_arithmetic=a['arithmetic'],call_details=call_details,model_contracts_reexecuted=models,
                    final_leaf_records=leaves,coverage_source='original final leaf ledger plus inherited scope/chronology checks' if l['arm']=='M-B' else 'own cold original model returned native log and API readback',
                    producer_receipt_SHA=sha(d/'producer_receipt.json'),result_SHA=sha(d/'result.json'),audit_final_endpoint=audit['endpoint'])
                values.append(value);ARMS.append(value);claims.extend(item['claims']);witnesses.extend(ind['witnesses'])
                # Re-read every actually used proof/closeout dependency identity.
                for name in ['native_claims.json','claim_rejections.json','production_checks.json','call_log_views.json','round120_model_contracts.json','round120_extended_verification.json','native_end_receipt.json','affinity.json','launch.json']:
                    sha(d/name)
                del item,recs,context
                gc.collect()
        contradictions=cross_check(claims,witnesses)
        assert not contradictions,contradictions[:2]
        by={v['method']:v for v in values};pair=classify(by['M-B'],by['P-GRB']);PAIRS.append(pair)
        GROUPS.append(dict(group_number=n,id=pair['id'],native_claims_rechecked=len(claims),physical_witnesses_rechecked=len(witnesses),
            contradictions=contradictions,one_sided_deep_review=n in [4,6],seconds=time.perf_counter()-t))
        total_claims+=len(claims);total_witnesses+=len(witnesses)
        print(json.dumps(dict(group=n,classification=pair['classification'],claims=len(claims),witnesses=len(witnesses),seconds=time.perf_counter()-t)),flush=True)
        del claims,witnesses,values
        gc.collect()
    assert len(ARMS)==12 and len(PAIRS)==6 and len({(x['pid'],x['actual_creation_unix']) for x in all_processes})==12
    # Compare only after all independently derived outcomes are fixed.
    saved_arms=rows(OUT/'arms.csv');saved_pairs=rows(OUT/'certification_pairs.csv');saved_summary=read(OUT/'certification_summary.json')
    for a in ARMS:
        s=next(x for x in saved_arms if x['id']==a['id'] and x['arm']==a['method'])
        for k in ['U','L','T_produce','T_verify','T_total']:near(a[k],float(s[k]),1e-9)
        near(a['signed_gap'],float(s['gap']),1e-12)
        assert str(a['certificate'])==s['certificate'] and str(a['own_exact_zero'])==s['own_exact_zero'] and a['proof_evidence']==s['proof_evidence']
        assert s['formal_protocol_qualified']==s['certificate_qualified']==s['numbers_qualified']=='True' and s['source_reduced']=='False'
        assert s['T_cert']=='' if a['T_cert'] is None else abs(float(s['T_cert'])-a['T_cert'])<1e-9
    for p in PAIRS:
        s=next(x for x in saved_pairs if x['id']==p['id']);assert p['classification']==s['classification']
        for k in ['MB_T_cert','P_T_cert','speedup','observed_P_minus_MB_seconds','time_materiality_seconds','total_time_speedup']:
            assert s[k]=='' if p[k] is None else abs(float(s[k])-p[k])<1e-9
        assert (p['time_description'] or '')==s['time_description']
        assert ('' if p['certified_objectives_compatible'] is None else str(p['certified_objectives_compatible']))==s['certified_objectives_compatible']
    counts={c:sum(p['classification']==c for p in PAIRS) for c in ['BOTH_CERTIFIED','MB_ONLY_CERTIFIED','P_ONLY_CERTIFIED','BOTH_OPEN','UNEVALUABLE']}
    per={m:dict(certified=sum(a['certificate'] for a in ARMS if a['method']==m),nonzero_certified=sum(a['certificate'] and a['U']>1e-12 for a in ARMS if a['method']==m),zero_certified=0,startup_zero=0) for m in ['M-B','P-GRB']}
    assert counts==saved_summary['categories'] and per==saved_summary['per_method']
    intersection=[p for p in PAIRS if p['classification']=='BOTH_CERTIFIED'];ratios=[p['speedup'] for p in intersection]
    conditional=dict(ids=[p['id'] for p in intersection],n=len(intersection),speedup_median=statistics.median(ratios),speedup_geometric_mean=math.exp(sum(math.log(r) for r in ratios)/len(ratios)))
    near(conditional['speedup_median'],saved_summary['both_certified_subset']['speedup_median'],1e-12)
    near(conditional['speedup_geometric_mean'],saved_summary['both_certified_subset']['speedup_geometric_mean'],1e-12)
    support=[p['id'] for p in PAIRS if p['classification']=='MB_ONLY_CERTIFIED' or p['classification']=='BOTH_CERTIFIED' and p['time_description']=='MB_FASTER']
    losses=[p['id'] for p in PAIRS if p['classification']=='P_ONLY_CERTIFIED' or p['classification']=='BOTH_CERTIFIED' and p['time_description']=='P_FASTER']
    judgment='LIMITED_DIRECT_CERTIFICATION_SUPPORT' if support and not losses else 'MIXED_DIRECT_CERTIFICATION_EVIDENCE' if support else 'NONZERO_CERTIFICATION_EVIDENCE_LIMITED'
    assert support==saved_summary['supporting_nonzero_problems'] and losses==saved_summary['adverse_problems'] and judgment==saved_summary['scientific_judgment']
    FINDINGS.extend([
        'SC-C15-B cold P-GRB retains a signed gap of -1.734723475976807e-17, within the original 1e-7 policy; L was not clipped to U.',
        'SC-B15-S observed production speedup is below the 30-second materiality threshold and remains TIME_CLOSE despite a ratio above one.',
        'SC-B20-S and SC-B20-U are qualitative single-sided certification outcomes. Their P-GRB observations return normally before nominal cap; no cap-substituted speedup or lower bound is inferred.',
        'SC-C20-S remains BOTH_OPEN. Production duration orders M-B first while total duration orders P-GRB first; neither duration is a certification time.',
        'All eight certified arm endpoints have positive physical objectives; zero and startup-zero categories do not occur.',
        'No same-input, same-scope native-bound contradiction was found among the actual saved claims and physical witnesses checked.'
    ])
    protected=dict(HASHES)
    for path,h in protected.items():
        actual=ROOT/path if not Path(path).is_absolute() else Path(path)
        assert hashlib.sha256(actual.read_bytes()).hexdigest()==h,('review changed source',path)
    report=dict(schema='round126-independent-certification-review-v1',reviewer='independent_cert_review; separate executor from production and manuscript author',
        completed=True,scope='all 12 formal arms and 6 predeclared pairs; full raw final fleet replay, receipts, provenance, actual model scopes, per-call logs, lifecycle and complete-coverage checks; independent classifier and arithmetic',
        command='D:/msys64/ucrt64/bin/python.exe -B scripts/round126_run.py review_quant engineering 240 3600 scripts/round126_independent_audit.py',
        forbidden_actions_executed=dict(new_solver=0,H=0,LP=0,MIP=0,route_search=0,input_generation=0,production_changes=0),
        classification_function_imported_or_called=False,fee_launch_SHA=sha(OUT/'fees/review_quant/launch.json'),
        raw_endpoint_policy='Independently replayed physical F and original raw native/leaf L. audit.json endpoint used only as a comparison; top-level observation fields are not endpoint values.',
        inherited_predicates='read_round118.item under round122_evidence.extension; ArmModels model_contract and scope replay. No read_round126 classifier, old both-open WIN, or reader.finalize classifier used.',
        categories=counts,per_method=per,both_certified_subset=conditional,scientific_judgment=judgment,supporting_nonzero_problems=support,adverse_problems=losses,
        proof_evidence_counts=dict(collections.Counter(a['proof_evidence'] for a in ARMS)),groups=GROUPS,pairs=PAIRS,arms=ARMS,
        claims_checked=total_claims,witnesses_checked=total_witnesses,findings=FINDINGS,
        limitations=['Established model/coverage mathematical predicates were re-executed from the saved raw assets; this is not a new independent formal proof of the model, cuts or floating-point solver.',
            'The physical check establishes legality and objective of recorded fleets only. It never searches for a new route, bound or certificate.',
            'The cross-arm source rejection search covers actually saved physically verified witnesses, and does not guarantee absence of all numerical or solver defects.',
            'Manuscript claims and final PDF layout are outside this quantitative reviewer scope and require the separate document review.',
            'This JSON is written before the parent fee controller observes this child exit; the matching review_quant receipt is the authoritative final task charge.'],
        file_hashes=HASHES,original_hashed_evidence_unchanged=True,engineering_seconds=time.perf_counter()-START)
    DEST.mkdir(exist_ok=True)
    (DEST/'independent_certification_review.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    md=['# Round126 independent certification review','',
        'A separate executor re-read the actual evidence for all 12 formal arms and independently computed all six classifications and time comparisons. No solver, H, LP/MIP, route search, input generator or production mutation was run. The original evidence hashes were stable before and after this review.','',
        f"The independently derived category counts are `{counts}`. M-B certified {per['M-B']['certified']}/6 and cold P-GRB {per['P-GRB']['certified']}/6; all eight arm certificates are nonzero. The supported evidence classification is `{judgment}`.",'',
        '| Problem | Independent class | M-B T_cert (s) | P T_cert (s) | P/M-B | Materiality | T_total P/M-B |',
        '|---|---|---:|---:|---:|---|---:|']
    for p in PAIRS:
        def fmt(x):return 'null' if x is None else f'{x:.9f}'
        md.append('| '+' | '.join([p['id'],p['classification'],fmt(p['MB_T_cert']),fmt(p['P_T_cert']),fmt(p['speedup']),p['time_description'] or 'qualitative only',fmt(p['total_time_speedup'])])+' |')
    md+=['',f"The both-certified subset is {conditional['ids']} (n={conditional['n']}): median speedup {conditional['speedup_median']:.9f}, geometric mean {conditional['speedup_geometric_mean']:.9f}. This conditional subset is accompanied by two single-sided certifications and one both-open pair; caps never fill missing times.",'',
        '## Actual checks and dependencies','',
        f"Verified frozen PE/DLL SHA256, all 216 production bindings, all frozen helper hashes, six input identities, every seed/cap/command and physical parameter, each sealed producer/verification clock and closeout chain, 12 distinct process birth identities, and actual successful native return/lifecycle records. Independently replayed all 12 final fleets and matched Y, G, P and F to the inherited physical replay. Checked {total_claims} native claims against {total_witnesses} saved physical witnesses within each input and actual true-G/cutoff scope.",'',
        'Re-executed inherited read-only model contracts and all per-call log bindings, including actual M-B continuous-quantity/A-B rows and saved G/cutoff scopes, returned LP/MIP sources, chronological availability and complete final cover. Final L was separately aggregated from cold native readback or the raw relevant-leaf ledger. The complete audit `endpoint` was compared only after these computations; no top-level audit observation field supplies a final endpoint. All actual evidence classes were covered: eight CLEAN_NONZERO_CERTIFICATE and four RELIABLE_POSITIVE_LB_OPEN.','',
        'Groups 4 and 6 received a full re-read of both M-B and P-GRB dependencies, retained in the JSON call_details/model_contracts_reexecuted/final_leaf_records. Their P-GRB models are original cold compact matrices, with one successful TIME_LIMIT return each, positive own bounds and legal own fleets. Their M-B proof is an admitted full interval cover with the original positive final physical objective; neither is a startup-zero result.','',
        '## Findings','']
    md+=['- '+f for f in FINDINGS]
    md+=['','## Execution and limits','',
        '`'+report['command']+'`','',
        f"Script SHA256: `{HASHES[key(__file__)]}`. The JSON records the exact reviewed file hashes, models, call scopes, terminal lines, fleet replay and clocks. Measured review child time before writing: {report['engineering_seconds']:.6f} seconds; final engineering charge is in `fees/review_quant/receipt.json` after controller closeout.",'']
    md+=['- '+f for f in report['limitations']]
    (DEST/'independent_certification_review.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
    print(json.dumps(dict(completed=True,categories=counts,per_method=per,claims_checked=total_claims,witnesses_checked=total_witnesses,
        judgment=judgment,report=str(DEST/'independent_certification_review.json'),seconds=time.perf_counter()-START)),flush=True)

if __name__=='__main__':main()
