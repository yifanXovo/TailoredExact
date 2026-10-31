"""Finite same-domain RN LPs, serial Seed0/Threads1, complete objective retained."""
import gzip
from itertools import combinations
from round143_math import rn_rows
from round143_common import *

def residual(model,point):
    high=0.
    for c in model.getConstrs():
        e=model.getRow(c); lhs=math.fsum(e.getCoeff(i)*point[e.getVar(i).VarName] for i in range(e.size()))
        v=max(0.,c.RHS-lhs) if c.Sense=='>' else max(0.,lhs-c.RHS) if c.Sense=='<' else abs(lhs-c.RHS)
        high=max(high,v)
    return dict(constraints=high,bounds=max([max(v.LB-point[v.VarName],point[v.VarName]-v.UB,0.) for v in model.getVars()] or [0.]),
        objective=model.ObjCon+math.fsum(v.Obj*point[v.VarName] for v in model.getVars()))

def semantics(m,old_columns=None,old_rows=None):
    columns=[(v.VarName,v.LB,v.UB,v.Obj,v.VType) for v in m.getVars() if old_columns is None or v.VarName in old_columns]
    rows=[]
    for c in m.getConstrs():
        if old_rows is not None and c.ConstrName not in old_rows: continue
        e=m.getRow(c); rows.append((c.ConstrName,c.Sense,c.RHS,sorted((e.getVar(i).VarName,e.getCoeff(i)) for i in range(e.size()))))
    return dict(columns=columns,rows=rows,ObjCon=m.ObjCon,ModelSense=m.ModelSense)

def solve(role,variant,cap=120):
    assert variant in ('base','stock','tc_stock')
    assert ctypes.windll.kernel32.SetProcessAffinityMask(ctypes.windll.kernel32.GetCurrentProcess(),4)
    from round100_gurobi_runtime import gp,binding
    identity=binding(); assert identity['sha256']==DLL_SHA
    tick=time.perf_counter(); folder=OUT/'inherited/roots'/role
    scope=read(folder/'scope.json'); spec=read(OUT/'domains'/role/'RN.json')
    target=OUT/'LP'/f'{role}_{variant}'; target.mkdir(parents=True,exist_ok=False)
    old=read(folder/variant/'result.json'); oldpoint=json.loads(gzip.decompress((folder/variant/'solution.json.gz').read_bytes()))
    source=folder/'inherited/original.lp'
    if variant!='base':
        options=[folder/'stock_export_exact_cutoff/original.lp',folder/'stock_export/original.lp']
        source=next(p for p in options if p.exists())
    assert sha(folder/variant/'solution.json.gz')==old['solution_SHA']
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0); env.start()
        with gp.read(str(source),env=env) as model:
            for v in model.getVars(): v.VType=gp.GRB.CONTINUOUS
            model.update(); vs={v.VarName:v for v in model.getVars()}
            if variant=='tc_stock':
                add=read(folder/'additions.json')
                H=gp.quicksum(v for name,v in vs.items() if name.startswith('h_'))
                model.addConstr(H>=gp.quicksum(a*vs[k] for k,a in add['TC'].items()),name='r143_inherited_TC')
                model.update()
            baseline=residual(model,oldpoint)
            assert baseline['constraints']<=1e-6 and baseline['bounds']<=1e-6,baseline
            assert abs(baseline['objective']-old['L'])<=1e-8,(baseline,old['L'])
            assert all(getattr(model,k)==old['after'][v] for k,v in [('NumVars','columns'),('NumConstrs','rows'),('NumNZs','nonzeros')])
            oldsem=semantics(model); oldnames=set(vs); oldrows={c.ConstrName for c in model.getConstrs()}
            before=dict(rows=model.NumConstrs,columns=model.NumVars,nonzeros=model.NumNZs)
            supports={int(i):ys for i,ys in spec['supports'].items()}; lt,ut=spec['L_t'],spec['U_t']
            model.addVar(lb=lt,ub=ut,name='rn_t')
            for i,ys in supports.items():
                model.addVar(lb=0.,name=f'rn_Y_{i}')
                for y in ys: model.addVar(lb=0.,ub=ut,name=f'rn_w_{i}_{y}')
            for i,j in combinations(supports,2): model.addVar(lb=0.,name=f'rn_h_{i}_{j}')
            model.update(); vs={v.VarName:v for v in model.getVars()}; expected=rn_rows(spec)
            for r in expected:
                e=gp.quicksum(a*vs[k] for k,a in r['terms'].items())
                model.addConstr(e>=r['rhs'] if r['sense']=='>' else e<=r['rhs'] if r['sense']=='<' else e==r['rhs'],name=r['name'])
            model.update(); assert semantics(model,oldnames,oldrows)==oldsem
            canonical=target/'model.mps'; model.write(str(canonical)); fingerprint=model.Fingerprint
            after=dict(rows=model.NumConstrs,columns=model.NumVars,nonzeros=model.NumNZs)
        with gp.read(str(canonical),env=env) as model:
            assert model.Fingerprint==fingerprint
            assert semantics(model,oldnames,oldrows)==oldsem
            assert not model.IsMIP and all(v.VType==gp.GRB.CONTINUOUS for v in model.getVars())
            for r in expected:
                c=model.getConstrByName(r['name']); e=model.getRow(c)
                assert c.Sense==r['sense'] and c.RHS==r['rhs']
                assert {e.getVar(i).VarName:e.getCoeff(i) for i in range(e.size())}==r['terms']
            vs={v.VarName:v for v in model.getVars()}
            assert vs['rn_t'].LB==lt and vs['rn_t'].UB==ut
            for name,v in vs.items():
                if name.startswith('rn_') and name!='rn_t':
                    assert v.LB==0 and v.UB==(ut if name.startswith('rn_w_') else gp.GRB.INFINITY)
            model.Params.Threads=1; model.Params.Seed=0; model.Params.Presolve=-1
            model.Params.TimeLimit=cap; model.Params.FeasibilityTol=1e-6; model.Params.OptimalityTol=1e-6
            model.Params.LogFile=str(target/'native.log'); model.Params.LogToConsole=0; model.Params.OutputFlag=1
            write(target/'scope.json',dict(role=role,variant=variant,RN=spec,source=str(source.relative_to(ROOT)),source_SHA=sha(source),
                inherited_result_SHA=sha(folder/variant/'result.json'),inherited_point_SHA=sha(folder/variant/'solution.json.gz'),
                saved_point_full_matrix=baseline,original_semantics_retained=True,all_new_rows_and_columns_read_back=True,
                canonical_SHA=sha(canonical),cutoff=scope['validated_U'],old_g_domain=[scope['alpha'],scope['beta']],
                expected_rows=expected,BASE_increment_includes_physical_bound_information=(variant=='base')))
            built=time.perf_counter(); model.optimize(); done=time.perf_counter()
            result=dict(role=role,variant=variant,status=model.Status,qualified=False,old_L=old['L'],old_g=old['G_aux'],
                old_weighted_penalty=old['L']-old['G_aux'],before=before,after=after,
                build_seconds=built-tick,optimize_wall_seconds=done-built,Runtime=model.Runtime,Work=model.Work,
                Seed=model.Params.Seed,Threads=model.Params.Threads,affinity_mask=4,LP_Optimize=1,MIP_Optimize=0,
                params={k:model.getParamInfo(k)[2] for k in ['Seed','Threads','Presolve','TimeLimit','FeasibilityTol','OptimalityTol']},
                fingerprint=fingerprint,canonical_SHA=sha(canonical),native_identity=identity,
                writer_SHA=sha(__file__),math_SHA=sha(ROOT/'scripts/round143_math.py'),source_commit=git('rev-parse','HEAD').decode().strip(),
                S_L_exact=spec['S_L_exact'],S_U_exact=spec['S_U_exact'],L_t=lt,U_t=ut)
            if model.Status==gp.GRB.OPTIMAL:
                point={v.VarName:v.X for v in model.getVars()}
                with gzip.open(target/'solution.json.gz','wt',encoding='utf-8') as f: json.dump(point,f,separators=(',',':'))
                quality={k:model.getAttr(k) for k in ['ConstrVio','BoundVio','DualVio','ConstrResidual','DualResidual','ComplVio']}
                check=residual(model,point); g=point['G']; t=point['rn_t']
                result.update(L=model.ObjVal,g=g,weighted_penalty=model.ObjVal-g,difference=model.ObjVal-old['L'],quality=quality,
                    full_matrix_residual=check,qualified=all(v<=1e-6 for v in quality.values()) and check['constraints']<=1e-6 and check['bounds']<=1e-6,
                    t=t,solution_SHA=sha(target/'solution.json.gz'),iterations=model.IterCount,
                    tau=math.fsum(point[f'Y_{i}'] for i in supports),
                    normalized_gini=math.fsum(abs(spec['c_binary64'][str(i)]*point[f'rn_Y_{i}']-spec['c_binary64'][str(j)]*point[f'rn_Y_{j}']) for i,j in combinations(supports,2))/len(supports))
            write(target/'result.json',result)
    print(json.dumps({k:result.get(k) for k in ['role','variant','qualified','L','difference','g','weighted_penalty','build_seconds','optimize_wall_seconds']}),flush=True)

def run(role,variant):
    configure()
    label=f'LP_{role}_{variant}'
    assert metered(label,'diagnostic',[LP_PYTHON,'-B',ROOT/'scripts/round143_lp.py','solve',role,variant],reservation=150,timeout=180)==0

if __name__=='__main__':
    if sys.argv[1]=='solve': solve(sys.argv[2],sys.argv[3])
    else: run(sys.argv[2],sys.argv[3])
