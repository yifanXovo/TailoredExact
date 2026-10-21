"""Independent finite read-only R128 audit. No solver, build, runner or pair() call.

Run only through round128_common.py meter. Writes only its new review artifacts.
Reuses the established LP grammar and complete-H trace reader, not comparison math.
"""
from pathlib import Path
from collections import Counter
from decimal import Decimal, localcontext
import ast, csv, hashlib, json, math, re, sys, traceback
import round108_reader as core
from compare_round112_startup import reconstruct as complete_h, fleet_key

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/unified_exact_round128'
REVIEW=OUT/'review'
PE='ac96cfea3e0ac109cda523b9a1e2458d98a7d552bf0542e2877c1379e84234fa'
DLL='9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88'
PRE='bcf98c6f639218bbc3b798722632a114e024331cd1d74416f8b9fc44b87e8cf5'
EXPECTED=[('SC-C15-S',0,['P','MB','MD-R','MS2']),('SC-B20-S',0,['MB','MD-R','MS2','P']),
          ('PB-B35-B',0,['MD-R','MS2','P','MB']),('SC-C15-S',1,['MS2','MB']),('SC-B20-S',1,['MB','MS2'])]
CORE_PAIRS=[('MB','P'),('MB','MD-R'),('MB','MS2'),('MD-R','P'),('MS2','P')]
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def rows(p):
    with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def near(a,b,eps=1e-9):return math.isclose(float(a),float(b),abs_tol=eps,rel_tol=1e-13)
def qualified(a):return all(a[k] is True for k in ['formal_protocol_qualified','numbers_qualified','certificate_qualified']) and not a['source_reduced']
def dec(x):return Decimal.from_float(float(x))
def physical(p,w):
    """Separate physical replay: empty departure, loaded return, prefix Q, full duration."""
    text=(ROOT/p['input_path']).read_text(encoding='utf-8')
    def vector(n):return ast.literal_eval(re.search(r'^\s*'+n+r'\s*=\s*(\[[^\n]*\])',text,re.M)[1])
    initial=vector('initial');Y=list(initial);D=vector('target');cap=vector('capacities');xy=vector('points');weights=vector('weights')
    if abs(max(weights[1:])-10)<1e-6:weights=[x/10 for x in weights]
    seen=set();vehicles=set();durations=[];returns=[];pickups=[]
    for route in w['routes']:
        k=route.get('vehicle',route.get('vehicle_id'));assert type(k) is int and 0<=k<p['M'] and k not in vehicles;vehicles.add(k)
        nodes=route['nodes'];assert len(nodes)>=2 and nodes[0]==nodes[-1]==0
        ops={}
        for op in route['operations']:
            i,x,y=(op['station'],op['pickup'],op['drop']) if isinstance(op,dict) else op
            assert i not in ops and int(x)==x and int(y)==y and x>=0 and y>=0 and bool(x)!=bool(y);ops[i]=(x,y)
        assert len(nodes[1:-1])==len(set(nodes[1:-1])) and set(nodes[1:-1])==set(ops)
        load=pickup=0
        for i in nodes[1:-1]:
            assert 1<=i<=p['V'] and i not in seen;seen.add(i);x,y=ops[i];load+=x-y;pickup+=x
            assert 0<=load<=p['Q_vector'][k];Y[i]+=y-x;assert 0<=Y[i]<=cap[i]
        travel=math.fsum(math.hypot(xy[a][0]-xy[b][0],xy[a][1]-xy[b][1])/1.5 for a,b in zip(nodes,nodes[1:]))
        duration=travel+(p['pickup_seconds']+p['drop_seconds'])*pickup;assert duration<=p['T_seconds']+1e-7
        durations.append(duration);returns.append(load);pickups.append(pickup)
    assert sum(Y[1:])==sum(initial[1:])-sum(returns)
    ratios=[Y[i]/D[i] for i in range(1,p['V']+1)];S=math.fsum(ratios)
    G=math.fsum(abs(x-y) for i,x in enumerate(ratios) for y in ratios[i+1:])/(p['V']*S) if S>0 else 0.
    P=math.fsum(weights[i]*abs(ratios[i-1]-1) for i in range(1,p['V']+1));F=G+p['lambda']*P
    assert near(F,w.get('F',w.get('objective')),1e-12)
    return dict(F=F,G=G,P=P,Y=Y,maximum_duration=max(durations,default=0),return_loads=returns,pickups=pickups,vehicles_replayed=p['M'],implicit_empty_vehicles=p['M']-len(vehicles))

def summary(pp):
    both=[q for q in pp if q['classification']=='BOTH_CERTIFIED']
    with localcontext() as ctx:
        ctx.prec=50
        gm=float((sum((Decimal(str(q['right_over_left_certification_ratio'])).ln() for q in both),Decimal(0))/len(both)).exp()) if both else None
    return dict(rows=len(pp),nonalias_typed_entries=len(pp),evaluable_nonalias_entries=len(pp),unevaluable_nonalias_entries=0,alias_entries=0,
                classes=dict(Counter(q['classification'] for q in pp)),directions=dict(Counter(q['direction'] for q in pp)),
                both_certified_intersection_n=len(both),both_certified_ids=[q['id'] for q in both],conditional_geometric_mean=gm)

def run():
    assert sha(REVIEW/'preformal_source_review.md')==PRE
    protected=[OUT/n for n in ['arms.csv','pairs.csv','mechanism_costs.csv','support_two_seeds.csv','actual_method_differences.json','stratified_summary.json','E2_frozen.json']]
    protected += [ROOT/'scripts'/n for n in ['round128_common.py','round128_campaign.py','round128_evidence.py']]
    protected += [REVIEW/'preformal_source_review.md']
    before={str(p.relative_to(ROOT)):sha(p) for p in protected}
    seal=read(OUT/'E2_frozen.json');assert seal['PE_SHA']==PE and seal['DLL_SHA']==DLL and seal['final_source_seal'] is True
    assert sha(seal['PE'])==PE
    for n,h in seal['source_bindings'].items():assert sha(ROOT/n)==h,('sealed native source drift',n)
    manifest=read(OUT/'experiment_manifest.json');assert len(manifest['groups'])==5
    csv_arms={(int(a['group']),a['method']):a for a in rows(OUT/'arms.csv')}
    csv_costs={(int(a['group']),a['method']):a for a in rows(OUT/'mechanism_costs.csv')}
    published_pairs={(int(a['group']),a['left'],a['right']):a for a in rows(OUT/'pairs.csv')}
    assert len(csv_arms)==len(csv_costs)==16 and len(published_pairs)==17
    state={};clock_facts=[];exposure=[];h={};models={};model_cache={};calls={};differences=[];productions=[]
    for number,(g,expected) in enumerate(zip(manifest['groups'],EXPECTED),1):
        id,seed,methods=expected;assert g['number']==number and g['role']['id']==id and g['seed']==seed and g['methods']==methods
        planned=CORE_PAIRS if number<=3 else [('MB','MS2')];assert [tuple(x) for x in g['pairs']]==planned
        camp=OUT/g['name'];identity=read(camp/'identity.json');aa=read(camp/'reconstructed.json')['arms']
        protected.extend([camp/'identity.json',camp/'reconstructed.json']);before.update({str(p.relative_to(ROOT)):sha(p) for p in protected[-2:]})
        assert identity['candidate_binary_sha256']==PE and identity['dll_sha256']==DLL and identity['source_hashes']==seal['source_bindings']
        assert [a['method'] for a in aa]==[l['method'] for l in identity['launches']]==methods
        for a,l in zip(aa,identity['launches']):
            key=(number,a['method']);state[key]=a;d=Path(l['destination']);p=l['panel'];c=csv_arms[key];cost=csv_costs[key]
            assert a['id']==id and a['seed']==seed and a['PE_SHA']==PE and a['DLL_SHA']==DLL and a['binary_layer']=='E2' and qualified(a)
            assert a['actually_executed'] and a['native_proof_qualified'] and a['raw_audit_passed'] and not a['rejected_calls']
            assert sha(ROOT/p['input_path'])==p['input_sha256']==a['input_SHA'] and p['lambda']==.15 and p['pickup_seconds']==p['drop_seconds']==60
            assert '--gurobi-seed' in l['command'] and l['command'][l['command'].index('--gurobi-seed')+1]==str(seed)
            pr=read(d/'producer_receipt.json');total=read(d/'arm_total_receipt.json');vc=read(d/'verification_closeout.json');r=read(d/'result.json');audit=read(d/'audit.json')
            assert audit['passed'] and pr['required_outputs_closed'] and pr['native_stopped_no_reentry'] and total['necessary_verification_complete'] and vc['necessary_verification_complete']
            assert sha(d/'producer_receipt.json')==a['producer_receipt_SHA']==total['producer_receipt_SHA']==vc['producer_receipt_SHA']
            assert sha(d/'verification_closeout.json')==total['verification_closeout_SHA'] and sha(d/'audit.json')==vc['audit_SHA']
            for n,v in read(d/'producer_seal.json')['required_SHA'].items():assert sha(d/n)==v
            assert near(pr['t_produce_perf']-pr['t0_perf'],pr['T_produce']) and near(total['T_total'],pr['T_produce']+total['T_verify'])
            for n,v in [('T_produce',pr['T_produce']),('T_verify',total['T_verify']),('T_total',total['T_total'])]:assert a[n]==v and float(c[n])==v and float(cost[n])==v
            assert pr['T_produce']<=a['cap_seconds'] and (a['T_cert']==pr['T_produce'] if a['certificate'] else a['T_cert'] is None)
            assert c['T_cert']==('' if a['T_cert'] is None else str(a['T_cert'])) and (c['certificate']=='True')==a['certificate']
            assert near(float(c['signed_gap']),a['U']-a['L'],1e-15) and float(c['U'])==a['U'] and float(c['L'])==a['L'] and a['L']<=a['U']+1e-7
            origin=read(d/'child_process_origin.json');assert origin['PE_SHA']==PE;productions.append((origin['actual_creation_unix'],pr['t_produce_unix'],number,a['method']))
            clock_facts.append(dict(group=number,id=id,seed=seed,method=a['method'],certificate=a['certificate'],T_produce=pr['T_produce'],T_verify=total['T_verify'],T_total=total['T_total'],T_cert=a['T_cert'],producer_receipt_SHA=sha(d/'producer_receipt.json')))
            if a['method']=='P':
                assert r['gurobi_optimize_count']==a['native_Optimize']==1 and not r['gurobi_hga_start_requested']
                assert not list((d/'external/native_logs').glob('*.round68.start.values.csv'))
                continue
            h[key]=complete_h(ROOT,p,d);assert h[key]['complete'] and cost['H_complete']=='True'
            obs=read(d/'observations.json');cc=[q['payload'] for q in obs if q['payload']['kind']=='call'];root=next(q for q in cc if q['leaf']=='L0');calls[key]=root
            assert root['lower_g']==0 and near(root['cutoff'],h[key]['physical']['F'],1e-12) and root['upper_g']==min(root['cutoff'],(p['V']-1)/p['V'])
            for q in cc:
                assert Path(q['model_path']).is_relative_to(d) and Path(q['native_log_path']).is_relative_to(d)
                assert sha(q['model_path'])==q['model_sha256']
            if root['model_sha256'] not in model_cache:model_cache[root['model_sha256']]=core.lp_model(Path(root['model_path']))
            m=model_cache[root['model_sha256']];models[key]=m
            assert near(cost['initial_own_U'],root['cutoff'],1e-12) and json.loads(cost['root_scope'])==[root['lower_g'],root['upper_g']]
            assert int(cost['root_rows'])==len(m['rows']) and int(cost['root_columns'])==len(m['order']) and int(cost['root_sentinel_rows'])==sum(not t and s=='<=' and b==-1 for t,s,b in m['rows'])==0
            ledger=rows(d/'external/paper_optimize_ledger.csv');kinds=Counter(q['solve_kind'] for q in ledger)
            counts=dict(actual_native_calls=len(ledger),root_LP_calls=sum(q['solve_kind']=='LP' and q['leaf_id']=='L0' for q in ledger),child_LP_calls=sum(q['solve_kind']=='LP' and q['leaf_id']!='L0' for q in ledger),terminal_calls=kinds['MIP'],partial_target_calls=sum(v for k,v in kinds.items() if k!='LP' and k!='MIP'),NEXT_target_calls=sum('NEXT' in q['solve_kind'] for q in ledger),child_bound_target_calls=sum('CHILD' in q['solve_kind'] for q in ledger),split_count=r['external_gini_tree_split_count'])
            for n,v in counts.items():assert int(cost[n])==v
            assert counts['actual_native_calls']==a['native_Optimize']==len(cc) and counts['split_count']==0
            for prefix,select in [('LP',True),('MIP',False)]:
                assert near(cost[prefix+'_native_seconds'],sum(float(q['solver_runtime']) for q in ledger if (q['solve_kind']=='LP')==select))
            starts=[read(s) for s in (d/'external/native_logs').glob('*.round68.start.json')];assert int(cost['actual_submitted_Starts'])==sum(bool(s['submitted']) for s in starts)
            if a['method']=='MD-R':
                assert kinds==Counter({'LP':1,'MIP':1}) and all(q['leaf_id']=='L0' for q in ledger)
                assert len({q['model_sha256'] for q in ledger})==1 and int(ledger[0]['integer_domain_restored'])==1 and r['external_gini_tree_canonical_artifact_generation_count']==1 and r['external_gini_tree_canonical_artifact_invalidation_count']==0
                assert sum(bool(s['submitted']) for s in starts)==1 and root['cutoff']==cc[-1]['cutoff'] and r['external_gini_tree_lifecycle_complete']
                assert (ledger[-1]['native_status']=='OPTIMAL')==a['certificate']
            exposure.append(dict(group=number,id=id,seed=seed,method=a['method'],H_complete=True,own_U0=root['cutoff'],native_statuses=[q['native_status'] for q in ledger],**counts))
        for candidate in ['MD-R','MS2']:
            if (number,candidate) not in h:continue
            a,b=h[(number,'MB')],h[(number,candidate)];ca,cb=calls[(number,'MB')],calls[(number,candidate)]
            assert a['fleet']==b['fleet'] and a['semantic_traces']==b['semantic_traces'] and a['physical']['Y']==b['physical']['Y']
            assert all(ca[n]==cb[n] for n in ['lower_g','upper_g','cutoff','settings'])
            if candidate=='MD-R':assert models[(number,'MB')]==models[(number,candidate)]
            differences.append(dict(group=number,id=id,comparison='MB/'+candidate,H_actions_fleet_match=True,root_scope_U_settings_match=True,MB_sentinel_rows=0,MB_splits=0,component_eligible=True))
    assert len(state)==16 and len({a['input_SHA'] for a in state.values()})==3
    ordered=sorted(productions);assert all(previous[1]<=following[0] for previous,following in zip(ordered,ordered[1:])),('overlapping native production',ordered)
    pp=[]
    for group,g in enumerate(manifest['groups'],1):
        for left,right in (CORE_PAIRS if group<=3 else [('MB','MS2')]):
            a,b=state[group,left],state[group,right];assert a['input_SHA']==b['input_SHA'] and a['PE_SHA']==b['PE_SHA']==PE and a['seed']==b['seed']
            ac,bc=a['certificate'],b['certificate'];ratio=delta=None
            if ac and bc:
                assert abs(a['U']-b['U'])<=1e-7
                delta=dec(a['T_produce'])-dec(b['T_produce']);direction='Win' if delta<0 else 'Lose' if delta>0 else 'Tie';classification='BOTH_CERTIFIED';ratio=dec(b['T_produce'])/dec(a['T_produce'])
            elif ac:classification,direction='LEFT_ONLY_CERTIFIED','Win'
            elif bc:classification,direction='RIGHT_ONLY_CERTIFIED','Lose'
            else:classification,direction='BOTH_OPEN','UNDETERMINED'
            q=dict(group=group,id=a['id'],seed=a['seed'],left=left,right=right,classification=classification,direction=direction,
                   left_T_cert=a['T_cert'],right_T_cert=b['T_cert'],left_minus_right_seconds=float(delta) if delta is not None else None,right_over_left_certification_ratio=float(ratio) if ratio is not None else None)
            old=published_pairs[group,left,right];assert old['classification']==classification and old['direction']==direction and old['alias']=='False' and old['nonalias_entry']=='True' and old['binary_layer']=='E2'
            for n in ['left_T_cert','right_T_cert','left_minus_right_seconds','right_over_left_certification_ratio']:
                assert old[n]=='' if q[n] is None else near(old[n],q[n]),(group,left,right,n,old[n],q[n])
            pp.append(q)
    assert len(pp)==17
    published=read(OUT/'stratified_summary.json');denominators={}
    for left,right in CORE_PAIRS:
        name=left+'/'+right;denominators[name]=summary([q for q in pp if q['group']<=3 and q['left']==left and q['right']==right])
        for n,v in denominators[name].items():assert near(v,published['core_by_comparison'][name][n]) if isinstance(v,float) else v==published['core_by_comparison'][name][n]
    denominators['additional_support_Seed1']=summary([q for q in pp if q['group']>3])
    for n,v in denominators['additional_support_Seed1'].items():assert near(v,published['additional_support_Seed1'][n]) if isinstance(v,float) else v==published['additional_support_Seed1'][n]
    support=[]
    for old in rows(OUT/'support_two_seeds.csv'):
        group=int(old['group']);a,b=state[group,'MB'],state[group,'MS2'];saving=dec(a['T_produce'])-dec(b['T_produce']) if a['certificate'] and b['certificate'] else None
        assert old['MS2_saving_seconds']=='' if saving is None else near(old['MS2_saving_seconds'],saving)
        support.append(dict(id=a['id'],seed=a['seed'],both_certified=saving is not None,MS2_saving_seconds=float(saving) if saving is not None else None,MS2_saving_percent=float(saving/dec(a['T_produce'])*100) if saving is not None else None,MB_U=a['U'],MB_L=a['L'],MS2_U=b['U'],MS2_L=b['L']))
    assert len(support)==5
    recorded={(x['group'],x['comparison']):x for x in read(OUT/'actual_method_differences.json')['records']}
    for q in differences:
        old=recorded[q['group'],q['comparison']];assert all(old[n] is True for n in ['complete_H_actions_fleet_equal','initial_root_scope_U_equal','actual_initial_native_settings_equal','component_interpretation_eligible']) and old['MB_actual_splits']==0 and old['MB_sentinel_rows']==0
    # Representative formal MD-R: independent full Start residual and physical replay.
    g=manifest['groups'][0];identity=read(OUT/g['name']/'identity.json');launch=next(l for l in identity['launches'] if l['method']=='MD-R');d=Path(launch['destination']);p=launch['panel'];m=models[1,'MD-R']
    pre=rows(d/'external/native_logs/L0_lp.gurobi.log.round128.pre_lp.values.csv');st=rows(d/'external/native_logs/L0_terminal_mip.gurobi.log.round68.start.values.csv')
    assert len(pre)==len(st)==len(m['order']) and [q['variable'] for q in pre]==[q['variable'] for q in st]==m['order']
    x={q['variable']:float(q['value']) for q in st}
    assert all(float(a['mapped_value'])==float(b['value'])==float(b['readback']) and a['type']==b['type']==m['types'][a['variable']] for a,b in zip(pre,st))
    assert all(lo-1e-7<=x[n]<=hi+1e-7 for n,(lo,hi) in m['bounds'].items()) and all(abs(x[n]-round(x[n]))<=1e-7 for n in m['order'] if m['types'][n] in ['I','B'])
    residual=[]
    for terms,sense,rhs in m['rows']:
        v=math.fsum(c*x[n] for n,c in terms)-rhs;residual.append(abs(v) if sense=='=' else max(0,v) if sense=='<=' else max(0,-v))
    assert max(residual)<=1e-7
    own=read(d/'hga.csv.exchange/final.json');own_physical=physical(p,own);final_physical=physical(p,read(d/'result.json'))
    objective=math.fsum(c*x[n] for n,c in m['objective'][0])+m['objective'][1];assert near(objective,own_physical['F'],1e-12)
    assert all(x[f'Y_{i}']==own_physical['Y'][i] for i in range(1,p['V']+1))
    pre_meta=read(d/'external/native_logs/L0_lp.gurobi.log.round68.start.json');st_meta=read(d/'external/native_logs/L0_terminal_mip.gurobi.log.round68.start.json')
    assert not pre_meta['submitted'] and all(pre_meta[n] for n in ['mapping_complete','rows_valid','objective_valid']) and all(st_meta[n] for n in ['mapping_complete','rows_valid','objective_valid','submitted','readback_valid'])
    obs=read(d/'observations.json');first_call=next(q for q in obs if q['payload']['kind']=='call');phase=next(q for q in rows(d/'phases.csv') if q['event']=='round128_own_Start_pre_lp');assert float(phase['process_seconds'])<=first_call['data_close_seconds']
    leaf=rows(d/'external/paper_leaf_ledger.csv');assert len(leaf)==1 and leaf[0]['status']=='closed' and leaf[0]['closure_source']=='native_terminal_mip_optimal'
    assert 'Optimal solution found' in (d/'external/native_logs/L0_terminal_mip.gurobi.log').read_text()
    deep=dict(path=str(d.relative_to(ROOT)),root_SHA=calls[1,'MD-R']['model_sha256'],columns=len(x),rows=len(residual),maximum_row_residual=max(residual),all_types_bounds_integer_domains_checked=True,pre_LP_and_full_submitted_readback_equal=True,pre_LP_before_native_call=True,mapped_original_objective=objective,own_fleet=own_physical,final_fleet=final_physical,closure_source=leaf[0]['closure_source'])
    # Full actual PB-B35 MS2 deletion, independently classify each removed row.
    a,b=models[3,'MB'],models[3,'MS2'];ca,cb=Counter(a['rows']),Counter(b['rows']);removed=ca-cb
    assert not cb-ca and a['order']==b['order'] and a['types']==b['types'] and a['bounds']==b['bounds'] and a['objective']==b['objective']
    families=Counter()
    for (terms,sense,rhs),count in removed.items():
        terms=dict(terms);z=[n for n in terms if n.startswith('z_')];pickup=[n for n in terms if n.startswith('p_')]
        assert len(z)==3 and len({n.split('_')[1] for n in z})==1 and sense=='<='
        if not pickup:assert set(z)==set(terms) and all(terms[n]==1 for n in z) and rhs==2;family='cover_3'
        else:assert len(pickup)==3 and set(pickup+z)==set(terms) and all(terms[n]==120 for n in pickup) and len({terms[n] for n in z})==1;family='conditional_3'
        families[family]+=count
    assert sum(removed.values())==3*math.comb(35,3)==19635 and dict(families)=={'conditional_3':12729,'cover_3':6906}
    deletion=dict(group=3,id='PB-B35-B',removed_rows=sum(removed.values()),families=dict(families),removed_columns=[],every_other_duplicate_preserving_row_type_bound_objective_equal=True)
    # Actual saved equality boundary, shared and fallback; no regenerated exports.
    boundaries=[]
    for path in ['La_equal_c/shared','La_equal_c/fallback','T3600_no_old_sentinel/shared','T3600_no_old_sentinel/fallback']:
        folder=OUT/'qualification/boundaries'/path;old,new=core.lp_model(folder/'mb/original.lp'),core.lp_model(folder/'md-r/original.lp')
        removed=Counter(old['rows'])-Counter(new['rows']);assert not Counter(new['rows'])-Counter(old['rows'])
        assert old['order']==new['order'] and old['types']==new['types'] and old['bounds']==new['bounds'] and old['objective']==new['objective'] and set(removed)<= {((),'<=',-1.)}
        n=sum(removed.values());assert n==(1 if path.startswith('La_equal') else 0)
        if n:assert any(s=='>=' and rhs==2 and dict(t)=={'e_1':1.,'e_2':1.} for t,s,rhs in new['rows'])
        boundaries.append(dict(case=path,removed_semantic_sentinels=n,all_other_semantics_equal=True,penalty_lower_bound_retained=True))
    assert all(sha(ROOT/n)==v for n,v in before.items()),'reviewed protected artifact changed during audit'
    assert sha(REVIEW/'preformal_source_review.md')==PRE
    result=dict(status='PASS',review_date='2026-10-22 Asia/Shanghai',actual_Optimize_or_Start_or_builds_by_reviewer=0,
                script_SHA=sha(__file__),preformal_SHA_preserved=PRE,protected_artifact_hashes=before,PE_SHA=PE,DLL_SHA=DLL,
                formal_arms=16,known_inputs=3,typed_comparisons=17,certified_arms=sum(a['certificate'] for a in state.values()),open_arms=sum(not a['certificate'] for a in state.values()),
                all_clock_receipts_and_qualifications_checked=True,native_productions_serial=True,comparison_arithmetic='Decimal.from_float of own producer receipts; pair() never called',
                comparisons=pp,denominators=denominators,clocks=clock_facts,support_two_seeds=support,H_root_eligibility=differences,controller_exposure=exposure,
                formal_MD_R_deep_check=deep,actual_MS2_full_deletion=deletion,boundary_differences=boundaries,
                limits=['Three known inputs; two Seeds only on two roles; shared arms are not independent observations.',
                        'Detailed row/type/bound/Start replay covers one formal MD-R; full explicit MS2 deletion covers one formal PB-B35 pair.',
                        'Reuses established LP grammar and complete-H trace reader; comparisons and representative physical replay are independently implemented.',
                        'No rational proof of all generated matrices or global floating-point error bound; no extra optimization.',
                        'Legacy formal_performance field is retained and not used as the present qualification authority.'])
    (REVIEW/'final_independent_evidence.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    table='\n'.join(f"| {q['group']} | {q['id']} | {q['seed']} | {q['left']}/{q['right']} | {q['classification']} | {q['direction']} |" for q in pp)
    den='\n'.join(f"| {name} | {q['rows']} | {q['both_certified_intersection_n']} | {q['conditional_geometric_mean']} |" for name,q in denominators.items())
    md=f'''# Round128 final independent review

**PASS for the bounded requested checks.** Reviewed on 2026-10-22 (Asia/Shanghai) by the separate preformal reviewer. No Optimize, native Start submission, build, experiment, native-source edit or sealed-artifact rewrite was performed. The preformal review remains SHA256 `{PRE}`. The audit ran through the requested `final_independent_review_01` analysis meter; its external receipt is the lifetime authority.

## Identity, qualification and clocks

All 16 formal arms use the same E2 PE `{PE}` and DLL `{DLL}` on exactly three known inputs in five predeclared groups. All current source bindings match the E2 seal. Every arm passes `formal_protocol_qualified`, `numbers_qualified`, `certificate_qualified`, native-proof and source checks. There are {result['certified_arms']} certified arms and {result['open_arms']} qualified open arms. Every uncertified `T_cert` is null; each certified `T_cert` equals its own unrounded `T_produce`. Producer seals, receipt hash links, complete production cost, verification/total clocks and serial native production were checked for every arm. The inherited `formal_performance` field is not the current qualification authority.

## Independently recomputed typed comparisons

Arithmetic starts from each arm's own full-precision producer/total receipts, using Decimal representations of binary64 clocks; the existing `pair()` function is never called. All 17 classifications, strict time directions, conditional ratios, difference fields and published denominators agree. No cap is substituted for a missing certification time and no R127/E1 time, solution or certificate supplies a comparison. Shared arms remain shared observations.

| Group | Input | Seed | Left/right | Class | Direction |
| --- | --- | ---: | --- | --- | --- |
{table}

| Comparison | Typed denominator | Both-certified ratio denominator | Conditional geometric mean, right/left |
| --- | ---: | ---: | ---: |
{den}

## Actual domains and controller exposure

All 13 MB-type arms complete the full 25-seed H trace. The eight actual MB/MD-R or MB/MS2 component comparisons have matching complete H actions/fleets, inventories, initial U, root scope and initial native settings. Actual MB/MD-R roots are fully semantically equal and all ordinary MB roots contain zero disputed sentinels. Every MB-type split count is zero. Child LPs and child-bound targets are recorded from actual ledgers and agree with `mechanism_costs.csv`; these runs support probing/target/scheduling comparisons, not observed multi-leaf split speedup. All three formal MD-R arms have exactly one root LP and one root MIP, no child/partial/target call, no rebuild, a complete submitted Start and a fixed own-U0 scope. Qualified open MD-R remains open.

## Representative formal MD-R and physical replay

Detailed arm: `{deep['path']}`. Its one original model is `{deep['root_SHA']}`. The actual ledger is OPTIMAL LP (return code zero), integer-domain restoration, OPTIMAL MIP (return code zero); the final L0 closure source is `native_terminal_mip_optimal`. The pre-LP check precedes the committed native call and submits no LP Start. All {deep['columns']} columns, actual VTypes, bounds, integer domains, all {deep['rows']} original rows and original objective were checked against the complete submitted/readback vector. Pre-LP values and Start/readback match column by column; maximum independently recomputed row residual is `{deep['maximum_row_residual']}`.

The separately implemented physical replay checks unique station service, integral one-way operations, empty departure, every capacity prefix, allowed loaded return, all travel plus full pickup/drop handling duration, inventory bounds/conservation and the depot-excluded G/P objective with the zero-denominator convention. Own H fleet: F={own_physical['F']}, G={own_physical['G']}, P={own_physical['P']}, longest duration={own_physical['maximum_duration']} seconds, return loads={own_physical['return_loads']}. Final nonempty fleet: F={final_physical['F']}, longest duration={final_physical['maximum_duration']} seconds, return loads={final_physical['return_loads']}. Both are legal under the original 3600-second horizon.

## Boundary and actual MS2 deletion

Saved T60 equality matrices in both shared and fallback writers differ only by one semantic empty `0<=-1` sentinel. Every other duplicate-preserving row, column, type, bound and objective is identical, including the retained weighted penalty lower bound. The T3600 controls remove no row. No boundary matrix was regenerated. Equality still excludes strict improvement rather than the equal-c physical witness; the near-equality numerical policy is not promoted to an exact-c proof.

The actual formal PB-B35-B Seed0 MB/MS2 root pair was independently parsed in full. MS2 removes exactly 19,635 rows: 12,729 conditional-three rows and 6,906 three-station covers. Each removed row involves exactly three stations on one vehicle; no pair/order-supply row or column is removed. The objective, column order, VTypes, bounds and every remaining duplicate-preserving row match. This directly checks the difficult cover/conditional mix rather than relying on the published deletion label.

## Finite interpretation and limits

K2 MS2 savings repeat at both same-build Seeds: 75.35878577339463 seconds (Seed0) and 285.8406637816224 seconds (Seed1), with both methods certified. K1 reverses from 8.127292800112627 seconds saved to 0.24072338780388236 seconds slower. All four K3 methods remain open. The draft single `BOUNDED_SIMPLIFICATION_SIGNAL` interpretation is consistent only as a proposal for one unexecuted, globally uniform triple-removal confirmation, while retaining these risks and the frozen complete M-B as the sole paper method. It establishes neither universal safety nor a replacement default. MD-R timing is mixed; legal definition alone is not a D performance victory.

The audit covers all comparison arithmetic, all clocks/qualifications and all H/root/exposure relations; detailed native-vector/physical replay covers one formal MD-R and full deletion classification covers one actual formal MS2 pair. It reuses the established LP grammar and complete-H trace reader. It is not an independent implementation of every historical reader, an all-history requalification, a rational proof of all matrices or a global floating-point error theorem. Full-precision recomputations and checked file hashes are in `final_independent_evidence.json`. Original formal files and the preformal review are unchanged.
'''
    (REVIEW/'final_independent_review.md').write_text(md,encoding='utf-8')
    print(json.dumps(dict(status='PASS',arms=16,pairs=17,certified=result['certified_arms'],open=result['open_arms'],directions=dict(Counter(q['direction'] for q in pp)),review=str(REVIEW/'final_independent_review.md'),evidence_SHA=sha(REVIEW/'final_independent_evidence.json'),preformal_SHA=sha(REVIEW/'preformal_source_review.md'))))

if __name__=='__main__':run()
