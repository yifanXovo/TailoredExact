"""Extra finite interface readback and a binding prefix-load DP counterexample."""
from round159_common import *
from fractions import Fraction as F
from itertools import permutations

def run():
    from round100_gurobi_runtime import gp
    from round150_lp import affinity
    from round153_pricing import Oracle
    from round157_floor import attach
    from round158_level import envelope
    affinity();facts=[]
    def row(m,c):
        e=m.getRow(c)
        return c.Sense,c.RHS,{e.getVar(i).VarName:e.getCoeff(i) for i in range(e.size()) if e.getCoeff(i)}
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        for role,label in [('R-X35-S-T2','qualify_rx'),('N-B35-S','qualify_nb')]:
            source=read(OUT/'inputs_v2'/role/'source.json');d=source['data']
            md,_=envelope(d,read(source['coefficient_package']['path']))
            o=Oracle(source['scope'],env,old_joint=True);attach(o,md,[])
            with gp.read(str(OUT/'runs'/label/'joint.mps'),env=env) as actual:
                count=0
                for c in o.model.getConstrs():
                    if c.ConstrName.startswith('resource_') and not c.ConstrName.startswith('resource_handling_'):
                        back=actual.getConstrByName(c.ConstrName);assert back is not None and row(actual,back)==row(o.model,c);count+=1
                facts.append(dict(role=role,all_assignment_visit_pickup_drop_return_rows_equal_R157=count))
            o.close()
    folder=OUT/'qualification_dp/prefix_binding';folder.mkdir(parents=True,exist_ok=False)
    b=[2,2,0,0];Y=[0,0,3,1];n=4;Q=3;T=1000
    cycle={tuple(sorted((i,(i+1)%5))) for i in range(5)}
    d=[[0 if i==j else 1 if tuple(sorted((i,j))) in cycle else 9 for j in range(5)] for i in range(5)]
    lines=['4 1 0 4 1 120 1000 1000','3']
    for bi,yi in zip(b,Y):
        support=sorted(set((bi,yi)));lines.append(' '.join(map(str,[bi,max(bi,yi),1,0,len(support),*support])))
    lines+=[' '.join(map(str,r)) for r in d]+['8 0','0 0 3 1','0 0 0 0']
    path=folder/'data.txt';path.write_text('\n'.join(lines)+'\n')
    subprocess.run([str(PE),'complete',str(path),'unused',str(folder/'output')],env=meter.environment(),check=True)
    result=read(folder/'output/completion.json');row=result['vehicles'][0];best=plain=None
    for order in permutations(range(1,5)):
        nodes=(0,)+order+(0,);cost=sum(F(d[i][j]) for i,j in zip(nodes,nodes[1:]));plain=cost if plain is None else min(plain,cost)
        load=0;valid=True
        for i in order:load+=b[i-1]-Y[i-1];valid &= 0<=load<=Q
        if valid:best=cost if best is None else min(best,cost)
    assert F(row['travel_scaled'])/2**53==best and F(row['unloaded_travel_scaled'])/2**53==plain and best>plain
    write(OUT/'interface_qualification.json',dict(UTC=utc(),PASS=True,resource_facts=facts,
        binding_prefix_fixture=dict(load_constrained=str(best),unloaded=str(plain),enumerated_orders=24,P=4,Q=3),
        Optimize=0,PE_SHA=sha(PE)))

if __name__=='__main__':run()
