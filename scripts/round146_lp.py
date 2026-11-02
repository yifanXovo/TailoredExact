"""Five matched continuous GD tests, reusing sealed baseline optima/points."""
import gzip,collections
import round108_reader as parser
from round143_qualify import actual_spec
from round143_lp import semantics,residual
from round145_lp import add_rows,save_gz
from round146_math import compiled,activity
from round146_common import *
configure()
def domain(role,carrier):
    inherited=ROOT/'results/unified_exact_round143/inherited/roots'/role
    scope=read(inherited/'scope.json')
    if carrier=='joint':
        folder=ROOT/'results/unified_exact_round145/LP'/f'{role}_joint'
        matrix=folder/'model.mps';old=read(folder/'result.json');point=folder/'solution.json.gz'
        assert sha(matrix)==old['model_SHA'];spec=read(folder/'scope.json')['RN']
    else:
        assert carrier in ('base','stock');folder=inherited/carrier;old=read(folder/'result.json');point=folder/'solution.json.gz'
        assert sha(point)==old['solution_SHA']
        matrix=inherited/'inherited/original.lp'
        if carrier=='stock':matrix=next(p for p in [inherited/'stock_export_exact_cutoff/original.lp',inherited/'stock_export/original.lp'] if p.exists())
        spec=actual_spec(parser.lp_model(matrix),scope['Bminus'],scope['B'])
    return dict(matrix=matrix,old=old,point=json.loads(gzip.decompress(point.read_bytes())),spec=spec,
        provenance=dict(result=str((folder/'result.json').relative_to(ROOT)),result_SHA=sha(folder/'result.json'),
            solution=str(point.relative_to(ROOT)),solution_SHA=sha(point),matrix=str(matrix.relative_to(ROOT)),matrix_SHA=sha(matrix),
            physical_input_SHA=scope['panel']['input_sha256'],baseline_Optimize_new=0))
def solve(role,carrier):
    configure()
    from round100_gurobi_runtime import gp,binding
    assert binding()['sha256']==DLL_SHA
    kernel=ctypes.WinDLL('kernel32',use_last_error=True);kernel.GetCurrentProcess.restype=ctypes.c_void_p
    kernel.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t];assert kernel.SetProcessAffinityMask(kernel.GetCurrentProcess(),4)
    d=domain(role,carrier);target=OUT/'LP'/f'{role}_{carrier}_GD';target.mkdir(parents=True,exist_ok=False)
    block=compiled(d['spec'],target/'compiled_rows.json');rows=block['rows'];assert len(rows)<=2
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Seed',0);env.setParam('Threads',1);env.start()
        with gp.read(str(d['matrix']),env=env) as model:
            for v in model.getVars():v.VType=gp.GRB.CONTINUOUS
            model.update();before=semantics(model);names={v.VarName for v in model.getVars()};oldrows={c.ConstrName for c in model.getConstrs()}
            baseline_check=residual(model,d['point']);assert max(baseline_check['constraints'],baseline_check['bounds'])<=1e-6 and abs(baseline_check['objective']-d['old']['L'])<1e-8
            if carrier!='joint':assert all(getattr(model,k)==d['old']['after'][v] for k,v in [('NumVars','columns'),('NumConstrs','rows'),('NumNZs','nonzeros')])
            counts=dict(rows=model.NumConstrs,columns=model.NumVars,nonzeros=model.NumNZs)
            add_rows(model,rows,gp);assert semantics(model,names,oldrows)==before;model.write(str(target/'model.mps'))
        with gp.read(str(target/'model.mps'),env=env) as model:
            assert semantics(model,names,oldrows)==before
            for row in rows:
                c=model.getConstrByName(row['name']);e=model.getRow(c)
                assert c.Sense==row['sense'] and c.RHS==row['rhs'] and {e.getVar(i).VarName:e.getCoeff(i) for i in range(e.size())}==row['terms']
            model.Params.Threads=1;model.Params.Seed=0;model.Params.TimeLimit=120
            model.Params.OutputFlag=1;model.Params.LogToConsole=0;model.Params.LogFile=str(target/'native.log')
            write(target/'call.json',dict(UTC=utc(),state='BEFORE_OPTIMIZE',Seed=0,Threads=1,model_SHA=sha(target/'model.mps')))
            tick=time.perf_counter();model.optimize();elapsed=time.perf_counter()-tick
            write(target/'return.json',dict(UTC=utc(),Status=model.Status,Runtime=model.Runtime,Work=model.Work,optimize_wall=elapsed));assert model.Status==gp.GRB.OPTIMAL
            point={v.VarName:v.X for v in model.getVars()};quality={k:model.getAttr(k) for k in ['ConstrVio','BoundVio','DualVio','ConstrResidual','DualResidual','ComplVio']};check=residual(model,point)
            assert max(quality.values())<=1e-6 and max(check['constraints'],check['bounds'])<=1e-6
            save_gz(target/'solution.json.gz',point)
            result=dict(role=role,carrier=carrier,variant=carrier+'+GD-state',L=model.ObjVal,g=point['G'],weighted_penalty=model.ObjVal-point['G'],
                old_L=d['old']['L'],old_g=d['point']['G'],old_weighted_penalty=d['old']['L']-d['point']['G'],gain=model.ObjVal-d['old']['L'],
                rows=model.NumConstrs,columns=model.NumVars,nonzeros=model.NumNZs,before=counts,added_rows=len(rows),added_nonzeros=sum(len(r['terms']) for r in rows),
                coefficient_generation_seconds=block['seconds'],Runtime=model.Runtime,Work=model.Work,iterations=model.IterCount,optimize_wall=elapsed,
                quality=quality,residual=check,baseline_residual=baseline_check,baseline_reused=d['provenance'],
                activities=activity(rows,point),old_activities=activity(rows,d['point']),Seed=0,Threads=1,affinity_mask=4,
                model_SHA=sha(target/'model.mps'),row_header_SHA=block['header_SHA'],Native=binding(),qualified=True,
                complete_objective_constants_old_matrix_support_bounds_cutoff_retained=True,actual_Native_GD_readback=True,LP_Optimize=1)
            write(target/'result.json',result)
    print(json.dumps({k:result[k] for k in ['role','variant','old_L','L','gain','coefficient_generation_seconds','Runtime','qualified']}),flush=True)
def run():
    configure()
    for role,carrier in [('K-20-S','base'),('K-20-S','joint'),('K-35-U','base'),('R-X20-S-T1','base'),('K-20-S','stock')]:
        assert metered('LP_'+role+'_'+carrier,'diagnostic',[LP_PYTHON,'-B',__file__,'solve',role,carrier],180,240)==0
if __name__=='__main__':
    if sys.argv[1]=='solve':solve(*sys.argv[2:])
    else:run()
