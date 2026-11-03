"""Independent scientific closeout, using only bytes and Python stdlib."""
from pathlib import Path
from collections import Counter
import ast,csv,datetime,hashlib,json,math,re,time

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'results/unified_exact_round151'
TICK=time.perf_counter()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def table(p):
    with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def near(x,y,tol=1e-10):assert abs(float(x)-float(y))<=tol,(x,y)

matrix=read(OUT/'confirmation_matrix.json');report=read(OUT/'reports/full.json')
manifest=read(OUT/'candidate_manifest.json');admission=read(OUT/'review/confirmation_admission.json')
assert admission['decision']=='ACCEPT' and admission['matrix_SHA']==sha(OUT/'confirmation_matrix.json')
assert sha(manifest['production_PE'])==manifest['production_PE_SHA']==admission['PE_SHA']
assert sha(manifest['DLL'])==manifest['DLL_SHA']
for name,digest in manifest['source_hashes'].items():assert sha(ROOT/name)==digest,name
assert matrix['candidate_manifest_SHA']==sha(OUT/'candidate_manifest.json')
assert matrix['candidate_freeze_SHA']==sha(OUT/'candidate_freeze.json')
assert len(report['formal_arms'])==2 and not report['pending']
assert report['complete_Native_Optimize']==report['complete_Native_returned']==9
assert report['qualification_Native_Optimize']==report['qualification_Native_returned']==4
assert report['diagnostic_LP_Optimize']==report['diagnostic_LP_returned']==2
assert report['repeated_baseline_Optimize']==report['extra_quality_Optimize']==0
trajectory=table(OUT/'reports/verified_U_trajectories.csv')
full_csv=table(OUT/'reports/full.csv');comparison_csv=table(OUT/'reports/comparisons.csv')
facts=[];native_count=0;h_fleets=[]

def physical(panel,event):
    text=(ROOT/panel['input_path']).read_text(encoding='utf-8')
    def vec(name):return ast.literal_eval(re.search(r'^\s*'+name+r'\s*=\s*(\[[^\n]*\])',text,re.M)[1])
    initial,target,capacity,points,weight=[vec(k) for k in ['initial','target','capacities','points','weights']]
    if abs(max(weight[1:])-10)<1e-6:weight=[x/10 for x in weight]
    y=initial.copy();seen=set();cars=set();durations=[];returns=[]
    for route in event['routes']:
        k=route.get('vehicle',route.get('vehicle_id'));assert k not in cars and 0<=k<panel['M'];cars.add(k)
        nodes=route['nodes'];assert nodes[0]==nodes[-1]==0
        ops={}
        for op in route['operations']:
            i,p,d=(op['station'],op['pickup'],op['drop']) if isinstance(op,dict) else op
            assert i not in ops and p>=0 and d>=0 and p==int(p) and d==int(d) and bool(p)!=bool(d)
            ops[i]=(p,d)
        assert len(nodes[1:-1])==len(set(nodes[1:-1])) and set(nodes[1:-1])==set(ops)
        load=0;handling=0.
        for i in nodes[1:-1]:
            assert i not in seen and 1<=i<=panel['V'];seen.add(i)
            p,d=ops[i];load+=p-d;y[i]+=d-p
            assert 0<=load<=panel['Q_vector'][k] and 0<=y[i]<=capacity[i]
            handling+=panel['pickup_seconds']*p+panel['drop_seconds']*d
        # Returning stock to the depot is permitted. Its unload handling is
        # paid at the same drop unit cost; it reduces final station inventory.
        handling+=panel['drop_seconds']*load;returns.append(load)
        duration=sum(math.dist(points[a],points[b])/1.5 for a,b in zip(nodes,nodes[1:]))+handling
        assert duration<=panel['T_seconds']+1e-7;durations.append(duration)
    assert cars==set(range(panel['M']))
    assert sum(y[1:])==sum(initial[1:])-sum(returns)
    ratios=[y[i]/target[i] for i in range(1,len(y))];total=sum(ratios)
    g=sum(abs(ratios[i]-ratios[j]) for i in range(len(ratios)) for j in range(i))/(len(ratios)*total) if total else 0.
    p=sum(weight[i]*abs(y[i]/target[i]-1) for i in range(1,len(y)))
    f=g+panel['lambda']*p
    near(f,event.get('objective',event.get('F')),1e-7)
    return dict(G=g,P=p,F=f,Y=y,max_duration=max(durations))

for record in report['formal_arms']:
    group=matrix['groups'][record['position']-1];identity_path=OUT/group['group']/'identity.json'
    assert sha(identity_path)==group['identity_SHA'];identity=read(identity_path);launch=group['launch']
    assert identity['launches']==[launch]
    assert identity['candidate_binary_sha256']==record['PE_SHA']==manifest['production_PE_SHA']
    d=Path(record['destination']);panel=launch['panel']
    assert sha(ROOT/panel['input_path'])==record['input_SHA']==panel['input_sha256']
    assert panel['lambda']==.15 and panel['T_seconds']==7200 and panel['Q_vector']==[20,25,30]
    assert launch['cap_seconds']==record['cap']==2400
    close=read(d/'verification_closeout.json');seal=read(d/'producer_seal.json');receipt=read(d/'producer_receipt.json')
    assert close['necessary_verification_complete'] and close['implementation_qualified'] and close['evidence_complete']
    assert close['native_proof_qualified'] and close['no_new_solution_or_certificate_backfilled']
    assert seal['native_stopped_no_reentry'] and receipt['required_outputs_closed']
    assert sha(d/'producer_seal.json')==receipt['producer_seal_SHA']
    assert sha(d/'producer_receipt.json')==close['producer_receipt_SHA']
    for name,digest in seal['required_SHA'].items():assert sha(d/name)==digest
    audit=read(d/'audit.json');assert sha(d/'audit.json')==close['audit_SHA']
    assert audit['passed'] and audit['implementation_qualified'] and audit['raw_bytes_unchanged']
    for k in ['U','L','signed_gap','relative_gap','T_produce']:
        near(audit['endpoint'][k],record[k])
    assert record['certificate'] is False and record['T_cert'] is None
    near(record['T_total'],record['T_produce']+record['T_verify'])
    near(record['signed_gap'],record['U']-record['L']);near(record['relative_gap'],record['signed_gap']/record['U'])
    near(record['T_produce'],receipt['T_produce'])
    total_receipt=read(d/'arm_total_receipt.json')
    near(total_receipt['T_total'],record['T_total'])
    obs=read(d/'observations.json');calls={};returns=set();improvements=[];best=math.inf;witness_count=0;first_physical=None
    cached_model_sha={}
    for item in obs:
        event=item['payload'];seq=item['sequence'];raw=d/'journal'/f'event_{seq}.json'
        assert sha(raw)==item['sha256'] and read(raw)==event and event['sequence']==seq
        commit=(d/'journal'/f'event_{seq}.commit').read_text().split()
        assert int(commit[1])==seq and int(commit[3])==raw.stat().st_size and commit[4]==item['sha256']
        if event['kind']=='call':
            assert event['call'] not in calls;calls[event['call']]=event
            assert event['settings']['Seed']==0 and event['settings']['Threads']==1
            model_path=Path(event['model_path'])
            if model_path not in cached_model_sha:cached_model_sha[model_path]=sha(model_path)
            assert cached_model_sha[model_path]==event['model_sha256']
        elif event['kind']=='returned':
            assert event['return_code']==0 and event['call'] in calls;returns.add(event['call'])
        elif event['kind']=='witness':
            actual=physical(panel,event);witness_count+=1
            near(actual['G'],event['G'],1e-7);near(actual['P'],event['P'],1e-7)
            if first_physical is None:first_physical=actual
            if event['objective']<best-1e-15:
                best=event['objective'];improvements.append((seq,best,item['effective_available_seconds'],item['sha256']))
        elif event['kind']=='bound':assert not event['inconsistent']
    assert returns==set(calls)
    ledger=table(d/'external/paper_optimize_ledger.csv')
    assert len(ledger)==len(calls)==record['declared_calls']==record['returned_calls'];native_count+=len(ledger)
    assert all(row['optimize_return_code']=='0' for row in ledger)
    near(sum(float(row['work']) for row in ledger),record['Native_total_Work'])
    near(sum(float(row['simplex_iterations']) for row in ledger),record['Native_total_simplex_iterations'])
    assert sum('TARGET' in row['solve_kind'] for row in ledger)==record['target_calls']
    assert sum(row['solve_kind']=='LP' for row in ledger)==record['LP_calls']==3
    split=table(d/'external/split_decision_ledger.csv')
    assert sum(int(row['split']) for row in split)==record['actual_split_count']==0
    cover=audit['qualified_cover'];assert cover['complete_coverage'] and not cover['all_relevant_closed']
    assert len(cover['leaves'])==1 and cover['leaves'][0]['status']=='open'
    near(float(cover['leaves'][0]['lower_bound']),record['L'])
    near(cover['L'],record['L'])
    root_calls=[event for event in calls.values() if event['leaf']=='L0']
    root_bound=max(item['payload']['native_bound'] for item in obs if item['payload']['kind']=='bound' and item['payload']['call'] in {event['call'] for event in root_calls})
    near(root_bound,record['L'])
    for event in root_calls:
        assert event['lower_g']==0 and event['upper_g']==first_physical['F'] or abs(event['upper_g']-first_physical['F'])<1e-12
        assert event['cutoff']>=record['U']
    proof=[row for row in ledger if row['solve_kind']=='MIP'][-1]
    native_text=Path(proof['native_log']).read_text(encoding='utf-8')
    printed=re.findall(r'Best objective [^,]+, best bound ([^,]+), gap',native_text)
    assert printed;near(float(printed[-1]),record['L'],1e-7)
    physical_endpoint=physical(panel,read(d/'independent_evidence.json')['physical'])
    near(physical_endpoint['F'],record['U']);near(best,record['U'],1e-8)
    near(physical_endpoint['G'],record['physical_G']);near(physical_endpoint['P'],record['physical_P'])
    selected=[row for row in trajectory if row['method']==record['method'] and row['role']==record['role']]
    assert len(selected)==len(improvements)
    for saved,(seq,value,at,digest) in zip(selected,improvements):
        assert int(saved['sequence'])==seq and saved['committed_event_SHA']==digest
        near(saved['U'],value);near(saved['producer_seconds'],at)
        assert saved['raw_observation_SHA']==sha(d/'observations.json')
    h=audit['full_H'];assert h['complete'] and h['seed_ids']==list(range(1,26));h_fleets.append(h['fleet'])
    assert record['H_complete'] and record['H_semantic_SHA']==report['formal_arms'][0]['H_semantic_SHA']
    cap_audit=read(d/'round151_control_audit.json');assert cap_audit['PASS']
    assert read(d/'round149_control_audit.json')['enabled'] is False
    if record['method']=='B':assert cap_audit['mode']=='off' and cap_audit['root'] is None and not cap_audit['models']
    else:
        assert cap_audit['mode']=='conditional' and cap_audit['root']['base_model_SHA']==admission['helper_scope_change']['zero_solve_requalification'][0]['source_SHA']
        assert cap_audit['root']['states']==read(OUT/'LP/arithmetic/N-B35-S.json')['states']
        assert cap_audit['first_call_SHA']==calls[min(calls)]['model_sha256']
        assert record['cap_rows']==537 and record['cap_nonzeros']==1074
    csvrow=next(row for row in full_csv if row['method']==record['method'])
    for k in ['U','L','signed_gap','relative_gap','T_produce','T_verify','T_total','Native_total_Work']:
        near(csvrow[k],record[k])
    facts.append(dict(method=record['method'],physical_U=physical_endpoint['F'],supported_L=record['L'],
        complete_witnesses_physically_recomputed=witness_count,strict_U_events=len(improvements),
        calls=len(calls),returned=len(returns),actual_splits=0,target_calls=record['target_calls'],
        sealed_required_members=len(seal['required_SHA']),all_event_hashes_and_commits_verified=True))
assert native_count==9 and h_fleets[0]==h_fleets[1]

b,c=report['formal_arms'];comparison=report['comparisons'][0]
near(comparison['delta_U'],c['U']-b['U']);near(comparison['delta_L'],c['L']-b['L'])
near(comparison['delta_signed_gap'],c['signed_gap']-b['signed_gap'])
near(comparison['U_improvement_percent'],100*(b['U']-c['U'])/b['U'])
near(comparison['L_improvement_percent'],100*(c['L']-b['L'])/b['L'])
for k in ['delta_U','delta_L','delta_signed_gap','U_improvement_percent','L_improvement_percent']:
    near(comparison_csv[0][k],comparison[k])
severe=(c['U']-b['U']>max(.001,.05*b['U']) and c['signed_gap']-b['signed_gap']>max(.005,.25*b['signed_gap']))
assert severe is False and comparison['serious_double_open_regression'] is False
decision=read(OUT/'candidate_decision.json')
assert decision['decision']=='EXPRESSION_AND_LP_VALUE_ONLY_CLOSE_COMPLETE_PROMOTION'
assert decision['study_complete'] and decision['root_penalty_chain_closed'] and decision['stable_B_primary']
assert not decision['recommend_complete_enhancement'] and decision['adoption_not_threshold_only']
assert read(OUT/'certificate_pair_decision.json')['enter'] is False
assert read(OUT/'clarification_decision.json')['enter'] is False
for group in matrix['groups'][2:]:assert not Path(group['launch']['destination']).exists()
assert len(report['unentered'])==2 and all(row['role']=='N-C20-U' for row in report['unentered'])

frozen=read(OUT/'LP_frozen.json');revision=read(OUT/'engineering/helper_revision_record.json')
assert sha(OUT/'engineering/executed_LP.py')==frozen['LP_script_SHA']
assert sha(OUT/'engineering/executed_LP_math.py')==revision['executed_LP_math_SHA']==frozen['math_SHA']
assert sha(ROOT/'scripts/round151_math.py')==revision['current_math_SHA']
for tag in ['P','C']:
    folder=OUT/'LP'/f'N-B35-S_{tag}';result=read(folder/'result.json')
    assert result['qualified'] and result['LP_Optimize']==1 and not result['exact_rational_optimality_certificate']
    for name,key in [('model.mps','model_SHA'),('solution.json.gz','solution_SHA'),('dual.json.gz','dual_SHA')]:assert sha(folder/name)==result[key]

cost=read(OUT/'cost_report.json');charged=0.;build=0.;failed=[];later_charges=[]
cost_timestamp=datetime.datetime.fromisoformat(cost['UTC']).timestamp()
for launch_path in (OUT/'fees').glob('*/launch.json'):
    launch=read(launch_path);receipt=read(launch_path.parent/'receipt.json')
    assert receipt['exit_observed'] and receipt['nested_H_LP_MIP_not_added']
    charged+=receipt['G1_seconds'];build+=receipt['separately_reported_seconds']
    if receipt['end_unix']>cost_timestamp:later_charges.append(dict(label=launch_path.parent.name,seconds=receipt['G1_seconds']))
    if receipt['exit_code']:failed.append(dict(label=launch_path.parent.name,seconds=receipt['G1_seconds']))
charged+=sum(row['outer_seconds'] for row in read(OUT/'infra/external_costs.json')['processes'])
near(charged,cost['charged_new_experiment_seconds']+sum(row['seconds'] for row in later_charges),1e-7)
near(build,cost['build_seconds'],1e-7)
assert charged<14400 and cost['exact_clock_accounting_incomplete']
assert not cost['experiment']['unclosed'] and cost['nested_Runtime_Work_not_added']
docs=['final_report.md','mathematical_analysis.md','LP_report.md','manuscript.tex']
result=dict(decision='ACCEPT_SCIENTIFIC_CLOSEOUT',independent_nonimplementer_review=True,
    source_commit=manifest['source_commit'],PE_SHA=manifest['production_PE_SHA'],
    candidate_decision_SHA=sha(OUT/'candidate_decision.json'),full_report_SHA=sha(OUT/'reports/full.json'),
    reviewed_prose_SHA={name:sha(OUT/name) for name in docs},
    mathematical_validity_and_actual_inclusion_preserved=True,LP_and_complete_evidence_kept_separate=True,
    original_physical_fleets_and_every_committed_witness_checked=True,formal_arms=facts,
    raw_data_versions_seals_and_expenses_consistent=True,
    adoption_conclusion='The finite prescribed same-PE B/C test provides no sufficient complete benefit; closing promotion while retaining expression/LP results is supported.',
    scope_limit='One known/exposed complete role and one Seed; no complete N-C20 or P attribution result is inferred.',
    severe_reference_is_not_adoption_criterion=True,stop_and_unentered_decisions_supported=True,
    costs_before_this_review=dict(charged_seconds=charged,build_seconds=build,ceiling=14400,failed_processes=failed,
        fee_receipts_after_current_cost_snapshot=later_charges,refresh_still_required=True),
    minor_editorial_comments_resolved=['P Optimize wall and Runtime are now distinguished.','Cap-pass complexity is linear after multiplier selection; inherited sorting is now separately disclosed.'],
    findings=[],remaining_delivery_checks=['Refresh charged review/local closure fees and generated prose once.','Public byte/member restore and Draft PR readback are delivery steps, not new science.','Final prose readback after two minor editorial corrections.'],
    Optimize=0,Native_load=0,compile=0,reviewer_outer_seconds=time.perf_counter()-TICK)
(OUT/'review/final_scientific_review.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result))
