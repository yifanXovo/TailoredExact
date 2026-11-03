"""Bounded independent Round150 science checks, no solver import or execution."""
from pathlib import Path
import ast,collections,csv,datetime,gzip,hashlib,json,math,re,time
from independent_mps import read_mps

ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'results/unified_exact_round150'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def close(a,b,tol=1e-10):assert abs(a-b)<=tol,(a,b,abs(a-b))
def physical(data,routes,T,lambda_value=.15):
    n=len(data['target'])-1;Y=list(data['initial']);visited=set();vehicle_ids=set();durations=[]
    for route in routes:
        vehicle=route['vehicle'];assert vehicle not in vehicle_ids;vehicle_ids.add(vehicle)
        Q=data['Q'][vehicle];nodes=route['nodes'];assert nodes[0]==nodes[-1]==0
        assert all(1<=i<=n for i in nodes[1:-1])
        assert len(set(nodes[1:-1]))==len(nodes[1:-1]) and not visited.intersection(nodes[1:-1])
        visited.update(nodes[1:-1]);ops={o['station']:o for o in route['operations']}
        assert len(ops)==len(route['operations']) and set(ops)<=set(nodes[1:-1])
        load=0;handling=0
        for i in nodes[1:-1]:
            op=ops.get(i,dict(pickup=0,drop=0));p,d=op['pickup'],op['drop']
            assert int(p)==p and int(d)==d and p>=0 and d>=0
            load+=p-d;assert 0<=load<=Q
            Y[i]=Y[i]-p+d;assert 0<=Y[i]<=data['capacities'][i]
            handling+=60*(p+d)
        # Trucks start empty; residual return load is unloaded at the depot
        # and pays the same drop handling time in the original physical model.
        handling+=60*load
        travel=math.fsum(math.dist(data['points'][i],data['points'][j])/1.5 for i,j in zip(nodes,nodes[1:]))
        duration=travel+handling;assert duration<=T+1e-6,(duration,T)
        durations.append(duration)
    assert vehicle_ids==set(range(len(data['Q'])))
    ratios=[Y[i]/data['target'][i] for i in range(1,n+1)];S=math.fsum(ratios)
    G=math.fsum(abs(a-b) for i,a in enumerate(ratios) for b in ratios[i+1:])/(n*S) if S else 0.
    P=math.fsum(data['weights'][i]*abs(ratios[i-1]-1) for i in range(1,n+1))
    return dict(U=G+lambda_value*P,G=G,P=P,Y=Y,durations=durations)

def input_data(path):
    lines=Path(path).read_text(encoding='utf-8').splitlines();data={}
    data['Q']=ast.literal_eval(re.match(r'^\s*\d+\s+\d+\s+(\[.*\])',lines[0]).group(1))
    for line in lines[1:]:
        if '=' in line:
            key,value=line.split('=',1);data[key.strip()]=ast.literal_eval(value.strip())
    return data

def lp_check(role):
    folder=OUT/'LP'/f'{role}_CPF';result=read(folder/'result.json')
    assert result['qualified'] and result['Status']==2 and result['LP_Optimize']==1
    assert result['baseline_Optimize_new']==0 and not result['exact_rational_optimality_certificate']
    assert sha(folder/'model.mps')==result['model_SHA']
    assert sha(folder/'solution.json.gz')==result['solution_SHA'] and sha(folder/'dual.json.gz')==result['dual_SHA']
    model=read_mps(folder/'model.mps');point=json.loads(gzip.decompress((folder/'solution.json.gz').read_bytes()))
    dual=json.loads(gzip.decompress((folder/'dual.json.gz').read_bytes()));Pi,RC=dual['Pi'],dual['RC']
    objective=next(k for k,v in model['rows'].items() if v=='N');conrows={k:v for k,v in model['rows'].items() if v!='N'}
    assert set(point)==set(model['columns'])==set(RC) and set(Pi)==set(conrows)
    rowparts=collections.defaultdict(list);bounds={};stationarity=[]
    bound_vio=[];dual_bound_terms=[];infinite_adverse=[]
    for v,terms in model['columns'].items():
        for row,value in terms.items():rowparts[row].append(value*point[v])
        lo,hi=0.,math.inf
        for kind,value in model['bounds'].get(v,[]):
            if kind=='LO':lo=value
            elif kind=='UP':hi=value
            elif kind=='FX':lo=hi=value
            elif kind=='FR':lo,hi=-math.inf,math.inf
            elif kind=='MI':lo=-math.inf
            elif kind=='PL':hi=math.inf
            else:raise AssertionError((v,kind))
        bounds[v]=(lo,hi);bound_vio.append(max(lo-point[v],point[v]-hi,0.))
        favorable=lo if RC[v]>=0 else hi
        if math.isfinite(favorable):dual_bound_terms.append(RC[v]*favorable)
        else:infinite_adverse.append(abs(RC[v]))
        stationarity.append(abs(terms.get(objective,0.)-math.fsum(value*Pi[row] for row,value in terms.items() if row!=objective)-RC[v]))
    row_vio=[];dual_sign=[];complementarity=[]
    for row,kind in conrows.items():
        activity=math.fsum(rowparts[row]);rhs=model['rhs'].get(row,0.)
        row_vio.append(max(activity-rhs,0.) if kind=='L' else max(rhs-activity,0.) if kind=='G' else abs(activity-rhs))
        dual_sign.append(max(Pi[row],0.) if kind=='L' else max(-Pi[row],0.) if kind=='G' else 0.)
        complementarity.append(abs(Pi[row]*(activity-rhs)))
    primal=math.fsum(rowparts[objective]);dual_value=math.fsum(Pi[row]*model['rhs'].get(row,0.) for row in conrows)+math.fsum(dual_bound_terms)
    close(primal,result['L'],1e-12);close(dual_value,result['numerical_dual_objective'],1e-12)
    assert max(row_vio)<=1e-6 and max(bound_vio)<=1e-6
    assert max(stationarity)<=1e-12 and max(dual_sign)<=1e-12 and max(infinite_adverse or [0.])==0.
    assert result['CPF_minus_PF']>0 and result['numerical_dual_objective']>result['old_PF_L']
    return dict(role=role,numerical_primal=primal,numerical_dual=dual_value,
        CPF_minus_PF=result['CPF_minus_PF'],row_residual=max(row_vio),bound_violation=max(bound_vio),
        stationarity_residual=max(stationarity),dual_sign_violation=max(dual_sign),
        complementarity_row_residual=max(complementarity),infinite_bound_adverse_RC=0.,
        model_SHA=result['model_SHA'],solution_SHA=result['solution_SHA'],dual_SHA=result['dual_SHA'])

def run():
    tick=time.perf_counter();full=read(OUT/'reports/full.json');matrix=read(OUT/'confirmation_matrix.json')
    assert sha(OUT/'confirmation_matrix.json')==read(OUT/'review/confirmation_admission.json')['matrix_SHA']
    assert sha(OUT/'CPF_frozen.json')==read(OUT/'review/CPF_admission.json')['CPF_frozen_SHA']
    arms=full['formal_arms'];assert len(arms)==len(matrix['groups'])==4 and not full['pending']
    assert full['complete_Native_Optimize']==full['complete_Native_returned']==19
    assert full['diagnostic_LP_Optimize']==full['diagnostic_LP_returned']==3
    assert full['repeated_baseline_Optimize']==full['extra_quality_Optimize']==0
    assert not full['optional_clarification_entered'] and not full['CPF_full_entered']
    trajectories=list(csv.DictReader((OUT/'reports/verified_U_trajectories.csv').open(encoding='utf-8',newline='')))
    armfacts=[];counted_calls=0
    for arm,g in zip(arms,matrix['groups']):
        launch=g['launch'];d=Path(arm['destination']);assert str(d)==launch['destination']
        assert arm['role']==launch['id'] and arm['method']==launch['R150_method']
        seal=read(d/'producer_seal.json');producer=read(d/'producer_receipt.json');closeout=read(d/'verification_closeout.json');audit=read(d/'audit.json')
        assert sha(d/'producer_seal.json')==producer['producer_seal_SHA']
        assert all(seal[k] for k in ['required_outputs_closed','necessary_producer_trailer_complete','native_stopped_no_reentry'])
        for name,digest in seal['required_SHA'].items():assert sha(d/name)==digest,name
        binding={'audit_SHA':'audit.json','own_evidence_SHA':'independent_evidence.json','claims_SHA':'native_claims.json',
            'rejection_SHA':'claim_rejections.json','producer_receipt_SHA':'producer_receipt.json'}
        for key,name in binding.items():assert sha(d/name)==closeout[key],name
        assert all(closeout[k] for k in ['necessary_verification_complete','implementation_qualified','evidence_complete','native_proof_qualified','performance_eligible'])
        assert audit['passed'] and audit['raw_bytes_unchanged'] and audit['raw_tree_lifecycle_complete']
        assert not audit['source_rejections'] and audit['full_H']['complete']
        endpoint=audit['endpoint'];close(arm['U'],endpoint['U']);close(arm['L'],endpoint['L'])
        assert arm['certificate']==endpoint['certificate']
        close(arm['T_produce'],producer['T_produce']);close(arm['T_produce']+arm['T_verify'],arm['T_total'])
        assert arm['T_cert']==(arm['T_produce'] if arm['certificate'] else None)
        close(arm['signed_gap'],arm['U']-arm['L']);close(arm['relative_gap'],arm['signed_gap']/arm['U'])
        assert arm['known'] and arm['exposed'] and not arm['used_in_GD_selection']
        assert arm['H_complete'] and not any(arm[k] for k in ['PF','Shared_S','STOCK','AP','stock_rows','new_columns','paid_source_solves'])
        input_path=ROOT/launch['panel']['input_path'];assert sha(input_path)==arm['input_SHA']
        data=input_data(input_path);raw=read(d/'result.json');value=physical(data,raw['routes'],arm['physical_T'])
        assert value['Y']==raw['final_inventories'];close(value['U'],arm['U']);close(value['G'],arm['physical_G']);close(value['P'],arm['physical_P'])
        obs=read(d/'observations.json');calls={r['payload']['call']:r for r in obs if r['payload']['kind']=='call'}
        returns=[r for r in obs if r['payload']['kind']=='returned'];assert len(calls)==len(returns)==arm['declared_calls']==arm['returned_calls']
        assert set(calls)==set(r['payload']['call'] for r in returns)
        assert len(set(r['payload']['call'] for r in returns))==len(returns)
        for ret in returns:assert ret['payload']['return_code']==0 and ret['sequence']>calls[ret['payload']['call']]['sequence']
        for call in calls.values():
            payload=call['payload'];assert sha(payload['model_path'])==payload['model_sha256']
            assert payload['settings']['Seed']==0 and payload['settings']['Threads']==1
        control=read(d/'round147_control_audit.json');pf=read(d/'round149_control_audit.json')
        assert control['PASS'] and not control['STOCK'] and control['GD']==arm['GD']
        assert pf['PASS'] and not pf['enabled'] and not pf['models'] and not pf['Native_audits']
        assert all(m['GD_rows']==arm['GD_rows'] and m['GD_nonzeros']==arm['GD_nonzeros'] for m in control['models'])
        assert control['models'] and len(control['models'])==len(calls)
        if arm['GD']:
            assert all(a['PASS'] and a['GD_rows']==arm['GD_rows'] for a in control['Native_audits'])
            assert {a['model_SHA'] for a in control['Native_audits']}=={r['payload']['model_sha256'] for r in calls.values()}
        obs_by={r['sequence']:r for r in obs};rows=[r for r in trajectories if r['role']==arm['role'] and r['method']==arm['method']]
        assert rows;last=math.inf
        for row in rows:
            event=obs_by[int(row['sequence'])];payload=event['payload']
            assert payload['kind']=='witness' and event['sha256']==row['committed_event_SHA']
            assert sha(d/'observations.json')==row['raw_observation_SHA']
            close(float(row['producer_seconds']),event['effective_available_seconds'])
            close(float(row['U']),payload['objective'])
            recomputed=physical(data,payload['routes'],arm['physical_T'])
            close(recomputed['U'],float(row['U']),1e-8)
            assert float(row['U'])<=last+1e-10;last=float(row['U'])
        close(last,arm['U']);first=min(float(r['producer_seconds']) for r in rows if abs(float(r['U'])-arm['U'])<=1e-10)
        close(first,arm['first_final_U_seconds'])
        counted_calls+=len(calls)
        armfacts.append(dict(role=arm['role'],method=arm['method'],U=value['U'],L=arm['L'],certificate=arm['certificate'],
            T_cert=arm['T_cert'],T_total=arm['T_total'],returned_calls=len(returns),
            independently_verified_trajectory_points=len(rows),first_final_U_seconds=first,
            fleet_durations=value['durations'],producer_seal_bound=True,closeout_hashes_bound=True,
            all_call_model_SHAs_bound=True,GD_rows=arm['GD_rows'],GD_nonzeros=arm['GD_nonzeros']))
    assert counted_calls==19
    for i in [0,2]:assert arms[i]['H_semantic_SHA']==arms[i+1]['H_semantic_SHA'] and arms[i]['H_fleet_SHA']==arms[i+1]['H_fleet_SHA']
    comparisons=full['comparisons']
    for comparison in comparisons:
        role=comparison['role'];b,d=[a for a in arms if a['role']==role]
        du=d['U']-b['U'];dg=d['signed_gap']-b['signed_gap']
        severe=not b['certificate'] and not d['certificate'] and du>max(.001,.05*b['U']) and dg>max(.005,.25*b['signed_gap'])
        assert severe==comparison['serious_double_open_regression']==False
        close(comparison['delta_U'],du);close(comparison['delta_signed_gap'],dg)
        if b['certificate'] and d['certificate']:close(comparison['certificate_speedup_percent'],100*(1-d['T_cert']/b['T_cert']))
        else:assert comparison['certificate_speedup_percent'] is None
    lp=[lp_check(role) for role in ['K-20-S','K-35-U','R-X20-S-T1']]
    fees=[read(p) for p in (OUT/'fees').glob('*/receipt.json')]
    external=read(OUT/'infra/external_costs.json')['processes'];cost=read(OUT/'cost_report.json')
    actual_cost=math.fsum(f['G1_seconds'] for f in fees)+math.fsum(p['outer_seconds'] for p in external)
    close(actual_cost,cost['charged_new_experiment_seconds'],1e-7)
    assert actual_cost<14400 and not cost['experiment']['unclosed'] and cost['build_seconds']==0
    assert all(f['exit_code']==0 and not f['timeout'] and f['exit_observed'] for f in fees)
    start=read(OUT/'start_receipt.json');candidate=read(OUT/'candidate_manifest.json')
    for name,digest in start['protected_entry_bytes'].items():assert sha(ROOT/name)==digest
    for name,digest in candidate['source_hashes'].items():assert sha(ROOT/name)==digest
    for name,digest in start['protected_modified_file_hashes'].items():assert sha(Path('E:/codes/ExactEBRP')/name)==digest
    assert sha(candidate['production_PE'])==candidate['production_PE_SHA'] and sha(candidate['DLL'])==candidate['DLL_SHA']
    bindings={name:sha(OUT/name) for name in ['confirmation_matrix.json','CPF_frozen.json','candidate_decision.json','CPF_decision.json',
        'reports/full.json','reports/comparisons.csv','reports/verified_U_trajectories.csv','reports/LP.json','reports/R147_selection.json']}
    receipt=dict(PASS=True,independent_nonimplementer_review=True,UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        Native_load=0,Optimize=0,compile=0,new_baseline_solve=0,elapsed_seconds=time.perf_counter()-tick,
        independent_script_SHA=sha(__file__),bindings=bindings,arms=armfacts,CPF=lp,
        observed_cost_before_final_review_charge=actual_cost,final_review_charge_pending=True,
        exact_rational_LP_optimality_claimed=False,public_delivery_not_yet_verified=True)
    (OUT/'review/independent_final_check.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k not in ['arms','CPF','bindings']}))
if __name__=='__main__':run()
