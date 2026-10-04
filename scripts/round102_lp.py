"""Preregistered finite full-old-matrix implications and objective checks.
Maximum24 Optimize calls (six/role), no native search or performance claims.
"""
from round102_common import *
from round102_screen import matrix_names,OLD
from round102_support import exact
from fractions import Fraction as F
import sys,math
def main(label):
    from round100_idle import ensure_idle
    ensure_idle()
    from round100_gurobi_runtime import gp,binding
    from gurobipy import GRB
    from round98_projection_vector_audit import check
    from round70_affinity import inherited_core
    d=OUT/'diagnostics'/label;d.mkdir(parents=True,exist_ok=False);calls=0;records=[]
    write(d/'plan.json',dict(roles=['F2','R98-C2','R99-N2','F5'],per_solve_cap=120,maximum_calls=24,
        operations=['original objective','two saved full-A S row implications','actual-direction J implication','fixed-charge J implication','original objective plus qualified rows'],
        question='actual old-LP separation versus implication and objective gain; maximum incumbent only proves violation, no implication without upper proof'))
    def optimize(m,role,kind):
        nonlocal calls
        with (d/'calls.jsonl').open('a') as f:f.write(json.dumps(dict(event='start',role=role,kind=kind))+'\n');f.flush()
        calls+=1;m.Params.TimeLimit=120;m.optimize()
        r=dict(event='return',role=role,kind=kind,status=m.Status,seconds=m.Runtime,
            objective=m.ObjVal if m.SolCount else None,bound=m.ObjBound if m.IsMIP else (m.ObjVal if m.Status==GRB.OPTIMAL else None))
        with (d/'calls.jsonl').open('a') as f:f.write(json.dumps(r)+'\n');f.flush()
        assert m.Status==GRB.OPTIMAL,r
        return r
    with inherited_core() as affinity,gp.Env(empty=True) as engine:
        engine.setParam('OutputFlag',0);engine.start();runtime=binding();assert gp.gurobi.version()==(13,0,2)
        sources={r['role']:r for r in read(OLD/'diagnostics/lp01/summary.json')['records']}
        for role in ['F2','R98-C2','R99-N2','F5']:
            rd=d/role;rd.mkdir();source=ROOT/sources[role]['actual_source'];assert sha(source)==sources[role]['actual_sha256']
            with gp.read(str(source),env=engine) as original:
                m=original.relax();m.Params.Threads=1;m.Params.Seed=0;m.Params.LogFile=str(rd/'gurobi.log')
                vars=m.getVars();assert [v.VarName for v in vars]==matrix_names(role);by={v.VarName:v for v in vars};obj=m.getObjective()
                q=read(OUT/'diagnostics/screen01'/role/'raw.json');c=q['contract'];W=[r for r in q['J'] if r['family'] in ['actual-direction','fixed-charge']]
                initial=optimize(m,role,'original_objective');old=initial['objective'];original_checks=[]
                for kind in ['raw','implication_0','implication_1']:
                    bank=OLD/'compact_evidence/lp'/role
                    vals=list(map(float,(bank/'raw.point').read_text().split())) if kind=='raw' else read(bank/(kind+'.json'))['point']
                    residual=check(m,{v.VarName:x for v,x in zip(vars,vals)});assert residual['maximum_absolute_residual']<1e-6
                    original_checks.append(dict(kind=kind,residual=residual))
                rows=[];implications=[]
                for j in [0,1]:
                    saved=read(OLD/'compact_evidence/lp'/role/f'implication_{j}.json')['row'];es=saved['proof']['events']
                    coeff={};rhs=F(saved['proof']['rank']);used=[]
                    for i,s,qv in es:
                        cap=min(c['initial'][i] if s<0 else c['station_capacity'][i]-c['initial'][i],max(c['capacities']))
                        if qv>cap:continue
                        a=F(1,cap-qv+1);rhs+=(qv-1)*a;used.append([i,s,qv])
                        # nonnegative coefficients rounded DOWN; RHS rounded UP
                        af=math.nextafter(float(a),-math.inf)
                        for k in range(len(c['capacities'])):coeff[f'{"p" if s<0 else "d"}_{k}_{i}']=af
                    if not coeff:raise RuntimeError('empty S containment candidate')
                    rf=math.nextafter(float(rhs),math.inf);expr=gp.quicksum(a*by[name] for name,a in coeff.items())
                    m.setObjective(expr,GRB.MAXIMIZE);r=optimize(m,role,f'S{j}_implication');r.update(excess=r['objective']-rf,rhs=rf,kind=f'S{j}')
                    residual=check(m,{v.VarName:v.X for v in vars});assert residual['maximum_absolute_residual']<1e-6
                    write(rd/f'S{j}.json',dict(coefficients=coeff,rhs=rf,proof=saved['proof'],active_events=used,rhs_fraction=str(rhs),result=r,residual=residual,
                        point={v.VarName:v.X for v in vars}))
                    rows.append((expr,rf));implications.append(r)
                for r in W:
                    coeff={}
                    for k,wk in enumerate(r['weights']):
                        for i,wi in enumerate(wk[1:],1):
                            for tag,a in zip(['p','d','z'],wi):
                                if a:coeff[f'{tag}_{k}_{i}']=a
                    expr=gp.quicksum(a*by[name] for name,a in coeff.items());m.setObjective(expr,GRB.MAXIMIZE)
                    out=optimize(m,role,r['family']+'_implication');out.update(excess=out['objective']-r['rhs'],rhs=r['rhs'],kind=r['family'])
                    residual=check(m,{v.VarName:v.X for v in vars});assert residual['maximum_absolute_residual']<1e-6
                    write(rd/(r['family']+'.json'),dict(coefficients=coeff,rhs=r['rhs'],support_certificate=r,result=out,residual=residual,
                        point={v.VarName:v.X for v in vars}))
                    rows.append((expr,r['rhs']));implications.append(out)
                m.setObjective(obj,GRB.MINIMIZE)
                for expr,rhs in rows:m.addConstr(expr<=rhs)
                strengthened=optimize(m,role,'original_objective_plus_4_rows')
                write(rd/'strengthened_point.json',{v.VarName:v.X for v in vars})
                records.append(dict(role=role,actual_source=str(source.relative_to(ROOT)),actual_sha256=sha(source),original_point_checks=original_checks,
                    original_objective=old,strengthened_objective=strengthened['objective'],delta=strengthened['objective']-old,implications=implications))
                print(json.dumps(records[-1]),flush=True);m.dispose()
    write(d/'summary.json',dict(records=records,Optimize_calls=calls,runtime=runtime,affinity=affinity,passed=True))
if __name__=='__main__':main(sys.argv[1])
