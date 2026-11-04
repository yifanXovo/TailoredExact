"""Complete finite inventory universes versus the declared old strong block.

No route-model or all-historical-hull claim: this is an explicitly defined
inventory objective block with AP, GD, stock, TC/TC2, all count bounds and CP.
Strictness is established by an exact feasible extension and exhaustive
integer objective evaluation, plus a common-distribution feasibility witness.
"""
from fractions import Fraction as F
from itertools import product,combinations
from round152_qualify import scope
from round152_math import *
from round152_discover import complement_dp,make_pi
from round145_lp import add_rows
from round152_common import *

def linear_solve(A,b):
    mat=[list(row)+[rhs] for row,rhs in zip(A,b)];n=len(b)
    for j in range(n):
        pivot=next(i for i in range(j,n) if mat[i][j]);mat[j],mat[pivot]=mat[pivot],mat[j]
        z=mat[j][j];mat[j]=[v/z for v in mat[j]]
        for i in range(n):
            if i!=j and mat[i][j]:
                v=mat[i][j];mat[i]=[a-v*b for a,b in zip(mat[i],mat[j])]
    return [mat[i][-1] for i in range(n)]

def exact_basis(m,rhs_override=None):
    vs=m.getVars();basic=[v for v in vs if v.VBasis==0];active=[c for c in m.getConstrs() if c.CBasis==-1]
    assert len(basic)==len(active);known={}
    for v in vs:
        if v.VBasis!=0:
            assert v.VBasis in (-1,-2)
            known[v.VarName]=F(v.LB if v.VBasis==-1 else v.UB)
    index={v.VarName:j for j,v in enumerate(basic)};A=[];b=[]
    for c in active:
        row=[F(0)]*len(basic);rhs=F((rhs_override or {}).get(c.ConstrName,c.RHS));e=m.getRow(c)
        for k in range(e.size()):
            name=e.getVar(k).VarName;a=F(e.getCoeff(k))
            if name in index:row[index[name]]=a
            else:rhs-=a*known[name]
        A.append(row);b.append(rhs)
    point=known|dict(zip(index,linear_solve(A,b)))
    violations=[]
    for c in m.getConstrs():
        e=m.getRow(c);lhs=sum(F(e.getCoeff(k))*point[e.getVar(k).VarName] for k in range(e.size()));rhs=F((rhs_override or {}).get(c.ConstrName,c.RHS))
        v=max(F(0),rhs-lhs) if c.Sense=='>' else max(F(0),lhs-rhs) if c.Sense=='<' else abs(lhs-rhs)
        if v:violations.append((c.ConstrName,str(v),float(v)))
    for v in vs:
        x=point[v.VarName]
        excess=max([F(0)]+([F(v.LB)-x] if math.isfinite(v.LB) else [])+([x-F(v.UB)] if math.isfinite(v.UB) else []))
        if excess:violations.append((v.VarName,'bound',float(excess)))
    return point,violations

def build(gp,env,d):
    m=gp.Model(env=env);ss=d['stations'];n=len(ss)
    s=m.addVars([f'state_{i}_{y}' for i,y in states(d)],lb=0,ub=1,name='')
    # Explicit names avoid tuple-key pretty-printing in the reference rows.
    for name,v in s.items():v.VarName=name
    q={};Y={};r={};e={};z={}
    G=m.addVar(lb=d['gamma_L'],ub=d['gamma_U'],obj=1,name='G')
    for site in ss:
        i=site['i'];ys=site['support']
        Y[i]=m.addVar(lb=min(ys),ub=max(ys),name=f'Y_{i}');r[i]=m.addVar(lb=0,name=f'r_{i}')
        e[i]=m.addVar(lb=0,obj=site['omega'],name=f'e_{i}');z[i]=m.addVar(lb=0,name=f'zprod_{i}')
        for y in ys:
            q[i,y]=m.addVar(lb=0,name=f'state_g_{i}_{y}')
            m.addConstr(q[i,y]>=d['gamma_L']*s[f'state_{i}_{y}']);m.addConstr(q[i,y]<=d['gamma_U']*s[f'state_{i}_{y}'])
        m.addConstr(gp.quicksum(s[f'state_{i}_{y}'] for y in ys)==1)
        m.addConstr(Y[i]==gp.quicksum(y*s[f'state_{i}_{y}'] for y in ys))
        m.addConstr(r[i]==site['c']*Y[i]);m.addConstr(e[i]>=r[i]-1);m.addConstr(e[i]>=1-r[i])
        m.addConstr(gp.quicksum(q[i,y] for y in ys)==G);m.addConstr(z[i]==gp.quicksum(y*q[i,y] for y in ys))
    hh=[]
    for i,j in combinations(Y,2):
        h=m.addVar(lb=0,name=f'h_{i}_{j}');hh.append(h);m.addConstr(h>=r[i]-r[j]);m.addConstr(h>=r[j]-r[i])
    m.addConstr(gp.quicksum(hh)<=n*gp.quicksum(site['c']*z[site['i']] for site in ss))
    m.addConstr(gp.quicksum(Y.values())>=d['Bminus']);m.addConstr(gp.quicksum(Y.values())<=d['B'])
    m.update();add_rows(m,[ap_row(d)]+gd_rows(d)+old_resource_rows(d)+old_count_factor_rows(d),gp)
    return m

def run(label='v1'):
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    configure();affinity();assert binding()['sha256']==DLL_SHA;target=OUT/'small'/label;target.mkdir(parents=True,exist_ok=False)
    cases=[('equal_known',scope([1.]*4,[[0,1,2]]*4,0,3,0.,.75,[.15]*4)),
           ('heterogeneous_tight',scope([1.,.5,1.,.5],[[0,1,2]]*4,3,5,0.,.75)),
           ('heterogeneous_wide',scope([1.,.5,.25],[[0,1,2,3,4]]*3,2,5,0.,.75)),
           ('nonminimal_lower',scope([1.,.5,1.,.5],[[0,1,2]]*4,3,5,.125,.75))]
    facts=[]
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Threads',1);env.setParam('Seed',0);env.start()
        for tag,d in cases:
            folder=target/tag;folder.mkdir();universe=[evaluate(d,Y,exact=True) for Y in product(*[s['support'] for s in d['stations']])];universe=[p for p in universe if p['feasible']]
            integer=min(p['phi'] for p in universe)
            with build(gp,env,d) as m:
                m.Params.Method=1;m.Params.TimeLimit=30;m.write(str(folder/'reference.mps'))
                write(folder/'call.json',dict(UTC=utc(),kind='LP',Seed=0,Threads=1,cap=30,model_SHA=sha(folder/'reference.mps')))
                m.optimize();write(folder/'return.json',dict(UTC=utc(),Status=m.Status,Runtime=m.Runtime,Work=m.Work));assert m.Status==2
                exact,viol=exact_basis(m);value=F(m.ObjCon)+sum(F(v.Obj)*exact[v.VarName] for v in m.getVars())
                record=dict(tag=tag,scope=d,LP=m.ObjVal,exact_reference_objective=str(value),exact_integer_minimum=str(integer),gap=float(integer-value),
                            exact_extension_feasible=not viol,exact_extension_violations=viol,integer_vectors=len(universe),Optimize=1)
                save_gz(folder/'exact_extension.json.gz',{k:str(v) for k,v in exact.items()})
                if not viol:
                    # Match the exact reconstructed marginal in the full finite domain.
                    with gp.Model(env=env) as joint:
                        lam=joint.addVars(len(universe),lb=0,name='lambda');rhs={'mass':F(1)};joint.addConstr(lam.sum()==1,name='mass')
                        for s in d['stations']:
                            for y in s['support'][:-1]:
                                name=f's_{s["i"]}_{y}';v=exact[f'state_{s["i"]}_{y}'];rhs[name]=v
                                joint.addConstr(gp.quicksum(lam[k] for k,p in enumerate(universe) if p['Y'][s['i']-1]==y)==float(v),name=name)
                        joint.setObjective(gp.quicksum(float(p['phi'])*lam[k] for k,p in enumerate(universe)));joint.Params.Method=1;joint.Params.TimeLimit=30
                        joint.update();joint.write(str(folder/'joint.mps'));write(folder/'joint_call.json',dict(UTC=utc(),kind='LP_finite_joint',Seed=0,Threads=1,cap=30))
                        joint.optimize();write(folder/'joint_return.json',dict(UTC=utc(),Status=joint.Status,Runtime=joint.Runtime,Work=joint.Work))
                        record['Optimize']+=1
                        if joint.Status==2:
                            jp,jv=exact_basis(joint,rhs);mixture=[dict(weight=str(jp[lam[k].VarName]),Y=p['Y'],phi=str(p['phi'])) for k,p in enumerate(universe) if jp[lam[k].VarName]]
                            record.update(exact_joint_compatible=not jv,exact_joint_violations=jv,joint_LP=joint.ObjVal,mixture=mixture,
                                          strict_objective_gap_beyond_declared_strong_block=not jv and integer>value)
                # Independent exact complement DP for signed residual potentials.
                active={s['i']:s['support'][:max(1,len(s['support'])-1)] for s in d['stations']};anchors={s['i']:0. for s in d['stations']}
                psi={(s['i'],y):(.125 if y%2 else -.25) for s in d['stations'] for y in active[s['i']]};pi=make_pi(d,psi,active,.75,anchors)
                cc=complement_dp(d,active,pi)
                outside=[p for p in universe if any(y not in active[s['i']] for s,y in zip(d['stations'],p['Y']))]
                if outside:assert not cc['empty'] and F(cc['lower'])<=min(evaluate(d,p['Y'],pi,True)['price'] for p in outside)
                record['complement_DP_exact_validity']=True
                write(folder/'result.json',record);facts.append(record)
    write(target/'result.json',dict(facts=facts,scope='complete declared finite inventory objective block, not full routes',
           new_strict_examples=sum(bool(f.get('strict_objective_gap_beyond_declared_strong_block')) for f in facts),complement_qualification_PASS=True))
    print(json.dumps([{k:v for k,v in f.items() if k not in ['scope','mixture']} for f in facts]),flush=True)

if __name__=='__main__':run(*sys.argv[1:])
