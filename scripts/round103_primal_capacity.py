"""Finite legitimate columns give an UPPER bound on the hull LP optimum.

This is solely a capability upper witness, never a BRP lower bound or a
physical route UB. No pricing completeness is needed for that upper direction.
All original columns/rows plus service-combination equalities remain present.
"""
from round103_points import *
def main(label,parent,cap=600.):
    from round100_idle import ensure_idle
    from round100_gurobi_runtime import gp,binding
    from gurobipy import GRB
    from round98_projection_vector_audit import check
    from round70_affinity import inherited_core
    ensure_idle();source=OUT/'diagnostics'/parent;directory=OUT/'diagnostics'/label;directory.mkdir(parents=True,exist_ok=False)
    previous=read(source/'plan.json');role=previous['role'];original_path=ROOT/previous['source'];assert sha(original_path)==previous['source_sha256']
    c=read(source/'contract.json')['resource'];selection=previous.get('anchor_selection')
    anchors={r['vehicle']:r['anchors'] for r in read(OUT/'diagnostics'/selection/'selection.json')['selections']} if selection else {}
    banks={k:{} for k in range(role['M'])}
    for line in (source/'oracle_calls.jsonl').read_text().splitlines():
        p=json.loads(line)['proof'];k=p['vehicle'];r=p['solution'];validate(c,k,r,anchors.get(k,[]));banks[k][tuple(v for row in r for v in row)]=r
    zero=[[0,0,0] for _ in c['initial']]
    for k in banks:banks[k][tuple(v for row in zero for v in row)]=zero
    write(directory/'plan.json',dict(parent=parent,source_sha256=sha(original_path),cap_seconds=cap,anchors=anchors,
        question='feasible finite-service-column model yields a hull-objective upper witness; it is NEVER an original BRP lower bound',
        columns_per_vehicle={k:len(v) for k,v in banks.items()},source_plan_hash=sha(source/'plan.json')))
    tick=time.perf_counter();deadline=tick+cap
    with inherited_core() as affinity,gp.Env(empty=True) as engine:
        engine.setParam('OutputFlag',0);engine.start();runtime=binding()
        with gp.read(str(original_path),env=engine) as original:
            with original.relax() as model:
                model.Params.Threads=1;model.Params.Seed=0;model.Params.Presolve=-1;model.Params.FeasibilityTol=1e-9;model.Params.OptimalityTol=1e-9
                model.Params.LogFile=str(directory/'restricted_hull.log');by={v.VarName:v for v in model.getVars()};plans={k:list(v.values()) for k,v in banks.items()};variables={}
                for k,bank in plans.items():
                    lam=[model.addVar(lb=0.,name=f'hull_lambda_{k}_{j}') for j in range(len(bank))];variables[k]=lam
                    model.addConstr(gp.quicksum(lam)==1.,name=f'hull_mass_{k}')
                    for i in range(1,len(c['initial'])):
                        for t,tag in enumerate(['p','d','z']):model.addConstr(by[f'{tag}_{k}_{i}']==gp.quicksum(p[i][t]*l for p,l in zip(bank,lam) if p[i][t]),name=f'hull_coordinate_{k}_{i}_{t}')
                model.Params.TimeLimit=max(.001,deadline-time.perf_counter())
                write(directory/'Optimize_begin.json',dict(call=1,kind='restricted_hull_upper_witness'))
                model.optimize();solution=None
                write(directory/'Optimize_return.json',dict(call=1,status=model.Status,seconds=model.Runtime,SolCount=model.SolCount))
                if model.SolCount:
                    values={name:v.X for name,v in by.items()};combinations=[];max_residual=0.
                    for k,lam in variables.items():
                        positive=[(exact(v.X),p) for v,p in zip(lam,plans[k]) if v.X>0.];mass=sum((a for a,p in positive),F(0));assert mass>0
                        combo=[(a/mass,p) for a,p in positive];assert sum((a for a,p in combo),F(0))==1
                        for a,p in combo:assert a>=0;validate(c,k,p,anchors.get(k,[]))
                        for i in range(1,len(c['initial'])):
                            for t,tag in enumerate(['p','d','z']):
                                exact_value=sum((a*p[i][t] for a,p in combo),F(0));name=f'{tag}_{k}_{i}'
                                max_residual=max(max_residual,abs(float(exact_value)-values[name]));values[name]=float(exact_value)
                        combinations.append(dict(vehicle=k,anchors=anchors.get(k,[]),combination=[dict(lambda_rational=str(a),plan=p) for a,p in combo]))
                    residual=check(original,values)
                    qualified=residual['maximum_absolute_residual']<=1e-6
                    solution=dict(status='NUMERICALLY_QUALIFIED_HULL_UPPER_WITNESS' if qualified else 'UNKNOWN',
                        objective=residual['objective'],original_matrix_residual=residual,combination_replacement_maximum=max_residual,
                        point=values,combinations=combinations,scope='exact-rational convex combinations; original LP feasible only within declared numerical row tolerance; no route feasibility or strict rational full-matrix proof')
                    write(directory/'upper_witness.json',solution)
    result=dict(parent=parent,status=solution['status'] if solution else 'UNKNOWN',hull_objective_upper=solution['objective'] if solution and solution['status'].startswith('NUMERICALLY') else None,
        Optimize_calls=1,DP_calls=0,outer_seconds=time.perf_counter()-tick,runtime=runtime,affinity=affinity,
        original_matrix_residual=solution['original_matrix_residual'] if solution else None)
    write(directory/'summary.json',result);print(json.dumps(result),flush=True)
if __name__=='__main__':main(sys.argv[1],sys.argv[2],float(sys.argv[3]) if len(sys.argv)>3 else 600.)
