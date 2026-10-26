"""Prospectively frozen four-role data generator; never screen, replace or regenerate."""
import hashlib
import json
import math
import statistics
import subprocess
import time
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / 'results/unified_exact_round86'
DATA = ROOT / 'reference/round86_unadapted_confirmation'
CANDIDATE_SOURCE = '4496078f25c0cdad1cf7a5c39835fd23121e8978'
VERSION = 'round86-unadapted-varied-structures-v1'
ROLES = [
    dict(id='F1', family='citibike', V=12, M=2, Q=20, geography='regional', inventory='surplus', T_seconds=3600, cap=120),
    dict(id='F2', family='synthetic', V=20, M=2, Q=30, geometry='alternating_rings', inventory='paired_shortage', T_seconds=3600, cap=300),
    dict(id='F5', family='synthetic', V=50, M=4, Q=30, geometry='perturbed_grid', inventory='paired_shortage', T_seconds=7200, cap=3600),
    dict(id='F6', family='citibike', V=50, M=4, Q=30, geography='compact', inventory='shortage', T_seconds=18000, cap=3600),
]
RANGES = {'F2': dict(D=[20,28], a=[8,12], delta=[3,6]),
          'F5': dict(D=[14,24], a=[3,8], delta=[2,5])}


def read(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
def canonical(value): return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True)
def material(role): return CANDIDATE_SOURCE+'|'+VERSION+'|'+canonical(role)
def digest(role, field): return hashlib.sha256((material(role)+'|'+field).encode('utf-8')).digest()
def integer(role, field, lo, hi): return lo+int.from_bytes(digest(role,field),'big')%(hi-lo+1)
def unit(role, field): return int.from_bytes(digest(role,field)[:8],'big')/(2**64-1)


def preregistration(base):
    import generate_citibike443_regional_v1 as citi
    return dict(base=base, candidate_source=CANDIDATE_SOURCE, version=VERSION,
        roles=ROLES, synthetic_ranges=RANGES,
        seed_material={r['id']:material(r) for r in ROLES},
        citi_namespace={r['id']:'citibike443-'+VERSION+'-'+hashlib.sha256(material(r).encode('utf-8')).hexdigest()
                        for r in ROLES if r['family']=='citibike'},
        citi_replicate=1, citi_selection_prefix='round86_',
        field_hash='SHA256(UTF8(candidate source|version|canonical role JSON|field)); integer=full big-endian modulo inclusive range; unit=first8 big-endian/(2^64-1)',
        coordinates='Translated by (584400,4511800) meters and rounded to3 decimals; depot is rounded centroid of serialized points; parser Euclidean/1.5m/s',
        weights='Synthetic 0.25+0.75*hash unit, rounded6 decimals; inherited CitiBike weights unchanged',
        min_ratio='Synthetic 0.7*min(initial,target)/target, rounded4 decimals; depot0; inherited CitiBike formula unchanged',
        original_lambda=.15, pickup_seconds=60, drop_seconds=60,
        generators={str(Path(p).relative_to(ROOT)):sha(p) for p in [__file__,citi.__file__]},
        generated_inputs_exist=False, optimizer_calls=0, planned_runs=12,
        maximum_process_seconds=3*sum(r['cap'] for r in ROLES),
        policy='Keep all four admitted generated roles; no outcome screening, reseeding, resizing, T adjustment or best-repeat selection.')


def synthetic_landscape(role):
    spec=RANGES[role['id']]; n=role['V']; points=[]
    for j in range(n):
        if role['geometry']=='alternating_rings':
            angle=2*math.pi*j/n+(2*unit(role,f'angle:{j}')-1)*.04
            radius=700+300*(j%2)+(2*unit(role,f'radius:{j}')-1)*50
            x,y=radius*math.cos(angle),radius*math.sin(angle)
        elif role['geometry']=='two_lane_corridor':
            x=150*(j//2)+(2*unit(role,f'x:{j}')-1)*40
            y=(-175 if j%2==0 else 175)+(2*unit(role,f'y:{j}')-1)*40
        elif role['geometry']=='perturbed_grid':
            x=220*(j%10)+(2*unit(role,f'x:{j}')-1)*40
            y=220*(j//10)+(2*unit(role,f'y:{j}')-1)*40
        else: raise ValueError(role['geometry'])
        points.append([round(584400+x,3),round(4511800+y,3)])
    target=[integer(role,f'target:{j}',*spec['D']) for j in range(n)]
    capacity=[target[j]+spec['a'][1]+integer(role,f'capacity_slack:{j}',4,12) for j in range(n)]
    order=sorted(range(n),key=lambda j:(digest(role,f'pair_order:{j}'),j))
    initial=target.copy();pairs=[]
    for k in range(n//2):
        donor,receiver=order[2*k:2*k+2]
        a=integer(role,f'transfer:{k}',*spec['a']);delta=integer(role,f'shortage:{k}',*spec['delta'])
        initial[donor]+=a;initial[receiver]-=a+delta
        pairs.append(dict(donor_service_index=donor+1,receiver_service_index=receiver+1,a=a,delta=delta))
    weights=[round(.25+.75*unit(role,f'weight:{j}'),6) for j in range(n)]
    ratios=[round(.7*min(b,d)/d,4) for b,d in zip(initial,target)]
    assert all(0<=b<=c and 0<d<=c for b,d,c in zip(initial,target,capacity))
    assert sum(target)-sum(initial)==sum(p['delta'] for p in pairs)>0
    return dict(schema=VERSION, classification='prospectively_generated_unadapted_confirmation',
        V=n, geometry=role['geometry'], role=role, seed_derivation_material=material(role),
        depot=dict(artificial=True, coordinate_utm18n_meters=[round(statistics.fmean(p[k] for p in points),3) for k in [0,1]],
                   capacity_placeholder=100000,initial_placeholder=50000,target_placeholder=0),
        capacities=capacity, initial=initial, target=target, weights=weights,
        min_ratio=ratios, points_utm18n_meters=points, construction_pairs=pairs)


def structural_record(role, parsed, citi):
    b=parsed['initial'][1:];d=parsed['target'][1:];c=parsed['capacities'][1:];w=parsed['weights'][1:]
    assert all(0<=a<=cap and 0<t<=cap for a,t,cap in zip(b,d,c))
    assert all(math.isfinite(x) and x>0 for x in w)
    shortage=sum(d)-sum(b); surplus=sum(a>t for a,t in zip(b,d)); deficit=sum(a<t for a,t in zip(b,d))
    assert surplus and deficit
    bound=Fraction(3,20)*min(Fraction(str(x))/int(t) for x,t in zip(w,d))*max(shortage,0)
    required_pickup=sum(max(a-t,0) for a,t in zip(b,d))
    handling_capacity=Fraction(role['M']*role['T_seconds'],120)
    return dict(id=role['id'], V=role['V'], M=role['M'], Q=role['Q'],
        total_initial=sum(b),total_target=sum(d),shortage=shortage,
        surplus_stations=surplus,deficit_stations=deficit,
        required_pickup_for_zero=required_pickup,handling_only_pickup_capacity=float(handling_capacity),
        zero_analytically_excluded=shortage>0 or required_pickup>handling_capacity,
        zero_exclusion_reason='global_stock_shortage' if shortage>0 else 'necessary_handling_exceeds_fleet_time' if required_pickup>handling_capacity else 'not_established',
        input_only_penalty_bound=dict(numerator=bound.numerator,denominator=bound.denominator,value=float(bound)),
        bound_scope='Elementary structural diagnostic only; not an algorithm input, native solver certificate or difficulty selection rule.',
        geographic_statistics=citi.pairwise_stats(parsed['points'][1:],parsed['points'][0]))


def main():
    started=time.perf_counter()
    assert Path(__file__).parent==ROOT/'scripts','Preparation copy cannot generate data'
    import generate_citibike443_regional_v1 as citi
    frozen=read(STAGE/'preregistration.json')
    assert frozen==preregistration(frozen['base']), 'Frozen recipe changed'
    assert read(STAGE/'base_publication.json')['head_sha']==frozen['base']
    prior=ROOT/'results/unified_exact_round85'
    assert not (prior/'campaign/active_run.lock').exists()
    assert read(prior/'campaign/driver_completion.json')['all_valid']
    assert read(prior/'campaign/replication_audit.json')['all_checks_passed']
    branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT).decode().strip()
    assert branch=='codex/round86-ensc-varied-unadapted-confirmation'
    assert not DATA.exists() and not (STAGE/'generation.json').exists(), 'Never regenerate or replace'
    for path in [Path(__file__),STAGE/'preregistration.json',STAGE/'plan.md',STAGE/'base_publication.json']:
        assert not subprocess.check_output(['git','status','--porcelain','--',str(path)],cwd=ROOT).strip(),path
    freeze=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()
    citi.require_authoritative_hashes();stations,source_meta=citi.load_source_stations()
    DATA.mkdir();panels=[];structures=[];selections=[]
    for role in ROLES:
        path=DATA/(role['id']+'.txt')
        if role['family']=='synthetic':
            landscape=synthetic_landscape(role)
        else:
            citi.FAMILY=frozen['citi_namespace'][role['id']]
            selection=citi.build_selection(stations,role['V'],role['geography'],frozen['citi_replicate'])
            selection['selection_id']=frozen['citi_selection_prefix']+role['id']+'_'+selection['selection_id']
            landscape=citi.build_landscape(selection,role['inventory'],stations)
            landscape['classification']='prospectively_generated_unadapted_confirmation'
            write(DATA/(role['id']+'_selection.json'),selection)
            selections.append(dict(id=role['id'],indices=selection['selected_source_station_row_indices']))
        path.write_text(citi.instance_text(landscape,role['M'],role['Q']),encoding='utf-8',newline='\n')
        write(DATA/(role['id']+'_landscape.json'),landscape)
        parsed=citi.parse_instance_mirror(path)
        assert (parsed['V'],parsed['M'],parsed['Q'])==(role['V'],role['M'],[role['Q']]*role['M'])
        structures.append(structural_record(role,parsed,citi))
        panels.append(dict(role, instance_path=path.relative_to(ROOT).as_posix(),input_sha256=sha(path),
            scenario_id=VERSION+'_'+role['id'],pickup_seconds=60,drop_seconds=60,
            stage='confirmation_unadapted',role='Prospectively frozen varied structure; all generated outcomes retained',**{'lambda':.15}))
    old=[]
    paths=sorted((ROOT/'reference/citibike443-regional-v1/selections').glob('*/*.json'))
    paths+=sorted((ROOT/'reference/round82_unadapted_confirmation').glob('*_selection.json'))
    for path in paths:
        value=read(path)
        old.append(dict(id=value['selection_id'],path=path.relative_to(ROOT).as_posix(),sha256=sha(path),indices=value['selected_source_station_row_indices']))
    overlap=[]
    for i,a in enumerate(selections):
        for b in old+selections[i+1:]:
            x,y=set(a['indices']),set(b['indices'])
            overlap.append(dict(new_id=a['id'],other_id=b['id'],shared=len(x&y),new_count=len(x),other_count=len(y),jaccard=len(x&y)/len(x|y)))
    write(STAGE/'protocol.json',dict(base=frozen['base'],candidate_source=CANDIDATE_SOURCE,panel=panels,
        order=[r['id'] for r in ROLES],arms=['P-GRB','ENS-C','K1-R'],all_inputs_exposed=False,
        prior_bindings={},maximum_process_seconds=22860,
        checkpoints={'120':[30,60,120],'300':[60,120,180,300],'3600':[300,600,1200,1800,2400,3600]}))
    write(STAGE/'generation.json',dict(freeze_commit=freeze,preregistration_sha256=sha(STAGE/'preregistration.json'),
        plan_sha256=sha(STAGE/'plan.md'),generators=frozen['generators'],structures=structures,
        overlap=overlap,old_selection_sources=old,source_annotation_limits=source_meta,
        optimizer_calls=0,wall_seconds=time.perf_counter()-started,generated_count=4,screened_or_rejected_count=0,
        input_sha256={p['id']:p['input_sha256'] for p in panels},
        interpretation='Unadapted outcomes on frozen varied recipes; related443-station geography and artificial synthetic shapes, not independent-city validation.'))
    print(json.dumps(dict(generated=4,structures=structures,optimizer_calls=0),indent=2))


if __name__=='__main__':main()
