"""Exactly6 micro MIPs +6 root LPs +6 standalone presolves, no formal timing."""
import sys,time,json,gzip,collections,math
from round99_gurobi_runtime import gp,binding
from gurobipy import GRB
from round99_common import *
from round99_idle import ensure_idle
from round98_qualification import physics,residual
from round98_projection_vector_audit import check
from round99_factor_diagnostic import size,signature

MODES=['m-binary','m-binary-linked']
def direction_rows(m,p):
    names={v.VarName for v in m.getVars()};answer=[]
    for i,b in enumerate(p['initial'][1:],1):
        terms={f'mode_{k}_{i}':1.0 for k in range(p['M'])}
        for name in names:
            if name.startswith(f'state_{i}_') and int(name.split('_')[-1])<b:terms[name]=-1.0
        answer.append(('=',0.0,tuple(sorted(terms.items()))))
    return answer
def row_signatures(m):
    rows=[]
    for c in m.getConstrs():
        row=m.getRow(c);rows.append((c.Sense,c.RHS,tuple(sorted((row.getVar(j).VarName,row.getCoeff(j)) for j in range(row.size())))))
    return collections.Counter(rows)
def run(label):
    ensure_idle();runtime=binding();dest=OUT/'diagnostics'/label;dest.mkdir(parents=True,exist_ok=False)
    tick=time.monotonic();calls=0;records=[];micro=[];expected=physics()
    write(dest/'plan.json',dict(maximum_optimize=12,maximum_presolve=6,process_cap=300,scope='registered linked_plan.md qualification',runtime=runtime))
    def settings(m):
        for name,value in dict(Threads=1,Seed=0,Presolve=-1,MIPGap=0,MIPGapAbs=0,FeasibilityTol=1e-6,IntFeasTol=1e-5,OptimalityTol=1e-6).items():setattr(m.Params,name,value)
    def optimize(m,name):
        nonlocal calls
        assert calls<12;settings(m);m.Params.TimeLimit=max(.001,285-(time.monotonic()-tick))
        with (dest/'calls.jsonl').open('a') as f:f.write(json.dumps(dict(kind='start',name=name))+'\n');f.flush()
        calls+=1;m.optimize()
        with (dest/'calls.jsonl').open('a') as f:f.write(json.dumps(dict(kind='return',name=name,status=m.Status,runtime=m.Runtime))+'\n');f.flush()
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start();assert gp.gurobi.version()==(13,0,2)
        for suffix in ['', '_forced','_empty']:
            for mode in MODES:
                path=OUT/'linked_micro_models01'/(mode+suffix+'.lp')
                with gp.read(str(path),env=env) as m:
                    optimize(m,mode+suffix)
                    if suffix=='_empty':assert m.Status==GRB.INFEASIBLE;quality=None
                    else:
                        assert m.Status==GRB.OPTIMAL and abs(m.ObjVal-(0 if suffix else expected['optimum']))<=1e-7
                        quality=residual(m);assert quality['max_row']<=1e-6 and quality['max_bound']<=1e-6 and quality['max_physical_operation_integrality']<=1e-5
                    micro.append(dict(mode=mode,case=suffix,status=m.Status,objective=m.ObjVal if m.SolCount else None,residual=quality,model_sha256=sha(path)))
        for p in read(OUT/'development_inputs.json')['roles']:
            import generate_citibike443_regional_v1 as parser
            ind=parser.parse_instance_mirror(ROOT/p['input_path']);opened={};vectors={};local=[]
            for mode in MODES:
                path=OUT/'linked_exports01'/p['id']/(mode+'.lp');assert sha(path)==read(path.with_suffix('.json'))['sha256']
                m=gp.read(str(path),env=env);opened[mode]=m;settings(m)
                assert all(v.VType=='C' for v in m.getVars() if v.VarName.startswith(('p_','d_')))
                assert all(v.VType=='B' for v in m.getVars() if v.VarName.startswith('mode_'))
                pm=m.presolve();presolved=size(pm);pm.dispose()
                relaxed=m.relax();optimize(relaxed,p['id']+'_'+mode+'_raw_LP');assert relaxed.Status==GRB.OPTIMAL
                values={v.VarName:v.X for v in relaxed.getVars()};vectors[mode]=values;checked=check(relaxed,values)
                assert checked['maximum_absolute_residual']<=1e-6
                with gzip.open(dest/(p['id']+'_'+mode+'_values.json.gz'),'wt') as f:json.dump(values,f)
                local.append(dict(mode=mode,model_sha256=sha(path),original=size(m),presolved=presolved,raw_LP=relaxed.ObjVal,
                    raw_LP_runtime=relaxed.Runtime,raw_LP_iterations=relaxed.IterCount,maximum_residual=checked['maximum_absolute_residual'],typed_signature=signature(m,True)))
                relaxed.dispose()
            a,b=opened[MODES[0]],opened[MODES[1]]
            assert [(v.VarName,v.LB,v.UB,v.Obj,v.VType) for v in a.getVars()]==[(v.VarName,v.LB,v.UB,v.Obj,v.VType) for v in b.getVars()]
            before,after=row_signatures(a),row_signatures(b);added=collections.Counter(direction_rows(b,dict(ind,M=p['M'])))
            assert after==before+added,'change extends beyond the registered direction equalities'
            assert b.NumConstrs-a.NumConstrs==p['V'] and a.NumVars==b.NumVars
            assert local[1]['raw_LP']+1e-7>=local[0]['raw_LP']
            old=vectors[MODES[0]];violations=[]
            for sense,rhs,terms in direction_rows(b,dict(ind,M=p['M'])):
                lhs=sum(coef*old[name] for name,coef in terms);violations.append(abs(lhs-rhs))
            records.append(dict(role=p['id'],records=local,old_LP_point_new_row_maximum_violation=max(violations),
                new_row_violations=violations,exact_new_rows=p['V'],no_new_columns=True,old_rows_unchanged=True))
            for m in opened.values():m.dispose()
    assert calls==12 and any(r['old_LP_point_new_row_maximum_violation']>1e-6 for r in records),'no actual nonredundancy evidence'
    summary=dict(passed=True,optimizer_calls=calls,presolve_calls=6,runtime=runtime,micro=micro,real=records,
        source_bindings=bindings(),binary_sha256=sha(BUILD/'ExactEBRP.exe'),script_sha256=sha(__file__),outer_seconds=time.monotonic()-tick,
        scope='correctness/matrix qualification only; no end-to-end performance claim')
    write(dest/'summary.json',summary);print(json.dumps(summary),flush=True)
if __name__=='__main__':run(sys.argv[1])
