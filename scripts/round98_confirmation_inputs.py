"""One-shot isolated confirmation recipe; freeze then generate, zero Optimize.

Reuse the R96 deterministic landscape and original instance text writer, with
a new version seed. No result files, previous winners or optimum are accessed.
"""
import sys
import round96_prepare as generation
from round98_common import *
VERSION='round98-state-service-confirmation-v1'
ROLES=[
    dict(id='C1',V=20,M=2,Q_vector=[12,18],geometry='three_clusters',inventory='surplus',T_seconds=4800,cap_seconds=900),
    dict(id='C2',V=30,M=3,Q_vector=[20,25,30],geometry='radial_spokes',inventory='shortage',T_seconds=7200,cap_seconds=1800),
    dict(id='C3',V=50,M=4,Q_vector=[20,25,30,35],geometry='separated_islands',inventory='shortage',T_seconds=7200,cap_seconds=3600)]
ORDERS=[['P-GRB','R2','ENS-C'],['ENS-C','P-GRB','R2'],['R2','ENS-C','P-GRB']]
def recipe():
    return dict(version=VERSION,roles=ROLES,orders=ORDERS,source_sha256=sha(__file__),
        landscape_source_sha256=sha(generation.__file__),writer_sha256=sha(generation.citi.__file__),
        seed='SHA256(version|id|field), first8 bytes /2^64',optimizer_calls=0,
        retention='All generated roles retained, including zero, difficult and negative outcomes; no reseed or T adjustment',
        isolation='No Round98 design solves or optimizer-informed data selection; new geography/inventory/fleet combinations',
        maximum_starts=9,maximum_process_seconds=18900)
def freeze():write(OUT/'confirmation_generation_recipe.json',recipe())
def generate():
    assert read(OUT/'confirmation_generation_recipe.json')==recipe()
    assert (OUT/'candidate_freeze.json').is_file(),'candidate rules freeze before generation'
    assert read(OUT/'candidate_freeze.json')['selected_arm']=='R2','orders name the frozen uniform R2 candidate'
    data=ROOT/'reference/round98_confirmation';assert not data.exists();data.mkdir()
    generation.VERSION=VERSION;roles=[]
    for r,order in zip(ROLES,ORDERS):
        obj=generation.landscape(r);path=data/(r['id']+'.txt')
        contents=generation.citi.instance_text(obj,r['M'],r['Q_vector'][0]).splitlines()
        contents[0]=f'{r["V"]} {r["M"]} {r["Q_vector"]}'
        with path.open('x',encoding='utf-8',newline='\n') as f:f.write('\n'.join(contents)+'\n')
        parsed=generation.citi.parse_instance_mirror(path);assert parsed['Q']==r['Q_vector']
        assert all(0<=b<=c and 0<d<=c for b,d,c in zip(obj['initial'],obj['target'],obj['capacities']))
        assert len(set(map(tuple,parsed['points'])))==r['V']+1
        roles.append(dict(r,method_order=order,input_path=path.relative_to(ROOT).as_posix(),
            instance_path=path.relative_to(ROOT).as_posix(),input_sha256=sha(path),scenario_id=VERSION+'-'+r['id'],
            pickup_seconds=60,drop_seconds=60,**{'lambda':.15},total_initial=sum(obj['initial']),
            total_target=sum(obj['target']),zero_excluded_by_stock_shortage=sum(obj['initial'])<sum(obj['target'])))
    write(OUT/'confirmation_protocol01.json',dict(roles=roles,recipe_sha256=sha(OUT/'confirmation_generation_recipe.json'),
        candidate_freeze_sha256=sha(OUT/'candidate_freeze.json'),optimizer_calls=0,phase='frozen independent confirmation',
        reference_billing='one_finite_batch'))
if __name__=='__main__':{'freeze':freeze,'generate':generate}[sys.argv[1]]()
