"""Four finite common-coordinate feasibility tests on saved qualification points."""
from round101_common import *
from round100_idle import ensure_idle
def main(label):
    ensure_idle()
    from round100_gurobi_runtime import gp,binding
    from gurobipy import GRB
    from round70_affinity import inherited_core
    d=OUT/'diagnostics'/label;d.mkdir(parents=True,exist_ok=False);records=[];calls=0
    with inherited_core() as affinity,gp.Env(empty=True) as engine:
        engine.setParam('OutputFlag',0);engine.start();runtime=binding()
        for p in read(OUT/'diagnostics/lp01/summary.json')['records']:
            folder=OUT/'diagnostics/lp01'/p['role'];raw=read(folder/'raw.separation.json')
            with gp.read(str(ROOT/p['actual_source']),env=engine) as original:
                m=original.relax();m.Params.Threads=1;m.Params.Seed=0;m.Params.TimeLimit=120;m.Params.LogFile=str(d/(p['role']+'.log'))
                vals=list(map(float,(folder/'raw.point').read_text().split()));vars=m.getVars();fixed=0
                for v,value in zip(vars,vals):
                    if not v.VarName.startswith('state_'):v.LB=v.UB=value;fixed+=1
                for j in range(p['bank_size']):
                    row=read(folder/f'implication_{j}.json')['row'];m.addConstr(gp.quicksum(vars[k] for k in row['columns'])<=row['proof']['rank'])
                m.setObjective(0)
                with (d/'calls.jsonl').open('a') as f:f.write(json.dumps(dict(kind='start',role=p['role']))+'\n');f.flush()
                calls+=1;m.optimize()
                with (d/'calls.jsonl').open('a') as f:f.write(json.dumps(dict(kind='return',role=p['role'],status=m.Status,seconds=m.Runtime))+'\n');f.flush()
                assert m.Status in [GRB.OPTIMAL,GRB.INFEASIBLE]
                records.append(dict(role=p['role'],fixed_common_coordinates=fixed,free='state selectors and state_g companions',status=m.Status,
                    common_point_reextends=m.Status==GRB.OPTIMAL,bank_rows=p['bank_size'],actual_sha256=sha(ROOT/p['actual_source'])))
                if m.Status==GRB.OPTIMAL:write(d/(p['role']+'_completion.json'),{v.VarName:v.X for v in vars if v.VarName.startswith('state_')})
                m.dispose()
    write(d/'summary.json',dict(passed=True,records=records,optimizer_calls=calls,runtime=runtime,affinity=affinity))
    print(json.dumps(records))
if __name__=='__main__':
    import sys;main(sys.argv[1])
