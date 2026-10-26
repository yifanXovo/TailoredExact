"""Round137 setup/once-only data draw; no Optimize or solver on import."""
from pathlib import Path
import argparse, collections, copy, dataclasses, hashlib, json, math, subprocess

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/unified_exact_round137'
BASE='b2b940c1e517a72e226ec60fc49ff19651737632'

def materialize(name):
    path=ROOT/name
    if not path.exists():
        data=subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT)
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    return path

def bootstrap():
    # Small saved source snapshots only; no historical raw recovery.
    names=['results/data_generation_citibike_round57/source_station_table.csv',
        'results/unified_exact_round116/projection_contract.json',
        'results/unified_exact_round116/source/snapshot.json',
        'results/unified_exact_round116/source/source_station_table.csv',
        'results/unified_exact_round116/source/row_decisions.json',
        'results/unified_exact_round116/source/requests/station_information/01.response',
        'results/unified_exact_round132/source/DIVVY/qualified_stations.json',
        'results/unified_exact_round132/source/DIVVY/snapshot.json',
        'results/unified_exact_round132/source/DIVVY/station_information.json',
        'results/unified_exact_round130/argv_freeze.json',
        'results/unified_exact_round131/argv_freeze.json',
        'results/unified_exact_round132/D_argv_freeze.json']
    for n in names:materialize(n)
    common=(ROOT/'scripts/round135_common.py').read_text(encoding='utf-8-sig')
    common=common.replace('Round135','Round137').replace('round135','round137').replace('ROUND135','ROUND137')
    common=common.replace("BASE = 'd3353749e6933e6685c7f0d92d153d0641816bcb'",f"BASE = '{BASE}'")
    common=common.replace('LIMITS = dict(B=28800., C=28800., D=28800., E=28800., repair=28800.)',
                          'LIMITS = dict(native=216000., diagnostic=216000.)')
    common=common.replace('TOTAL_LIMIT = 28800.', 'TOTAL_LIMIT = 216000.')
    target=ROOT/'scripts/round137_common.py'
    if target.exists():assert target.read_text(encoding='utf-8')==common
    else:target.write_text(common,encoding='utf-8',newline='\n')
    print('Bounded source snapshots and inherited meter ready; Optimize=0')

NEW=[('N-B15-B','CABI',15,'balanced','compact',1),
     ('N-X15-S','DIVVY',15,'shortage','compact',2),
     ('N-C20-U','CITI',20,'surplus','compact',1),
     ('N-X20-B','DIVVY',20,'balanced','regional',2),
     ('N-B35-S','CABI',35,'shortage','compact',1),
     ('N-C35-B','CITI',35,'balanced','regional',2),
     ('R-B20-S','CABI',20,'shortage','compact',1),
     ('R-X20-S','DIVVY',20,'shortage','compact',2),
     ('R-B35-S','CABI',35,'shortage','compact',1),
     ('R-X35-S','DIVVY',35,'shortage','compact',2)]
KNOWN=['K-15-S','X-15-B','UC-B20-B','K-20-S','K-35-U','X-35-B']

def recipe():
    from round137_common import write,sha,utc
    assert not (OUT/'source_recipe.json').exists()
    names=['scripts/round137_setup.py','scripts/round122_data.py','scripts/round109_data.py',
           'scripts/round118_data.py','scripts/generate_citibike443_regional_v1.py']
    write(OUT/'source_recipe.json',dict(UTC=utc(),base=BASE,known=KNOWN,new_specs=NEW,
        family='round137-gi-tbc-stage-consolidation-v1',
        source='fixed archived CITI/R57, CABI/R116, DIVVY/R132 snapshots; no new network acquisition',
        selection='unchanged four-anchor compact/regional rule and replicate; fixed table order; exclude previous new selections within source; no result-dependent redraw',
        inventory='unchanged R109/R122 shortage/balanced/surplus mathematics and sign repair',
        B1_T='n15:3600/5400 compact/regional; n20:5400/7200; n35:7200/10800',
        B2_T='base=2*max_depot_distance/1.5+120*sum(max(b-D,0))/M; T1=ceil(max(1800,.75*base)/300)*300; T2=ceil(1.5*T1/300)*300',
        B2_positive='serialized sum(D)-sum(b)>0, min(w)>0; both local supply and receiving stations required',
        weights='B1 lambda=.15; B2 rho=1; B3 rho=.5,1,2; lambda=rho/Omega',
        B3_preselected=['R-B20-S-T1','R-X35-S-T2'],
        C1_roles=['K-15-S','K-20-S','UC-B20-B','K-35-U'],C1_caps=[600,1200,1200,2400],
        C2_roles=['K-15-S','UC-B20-B','K-20-S','K-35-U'],C2_caps=[600,1200,1200,2400],
        D2_roles=['K-15-S','UC-B20-B','R-B20-S-T1','K-35-U'],D2_caps=[600,1200,1200,2400],
        D2_AM_mechanism=['K-15-S','UC-B20-B'],
        AM=[.04,.08,.16],default_AM=.08,H_seed=20260626,Gurobi_Seeds=[0,1],
        default_AP=False,pair_only=True,threads=1,serial=True,affinity=4,
        C1_adjustment='UC-B20-B retains its exact1200s matching C2/D2 cap; cap sum5400, extra10800s',
        total_planned_positions=120,planned_caps_seconds=174600,limit_seconds=216000,
        generation_dependencies={n:sha(ROOT/n) for n in names},Optimize=0,H=0))

def generate():
    from round137_common import write,read,sha,git,utc
    import round122_data as source
    import round109_data as landscape
    import generate_citibike443_regional_v1 as old
    from round134_campaign import frozen_inputs
    recipe=read(OUT/'source_recipe.json');assert not (OUT/'input_manifest.json').exists()
    for n,digest in recipe['generation_dependencies'].items():assert sha(ROOT/n)==digest,n
    # Recipe must precede every generation, with its exact Git identity.
    assert json.loads(git('show','HEAD:results/unified_exact_round137/source_recipe.json'))==recipe
    sets=source.load_sources()
    sets['DIVVY']=[source.cabi.Station(q['source_row_index'],q['station_id'],q['capacity'],q['x'],q['y'],q['latitude'],q['longitude'],tuple(q['original_row_indices']))
        for q in read(ROOT/'results/unified_exact_round132/source/DIVVY/qualified_stations.json')]
    hashes={s:v['identity_SHA'] for s,v in source.SOURCES.items()}
    hashes['DIVVY']=sha(ROOT/'results/unified_exact_round132/source/DIVVY/station_information.json')
    bindings=frozen_inputs();roles=[]
    for name in KNOWN:
        binding=bindings[name];p=copy.deepcopy(binding['panel']);materialize(p['input_path'])
        assert sha(ROOT/p['input_path'])==p['input_sha256']
        p.update(module='B1',base_id=name,known=True,cap_seconds={15:600,20:1200,35:2400}[p['V']],
            gurobi_seed=0,panel_kind='Round137 preselected known representative')
        p['instance_path']=p['input_path'];roles.append(p)
    used=collections.defaultdict(set);draws=[]
    for name,s,n,inventory,geometry,rep in NEW:
        all_stations=sets[s];pool=[q for q in all_stations if 0<q.capacity<100 and q.source_row_index not in used[s]]
        family=recipe['family']+f'|source={s}|source_sha256={hashes[s]}'
        old.FAMILY=family;landscape.VERSION=family;landscape.SOURCE_SHA=hashes[s]
        selection=old.build_selection(pool,n,geometry,rep);selection['selection_id']=f'r137_{name}'
        selection.update(source=s,coordinate_CRS='EPSG:32616' if s=='DIVVY' else 'EPSG:32618',
            excluded_previous_new_rows=sorted(used[s]),pool_source_rows=[q.source_row_index for q in pool])
        value=landscape.landscape(selection,inventory,all_stations)
        landscape.assert_equivalent(selection,inventory,all_stations,value)
        M=2 if n<35 else 3;Q=[30,30] if M==2 else [20,25,30]
        lines=old.instance_text(value,M,Q[0]).splitlines();lines[0]=f'{n} {M} {json.dumps(Q)}'
        dest=OUT/'inputs'/f'{name}.txt';dest.parent.mkdir(exist_ok=True)
        with dest.open('x',encoding='utf-8',newline='\n') as f:f.write('\n'.join(lines).rstrip()+'\n')
        parsed=old.parse_instance_mirror(dest)
        for suffix,obj in [('selection',selection),('landscape',value),('parsed',parsed),
            ('source_mapping',[dataclasses.asdict(q) for q in all_stations if q.source_row_index in selection['selected_source_station_row_indices']])]:
            write(dest.with_name(name+'_'+suffix+'.json'),obj)
        selected=set(selection['selected_source_station_row_indices']);assert not used[s]&selected;used[s]|=selected
        D,b,w=value['target'],value['initial'],value['weights'];omega=sum(w)
        p=dict(id=name,base_id=name,V=n,M=M,source=s,inventory=inventory,geometry=geometry,replicate=rep,
            Q_vector=Q,input_path=dest.relative_to(ROOT).as_posix(),instance_path=dest.relative_to(ROOT).as_posix(),
            input_sha256=sha(dest),source_identity_SHA=hashes[s],known=False,
            pickup_seconds=60,drop_seconds=60,cap_seconds={15:600,20:1200,35:2400}[n],
            gurobi_seed=0,Omega=omega,sum_weights=omega,total_initial=sum(b),total_target=sum(D),
            total_capacity=sum(value['capacities']),**{'lambda':.15},rho=.15*omega,
            panel_kind='Round137 preregistered new draw from archived public snapshot',
            selection_path=dest.with_name(name+'_selection.json').relative_to(ROOT).as_posix())
        if name.startswith('N-'):
            p.update(module='B1',T_seconds={15:3600,20:5400,35:7200}[n]*(1.5 if geometry=='regional' else 1))
            p['T_seconds']=int(p['T_seconds']);roles.append(p)
        else:
            assert sum(D)-sum(b)>0 and min(w)>0 and any(x>y for x,y in zip(b,D)) and any(x<y for x,y in zip(b,D))
            # Serialized depot coordinates, rather than a solver route, fix T.
            xy=parsed['points']
            max_dist=max(math.dist(xy[0],point) for point in xy[1:])
            base=2*max_dist/1.5+120*sum(max(x-y,0) for x,y in zip(b,D))/M
            T1=300*math.ceil(max(1800,.75*base)/300);T2=300*math.ceil(1.5*T1/300)
            lower_a=min(x/y for x,y in zip(w,D));floor=(lower_a*(sum(D)-sum(b)))/omega
            for j,T in [(1,T1),(2,T2)]:
                roles.append(dict(p,id=f'{name}-T{j}',module='B2',T_seconds=T,rho=1.,
                    **{'lambda':1/omega},positive_objective_floor=floor,T_design_base=base,shortage=sum(D)-sum(b)))
        draws.append(dict(id=name,SHA256=sha(dest),source=s,selected_rows=selection['selected_source_station_row_indices']))
    assert len(roles)==20 and len(draws)==10
    write(OUT/'input_manifest.json',dict(UTC=utc(),roles=roles,draws=draws,base_inputs=16,physical_configurations=20,
        recipe_SHA=sha(OUT/'source_recipe.json'),recipe_commit=git('rev-parse','HEAD').decode().strip(),
        generation_once=True,Optimize=0,H=0,within_source_new_draws_disjoint=True,
        historical_overlap='Archived stations may overlap old rounds; every selected row is disclosed; inputs are new draws, not new source or observed demand'))
    print(json.dumps([dict(id=p['id'],n=p['V'],T=p['T_seconds'],lam=p['lambda']) for p in roles]))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['bootstrap','recipe','generate']);a=p.parse_args()
    globals()[a.action]()
