"""Six preregistered once-only draws; original R57/R109 mathematics."""
from round122_common import *
import copy, csv, dataclasses, math, statistics
import round118_data as cabi
import round109_data as landscape_math
import generate_citibike443_regional_v1 as old

CITI_SHA='9f9aad24e61d661971c24c6f5ec78a69081edf01ffc433563e52a70b2eaca2d0'
SOURCES={'CITI':dict(identity_SHA=CITI_SHA,table_SHA=CITI_SHA,rows=443,qualified=442),
    'CABI':dict(identity_SHA=cabi.RAW_SHA,table_SHA=cabi.TABLE_SHA,rows=865,qualified=865)}
VERSION='round122-thin-offline-adapter-v1'
REF=ROOT/'reference/round122_paper_benchmark'
ROLES=[dict(id='PB-C20-B',source='CITI',V=20,M=2,geometry='compact',replicate=1,inventory='balanced',Q_vector=[30,30],T_seconds=3600,cap_seconds=900,selection_id='citi_r122_V20_compact_r1'),
    dict(id='PB-B20-S',source='CABI',V=20,M=2,geometry='regional',replicate=2,inventory='shortage',Q_vector=[20,40],T_seconds=7200,cap_seconds=900,selection_id='cabi_r122_V20_regional_r2'),
    dict(id='PB-C35-U',source='CITI',V=35,M=3,geometry='regional',replicate=1,inventory='surplus',Q_vector=[20,25,30],T_seconds=10800,cap_seconds=2400,selection_id='citi_r122_V35_regional_r1'),
    dict(id='PB-B35-B',source='CABI',V=35,M=3,geometry='compact',replicate=2,inventory='balanced',Q_vector=[25,25,25],T_seconds=7200,cap_seconds=2400,selection_id='cabi_r122_V35_compact_r2'),
    dict(id='PB-C50-S',source='CITI',V=50,M=4,geometry='compact',replicate=1,inventory='shortage',Q_vector=[30,30,30,30],T_seconds=10800,cap_seconds=3600,selection_id='citi_r122_V50_compact_r1'),
    dict(id='PB-B50-U',source='CABI',V=50,M=4,geometry='regional',replicate=2,inventory='surplus',Q_vector=[20,25,35,40],T_seconds=18000,cap_seconds=3600,selection_id='cabi_r122_V50_regional_r2')]
ORDERS=[['P-GRB','ENS-C','M-B','MB-D1'],['ENS-C','M-B','MB-D1','P-GRB'],['M-B','MB-D1','P-GRB','ENS-C'],
    ['MB-D1','P-GRB','ENS-C','M-B'],['MB-D1','M-B','ENS-C','P-GRB'],['P-GRB','MB-D1','M-B','ENS-C'],
    ['ENS-C','P-GRB','MB-D1','M-B'],['M-B','ENS-C','P-GRB','MB-D1']]
for p in ROLES:p.update(pickup_seconds=60,drop_seconds=60,**{'lambda':.15},gurobi_seed=0,panel_kind='new_problem_Seed0')

def family(source):return f'round122-paper-benchmark-v1|source={source}|source_sha256='+SOURCES[source]['identity_SHA']
def configure(source):
    f=family(source);old.FAMILY=f;landscape_math.VERSION=f;landscape_math.SOURCE_SHA=SOURCES[source]['identity_SHA']
    assert old.GEOGRAPHIC_REGIMES==('compact','regional') and old.REPLICATES==(1,2)
    assert old.COORD_DECIMALS==3 and old.WEIGHT_DECIMALS==6

def load_sources():
    landscape_math.SOURCE_SHA=CITI_SHA
    return {'CITI':landscape_math.load(ROOT),'CABI':cabi.source_check()}

def selection(stations,p):
    configure(p['source']);s=old.build_selection(stations,p['V'],p['geometry'],p['replicate'])
    s.update(schema='round122-geographic-selection-v1',selection_id=p['selection_id'],generator_version=VERSION)
    return s

def landscape(s,stations,p):
    configure(p['source']);v=landscape_math.landscape(s,p['inventory'],stations)
    landscape_math.assert_equivalent(s,p['inventory'],stations,v)
    assert v['dataset_family']==family(p['source']) and v['seed_derivation_material'].startswith(family(p['source'])+'|')
    v.update(schema='round122-station-landscape-v1',generator_version=VERSION,
        source_hashes={'source_identity_SHA256':SOURCES[p['source']]['identity_SHA'],'safe_table_SHA256':SOURCES[p['source']]['table_SHA']})
    return v

def fixed_roles(roles):
    groups=copy.deepcopy(roles)+[copy.deepcopy(roles[3]),copy.deepcopy(roles[4])]
    for j,(p,order) in enumerate(zip(groups,ORDERS),1):
        p.update(group_number=j,gurobi_seed=int(j>6),method_order=order)
        if j>6:p['panel_kind']='fixed_input_Seed1_sensitivity'
    return groups

def freeze():
    assert not REF.exists() and not (OUT/'source_recipe.json').exists()
    deps=['scripts/round122_data.py','scripts/round118_data.py','scripts/round109_data.py','scripts/generate_citibike443_regional_v1.py']
    write(OUT/'source_recipe.json',dict(round=122,base=BASE,UTC=utc(),sources=SOURCES,families={s:family(s) for s in SOURCES},roles=ROLES,
        full_fixed_running_table=fixed_roles(ROLES),generation_dependencies={n:sha(ROOT/n) for n in deps},
        source_loader='CITI R109 load (C++/R57 row semantics); CABI R118 source_check only, no wrapper configure',
        four_original_anchors_hash_order_ties=True,target_fraction=[.44,.56],coordinates_decimals=3,weights_decimals=6,
        delta='max(V,floor(.12*sum(D)+.5))',local_perturbation={'balanced':.18,'other':.30},
        original_total_correction_sign_repair_max_normalization_and_centroid=True,
        only_instance_first_line_replaced_by_actual_Q_vector=True,generated_input_count=0,no_network_or_reprojection=True,
        no_difficulty_filter=True,no_redraw=True,formal_arms=32,formal_pairs=48,nominal_seconds=79200,management_reference=960,
        total_limit_seconds=TOTAL_LIMIT,qualification_soft_seconds=QUAL_PLAN,qualification_authorized_seconds=QUAL_LIMIT,
        no_V60_V100_or_additional_research_input=True))
    print('Six-input recipe, adapter and complete eight-group table frozen before generation; commit required')

def generate():
    tick=time.perf_counter();recipe=read(OUT/'source_recipe.json');assert not REF.exists()
    for n,h in recipe['generation_dependencies'].items():assert sha(ROOT/n)==h
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()
    for n in ['scripts/round122_data.py','results/unified_exact_round122/source_recipe.json']:
        committed=subprocess.check_output(['git','show',commit+':'+n],cwd=ROOT)
        assert committed.replace(b'\r\n',b'\n')==(ROOT/n).read_bytes().replace(b'\r\n',b'\n'),'commit recipe before generating'
    stations=load_sources();history=read(ROOT/'results/unified_exact_round116/historical_input_hash_index.json')['SHA_to_paths']
    oldroles=[]
    for rn in [109,116,118,121]:
        m=read(ROOT/f'results/unified_exact_round{rn}/input_manifest.json')
        for p0 in m.get('roles',[]):
            if p0.get('input_sha256'):history.setdefault(p0['input_sha256'],[]).append(p0['input_path'])
            if p0.get('selection_path') and p0.get('V',100)<=50:
                oldroles.append((rn,p0,'CITI' if rn==109 or rn==121 and p0['id'] in ['F2','R98-C2'] else 'CABI'))
    REF.mkdir(parents=True,exist_ok=False);roles=[];overlaps=[]
    for p0 in ROLES:
        p=copy.deepcopy(p0);ss=stations[p['source']];s=selection(ss,p);v=landscape(s,ss,p)
        lines=old.instance_text(v,p['M'],p['Q_vector'][0]).splitlines();lines[0]=f"{p['V']} {p['M']} {json.dumps(p['Q_vector'])}"
        path=REF/(p['id']+'.txt')
        with path.open('x',encoding='utf-8',newline='\n') as f:f.write('\n'.join(lines).rstrip()+'\n')
        digest=sha(path);parsed=old.parse_instance_mirror(path)
        for suffix,obj in [('selection',s),('landscape',v),('parsed',parsed)]:write(REF/(p['id']+'_'+suffix+'.json'),obj)
        by={q.source_row_index:q for q in ss}
        mapping=[dict(local_station_index=j,source=p['source'],**dataclasses.asdict(by[i]),source_identity_SHA=SOURCES[p['source']]['identity_SHA']) for j,i in enumerate(s['selected_source_station_row_indices'],1)]
        write(REF/(p['id']+'_source_mapping.json'),mapping)
        if digest in history:
            write(OUT/'duplicate_failure.json',dict(id=p['id'],input_SHA=digest,existing=history[digest],record_retained=True,no_redraw=True))
            raise RuntimeError('DATA_IDENTITY_BLOCKED: exact duplicate, no redraw')
        history[digest]=[path.relative_to(ROOT).as_posix()]
        assert (parsed['V'],parsed['M'],parsed['Q'])==(p['V'],p['M'],p['Q_vector'])
        assert len(set(s['selected_source_station_row_indices']))==p['V']
        assert all(0<=b<=c and 0<d<=c for b,c,d in zip(v['initial'],v['capacities'],v['target']))
        assert all(w>0 for w in v['weights']) and max(v['weights'])==1
        assert v['depot']['coordinate_utm18n_meters']==[round(statistics.fmean(q[j] for q in parsed['points'][1:]),3) for j in range(2)]
        chosen=set(s['selected_source_station_row_indices'])
        for rn,previous,source in oldroles:
            if source==p['source']:
                prev=read(ROOT/previous['selection_path'])['selected_source_station_row_indices']
                overlaps.append(dict(id=p['id'],source=source,old_round=rn,old_id=previous['id'],old_V=previous['V'],new_V=p['V'],overlap=len(chosen&set(prev))))
        for previous in roles:
            if previous['source']==p['source']:
                prev=read(ROOT/previous['selection_path'])['selected_source_station_row_indices']
                overlaps.append(dict(id=p['id'],source=p['source'],old_round=122,old_id=previous['id'],old_V=previous['V'],new_V=p['V'],overlap=len(chosen&set(prev))))
        ratios=[b/d for b,d in zip(v['initial'],v['target'])];S=sum(ratios)
        G=sum(abs(x-y) for i,x in enumerate(ratios) for y in ratios[i+1:])/(p['V']*S) if S else 0.
        penalty=sum(w*abs(r-1) for w,r in zip(v['weights'],ratios))
        p.update(input_path=path.relative_to(ROOT).as_posix(),instance_path=path.relative_to(ROOT).as_posix(),input_sha256=digest,input_bytes=path.stat().st_size,
            selection_path=(REF/(p['id']+'_selection.json')).relative_to(ROOT).as_posix(),landscape_path=(REF/(p['id']+'_landscape.json')).relative_to(ROOT).as_posix(),
            source_identity_SHA=SOURCES[p['source']]['identity_SHA'],total_initial=sum(v['initial']),total_target=sum(v['target']),total_capacity=sum(v['capacities']),
            sum_weights=sum(v['weights']),lambda_sum_weights=.15*sum(v['weights']),
            empty_fleet=dict(physically_feasible=True,G=G,P=penalty,lambda_P=.15*penalty,F=G+.15*penalty,duration=0,all_loads=0))
        roles.append(p)
    h=copy.deepcopy(read(ROOT/'results/unified_exact_round121/input_manifest.json')['qualification_roles'][0])
    h.update(gurobi_seed=1,method_order=METHODS,panel_kind='qualification',cap_seconds=120)
    write(OUT/'input_manifest.json',dict(roles=fixed_roles(roles),new_roles=roles,qualification_roles=[h],families={s:family(s) for s in SOURCES},
        sources=SOURCES,source_recipe_SHA=sha(OUT/'source_recipe.json'),recipe_commit_before_generation=commit,generated_once=True,
        new_problem_denominator=6,fixed_input_Seed1_blocks=2,formal_arm_denominator=32,overlaps=overlaps,
        exact_historical_SHA_duplicates=False,not_factorial_not_IID_not_six_cities=True))
    write(OUT/'generation_receipt.json',dict(UTC=utc(),recipe_commit=commit,unique_input_files_written=6,
        no_H_LP_MIP_or_difficulty_filter=True,no_redraw=True,Optimize=0,native_starts=0,engineering_seconds=time.perf_counter()-tick))
    print(json.dumps([{k:p[k] for k in ['id','input_sha256','total_initial','total_target','sum_weights']} for p in roles]))

if __name__=='__main__':{'freeze':freeze,'generate':generate}[sys.argv[1]]()
