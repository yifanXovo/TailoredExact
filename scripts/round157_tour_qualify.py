"""Independent tiny tour enumeration and actual fleet shortcut validation."""
from itertools import permutations
from fractions import Fraction as F
from round157_tour import solve,shortest
from round157_qualify import micro
from round157_inventory import instance
from round157_fleet import verify
from round157_common import *

def run():
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    affinity();assert binding()['sha256']==DLL_SHA
    target=OUT/'qualification/tour_v1';target.mkdir(parents=True,exist_ok=False);facts=[]
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        for name,positions in [('singleton',[0,3]),('triangle',[0,1,4]),
                               ('disjoint_cycles',[0,1,2,100,101,102])]:
            n=len(positions)-1;data=micro([0]*n,[0]*n,[3],100,positions=positions)
            mandatory=list(range(1,n+1));d=shortest(data)
            exact=min(sum((d[i][j] for i,j in zip((0,)+order,order+(0,))),F(0)) for order in permutations(mandatory))
            result=solve(data,mandatory,env,target/name,4096,60)
            assert result['qualified'] and F(result['lower'])<=exact
            assert abs(result['upper']-float(exact))<=1e-7
            if name=='disjoint_cycles':assert result['lazy_rows']>0
            facts.append(dict(case=name,exact=str(exact),lower=result['lower'],upper=result['upper'],
                              lazy_rows=result.get('lazy_rows',0),PASS=True))
        for role,source in read(OUT/'inventory_families.json').items():
            data=instance(source['panel']);witness=source['positive_control']['witness'];physical=verify(data,witness)
            order=[i for r in witness['routes'] for i in r['nodes'][1:-1]]
            assert len(order)==len(set(order));d=shortest(data)
            shortcut=sum((d[i][j] for i,j in zip([0]+order,order+[0])),F(0))
            actual=sum((F(data['distance'][i][j]) for r in witness['routes'] for i,j in zip(r['nodes'],r['nodes'][1:])),F(0))
            assert shortcut<=actual
            for h in range(data['n']+1):
                for i in range(data['n']+1):
                    for j in range(data['n']+1):assert d[i][j]<=d[i][h]+d[h][j]
            facts.append(dict(role=role,shortcut_travel=float(shortcut),actual_fleet_travel=float(actual),
                              exact_rational_metric=True,PASS=True))
    write(target/'result.json',dict(UTC=utc(),PASS=True,facts=facts,source_SHA=sha(__file__),
        bound_is_on_total_fleet_travel_only=True,review='same agent, independent tour enumeration and actual fleet shortcut'))
    print(json.dumps(facts),flush=True)

if __name__=='__main__':run()
