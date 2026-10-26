"""Prospective six-role confirmation inputs; data only, never optimize."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import time
import generate_hard_exact_stress_instances as synthetic
import generate_citibike443_regional_v1 as citi

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / 'results/unified_exact_round82'
BASE = '298e97f5d163a54eb9d899c664cafd9f07c8647c'
VERSION = 'round82-unadapted-confirmation-v1'
DATA = ROOT / 'reference/round82_unadapted_confirmation'
ROLES = [
    dict(id='U1', family='synthetic', V=12, M=1, Q=20, stress='tight_T', T_seconds=2400, cap=120),
    dict(id='U2', family='citibike', V=12, M=2, Q=30, geography='compact', inventory='surplus', T_seconds=3600, cap=120),
    dict(id='U3', family='synthetic', V=20, M=2, Q=30, stress='high_imbalance', T_seconds=3600, cap=300),
    dict(id='U4', family='citibike', V=30, M=3, Q=20, geography='regional', inventory='balanced', T_seconds=3600, cap=3600),
    dict(id='U5', family='synthetic', V=50, M=3, Q=20, stress='moderate', T_seconds=3600, cap=3600),
    dict(id='U6', family='citibike', V=50, M=4, Q=30, geography='compact', inventory='shortage', T_seconds=18000, cap=3600),
]

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def write(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')

def seed_material(role):
    return BASE+'|'+VERSION+'|'+json.dumps(role, sort_keys=True, separators=(',', ':'))

def preregistration():
    return dict(base=BASE, version=VERSION, roles=ROLES,
        synthetic_seeds={r['id']:dict(material=seed_material(r),
            seed=10000+int(hashlib.sha256(seed_material(r).encode()).hexdigest()[:16],16)%1900000000)
            for r in ROLES if r['family']=='synthetic'},
        citi_family_namespace='citibike443-'+VERSION+'-'+BASE,
        citi_replicate=1, citi_selection_id_prefix='round82_',
        generators={str(Path(p).relative_to(ROOT)):sha(p) for p in [__file__,synthetic.__file__,citi.__file__]},
        generated_inputs_exist=False, optimizer_calls=0, planned_runs=18,
        maximum_process_seconds=3*sum(r['cap'] for r in ROLES),
        policy='All six fixed roles retained, no outcome screening, reseeding, resizing or T adjustment.')

def main():
    start=time.perf_counter()
    frozen=json.loads((STAGE/'preregistration.json').read_text(encoding='utf-8'))
    assert frozen==preregistration(), 'Pre-generation recipe must remain frozen'
    assert not DATA.exists() and not (STAGE/'generation.json').exists(), 'Never overwrite or regenerate'
    assert not subprocess.check_output(['git','status','--porcelain','--',__file__,
        STAGE/'preregistration.json',STAGE/'plan.md'],cwd=ROOT).strip(), 'Commit recipe before generation'
    freeze_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()
    citi.require_authoritative_hashes()
    stations, source_meta=citi.load_source_stations()
    citi.FAMILY=frozen['citi_family_namespace']
    DATA.mkdir()
    panels=[];structures=[];selections=[]
    for role in ROLES:
        p=dict(role, lambda_=0.15)
        path=DATA/(role['id']+'.txt')
        if role['family']=='synthetic':
            seed=frozen['synthetic_seeds'][role['id']]['seed']
            description=synthetic.write_instance(path,seed,role['stress'],role['T_seconds'],
                v=role['V'],m=role['M'],q=role['Q'])
        else:
            selection=citi.build_selection(stations,role['V'],role['geography'],frozen['citi_replicate'])
            selection['selection_id']=frozen['citi_selection_id_prefix']+selection['selection_id']
            landscape=citi.build_landscape(selection,role['inventory'],stations)
            landscape['classification']='prospectively_generated_unadapted_confirmation'
            path.write_text(citi.instance_text(landscape,role['M'],role['Q']),encoding='utf-8',newline='\n')
            write(DATA/(role['id']+'_selection.json'),selection)
            write(DATA/(role['id']+'_landscape.json'),landscape)
            description=landscape
            selections.append(dict(id=role['id'],indices=selection['selected_source_station_row_indices']))
        parsed=citi.parse_instance_mirror(path)
        assert (parsed['V'],parsed['M'],parsed['Q'])==(role['V'],role['M'],[role['Q']]*role['M'])
        assert all(d>0 for d in parsed['target'][1:]) and all(w>0 for w in parsed['weights'][1:])
        b=parsed['initial'][1:];d=parsed['target'][1:];caps=parsed['capacities'][1:]
        assert all(0<=a<=c and 0<t<=c for a,t,c in zip(b,d,caps))
        shortage=sum(d)-sum(b)
        zero_pickup=sum(max(a-t,0) for a,t in zip(b,d))
        handling_capacity=role['M']*role['T_seconds']/120
        # Necessary conditions only, not an optimizer or performance selection.
        zero_excluded=shortage>0 or zero_pickup>handling_capacity
        structures.append(dict(id=role['id'],V=role['V'],M=role['M'],Q=role['Q'],
            total_initial=sum(b),total_target=sum(d),shortage=shortage,
            required_pickup_for_zero=zero_pickup,handling_only_pickup_capacity=handling_capacity,
            zero_analytically_excluded=zero_excluded,
            zero_exclusion_reason='global_stock_shortage' if shortage>0 else
                'necessary_handling_exceeds_fleet_time' if zero_pickup>handling_capacity else 'not_established',
            diameter_m=citi.pairwise_stats(parsed['points'][1:],parsed['points'][0])['geographic_diameter_m']))
        panel=dict(role,instance_path=path.relative_to(ROOT).as_posix(),input_sha256=sha(path),
            scenario_id=VERSION+'_'+role['id'],pickup_seconds=60,drop_seconds=60,
            stage='confirmation_unadapted',role='Prospectively fixed structural role; see Round82 plan')
        panel['lambda']=.15
        panels.append(panel)
        write(DATA/(role['id']+'_generation.json'),description)
    # Metadata-only overlap check; never used to select or replace samples.
    old=[]
    for path in sorted((ROOT/'reference/citibike443-regional-v1/selections').glob('*/*.json')):
        value=json.loads(path.read_text(encoding='utf-8'))
        old.append(dict(id=value['selection_id'],indices=value['selected_source_station_row_indices']))
    overlap=[]
    for i,a in enumerate(selections):
        for b in old+selections[i+1:]:
            x,y=set(a['indices']),set(b['indices'])
            overlap.append(dict(new_id=a['id'],other_id=b['id'],shared=len(x&y),
                new_count=len(x),other_count=len(y),jaccard=len(x&y)/len(x|y)))
    write(STAGE/'protocol.json',dict(base=BASE,panel=panels))
    write(STAGE/'generation.json',dict(freeze_commit=freeze_commit,
        preregistration_sha256=sha(STAGE/'preregistration.json'),plan_sha256=sha(STAGE/'plan.md'),
        generators=frozen['generators'],structures=structures,overlap=overlap,
        source_annotation_limits=source_meta,optimizer_calls=0,wall_seconds=time.perf_counter()-start,
        generated_count=6,screened_or_rejected_count=0,
        input_sha256={p['id']:p['input_sha256'] for p in panels},
        interpretation='Fresh draws from established recipes; correlated source geography and familiar recipes, not new independent cities.'))
    print(json.dumps(dict(generated=6,structures=structures,optimizer_calls=0),indent=2))

if __name__=='__main__':main()
