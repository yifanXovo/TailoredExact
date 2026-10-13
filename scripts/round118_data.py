"""One offline V40 draw; inherited R57 mathematics, no acquisition or solver."""
from __future__ import annotations
import copy, csv, dataclasses, datetime, hashlib, json, math, statistics, sys, time
from pathlib import Path
import generate_citibike443_regional_v1 as old
import round109_data as inherited

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/unified_exact_round118'
REF = ROOT / 'reference/round118_positive'
BASE = '71ccd3b75ca8d713018f4edd222cd4c5f0a0b962'
RAW_SHA = 'd4e664c3ecb8c580e95d39541555be9cf592666a515cb854a857fb1d117ff0b8'
TABLE_SHA = 'd982051e5871c575ecdf9df538605401bd98341ae9b3b48112482eff80d42ffa'
FAMILY = 'round118-v40-positive-proof-v1|source_sha256=' + RAW_SHA
SELECTION_ID = 'cabi_r118_V40_regional_r1'
VERSION = 'round118-thin-offline-adapter-v1'
ROLE = dict(number=1, id='N40-R1-S', V=40, M=4, geometry='regional', replicate=1,
    inventory='shortage', Q_vector=[20,25,35,40], Q_class='X', T_seconds=10800,
    pickup_seconds=60, drop_seconds=60, **{'lambda':.15}, gurobi_seed=0,
    cap_seconds=5400, method_order=['P-GRB','M-B','P-S','ENS-C'], panel_kind='positive_confirmation')

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def utc(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def write(p, value):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(value,f,ensure_ascii=False,indent=2); f.write('\n')
def configure():
    old.FAMILY=FAMILY; inherited.VERSION=FAMILY; inherited.SOURCE_SHA=RAW_SHA
    assert old.GEOGRAPHIC_REGIMES==('compact','regional') and old.REPLICATES==(1,2)
    assert old.COORD_DECIMALS==3 and old.WEIGHT_DECIMALS==6

@dataclasses.dataclass(frozen=True)
class Station:
    source_row_index:int
    station_id:str
    capacity:int
    x:float
    y:float
    latitude:float
    longitude:float
    original_row_indices:tuple

def source_check():
    r116=ROOT/'results/unified_exact_round116'; snapshot=read(r116/'source/snapshot.json')
    table=r116/'source/source_station_table.csv'; response=ROOT/snapshot['station_response_path']
    assert sha(table)==TABLE_SHA and sha(response)==snapshot['station_response_SHA']==RAW_SHA
    raw=read(response)['data']['stations']
    with table.open(encoding='utf-8',newline='') as f: rows=list(csv.DictReader(f))
    decisions=read(r116/'source/row_decisions.json')
    assert len(raw)==len(rows)==len(decisions)==865
    assert [r['station_id'] for r in rows]==sorted((r['station_id'] for r in rows),key=lambda x:x.encode('utf-8'))
    assert len({r['station_id'] for r in rows})==865
    area=read(r116/'projection_contract.json')['area_of_use']; stations=[]
    for i,r in enumerate(rows):
        assert int(r['source_row_index'])==i and r['raw_source_SHA']==RAW_SHA
        c,lat,lon=int(r['capacity']),float(r['latitude']),float(r['longitude'])
        assert 0<c<100 and area['west']<=lon<=area['east'] and area['south']<=lat<=area['north']
        x,y=float(r['utm18n_easting_unrounded_m']),float(r['utm18n_northing_unrounded_m'])
        assert math.isfinite(x) and math.isfinite(y)
        assert r['utm18n_easting_m']==f'{round(x,3):.3f}' and r['utm18n_northing_m']==f'{round(y,3):.3f}'
        assert abs(float(r['inverse_longitude'])-lon)<1e-10 and abs(float(r['inverse_latitude'])-lat)<1e-10
        indices=tuple(json.loads(r['original_row_indices']))
        for j in indices:
            q=raw[j]; d=decisions[j]
            assert q['station_id']==r['station_id'] and q['capacity']==c and q['lat']==lat and q['lon']==lon
            assert q.get('is_virtual_station') is not True and d['original_row']==q and d['qualified_physical_row']
        stations.append(Station(i,r['station_id'],c,round(x,3),round(y,3),lat,lon,indices))
    return stations

def selection(stations,v=40,g='regional',r=1,selection_id=SELECTION_ID):
    configure(); result=old.build_selection(stations,v,g,r)
    result.update(schema='cabi-round118-geographic-selection-v1',selection_id=selection_id,generator_version=VERSION)
    return result

def landscape(s,stations):
    configure(); value=inherited.landscape(s,'shortage',stations)
    # The pure reference reads no private source: its two source identities are supplied explicitly.
    before=old.sha256_file; old.sha256_file=lambda p:RAW_SHA
    try: expected=old.build_landscape(s,'shortage',stations)
    finally: old.sha256_file=before
    expected['source_hashes']={'public_table_sha256':RAW_SHA}
    actual=copy.deepcopy(value); actual.pop('generation_trace')
    assert actual==expected,'pure generation mathematics changed'
    value.update(schema='cabi-round118-station-landscape-v1',generator_version=VERSION,
        source_hashes={'official_station_response_SHA256':RAW_SHA})
    return value

def freeze():
    assert not REF.exists() and not (OUT/'source_recipe.json').exists()
    OUT.mkdir(parents=True,exist_ok=True)
    deps=['scripts/round118_data.py','scripts/generate_citibike443_regional_v1.py','scripts/round109_data.py']
    write(OUT/'source_recipe.json',dict(round=118,frozen_UTC=utc(),base=BASE,role=ROLE,
        family=FAMILY,selection_id=SELECTION_ID,raw_source_SHA=RAW_SHA,table_SHA=TABLE_SHA,
        adapter_SHA=sha(__file__),generation_dependencies={p:sha(ROOT/p) for p in deps},
        geographic_regimes=['compact','regional'],replicates=[1,2],anchor_slot=2,
        selection='four original anchors; regional/r1; 2V nearest pool; original farthest-first and ties',
        target_fraction=[.44,.56],stock='max(0,sum(D)-max(V,floor(.12*sum(D)+.5)))',
        original_round_clip_correction_sign_repair_weights_and_centroid=True,
        min_ratio_is_compatibility_only=True,production_distances='C++ Parser Euclidean/1.5 from serialized points',
        source_table_reprojection=False,new_network=False,generated_input_count=0,
        target_total_station_set_optimum_H_LP_MIP_and_runtime_unknown_at_freeze=True,
        no_difficulty_filter=True,no_resampling=True))
    print('recipe and generation code frozen; input count=0; Optimize=0')

def generate():
    tick=time.perf_counter(); recipe=read(OUT/'source_recipe.json')
    assert recipe['adapter_SHA']==sha(__file__) and recipe['family']==FAMILY and not REF.exists()
    for p,h in recipe['generation_dependencies'].items(): assert sha(ROOT/p)==h
    # The finite equivalence fixture is artificial and creates no research input file.
    artificial=[Station(i,f'NONREAL-{i:03}',10+i%25,500000.+13*i,4300000.+7*i*i,38.,-75.,(i,)) for i in range(160)]
    trial=selection(artificial,selection_id='NONREAL-pure-equivalence')
    landscape(trial,artificial)
    stations=source_check(); s=selection(stations); value=landscape(s,stations)
    REF.mkdir(parents=True,exist_ok=False)
    lines=old.instance_text(value,ROLE['M'],ROLE['Q_vector'][0]).splitlines()
    lines[0]=f"40 4 {json.dumps(ROLE['Q_vector'])}"
    path=REF/(ROLE['id']+'.txt')
    with path.open('x',encoding='utf-8',newline='\n') as f: f.write('\n'.join(lines).rstrip()+'\n')
    digest=sha(path); historic=read(ROOT/'results/unified_exact_round116/historical_input_hash_index.json')['SHA_to_paths']
    for role in read(ROOT/'results/unified_exact_round116/input_manifest.json')['roles']:
        historic.setdefault(role['input_sha256'],[]).append(role['input_path'])
    if digest in historic: raise RuntimeError('DATA_IDENTITY_BLOCKED: duplicate input; no redraw authorized')
    parsed=old.parse_instance_mirror(path)
    assert parsed['V']==40 and parsed['M']==4 and parsed['Q']==ROLE['Q_vector']
    assert all(0<=b<=c and 0<d<=c for b,c,d in zip(value['initial'],value['capacities'],value['target']))
    assert len(set(s['selected_source_station_row_indices']))==40
    assert all(w>0 for w in value['weights']) and max(value['weights'])==1
    assert value['depot']['coordinate_utm18n_meters']==[round(statistics.fmean(q[j] for q in parsed['points'][1:]),3) for j in range(2)]
    for suffix,obj in [('selection',s),('landscape',value),('parsed',parsed)]: write(REF/(ROLE['id']+'_'+suffix+'.json'),obj)
    mapping=[dict(local_station_index=j,**dataclasses.asdict(stations[i]),source_response_SHA=RAW_SHA)
        for j,i in enumerate(s['selected_source_station_row_indices'],1)]
    write(REF/(ROLE['id']+'_source_mapping.json'),mapping)
    overlap=[]
    chosen=set(s['selected_source_station_row_indices'])
    for role in read(ROOT/'results/unified_exact_round116/input_manifest.json')['roles']:
        if role['V']<=50:
            prev=read(ROOT/role['selection_path'])['selected_source_station_row_indices']
            overlap.append(dict(id=role['id'],overlap=len(chosen&set(prev)),old_V=role['V'],new_V=40))
    role=copy.deepcopy(ROLE)
    role.update(input_path=path.relative_to(ROOT).as_posix(),instance_path=path.relative_to(ROOT).as_posix(),
        input_sha256=digest,input_bytes=path.stat().st_size,
        selection_path=(REF/(ROLE['id']+'_selection.json')).relative_to(ROOT).as_posix(),
        landscape_path=(REF/(ROLE['id']+'_landscape.json')).relative_to(ROOT).as_posix(),
        source_response_SHA=RAW_SHA,source_recipe_SHA=sha(OUT/'source_recipe.json'),
        total_initial=sum(value['initial']),total_target=sum(value['target']),role_identity='unmeasured_after_once_only_generation')
    write(OUT/'input_manifest.json',dict(roles=[role],family=FAMILY,source_table_SHA=TABLE_SHA,raw_station_response_SHA=RAW_SHA,
        recipe_SHA=sha(OUT/'source_recipe.json'),generated_once=True,overlaps=overlap,historical_input_duplicates=False))
    write(OUT/'generation_receipt.json',dict(generated_UTC=utc(),source_recipe_SHA=sha(OUT/'source_recipe.json'),
        input_SHA=digest,unique_input_files_written=1,new_research_roles=1,pure_artificial_equivalence=True,
        source_rows=865,source_table_SHA=TABLE_SHA,source_response_SHA=RAW_SHA,stock_B=role['total_initial'],
        Dsum=role['total_target'],Delta_stock=value['generation_trace']['delta_amount'],
        actual_shortage=role['total_target']-role['total_initial'],overlaps=overlap,
        native_starts=0,Optimize=0,H_LP_MIP_or_difficulty_screen=False,engineering_seconds=time.perf_counter()-tick))
    print(json.dumps(dict(input_SHA=digest,B=role['total_initial'],Dsum=role['total_target'],input_count=1,Optimize=0)))

if __name__=='__main__': {'freeze':freeze,'generate':generate}[sys.argv[1]]()
