"""One finite family-exclusion counterfactual; no master/oracle loop.

A qualified complete-family impossibility excludes its exact finite member
vectors in the unchanged original RN inventory model. At most two
preselected families enter one batch, with at most32 total members.
"""
from fractions import Fraction as F
from itertools import combinations
from round157_inventory import classes,signature,value,family
from round157_floor import objective,original_lower,retain_known_lower
from round153_pricing import Oracle
from round143_math import outward
from round143_lp import semantics,residual
from round157_common import *

def exclude_family(oracle,Y,batch=0):
    from round100_gurobi_runtime import gp
    m=oracle.model;members=family(oracle.scope,Y);assert len(members)<=32
    records=[];n=len(oracle.scope['stations'])
    for no,member in enumerate(members):
        name=f'exclude_family_{batch}_member_{no}'
        m.addConstr(gp.quicksum(oracle.x[s['i'],v] for s,v in zip(oracle.scope['stations'],member))<=n-1,name=name)
        records.append(dict(member=member,row=name,batch=batch))
    m.update();return records

def inventory_point(oracle,Y,indicators,enforce_new_domain=True):
    scope=oracle.scope;val=value(scope,Y);assert val['feasible'] and val['S']>0
    p={v.VarName:0. for v in oracle.model.getVars()};t=1/val['S']
    for s,y in zip(scope['stations'],Y):
        i=s['i'];p[f'x[{i},{y}]']=1.;p[f'w[{i},{y}]']=float(t)
        p[f'z[{i}]']=float(t*y);p[f'r[{i}]']=float(F(s['c'])*t*y)
    p['t']=float(t);p['q']=float(val['G'])
    for a,b in combinations(scope['stations'],2):
        i,j=a['i'],b['i'];p[f'a[{i},{j}]']=abs(p[f'r[{i}]']-p[f'r[{j}]'])
    if enforce_new_domain:assert all(list(Y)!=r['member'] for r in indicators),'excluded inventory cannot supply a new-domain upper'
    return p,val

def run(role,label,nodes=16384,cap=3600,proof_labels='rx35_family4096_v1'):
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    affinity();assert binding()['sha256']==DLL_SHA
    assert read(OUT/'qualification/family_floor_v1/result.json')['PASS']
    assert read(OUT/'review/family_predeep_v1.json')['PASS']
    source=read(OUT/'inventory_sources.json')[role];family_source=read(OUT/'inventory_families.json')[role]
    scope=source['scope'];proofs=[];anchors=[];forbidden=set()
    for proof_label in proof_labels.split(','):
        proof=OUT/'resource'/proof_label;condition=read(proof/'condition.json');pr=read(proof/'result.json')
        assert condition['role']==role and pr['classification']=='RESOURCE_INFEAS' and pr['bound_status_qualified']
        assert pr['required_time_lower']>pr['original_T']+pr['margin']
        if condition['rank']!=1:
            readback=read(OUT/'review'/f'{proof_label}_readback.json')
            assert readback['PASS'] and readback['result_SHA']==sha(proof/'result.json')
        anchor=family_source['candidates'][condition['rank']-1]['Y']
        expected=family(scope,anchor);assert expected==condition['members']
        anchors.append(anchor);forbidden.update(map(tuple,expected))
        proofs.append(dict(label=proof_label,result_SHA=sha(proof/'result.json'),condition_SHA=sha(proof/'condition.json')))
    assert len(anchors)<=2 and len(forbidden)<=32
    retained=[s for s in source['stocks'] if tuple(s['Y']) not in forbidden]
    upper_stock=min(retained,key=lambda s:F(s['price_exact']));Y=upper_stock['Y'];u=F(upper_stock['price_exact'])
    assert value(scope,Y)['phi']==u and value(scope,Y)['feasible'] and scope['gamma_L']==0
    target=(F(source['upper'])+u)/2;folder=OUT/'family_floor'/label;folder.mkdir(parents=True,exist_ok=False);tick=time.perf_counter()
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        oracle=Oracle(scope,env,old_joint=True);assert not oracle.bounds['zero_possible']
        m=oracle.model;transport=objective(oracle);old=semantics(m)
        cols={v.VarName for v in m.getVars()};rows={c.ConstrName for c in m.getConstrs()}
        indicators=[]
        for batch,anchor in enumerate(anchors):indicators+=exclude_family(oracle,anchor,batch)
        retain_known_lower(oracle,source['lower'])
        assert semantics(m,cols,rows)==old
        point,stock=inventory_point(oracle,Y,indicators);quality=residual(m,point)
        assert quality['constraints']<=1e-7 and quality['bounds']<=1e-7,quality
        for v in m.getVars():v.Start=point[v.VarName]
        write(folder/'new_upper.json',dict(Y=Y,J=float(u),J_exact=str(u),point=point,quality=quality,
            excluded_old_upper_not_retained=True,physical_route=False))
        m.Params.Seed=0;m.Params.Threads=1;m.Params.MIPGap=0;m.Params.MIPGapAbs=1e-4/transport['scale']
        m.Params.NodeLimit=int(nodes);m.Params.TimeLimit=float(cap);m.Params.IntFeasTol=1e-6;m.Params.DualReductions=0
        m.Params.LogFile=str(folder/'native.log');m.Params.OutputFlag=1;m.Params.LogToConsole=0
        m.write(str(folder/'model.mps'))
        write(folder/'call.json',dict(role=role,scope=scope,anchors=anchors,proofs=proofs,
            excluded_inventories=len(forbidden),families_in_one_batch=len(anchors),
            family_review_SHA=sha(OUT/'review/family_predeep_v1.json'),model_SHA=sha(folder/'model.mps'),
            source_SHA=sha(__file__),baseline_lower=source['lower'],old_inventory_upper=source['upper'],
            new_valid_inventory_upper=outward(u,True),target_level=float(target),target_level_exact=str(target),
            anchors_exact={str(k):str(v) for k,v in transport['anchors'].items()},scale=transport['scale'],
            guard=transport['guard'],correction_exact=str(transport['correction']),NodeLimit=int(nodes),TimeLimit=float(cap),
            finite_batches=1,master_oracle_loop=False,no_physical_upper_claim=True))
        stop=[False]
        def observe(model,where):
            if where==gp.GRB.Callback.MIP:
                raw=model.cbGet(gp.GRB.Callback.MIP_OBJBND)
                if abs(raw)<1e90 and original_lower(raw,transport)>target:stop[0]=True;model.terminate()
        m.optimize(observe)
        from round157_resource import native_quality
        numerical=native_quality(m,folder/'native.log')
        qualified=numerical['numeric_ok'] and (m.Status in (2,8,9,15) or (m.Status==11 and stop[0]))
        lower=max(F(source['lower']),original_lower(m.ObjBound,transport)) if qualified else F(source['lower'])
        assert lower<=u
        result=dict(role=role,status=m.Status,bound_status_qualified=qualified,numerical_quality=numerical,
            original_lower=outward(lower,False),new_inventory_upper=outward(u,True),physical_U=None,
            target_level=float(target),level_excluded=lower>target,bound_stop=stop[0],
            native_bound=m.ObjBound,NodeCount=m.NodeCount,Runtime=m.Runtime,Work=m.Work,SolCount=m.SolCount,
            all_physical_original_inventories_covered=True,finite_batches=1,
            maximum_increment_over_Eplus_from_this_batch=float(u-F(source['lower'])),
            total_seconds=time.perf_counter()-tick,model_SHA=sha(folder/'model.mps'),call_SHA=sha(folder/'call.json'))
        if m.SolCount:save_gz(folder/'solution.json.gz',{v.VarName:v.X for v in m.getVars()})
        write(folder/'result.json',result);oracle.close()
    print(json.dumps(result),flush=True)

if __name__=='__main__':run(*sys.argv[1:])
