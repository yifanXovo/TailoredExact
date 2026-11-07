"""Exact finite family coverage and actual excluded/retained matrix lifts."""
from itertools import product
from fractions import Fraction as F
from round157_family_floor import exclude_family,inventory_point
from round157_floor import objective,retain_known_lower
from round157_inventory import signature,classes,family
from round153_pricing import Oracle
from round143_lp import residual,semantics
from round157_common import *

def run():
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    affinity();assert binding()['sha256']==DLL_SHA
    target=OUT/'qualification/family_floor_v1';target.mkdir(parents=True,exist_ok=False)
    tiny=dict(Bminus=0,B=4,gamma_L=0.,gamma_U=1.,cutoff=2.,
        stations=[dict(i=i,c=.5,omega=.15,lo=0,hi=2,support=[0,1,2]) for i in (1,2)])
    anchor=[0,2];members=family(tiny,anchor);assert members==[[0,2],[2,0]];checked=0
    # Complete class-count coverage is checked independently of the matrix.
    for Y in product(range(3),repeat=2):
        assert (list(Y) in members)==(signature(tiny,Y)==signature(tiny,anchor));checked+=1
    source=read(OUT/'inventory_sources.json')['R-X35-S-T2'];scope=source['scope']
    c=read(OUT/'inventory_families.json')['R-X35-S-T2']['candidates'];facts=[]
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        for count in (1,2):
            o=Oracle(scope,env,old_joint=True);t=objective(o);old=semantics(o.model)
            cols={v.VarName for v in o.model.getVars()};rows={r.ConstrName for r in o.model.getConstrs()}
            flags=[]
            for batch in range(count):flags+=exclude_family(o,c[batch]['Y'],batch)
            retain_known_lower(o,source['lower']);assert semantics(o.model,cols,rows)==old
            forbidden={tuple(r['member']) for r in flags}
            for member in forbidden:
                oldpoint,_=inventory_point(o,member,flags,enforce_new_domain=False)
                assert abs(residual(o.model,oldpoint)['constraints']-1.)<=1e-7
            retained=min((s for s in source['stocks'] if tuple(s['Y']) not in forbidden),key=lambda s:F(s['price_exact']))
            Y=retained['Y'];p,v=inventory_point(o,Y,flags);q=residual(o.model,p)
            assert q['constraints']<=1e-7 and q['bounds']<=1e-7,q
            path=target/f'actual_model_{count}.mps';o.model.write(str(path))
            with gp.read(str(path),env=env) as back:assert semantics(back)==semantics(o.model) and residual(back,p)==q
            write(target/f'retained_upper_{count}.json',dict(Y=Y,J_exact=str(v['phi']),J=float(v['phi']),point=p,quality=q,
                signature_differs=True,physical_upper_claim=False,model_SHA=sha(path)))
            facts.append(dict(families=count,excluded_members=len(forbidden),retained_J=float(v['phi']),quality=q))
            o.close()
    write(target/'result.json',dict(UTC=utc(),PASS=True,tiny_inventories=checked,all_actual_excluded_members_violate=True,
        actual_batches=facts,actual_saved_matrix_readback=True,
        finite_exclusion_batches=1,no_Benders_master_loop=True,Optimize=0,source_SHA=sha(__file__),
        review='same agent, exhaustive class-family coverage and excluded/retained full-matrix lifts'))
    print(json.dumps(read(target/'result.json')),flush=True)

if __name__=='__main__':run()
