"""Complete-LP numerical primals and exact binary64 dual residual support.

No primal objective is substituted for a dual lower bound. Finite bounds
below are implied by existing rows; they do not change the declared LP Q.
"""
from fractions import Fraction as F
from round143_math import outward
from round143_lp import semantics, residual
from round153_common import *

def add_rows(m,rows,gp):
    vs={v.VarName:v for v in m.getVars()}
    for r in rows:
        e=gp.quicksum(a*vs[k] for k,a in r['terms'].items())
        m.addConstr(e>=r['rhs'] if r['sense']=='>' else e<=r['rhs'] if r['sense']=='<' else e==r['rhs'],name=r['name'])
    m.update()

def finite_bounds(m):
    """Outward bound propagation, only where a model bound is infinite.

    A <= b implies a_j x_j <= b-min(sum_{k!=j} a_k x_k).
    Each saved derivation uses only current proved bounds. Both sides of an
    equality are eligible. No auxiliary can be lowered to justify a cap.
    """
    bounds={v.VarName:[v.LB if v.LB>-1e99 else None,v.UB if v.UB<1e99 else None] for v in m.getVars()}
    rows=[]
    for c in m.getConstrs():
        e=m.getRow(c);terms=[(e.getVar(j).VarName,F(e.getCoeff(j))) for j in range(e.size())]
        for sign in ([1,-1] if c.Sense=='=' else [1] if c.Sense=='<' else [-1]):
            rows.append((c.ConstrName,sign,[(k,a*sign) for k,a in terms],F(c.RHS)*sign))
    derivations=[]
    for iteration in range(12):
        changed=0
        for name,sign,terms,rhs in rows:
            values=[];missing=[]
            for j,(k,a) in enumerate(terms):
                b=bounds[k][0 if a>0 else 1]
                if b is None:missing.append(j);values.append(None)
                else:values.append(a*F(b))
            if len(missing)>1:continue
            total=sum((v for v in values if v is not None),F(0))
            for j,(k,a) in enumerate(terms):
                side=1 if a>0 else 0
                if bounds[k][side] is not None or (missing and j!=missing[0]):continue
                q=(rhs-total+(values[j] or F(0)))/a
                value=outward(q,side==1)
                bounds[k][side]=value;changed+=1
                derivations.append(dict(variable=k,side=['LB','UB'][side],value=value,exact=str(q),row=name,row_sign=sign,pass_index=iteration))
        if not changed:break
    return bounds,derivations

def dual_certificate(m,pi=None,bounds=None,exclude_columns=(),exclude_rhs=()):
    """Exact residual support for stored binary64 matrix/multipliers.

    For coupled RMPs exclude lambda columns and convexity RHS to obtain C_Q.
    Every original-Q column and every original row still participates.
    """
    if bounds is None:bounds,_=finite_bounds(m)
    excluded=set(exclude_columns);excluded_rhs=set(exclude_rhs)
    vs={v.VarName:v for v in m.getVars() if v.VarName not in excluded}
    rc={k:F(v.Obj) for k,v in vs.items()};value=F(m.ObjCon);repairs=[];multipliers={}
    for c in m.getConstrs():
        raw=F(pi.get(c.ConstrName,0.) if pi is not None else c.Pi)
        p=max(F(0),raw) if c.Sense=='>' else min(F(0),raw) if c.Sense=='<' else raw
        if p!=raw:repairs.append(c.ConstrName)
        multipliers[c.ConstrName]=float(p)
        if not p:continue
        if c.ConstrName not in excluded_rhs:value+=p*F(c.RHS)
        e=m.getRow(c)
        for j in range(e.size()):
            k=e.getVar(j).VarName
            if k in rc:rc[k]-=p*F(e.getCoeff(j))
    row_value=value;infinite=[];contributions={}
    for k,r in rc.items():
        if not r:continue
        bound=bounds[k][0 if r>0 else 1]
        if bound is None:infinite.append(dict(variable=k,residual_exact=str(r)));continue
        term=r*F(bound);value+=term
        if term:contributions[k]=str(term)
    return dict(qualified=not infinite,lower=outward(value,False) if not infinite else None,
                lower_exact=str(value) if not infinite else None,row_objective_exact=str(row_value),
                residual_support_exact=str(value-row_value),sign_repairs=repairs,
                unresolved_infinite=infinite,multipliers=multipliers,
                nonzero_column_residuals={k:str(v) for k,v in rc.items() if v},
                bound_contributions_exact=contributions,
                arithmetic='Fraction of actual binary64 matrix, repaired Pi, and outward implied bounds')

def primal_record(m,point=None):
    if point is None:point={v.VarName:v.X for v in m.getVars()}
    check=residual(m,point)
    return dict(qualified=max(check['constraints'],check['bounds'])<=1e-6,
                **check,policy='Inherited numerical LP feasibility qualification; not a rational primal certificate')

def optimize(m,target,cap=180,save_model=True):
    target=Path(target);target.mkdir(parents=True,exist_ok=True)
    m.Params.Threads=1;m.Params.Seed=0;m.Params.TimeLimit=float(cap)
    m.Params.FeasibilityTol=1e-8;m.Params.OptimalityTol=1e-8
    m.Params.Method=1;m.Params.OutputFlag=1;m.Params.LogToConsole=0;m.Params.LogFile=str(target/'native.log')
    m.update()
    if save_model:m.write(str(target/'model.mps'))
    write(target/'call.json',dict(UTC=utc(),kind='LP',Seed=0,Threads=1,cap=cap,
          columns=m.NumVars,rows=m.NumConstrs,nonzeros=m.NumNZs,
          model_SHA=sha(target/'model.mps') if save_model else None,all_original_variables_free=True))
    start=time.perf_counter();m.optimize()
    record=dict(UTC=utc(),Status=m.Status,Runtime=m.Runtime,Work=m.Work,seconds=time.perf_counter()-start,
                iterations=m.IterCount,solution_count=m.SolCount)
    write(target/'return.json',record)
    if m.SolCount:
        save_gz(target/'solution.json.gz',{v.VarName:v.X for v in m.getVars()})
        record['primal']=primal_record(m);record['objective']=m.ObjVal
        if m.Status==2:
            save_gz(target/'dual.json.gz',dict(Pi={c.ConstrName:c.Pi for c in m.getConstrs()},RC={v.VarName:v.RC for v in m.getVars()}))
            record['quality']={k:m.getAttr(k) for k in ['ConstrVio','BoundVio','DualVio','ConstrResidual','DualResidual','ComplVio']}
    return record
