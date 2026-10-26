"""Enumerated small actual domain: real primal/dual LP and pricing checks.

Finite mathematical qualification, never a candidate rule or confirmation.
All Optimize/DP calls and the reference child are inside one paid receipt.
"""
import sys,json,itertools,random
from fractions import Fraction as F
from round103_points import typed_matrix
from round103_hull import *
from round100_idle import ensure_idle
from round100_gurobi_runtime import gp,binding
from round70_affinity import inherited_core

def main(label):
    ensure_idle();d=OUT/'diagnostics'/label;d.mkdir(exist_ok=False)
    source=d/'input.txt'
    source.write_text('3 2 [1, 2]\ncapacities = [100000, 2, 2, 2]\ninitial = [50000, 1, 0, 2]\ntarget = [0, 1, 1, 1]\nweights = [0, 1, 1, 0]\nmin_ratio = [0, 0, 0, 0]\npoints = [(0, 0), (0, 0), (0, 0), (0, 0)]\n')
    role=dict(id='enumerated-small',V=3,M=2,Q_vector=[1,2],T_seconds=5,pickup_seconds=1,drop_seconds=1,
        input_path=source.relative_to(ROOT).as_posix(),input_sha256=sha(source),**{'lambda':.15})
    ref=d/'reference';ref.mkdir()
    # The hull contract audits actual VD-P state/link rows. P's original
    # compact build intentionally lacks that structure and is not a valid
    # oracle matrix. This same-source export-only tool never Optimize.
    cmd=[BUILD/'Round98ModelExport.exe',source,'5','1','1','.15','0','1','1',ref]
    write(ref/'launch.json',dict(command=list(map(str,cmd)),Optimize_calls=0,
        binary_sha256=sha(BUILD/'Round98ModelExport.exe'),selected_mode='off'))
    allowances=read(OUT/'additional_fee_allowances.json')
    allowances['fees'].append(dict(label=label+'_nested_reference_child',starts=1,seconds=0,
        failed=False,Optimize_calls=0,DP_calls=0,
        scope='Conservative additional physical reference-child count; its observed duration is inside the paid parent receipt and is not added twice'))
    # This owned ledger is append-only in content; the common diagnostic
    # writer deliberately refuses to replace an already existing file.
    (OUT/'additional_fee_allowances.json').write_text(json.dumps(allowances,indent=2)+'\n',encoding='utf-8')
    tick=time.perf_counter()
    with (ref/'stdout.log').open('x') as so,(ref/'stderr.log').open('x') as se:
        ret=subprocess.run(list(map(str,cmd)),cwd=ROOT,env=env(),stdout=so,stderr=se,timeout=60)
    write(ref/'completion.json',dict(exit_code=ret.returncode,outer_seconds=time.perf_counter()-tick,Optimize_calls=0))
    assert ret.returncode==0
    records=[];enum_calls=0;master_calls=0;DP_calls=0;rng=random.Random(10317)
    with inherited_core() as affinity,gp.Env(empty=True) as engine:
        engine.setParam('OutputFlag',0);engine.start();runtime=binding()
        with gp.read(str(ref/'off.lp'),env=engine) as model:typed_matrix(model,d/'matrix.txt')
        oracle=Oracle(role,d/'matrix.txt',d);c=oracle.contract['resource']
        try:
            for k,Q in enumerate([1,2]):
                widths=[[0,0,0]]+[[min(b,Q),min(2-b,Q),1] for b in [1,0,2]]
                options=[[(0,0,0)]+[(p,0,1) for p in range(1,widths[i][0]+1)]+[(0,z,1) for z in range(1,widths[i][1]+1)] for i in range(1,4)]
                # Exact 2P<=5 is equivalent to this fixture's actual floating
                # outward predicate: P is integral, all travel is zero, and
                # the nearest excluded layer is 6, a full unit above T.
                plans=[[[0,0,0]]+[list(r) for r in product] for product in itertools.product(*options)
                    if sum(r[1] for r in product)<=sum(r[0] for r in product) and 2*sum(r[0] for r in product)<=5]
                for plan in plans:validate(c,k,plan)
                write(d/f'enumerated_plans_{k}.json',dict(vehicle=k,plans=plans,widths=widths))
                coordinates=[(i,t,widths[i][t]) for i in range(1,4) for t in range(3) if widths[i][t]]
                points=[[[0.,0.,0.] for _ in range(4)]]
                for _ in range(7):
                    a,b=rng.sample(plans,2);points.append([[.5*x+.5*y for x,y in zip(ar,br)] for ar,br in zip(a,b)])
                for _ in range(8):points.append([[0.,0.,0.]]+[[rng.randrange(5)*s/4 for s in row] for row in widths[1:]])
                for no,point in enumerate(points):
                    case=d/f'case_{k}_{no:02d}';case.mkdir()
                    write(case/'point.json',dict(vehicle=k,point=point,widths=widths))
                    with gp.Model('enumerated_full_distance',env=engine) as master:
                        master.Params.OutputFlag=0;master.Params.Threads=1;master.Params.Seed=0;master.Params.Presolve=-1
                        master.Params.FeasibilityTol=master.Params.OptimalityTol=1e-9;master.Params.Method=1
                        lam=master.addVars(len(plans),lb=0.);t=master.addVar(lb=0.,obj=1.)
                        mass=master.addConstr(lam.sum()==1.)
                        lo=[];hi=[]
                        for i,j,s in coordinates:
                            expression=gp.quicksum(plan[i][j]/s*lam[a] for a,plan in enumerate(plans))
                            lo.append(master.addConstr(expression+t>=point[i][j]/s))
                            hi.append(master.addConstr(expression-t<=point[i][j]/s))
                        enum_calls+=1
                        with (d/'enum_master_calls.jsonl').open('a') as f:f.write(json.dumps(dict(event='begin',call=enum_calls))+'\n')
                        master.optimize();assert master.Status==2
                        with (d/'enum_master_calls.jsonl').open('a') as f:f.write(json.dumps(dict(call=enum_calls,status=master.Status,distance=master.ObjVal))+'\n')
                        weights=[[0.,0.,0.] for _ in range(4)]
                        for (i,j,s),l,u in zip(coordinates,lo,hi):weights[i][j]=(l.Pi+u.Pi)/s
                        norm=sum(abs(weights[i][j])*s for i,j,s in coordinates);assert norm<=1+1e-8
                        support=max(sum(x*w for row,wr in zip(plan,weights) for x,w in zip(row,wr)) for plan in plans)
                        dual=sum(x*w for row,wr in zip(point,weights) for x,w in zip(row,wr))-support
                        assert abs(master.ObjVal-dual)<=1e-8
                        full_distance=master.ObjVal
                        write(case/'full_distance.json',dict(distance=full_distance,dual=dual,weights=weights,
                            norm=norm,enumerated_support=support,
                            primal=[dict(coefficient=lam[a].X,plan=plan) for a,plan in enumerate(plans) if lam[a].X>0],
                            qualification='Gurobi numerical full finite enumeration optimum and dual check, not a rational optimum'))
                    result=classify(oracle,k,point,engine,case,time.perf_counter()+30)
                    master_calls+=result['Optimize_calls'];DP_calls+=result['DP_calls']
                    if full_distance<=1e-8:assert result['status']=='INSIDE',result
                    if result['status']=='INSIDE':assert full_distance<=1e-8
                    if result['status']=='OUTSIDE':
                        p=result['support'];assert p['upper']==max(sum(a*b for wr,pr in zip(p['weights'],plan) for a,b in zip(wr,pr)) for plan in plans)
                        assert exact(result['full_distance_lower'])<=exact(full_distance)+F(1,10**8)
                    records.append(dict(vehicle=k,case=no,plans=len(plans),full_distance=full_distance,dual=dual,dual_norm=norm,status=result['status']))
        finally:
            # Actual attempts remain in the durable oracle logs even if a
            # classifier fails before its result can be accumulated.
            actual_DP_calls=oracle.calls
            oracle.close()
        assert DP_calls==actual_DP_calls
    write(d/'summary.json',dict(passed=True,Optimize_calls=enum_calls+master_calls,enum_Optimize_calls=enum_calls,
        hull_master_Optimize_calls=master_calls,DP_calls=DP_calls,model_read_attempts=1,physical_reference_children=1,
        records=records,runtime=runtime,affinity=affinity,script_sha256=sha(__file__),
        source_model_sha256=sha(ref/'off.lp'),production_binary_sha256=sha(BUILD/'ExactEBRP.exe'),
        scope='32 actual fully enumerated toy-domain infinity-distance primal/dual comparisons and certificate classifications. Not real-model performance or confirmation; no native MIP Optimize.'))
    print(json.dumps(dict(passed=True,cases=len(records),Optimize_calls=enum_calls+master_calls,DP_calls=DP_calls)))

if __name__=='__main__':main(sys.argv[1])
