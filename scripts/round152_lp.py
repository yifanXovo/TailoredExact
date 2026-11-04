"""Append explicitly qualified rows to a complete free saved LP."""
from round143_lp import semantics,residual
from round150_lp import affinity,readback
from round145_lp import add_rows
from round152_math import ap_row,gd_rows,old_resource_rows,old_count_factor_rows
from round143_math import denominator,rn_rows
from round152_common import *

def solve(role,variant,parent='B',row_path=None):
    from round100_gurobi_runtime import gp,binding
    configure();affinity();assert binding()['sha256']==DLL_SHA
    d=read(OUT/'domains'/role/'domain.json');target=OUT/'LP'/f'{role}_{variant}';target.mkdir(parents=True,exist_ok=False)
    if parent=='B':source=OUT/'domains'/role/'B.mps';oldL=d['B_L']
    else:
        source=OUT/'LP'/f'{role}_{parent}'/'model.mps';p=read(source.parent/'result.json');assert p['qualified'];oldL=p['L']
    rn_spec=None
    if variant=='AP':rows=[ap_row(d['scope'])]
    elif variant=='strong':rows=gd_rows(d['scope'])+old_resource_rows(d['scope'])
    elif variant.startswith('strongCP'):rows=old_count_factor_rows(d['scope'])
    elif variant=='strongRN':
        ss=d['scope']['stations'];rn_spec=denominator({s['i']:s['c'] for s in ss},{s['i']:s['support'] for s in ss},d['scope']['Bminus'],d['scope']['B'])
        assert rn_spec['applicable'],'Continuous positive normalization cannot exclude a legal zero state'
        rows=rn_rows(rn_spec)
        for tag,sense,bound in [('low','>',d['scope']['Bminus']),('high','<',d['scope']['B'])]:
            terms={f'rn_Y_{s["i"]}':1. for s in ss};terms['rn_t']=-float(bound)
            rows.append(dict(name='r152_known_RN_stock_'+tag,terms={k:v for k,v in terms.items() if v},sense=sense,rhs=0.))
    else:
        assert row_path;bundle=read(row_path);assert bundle['qualified'];assert bundle['scope']==d['scope']
        rows=bundle['rows']
    write(target/'rows.json',rows)
    tick=time.perf_counter()
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Threads',1);env.setParam('Seed',0);env.start()
        with gp.read(str(source),env=env) as m:
            assert not m.IsMIP and all(v.VType=='C' for v in m.getVars())
            oldsem=semantics(m);names={v.VarName for v in m.getVars()};cnames={c.ConstrName for c in m.getConstrs()}
            before=dict(columns=m.NumVars,rows=m.NumConstrs,nonzeros=m.NumNZs)
            if rn_spec:
                from itertools import combinations
                m.addVar(lb=rn_spec['L_t'],ub=rn_spec['U_t'],name='rn_t')
                for s in d['scope']['stations']:
                    m.addVar(lb=0,name=f'rn_Y_{s["i"]}')
                    for y in s['support']:m.addVar(lb=0,ub=rn_spec['U_t'],name=f'rn_w_{s["i"]}_{y}')
                for a,b in combinations(d['scope']['stations'],2):m.addVar(lb=0,name=f'rn_h_{a["i"]}_{b["i"]}')
                m.update()
            add_rows(m,rows,gp);assert semantics(m,names,cnames)==oldsem
            m.write(str(target/'model.mps'))
        with gp.read(str(target/'model.mps'),env=env) as m:
            assert semantics(m,names,cnames)==oldsem;readback(m,rows)
            m.Params.TimeLimit=180;m.Params.OutputFlag=1;m.Params.LogToConsole=0;m.Params.LogFile=str(target/'native.log')
            m.Params.FeasibilityTol=1e-6;m.Params.OptimalityTol=1e-6
            write(target/'call.json',dict(UTC=utc(),model_SHA=sha(target/'model.mps'),source_SHA=sha(source),Native=binding(),Seed=0,Threads=1,cap=180,kind='LP',all_variables_free=True))
            built=time.perf_counter();m.optimize();done=time.perf_counter()
            write(target/'return.json',dict(UTC=utc(),Status=m.Status,Runtime=m.Runtime,Work=m.Work))
            result=dict(role=role,variant=variant,parent=parent,L=None,qualified=False,old_L=oldL,before=before,
                        after=dict(columns=m.NumVars,rows=m.NumConstrs,nonzeros=m.NumNZs),added_rows=len(rows),added_nonzeros=sum(len(r['terms']) for r in rows),
                        construct_seconds=built-tick,optimize_seconds=done-built,Runtime=m.Runtime,Work=m.Work,iterations=m.IterCount,
                        Status=m.Status,Optimize_new=1,all_variables_free=True,original_semantics_retained=True,model_SHA=sha(target/'model.mps'))
            if m.SolCount:
                point={v.VarName:v.X for v in m.getVars()};save_gz(target/'solution.json.gz',point)
                quality={k:m.getAttr(k) for k in ['ConstrVio','BoundVio','DualVio','ConstrResidual','DualResidual','ComplVio']};check=residual(m,point)
                dual=m.ObjCon+math.fsum(c.Pi*c.RHS for c in m.getConstrs());infinite=[];terms=[]
                for v in m.getVars():
                    b=v.LB if v.RC>=0 else v.UB
                    if abs(b)<gp.GRB.INFINITY:terms.append(v.RC*b)
                    else:infinite.append(abs(v.RC))
                dual+=math.fsum(terms)
                save_gz(target/'dual.json.gz',dict(Pi={c.ConstrName:c.Pi for c in m.getConstrs()},RC={v.VarName:v.RC for v in m.getVars()}))
                ap=math.fsum(s['omega']*abs(s['c']*y-1)*point[f'state_{s["i"]}_{y}'] for s in d['scope']['stations'] for y in s['support'])
                result.update(L=m.ObjVal,g=point['G'],penalty=m.ObjVal-point['G'],AP_expectation=ap,gain=m.ObjVal-oldL,quality=quality,residual=check,
                              numerical_dual_objective=dual,primal_dual_gap=m.ObjVal-dual,infinite_adverse_RC=max(infinite or [0]),
                              qualified=m.Status==gp.GRB.OPTIMAL and max(quality.values())<=1e-6 and max(check['constraints'],check['bounds'])<=1e-6)
            write(target/'result.json',result)
    print(json.dumps(result),flush=True)

if __name__=='__main__':solve(*sys.argv[1:])
