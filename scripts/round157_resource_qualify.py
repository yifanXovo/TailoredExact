"""Validate new resource inequalities by saved-route lifts and tiny tours."""
from itertools import permutations,combinations
from fractions import Fraction as F
from round157_resource import travel_bounds,fixed_model,resource_lift
from round157_inventory import instance
from round157_fleet import verify
from round157_qualify import micro,enumerated
from round157_common import *

def run():
    from round100_gurobi_runtime import gp,binding
    from round143_lp import residual
    from round150_lp import affinity
    affinity();assert binding()['sha256']==DLL_SHA
    target=OUT/'qualification/resource_v1';target.mkdir(parents=True,exist_ok=False);facts=[]
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        for role,source in read(OUT/'inventory_families.json').items():
            data=instance(source['panel']);witness=source['positive_control']['witness'];checked=verify(data,witness)
            supports={i:[v] for i,v in enumerate(checked['Y'],1)}
            active=[i for i,vs in supports.items() if vs[0]!=data['initial'][i]]
            bounds=travel_bounds(data,active);m,ref=fixed_model(data,supports,None,env,bounds)
            point=resource_lift(data,ref,witness);q=residual(m,point)
            assert q['constraints']<=1e-7 and q['bounds']<=1e-7,q
            path=target/f'{role}.mps';m.write(str(path))
            write(target/f'{role}_lift.json',dict(point=point,quality=q,bounds=bounds,model_SHA=sha(path),
                witness_source_SHA=source['positive_control']['SHA'],physical=checked))
            m.dispose()
            facts.append(dict(role=role,actual_physical_witness_all_resource_rows='PASS',subsets=len(bounds),quality=q))
        # Every subset-tour bound is checked against every longer tiny tour.
        data=micro([2,0,2,0],[1,1,1,1],[3],100,positions=[0,2,10,9,5])
        bounds=travel_bounds(data,list(range(1,5)));checked_tours=0
        for length in range(1,5):
            for subset in combinations(range(1,5),length):
                for order in permutations(subset):
                    tour=(0,)+order+(0,)
                    actual=sum((F(data['distance'][i][j]) for i,j in zip(tour,tour[1:])),F(0))
                    for bound in bounds:
                        if set(bound['stations'])<=set(subset):
                            assert F(bound['lower'])<=F(bound['exact'])<=actual
                    checked_tours+=1
        # Heterogeneous capacities and loaded return retain a valid route lift;
        # a resource feasible point is deliberately never called a route.
        for name,b,Y,Q,T in [('loaded_return',[3],[1],[2],4),('heterogeneous',[3,0],[1,2],[1,3],12)]:
            data=micro(b,Y,Q,T);witness=enumerated(data,[Y]);assert witness
            bounds=travel_bounds(data,list(range(1,len(Y)+1)))
            m,ref=fixed_model(data,{i:[v] for i,v in enumerate(Y,1)},None,env,bounds)
            q=residual(m,resource_lift(data,ref,witness));assert q['constraints']<=1e-8 and q['bounds']<=1e-8
            facts.append(dict(case=name,quality=q));m.dispose()
    write(target/'result.json',dict(UTC=utc(),PASS=True,facts=facts,tiny_tours=checked_tours,
        exact_downward_subtour_bounds=True,Optimize=0,source_SHA=sha(__file__),
        attribution='classical necessary routing resource projection; no complete route from its feasible assignment',
        review='same agent, separate exhaustive path and saved-row reconstruction'))
    print(json.dumps(dict(facts=facts,tiny_tours=checked_tours)),flush=True)

if __name__=='__main__':run()
