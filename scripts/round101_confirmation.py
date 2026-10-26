"""One-time deterministic design-isolated inputs, admitted only after freeze.
No native process or Optimize. No outcome filter, redraw, reseed or replacement.
"""
import math,random,sys,ast
from round101_common import *

RECIPES=[
    dict(id='C101-V20',V=20,M=2,Q_vector=[18,26],T_seconds=4800,cap_seconds=1800,
         seed=101201,geometry='curved_corridor',order=['ENS-C','FLEET','P-GRB']),
    dict(id='C101-V30',V=30,M=3,Q_vector=[15,23,31],T_seconds=7200,cap_seconds=7200,
         seed=101301,geometry='elliptic_two_bands',order=['P-GRB','FLEET','ENS-C']),
    dict(id='C101-V50',V=50,M=4,Q_vector=[20,26,32,38],T_seconds=7200,cap_seconds=1800,
         seed=101501,geometry='offset_lattice',order=['FLEET','P-GRB','ENS-C'])]

def generate(freeze_path):
    freeze=read(freeze_path)
    assert freeze['confirmation_generator_sha256']==sha(__file__)
    assert freeze['source_hashes']==bindings()
    assert freeze['candidate_binary_sha256']==sha(BUILD/'ExactEBRP.exe')
    assert freeze['fleet_arm'] in ['FLEET-ROOT','FLEET-SUBMIT']
    assert freeze['candidate_frozen_before_confirmation_inputs'] is True
    directory=ROOT/'reference/round101_confirmation';directory.mkdir(exist_ok=False)
    roles=[]
    for recipe in RECIPES:
        p=dict(recipe);rng=random.Random(p['seed']);n=p['V']
        points=[(585250.,4512250.)];target=[0];initial=[50000];capacity=[100000];weights=[0.]
        for i in range(n):
            demand=rng.randint(16,26)
            if p['geometry']=='curved_corridor':
                x=-1050+110*i;y=450*math.sin(i*math.pi/8)
                stock=demand+(10 if i%3==0 else -7)
            elif p['geometry']=='elliptic_two_bands':
                angle=2*math.pi*i/n;radius=1.0 if i%2==0 else .68
                x=1200*radius*math.cos(angle);y=700*radius*math.sin(angle)
                stock=demand+(11 if i%3==0 else -8)
            else:
                x=(i%10-4.5)*230;y=(i//10-2)*250
                stock=demand+(6 if i%4 in [0,1] else -9)
            points.append((round(585250+x+rng.uniform(-35,35),3),round(4512250+y+rng.uniform(-35,35),3)))
            target.append(demand);initial.append(stock);capacity.append(demand+14)
            weights.append(round(rng.uniform(.35,.95),6))
        text=f'{n} {p["M"]} {p["Q_vector"]}\n'
        text+='capacities = '+str(capacity)+'\ninitial = '+str(initial)+'\ntarget = '+str(target)+'\n'
        text+='weights = '+str(weights)+'\n'
        ratios=[0.]+[round(min(.7,initial[i]/target[i]),4) for i in range(1,n+1)]
        text+='min_ratio = '+str(ratios)+'\npoints = '+str(points)+'\n'
        path=directory/(p['id']+'.txt');path.write_bytes(text.encode('utf-8'))
        # Structural input validity is checked after writing and never triggers a redraw.
        assert all(0<=initial[i]<=capacity[i] and target[i]>0 and weights[i]>0 for i in range(1,n+1))
        assert sum(initial[1:])<sum(target[1:])
        p.update(input_path=path.relative_to(ROOT).as_posix(),instance_path=path.relative_to(ROOT).as_posix(),
            input_sha256=sha(path),scenario_id='round101-fleet-design-isolated-v1-'+p['id'],
            pickup_seconds=60,drop_seconds=60,**{'lambda':.15},inventory='deterministic paired shortage',
            total_initial=sum(initial[1:]),total_target=sum(target[1:]),zero_excluded_by_stock_shortage=True,
            method_order=[freeze['fleet_arm'] if a=='FLEET' else a for a in p.pop('order')])
        roles.append(p)
    write(OUT/'confirmation_protocol01.json',dict(roles=roles,phase='fleet confirmation',
        reference_billing='one_finite_batch',maximum_optimize_calls_per_arm=2048,
        planning_call_envelope_not_production_gate=True,generator_sha256=sha(__file__),
        candidate_freeze_path=str(Path(freeze_path).resolve()),candidate_freeze_sha256=sha(freeze_path),
        inputs_generated_after_candidate_freeze=True,all_generated_outputs_retained=True,
        no_redraw_reseed_or_outcome_replacement=True,
        nonzero_reason='Empty departure and nonnegative loaded return imply total final station inventory cannot exceed initial station stock. Initial stock is below target sum and all penalty weights/lambda are positive, so F=0 is impossible. No station-stock equality is imposed.',
        maximum_formal_starts=9,maximum_formal_seconds=sum(p['cap_seconds']*3 for p in roles)))
    print(json.dumps(dict(generated_roles=[p['id'] for p in roles],maximum_formal_seconds=sum(p['cap_seconds']*3 for p in roles),Optimize=0)))

if __name__=='__main__':generate(sys.argv[1])
