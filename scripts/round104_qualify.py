"""Charged real-pool C++ compression, exact validity and LP reoptimization."""
from round104_common import *
from round104_pool import exact,old_pool
from fractions import Fraction as F
import math,gzip

def main(label,cap):
    from round100_idle import ensure_idle
    from round100_gurobi_runtime import gp,binding
    from gurobipy import GRB
    from round98_projection_vector_audit import check
    from round70_affinity import inherited_core
    ensure_idle();d=OUT/'diagnostics'/label;d.mkdir(parents=True,exist_ok=False)
    pool=OUT/'diagnostics/pool_F2_02';plan=read(pool/'plan.json');rows,_=old_pool('F2')
    dual=read(pool/'dual_support.json');source=ROOT/plan['source'];assert sha(source)==plan['source_sha256']
    tick=time.perf_counter();deadline=tick+cap;calls=0;records={};proofs={}
    with inherited_core() as affinity,gp.Env(empty=True) as engine:
        engine.setParam('OutputFlag',0);engine.start();runtime=binding()
        with gp.read(str(source),env=engine) as old:
            variables=old.getVars();names=[v.VarName for v in variables];byname={n:i for i,n in enumerate(names)}
            with (d/'pool.txt').open('x') as f:
                f.write(f"{plan['source_sha256']} {len(names)} {len(rows)}\n")
                for v in variables:f.write(f'{max(-1e100,v.LB):.17g} {min(1e100,v.UB):.17g}\n')
                for row,lam in zip(rows,dual['multipliers']):
                    f.write(f"{row['vehicle']} {lam:.17g} {row['rhs']:.17g} {len(row['coefficients'])}"+
                        ''.join(f' {byname[n]} {a:.17g}' for n,a in row['coefficients'])+'\n')
            for mode in ['grouped','fleet']:
                cmd=[BUILD/'Round104Compression.exe',d/'pool.txt',mode]
                p=subprocess.run(list(map(str,cmd)),cwd=ROOT,env=env(),capture_output=True,text=True,check=True)
                (d/(mode+'.cpp.json')).write_text(p.stdout,encoding='utf-8')
                generated=json.loads(p.stdout)['rows'];proof=[]
                for row in generated:
                    a={};b=F(0)
                    for j in row['source_rows']:
                        lam=exact(dual['multipliers'][j]);original=rows[j];b+=lam*exact(original['rhs'])
                        for n,value in original['coefficients']:a[n]=a.get(n,F(0))+lam*exact(value)
                    got={names[i]:exact(v) for i,v in row['coefficients']};required=F(0)
                    for n,value in a.items():
                        delta=got.get(n,F(0))-value;v=variables[byname[n]]
                        required+=max(delta*exact(v.LB),delta*exact(v.UB))
                    margin=exact(row['rhs'])-b-required;assert margin>=0
                    proof.append(dict(vehicle=row['vehicle'],exact_weighted_rhs=str(b),exact_required_compensation=str(required),
                        exact_safe_margin=str(margin),sources=row['source_rows']))
                proofs[mode]=proof
                m=old.relax();by={v.VarName:v for v in m.getVars()}
                inserted=[]
                for j,row in enumerate(generated):inserted.append(m.addConstr(gp.quicksum(a*by[names[i]] for i,a in row['coefficients'])<=row['rhs'],name=f'cpp_{j}'))
                m.update()
                for row,actual in zip(generated,inserted):
                    expression=m.getRow(actual)
                    got={expression.getVar(t).index:expression.getCoeff(t) for t in range(expression.size())}
                    assert got==dict(row['coefficients']) and actual.Sense=='<' and actual.RHS==row['rhs'], 'C++ row changed on API readback'
                m.Params.Threads=1;m.Params.Seed=0;m.Params.Presolve=-1;m.Params.Method=1
                m.Params.FeasibilityTol=1e-9;m.Params.OptimalityTol=1e-9;m.Params.TimeLimit=max(.001,deadline-time.perf_counter());calls+=1
                with (d/'calls.jsonl').open('a') as f:f.write(json.dumps(dict(event='Optimize_begin',serial=calls,kind=mode))+'\n')
                m.optimize()
                with (d/'calls.jsonl').open('a') as f:f.write(json.dumps(dict(event='Optimize_return',serial=calls,kind=mode,status=m.Status,seconds=m.Runtime))+'\n')
                assert m.Status==GRB.OPTIMAL
                point={v.VarName:v.X for v in m.getVars()};r=check(m,point)
                records[mode]=dict(objective=m.ObjVal,residual=r,rows=len(generated),signed_minus_ALL=m.ObjVal-read(pool/'ALL.json')['objective'],
                    type_restoration='only disposable relax; original typed model retained',old_columns_unchanged=True,
                    old_rows=m.NumConstrs-len(generated),old_objective_constant=old.ObjCon,old_objective_sense=old.ModelSense)
                assert all((a.VarName,a.LB,a.UB,a.Obj)==(b.VarName,b.LB,b.UB,b.Obj) for a,b in zip(old.getVars(),m.getVars()))
                with gzip.open(d/(mode+'.point.json.gz'),'wt') as f:json.dump(point,f)
                m.dispose()
    write(d/'exact_compensation.json',proofs)
    write(d/'summary.json',dict(passed=True,records=records,Optimize_calls=calls,DP_calls=0,
        compression_binary_sha256=sha(BUILD/'Round104Compression.exe'),source_sha256=plan['source_sha256'],
        runtime=runtime,affinity=affinity,seconds=time.perf_counter()-tick,
        qualification='exact Fraction validity of actual C++ output, numerical reoptimized objective; no exact optimality'))
    print(json.dumps(records),flush=True)
if __name__=='__main__':main(sys.argv[1],float(sys.argv[2]))
