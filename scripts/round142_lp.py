"""Finite count-source CP comparison on six hash-bound R141 continuous LPs.

Only this diagnostic entry loads Native. No diagnostic floor is imported by
the complete method. Range-only equality uses the saved same-objective point.
"""
from round142_common import *
from round142_math import OLD, F, ranges, range_rows, product_rows, residual, count_diagnostic
import gzip

def floor(value, cutoff):
    return max(0.,math.nextafter(min(value,cutoff)-1e-7,-math.inf))

def audit_row(model, r):
    c=model.getConstrByName(r['name']);assert c is not None,r['name']
    e=model.getRow(c);actual={e.getVar(i).VarName:e.getCoeff(i) for i in range(e.size())}
    assert actual=={k:float(v) for k,v in r['terms'].items() if v},r['name']
    assert c.Sense==r['sense'] and c.RHS==r['rhs'],r['name']

def matrix_residual(model,point):
    high=0.
    for c in model.getConstrs():
        e=model.getRow(c);lhs=math.fsum(e.getCoeff(i)*point[e.getVar(i).VarName] for i in range(e.size()))
        violation=max(0.,c.RHS-lhs) if c.Sense=='>' else max(0.,lhs-c.RHS) if c.Sense=='<' else abs(lhs-c.RHS)
        high=max(high,violation)
    bounds=max([max(v.LB-point[v.VarName],point[v.VarName]-v.UB,0.) for v in model.getVars()] or [0.])
    return dict(constraints=high,bounds=bounds,objective=model.ObjCon+math.fsum(v.Obj*point[v.VarName] for v in model.getVars()))

def solve(spec,mode):
    assert mode in ('selected','all')
    ctypes.windll.kernel32.SetProcessAffinityMask(ctypes.windll.kernel32.GetCurrentProcess(),4)
    from round100_gurobi_runtime import gp,binding
    identity=binding();assert identity['sha256']==DLL_SHA
    target=OUT/'LP'/f'{spec["label"]}_{mode}';target.mkdir(parents=True,exist_ok=False)
    tick=time.perf_counter();add=read(OLD/'domains'/spec['role']/'additions.json')
    intervals=ranges(add,spec,mode);linear=range_rows(add,intervals,spec)
    products=product_rows(add,intervals,spec['alpha'],spec['beta'])
    assert sha(spec['source_model'])==spec['source_SHA'] and sha(spec['source_result'])==spec['source_result_SHA']
    assert sha(spec['old_solution'])==spec['old_solution_SHA']
    old=read(spec['source_result']);point=json.loads(gzip.decompress(Path(spec['old_solution']).read_bytes()))
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        model=gp.read(spec['source_model'],env=env)
        assert all(v.VType==gp.GRB.CONTINUOUS for v in model.getVars())
        assert model.Fingerprint==old['fingerprint']
        vs={v.VarName:v for v in model.getVars()};assert set(vs)==set(point)
        before=dict(rows=model.NumConstrs,columns=model.NumVars,nonzeros=model.NumNZs)
        common_objective={v.VarName:v.Obj for v in model.getVars()};common_constant=model.ObjCon
        baseline=matrix_residual(model,point)
        assert baseline['constraints']<=1e-6 and baseline['bounds']<=1e-6
        assert abs(baseline['objective']-spec['old_L'])<=1e-8
        range_v=max(0.,residual(linear,point));cp_v=max(0.,residual(products,point))
        control=dict(old_L=spec['old_L'],old_beta=spec['old_beta'],original_model_SHA=spec['source_SHA'],
            original_solution_SHA=spec['old_solution_SHA'],full_matrix_saved_point=baseline,
            new_range_max_violation=range_v,same_objective_witness=range_v<=1e-6,
            range_only_Optimize=0,scope='Inherited qualified numerical LP optimum and complete saved primal; not a rational optimum certificate')
        write(target/'range_control.json',control)
        for r in [*linear,*products]:
            model.addConstr(gp.quicksum(v*vs[k] for k,v in r['terms'].items())>=r['rhs'],name=r['name'])
        model.update()
        canonical=target/'model.mps';model.write(str(canonical))
        fingerprint=model.Fingerprint
        after=dict(rows=model.NumConstrs,columns=model.NumVars,nonzeros=model.NumNZs)
        model.dispose();model=gp.read(str(canonical),env=env)
        assert model.Fingerprint==fingerprint
        assert common_constant==model.ObjCon and common_objective=={v.VarName:v.Obj for v in model.getVars()}
        assert all(v.VType==gp.GRB.CONTINUOUS for v in model.getVars())
        for r in [*linear,*products]:audit_row(model,r)
        model.Params.Threads=1;model.Params.Seed=0;model.Params.Presolve=-1
        model.Params.TimeLimit=spec.get('cap_seconds',90)
        model.Params.FeasibilityTol=1e-6;model.Params.OptimalityTol=1e-6
        model.Params.LogFile=str(target/'native.log');model.Params.LogToConsole=0;model.Params.OutputFlag=1
        write(target/'scope.json',dict(spec=spec,mode=mode,canonical_SHA=sha(canonical),audits=linear+products,
            original_full_matrix_retained=True,complete_objective=common_objective,ObjCon=common_constant,
            original_cutoff_support_g_retained=True,range_control=control,old_point_CP_violation=cp_v,
            condition_sources_only=True,no_global_or_MIP_CP=True,expected_rows_all_read_back=True))
        built=time.perf_counter();model.optimize();done=time.perf_counter()
        result=dict(spec=spec,mode=mode,status=model.Status,canonical_SHA=sha(canonical),fingerprint=model.Fingerprint,
            before=before,after=after,added_range_rows=len(linear),added_CP_rows=len(products),
            construction_seconds=built-tick,optimize_wall_seconds=done-built,Runtime=model.Runtime,Work=model.Work,
            native_identity=identity,Seed=model.Params.Seed,Threads=model.Params.Threads,
            FeasibilityTol=model.Params.FeasibilityTol,OptimalityTol=model.Params.OptimalityTol,
            LP_Optimize=1,MIP_Optimize=0,qualified=False,L=None,beta=None,range_control=control,
            writer_SHA=sha(__file__),math_SHA=sha(ROOT/'scripts/round142_math.py'),
            source_rev=git('rev-parse','HEAD').decode().strip(),old_point_CP_violation=cp_v)
        if model.Status==gp.GRB.OPTIMAL:
            point={v.VarName:v.X for v in model.getVars()}
            with gzip.open(target/'solution.json.gz','wt',encoding='utf-8') as stream:json.dump(point,stream,separators=(',',':'))
            quality={k:model.getAttr(k) for k in ['ConstrVio','BoundVio','DualVio','ConstrResidual','DualResidual','ComplVio']}
            qualified=all(v<=1e-6 for v in quality.values())
            selected=ranges(add,spec,'selected')[0]
            result.update(L=model.ObjVal,beta=floor(model.ObjVal,spec['cutoff']) if qualified else None,
                qualified=qualified,quality=quality,solution_SHA=sha(target/'solution.json.gz'),
                diagnostic=count_diagnostic(add,selected,point,spec['alpha'],spec['beta']),
                CP_max_violation=max(0.,residual(products,point)),range_max_violation=max(0.,residual(linear,point)),
                difference=model.ObjVal-spec['old_L'])
        write(target/'result.json',result);model.dispose()
    print(json.dumps({k:result.get(k) for k in ['mode','status','qualified','L','beta','difference','construction_seconds','optimize_wall_seconds']}),flush=True)

def run(mode):
    assert mode in ('selected','all')
    for spec in read(OUT/'LP_plan.json')['positions']:
        label=spec['label']+'_'+mode
        if (OUT/'LP'/label/'result.json').exists():continue
        assert metered(label,'diagnostic',[LP_PYTHON,ROOT/'scripts/round142_lp.py','one',json.dumps(spec),mode],120,180)==0
    summary=[]
    positions=read(OUT/'LP_plan.json')['positions']
    for role in dict.fromkeys(p['role'] for p in positions):
        sides=[read(OUT/'LP'/(p['label']+'_'+mode)/'result.json') for p in positions if p['role']==role]
        assert len(sides)==2 and all(s['qualified'] for s in sides)
        summary.append(dict(role=role,old_cover=min(s['spec']['old_L'] for s in sides),
            new_cover=min(s['L'] for s in sides),cover_gain=min(s['L'] for s in sides)-min(s['spec']['old_L'] for s in sides),
            old_floor=min(s['spec']['old_beta'] for s in sides),new_floor=min(s['beta'] for s in sides),
            sides=[dict(side=s['spec']['side'],old_L=s['spec']['old_L'],L=s['L'],gain=s['difference']) for s in sides]))
    write(OUT/f'LP_{mode}_summary.json',dict(mode=mode,roles=summary,budget=budget()))
    print(json.dumps(summary,indent=2))

if __name__=='__main__':
    if sys.argv[1]=='one':solve(json.loads(sys.argv[2]),sys.argv[3])
    elif sys.argv[1]=='run':run(sys.argv[2])
