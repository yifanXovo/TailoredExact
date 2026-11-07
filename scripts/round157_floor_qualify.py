"""Audit RN preservation, resource projection and original-objective transport."""
from itertools import product
from fractions import Fraction as F
from round157_floor import attach,objective,lifted,original_lower,retain_known_lower
from round157_resource import travel_bounds
from round157_inventory import instance
from round157_qualify import micro,enumerated
from round153_pricing import Oracle,stock_value
from round143_lp import semantics,residual
from round157_common import *

def run(label='floor_v1'):
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    affinity();assert binding()['sha256']==DLL_SHA
    target=OUT/'qualification'/label;target.mkdir(parents=True,exist_ok=False);facts=[]
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        for role,source in read(OUT/'inventory_families.json').items():
            data=instance(source['panel']);scope=source['scope'];o=Oracle(scope,env,old_joint=True)
            t=objective(o);old=semantics(o.model);cols={v.VarName for v in o.model.getVars()};rows={c.ConstrName for c in o.model.getConstrs()}
            bounds=travel_bounds(data,list(range(1,data['n']+1)));ref=attach(o,data,bounds)
            assert semantics(o.model,cols,rows)==old
            retain_known_lower(o,read(OUT/'inventory_sources.json')[role]['lower'])
            p,physical=lifted(data,scope,o,ref,source['positive_control']['witness']);q=residual(o.model,p)
            assert q['constraints']<=1e-7 and q['bounds']<=1e-7,q
            reconstructed=F(t['scale'])*F(q['objective'])+sum(t['anchors'].values(),F(0))
            assert abs(float(reconstructed)-physical['J'])<=1e-7
            path=target/f'{role}.mps';o.model.write(str(path))
            with gp.read(str(path),env=env) as back:
                assert semantics(back)==semantics(o.model) and residual(back,p)==q
            write(target/f'{role}_lift.json',dict(point=p,quality=q,physical=physical,
                original_RN_columns_rows_preserved=True,original_scaled_objective_reconstructed=float(reconstructed),
                model_SHA=sha(path),source_witness_SHA=source['positive_control']['SHA']))
            facts.append(dict(role=role,PASS=True,quality=q,columns=o.model.NumVars,rows=o.model.NumConstrs,nonzeros=o.model.NumNZs))
            o.close()
        data=micro([2,0],[1,1],[1],10,positions=[0,1,100]);data['capacity']=[999999,2,2]
        scope=dict(Bminus=1,B=2,gamma_L=0.,gamma_U=1.,cutoff=1.,stations=[dict(i=i,c=.5,omega=.15,lo=0,hi=2,support=[0,1,2]) for i in (1,2)])
        exact_prices=[];physical_prices=[]
        costs={(i,y):F(.15)*abs(F(.5)*y-1) for i in (1,2) for y in (0,1,2)}
        for Y in product(range(3),repeat=2):
            v=stock_value(scope,Y,1,costs)
            if not v['feasible']:continue
            exact_prices.append(v['phi'])
            if enumerated(data,[list(Y)]) is not None:physical_prices.append(v['phi'])
        plain=min(exact_prices);physical=min(physical_prices)
        assert float(physical)>float(plain)+.4
        o=Oracle(scope,env,old_joint=True);t=objective(o);attach(o,data,travel_bounds(data,[1,2]));retain_known_lower(o,plain)
        m=o.model;m.Params.Seed=0;m.Params.Threads=1;m.Params.MIPGap=0;m.Params.MIPGapAbs=0
        m.Params.TimeLimit=30;m.Params.NodeLimit=4096;m.Params.IntFeasTol=1e-6
        m.write(str(target/'tiny_full_level.mps'));m.optimize();assert m.Status==gp.GRB.OPTIMAL
        lower=original_lower(m.ObjBound,t)
        original_native=F(t['scale'])*F(m.ObjVal)+sum(t['anchors'].values(),F(0))
        assert lower<=physical and abs(float(original_native-physical))<=1e-7
        assert lower>plain+F(.4)
        facts.append(dict(case='whole_level_not_one_family',plain_inventory_exact=str(plain),
            exhaustive_physical_exact=str(physical),new_lower=float(lower),native_original_objective=float(original_native),PASS=True))
        o.close()
    write(target/'result.json',dict(UTC=utc(),PASS=True,facts=facts,source_SHA=sha(__file__),
        inherited_R153_objective_transport=True,all_original_inventory_support=True,
        actual_positive_controls_and_saved_matrices=True,review='same agent, separate exhaustive and model-row reconstruction'))
    print(json.dumps(facts),flush=True)

if __name__=='__main__':run(*sys.argv[1:])
