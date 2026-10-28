"""Small preregistered same-domain LP comparison; no H, tree or Start sharing."""
from round138_common import *
from round138_setup import stock_rows
from round134_count_bound import count_coefficients, downward
from fractions import Fraction as F
import collections, gzip, re
import round108_reader as core

LP_PYTHON=Path('E:/codes/ExactEBRP/build/research/round88-ot/venv/Scripts/python.exe')
ROLES=['K-35-U','R-X20-S-T1','R-X35-S-T2','K-20-S']

def prepare():
    assert read(OUT/'qualification/matrix_checks.json')['PASS']
    assert (OUT/'review/pre_implementation.md').exists()
    positions=[]
    for role in ROLES:
        scope=read(OUT/'roots'/role/'scope.json');p=scope['panel'];base=OUT/'roots'/role/'inherited/original.lp'
        # Reuse the stored native cutoff, not a recomputed physical U whose
        # final binary64 bit can differ. All these roots have native U=beta<1.
        cutoff=scope['beta']
        suffix='' if cutoff==scope['validated_U'] else '_exact_cutoff'
        dest=OUT/'roots'/role/('stock_export'+suffix)
        label='root_stock_export_'+role+suffix
        args=[BUILD/'Round138Export.exe',ROOT/p['input_path'],p['T_seconds'],scope['alpha'],scope['beta'],
              cutoff,'ms2',dest,p['lambda'],'stock']
        if (OUT/'fees'/label/'receipt.json').exists():
            assert read(OUT/'fees'/label/'receipt.json')['exit_code']==0
            assert read(OUT/'fees'/label/'launch.json')['command']==list(map(str,args))
        else:assert metered(label,'engineering',args,timeout=60)==0
        old=core.lp_model(base);new=core.lp_model(dest/'original.lp')
        assert all(old[k]==new[k] for k in ['order','bounds','types','objective'])
        assert not collections.Counter(old['rows'])-collections.Counter(new['rows'])
        delta=collections.Counter(new['rows'])-collections.Counter(old['rows'])
        assert delta==collections.Counter(stock_rows(p['V'],scope['alpha'],scope['beta'],scope['Bminus'],scope['B']))
        supports=collections.defaultdict(list);ratios={}
        for n in old['bounds']:
            m=re.fullmatch(r'state_(\d+)_(\d+)',n)
            if m:supports[int(m[1])].append(int(m[2]))
        for terms,sense,rhs in old['rows']:
            t=dict(terms)
            if sense=='=' and rhs==0 and len(t)==2:
                for n,c in t.items():
                    m=re.fullmatch(r'r_(\d+)',n)
                    if m and c==1 and f'Y_{m[1]}' in t:ratios[int(m[1])]=-t[f'Y_{m[1]}']
        assert set(supports)==set(ratios)==set(range(1,p['V']+1))
        tc=count_coefficients(supports,{i:F(v) for i,v in ratios.items()},scope['B'])
        coeff={f'state_{i}_{y}':downward(v) for (i,y),v in tc['coefficients'].items() if v}
        # Exact continuous inventory knapsack bound on ratio S, shared by both GS controls.
        minima={i:min(v) for i,v in supports.items()};rem=F(scope['B']-sum(minima.values()))
        upper=sum(F(ratios[i])*v for i,v in minima.items())
        for i in sorted(ratios,key=lambda i:ratios[i],reverse=True):
            amount=min(rem,max(supports[i])-minima[i]);upper+=amount*F(ratios[i]);rem-=amount
        Su=float(upper)
        if F(Su)<upper:Su=math.nextafter(Su,math.inf)
        write(OUT/'roots'/role/'additions.json',dict(TC=coeff,TC_exact={f'state_{i}_{y}':str(v) for (i,y),v in tc['coefficients'].items() if v},
            ratio_coefficients=ratios,GS_S_lower=0.,GS_S_upper=Su,GS_S_upper_exact=str(upper),
            GS_bound_source='Fractional inventory knapsack over same supported Y and physical sum(Y)<=B',
            stock_model=dest.relative_to(ROOT).as_posix()+'/original.lp',
            stock_export_SHA=sha(dest/'original.lp'),base_SHA=sha(base)))
        variants=['base','stock','tc','tc_stock']
        if role in ['K-35-U','R-X20-S-T1']:variants+=['gs_independent','gs_shared']
        for variant in variants:
            positions.append(dict(position=len(positions)+1,role=role,variant=variant,seed=0,cap_seconds=120,
                alpha=scope['alpha'],beta=scope['beta'],cutoff=cutoff,panel=p,
                input_SHA=p['input_sha256'],base_LP_SHA=sha(base),stock_LP_SHA=sha(dest/'original.lp')))
    assert sha(LP_PYTHON)=='2204195cec25879507d958a8b6949add67091244b8b4da9cf3672f993548fa49'
    write(OUT/'roots/plan.json',dict(UTC=utc(),positions=positions,python=str(LP_PYTHON),python_SHA=sha(LP_PYTHON),
        native_DLL_SHA=DLL_SHA,threads=1,serial=True,affinity=4,Seed=0,AP=False,
        before_new_Optimize=True,core_positions=16,GS_positions=4,TC_not_enabled_in_full_candidate_yet=True))
    print('20 finite LP positions registered; exact saved domains; Seed0, AP off')

def solve(position):
    import ctypes
    ctypes.windll.kernel32.SetProcessAffinityMask(ctypes.windll.kernel32.GetCurrentProcess(),4)
    from round100_gurobi_runtime import gp,binding
    plan=read(OUT/'roots/plan.json');a=plan['positions'][int(position)-1];role=a['role'];variant=a['variant']
    assert sha(sys.executable)==plan['python_SHA']
    scope=read(OUT/'roots'/role/'scope.json');added=read(OUT/'roots'/role/'additions.json')
    target=OUT/'roots'/role/variant;target.mkdir(parents=True,exist_ok=False)
    source=ROOT/added['stock_model'] if variant in ['stock','tc_stock'] else OUT/'roots'/role/'inherited/original.lp'
    tick=time.perf_counter();identity=binding();assert identity['sha256']==DLL_SHA
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        with gp.read(str(source),env=env) as m:
            m.Params.Threads=1;m.Params.Seed=0;m.Params.Presolve=-1;m.Params.TimeLimit=120
            m.Params.FeasibilityTol=1e-6;m.Params.OptimalityTol=1e-6
            m.Params.LogFile=str(target/'native.log');m.Params.LogToConsole=0;m.Params.OutputFlag=1
            for v in m.getVars():v.VType=gp.GRB.CONTINUOUS
            m.update();vs={v.VarName:v for v in m.getVars()};n=scope['panel']['V']
            before=dict(rows=m.NumConstrs,columns=m.NumVars,nonzeros=m.NumNZs)
            if variant in ['tc','tc_stock']:
                H=gp.quicksum(v for name,v in vs.items() if name.startswith('h_'))
                m.addConstr(H>=gp.quicksum(c*vs[name] for name,c in added['TC'].items()),name='r138_control_TC')
            if variant.startswith('gs_'):
                alpha,beta=a['alpha'],a['beta'];Su=added['GS_S_upper'];S=gp.quicksum(vs[f'r_{i}'] for i in range(1,n+1))
                if variant=='gs_independent': W=m.addVar(lb=0.,ub=math.nextafter(beta*Su,math.inf),name='r138_control_W_GS')
                else:W=gp.quicksum(float(c)*vs[f'zprod_{i}'] for i,c in added['ratio_coefficients'].items())
                m.addConstr(W>=alpha*S,name='r138_GS_lb0')
                m.addConstr(W-beta*S-Su*vs['G']>=math.nextafter(-beta*Su,-math.inf),name='r138_GS_lbU')
                m.addConstr(W<=beta*S,name='r138_GS_ub0')
                m.addConstr(W-alpha*S-Su*vs['G']<=math.nextafter(-alpha*Su,math.inf) if alpha else W-Su*vs['G']<=0,name='r138_GS_ubU')
                H=gp.quicksum(v for name,v in vs.items() if name.startswith('h_'))
                m.addConstr(H<=n*W,name='r138_GS_epigraph')
            m.update();after=dict(rows=m.NumConstrs,columns=m.NumVars,nonzeros=m.NumNZs)
            params={k:m.getParamInfo(k)[2] for k in ['Seed','Threads','Presolve','TimeLimit','FeasibilityTol','OptimalityTol']}
            assert params['Seed']==0 and params['Threads']==1 and m.IsMIP==0
            construct=time.perf_counter();m.optimize();solved=time.perf_counter()
            assert m.Status==gp.GRB.OPTIMAL,(role,variant,m.Status)
            vector={v.VarName:v.X for v in m.getVars()}
            with gzip.open(target/'solution.json.gz','wt',encoding='utf-8') as stream:json.dump(vector,stream,separators=(',',':'))
            quality={k:m.getAttr(k) for k in ['ConstrVio','BoundVio','DualVio','ConstrResidual','DualResidual','ComplVio']}
            U=scope['validated_U'];L=m.ObjVal
            result=dict(position=int(position),role=role,variant=variant,status='NUMERICAL_OPTIMAL_LP',L=L,
                delta_saved=L-scope['L_saved'],same_validated_U=U,signed_gap=U-L,relative_gap=(U-L)/max(abs(U),1e-12),
                G_aux=vector['G'],J=math.fsum(vector[f'zprod_{i}'] for i in range(1,n+1)),
                tau=math.fsum(vector[f'Y_{i}'] for i in range(1,n+1)),
                S=math.fsum(vector[f'r_{i}'] for i in range(1,n+1)),
                quality=quality,before=before,after=after,params=params,
                model_SHA=sha(source),solution_SHA=sha(target/'solution.json.gz'),native_identity=identity,
                construct_seconds=construct-tick,optimize_wall_seconds=solved-construct,
                runtime=m.Runtime,Work=m.Work,iterations=m.IterCount,LP_Optimize=1,MIP_Optimize=0,
                noncomparison_auxiliaries_free=True,AP=False,source_plan_SHA=sha(OUT/'roots/plan.json'))
            write(target/'result.json',result)
    print(json.dumps({k:result[k] for k in ['role','variant','L','delta_saved','G_aux','J','tau','S']}),flush=True)

def run():
    plan=read(OUT/'roots/plan.json')
    for a in plan['positions']:
        label=f'LP_{a["position"]:02}_{a["role"]}_{a["variant"]}'
        assert metered(label,'diagnostic',[LP_PYTHON,ROOT/'scripts/round138_lp.py','solve',a['position']],
                       reservation=150,timeout=180)==0

if __name__=='__main__':
    if sys.argv[1]=='solve':solve(int(sys.argv[2]))
    else:globals()[sys.argv[1]]()
