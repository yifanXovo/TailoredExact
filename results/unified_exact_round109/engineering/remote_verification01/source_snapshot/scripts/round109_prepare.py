"""Freeze all candidate/data/decision rules before generating the twelve draws."""
from round109_common import *
import round109_data as data
import copy, math, csv, itertools

ROLES=[]
for n,(id,v,m,geo,rep,stock,qclass,T,cap,order) in enumerate([
    ('G20-C1',20,2,'compact',1,'shortage','H',3600,900,'PEB'),
    ('G20-C2',20,2,'compact',2,'balanced','X',7200,900,'EBP'),
    ('G20-R1',20,2,'regional',1,'surplus','H',7200,900,'BPE'),
    ('G20-R2',20,2,'regional',2,'shortage','X',3600,900,'PBE'),
    ('G50-C1',50,4,'compact',1,'balanced','H',7200,1800,'BEP'),
    ('G50-C2',50,4,'compact',2,'surplus','X',18000,1800,'EPB'),
    ('G50-R1',50,4,'regional',1,'shortage','X',7200,1800,'PEB'),
    ('G50-R2',50,4,'regional',2,'balanced','H',18000,1800,'EBP'),
    ('G100-C1',100,8,'compact',1,'surplus','X',18000,3600,'BPE'),
    ('G100-C2',100,8,'compact',2,'shortage','H',7200,3600,'PBE'),
    ('G100-R1',100,8,'regional',1,'balanced','X',7200,3600,'BEP'),
    ('G100-R2',100,8,'regional',2,'surplus','H',18000,3600,'EPB')],1):
    q=[30]*m if qclass=='H' else [20,40] if m==2 else [20,25,35,40]*(m//4)
    ROLES.append(dict(number=n,id=id,V=v,M=m,geometry=geo,replicate=rep,inventory=stock,Q_class=qclass,
        Q_vector=q,T_seconds=T,cap_seconds=cap,method_order=[{'P':'P-GRB','E':'ENS-C','B':'M-B'}[c] for c in order],
        pickup_seconds=60,drop_seconds=60,**{'lambda':.15},gurobi_seed=0,panel_kind='main'))
SEEDS=[dict(number=13,id='G20-C2',gurobi_seed=1,method_order=['P-GRB','M-B']),
       dict(number=14,id='G50-R1',gurobi_seed=1,method_order=['M-B','P-GRB']),
       dict(number=15,id='G100-R2',gurobi_seed=1,method_order=['P-GRB','M-B'])]
COMMON=dict(threads=1,mip_threads=1,gurobi_seed=0,gurobi_presolve=-1,gurobi_version='13.0.2',affinity_mask=4,
    native_limit_offset_seconds=6,hard_stop_offset_seconds=2,shutdown_margin_seconds=30,
    requested_mip_gap=0,requested_mip_gap_abs=0,FeasibilityTol=1e-6,OptimalityTol=1e-6,IntFeasTol=1e-5)

def recipe():
    return dict(version=data.VERSION,roles=ROLES,seed_checks=SEEDS,public_source=dict(path=data.SOURCE_PATH,
        commit=BASE,blob='84fb8af5aaa9836d316820227e4f06e8cd4b1e63',bytes=69678,SHA=data.SOURCE_SHA,rows=443,eligible=442),
        adapter_SHA=sha(data.__file__),original_generator_SHA=sha(data.old.__file__),prepare_SHA=sha(__file__),
        pure_rules=['four farthest anchors per V; original ties','compact nearest V; regional farthest-first within nearest 2V',
            'centroid at three decimals','target 44%-56% capacity by inherited hash profile',
            '12% total offset, at least V; local imbalance; deterministic total correction and ensure_both_local_signs',
            'max-normalized weights; inherited four-decimal compatibility min_ratio; original points-only writer'],
        differences=['public source table replaces private capacity/coordinate rehash','new family prefix in all hash material',
            'explicit heterogeneous or homogeneous fleet header; listed external T','trace-only intermediate recording'],
        no_performance_pilot=True,retain_every_legal_draw=True,zero_solve_checks_only=True,
        minimum_ratio_is_compatibility_only=True,empty_routes_are_data_witness_only_never_extra_Start=True,
        synthetic_fields=['depot','target','initial','weights','min_ratio','fleet','T'],
        same_city_source=True,independent_IID_geographic_samples_claim=False)

def freeze():
    check_identity();OUT.mkdir(exist_ok=True)
    assert not (OUT/'generation_recipe.json').exists()
    write(OUT/'generation_recipe.json',recipe())
    write(OUT/'candidate_contract_freeze.json',dict(candidate='R100 frozen M-B',original_commit='b5d6d83bb8fc74682de6f1f6862c2e687712f4cf',
        original_freeze_path='results/unified_exact_round100/candidate_freeze.json',original_freeze_SHA=sha(ROOT/'results/unified_exact_round100/candidate_freeze.json'),
        measured_production_source_commit='b5db3f038f64215766a54498d8acc82e384de733',base_commit=BASE,
        source_bindings=bindings(),production_PE_SHA=PE_SHA,DLL_SHA=DLL_SHA,input_preset='research-round83-vds-equal-net-exchange',
        appended_argv=['--round98-state-service','m-binary'],effective_identity='research-round99-ensc-discrete-structure-m-binary',
        round100_continuous_quantities=False,default_ENS_changed=False,no_new_mechanism=True,no_instance_dispatch=True))
    protocol=dict(version=data.VERSION,roles=ROLES,seed_checks=SEEDS,common_parameters=COMMON,
        formal_arms=42,main_arms=36,seed_arms=6,nominal_seconds=88200,main_nominal_seconds=75600,seed_nominal_seconds=12600,
        maximum_starts=72,maximum_outer_seconds=100000,qualification_starts_reserved=8,qualification_outer_seconds_reserved=1200,
        planned_formal_starts=57,start_reserve=7,serial=True,full_42_required_for_normal_results=True,
        no_early_performance_cancellation=True,no_best_of_two=True,no_cross_arm_UB_Start_route_cut_cache=True,
        materiality=dict(a_U='max(.001,.01*abs(U_C))',a_gap='max(.001,.10*abs(gap_C))',a_t='max(30,.10*t_C)'),
        severity=dict(control_only_certificate=True,both_certified='t_A>=2*t_C and t_A-t_C>=120',
            both_uncertified='U_A-U_C>=max(.001,.05*abs(U_C)) and gap_A-gap_C>=max(.005,.25*abs(gap_C))'),
        closure_tolerance=1e-7,zero_objective_tolerance=1e-12,signed_gap_not_clipped=True,
        relative_gap='qualified finite U/L and abs(U)>1e-12 else null',MIXED_not_WIN=True,
        support_requires=dict(all_42_valid_same_PE=True,all_12_eligible_at_initial_freeze=True,main_all_evaluable=True,
            main_MIN_WIN=6,main_MAX_LOSS=2,main_severe_regressions=0,WIN_in_each_V=[20,50,100],WIN_in_each_geometry=['compact','regional'],
            seed_all_evaluable=True,seed_severe_regressions=0,seed_min_not_LOSS=2,no_Seed0_WIN_to_Seed1_LOSS=True),
        ENS_dominance_hidden_condition=False,stages=['BLOCKED','BROAD_PANEL_SUPPORT','BROAD_PANEL_NOT_SUPPORTED'],
        frozen_recipe_SHA=sha(OUT/'generation_recipe.json'),frozen_candidate_SHA=sha(OUT/'candidate_contract_freeze.json'))
    write(OUT/'protocol.json',protocol);print('candidate, full recipe/roles/order/Seed/decision frozen; no draw or Optimize')

def generate():
    assert recipe()==read(OUT/'generation_recipe.json')
    stations=data.load(ROOT);folder=ROOT/'reference/round109_geographic';folder.mkdir(exist_ok=False)
    roles=copy.deepcopy(ROLES);selections={};stats=[]
    for role in roles:
        selection=data.old.build_selection(stations,role['V'],role['geometry'],role['replicate'])
        obj=data.landscape(selection,role['inventory'],stations);data.assert_equivalent(selection,role['inventory'],stations,obj)
        lines=data.old.instance_text(obj,role['M'],role['Q_vector'][0]).splitlines()
        lines[0]=f"{role['V']} {role['M']} {json.dumps(role['Q_vector'])}"
        path=folder/(role['id']+'.txt')
        with path.open('x',encoding='utf-8',newline='\n') as f:f.write('\n'.join(lines)+'\n')
        # Bytes are durable before the syntax/domain checks. Never redraw an existing role.
        write(folder/(role['id']+'_selection.json'),selection);write(folder/(role['id']+'_landscape.json'),obj)
        parsed=data.old.parse_instance_mirror(path);write(folder/(role['id']+'_parsed.json'),parsed)
        assert parsed['V']==role['V'] and parsed['M']==role['M'] and parsed['Q']==role['Q_vector']
        assert len(parsed['points'])==role['V']+1 and len(set(map(tuple,parsed['points'])))==role['V']+1
        assert all(0<=b<=c and d>0 for b,c,d in zip(obj['initial'],obj['capacities'],obj['target']))
        assert role['T_seconds']>0 and all(w>0 for w in obj['weights']) and max(obj['weights'])==1
        ratios=[b/d for b,d in zip(obj['initial'],obj['target'])];den=role['V']*sum(ratios)
        G=sum(abs(a-b) for a,b in itertools.combinations(ratios,2))/den if den else 0.
        P=sum(w*abs(r-1) for w,r in zip(obj['weights'],ratios))
        witness=dict(empty_vehicles=role['M'],each_route=[0,0],operations=[],initial_departure_load=0,
            prefix_return_loads=0,travel_seconds=0,handling_seconds=0,Y=obj['initial'],G=G,P=P,F=G+.15*P,
            feasible=True,min_ratio_constraint_applied=False,not_injected_as_Start_or_UB=True)
        write(folder/(role['id']+'_empty_route_witness.json'),witness)
        mapping=[dict(local_station_index=j,source_station_row_index=i,capacity=stations[i].capacity,
            x=stations[i].x,y=stations[i].y) for j,i in enumerate(obj['source_station_row_indices'],1)]
        write(folder/(role['id']+'_source_mapping.json'),mapping)
        role.update(input_path=path.relative_to(ROOT).as_posix(),input_sha256=sha(path),input_bytes=path.stat().st_size,
            selection_path=(folder/(role['id']+'_selection.json')).relative_to(ROOT).as_posix(),
            landscape_path=(folder/(role['id']+'_landscape.json')).relative_to(ROOT).as_posix(),role_identity='prospective_unmeasured_at_initial_freeze',
            total_initial=sum(obj['initial']),total_target=sum(obj['target']),sum_omega=sum(obj['weights']))
        stats.append(dict(id=role['id'],V=role['V'],M=role['M'],geometry=role['geometry'],inventory=role['inventory'],
            Q_class=role['Q_class'],T_seconds=role['T_seconds'],cap_seconds=role['cap_seconds'],sum_omega=sum(obj['weights']),**obj['statistics']))
        selections[role['id']]=set(obj['source_station_row_indices'])
    overlap=[dict(first=a,second=b,shared_stations=len(selections[a]&selections[b]),
        shared_source_row_indices=sorted(selections[a]&selections[b])) for a,b in itertools.combinations(selections,2)]
    write(OUT/'input_manifest.json',dict(roles=roles,recipe_SHA=sha(OUT/'generation_recipe.json'),zero_Optimize=True,empty_route_feasibility_passed=True))
    write(OUT/'structure_statistics.json',stats);write(OUT/'source_subset_overlap.json',overlap)
    print(json.dumps(dict(generated_once=len(roles),V100_inputs=sum(r['V']==100 for r in roles),Optimize=0)),flush=True)

if __name__=='__main__':{'freeze':freeze,'generate':generate}[sys.argv[1]]()
