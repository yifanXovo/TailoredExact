"""Inherited R108 independently computed physics/model/Start/coverage kernel, adapted for per-arm Seed, zero objective and R109 paths. No main; caller injects explicit-root IO."""
def full_physics(q,routes,p):
    routes=[dict(r) for r in routes];cars=[r['vehicle'] for r in routes]
    require(len(set(cars))==len(cars),'unique represented vehicles')
    for k in range(q['M']):
        if k not in cars:routes.append(dict(vehicle=k,nodes=[0,0],operations=[]))
    ph=physical(q,routes,p['T_seconds'],p['lambda'],p['pickup_seconds'],p['drop_seconds'])
    ph.update(full_routes=routes,empty_vehicles_added=q['M']-len(cars))
    require(sum(ph['final_inventories'][1:])==sum(q['initial'][1:])-sum(x['return_load'] for x in ph['routes']),'fleet inventory minus depot return conservation')
    return ph

def domain_contract(m,q,arm):
    t=m['types'];quant=[n for n in t if n.startswith(('p_','d_'))]
    require(len(quant)==2*q['V']*q['M'],'complete quantity column domain')
    require(all(t[n]==('C' if arm=='M-B' else 'I') for n in quant),'original p/d native domain '+arm)
    require(all(t[n] in ['I','B'] for n in t if n.startswith(('x_','load_','Y_'))),'integer original route/load/inventory domain')
    require(all(t[n]=='B' for n in t if n.startswith(('mode_','z_')) or re.fullmatch(r'state_\d+_\d+',n)),'original binary state/direction/visit domain')
    require(sum(n.startswith('mode_') for n in t)==q['V']*q['M'],'all original direction binaries retained')
    expected=[]
    if arm=='M-B':
        for i in range(1,q['V']+1):
            a={f'{v}_{k}_{i}':1. for k in range(q['M']) for v in ['p','d']}
            selectors=[n for n in t if re.fullmatch(f'state_{i}_'+r'\d+',n)]
            require(bool(selectors),'existing admissible state selectors '+str(i))
            for n in selectors:
                motion=abs(q['initial'][i]-int(n.rsplit('_',1)[1]))
                if motion:a[n]=-float(motion)
            b={f'z_{k}_{i}':1. for k in range(q['M'])}
            initial=f"state_{i}_{q['initial'][i]}"
            if initial in t:b[initial]=1.
            expected.extend([('=',0.,tuple(sorted(a.items()))),('=',1.,tuple(sorted(b.items())))])
        require(not Counter(expected)-Counter(m['rows']),'all frozen A/B coefficient equations present')
    return dict(columns=len(t),rows=len(m['rows']),native_types=dict(Counter(t.values())),quantity_columns=len(quant),AB_exact_rows=len(expected))

def scope_contract(c,m,q):
    if c['full_original']:
        require(native_scope_qualified(c),'full original model uses independently qualified integer native call');return
    lo,hi,cut=c['lower_g'],c['upper_g'],c['cutoff']
    require(c['gmax']==(q['V']-1)/q['V'] and 0<=lo<=hi<=c['gmax']+TOL,'actual physical gmax and scope')
    require(m['bounds']['G']==(lo,hi),'saved native G domain equals journal scope')
    rr=Counter(m['rows'])
    require(rr[('<',cut,tuple(sorted(m['objective'].items())))]>=1,'actual objective cutoff row equals journal cutoff')
    for g,sense in [(lo,'>'),(hi,'<')]:
        terms={f'h_{i}_{j}':1. for i in range(1,q['V']+1) for j in range(i+1,q['V']+1)}
        if g:
            for i in range(1,q['V']+1):terms[f'r_{i}']=-q['V']*g
        require(rr[(sense,0.,tuple(sorted(terms.items())))]>=1,'actual shared true-G cap/floor row equals scope')

def supported(lo,hi,proofs):
    """Unconditional bound on a true-G interval; no epigraph-scope extension."""
    require(0<=lo<=hi,'valid requested proof interval')
    points=sorted({lo,hi,*[x for p in proofs for x in [p['lo'],p['hi']] if lo<x<hi]})
    segments=list(zip(points,points[1:])) or [(lo,hi)]
    return min(max([left]+[min(p['L'],p['cutoff']) for p in proofs if p['lo']<=left+1e-12 and p['hi']+1e-12>=right]) for left,right in segments)

def cover_check(c,value,proofs,witnesses):
    if c['full_original']:
        require(value<=min((w['U'] for w in witnesses),default=math.inf)+TOL,'plain full-model native bound does not contradict available physical U');return value
    pieces=[dict(x) for x in c['cover']];cutoff=c['cutoff'];matched=0
    for x in pieces:
        if value is not None and (x['id'],x['lower_g'],x['upper_g'],x['cutoff'])==(c['leaf'],c['lower_g'],c['upper_g'],cutoff):
            x['lower']=max(x['lower'],value);matched+=1
        require(math.isfinite(x['lower']) and x['cutoff']+TOL>=cutoff,'finite same-or-weaker coverage cutoff')
        bound=supported(x['lower_g'],x['upper_g'],proofs)
        require(min(x['lower'],x['cutoff'])<=bound+TOL,'chronologically supported actual saved cover piece')
        for w in witnesses:
            if x['lower_g']-TOL<=w['G']<=x['upper_g']+TOL and w['U']<=x['cutoff']+TOL:
                require(x['lower']<=w['U']+TOL,'cover piece bound consistent with own physical witnesses')
    if value is not None:require(matched==1,'current native bound updates exactly one matching active cover piece')
    covered=0.
    for x in sorted(pieces,key=lambda x:x['lower_g']):
        require(0<=x['lower_g']<=covered+1e-12 and x['lower_g']<=x['upper_g'],'saved full cover has no hole');covered=max(covered,x['upper_g'])
    require(pieces and covered+1e-12>=min(cutoff,c['gmax']),'saved full cover covers every possible improving true G')
    require(cutoff+TOL>=min(w['U'] for w in witnesses),'same-run cutoff has own physical witness')
    return min([cutoff]+[min(x['lower'],x['cutoff']) for x in pieces])

def normalize_existing_start_routes(q,routes):
    """Exact inherited normalizeRound61Routes: no arbitrary vehicle matching.

    Classes use equal original Q, gather ascending original vehicle ids, stable
    sort by decreasing operation count, then assign ascending ids in that same
    class. Unused vehicles are omitted, as in the original C++ implementation.
    """
    require(len({r['vehicle'] for r in routes})==len(routes) and all(0<=r['vehicle']<q['M'] for r in routes),'Start normalization has valid unique original vehicle ids')
    lookup={r['vehicle']:r for r in routes};normalized=[];mapping=[]
    for capacity in sorted(set(q['Q'])):
        ids=[k for k in range(q['M']) if q['Q'][k]==capacity]
        used=[lookup[k] for k in ids if k in lookup and lookup[k]['operations']]
        used.sort(key=lambda r:-len(r['operations'])) # stable after ascending ids
        for target,r in zip(ids,used):
            require(q['Q'][r['vehicle']]==q['Q'][target],'original Start normalization never crosses capacities')
            mapping.append(dict(source_vehicle=r['vehicle'],normalized_vehicle=target,capacity=capacity,operation_count=len(r['operations'])))
            rr=dict(r);rr['vehicle']=target;normalized.append(rr)
    normalized.sort(key=lambda r:r['vehicle'])
    return normalized,mapping

def validate_start_fleet_vector(vals,q,routes,ph):
    """Every actual x/conn/z/mode/p/d/load/ord column against that exact fleet."""
    expected={}
    for r in routes:
        k=r['vehicle'];ops={o['station']:o for o in r['operations']};load=0;nodes=r['nodes']
        require(len(ops)==len(r['operations']),'unique Start station operations')
        for position,(i,j) in enumerate(zip(nodes,nodes[1:]),1):
            expected[f'x_{k}_{i}_{j}']=1.;expected[f'conn_{k}_{i}_{j}']=float(len(nodes)-1-position)
        for position,i in enumerate(nodes[1:-1],1):
            o=ops[i];pu,dr=o['pickup'],o['drop'];load+=pu-dr
            require(0<=load<=q['Q'][k],'normalized Start own prefix load within unchanged capacity')
            expected.update({f'p_{k}_{i}':float(pu),f'd_{k}_{i}':float(dr),f'z_{k}_{i}':1.,f'mode_{k}_{i}':float(pu>0),f'load_{k}_{i}':float(load),f'ord_{k}_{i}':float(position)})
    checked=Counter()
    for n,v in vals.items():
        family=n.split('_',1)[0]
        if family in {'x','conn','z','mode','p','d','load','ord'}:
            require(near(v,expected.get(n,0.),1e-5),'complete normalized own-fleet Start column '+n);checked[family]+=1
        elif family=='Y':require(near(v,ph['final_inventories'][int(n.split('_')[1])],1e-5),'Start inventory is from same normalized own fleet');checked['Y']+=1
        elif re.fullmatch(r'state_\d+_\d+',n):
            _,i,state=n.split('_');require(near(v,float(ph['final_inventories'][int(i)]==int(state)),1e-5),'Start state selector is from same normalized own fleet');checked['state']+=1
    require(near(vals['G'],ph['G'],1e-7),'Start true G matches same normalized own physical fleet')
    return dict(checked)

def start_check(d,sp,m,q,p):
    meta=obj(sp);csvp=sp.with_name(sp.name.replace('.json','.values.csv'));rr=rows(csvp)
    vals={r['variable']:float(r['value']) for r in rr}
    require(meta['submitted'] and meta['mapping_complete'] and meta['readback_valid'],'complete actually submitted native Start')
    require(meta['model_sha256']==sha(next(under_root(c['model_path']) for c in start_check.calls if c['model_sha256']==meta['model_sha256'])),'Start exact measured model SHA')
    require(set(vals)==set(m['bounds']) and len(vals)==len(rr),'Start has every original model column exactly once')
    for r in rr:
        n=r['variable'];v=vals[n];low,high=m['bounds'][n]
        require(r['type']==m['types'][n] and math.isfinite(v) and near(v,float(r['readback']),1e-12),'actual native Start type/value readback')
        require(low-1e-6<=v<=high+1e-6 and (r['type']=='C' or abs(v-round(v))<=1e-5),'Start finite native bound/domain')
    violations=[]
    for sense,rhs,terms in m['rows']:
        lhs=sum(vals[n]*a for n,a in terms)
        violations.append(abs(lhs-rhs) if sense=='=' else max(0,lhs-rhs) if sense=='<' else max(0,rhs-lhs))
    require(max(violations,default=0)<=1e-6,'all actual Start numeric original rows hold')
    wp=d/'external'/(meta['source']+'_witness.json');w=obj(wp);before=full_physics(q,w['routes'],p)
    normalized,mapping=normalize_existing_start_routes(q,w['routes']);ph=full_physics(q,normalized,p)
    require(before['final_inventories']==ph['final_inventories'] and near(before['U'],ph['U'],1e-10) and near(before['G'],ph['G'],1e-10),'exact inherited equal-Q relabelling preserves original own physical witness')
    require(near(ph['U'],w['objective']) and near(ph['U'],meta['objective']) and near(ph['U'],sum(vals[n]*a for n,a in m['objective'].items())),'Start physical/objective agreement')
    matched=validate_start_fleet_vector(vals,q,normalized,ph)
    return dict(metadata_path=str(sp.relative_to(ROOT)),metadata_SHA=sha(sp),values_SHA=sha(csvp),model_SHA=meta['model_sha256'],columns=len(vals),rows_checked=len(violations),max_row_violation=max(violations,default=0),own_physical_U=ph['U'],native_types=dict(Counter(r['type'] for r in rr)),source_witness_SHA=sha(wp),exact_original_vehicle_normalization=mapping,all_normalized_route_columns_checked=matched,normalization_call_site='src/GurobiBaseline.cpp:634',normalization_implementation='src/Round61Candidates.cpp:89-108')

def final_partition(d,q,initial_U,U,proofs,native_records,lpstatus,raw):
    """Validate the actual tree partition without fixing its leaf/call counts."""
    leaves=rows(d/'external/paper_leaf_ledger.csv');ids={r['leaf_id']:r for r in leaves}
    require(len(ids)==len(leaves) and bool(ids),'all actual leaf ledger identities unique')
    roots=[r for r in leaves if not r['parent_id']]
    require(len(roots)==1 and roots[0]['leaf_id']=='L0','one inherited actual root identity')
    root=roots[0];rootlo=float(root['gamma_L']);roothi=float(root['gamma_U'])
    require(rootlo==0 and near(roothi,min(initial_U,(q['V']-1)/q['V']),1e-12),'root covers original potentially improving true-G domain')
    valid_sources={'objective_nonnegative_penalty_G_floor','optimal_complete_lp_relaxation',
        'valid_child_target_native_bound','valid_next_leaf_target_native_bound','native_terminal_mip_bound',
        'inherited_parent_lp_bound','optimal_complete_child_lp_relaxation','complete_disjunction_min_child_bound',
        'native_partial_mip_bound','gamma_lower_bound_floor','inherited_parent_valid_bound',
        'inherited_requeued_parent_native_bound','inherited_parent_partial_native_bound',
        'minimum_original_sibling_valid_bound'}
    children={i:[] for i in ids};qualified=[]
    for r in leaves:
        lo,hi,L=float(r['gamma_L']),float(r['gamma_U']),float(r['lower_bound'])
        require(0<=lo<=hi<=roothi+1e-12 and math.isfinite(L) and L>=-TOL,'finite actual leaf domain/bound')
        require(r['status'] in {'open','closed','fathomed','empty','replaced','coalesced'},'qualified inherited leaf status')
        if r['parent_id']:
            require(r['parent_id'] in ids,'every actual child has an actual ledger parent')
            parent=ids[r['parent_id']];children[r['parent_id']].append(r)
            require(float(parent['gamma_L'])<=lo<=hi<=float(parent['gamma_U']) and int(r['depth'])==int(parent['depth'])+1,'actual child belongs to parent true-G domain')
        sources=set(r['lower_bound_sources'].split(';'))-{''}
        require(bool(sources) and sources<=valid_sources,'all inherited leaf bound source tokens independently recognized')
        matching=[x for x in native_records if x['leaf']==r['leaf_id']]
        if int(r['lp_complete']):
            lr=[x for x in lpstatus if x['leaf_id']==r['leaf_id']]
            require(lr and any(int(x['terminal_valid']) for x in lr),'complete leaf LP linked actual returned terminal LP')
        for token,kind in [('valid_child_target_native_bound','CHILD_BOUND_TARGET_MIP'),('valid_next_leaf_target_native_bound','NEXT_LEAF_TARGET_MIP'),('native_terminal_mip_bound','MIP')]:
            if token in sources:require(any(x['solve_kind']==kind for x in matching),'leaf native provenance has actual same-leaf successful original call '+token)
        if r['closure_source']=='native_terminal_mip_optimal':
            require(any(x['solve_kind']=='MIP' and x['native_status']=='OPTIMAL' for x in matching),'terminal leaf closure linked exact same-leaf original MIP optimum')
        if r['status']=='empty':
            require(r['closure_source']=='complete_child_lp_infeasible' and any(x['solve_kind']=='LP' and x['native_status']=='INFEASIBLE' for x in matching),'empty actual leaf linked complete returned LP infeasibility')
        bound=supported(lo,hi,proofs)
        require(min(L,U)<=bound+TOL,'every actual leaf conditional bound supported on its complete physical true-G partition')
        reason='terminal_saved_status' if r['status'] in {'closed','fathomed','empty'} else 'physical_G_floor_excludes_improvement' if lo>=U-TOL else 'qualified_whole_leaf_LB_excludes_improvement' if L>=U-TOL else None
        qualified.append(dict(leaf=r['leaf_id'],original_status=r['status'],G_interval=[lo,hi],raw_leaf_L=L,whole_scope_supported_L=bound,conditional_claim=min(L,U),discharge_reason=reason,discharged=reason is not None))
    splits=[]
    for i,parent in ids.items():
        if parent['status']!='replaced':continue
        cc=sorted(children[i],key=lambda x:float(x['gamma_L']))
        require(len(cc)>=2,'replaced parent has genuine actual children, not speculative model files')
        point=float(parent['gamma_L'])
        for child in cc:
            require(near(float(child['gamma_L']),point,1e-12),'actual child partition has neither hole nor overlap');point=float(child['gamma_U'])
        require(near(point,float(parent['gamma_U']),1e-12),'actual child partition covers the complete replaced parent')
        splits.append(dict(parent=i,children=[x['leaf_id'] for x in cc],G_interval=[float(parent['gamma_L']),point]))
    live=[r for r in leaves if r['status'] not in {'replaced','coalesced'}];point=0.
    require(bool(live),'actual complete final partition is nonempty')
    for r in sorted(live,key=lambda x:float(x['gamma_L'])):
        require(near(float(r['gamma_L']),point,1e-12),'actual complete final true-G partition has neither hole nor overlap');point=float(r['gamma_U'])
    require(near(point,roothi,1e-12) and point+TOL>=min(U,(q['V']-1)/q['V']),'final actual live partition covers the whole potentially improving true-G domain')
    events=rows(d/'external/paper_tree_events.csv');atomic=[r for r in events if r['event']=='atomic_split']
    require({r['leaf_id'] for r in atomic}=={r['parent'] for r in splits},'actual committed split events match actual replaced parent partitions')
    traces=rows(d/'external/global_bound_trace.csv');previous=-math.inf;previousU=math.inf
    for t in traces:
        upper=float(t['verified_global_upper_bound']);parts=[float(t[k]) for k in ['active_leaf_valid_lower_bound','other_open_leaf_min_valid_lower_bound'] if t[k]!=''];reported=float(t['valid_global_lower_bound'])
        require(math.isfinite(upper) and math.isfinite(reported) and near(reported,min([upper]+parts)) and reported+TOL>=previous and upper<=previousU+TOL and reported<=upper+TOL,'raw complete scheduler trace aggregation and monotonicity')
        previous=reported;previousU=upper
    relevant=[r for r in live if float(r['gamma_L'])<previousU-TOL]
    L=min((float(r['lower_bound']) for r in relevant),default=0.)
    require(traces and near(previous,min(L,previousU)) and near(L,raw['lower_bound']) and near(previousU,U),'original published raw endpoint linked final complete relevant-leaf trace without clipping')
    liveids={r['leaf_id'] for r in live};livequalified=[r for r in qualified if r['leaf'] in liveids]
    closed=all(r['discharged'] for r in livequalified)
    return L,closed,dict(root_gamma=[rootlo,roothi],same_arm_startup_physical_U=initial_U,physical_gmax=(q['V']-1)/q['V'],raw_published_final_L=L,
        unconditional_whole_root_supported_L=supported(rootlo,roothi,proofs),conditional_min_raw_L_own_U=min(L,U),live_leaves=live,
        independently_qualified_actual_leaves=qualified,actual_parent_child_partitions=splits,actual_atomic_split_events=atomic,
        whole_improving_domain_covered=True,all_relevant_closed=closed,open_relevant_leaves=sum(not r['discharged'] for r in livequalified),
        proofs=proofs,global_trace_rows=len(traces),raw_final_trace=traces[-1],genuine_active_leaf_split=bool(splits))

def audit_start_attempt(d,sp,record,models,q,p):
    meta=obj(sp)
    require(meta['model_sha256']==record['model_SHA'] and meta['leaf']==record['leaf'],'every Start attempt bound to exact actual integer call/model/leaf')
    if meta.get('submitted'):
        checked=start_check(d,sp,models[meta['model_sha256']],q,p)
        return dict(metadata_path=str(sp.relative_to(ROOT)),submitted=True,call=record['call'],source=meta['source'],native_log_SHA=record['native_log_SHA']),checked
    require(meta['status']=='ineligible:verified_start_outside_static_gini_interval','only independently proved original outside-scope Start omission admitted')
    require(not meta['mapping_complete'] and not meta['rows_valid'] and not meta['readback_valid'] and meta['checked_rows']==0 and meta['retained_model'],'outside-scope Start was not mapped, submitted or read back')
    wpath=d/'external'/(meta['source']+'_witness.json');w=obj(wpath);ph=full_physics(q,w['routes'],p)
    require(near(ph['U'],w['objective']) and near(ph['U'],meta['objective']),'skipped Start still independently replayed as actual same-arm physical witness')
    lo,hi=models[meta['model_sha256']]['bounds']['G']
    require(ph['G']<lo-1e-7 or ph['G']>hi+1e-7,'skipped Start own physical true G is outside exact saved interval')
    csvp=sp.with_name(sp.name.replace('.json','.values.csv'))
    require(not csvp.exists() and 'Loaded user MIP start' not in txt(under_root(record['native_log_path'])) and 'User MIP start' not in txt(under_root(record['native_log_path'])),'ineligible mapping produced no native submitted vector or user Start')
    return dict(metadata_path=str(sp.relative_to(ROOT)),metadata_SHA=sha(sp),submitted=False,call=record['call'],source=meta['source'],witness_SHA=sha(wpath),own_physical_G=ph['G'],own_physical_U=ph['U'],saved_G_interval=[lo,hi],reason=meta['status'],native_log_SHA=record['native_log_SHA']),None

def audit_arm(launch,identity,formal):
    if formal and (launch['number'],launch['id'],launch['seed'],launch['arm'])==(17,'G50-C2',0,'P-GRB'):
        return independent_main06_arm(launch,identity)
    d=under_root(launch['destination']);p=launch['panel'];arm=launch['arm'];label=p['id']+' '+arm
    actual=obj(d/'launch.json');raw=obj(d/'result.json');comp=obj(d/'completion.json');audit=obj(d/'audit.json')
    require(actual['command']==launch['command'] and actual['panel']==p and actual['prereg_sha256']==identity['prereg_sha256'],'actual frozen complete launch identity '+label)
    require(comp['returncode']==0 and comp['stop_reason']=='normal_return' and comp['within_cap'] and audit['passed'],'normal closed functional execution '+label)
    require(audit['binary_sha256']==production_pe_sha(),'postexit retained actual production binary SHA '+label)
    require(raw['algorithm_preset']=={'P-GRB':'custom','ENS-C':'research-round83-vds-equal-net-exchange','M-B':'research-round99-ensc-discrete-structure-m-binary'}[arm],'actual effective parser/preset identity '+label)
    q=input_file(ROOT/p['input_path']);require(sha(ROOT/p['input_path'])==p['input_sha256'] and (q['V'],q['M'],q['Q'])==(p['V'],p['M'],p['Q_vector']),'actual frozen input bytes/header '+label)
    ph=full_physics(q,raw['routes'],p);require(near(ph['U'],raw['upper_bound']) and near(ph['U'],raw['objective']) and ph['final_inventories']==raw['final_inventories'],'own final physical fleet objective and station inventory '+label)
    numerical=independent_numerical_recovery(launch,formal)
    timing=obj(d/'whole_arm_receipt.json') if formal and numerical is None else None
    complete=numerical['complete_seconds_interval'][1] if numerical else timing['complete_seconds'] if formal else comp['fully_observed_end_to_end_seconds']
    offset=complete-comp['fully_observed_end_to_end_seconds'] if formal else 0.
    require(0<=offset+1e-9 and complete<=launch['cap_seconds'],'complete arm within original cap '+label)
    if formal and numerical is None:
        require(timing['completion_SHA']==sha(d/'completion.json') and timing['audit_SHA']==sha(d/'audit.json'),'complete timing binds actual termination/audit '+label)
        require(timing['includes_admission_identity_checks_startup_native_calls_callbacks_raw_writes_postexit_audit_crosscheck'] and not timing.get('native_time_added',False),'all arm work included exactly once '+label)
    observations=obj(d/'observations.json');calls={};returns={};notstarted=set();witnesses=[];bound_events=[];timeline=[]
    computed_scope=independent_seed_scope(launch) if p['gurobi_seed']==1 else None
    set_qualified_scope(computed_scope)
    for seq,o in enumerate(observations,1):
        e=o['payload'];require(e['sequence']==o['sequence']==seq,'contiguous journal sequence '+label)
        f=d/'journal'/f'event_{seq}.json';bb=data(f);co=txt(f.with_suffix('.commit')).split()
        require(hashlib.sha256(bb).hexdigest()==o['sha256']==co[4] and json.loads(bb)==e and co[0]=='NEJ1' and int(co[1])==seq and int(co[3])==len(bb),'raw journal atomic committed exact bytes '+label)
        require(near(float(co[2]),o['data_close_seconds'],1e-9) and near(o['effective_available_seconds'],max(o['data_close_seconds'],o['first_observed_seconds']),1e-9),'actual read availability timestamps '+label)
        if e['kind']=='identity':
            require(seq==1 and e['input_sha256']==p['input_sha256'] and (e['V'],e['M'],e['T'],e['lambda'],e['pickup_seconds'],e['drop_seconds'])==(p['V'],p['M'],p['T_seconds'],p['lambda'],p['pickup_seconds'],p['drop_seconds']),'actual native identity settings '+label)
        elif e['kind']=='call':
            require(e['call'] not in calls and e['settings']==dict(read_return_code=0,**SETTINGS,Seed=p['gurobi_seed']),'every actual native call unchanged numerical parameters '+label)
            require(sha(under_root(e['model_path']))==e['model_sha256'],'every actual native call saved model bytes '+label);calls[e['call']]=e
        elif e['kind']=='returned':
            require(e['call'] in calls and e['call'] not in returns and e['return_code']==0,'successful actual native call return '+label);returns[e['call']]=seq
        elif e['kind']=='not_started':
            require(e['call'] in calls and e['call'] not in notstarted and not e['actual_Optimize'],'unique deadline skip had no native Optimize');notstarted.add(e['call'])
        elif e['kind']=='witness':
            w=full_physics(q,e['routes'],p);require(near(w['U'],e['objective']) and near(w['G'],e['G']) and near(w['P'],e['P']),'every own committed physical witness '+label)
            require(e['call']==0 or e['call'] in calls and e['call'] not in returns,'witness belongs to live same-arm call '+label)
            w.update(sequence=seq,source=e['source'],improving=e['improving'],raw_available=o['effective_available_seconds'],safe_complete_arm_available=o['effective_available_seconds']+max(0.,offset));witnesses.append(w)
        elif e['kind']=='bound':require(e['call'] in calls and e['call'] not in returns and not e['inconsistent'],'actual bound belongs to live noncontradictory same-arm call '+label);bound_events.append(e)
        elif e['kind']=='witness_rejected':pass
        else:raise AssertionError(('unexpected native event',label,e))
    require(set(calls)==set(returns)|notstarted and not set(returns)&notstarted,'every declared native call returned or genuinely skipped '+label)
    require(witnesses and near(min(w['U'] for w in witnesses),ph['U']),'final physical U from same-arm committed witnesses '+label)
    # Parse every saved model, even speculative/uncommitted child scopes.
    paths=[d/'compact.lp'] if arm=='P-GRB' else sorted((d/'external/models').glob('*.lp'))
    models={};contracts=[]
    for path in paths:
        m=model(path);digest=sha(path);models[digest]=m
        contracts.append(dict(path=str(path.relative_to(ROOT)),SHA=digest,**domain_contract(m,q,arm)))
    for c in calls.values():require(c['model_sha256'] in models,'every native call bound to saved model contract');scope_contract(c,models[c['model_sha256']],q)
    ledger=rows(d/'external/paper_optimize_ledger.csv') if arm!='P-GRB' else []
    lpstatus=rows(d/'external/lp_status_ledger.csv') if arm!='P-GRB' else []
    if ledger:require(len(ledger)==len(returns),'one actual native ledger per successful native call')
    returned_proofs={};native_records=[];lp_index=0
    for (callid,c),r in zip(((i,c) for i,c in calls.items() if i in returns),ledger if arm!='P-GRB' else [dict(model_sha256=sha(d/'compact.lp'),leaf_id='',solve_kind='MIP',native_status=raw['native_mip_status_text'],optimize_return_code=raw['native_mipopt_return_code'],native_log=str(d/'native.log'))]):
        require(callid in returns and int(r['optimize_return_code'])==0 and r['model_sha256']==c['model_sha256'],'actual native ledger matches call/model/return '+label)
        require(under_root(r['native_log'])==under_root(c['native_log_path']),'actual integer/LP native log belongs to this exact call '+label)
        if ledger:require(r['leaf_id']==c['leaf'],'actual native ledger leaf identity '+label)
        m=models[c['model_sha256']];native_log=under_root(r['native_log']);nt=txt(native_log);size=re.search(r'Optimize a model with (\d+) rows, (\d+) columns',nt)
        require(size and (int(size[1]),int(size[2]))==(len(m['rows']),len(m['bounds'])),'actual native original model size before presolve '+label)
        native_types=None;proofvalue=None
        if r['solve_kind']=='LP':
            require(not c['native_preconditions'],'LP carries relaxation identity, not integer bound identity')
            s=lpstatus[lp_index];lp_index+=1
            require(s['leaf_id']==r['leaf_id'] and s['native_status']==r['native_status'] and float(s['gamma_L'])==c['lower_g'] and float(s['gamma_U'])==c['upper_g'],'actual LP status/leaf/range linked to returned call')
            if int(s['terminal_valid']) and int(s['optimal']) and int(s['bound_available']):
                printed=re.findall(r'Optimal objective\s+([-+0-9.eE]+)',nt);proofvalue=float(s['lower_bound'])
                require(r['native_status']=='OPTIMAL' and printed and near(float(printed[-1]),proofvalue),'actual returned native LP numeric objective bound')
            elif int(s['terminal_valid']) and int(s['infeasible']):
                require(r['native_status']=='INFEASIBLE' and 'Infeasible model' in nt,'actual complete LP infeasibility terminal native log');proofvalue=c['cutoff']
        else:
            require(native_scope_qualified(c),'actual independently qualified restored integer-domain native bound call')
            match=re.search(r'Variable types: (\d+) continuous, (\d+) integer \((\d+) binary\)',nt);ct=Counter(m['types'].values())
            native_types={'C':int(match[1]),'I':int(match[2])-int(match[3]),'B':int(match[3])} if match else None
            require(native_types=={k:ct.get(k,0) for k in ['C','I','B']},'actual native pre-presolve VType restored exactly to saved model')
            printed=re.findall(r'Best objective ([^,]+), best bound ([^,]+), gap ([^\n]+)',nt)
            require(bool(printed),'actual successful native MIP final bound log')
            proofvalue=float(printed[-1][1]);require(math.isfinite(proofvalue) and abs(proofvalue)<1e90,'finite actual returned native bound')
            if r['native_status']=='OPTIMAL':require('Optimal solution found (tolerance 0.00e+00)' in nt,'actual zero requested native MIP optimum')
            elif r['native_status']=='TIME_LIMIT':require('Time limit reached' in nt,'actual normal native time limit')
            elif r['native_status']=='INTERRUPTED':require('Solve interrupted' in nt,'actual original child target interruption')
            else:raise AssertionError(('unqualified native status',r))
        if proofvalue is not None and not c['full_original']:
            require(c['cutoff']+TOL>=ph['U'],'proof cutoff qualified by same-arm final physical U')
            returned_proofs[callid]=dict(lo=c['lower_g'],hi=c['upper_g'],L=proofvalue,cutoff=c['cutoff'],sequence=returns[callid],call=callid,source='actual_returned_native_LP' if r['solve_kind']=='LP' else 'actual_returned_integer_native_final_log')
        native_records.append(dict(call=callid,leaf=c.get('leaf',''),model_SHA=c['model_sha256'],model_path=c['model_path'],native_log_path=r['native_log'],actual_read_native_log=str(native_log.relative_to(ROOT)),native_log_SHA=sha(native_log),native_status=r['native_status'],solve_kind=r['solve_kind'],return_sequence=returns[callid],native_types=native_types,returned_native_log_L=proofvalue))
    require(lp_index==len(lpstatus),'all complete LP status rows independently linked')
    plain_final=None
    if arm=='P-GRB':
        require(len(calls)==len(returns)==1 and next(iter(calls.values()))['full_original'],'one returned full original integer P call')
        require(raw['native_mip_best_bound_available'] and math.isfinite(raw['native_mip_best_bound']) and near(native_records[0]['returned_native_log_L'],raw['native_mip_best_bound']),'final plain native attribute/log bound exact-call corroboration')
        require(raw['native_mip_status_code_text_consistent'] and raw['native_mip_lifecycle_valid'],'plain final native status and lifecycle coherent')
        plain_final=dict(call=native_records[0]['call'],sequence=native_records[0]['return_sequence'],raw_final_native_L=raw['native_mip_best_bound'],printed_final_native_L=native_records[0]['returned_native_log_L'],native_log_SHA=native_records[0]['native_log_SHA'],model_SHA=native_records[0]['model_SHA'],source='returned_full_original_integer_native_final_readback_with_log_corroboration')
    # Chronological proof accumulation: final native log only exists after return.
    prior={};seenw=[];chronology=[];rejected_chronology=[];bestplain=0.;maxjournal=0.
    def remember_proof(proof):
        # All events are still individually checked. For the identical call,
        # true-G interval and cutoff, max(bound) is the strongest already
        # available proof; retaining weaker copies adds no mathematical scope.
        key=(proof['call'],proof['lo'],proof['hi'],proof['cutoff'])
        old=prior.get(key)
        if old is None or proof['L']>old['L']:prior[key]=proof
    for o in observations:
        e=o['payload'];seq=e['sequence'];kind=e['kind']
        if kind=='witness':seenw.append(next(w for w in witnesses if w['sequence']==seq))
        if kind=='returned' and e['call'] in returned_proofs:remember_proof(returned_proofs[e['call']])
        if kind=='returned' and plain_final is not None and e['call']==plain_final['call'] and numerical is None:
            require(seq==plain_final['sequence'] and maxjournal<=plain_final['raw_final_native_L']+TOL,'prior P callbacks do not contradict final returned bound')
            maxjournal=max(maxjournal,plain_final['raw_final_native_L'])
            chronology.append(dict(sequence=seq,kind='returned_original_integer_native_final_bound',call=e['call'],global_L=plain_final['raw_final_native_L'],maximum_prior_sequence=seq))
        if kind=='call' and not e['full_original']:
            cover_check(e,None,list(prior.values()),seenw)
            chronology.append(dict(sequence=seq,kind=kind,call=e['call'],prior_proof_count=len(prior),maximum_prior_sequence=max((x['sequence'] for x in prior.values()),default=0)))
        if numerical is not None and (kind=='bound' or kind=='returned' and e['call']==1):
            require(e['call']==numerical['call'],'only exact independently rejected numerical call suppressed from qualified chronology')
            rejected_chronology.append(dict(sequence=seq,kind=kind,call=e['call'],raw_payload=e,native_bound_mathematically_qualified=False,reason='known incorrect native lower claim; independently proved own full-domain floor used separately'))
        if kind=='bound':
            c=calls[e['call']]
            require(native_scope_qualified(c),'callbacks bound only independently qualified restored original integer model')
            if not c['full_original']:remember_proof(dict(lo=c['lower_g'],hi=c['upper_g'],L=e['native_bound'],cutoff=c['cutoff'],sequence=seq,call=e['call'],source='actual_same_arm_committed_integer_native_callback'))
            if e['global_available']:
                L=cover_check(c,e['native_bound'],list(prior.values()),seenw)
                require(near(L,e['global_bound'],1e-10),'independently recomputed actual native full-cover global callback bound')
                if numerical is None:
                    maxjournal=max(maxjournal,L)
                    if c['full_original']:bestplain=max(bestplain,L)
                    chronology.append(dict(sequence=seq,kind=kind,call=e['call'],global_L=L,maximum_prior_sequence=max((x['sequence'] for x in prior.values()),default=0)))
            else:require(e['global_bound'] is None,'unavailable global callback bound not used')
        require(all(x['sequence']<=seq for x in prior.values()),'never use future proof in chronological cover')
        if seenw:
            U=min(w['U'] for w in seenw)
            require(maxjournal<=U+TOL,'all chronological global bounds consistent with own physical U')
            timeline.append(dict(sequence=seq,kind=kind,raw_supervisor_available=o['effective_available_seconds'],safe_complete_arm_available=o['effective_available_seconds']+max(0.,offset),own_U=U,committed_global_L=maxjournal,signed_gap=U-maxjournal))
    start_check.calls=list(calls.values());starts=[];start_attempts=[];cover=None
    if arm=='P-GRB':
        require(len(calls)==len(returns)==1 and next(iter(calls.values()))['full_original'],'P one complete original cold compact MIP')
        require(raw['gurobi_hga_start_requested'] is False and raw['gurobi_native_domain_audit_passed'] is True and 'Loaded user MIP start' not in txt(d/'native.log'),'actual P cold, original native domain audit')
        ref=reference_path(p)
        require(sha(ref)==sha(d/'compact.lp')==p['reference']['canonical_sha256'],'current P model byte-identical own current reference')
        for key,field in [('fingerprint','gurobi_model_fingerprint'),('columns','gurobi_num_vars'),('rows','gurobi_num_constrs')]:require(raw[field]==p['reference'][key],'P original native reference '+key)
        require(raw['native_mip_lifecycle_valid'] and raw['native_mip_solver_finalization_reached'] and raw['native_mip_problem_freed'] and raw['native_mip_environment_closed'] and raw['native_mip_mipopt_count']==1,'actual P native model/environment finalized')
        require(raw['native_mip_best_bound_available'] and near(raw['native_mip_best_bound'],raw['lower_bound']) and bestplain<=raw['lower_bound']+TOL and near(native_records[0]['returned_native_log_L'],raw['lower_bound']),'P exact final attribute/log/return linkage with all prior callbacks consistent')
        L=numerical['independently_qualified_own_full_domain_L'] if numerical else raw['native_mip_best_bound'];cert=raw['native_mip_status_text']=='OPTIMAL' and ph['U']-L<=TOL
        if numerical:
            require(not cert and raw['strict_certified_original_problem'] is False,'own P remains uncertified after rejection of invalid lower claim')
    elif ph['U']<=ZERO and not calls:
        require(p['lambda']>=0 and all(x>=0 for x in q['weights'][1:]),'zero own physical U and globally nonnegative original objective')
        L=0.;cert=True;cover=dict(independent_nonnegative_objective_floor=True,whole_improving_domain_covered=True,all_relevant_closed=True,open_relevant_leaves=0)
    else:
        initial=obj(d/'external/initial_witness.json');initialph=full_physics(q,initial['routes'],p)
        require(near(initialph['U'],initial['objective']),'actual original same-run startup physical U0')
        L,closed,cover=final_partition(d,q,initialph['U'],ph['U'],list(prior.values()),native_records,lpstatus,raw)
        reason=raw['external_gini_tree_failure_reason']
        require(reason=='none' or reason=='overall_global_deadline' and raw['status'] in ['time_limit','round31_c6_external_gini_tree_time_limit'],'only inherited legal overall time-window termination')
        for flag in ['root_coverage_valid','parent_child_coverage_valid','all_leaf_bounds_valid','leaf_bounds_monotone','global_bound_monotone','lifecycle_complete','feasibility_consistency_gate']:require(raw['external_gini_tree_'+flag] is True,'original complete native/tree lifecycle corroboration '+flag)
        cert=closed and ph['U']-L<=TOL
        integer_calls=[r for r in native_records if r['solve_kind']!='LP']
        expected={under_root(r['native_log_path']+'.round68.start.json'):r for r in integer_calls}
        require(set(expected)==set((d/'external/native_logs').glob('*.round68.start.json')),'all Start mapping attempts correspond exactly to actual integer calls')
        for sp,record in expected.items():
            attempt,submitted=audit_start_attempt(d,sp,record,models,q,p);start_attempts.append(attempt)
            if submitted is not None:starts.append(submitted)
        require(len(starts)==sum(x['submitted'] for x in start_attempts),'actual submitted Starts counted separately from complete mapping attempts')
        cover['native_final_proofs']=list(returned_proofs.values())
    require(math.isfinite(L) and L<=ph['U']+TOL,'finite independently qualified noncontradictory endpoint L')
    require(cert==raw['strict_certified_original_problem'],'own complete certificate agrees with serialized flag only after proof')
    gap=ph['U']-L
    require(gap>TOL or cert,'numerical closure cannot silently bypass certificate obligations')
    improved=[];best=math.inf
    for w in witnesses:
        if w['U']<best:
            improved.append(w);best=w['U']
    result=dict(id=p['id'],seed=p['gurobi_seed'],panel_kind=launch.get('panel_kind',launch.get('stage')),arm=arm,U=ph['U'],L=L,gap=gap,relative_gap=gap/abs(ph['U']) if abs(ph['U'])>ZERO else None,
        numbers_qualified=True,certificate_qualified=True,certificate=cert,complete_seconds=complete,PE_SHA=production_pe_sha(),DLL_SHA=native_dll_sha(),
        complete_receipt=timing,normal_completion=comp,raw_status=raw['status'],raw_tree_termination_reason=raw.get('external_gini_tree_failure_reason'),
        physical=ph,new_physical_UBs=improved,all_physical_witnesses=witnesses,total_physical_witnesses=len(witnesses),native_records=native_records,model_contracts=contracts,
        starts=starts,start_attempts=start_attempts,cover=cover,plain_returned_final_bound=plain_final,journal_event_count=len(observations),chronological_native_cover_events=len(chronology),
        chronological_cover_max_support_sequence_le_event=True,all_journal_commits_exact=True,availability_offset_seconds=max(0.,offset),
        availability_offset_is_upper_bound_unknown_prelaunch=True,availability_exact_first_discovery=False,independent_computed_Seed1_scope=computed_scope,
        bindings={n:sha(d/n) for n in ['launch.json','result.json','completion.json','audit.json','observations.json','native.log']},actual_full_argv=actual['command'])
    if not formal and audit.get('reader_only_recovery',False) and not (d/'whole_arm_receipt.json').exists():
        result['complete_seconds']=None
        result['complete_qualification_clock']='unknown; supervisor/native legacy times retained but not full qualification arm'
    if numerical:
        result.update(complete_seconds=None,complete_seconds_interval=numerical['complete_seconds_interval'],independent_numerical_recovery=numerical,
            native_bounds_mathematically_qualified=False,lower_bound_source='independently_proved_own_original_full_domain_nonnegative_floor',rejected_raw_native_chronology=rejected_chronology)
        require(not chronology and len(rejected_chronology)==4,'all3callback and finalreturned native bound events excluded from qualified chronology')
        for record in native_records:record['native_bounds_mathematically_qualified']=False
        plain_final['native_bound_mathematically_qualified']=False
    result['checkpoints']=independent_checkpoints(result,launch,timeline) if formal else []
    save(DEST/(p['id']+'_seed'+str(p['gurobi_seed'])+'_'+arm.replace('-','_')+'_timeline.json'),timeline)
    save(DEST/(p['id']+'_seed'+str(p['gurobi_seed'])+'_'+arm.replace('-','_')+'_cover_chronology.json'),chronology)
    milestones.append(label);print(json.dumps(dict(completed=label,U=ph['U'],L=L,gap=gap,certificate=cert,complete_seconds=result['complete_seconds'],complete_seconds_interval=result.get('complete_seconds_interval'),events=len(observations))),flush=True)
    return result,models,q
