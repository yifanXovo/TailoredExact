"""One-shot unused inputs, frozen after the uniform candidate; zero Optimize."""
import sys
import round96_prepare as generation
from round99_common import *
VERSION='round99-discrete-structure-confirmation-v1'
ROLES=[
    dict(id='N1',V=20,M=2,Q_vector=[16,24],geometry='offset_annulus',inventory='surplus',T_seconds=4500,cap_seconds=900),
    dict(id='N2',V=30,M=3,Q_vector=[16,22,28],geometry='bent_corridor',inventory='shortage',T_seconds=6600,cap_seconds=1800),
    dict(id='N3',V=50,M=4,Q_vector=[18,24,30,36],geometry='anisotropic_cloud',inventory='shortage',T_seconds=7800,cap_seconds=3600)]
ORDERS=[['P-GRB','M-B','ENS-C'],['ENS-C','P-GRB','M-B'],['M-B','ENS-C','P-GRB']]
def recipe():
    return dict(version=VERSION,roles=ROLES,orders=ORDERS,source_sha256=sha(__file__),
        landscape_source_sha256=sha(generation.__file__),writer_sha256=sha(generation.citi.__file__),
        seed='SHA256(version|id|field), first8 bytes /2^64',optimizer_calls=0,
        relation_to_history='Reuse R96 deterministic geometric/inventory families and text writer; new version/id seed, points, inventory, heterogeneous fleets and mathematical T. Families appeared in historical R96/R97; these bytes and outcomes have never been observed.',
        retention='Retain all3 inputs and all zero/difficult/negative outcomes. No reseed, replacement, resizing, T adjustment or outcome-based switch.',
        maximum_formal_starts=9,maximum_formal_seconds=18900,
        finite_reference_children=3,maximum_reference_child_seconds=60)
def freeze():
    assert read(OUT/'candidate_freeze.json')['selected_arm']=='M-B'
    write(OUT/'confirmation_generation_recipe.json',recipe())
def generate():
    assert read(OUT/'confirmation_generation_recipe.json')==recipe()
    selected=read(OUT/'candidate_freeze.json')
    assert selected['selected_arm']=='M-B' and selected['source_bindings']==bindings()
    assert selected['binary_sha256']==sha(BUILD/'ExactEBRP.exe')
    data=ROOT/'reference/round99_confirmation';assert not data.exists();data.mkdir()
    generation.VERSION=VERSION;roles=[]
    for r,order in zip(ROLES,ORDERS):
        obj=generation.landscape(r);path=data/(r['id']+'.txt')
        lines=generation.citi.instance_text(obj,r['M'],r['Q_vector'][0]).splitlines()
        lines[0]=f'{r["V"]} {r["M"]} {r["Q_vector"]}'
        with path.open('x',encoding='utf-8',newline='\n') as f:f.write('\n'.join(lines)+'\n')
        parsed=generation.citi.parse_instance_mirror(path)
        assert parsed['V']==r['V'] and parsed['M']==r['M'] and parsed['Q']==r['Q_vector']
        assert all(0<=b<=c and 0<d<=c for b,d,c in zip(obj['initial'],obj['target'],obj['capacities']))
        assert len(set(map(tuple,parsed['points'])))==r['V']+1
        shortage=sum(obj['initial'])<sum(obj['target'])
        if r['inventory']=='shortage':assert shortage
        roles.append(dict(r,method_order=order,input_path=path.relative_to(ROOT).as_posix(),
            instance_path=path.relative_to(ROOT).as_posix(),input_sha256=sha(path),scenario_id=VERSION+'-'+r['id'],
            pickup_seconds=60,drop_seconds=60,**{'lambda':.15},total_initial=sum(obj['initial']),
            total_target=sum(obj['target']),zero_excluded_by_stock_shortage=shortage))
    write(OUT/'confirmation_protocol01.json',dict(roles=roles,recipe_sha256=sha(OUT/'confirmation_generation_recipe.json'),
        candidate_freeze_sha256=sha(OUT/'candidate_freeze.json'),optimizer_calls=0,phase='frozen independent confirmation',
        reference_billing='one_finite_batch',native_budget_scope='9 complete production processes, all self-paid startup; no diagnostic state import'))
    print('Retained N1/N2/N3 once; zero Optimize; no outcomes read')
if __name__=='__main__':{'freeze':freeze,'generate':generate}[sys.argv[1]]()
