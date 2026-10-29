"""Finite same-domain TC2 reoptimization; every solve is explicit Seed0/one thread."""
from round140_common import *
from round140_math import evaluate
import gzip
LP_PYTHON=Path('E:/codes/ExactEBRP/build/research/round88-ot/venv/Scripts/python.exe')

def solve(position,suffix=''):
    ctypes.windll.kernel32.SetProcessAffinityMask(ctypes.windll.kernel32.GetCurrentProcess(),4)
    from round100_gurobi_runtime import gp,binding
    plan=read(OUT/'LP_plan.json');a=plan['positions'][position-1];role=a['role'];variant=a['variant']
    scope=read(OUT/'roots'/role/'scope.json');add=read(OUT/'roots'/role/'additions.json');n=scope['panel']['V']
    target=OUT/'LP'/f'{position:02}_{role}_{variant}{suffix}';target.mkdir(parents=True,exist_ok=False)
    stock=variant.endswith('_stock') or variant=='stock'
    source=scope['stock_model'] if stock or scope['base_model'] is None else scope['base_model']
    tick=time.perf_counter();identity=binding();assert identity['sha256']==DLL_SHA
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        with gp.read(source,env=env) as m:
            m.Params.Threads=1;m.Params.Seed=0;m.Params.Presolve=-1;m.Params.TimeLimit=120
            m.Params.FeasibilityTol=1e-6;m.Params.OptimalityTol=1e-6
            m.Params.LogFile=str(target/'native.log');m.Params.LogToConsole=0;m.Params.OutputFlag=1
            # RB35 has no inherited BASE model: remove exactly four known stock rows.
            if not stock and scope['base_model'] is None:
                from round138_repair import scaled_rows
                import round108_reader as core, collections
                parsed=core.lp_model(Path(source));wanted=collections.Counter(scaled_rows(n,*parsed['bounds']['G'],scope['Bminus'],scope['B']))
                remove=[]
                for row,constraint in zip(parsed['rows'],m.getConstrs()):
                    if wanted[row]>0:remove.append(constraint);wanted[row]-=1
                assert not +wanted and len(remove)==4;m.remove(remove)
            for v in m.getVars():v.VType=gp.GRB.CONTINUOUS
            m.update();vs={v.VarName:v for v in m.getVars()};before=dict(rows=m.NumConstrs,columns=m.NumVars,nonzeros=m.NumNZs)
            H=gp.quicksum(v for name,v in vs.items() if name.startswith('h_'))
            if variant!='stock':m.addConstr(H>=gp.quicksum(v*vs[k] for k,v in add['TC'].items()),name='r140_TC')
            if variant in ['tc2','tc2_stock']:
                m.addConstr(H>=add['constant']+gp.quicksum(v*vs[k] for k,v in add['TC2'].items()),name='r140_TC2')
            m.update();after=dict(rows=m.NumConstrs,columns=m.NumVars,nonzeros=m.NumNZs)
            assert not m.IsMIP and m.Params.Seed==0 and m.Params.Threads==1
            constructed=time.perf_counter();m.optimize();finished=time.perf_counter()
            assert m.Status==gp.GRB.OPTIMAL,(role,variant,m.Status)
            point={v.VarName:v.X for v in m.getVars()}
            with gzip.open(target/'solution.json.gz','wt',encoding='utf-8') as f:json.dump(point,f,separators=(',',':'))
            result=dict(a,status='NUMERICAL_OPTIMAL_CONTINUOUS_LP',L=m.ObjVal,validated_U=scope['validated_U'],
                signed_gap=scope['validated_U']-m.ObjVal,relative_gap=(scope['validated_U']-m.ObjVal)/abs(scope['validated_U']),
                **evaluate(point,add,n),before=before,after=after,source_SHA=sha(source),solution_SHA=sha(target/'solution.json.gz'),
                construction_seconds=constructed-tick,optimize_wall_seconds=finished-constructed,Runtime=m.Runtime,Work=m.Work,
                quality={k:m.getAttr(k) for k in ['ConstrVio','BoundVio','DualVio','ConstrResidual','DualResidual','ComplVio']},
                native_identity=identity,Seed=m.Params.Seed,Threads=m.Params.Threads,LP_Optimize=1,MIP_Optimize=0,
                plan_SHA=sha(OUT/'LP_plan.json'),writer_source_SHA=sha(ROOT/'scripts/round140_math.py'))
            write(target/'result.json',result)
    print(json.dumps({k:result[k] for k in ['role','variant','L','G','H_sum','J','tau']}),flush=True)

def run():
    for a in read(OUT/'LP_plan.json')['positions']:
        label=f'LP_{a["position"]:02}'
        if (OUT/'fees'/label/'receipt.json').exists():
            assert read(OUT/'fees'/label/'receipt.json')['exit_code']==0;continue
        assert metered(label,'diagnostic',[LP_PYTHON,ROOT/'scripts/round140_lp.py','solve',a['position']],reservation=150,timeout=180)==0

if __name__=='__main__':
    if sys.argv[1]=='solve':solve(int(sys.argv[2]),sys.argv[3] if len(sys.argv)>3 else '')
    else:run()
