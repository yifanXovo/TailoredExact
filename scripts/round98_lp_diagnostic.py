"""One declared real fixed-state batch: 3 objective LPs and at most1 completion LP.

Production matrices are created by Round98ModelExport, never patched here.
All variables are relaxed for raw LPs. Independent presolve sizes are explanatory.
"""
import gzip,json,math,sys,time
from pathlib import Path
import gurobipy as gp
from gurobipy import GRB
from round98_common import *
import generate_citibike443_regional_v1 as parser

def size(m):return dict(rows=m.NumConstrs,columns=m.NumVars,nonzeros=m.NumNZs,binary=m.NumBinVars,integer=m.NumIntVars)
def residuals(values,initial,M,V):
    rows=[]
    for i in range(1,V+1):
        states={int(n.split('_')[2]):x for n,x in values.items() if n.startswith(f'state_{i}_')}
        movement=sum(values[f'{p}_{k}_{i}'] for p in ['p','d'] for k in range(M))
        expected=math.fsum(abs(initial[i]-y)*s for y,s in states.items())
        visit=sum(values[f'z_{k}_{i}'] for k in range(M))
        rows.append(dict(station=i,movement_residual=movement-expected,
            visit_residual=visit-1+states.get(initial[i],0),movement=movement,expected_movement=expected))
    return rows

def run(role,label,strict=False):
    p=next(p for p in read(OUT/'development_inputs.json')['roles'] if p['id']==role)
    input_data=parser.parse_instance_mirror(ROOT/p['input_path'])
    dest=OUT/'diagnostics'/label;dest.mkdir(parents=True,exist_ok=False)
    start=time.monotonic();calls=[]
    def optimize(m,name):
        m.Params.TimeLimit=max(.001,285-(time.monotonic()-start))
        with (dest/'calls.jsonl').open('a') as f:f.write(json.dumps(dict(kind='start',name=name))+'\n')
        m.optimize();calls.append(dict(name=name,status=m.Status,seconds=time.monotonic()-start))
        with (dest/'calls.jsonl').open('a') as f:f.write(json.dumps(dict(kind='complete',**calls[-1]))+'\n')
    results=[];old_values=None
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start();assert gp.gurobi.version()==(13,0,2)
        for mode in ['off','aggregate','projected']:
            path=OUT/'exports'/role/(mode+'.lp')
            assert sha(path)==read(path.with_suffix('.json'))['sha256']
            with gp.read(str(path),env=env) as integer:
                integer.Params.Threads=1;integer.Params.Seed=0;integer.Params.Presolve=-1
                before=size(integer);presolved=integer.presolve();after=size(presolved);presolved.dispose()
                model=integer.relax();model.Params.LogFile=str(dest/(mode+'.log'))
                if strict:
                    model.Params.FeasibilityTol=1e-8;model.Params.OptimalityTol=1e-9
                optimize(model,mode+'_raw_LP')
                value=model.ObjVal if model.Status==GRB.OPTIMAL else None
                data=dict(mode=mode,status=model.Status,objective=value,original=before,presolved=after,model_sha256=sha(path),
                    feasibility_tolerance=model.Params.FeasibilityTol,optimality_tolerance=model.Params.OptimalityTol,
                    primal_violation=model.ConstrVio if value is not None else None,
                    dual_violation=model.DualVio if value is not None else None)
                if model.Status==GRB.OPTIMAL:
                    values={v.VarName:v.X for v in model.getVars()};res=residuals(values,input_data['initial'],p['M'],p['V'])
                    data['linkage_residuals']=res
                    with gzip.open(dest/(mode+'_values.json.gz'),'wt') as f:json.dump(values,f)
                    data['values_sha256']=sha(dest/(mode+'_values.json.gz'))
                    if mode=='off':old_values=values
                results.append(data);model.dispose()
                write(dest/(mode+'_record.json'),data)
        assert all(r['status']==GRB.OPTIMAL for r in results),'incomplete objective LP qualification'
        assert results[1]['objective']+1e-7>=results[0]['objective']
        assert abs(results[1]['objective']-results[2]['objective'])<=1e-7
        path=OUT/'exports'/role/'aggregate.lp'
        with gp.read(str(path),env=env) as integer:
            model=integer.relax();model.Params.Threads=1;model.Params.Seed=0;model.Params.Presolve=-1
            if strict:
                model.Params.FeasibilityTol=1e-8;model.Params.OptimalityTol=1e-9
            for v in model.getVars():
                if not v.VarName.startswith(('state_','mode_')):
                    v.LB=v.UB=old_values[v.VarName]
            model.setObjective(0);optimize(model,'old_common_coordinates_R1_completion')
            completion=dict(status=model.Status,feasible=model.Status==GRB.OPTIMAL,
                proved_no_extension=model.Status==GRB.INFEASIBLE,
                scope='R1 known feasible; old common coordinates fixed, selectors/q/m free. This is NOT interval infeasibility.')
            model.dispose()
    write(dest/'summary.json',dict(role=role,passed=True,optimizer_calls=len(calls),maximum_calls=4,
        outer_seconds=time.monotonic()-start,input_sha256=p['input_sha256'],fixed_state=p,
        records=results,completion=completion,script_sha256=sha(__file__)))
    print(json.dumps(dict(role=role,objectives=[r['objective'] for r in results],completion=completion,calls=len(calls))),flush=True)
if __name__=='__main__':run(sys.argv[1],sys.argv[2],len(sys.argv)>3 and sys.argv[3]=='strict')
