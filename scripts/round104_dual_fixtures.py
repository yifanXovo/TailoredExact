"""Paid LP theorem fixtures: constants, equalities, bounds and descendants."""
from round104_common import *
def main(label):
    from round100_idle import ensure_idle
    from round100_gurobi_runtime import gp,binding
    from gurobipy import GRB
    from round70_affinity import inherited_core
    ensure_idle();d=OUT/'diagnostics'/label;d.mkdir(parents=True,exist_ok=False)
    records=[]
    with inherited_core() as affinity,gp.Env(empty=True) as engine:
        engine.setParam('OutputFlag',0);engine.start();runtime=binding()
        for kind in ['ALL','AGGREGATE','BRANCH_ALL','BRANCH_AGGREGATE','ZERO_BOUND','ZERO_EMPTY','DEGENERATE']:
            with gp.Model(kind,env=engine) as m:
                m.Params.Threads=1;m.Params.Seed=0;m.Params.Presolve=-1;m.Params.Method=1
                m.Params.FeasibilityTol=1e-9;m.Params.OptimalityTol=1e-9;m.Params.TimeLimit=30
                x=m.addVar(lb=2 if kind.startswith('BRANCH') or kind.startswith('ZERO') else 0,ub=10,name='x')
                y=m.addVar(lb=0,ub=10,name='y');t=m.addVar(lb=-2,ub=2,name='t')
                m.addConstr(t==0,name='old_equality');m.setObjective(x+y+7,GRB.MINIMIZE)
                new=[]
                if kind in ['ALL','BRANCH_ALL','DEGENERATE']:
                    new=[m.addConstr(-x<=-1),m.addConstr(-y<=-1)]
                    if kind=='DEGENERATE':new.append(m.addConstr(-x<=-1))
                elif kind in ['AGGREGATE','BRANCH_AGGREGATE']:new=[m.addConstr(-x-y<=-2)]
                elif kind=='ZERO_BOUND':new=[m.addConstr(-x<=-1)]
                m.update();serial=len(records)+1
                with (d/'calls.jsonl').open('a') as f:f.write(json.dumps(dict(event='Optimize_begin',serial=serial,kind=kind))+'\n')
                m.optimize()
                with (d/'calls.jsonl').open('a') as f:f.write(json.dumps(dict(event='Optimize_return',serial=serial,kind=kind,status=m.Status,seconds=m.Runtime))+'\n')
                assert m.Status==GRB.OPTIMAL
                pi=[r.Pi for r in new];assert all(p<=0 for p in pi)
                expected={'ALL':9,'AGGREGATE':9,'BRANCH_ALL':10,'BRANCH_AGGREGATE':9,'ZERO_BOUND':9,'ZERO_EMPTY':9,'DEGENERATE':9}[kind]
                assert m.ObjVal==expected
                if kind=='ZERO_BOUND':assert pi==[0]
                records.append(dict(kind=kind,objective=m.ObjVal,new_Pi=pi,objective_constant=m.ObjCon,
                    old_equality_present=True,old_bounds_retained=True))
    write(d/'summary.json',dict(passed=True,records=records,Optimize_calls=len(records),DP_calls=0,runtime=runtime,affinity=affinity,
        scope='mathematical LP fixtures, no performance or physical BRP evidence'))
    print(json.dumps(records),flush=True)
if __name__=='__main__':main(sys.argv[1])
