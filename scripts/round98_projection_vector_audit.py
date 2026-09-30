"""Zero-Optimize independent common-coordinate and recovered-mode audit."""
import gzip,math,sys,time
import gurobipy as gp
from round98_common import *
import generate_citibike443_regional_v1 as parser

def check(model,values):
    assert {v.VarName for v in model.getVars()}==set(values)
    violations=[];maximum=0
    for v in model.getVars():
        x=values[v.VarName];assert math.isfinite(x)
        maximum=max(maximum,v.LB-x,x-v.UB)
    for row in model.getConstrs():
        expression=model.getRow(row)
        a=math.fsum(expression.getCoeff(j)*values[expression.getVar(j).VarName] for j in range(expression.size()))
        r=row.RHS;delta=a-r if row.Sense=='<' else r-a if row.Sense=='>' else abs(a-r)
        maximum=max(maximum,delta)
        if delta>1e-6:violations.append(dict(row=row.ConstrName,residual=delta,activity=a,rhs=r))
    objective=model.ObjCon+math.fsum(v.Obj*values[v.VarName] for v in model.getVars())
    return dict(objective=objective,maximum_absolute_residual=maximum,violations_over_native_feasibility_tol=violations)

def run(role,label):
    p=next(p for p in read(OUT/'development_inputs.json')['roles'] if p['id']==role)
    indata=parser.parse_instance_mirror(ROOT/p['input_path']);saved=OUT/'diagnostics'/label
    vectors={}
    for mode in ['off','aggregate','projected']:
        with gzip.open(saved/(mode+'_values.json.gz'),'rt') as f:vectors[mode]=json.load(f)
    records={};tick=time.monotonic()
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        for mode in ['off','aggregate','projected']:
            path=OUT/'exports'/role/(mode+'.lp')
            with gp.read(str(path),env=env) as m:
                records[mode]=check(m,vectors[mode])
                if mode=='projected':
                    transferred={v.VarName:vectors['aggregate'][v.VarName] for v in m.getVars()}
                    records['R1_to_R2']=check(m,transferred)
                if mode=='aggregate':
                    transferred=dict(vectors['projected'])
                    for k in range(p['M']):
                        for i in range(1,p['V']+1):
                            a=min(indata['initial'][i],p['Q_vector'][k])
                            transferred[f'mode_{k}_{i}']=transferred[f'p_{k}_{i}']/a if a else 0
                    records['R2_to_R1']=check(m,transferred)
    write(saved/'projection_vector_audit.json',dict(role=role,optimizer_calls=0,records=records,
        objective_difference=records['aggregate']['objective']-records['projected']['objective'],
        wall_seconds=time.monotonic()-tick,source_sha256=sha(__file__)))
    print(json.dumps({k:{'objective':v['objective'],'maximum_absolute_residual':v['maximum_absolute_residual'],
        'violations':len(v['violations_over_native_feasibility_tol'])} for k,v in records.items()}))
if __name__=='__main__':run(*sys.argv[1:])
