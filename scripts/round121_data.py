"""Three once-only prospective draws from the R117 safe fixed Cabi table."""
from round121_common import *
import copy,csv,dataclasses,math,statistics
import round118_data as safe
import round109_data as landscape_math
import generate_citibike443_regional_v1 as old
RAW_SHA=safe.RAW_SHA;TABLE_SHA=safe.TABLE_SHA
FAMILY='round121-frozen-d1-confirmation-v1|source_sha256='+RAW_SHA
VERSION='round121-thin-offline-adapter-v1'
REF=ROOT/'reference/round121_confirmation'
ROLES=[dict(id='Q30-C2-B',V=30,M=3,geometry='compact',replicate=2,inventory='balanced',Q_vector=[20,25,30],T_seconds=7200,cap_seconds=1800,selection_id='cabi_r121_V30_compact_r2',gurobi_seed=0,method_order=['P-GRB','MB-D1','M-B']),
 dict(id='Q40-R2-S',V=40,M=4,geometry='regional',replicate=2,inventory='shortage',Q_vector=[20,25,35,40],T_seconds=10800,cap_seconds=3600,selection_id='cabi_r121_V40_regional_r2',gurobi_seed=0,method_order=['MB-D1','M-B','P-GRB']),
 dict(id='Q50-C2-U',V=50,M=4,geometry='compact',replicate=2,inventory='surplus',Q_vector=[30,30,30,30],T_seconds=10800,cap_seconds=3600,selection_id='cabi_r121_V50_compact_r2',gurobi_seed=0,method_order=['M-B','P-GRB','MB-D1'])]
for p in ROLES:p.update(pickup_seconds=60,drop_seconds=60,**{'lambda':.15},panel_kind='prospective_confirmation')
def configure():
    old.FAMILY=FAMILY;landscape_math.VERSION=FAMILY;landscape_math.SOURCE_SHA=RAW_SHA
    assert old.GEOGRAPHIC_REGIMES==('compact','regional') and old.REPLICATES==(1,2)
    assert old.COORD_DECIMALS==3 and old.WEIGHT_DECIMALS==6
def selection(stations,p):
    configure();s=old.build_selection(stations,p['V'],p['geometry'],p['replicate'])
    s.update(schema='cabi-round121-geographic-selection-v1',selection_id=p['selection_id'],generator_version=VERSION)
    return s
def landscape(s,stations,p):
    configure();v=landscape_math.landscape(s,p['inventory'],stations)
    landscape_math.assert_equivalent(s,p['inventory'],stations,v)
    assert v['dataset_family']==FAMILY and v['seed_derivation_material'].startswith(FAMILY+'|')
    v.update(schema='cabi-round121-station-landscape-v1',generator_version=VERSION,source_hashes={'official_station_response_SHA256':RAW_SHA})
    return v
def fixed_roles():
    src=read(ROOT/'results/unified_exact_round120/input_manifest.json')
    known={p['id']:copy.deepcopy(p) for p in src['core_roles']+src['qualification_roles']}
    f,c,h=known['F2'],known['R98-C2'],known['H100']
    f.update(cap_seconds=1200,gurobi_seed=1,method_order=['MB-D0','P-GRB','MB-D1','M-B'],panel_kind='known_seed_sensitivity')
    c.update(cap_seconds=1800,gurobi_seed=1,method_order=['M-B','P-GRB','MB-D1'],panel_kind='known_seed_sensitivity')
    h.update(cap_seconds=120,gurobi_seed=1,method_order=['P-GRB','M-B','MB-D0','MB-D1'],panel_kind='qualification')
    for p in [f,c,h]:
        for k in list(p):
            if k.startswith(('historical_','diagnostic_')) or k=='reference':p.pop(k)
        p['instance_path']=p['input_path']
    return [f,copy.deepcopy(ROLES[0]),c,copy.deepcopy(ROLES[1]),copy.deepcopy(ROLES[2])],h
def freeze():
    assert not REF.exists() and not (OUT/'source_recipe.json').exists()
    roles,h=fixed_roles();deps=['scripts/round121_data.py','scripts/round118_data.py','scripts/round109_data.py','scripts/generate_citibike443_regional_v1.py']
    write(OUT/'source_recipe.json',dict(round=121,base=BASE,frozen_UTC=utc(),family=FAMILY,roles=ROLES,full_fixed_running_table=roles,
        qualification_role=h,adapter_SHA=sha(__file__),generation_dependencies={n:sha(ROOT/n) for n in deps},
        raw_source_SHA=RAW_SHA,table_SHA=TABLE_SHA,source_rows=865,source_loader='R118 source_check only; no R118 configure/selection/landscape wrapper',
        four_original_anchors_ties_geometry_and_selection=True,target_fraction=[.44,.56],coordinates_decimals=3,weights_decimals=6,
        delta='max(V,floor(.12*sum(D)+.5))',desired_total={'balanced':'sum(D)','shortage':'max(0,sum(D)-delta)','surplus':'min(sum(C),sum(D)+delta)'},
        local_perturbation={'balanced':.18,'other':.30},original_total_correction_sign_repair_max_normalized_weights_and_centroid=True,
        generated_input_count=0,actual_Dsum_optimum_H_LP_MIP_and_difficulty_unknown=True,no_network_or_reprojection=True,
        no_selection_by_result=True,no_resampling=True,formal_arms=16,formal_pairs=18,formal_nominal_seconds=37200,management_reserve=600,
        total_limit=[40,48000],qualification_limit=[8,1800],D0_only_F2_Seed1=True,V60_V100_excluded=True))
    print('R121 recipe, adapter and all roles/orders frozen before generation; commit before generate')
def generate():
    tick=time.perf_counter();recipe=read(OUT/'source_recipe.json')
    assert not REF.exists() and recipe['family']==FAMILY and recipe['adapter_SHA']==sha(__file__)
    for p,h in recipe['generation_dependencies'].items():assert sha(ROOT/p)==h
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()
    for n in ['scripts/round121_data.py','results/unified_exact_round121/source_recipe.json']:
        published=subprocess.check_output(['git','show',commit+':'+n],cwd=ROOT)
        assert published.replace(b'\r\n',b'\n')==(ROOT/n).read_bytes().replace(b'\r\n',b'\n'),'freeze must be committed first (Git newline normalization only)'
    stations=safe.source_check();REF.mkdir(parents=True,exist_ok=False)
    history=read(ROOT/'results/unified_exact_round116/historical_input_hash_index.json')['SHA_to_paths']
    oldroles=read(ROOT/'results/unified_exact_round116/input_manifest.json')['roles']+read(ROOT/'results/unified_exact_round118/input_manifest.json')['roles']
    for p in oldroles:history.setdefault(p['input_sha256'],[]).append(p['input_path'])
    overlaps=[];roles=[]
    for p0 in ROLES:
        p=copy.deepcopy(p0);s=selection(stations,p);v=landscape(s,stations,p)
        lines=old.instance_text(v,p['M'],p['Q_vector'][0]).splitlines();lines[0]=f"{p['V']} {p['M']} {json.dumps(p['Q_vector'])}"
        path=REF/(p['id']+'.txt')
        with path.open('x',encoding='utf-8',newline='\n') as f:f.write('\n'.join(lines).rstrip()+'\n')
        digest=sha(path)
        assert digest not in history,'DATA_IDENTITY_BLOCKED: exact duplicate retained, no redraw'
        history[digest]=[path.relative_to(ROOT).as_posix()];parsed=old.parse_instance_mirror(path)
        assert (parsed['V'],parsed['M'],parsed['Q'])==(p['V'],p['M'],p['Q_vector'])
        assert len(set(s['selected_source_station_row_indices']))==p['V'] and len(v['initial'])==p['V']
        assert all(0<=b<=c and 0<d<=c for b,c,d in zip(v['initial'],v['capacities'],v['target']))
        assert all(w>0 for w in v['weights']) and max(v['weights'])==1
        assert v['depot']['coordinate_utm18n_meters']==[round(statistics.fmean(q[j] for q in parsed['points'][1:]),3) for j in range(2)]
        mapping=[dict(local_station_index=j,**dataclasses.asdict(stations[i]),source_response_SHA=RAW_SHA) for j,i in enumerate(s['selected_source_station_row_indices'],1)]
        for suffix,obj in [('selection',s),('landscape',v),('parsed',parsed),('source_mapping',mapping)]:
            dest=REF/(p['id']+'_'+suffix+'.json');assert not dest.exists();write(dest,obj)
        chosen=set(s['selected_source_station_row_indices'])
        for previous in oldroles:
            if previous['V']<=50:
                prev=read(ROOT/previous['selection_path'])['selected_source_station_row_indices']
                overlaps.append(dict(id=p['id'],old_id=previous['id'],old_V=previous['V'],new_V=p['V'],overlap=len(chosen&set(prev))))
        ratios=[b/d for b,d in zip(v['initial'],v['target'])];S=sum(ratios)
        G=sum(abs(x-y) for i,x in enumerate(ratios) for y in ratios[i+1:])/(p['V']*S) if S else 0.
        penalty=sum(w*abs(r-1) for w,r in zip(v['weights'],ratios))
        p.update(input_path=path.relative_to(ROOT).as_posix(),instance_path=path.relative_to(ROOT).as_posix(),input_sha256=digest,input_bytes=path.stat().st_size,
            selection_path=(REF/(p['id']+'_selection.json')).relative_to(ROOT).as_posix(),landscape_path=(REF/(p['id']+'_landscape.json')).relative_to(ROOT).as_posix(),
            source_response_SHA=RAW_SHA,total_initial=sum(v['initial']),total_target=sum(v['target']),total_capacity=sum(v['capacities']),sum_weights=sum(v['weights']),
            lambda_sum_weights=.15*sum(v['weights']),empty_fleet=dict(physically_feasible=True,G=G,P=penalty,lambda_P=.15*penalty,F=G+.15*penalty,duration=0,all_loads=0),
            role_identity='new after D1 freeze; generated once without H/LP/MIP screening')
        roles.append(p)
    fixed,h=fixed_roles();by={p['id']:p for p in roles};fixed=[by.get(p['id'],p) for p in fixed]
    write(OUT/'input_manifest.json',dict(roles=fixed,new_roles=roles,qualification_roles=[h],family=FAMILY,source_recipe_SHA=sha(OUT/'source_recipe.json'),
        recipe_commit_before_generation=commit,generated_once=True,new_problem_denominator=3,known_role_seed_denominator=2,formal_arm_denominator=16,
        source_rows=865,raw_source_SHA=RAW_SHA,table_SHA=TABLE_SHA,overlaps=overlaps,exact_historical_SHA_duplicates=False,same_known_city_not_IID=True))
    write(OUT/'generation_receipt.json',dict(generated_UTC=utc(),inputs=[{k:p[k] for k in ['id','input_sha256','total_initial','total_target','sum_weights','lambda_sum_weights','empty_fleet']} for p in roles],
        recipe_commit=commit,unique_new_input_files_written=3,no_H_LP_MIP_or_difficulty_filter=True,no_redraw=True,Optimize=0,native_starts=0,engineering_seconds=time.perf_counter()-tick))
    print(json.dumps([{k:p[k] for k in ['id','input_sha256','total_initial','total_target','sum_weights']} for p in roles]))
if __name__=='__main__':{'freeze':freeze,'generate':generate}[sys.argv[1]]()
