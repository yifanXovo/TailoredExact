"""Prospectively freeze algorithms and once-only archived-source draws."""
from round163_common import *
import collections, copy, csv, dataclasses, math

FAMILY='round163-gi-tbc-eplus-prospective-v1'
SPECS=[('R163-C20-S','CITI',20,'shortage','compact',1,5400,1200),
       ('R163-B20-B','CABI',20,'balanced','regional',1,7200,1200),
       ('R163-X20-S','DIVVY',20,'shortage','compact',2,5400,1200),
       ('R163-C35-U','CITI',35,'surplus','regional',2,10800,2400),
       ('R163-B35-S','CABI',35,'shortage','compact',1,7200,2400),
       ('R163-X35-S','DIVVY',35,'shortage','regional',2,10800,2400)]
ORDERS=[['P','B','Eplus'],['B','Eplus','P'],['Eplus','P','B']]*2
GEN=['scripts/round163_setup.py','scripts/round137_setup.py','scripts/round122_data.py',
     'scripts/round109_data.py','scripts/round118_data.py','scripts/generate_citibike443_regional_v1.py']

def init():
    assert not (OUT/'source_recipe.json').exists()
    assert sha(PE)==PE_SHA and sha(DLL)==DLL_SHA
    source=read(ROOT/'results/unified_exact_round162/complete_candidate_manifest.json')
    helpers=read(ROOT/'results/unified_exact_round162/helper_manifest_Eplus.json')
    for n,h in helpers['helper_dependencies'].items():assert sha(ROOT/n)==h,n
    assert sha(PYTHON)==helpers['python_SHA']
    (OUT/'helper_manifest_Eplus.json').write_bytes((ROOT/'results/unified_exact_round162/helper_manifest_Eplus.json').read_bytes())
    # The inherited no-Gurobi stub repair is excluded from the measured PE.
    current={n:sha(ROOT/n) for n in source['source_hashes']}
    diffs={n:dict(measured=h,current=current[n]) for n,h in source['source_hashes'].items() if h!=current[n]}
    assert set(diffs)=={'src/Round160PhysicalNeighborhoodStub.cpp'}
    write(OUT/'candidate_manifest.json',dict(schema='round163-reused-common-production-v1',UTC=utc(),
        base=BASE,source_commit=MEASURED_CPP,production_PE=str(PE),research_PE=str(PE),production_PE_SHA=PE_SHA,research_PE_SHA=PE_SHA,
        DLL=str(DLL),DLL_SHA=DLL_SHA,source_hashes=current,measured_source_hashes=source['source_hashes'],
        excluded_non_Gurobi_stub_difference=diffs,rebuild=False,actual_files_hashed=True,
        inherited_build_manifest=dict(commit=BASE,path='results/unified_exact_round162/complete_candidate_manifest.json',SHA256=sha(ROOT/'results/unified_exact_round162/complete_candidate_manifest.json')),
        optimization_numerical_and_solver_policy_unchanged=True))
    for p in ['results/unified_exact_round116/projection_contract.json']:
        materialize(p)
    matrix=read(ROOT/'results/unified_exact_round137/matrix_frozen.json')
    oldp=next(g['launch'] for g in matrix['groups'] if g['launch']['method']=='P' and g['launch']['seed']==0)
    ptemplate=[v.replace(oldp['destination'],'${destination}') for v in oldp['command']]
    ptemplate[0]='${exe}'
    for f,v in {'--input':'${input}','--lambda':'${lambda}','--T':'${T}',
        '--time-limit':'${native_limit}','--process-wall-time-limit':'${cap}',
        '--round24-expected-gurobi-model-fingerprint':'${fingerprint}',
        '--round24-executable-sha256':'${PE_SHA}','--round24-manifest-executable-sha256':'${PE_SHA}'}.items():
        ptemplate[ptemplate.index(f)+1]=v
    b=read(ROOT/'config/gi_tbc_round137.json')
    e=read(ROOT/'config/gi_tbc_proof_floor_round156.json')
    write(OUT/'method_freeze.json',dict(UTC=utc(),B=b,Eplus=e,P_template=ptemplate,P_authority=dict(
        commit=BASE,path='results/unified_exact_round137/matrix_frozen.json',SHA256=sha(ROOT/'results/unified_exact_round137/matrix_frozen.json'),arm_id=oldp['arm_id']),
        runtime_manifest_SHA256=sha(OUT/'candidate_manifest.json'),helper_manifest_SHA256=sha(OUT/'helper_manifest_Eplus.json'),
        helper_entry='scripts/round156_online.py',helper_SHA256=sha(ROOT/'scripts/round156_online.py'),
        helper_interface_change='absolute root/manifest paths only; helper bytes, closure, arithmetic, capacity and affinity unchanged',
        rn_nodes=16384,price_absolute_gap=1e-4,old_joint=True,DP_and_fallback=True,root_once=True,global_deadline=True,
        Seed=0,Threads=1,MIPThreads=1,MIPFocus=0,Cuts=-1,Presolve=-1,requested_gaps=0,H_seed=20260626,
        affinity_mask=4,all_non_candidate_R138_R162_mechanisms_off=True,Native_NodeLimit='unlimited',
        same_PE_for_all=True,cold_P_NumStart=0,no_cross_arm_start_H_floor_or_source=True,
        Eplus_placement='qualified proof ledger only; no formal Native row, raw AM, hint, Start or branching change',
        one_production_deadline=True,native_limit_offset=6,outer_hard_stop_offset=2,shutdown_margin=30,
        scope='archived-source prospective configurations; no stable default change'))
    source_files=['results/data_generation_citibike_round57/source_station_table.csv',
        'results/unified_exact_round116/source/source_station_table.csv','results/unified_exact_round116/source/snapshot.json',
        'results/unified_exact_round116/source/row_decisions.json','results/unified_exact_round116/projection_contract.json',
        'results/unified_exact_round116/source/requests/station_information/01.response',
        'results/unified_exact_round132/source/DIVVY/qualified_stations.json','results/unified_exact_round132/source/DIVVY/snapshot.json',
        'results/unified_exact_round132/source/DIVVY/station_information.json']
    write(OUT/'source_recipe.json',dict(UTC=utc(),base=BASE,family=FAMILY,specs=SPECS,method_orders=ORDERS,
        selection_id_rule='r163_'+ '${instance_id}; collision k>0 appends _collision_k before landscape',
        source_family_rule="family+'|source='+source+'|source_sha256='+identity_SHA; collision k>0 appends '|collision=k'",
        anchors='unchanged R137/R57 four anchors: compact rep1/2 slots0/1; regional rep1/2 slots2/3; hash-first, then farthest-first',
        pool='original qualified source quality; 0<capacity<100; exclude earlier accepted source rows within this six-draw panel',
        inventory='unchanged R109/R122 target, landscape, total adjustment, sign repair and serialization',
        vehicles={'20':[30,30],'35':[20,25,30]},rho=1,pickup_seconds=60,drop_seconds=60,lambda_rule='1/sum(actual serialized non-depot weights)',
        generation_dependencies={n:sha(ROOT/n) for n in GEN},source_files={n:sha(ROOT/n) for n in source_files},
        before_any_H_DP_RN_or_Optimize=True,novelty_keys=['order-invariant base n/M/Q + depot/station coordinates/capacity/b/D/w','base + T/lambda/tp/td'],
        collision_rule='retain every attempt; same row, eligible pool and configuration; family |collision=k and selection_id _collision_k; first legal non-colliding input kept',
        never_select_on_difficulty_or_performance=True,all_six_groups_unconditional=True,nominal_seconds=32400,
        conservative_reservation_seconds=48600,total_science_seconds=TOTAL,qualification_plan_seconds=3600,
        decision_order=['correctness and evidence','certificates','paid times on joint CERT subset','both U/L endpoints and costs on OPEN'],
        no_extra_seed_parameter_grid_or_candidate=True))
    print('Algorithm/dependency and source recipe prepared; commit before generate. Optimize/H/DP/RN=0')

def canonical(parsed,config=None):
    def num(v):return float(v).hex()
    rows=sorted((num(parsed['points'][i][0]),num(parsed['points'][i][1]),int(parsed['capacities'][i]),
                 int(parsed['initial'][i]),int(parsed['target'][i]),num(parsed['weights'][i])) for i in range(1,parsed['V']+1))
    body=dict(n=parsed['V'],M=parsed['M'],Q=sorted(parsed['Q']),depot=list(map(num,parsed['points'][0])),stations=rows)
    key=lambda v:hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    base=key(body)
    if config is None:return base,None
    return base,key(dict(base=base,T=num(config['T_seconds']),lam=num(config['lambda']),tp=num(config.get('pickup_seconds',60)),td=num(config.get('drop_seconds',60))))

def history():
    """Read manifests and their small text inputs from Git; never unpack historical raw."""
    import generate_citibike443_regional_v1 as old
    allnames=git('ls-tree','-r','--name-only',BASE).decode().splitlines()
    files=set(allnames);manifests=[n for n in allnames if n.endswith('input_manifest.json')]
    index={};parsed_cache={};manifest_records=[];unresolved=[];overlap=[]
    def walk(v):
        if isinstance(v,dict):
            yield v
            for q in v.values():yield from walk(q)
        elif isinstance(v,list):
            for q in v:yield from walk(q)
    def resolve(v):
        s=v.replace('\\','/')
        for prefix in ['results/','reference/','instances/','testdata/']:
            i=s.find(prefix)
            if i>=0 and s[i:] in files:return s[i:]
        return s if s in files else None
    for name in manifests:
        raw=git('show',BASE+':'+name);obj=json.loads(raw)
        manifest_records.append(dict(path=name,commit=BASE,SHA256=hashlib.sha256(raw).hexdigest(),bytes=len(raw)))
        for p in walk(obj):
            candidates=[(k,v) for k,v in p.items() if isinstance(v,str) and v.lower().endswith('.txt') and ('path' in k or k in ('input','instance'))]
            for k,v in candidates:
                path=resolve(v)
                if not path:
                    unresolved.append(dict(manifest=name,field=k,path=v));continue
                if path not in parsed_cache:
                    raw_input=git('show',BASE+':'+path)
                    local=TEMP/'novelty_inputs'/hashlib.sha256(raw_input).hexdigest();local.parent.mkdir(parents=True,exist_ok=True)
                    local.write_bytes(raw_input)
                    try:parsed_cache[path]=old.parse_instance_mirror(local)
                    except (ValueError,IndexError):parsed_cache[path]=None
                parsed=parsed_cache[path]
                if parsed is None:
                    unresolved.append(dict(manifest=name,path=path,reason='not R57 text schema'));continue
                config=p if all(x in p for x in ('T_seconds','lambda')) else None
                bk,fk=canonical(parsed,config)
                record=dict(input=path,manifest=name,id=p.get('id'),base_key=bk,full_key=fk)
                index.setdefault(bk,[]).append(record)
            s=p.get('selection_path')
            if isinstance(s,str) and resolve(s):
                value=json.loads(git('show',BASE+':'+resolve(s)))
                rows=value.get('selected_source_station_row_indices')
                if rows is not None:
                    overlap.append(dict(id=p.get('id'),manifest=name,selection=resolve(s),source=p.get('source','CITI' if 'round109/' in name else None),rows=rows))
    write(OUT/'history_input_index.json',dict(UTC=utc(),commit=BASE,manifests=manifest_records,normalized_base_keys=index,
        historical_source_selections=overlap,distinct_text_inputs=len(parsed_cache),unresolved=unresolved,
        full_keys_available_only_with_actual_T_lambda=True,raw_carriers_recovered=0,Optimize=0))
    print(json.dumps(dict(manifests=len(manifests),inputs=len(parsed_cache),base_keys=len(index),unresolved=len(unresolved))))

def generate():
    import generate_citibike443_regional_v1 as old
    import round109_data as land
    source=legacy_import('round122_data')
    recipe=read(OUT/'source_recipe.json');assert not (OUT/'input_manifest.json').exists()
    assert json.loads(git('show','HEAD:results/unified_exact_round163/source_recipe.json'))==recipe
    for n,h in recipe['generation_dependencies'].items():assert sha(ROOT/n)==h,n
    for n,h in recipe['source_files'].items():assert sha(ROOT/n)==h,n
    sets=source.load_sources()
    sets['DIVVY']=[source.cabi.Station(q['source_row_index'],q['station_id'],q['capacity'],q['x'],q['y'],q['latitude'],q['longitude'],tuple(q['original_row_indices']))
        for q in read(ROOT/'results/unified_exact_round132/source/DIVVY/qualified_stations.json')]
    ids={s:p['identity_SHA'] for s,p in source.SOURCES.items()}
    ids['DIVVY']=sha(ROOT/'results/unified_exact_round132/source/DIVVY/station_information.json')
    h=read(OUT/'history_input_index.json');keys=h['normalized_base_keys'];used=collections.defaultdict(set);roles=[];attempts=[];overlaps=[]
    for (name,s,n,inventory,geometry,rep,T,cap) in SPECS:
        stations=sets[s];pool=[q for q in stations if 0<q.capacity<100 and q.source_row_index not in used[s]]
        k=0
        while True:
            family=FAMILY+f'|source={s}|source_sha256={ids[s]}'+(f'|collision={k}' if k else '')
            selection_id='r163_'+name+(f'_collision_{k}' if k else '')
            old.FAMILY=family;land.VERSION=family;land.SOURCE_SHA=ids[s]
            selection=old.build_selection(pool,n,geometry,rep)
            selection.update(selection_id=selection_id,source=s,coordinate_CRS='EPSG:32616' if s=='DIVVY' else 'EPSG:32618',
                excluded_previous_new_rows=sorted(used[s]),pool_source_rows=[q.source_row_index for q in pool])
            v=land.landscape(selection,inventory,stations);land.assert_equivalent(selection,inventory,stations,v)
            Q=[30,30] if n==20 else [20,25,30];M=len(Q)
            lines=old.instance_text(v,M,Q[0]).splitlines();lines[0]=f'{n} {M} {json.dumps(Q)}'
            dest=OUT/'inputs'/name/(f'collision_{k}' if k else 'first')/'instance.txt';dest.parent.mkdir(parents=True,exist_ok=True)
            with dest.open('x',encoding='utf-8',newline='\n') as f:f.write('\n'.join(lines).rstrip()+'\n')
            parsed=old.parse_instance_mirror(dest)
            assert (parsed['V'],parsed['M'],parsed['Q'])==(n,M,Q)
            c,b,D,w=[parsed[a][1:] for a in ['capacities','initial','target','weights']]
            assert all(0<=x<=cc and 0<dd<=cc<100 for cc,x,dd in zip(c,b,D))
            assert all(math.isfinite(x) and x>=0 for x in w) and sum(w)>0
            assert any(x>y for x,y in zip(b,D)) and any(x<y for x,y in zip(b,D))
            assert (sum(b)<sum(D))==(inventory=='shortage') and (sum(b)>sum(D))==(inventory=='surplus')
            assert all(math.isfinite(x) for point in parsed['points'] for x in point)
            Omega=sum(w);lam=1/Omega
            config=dict(T_seconds=T,**{'lambda':lam},pickup_seconds=60,drop_seconds=60)
            bk,fk=canonical(parsed,config);collision=bk in keys
            for suffix,value in [('selection',selection),('landscape',v),('parsed',parsed),('source_mapping',
                [dict(local_station_index=j,source_identity_SHA256=ids[s],**dataclasses.asdict(next(q for q in stations if q.source_row_index==i))) for j,i in enumerate(selection['selected_source_station_row_indices'],1)])]:
                write(dest.with_name(suffix+'.json'),value)
            attempts.append(dict(id=name,k=k,family=family,selection_id=selection_id,input=dest.relative_to(ROOT).as_posix(),
                SHA256=sha(dest),base_key=bk,full_key=fk,collision=collision,historical_collisions=keys.get(bk,[])))
            if not collision:break
            k+=1
        selected=set(selection['selected_source_station_row_indices']);assert not used[s]&selected;used[s]|=selected
        p=dict(id=name,base_id=name,V=n,M=M,source=s,inventory=inventory,geometry=geometry,replicate=rep,Q_vector=Q,
            input_path=dest.relative_to(ROOT).as_posix(),instance_path=dest.relative_to(ROOT).as_posix(),input_sha256=sha(dest),
            selection_path=dest.with_name('selection.json').relative_to(ROOT).as_posix(),landscape_path=dest.with_name('landscape.json').relative_to(ROOT).as_posix(),
            source_identity_SHA=ids[s],selection_id=selection_id,family=family,cap_seconds=cap,gurobi_seed=0,
            Omega=Omega,sum_weights=Omega,rho=1,lambda_decimal17=format(lam,'.17g'),lambda_binary64=lam.hex(),
            total_initial=sum(b),total_target=sum(D),total_capacity=sum(c),shortage=sum(D)-sum(b),**config,
            normalized_base_key=bk,normalized_full_key=fk,known=False,exposed=False,
            round137_delete_ab=False,panel_kind='Round163 prospective new configuration on archived sources')
        for previous in h['historical_source_selections']:
            if previous['source']==s:
                common=sorted(selected&set(previous['rows']))
                overlaps.append(dict(id=name,old_id=previous['id'],old_manifest=previous['manifest'],old_selection=previous['selection'],
                    source=s,overlap_rows=common,overlap_count=len(common),fraction_of_new=len(common)/n))
        keys[bk]=[dict(input=p['input_path'],id=name,base_key=bk,full_key=fk,manifest='Round163')];roles.append(p)
    write(OUT/'generation_attempts.json',attempts)
    write(OUT/'source_overlap.json',overlaps)
    write(OUT/'input_manifest.json',dict(UTC=utc(),roles=roles,recipe_commit=git('rev-parse','HEAD').decode().strip(),
        source_recipe_SHA256=sha(OUT/'source_recipe.json'),history_index_SHA256=sha(OUT/'history_input_index.json'),
        generation_once=True,Optimize=0,H=0,DP=0,RN=0,no_performance_screening=True,source_rows_disjoint_within_panel=True,
        historical_base_and_full_key_collisions=False,collision_attempts=sum(a['collision'] for a in attempts),
        scope='prospective new configurations on archived sources; synthetic demand; not new cities, IID distribution or external observed-demand validation'))
    print(json.dumps([dict(id=p['id'],T=p['T_seconds'],lam=p['lambda'],Omega=p['Omega'],shortage=p['shortage'],SHA256=p['input_sha256']) for p in roles]))

if __name__=='__main__':globals()[sys.argv[1]]()
