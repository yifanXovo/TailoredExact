"""Finite serial same-domain LPs, canonical matrices and numerical floors.

This is an offline diagnostic, not an online NativeEvidence producer. No child
can enter the Gini scheduler, and nothing is installed in a complete method.
"""
from round141_common import *
from round141_math import F, membership, child_rows, downward
import gzip, re

def floor(value, cutoff):
    return max(0.,math.nextafter(min(value,cutoff)-1e-7,-math.inf))

def add_chord(gp, model, vs, coefficients, constant, name):
    # Same exact power-of-two minimum-coefficient policy as the R140 writer.
    terms = {k:-v for k,v in coefficients.items()}
    terms.update({k:1. for k in vs if re.fullmatch(r'h_\d+_\d+',k)})
    smallest=min([abs(v) for v in terms.values() if v] or [1.])
    exponent=0
    while math.ldexp(smallest,exponent)<1e-12: exponent+=1
    actual={k:math.ldexp(v,exponent) for k,v in terms.items() if v}
    rhs=math.ldexp(constant,exponent)
    assert all(math.isfinite(v) for v in [*actual.values(),rhs])
    model.addConstr(gp.quicksum(v*vs[k] for k,v in actual.items())>=rhs,name=name)
    return dict(name=name,terms=actual,sense='>',rhs=rhs,scale_exponent=exponent)

def build_parent(gp,env,role):
    scope=read(OUT/'domains'/role/'scope.json')
    add=read(OUT/'domains'/role/'additions.json')
    source=Path(scope['stock_model']);assert sha(source)==scope['stock_SHA']
    model=gp.read(str(source),env=env)
    for v in model.getVars():v.VType=gp.GRB.CONTINUOUS
    model.update();vs={v.VarName:v for v in model.getVars()}
    audits=[add_chord(gp,model,vs,add['TC'],0.,'r141_parent_TC'),
            add_chord(gp,model,vs,add['TC2'],add['constant'],'r141_parent_TC2')]
    model.update()
    return model,vs,scope,add,audits

def append_objective_floor(gp,model,vs,beta0,beta1,conditional):
    """Downward affine endpoint writer with the complete ObjCon."""
    constant=model.ObjCon
    b0=beta0 if conditional else min(beta0,beta1)
    b1=beta1 if conditional else b0
    base=downward(F(b0)-F(constant))
    delta=downward(F(b1)-F(constant)-F(base)) if conditional else 0.
    assert F(base)+F(constant)<=F(b0)
    assert F(base)+F(delta)+F(constant)<=F(b1)
    terms={v.VarName:v.Obj for v in model.getVars() if v.Obj}
    if delta:terms['r141_b']=-delta
    model.addConstr(gp.quicksum(v*vs[k] for k,v in terms.items())>=base,name='r141_objective_floor')
    return dict(name='r141_objective_floor',terms=terms,sense='>',rhs=base,
        objective_constant=constant,beta0=beta0,beta1=beta1,conditional=conditional,
        actual_endpoint0=base+constant,actual_endpoint1=base+delta+constant,
        exact_endpoint0=str(F(base)+F(constant)),
        exact_endpoint1=str(F(base)+F(delta)+F(constant)),delta=delta)

def projected_floor(K,ell,u,m,beta0,beta1):
    """Exact scalar projection of the stated, unrounded ideal D1 rows."""
    if not ell<=K<=u:return None
    if beta1>=beta0:return max(beta0,beta0+(beta1-beta0)*(K-m)/(u-m))
    return max(beta1,beta1+(beta0-beta1)*(m+1-K)/(m+1-ell))

def solve(spec, suffix=''):
    ctypes.windll.kernel32.SetProcessAffinityMask(ctypes.windll.kernel32.GetCurrentProcess(),4)
    from round100_gurobi_runtime import gp,binding
    identity=binding();assert identity['sha256']==DLL_SHA
    label=spec['label']+suffix
    target=OUT/'LP'/label;target.mkdir(parents=True,exist_ok=False)
    tick=time.perf_counter()
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        model,vs,scope,add,audits=build_parent(gp,env,spec['role'])
        before=dict(rows=model.NumConstrs,columns=model.NumVars,nonzeros=model.NumNZs)
        variant=spec['variant']; K=None
        if variant in ['plain','conditional','d0','d1']:
            keys=membership(add,spec['threshold']);K=gp.quicksum(vs[k] for k in keys)
            m=spec['pivot']
            if variant in ['plain','conditional']:
                sense,rhs=('<',m) if spec['side']=='low' else ('>',m+1)
                model.addConstr(K<=rhs if sense=='<' else K>=rhs,name='r141_count_side')
                audits.append(dict(name='r141_count_side',terms={k:1. for k in keys},sense=sense,rhs=rhs))
                if variant=='conditional':
                    child=child_rows(add,spec['threshold'],m,spec['side'])
                    assert not child['incompatible'],child
                    write(target/'conditional_exact.json',child)
                    audits.append(add_chord(gp,model,vs,child['coefficients'],child['constant'],'r141_child_TC2'))
            else:
                b=model.addVar(lb=0,ub=1,vtype=gp.GRB.CONTINUOUS,name='r141_b')
                model.update();vs['r141_b']=b
                model.addConstr(K-(spec['u']-m)*b<=m,name='r141_count_upper')
                model.addConstr(K-(m+1-spec['ell'])*b>=spec['ell'],name='r141_count_lower')
                audits.extend([
                    dict(name='r141_count_upper',terms={**{k:1. for k in keys},'r141_b':-(spec['u']-m)},sense='<',rhs=m),
                    dict(name='r141_count_lower',terms={**{k:1. for k in keys},'r141_b':-(m+1-spec['ell'])},sense='>',rhs=spec['ell'])])
                audits.append(append_objective_floor(gp,model,vs,*spec['betas'],variant=='d1'))
        elif variant=='gini':
            raise RuntimeError('Gini controls require a rebuilt, source-matched canonical child, not a G-bound-only edit')
        else: assert variant=='parent'
        model.update()
        model.Params.Threads=1;model.Params.Seed=0;model.Params.Presolve=-1
        model.Params.TimeLimit=spec.get('cap_seconds',90)
        model.Params.FeasibilityTol=1e-6;model.Params.OptimalityTol=1e-6
        # Serialize before Optimize and optimize the actual roundtripped matrix.
        # Windows Native installation has no compressed-MPS writer; archive
        # compression is separate, after timed solves. Keep the actual MPS.
        canonical=target/'model.mps';model.write(str(canonical))
        expected_fingerprint=model.Fingerprint
        original_objective={v.VarName:v.Obj for v in model.getVars()}
        original_constant=model.ObjCon
        after=dict(rows=model.NumConstrs,columns=model.NumVars,nonzeros=model.NumNZs)
        model.dispose();model=gp.read(str(canonical),env=env)
        assert model.Fingerprint==expected_fingerprint
        vs={v.VarName:v for v in model.getVars()}
        assert original_constant==model.ObjCon
        assert original_objective=={v.VarName:v.Obj for v in model.getVars()}
        for row in audits:
            c=model.getConstrByName(row['name']);expr=model.getRow(c)
            actual={expr.getVar(i).VarName:expr.getCoeff(i) for i in range(expr.size())}
            assert actual=={k:float(v) for k,v in row['terms'].items() if v},(label,row['name'])
            assert c.Sense==row['sense'] and c.RHS==row['rhs']
        assert all(v.VType==gp.GRB.CONTINUOUS for v in model.getVars())
        model.Params.Threads=1;model.Params.Seed=0;model.Params.Presolve=-1
        model.Params.TimeLimit=spec.get('cap_seconds',90)
        model.Params.FeasibilityTol=1e-6;model.Params.OptimalityTol=1e-6
        model.Params.LogFile=str(target/'native.log');model.Params.LogToConsole=0;model.Params.OutputFlag=1
        write(target/'scope.json',dict(spec=spec,parent_scope_SHA=sha(OUT/'domains'/spec['role']/'scope.json'),
            parent_support_SHA=sha(OUT/'domains'/spec['role']/'additions.json'),
            source_stock_SHA=scope['stock_SHA'],canonical_SHA=sha(canonical),audits=audits,
            inherited_parent_rows_retained=True,count_scope_local_only=True,
            no_Gini_scheduler=True,complete_linear_objective=original_objective,ObjCon=original_constant))
        constructed=time.perf_counter();model.optimize();finished=time.perf_counter()
        result=dict(spec,status=model.Status,canonical_SHA=sha(canonical),fingerprint=model.Fingerprint,
            before=before,after=after,construction_seconds=constructed-tick,
            optimize_wall_seconds=finished-constructed,Runtime=model.Runtime,Work=model.Work,
            native_identity=identity,Seed=model.Params.Seed,Threads=model.Params.Threads,
            FeasibilityTol=model.Params.FeasibilityTol,OptimalityTol=model.Params.OptimalityTol,
            LP_Optimize=1,MIP_Optimize=0,qualified=False,L=None,beta=None,
            parent_cutoff=scope['validated_U'],parent_g_interval=[scope['alpha'],scope['beta']],
            writer_SHA=sha(ROOT/'scripts/round141_lp.py'),math_SHA=sha(ROOT/'scripts/round141_math.py'),
            source_rev=git('rev-parse','HEAD').decode().strip(),
            source_dirty=bool(git('diff','HEAD','--','scripts/round141_common.py',
                'scripts/round141_math.py','scripts/round141_lp.py')))
        if model.Status==gp.GRB.OPTIMAL:
            point={v.VarName:v.X for v in model.getVars()}
            with gzip.open(target/'solution.json.gz','wt',encoding='utf-8') as stream:
                json.dump(point,stream,separators=(',',':'))
            result['quality']={k:model.getAttr(k) for k in ['ConstrVio','BoundVio','DualVio','ConstrResidual','DualResidual','ComplVio']}
            qualified=all(v<=1e-6 for v in result['quality'].values())
            result.update(L=model.ObjVal,beta=floor(model.ObjVal,scope['validated_U']) if qualified else None,
                qualified=qualified,solution_SHA=sha(target/'solution.json.gz'),
                K=math.fsum(point[k] for k in membership(add,spec['threshold'])) if K is not None else None,
                G=point['G'],tau=math.fsum(point[f'Y_{i}'] for i in range(1,scope['panel']['V']+1)),
                b=point.get('r141_b'))
        elif model.Status==gp.GRB.INFEASIBLE:
            # No Farkas/Native qualification is implemented in this diagnostic.
            # A status alone cannot supply even an improvement-domain floor.
            result.update(qualified=False,beta=None,
                          infeasibility_scope='unverified improvement LP status; side retained; parent bound only')
        write(target/'result.json',result)
        model.dispose()
    print(json.dumps({k:result.get(k) for k in ['label','role','variant','side','pivot','L','beta','qualified','K','b']}),flush=True)

def child_plan():
    return [dict(p,label=f'{p["position"]:02}_{p["role"]}_{p["pivot_kind"]}_{p["side"]}_{p["variant"]}')
            for p in read(OUT/'LP_plan.json')['positions']]

def run_children(suffix=''):
    for role in read(OUT/'LP_plan.json')['roles']:
        label=f'parent_{role}'+suffix
        assert metered(label,'diagnostic',[LP_PYTHON,ROOT/'scripts/round141_lp.py','one',
            json.dumps(dict(label=label,role=role,variant='parent',cap_seconds=90))],110,120)==0
    for spec in child_plan():
        spec['label']+=suffix
        assert metered(spec['label'],'diagnostic',[LP_PYTHON,ROOT/'scripts/round141_lp.py','one',
            json.dumps(spec)],110,120)==0

def select_projections():
    records=[];positions=[]
    for role in read(OUT/'LP_plan.json')['roles']:
        parent=read(OUT/'LP'/f'parent_{role}_mps/result.json')
        inherited=next(r for r in read(OUT/'offline_screen.json')['roles'] if r['role']==role)
        assert abs(parent['L']-inherited['parent']['L'])<5e-7
        cases=[]
        for pivot in inherited['pivots']:
            group={variant:{} for variant in ['plain','conditional']}
            for spec in child_plan():
                if spec['role']!=role or spec['pivot']!=pivot['m']:continue
                row=read(OUT/'LP'/(spec['label']+'_mps')/'result.json')
                assert row['qualified'] and row['status']==2
                group[spec['variant']][spec['side']]=row
            case=dict(pivot=pivot['m'],pivot_kind=pivot['kind'],sides=group)
            for variant in group:
                case[variant+'_cover']=min(r['beta'] for r in group[variant].values())
                case[variant+'_raw_cover']=min(r['L'] for r in group[variant].values())
            cases.append(case)
        # Diagnostic selection only; this is not a per-role online rule.
        chosen=max(cases,key=lambda c:(c['conditional_cover'],-c['pivot']))
        threshold=inherited['chosen']
        for mode in ['d0','d1']:
            positions.append(dict(label=f'{role}_{chosen["pivot_kind"]}_{mode}',role=role,variant=mode,
                threshold=threshold['threshold'],ell=threshold['ell'],u=threshold['u'],
                pivot=chosen['pivot'],pivot_kind=chosen['pivot_kind'],
                betas=[chosen['sides']['conditional'][s]['beta'] for s in ['low','high']],
                proof_sources=[chosen['sides']['conditional'][s]['canonical_SHA'] for s in ['low','high']],
                cap_seconds=90,Seed=0,Threads=1))
        records.append(dict(role=role,parent=parent,cases=cases,selected_pivot=chosen['pivot'],
            selected_pivot_kind=chosen['pivot_kind'],selection='maximum qualified conditional cover; lower m breaks ties'))
    write(OUT/'child_comparison.json',dict(UTC=utc(),roles=records))
    write(OUT/'projection_plan.json',dict(UTC=utc(),positions=positions,
        diagnostic_only=True,shared_beta_sources=True,online_rule_not_yet_frozen=True))
    print(json.dumps([dict(role=r['role'],chosen=r['selected_pivot'],
        cases=[{k:c[k] for k in ['pivot','pivot_kind','plain_raw_cover','conditional_raw_cover']} for c in r['cases']])
        for r in records],indent=2))

def run_projections():
    for spec in read(OUT/'projection_plan.json')['positions']:
        assert metered(spec['label'],'diagnostic',[LP_PYTHON,ROOT/'scripts/round141_lp.py','one',json.dumps(spec)],110,120)==0

if __name__=='__main__':
    if sys.argv[1]=='one':solve(json.loads(sys.argv[2]))
    elif sys.argv[1]=='run_children':run_children(sys.argv[2] if len(sys.argv)>2 else '')
    elif sys.argv[1]=='select_projections':select_projections()
    elif sys.argv[1]=='run_projections':run_projections()
