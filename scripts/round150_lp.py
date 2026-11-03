"""Append CPF to three saved PF matrices, review, then one new LP per domain."""
import gzip
from collections import Counter
from round143_lp import semantics, residual
from round145_lp import add_rows, save_gz
from round150_math import conditional
from round150_common import *


def affinity():
    kernel = ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.GetCurrentProcess.restype = ctypes.c_void_p
    kernel.SetProcessAffinityMask.argtypes = [ctypes.c_void_p,ctypes.c_size_t]
    assert kernel.SetProcessAffinityMask(kernel.GetCurrentProcess(),4)


def scope_contract(model, arithmetic):
    scope = arithmetic['scope']
    vs = {v.VarName:v for v in model.getVars()}
    objective = {v.VarName:v.Obj for v in vs.values() if v.Obj}
    assert model.ModelSense==1 and model.ObjCon==0 and vs['G'].Obj==1
    assert all(k=='G' or (k.startswith('e_') and v>=0) for k,v in objective.items())
    assert not model.IsMIP and all(v.VType=='C' for v in vs.values())
    signatures = Counter()
    for con in model.getConstrs():
        e = model.getRow(con)
        terms = tuple(sorted((e.getVar(i).VarName,e.getCoeff(i)) for i in range(e.size())))
        signatures[(terms,con.Sense,con.RHS)] += 1
    def has(terms,sense,rhs):
        assert signatures[(tuple(sorted(terms.items())),sense,rhs)]>=1,(terms,sense,rhs)
    has(objective,'<',scope['cutoff'])
    assert (vs['G'].LB,vs['G'].UB)==(scope['gamma_L'],scope['gamma_U'])
    total = {}
    for s in scope['stations']:
        i, ys = s['i'], s['support']
        assert vs[f'e_{i}'].Obj==s['omega']
        assert (vs[f'Y_{i}'].LB,vs[f'Y_{i}'].UB)==(s['lo'],s['hi'])==(min(ys),max(ys))
        has({f'r_{i}':1.,f'Y_{i}':-s['c']},'=',0.)
        has({f'e_{i}':1.,f'r_{i}':-1.},'>',-1.)
        has({f'e_{i}':1.,f'r_{i}':1.},'>',1.)
        has({f'state_{i}_{y}':1. for y in ys},'=',1.)
        has({f'state_g_{i}_{y}':1. for y in ys}|{'G':-1.},'=',0.)
        for y in ys:
            assert vs[f'state_{i}_{y}'].LB>=0 and vs[f'state_{i}_{y}'].UB<=1
            has({f'state_g_{i}_{y}':1.,f'state_{i}_{y}':-arithmetic['beta']},'<',0.)
        total[f'Y_{i}'] = 1.
    has(total,'<',scope['B'])
    has(total,'>',scope['Bminus'])


def readback(model,rows):
    for r in rows:
        con = model.getConstrByName(r['name'])
        e = model.getRow(con)
        assert con.Sense==r['sense'] and con.RHS==r['rhs']
        assert {e.getVar(i).VarName:e.getCoeff(i) for i in range(e.size())}==r['terms']


def prepare():
    configure()
    from round100_gurobi_runtime import gp,binding
    identity = binding()
    assert identity['sha256']==DLL_SHA
    affinity()
    index = []
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0)
        env.setParam('Threads',1)
        env.setParam('Seed',0)
        env.start()
        for role in ROLES:
            start = time.perf_counter()
            folder = ROOT/'results/unified_exact_round149/LP'/f'{role}_PF'
            source = folder/'model.mps'
            old = read(folder/'result.json')
            assert sha(source)==old['model_SHA']
            assert sha(folder/'solution.json.gz')==old['solution_SHA']
            target = OUT/'LP'/f'{role}_CPF'
            target.mkdir(parents=True,exist_ok=False)
            point = json.loads(gzip.decompress((folder/'solution.json.gz').read_bytes()))
            ar = read(folder/'arithmetic.json')
            block = conditional(ar)
            write(target/'arithmetic.json',block)
            with gp.read(str(source),env=env) as model:
                before = semantics(model)
                names = {v.VarName for v in model.getVars()}
                oldrows = {c.ConstrName for c in model.getConstrs()}
                assert len(oldrows)==model.NumConstrs
                baseline = residual(model,point)
                assert max(baseline['constraints'],baseline['bounds'])<=1e-6
                assert abs(baseline['objective']-old['L'])<1e-8
                scope_contract(model,ar)
                counts = dict(rows=model.NumConstrs,columns=model.NumVars,nonzeros=model.NumNZs)
                violations = [dict(name=r['name'],violation=math.fsum(a*point[k] for k,a in r['terms'].items())) for r in block['rows']]
                add_rows(model,block['rows'],gp)
                assert semantics(model,names,oldrows)==before
                model.write(str(target/'model.mps'))
            read_tick = time.perf_counter()
            with gp.read(str(target/'model.mps'),env=env) as model:
                assert semantics(model,names,oldrows)==before
                assert model.NumVars==counts['columns']
                assert model.NumConstrs==counts['rows']+block['actual_rows']
                assert model.NumNZs==counts['nonzeros']+block['actual_nonzeros']
                readback(model,block['rows'])
                scope_contract(model,ar)
                read_seconds = time.perf_counter()-read_tick
            construction = dict(role=role,source_fixed_science=SCIENCE149,
                source_model=source.relative_to(ROOT).as_posix(),source_model_SHA=sha(source),
                source_result_SHA=sha(folder/'result.json'),source_arithmetic_SHA=sha(folder/'arithmetic.json'),
                source_solution_SHA=sha(folder/'solution.json.gz'),model_SHA=sha(target/'model.mps'),
                arithmetic_SHA=sha(target/'arithmetic.json'),before=counts,baseline_residual=baseline,
                old_D_L=old['old_L'],old_PF_L=old['L'],PF_minus_D=old['gain'],
                old_PF_quality=old['quality'],old_PF_numerical_dual=old['numerical_dual_objective'],
                old_PF_numerical_primal_dual_gap=old['numerical_primal_dual_gap'],
                actual_added_rows=block['actual_rows'],actual_added_nonzeros=block['actual_nonzeros'],
                old_point_violation_count=sum(v['violation']>1e-8 for v in violations),
                old_point_max_violation=max([v['violation'] for v in violations] or [0.]),
                old_point_violations=violations,construction_seconds=time.perf_counter()-start,
                arithmetic_seconds=block['seconds'],readback_seconds=read_seconds,
                old_semantics_exactly_retained=True,all_variables_free=True,baseline_Optimize_new=0,
                Native=identity,LP_Optimize=0,Seed=0,Threads=1,affinity_mask=4)
            write(target/'construction.json',construction)
            index.append(dict(role=role,model_SHA=sha(target/'model.mps'),
                arithmetic_SHA=sha(target/'arithmetic.json'),construction_SHA=sha(target/'construction.json')))
    write(OUT/'CPF_frozen.json',dict(UTC=utc(),domains=index,LP_cap_seconds=120,
        Seed=0,Threads=1,baseline_Optimize_new=0,extra_quality_Optimize_limit=1,
        math_SHA=sha(ROOT/'scripts/round150_math.py'),lp_SHA=sha(__file__),
        method='single fixed actual R149 binary64 resource dual; prefix/suffix Fraction; one propagation'))
    print(json.dumps(dict(prepared=len(index),Optimize=0)))


def solve(role):
    configure()
    gate = read(OUT/'review/CPF_admission.json')
    assert gate['decision']=='ACCEPT' and gate['independent_nonimplementer_review']
    assert gate['CPF_frozen_SHA']==sha(OUT/'CPF_frozen.json')
    frozen = read(OUT/'CPF_frozen.json')
    assert frozen['math_SHA']==sha(ROOT/'scripts/round150_math.py') and frozen['lp_SHA']==sha(__file__)
    item = next(v for v in frozen['domains'] if v['role']==role)
    target = OUT/'LP'/f'{role}_CPF'
    assert sha(target/'model.mps')==item['model_SHA']
    assert sha(target/'arithmetic.json')==item['arithmetic_SHA']
    assert sha(target/'construction.json')==item['construction_SHA']
    assert not (target/'call.json').exists(), 'Never automatically repeat Optimize'
    from round100_gurobi_runtime import gp,binding
    identity = binding()
    assert identity['sha256']==DLL_SHA
    affinity()
    old = read(target/'construction.json')
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0)
        env.setParam('Threads',1)
        env.setParam('Seed',0)
        env.start()
        with gp.read(str(target/'model.mps'),env=env) as model:
            assert not model.IsMIP
            model.Params.TimeLimit=120
            model.Params.FeasibilityTol=1e-6
            model.Params.OptimalityTol=1e-6
            model.Params.OutputFlag=1
            model.Params.LogToConsole=0
            model.Params.LogFile=str(target/'native.log')
            write(target/'call.json',dict(UTC=utc(),state='BEFORE_OPTIMIZE',Seed=0,Threads=1,
                model_SHA=item['model_SHA'],Native=identity,LP_Optimize=1,cap_seconds=120))
            tick = time.perf_counter()
            model.optimize()
            elapsed = time.perf_counter()-tick
            write(target/'return.json',dict(UTC=utc(),Status=model.Status,Runtime=model.Runtime,
                Work=model.Work,optimize_wall=elapsed,LP_Optimize=1))
            result = dict(role=role,Status=model.Status,qualified=False,LP_Optimize=1,
                model_SHA=item['model_SHA'],old_D_L=old['old_D_L'],old_PF_L=old['old_PF_L'],
                PF_minus_D=old['PF_minus_D'],old_PF_quality=old['old_PF_quality'],
                old_PF_numerical_dual=old['old_PF_numerical_dual'],
                old_PF_numerical_primal_dual_gap=old['old_PF_numerical_primal_dual_gap'],
                actual_added_rows=old['actual_added_rows'],actual_added_nonzeros=old['actual_added_nonzeros'],
                construction_seconds=old['construction_seconds'],readback_seconds=old['readback_seconds'],
                optimize_wall=elapsed,Runtime=model.Runtime,Work=model.Work,iterations=model.IterCount,
                Seed=0,Threads=1,affinity_mask=4,Native=identity,baseline_Optimize_new=0,
                exact_rational_optimality_certificate=False,no_variables_fixed_to_old_point=True,
                original_semantics_exactly_retained=True,all_old_PF_rows_retained=True)
            if model.SolCount:
                point = {v.VarName:v.X for v in model.getVars()}
                save_gz(target/'solution.json.gz',point)
                quality = {k:model.getAttr(k) for k in ['ConstrVio','BoundVio','DualVio','ConstrResidual','DualResidual','ComplVio']}
                check = residual(model,point)
                dual_rows = {c.ConstrName:c.Pi for c in model.getConstrs()}
                dual_rc = {v.VarName:v.RC for v in model.getVars()}
                save_gz(target/'dual.json.gz',dict(Pi=dual_rows,RC=dual_rc))
                dual = model.ObjCon+math.fsum(c.Pi*c.RHS for c in model.getConstrs())
                bound_terms, infinite = [], []
                for v in model.getVars():
                    bound = v.LB if v.RC>=0 else v.UB
                    if abs(bound)<gp.GRB.INFINITY:
                        bound_terms.append(v.RC*bound)
                    else:
                        infinite.append(abs(v.RC))
                dual += math.fsum(bound_terms)
                result.update(L=model.ObjVal,CPF_minus_PF=model.ObjVal-old['old_PF_L'],
                    g=point['G'],weighted_penalty=model.ObjVal-point['G'],quality=quality,residual=check,
                    numerical_dual_objective=dual,numerical_primal_dual_gap=model.ObjVal-dual,
                    infinite_bound_adverse_reduced_cost=max(infinite or [0.]),
                    qualified=model.Status==gp.GRB.OPTIMAL and max(quality.values())<=1e-6 and
                        max(check['constraints'],check['bounds'])<=1e-6,
                    solution_SHA=sha(target/'solution.json.gz'),dual_SHA=sha(target/'dual.json.gz'))
            write(target/'result.json',result)
    print(json.dumps({k:v for k,v in result.items() if k in ['role','Status','L','CPF_minus_PF','qualified','quality','numerical_primal_dual_gap']}),flush=True)


def run():
    configure()
    for role in ROLES:
        assert metered(f'LP_{role}_CPF','diagnostic',[LP_PYTHON,'-B',__file__,'solve',role],180,240)==0


if __name__=='__main__':
    if sys.argv[1]=='solve': solve(sys.argv[2])
    elif sys.argv[1]=='run': run()
    elif sys.argv[1]=='prepare': prepare()
    elif sys.argv[1]=='meter_prepare':
        assert metered('CPF_prepare','diagnostic',[LP_PYTHON,'-B',__file__,'prepare'],180,240)==0
