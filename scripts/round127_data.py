"""Once-only tiny adapter and fixed training/evaluation tables, no Optimize."""
from round127_common import *
import copy,dataclasses,statistics
import round122_data as source
from round126_data import positivity

TINY=[dict(id='SM-C8-S',source='CITI',V=8,M=1,geometry='compact',replicate=1,inventory='shortage',Q_vector=[20],T_seconds=2400,cap_seconds=90),
 dict(id='SM-B10-B',source='CABI',V=10,M=2,geometry='regional',replicate=2,inventory='balanced',Q_vector=[15,25],T_seconds=3600,cap_seconds=90)]
TRAIN=[dict(id='S12',input_path='reference/round106_confirmation/S12.txt',input_sha256='475763e70a2dc3b9d28a88028378e76946cbebf33aa7b7e5b033e018dd13369f',V=12,M=2,Q_vector=[8,12],T_seconds=3600,cap_seconds=90),
 dict(id='PB-B20-S',input_path='reference/round122_paper_benchmark/PB-B20-S.txt',input_sha256='3aa535245e6475f791d50d8be26e8165c6f83371d9dbebac76728b9cc36eebbc',V=20,M=2,Q_vector=[20,40],T_seconds=7200,cap_seconds=180),
 dict(id='R98-C2',input_path='reference/round98_confirmation/C2.txt',input_sha256='07d0964c87b534254e6bf2957911859a6a2bd73e377211728b7e65f44294fc76',V=30,M=3,Q_vector=[20,25,30],T_seconds=7200,cap_seconds=180)]
CONFIGS=[dict(id='q'+str(j),MIPFocus=f,Cuts=c,nondefault_parameters=int(f!=0)+int(c!=-1)) for j,(f,c) in enumerate([(0,-1),(1,-1),(2,-1),(3,-1),(2,2),(3,2)])]
def family(s):return f'round127-tiny-regression-v1|source={s}|source_sha256='+source.SOURCES[s]['identity_SHA']
def common(p):return dict(p,pickup_seconds=60,drop_seconds=60,**{'lambda':.15})
def freeze():
    assert not (OUT/'tiny_recipe.json').exists()
    deps=['scripts/round127_data.py','scripts/round126_data.py','scripts/round122_data.py','scripts/round118_data.py','scripts/round109_data.py','scripts/generate_citibike443_regional_v1.py']
    roles=[common(dict(p,selection_id=f'r127_{p["id"]}_{p["geometry"]}_r{p["replicate"]}')) for p in TINY]
    write(OUT/'tiny_recipe.json',dict(UTC=utc(),sources=source.SOURCES,roles=roles,families={s:family(s) for s in source.SOURCES},
        dependencies={p:sha(ROOT/p) for p in deps},coordinate_decimals=3,weight_decimals=6,target_fraction=[.44,.56],
        inventory_perturbation=dict(balanced=.18,other=.30),total_correction='unchanged R126/R122',
        original_selection_weights_depot_and_distance=True,no_redraw=True,no_network=True,no_Optimize_or_H=True))
    main=copy.deepcopy(read(ROOT/'results/unified_exact_round126/input_manifest.json')['roles'])
    for p in main:p.update(gurobi_seed=1,panel_kind='E0_seed1_confirmation')
    training=[]
    for j,p in enumerate(TRAIN):
        for seed in [2,3]:
            shift=(j+2*(seed-2))%6;order=CONFIGS[shift:]+CONFIGS[:shift]
            for c in order:training.append(dict(position=len(training)+1,role=common(p),seed=seed,configuration=c))
    tiny=[]
    for j,p in enumerate(roles):
        for seed in range(3):
            for repeat in [1,2]:
                order=['P','MB'] if (j+seed)%2==0 else ['MB','P']
                if repeat==2:order=list(reversed(order))
                tiny.append(dict(group=len(tiny)+1,role=p,seed=seed,repeat=repeat,methods=order))
    core=[]
    for k,(id,methods) in enumerate([
        ('SC-C15-S',['P','MR','MB','PT','MD','MG','MS2']),
        ('SC-B20-S',['MG','PT','MS2','MB','MR','P','MD']),
        ('PB-B35-B',['MD','MS2','P','MG','PT','MR','MB'])],1):
        p=next((copy.deepcopy(p) for p in main if p['id']==id),None)
        if p is None:p=common(dict(id=id,V=35,M=3,Q_vector=[25,25,25],T_seconds=7200,cap_seconds=1200,
            input_path='reference/round122_paper_benchmark/PB-B35-B.txt',input_sha256='41fdb57cad176be7746bb7c884f62da1643920ac2c49d75bd5235663936a5e3a',source='CABI',inventory='balanced'))
        p.update(gurobi_seed=1,panel_kind='E1_known_role_mechanism')
        core.append(dict(group=k,role=p,seed=1,methods=methods,prespecified_pairs=[['MB',b] for b in ['P','PT','MD','MR','MG','MS2']]+[['PT','P']]))
    write(OUT/'experiment_manifest.json',dict(version='Round127 complete replacement v3',base=BASE,E0_SHA=E0_SHA,DLL_SHA=DLL_SHA,
        sole_paper_method='M-B / GI-TBC',E0_main=main,E0_tiny=tiny,E1_training=training,E1_core=core,configurations=CONFIGS,
        seed_H=20260626,Threads=1,MIP_threads=1,affinity_mask=4,shutdown_reserve=30,native_offset=6,hard_stop_offset=2,
        MIPGap=0,MIPGapAbs=0,FeasibilityTol=1e-6,IntFeasTol=1e-5,OptimalityTol=1e-6,
        nominal=dict(main=10800,tiny=2160,core=21000,training=5400),qualification_soft=3600,qualification_limit=5400,total_outer_limit=54000,
        evaluation_unique_inputs=9,training_unique_inputs=3,formal_maximum_arms=57,training_arms=36,
        PT_q0_alias_no_duplicate_run=True,selection_before_E1_evaluation=True,no_performance_retries=True,
        mathematical_contract='R125/R126 unchanged; Gini interval decomposition, not R105 inventory-route decomposition',
        direction='both-certified strict unrounded time direction; one-sided certificate vs valid open; both-open UNDETERMINED; invalid UNEVALUABLE',
        tuning_selection='complete six positions; N>=N0,Nmin>=Nmin0 and [N>N0 or N=N0>0,S<S0,S<=.9*S0]; priority -N,-Nmin,S,nondefaults,qid; else q0'))
    for c in CONFIGS:
        text='# Round127 fixed configuration '+c['id']+'; all other P settings unchanged\n'
        if c['MIPFocus']!=0:text+='MIPFocus '+str(c['MIPFocus'])+'\n'
        if c['Cuts']!=-1:text+='Cuts '+str(c['Cuts'])+'\n'
        path=OUT/'tuning_manifest'/(c['id']+'.prm');path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='utf-8')
    print('36 training positions and 57 maximum formal arms frozen; commit recipe before generation')
def generate():
    recipe=read(OUT/'tiny_recipe.json');commit=git('rev-parse','HEAD').decode().strip()
    for p,h in recipe['dependencies'].items():assert sha(ROOT/p)==h
    for p in ['scripts/round127_data.py','results/unified_exact_round127/tiny_recipe.json','results/unified_exact_round127/experiment_manifest.json']:
        assert git('show',commit+':'+p).replace(b'\r\n',b'\n')==(ROOT/p).read_bytes().replace(b'\r\n',b'\n')
    directory=OUT/'inputs';directory.mkdir(exist_ok=False);stations=source.load_sources();roles=[]
    for p0 in recipe['roles']:
        p=copy.deepcopy(p0);sname=p['source'];ss=stations[sname]
        source.old.FAMILY=family(sname);source.landscape_math.VERSION=family(sname);source.landscape_math.SOURCE_SHA=source.SOURCES[sname]['identity_SHA']
        selection=source.old.build_selection(ss,p['V'],p['geometry'],p['replicate'])
        selection.update(schema='round127-tiny-selection-v1',selection_id=p['selection_id'],generator_version='round127-thin-v1')
        v=source.landscape_math.landscape(selection,p['inventory'],ss)
        source.landscape_math.assert_equivalent(selection,p['inventory'],ss,v)
        lines=source.old.instance_text(v,p['M'],p['Q_vector'][0]).splitlines();lines[0]=f'{p["V"]} {p["M"]} {json.dumps(p["Q_vector"])}'
        path=directory/(p['id']+'.txt');path.write_text('\n'.join(lines).rstrip()+'\n',encoding='utf-8',newline='\n')
        parsed=source.old.parse_instance_mirror(path);assert (parsed['V'],parsed['M'],parsed['Q'])==(p['V'],p['M'],p['Q_vector'])
        by={q.source_row_index:q for q in ss}
        for suffix,obj in [('selection',selection),('landscape',v),('parsed',parsed),('source_mapping',
            [dict(local_station_index=j,source=sname,**dataclasses.asdict(by[i])) for j,i in enumerate(selection['selected_source_station_row_indices'],1)])]:
            write(directory/(p['id']+'_'+suffix+'.json'),obj)
        p.update(input_path=path.relative_to(ROOT).as_posix(),instance_path=path.relative_to(ROOT).as_posix(),input_sha256=sha(path),
            source_identity_SHA=source.SOURCES[sname]['identity_SHA'],shortage_arithmetic=positivity(parsed,p))
        roles.append(p)
    manifest=read(OUT/'experiment_manifest.json')
    for p in manifest['E0_main']+[q['role'] for q in manifest['E1_core']]+TRAIN:
        assert sha(ROOT/p['input_path'])==p['input_sha256'],p
        parsed=source.old.parse_instance_mirror(ROOT/p['input_path'])
        assert (parsed['V'],parsed['M'],parsed['Q'])==(p['V'],p['M'],p['Q_vector']),p
    write(OUT/'input_manifest.json',dict(tiny_roles=roles,main_roles=manifest['E0_main'],training_roles=TRAIN,
        core_roles=[q['role'] for q in manifest['E1_core']],recipe_commit=commit,generated_once=True,Optimize=0))
    write(OUT/'generation_receipt.json',dict(UTC=utc(),recipe_commit=commit,input_SHA={p['id']:p['input_sha256'] for p in roles},Optimize=0,no_redraw=True))
    print(json.dumps(dict(tiny=[dict(id=p['id'],SHA=p['input_sha256']) for p in roles],Optimize=0)))
if __name__=='__main__':{'freeze':freeze,'generate':generate}[sys.argv[1]]()
