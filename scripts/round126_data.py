"""Exactly six prospective draws using the unchanged offline R122/R109/R57 rules."""
from round126_common import *
import copy, dataclasses, math, statistics
from fractions import Fraction
import round122_data as source

old=source.old;landscape_math=source.landscape_math
SOURCES=copy.deepcopy(source.SOURCES)
VERSION='round126-thin-offline-adapter-v1'
REF=OUT/'inputs'
ROLES=[]
for n,(id,s,v,geo,r,stock,q,T,B,order) in enumerate([
 ('SC-C15-S','CITI',15,'compact',1,'shortage',[30,30],3600,600,['P-GRB','M-B']),
 ('SC-B15-S','CABI',15,'regional',1,'shortage',[20,40],5400,600,['M-B','P-GRB']),
 ('SC-C15-B','CITI',15,'regional',2,'balanced',[30,30],5400,600,['P-GRB','M-B']),
 ('SC-B20-S','CABI',20,'compact',1,'shortage',[30,30],5400,1200,['M-B','P-GRB']),
 ('SC-C20-S','CITI',20,'regional',1,'shortage',[20,40],7200,1200,['P-GRB','M-B']),
 ('SC-B20-U','CABI',20,'compact',2,'surplus',[30,30],7200,1200,['M-B','P-GRB'])],1):
    ROLES.append(dict(group_number=n,id=id,source=s,V=v,M=2,geometry=geo,replicate=r,inventory=stock,Q_vector=q,
        T_seconds=T,cap_seconds=B,method_order=order,selection_id=f'r126_{id}_{geo}_r{r}',
        pickup_seconds=60,drop_seconds=60,**{'lambda':.15},gurobi_seed=0,panel_kind='new_problem_Seed0'))

def family(s):return f'round126-small-certification-v1|source={s}|source_sha256='+SOURCES[s]['identity_SHA']

def configure(s):
    old.FAMILY=family(s);landscape_math.VERSION=family(s);landscape_math.SOURCE_SHA=SOURCES[s]['identity_SHA']
    assert old.COORD_DECIMALS==3 and old.WEIGHT_DECIMALS==6
    assert old.GEOGRAPHIC_REGIMES==('compact','regional') and old.REPLICATES==(1,2)

def freeze():
    workspace();identity();assert not REF.exists() and not (OUT/'source_recipe.json').exists()
    deps=['scripts/round126_data.py','scripts/round122_data.py','scripts/round118_data.py','scripts/round109_data.py','scripts/generate_citibike443_regional_v1.py']
    write(OUT/'source_recipe.json',dict(round=126,UTC=utc(),base=BASE,adapter_version=VERSION,sources=SOURCES,
        families={s:family(s) for s in SOURCES},full_fixed_running_table=ROLES,
        generation_dependencies={p:sha(ROOT/p) for p in deps},
        selection='Original four anchors, compact/regional geometry and original source-row ties. The family enters anchor hash; the exact selection_id enters target and inventory hashes.',
        target_fraction=[.44,.56],coordinate_decimals=3,weight_decimals=6,delta='max(V,floor(.12*sum(D)+.5))',
        local_perturbation=dict(balanced=.18,other=.30),total_correction_and_sign_repair='unchanged',
        weights='original square-target rule, maximum normalization, six decimals',depot='original serialized-coordinate centroid',
        distance='original Euclidean/1.5; no projection rerun',input_header='explicit listed Q_vector',
        formal_arms=12,formal_pairs=6,formal_nominal_seconds=10800,outer_limit_seconds=18000,
        generated_input_count=0,Optimize=0,no_H_LP_MIP_filter=True,no_redraw=True,no_network=True))
    print('R126 six-input recipe frozen; commit before generation; Optimize=0')

def positivity(parsed,p):
    # Mirror arrays include depot. All mathematical sums below explicitly omit it.
    b,D,w=parsed['initial'][1:],parsed['target'][1:],parsed['weights'][1:]
    shortage=sum(D)-sum(b)
    lam=Fraction('0.15')
    decimal_weights=[Fraction(str(x)) for x in w]
    delta=min(lam*x/d for x,d in zip(decimal_weights,D))
    lower=delta*shortage
    if p['inventory']=='shortage':assert shortage>0 and delta>0 and lower>0
    return dict(id=p['id'],station_indices=f'1..{p["V"]}; depot excluded',sum_initial=sum(b),sum_target=sum(D),shortage=shortage,
        lambda_decimal='0.15',weights_interpretation='exact decimal values serialized at six decimal places',
        delta_rational=str(delta),positive_floor_rational=str(lower),positive_floor_decimal=float(lower),
        parsed_binary64_lambda=repr(float(.15)),parsed_binary64_weights=[float(x).hex() for x in w],
        positive_objective_proved=p['inventory']=='shortage',
        not_injected_into_model_or_reported_native_L=True,empty_fleet_is_feasible=True)

def generate():
    tick=time.perf_counter();workspace();r=read(OUT/'source_recipe.json');assert not REF.exists()
    for n,h in r['generation_dependencies'].items():assert sha(ROOT/n)==h
    commit=git('rev-parse','HEAD').decode().strip()
    for n in ['scripts/round126_data.py','results/unified_exact_round126/source_recipe.json']:
        assert git('show',commit+':'+n).replace(b'\r\n',b'\n')==(ROOT/n).read_bytes().replace(b'\r\n',b'\n'),'commit recipe before generation'
    stations=source.load_sources();REF.mkdir(parents=True,exist_ok=False);roles=[];overlaps=[];positive=[]
    history=read(ROOT/'results/unified_exact_round122/input_manifest.json')['new_roles']
    for p0 in ROLES:
        p=copy.deepcopy(p0);configure(p['source']);ss=stations[p['source']]
        s=old.build_selection(ss,p['V'],p['geometry'],p['replicate'])
        s.update(schema='round126-geographic-selection-v1',selection_id=p['selection_id'],generator_version=VERSION)
        v=landscape_math.landscape(s,p['inventory'],ss);landscape_math.assert_equivalent(s,p['inventory'],ss,v)
        assert s['dataset_family']==v['dataset_family']==family(p['source'])
        assert v['seed_derivation_material']==f"{family(p['source'])}|inventory|{p['selection_id']}|{p['inventory']}"
        v.update(schema='round126-station-landscape-v1',generator_version=VERSION,source_hashes=SOURCES[p['source']])
        lines=old.instance_text(v,p['M'],p['Q_vector'][0]).splitlines();lines[0]=f"{p['V']} {p['M']} {json.dumps(p['Q_vector'])}"
        path=REF/(p['id']+'.txt');path.write_text('\n'.join(lines).rstrip()+'\n',encoding='utf-8',newline='\n')
        parsed=old.parse_instance_mirror(path)
        assert (parsed['V'],parsed['M'],parsed['Q'])==(p['V'],p['M'],p['Q_vector'])
        assert len(set(s['selected_source_station_row_indices']))==p['V']
        assert all(0<=b<=c and 0<d<=c for b,c,d in zip(v['initial'],v['capacities'],v['target']))
        assert all(w>0 for w in v['weights']) and max(v['weights'])==1
        # Original depot contract is retained even if unrounded source coordinates imply a sub-millimetre mean difference.
        by={q.source_row_index:q for q in ss}
        expected_depot=[round(statistics.fmean(getattr(by[i],axis) for i in s['selected_source_station_row_indices']),3) for axis in ['x','y']]
        assert v['depot']['coordinate_utm18n_meters']==expected_depot
        for suffix,obj in [('selection',s),('landscape',v),('parsed',parsed)]:write(REF/(p['id']+'_'+suffix+'.json'),obj)
        mapping=[dict(local_station_index=j,source=p['source'],**dataclasses.asdict(by[i]),source_identity_SHA=SOURCES[p['source']]['identity_SHA']) for j,i in enumerate(s['selected_source_station_row_indices'],1)]
        write(REF/(p['id']+'_source_mapping.json'),mapping)
        p.update(input_path=path.relative_to(ROOT).as_posix(),instance_path=path.relative_to(ROOT).as_posix(),input_sha256=sha(path),input_bytes=path.stat().st_size,
            selection_path=(REF/(p['id']+'_selection.json')).relative_to(ROOT).as_posix(),landscape_path=(REF/(p['id']+'_landscape.json')).relative_to(ROOT).as_posix(),
            source_identity_SHA=SOURCES[p['source']]['identity_SHA'],total_initial=sum(v['initial']),total_target=sum(v['target']),total_capacity=sum(v['capacities']),
            sum_weights=sum(v['weights']),lambda_sum_weights=.15*sum(v['weights']))
        chosen=set(s['selected_source_station_row_indices'])
        for prior,rn in [(q,122) for q in history]+[(q,126) for q in roles]:
            if prior['source']!=p['source']:continue
            indices=read(ROOT/prior['selection_path'])['selected_source_station_row_indices']
            overlaps.append(dict(id=p['id'],previous_id=prior['id'],previous_round=rn,source=p['source'],overlap=len(chosen&set(indices)),new_V=p['V'],previous_V=prior['V']))
            assert p['input_sha256']!=prior['input_sha256'],'DATA_BLOCKED exact duplicate; no redraw'
        # Read-only station arithmetic: this is neither a supplied Start nor an optimizer observation.
        ratios=[b/d for b,d in zip(v['initial'],v['target'])];S=sum(ratios)
        G=sum(abs(x-y) for j,x in enumerate(ratios) for y in ratios[j+1:])/(p['V']*S) if S else 0.
        P=sum(w*abs(x-1) for w,x in zip(v['weights'],ratios))
        p['empty_fleet']=dict(physically_feasible=True,F=G+.15*P,G=G,P=P,not_supplied_to_formal_arms=True)
        positive.append(positivity(parsed,p));roles.append(p)
    write(OUT/'input_manifest.json',dict(roles=roles,new_roles=roles,sources=SOURCES,families={s:family(s) for s in SOURCES},
        adapter_version=VERSION,source_recipe_SHA=sha(OUT/'source_recipe.json'),recipe_commit_before_generation=commit,
        generated_once=True,new_problem_denominator=6,formal_arm_denominator=12,formal_pair_denominator=6,
        overlaps=overlaps,historical_overlap_scope='Six R122 small manifests/selections already available; no full historical recovery.',
        nonfactorial_nonIID_not_six_cities=True))
    write(OUT/'shortage_positive_objective.json',dict(proof='F>=sum(lambda*w_i/D_i)|Y_i-D_i|>=delta*sum|Y_i-D_i|>=delta*(sumD-sumb)>0',
        premises='empty departure, nonnegative loaded return, positive lambda and weights; service stations only',roles=positive))
    write(OUT/'generation_receipt.json',dict(UTC=utc(),recipe_commit=commit,inputs=6,Optimize=0,H_calls=0,LP_calls=0,MIP_calls=0,
        no_performance_screening=True,no_redraw=True,seconds=time.perf_counter()-tick))
    print(json.dumps([{k:p[k] for k in ['id','input_sha256','total_initial','total_target','sum_weights']} for p in roles]))

if __name__=='__main__':{'freeze':freeze,'generate':generate}[sys.argv[1]]()
