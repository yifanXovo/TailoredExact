"""Three saved base-D product LP increments and one redundant scalar control."""
import gzip
from collections import Counter
from round143_lp import semantics,residual
from round145_lp import add_rows,save_gz
from round149_math import compiled
from round149_common import *


def matrix_scope(model,block):
    spec=block['scope'];vs={v.VarName:v for v in model.getVars()}
    assert model.ModelSense==1 and model.ObjCon==0 and vs['G'].Obj==1
    objective={v.VarName:v.Obj for v in vs.values() if v.Obj}
    assert all(k=='G' or (k.startswith('e_') and v>=0) for k,v in objective.items())
    signatures=Counter();cutoffs=[]
    for con in model.getConstrs():
        row=model.getRow(con);terms={row.getVar(k).VarName:row.getCoeff(k) for k in range(row.size())}
        signatures[(tuple(sorted(terms.items())),con.Sense,con.RHS)]+=1
        if terms==objective and con.Sense=='<':cutoffs.append(con.RHS)
    assert cutoffs,'original objective cutoff missing'
    def has(terms,sense,rhs):
        assert signatures[(tuple(sorted(terms.items())),sense,rhs)]>=1,(terms,sense,rhs)
    stations=[];total={}
    for key,ys in spec['supports'].items():
        i=int(key);c=spec['c_binary64'][key];lo,hi=vs[f'Y_{i}'].LB,vs[f'Y_{i}'].UB
        assert (lo,hi)==(min(ys),max(ys))
        has({f'r_{i}':1.,f'Y_{i}':-c},'=',0.)
        has({f'e_{i}':1.,f'r_{i}':-1.},'>',-1.)
        has({f'e_{i}':1.,f'r_{i}':1.},'>',1.)
        has({f'state_{i}_{y}':1. for y in ys},'=',1.)
        has({f'state_g_{i}_{y}':1. for y in ys}|{'G':-1.},'=',0.)
        for y in ys:
            assert vs[f'state_{i}_{y}'].LB>=0 and vs[f'state_{i}_{y}'].UB<=1
            has({f'state_g_{i}_{y}':1.,f'state_{i}_{y}':-vs['G'].UB},'<',0.)
        stations.append(dict(i=i,lo=int(lo),hi=int(hi),c=c,omega=vs[f'e_{i}'].Obj,support=ys))
        total[f'Y_{i}']=1.
    has(total,'<',spec['B']);has(total,'>',spec['Bminus'])
    return dict(Bminus=spec['Bminus'],B=spec['B'],gamma_U=vs['G'].UB,
        gamma_L=vs['G'].LB,cutoff=min(cutoffs),stations=stations,
        actual_weighted_objective_ratio_penalty_resource_onehot_product_sum_verified=True)


def solve(role,mode):
    configure();assert mode in ('PF','BOUND')
    folder=ROOT/'results/unified_exact_round146/LP'/f'{role}_base_GD'
    old=read(folder/'result.json');source=folder/'model.mps'
    assert sha(source)==old['model_SHA']
    block=read(folder/'compiled_rows.json')
    point=json.loads(gzip.decompress((folder/'solution.json.gz').read_bytes()))
    target=OUT/'LP'/f'{role}_{mode}';target.mkdir(parents=True,exist_ok=False)
    start=time.perf_counter()
    from round100_gurobi_runtime import gp,binding
    identity=binding();assert identity['sha256']==DLL_SHA
    kernel=ctypes.WinDLL('kernel32',use_last_error=True);kernel.GetCurrentProcess.restype=ctypes.c_void_p
    kernel.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t]
    assert kernel.SetProcessAffinityMask(kernel.GetCurrentProcess(),4)
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Threads',1);env.setParam('Seed',0);env.start()
        with gp.read(str(source),env=env) as model:
            assert not model.IsMIP
            before=semantics(model);names={v.VarName for v in model.getVars()};oldrows={c.ConstrName for c in model.getConstrs()}
            baseline=residual(model,point)
            assert max(baseline['constraints'],baseline['bounds'])<=1e-6
            assert abs(baseline['objective']-old['L'])<1e-8
            scope=matrix_scope(model,block)
            floor=compiled(scope,target/'arithmetic.json')
            rows=floor['rows'] if mode=='PF' else [dict(name='r149_BOUND_ONLY',sense='<',rhs=floor['beta'],terms={'G':1.})]
            counts=dict(rows=model.NumConstrs,columns=model.NumVars,nonzeros=model.NumNZs)
            old_violations=[dict(name=r['name'],violation=math.fsum(v*point[k] for k,v in r['terms'].items())-r['rhs']) for r in rows]
            write(target/'construction.json',dict(scope=scope,rows=rows,old_point_max_violation=max(r['violation'] for r in old_violations),
                original_scalar_slack=floor['beta']-point['G'],new_columns=0,source_solves=0,baseline_Optimize_new=0))
            add_rows(model,rows,gp);assert semantics(model,names,oldrows)==before
            model.write(str(target/'model.mps'))
        read_tick=time.perf_counter()
        with gp.read(str(target/'model.mps'),env=env) as model:
            assert semantics(model,names,oldrows)==before
            for r in rows:
                con=model.getConstrByName(r['name']);row=model.getRow(con)
                assert con.Sense==r['sense'] and con.RHS==r['rhs']
                assert {row.getVar(i).VarName:row.getCoeff(i) for i in range(row.size())}==r['terms']
            readback_seconds=time.perf_counter()-read_tick
            model.Params.Seed=0;model.Params.Threads=1;model.Params.TimeLimit=120
            model.Params.FeasibilityTol=1e-6;model.Params.OptimalityTol=1e-6
            model.Params.OutputFlag=1;model.Params.LogToConsole=0;model.Params.LogFile=str(target/'native.log')
            construction=time.perf_counter()-start
            write(target/'call.json',dict(UTC=utc(),state='BEFORE_OPTIMIZE',Seed=0,Threads=1,
                model_SHA=sha(target/'model.mps'),source_model_SHA=sha(source),Native=identity,LP_Optimize=1))
            tick=time.perf_counter();model.optimize();elapsed=time.perf_counter()-tick
            write(target/'return.json',dict(UTC=utc(),Status=model.Status,Runtime=model.Runtime,Work=model.Work,optimize_wall=elapsed))
            assert model.Status==gp.GRB.OPTIMAL
            newpoint={v.VarName:v.X for v in model.getVars()};save_gz(target/'solution.json.gz',newpoint)
            quality={k:model.getAttr(k) for k in ['ConstrVio','BoundVio','DualVio','ConstrResidual','DualResidual','ComplVio']}
            check=residual(model,newpoint)
            assert max(quality.values())<=1e-6 and max(check['constraints'],check['bounds'])<=1e-6
            dual=model.ObjCon+math.fsum(con.Pi*con.RHS for con in model.getConstrs());infinite=[]
            for v in model.getVars():
                bound=v.LB if v.RC>=0 else v.UB
                if abs(bound)<gp.GRB.INFINITY:dual+=v.RC*bound
                else:infinite.append(abs(v.RC))
            if mode=='BOUND':assert abs(model.ObjVal-old['L'])<=1e-6
            assert model.ObjVal>=old['L']-1e-6
            result=dict(role=role,carrier='base-D',mode=mode,old_L=old['L'],L=model.ObjVal,gain=model.ObjVal-old['L'],
                g=newpoint['G'],weighted_penalty=model.ObjVal-newpoint['G'],penalty_lower=floor['penalty_lower'],beta=floor['beta'],
                qualified_LP_bound=model.ObjVal,qualified=True,exact_rational_optimality_certificate=False,
                numerical_dual_objective=dual,numerical_primal_dual_gap=model.ObjVal-dual,
                infinite_bound_adverse_reduced_cost=max(infinite or [0.]),quality=quality,residual=check,baseline_residual=baseline,
                before=counts,rows=model.NumConstrs,columns=model.NumVars,nonzeros=model.NumNZs,
                added_rows=len(rows),added_nonzeros=sum(len(r['terms']) for r in rows),
                old_point_max_violation=max(r['violation'] for r in old_violations),old_scalar_slack=floor['beta']-point['G'],
                construction_seconds=construction,readback_seconds=readback_seconds,oracle_seconds=floor['seconds'],
                optimize_wall=elapsed,Runtime=model.Runtime,Work=model.Work,iterations=model.IterCount,
                Seed=0,Threads=1,affinity_mask=4,model_SHA=sha(target/'model.mps'),solution_SHA=sha(target/'solution.json.gz'),
                source_model_SHA=sha(source),source_fixed_science=SCIENCE146,original_semantics_exactly_retained=True,
                actual_Native_row_readback=True,no_variables_fixed_to_old_point=True,LP_Optimize=1,Native=identity,
                helper_SHA={f:sha(ROOT/'scripts'/f) for f in ['round149_math.py','round149_lp.py','round149_common.py']})
            write(target/'result.json',result)
    print(json.dumps({k:result[k] for k in ['role','mode','old_L','L','gain','penalty_lower','beta','Runtime']}),flush=True)


def run():
    configure()
    for role,mode in [(r,'PF') for r in ROLES]+[('K-35-U','BOUND')]:
        assert metered(f'LP_{role}_{mode}','diagnostic',[LP_PYTHON,'-B',__file__,'solve',role,mode],180,240)==0


if __name__=='__main__':
    if sys.argv[1]=='solve':solve(*sys.argv[2:])
    else:run()
