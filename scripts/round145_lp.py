"""Finite matched LP decision stage; reuse RN optima, never rebuild a historical panel."""
import gzip, collections
import round108_reader as parser
from round143_qualify import actual_spec,expected_rows
from round143_lp import residual,semantics
from round145_math import joint_rows,row_activity,project,safe_row,F
from round145_common import *
configure()

def save_gz(path,obj):
    with gzip.open(path,'wt',encoding='utf-8') as f:json.dump(obj,f,separators=(',',':'),allow_nan=False)

def domain(role):
    if role in ('K-35-U','R-X20-S-T1'):
        folder=ROOT/'results/unified_exact_round144/LP'/f'{role}_base'
        meta=read(folder/'source_scope.json');old=read(folder/'result.json')['source']
        matrix=folder/'source.mps';assert sha(matrix)==meta['model_SHA']
        point=json.loads(gzip.decompress((folder/'source_solution.json.gz').read_bytes()))
        spec=meta['RN'];base=folder/'base.mps'
        return dict(matrix=matrix,base=base,spec=spec,old=old,point=point,meta=meta)
    assert role=='K-20-S'
    folder=ROOT/'results/unified_exact_round144/campaign_resource_k20/002/raw/R144_resource_k20_002_K-20-S_S0_RNP/external'
    meta=read(folder/'round144_source.json');evidence=read(folder/'round144_projection.json')
    matrix=folder/'models/round144_RN_source.lp';assert sha(matrix)==meta['source_SHA']
    parsed=parser.lp_model(matrix);scope=read(ROOT/'results/unified_exact_round143/inherited/roots'/role/'scope.json')
    spec=actual_spec(parsed,scope['Bminus'],scope['B']);point={v['name']:v['X'] for v in evidence['variables']}
    return dict(matrix=matrix,base=None,spec=spec,old=dict(L=meta['source_objective']),point=point,meta=meta)

def add_rows(model,rows,gp):
    vs={v.VarName:v for v in model.getVars()}
    for r in rows:
        expr=gp.quicksum(a*vs[k] for k,a in r['terms'].items())
        model.addConstr(expr>=r['rhs'] if r['sense']=='>' else expr<=r['rhs'] if r['sense']=='<' else expr==r['rhs'],name=r['name'])
    model.update()

def old_extra(spec,bounds):
    from round140_math import count_rows
    from round138_repair import scaled_rows
    support={int(i):ys for i,ys in spec['supports'].items()};ratio={int(i):F(c) for i,c in spec['c_binary64'].items()}
    counts=count_rows(support,ratio,spec['Bminus'],spec['B']);n=len(support);out=[]
    for j,(terms,sense,rhs) in enumerate(scaled_rows(n,*bounds['G'],spec['Bminus'],spec['B']),1):
        out.append(dict(name=f'r145_old_STOCK{j}',terms=dict(terms),sense={'>=':'>','<=':'<'}[sense],rhs=rhs))
    H={f'h_{i}_{j}':F(1) for i in support for j in support if i<j}
    for key,b in [('TC',F(0)),('TC2',counts['constant'])]:
        terms=dict(H);terms.update({f'state_{i}_{y}':-v for (i,y),v in counts[key].items() if v})
        row,_=safe_row('r145_old_'+key,terms,'>',b,bounds);out.append(row)
    return out

def solve(role,variant):
    configure()
    from round100_gurobi_runtime import gp,binding
    assert binding()['sha256']==DLL_SHA
    kernel=ctypes.WinDLL('kernel32',use_last_error=True);kernel.GetCurrentProcess.restype=ctypes.c_void_p
    kernel.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t]
    assert kernel.SetProcessAffinityMask(kernel.GetCurrentProcess(),4)
    d=domain(role);target=OUT/'LP'/f'{role}_{variant}';target.mkdir(parents=True,exist_ok=False)
    start=time.perf_counter()
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Threads',1);env.setParam('Seed',0);env.start()
        with gp.read(str(d['matrix']),env=env) as model:
            for v in model.getVars():v.VType=gp.GRB.CONTINUOUS
            model.update();before=semantics(model);oldnames={v.VarName for v in model.getVars()};oldrows={c.ConstrName for c in model.getConstrs()}
            baseline_check=residual(model,d['point']);assert max(baseline_check['constraints'],baseline_check['bounds'])<=1e-6 and abs(baseline_check['objective']-d['old']['L'])<1e-8
            bounds={v.VarName:(v.LB,v.UB) for v in model.getVars()};block=joint_rows(d['spec'],bounds)
            for r in expected_rows(d['spec']):
                c=model.getConstrByName(r['name']);e=model.getRow(c)
                assert c.Sense==r['sense'] and c.RHS==r['rhs'] and {e.getVar(i).VarName:e.getCoeff(i) for i in range(e.size())}==r['terms']
            assert bounds['rn_t']==(d['spec']['L_t'],d['spec']['U_t'])
            assert all(v.Obj==0 for v in model.getVars() if v.VarName.startswith('rn_'))
            if variant=='O':rows=old_extra(d['spec'],bounds)
            elif variant=='O_joint':rows=old_extra(d['spec'],bounds)+block['rows']
            else:
                assert variant in ('NC','TS','joint')
                rows=[r for r in block['rows'] if variant=='joint' or ('_NC' in r['name'] if variant=='NC' else '_TS' in r['name'])]
            add_rows(model,rows,gp);assert semantics(model,oldnames,oldrows)==before
            write(target/'new_rows.json',dict(block,actually_added=[r['name'] for r in rows],added_rows=rows))
            model.write(str(target/'model.mps'))
        with gp.read(str(target/'model.mps'),env=env) as model:
            assert semantics(model,oldnames,oldrows)==before
            for r in rows:
                c=model.getConstrByName(r['name']);e=model.getRow(c)
                assert c.Sense==r['sense'] and c.RHS==r['rhs'] and {e.getVar(i).VarName:e.getCoeff(i) for i in range(e.size())}==r['terms']
            model.Params.Seed=0;model.Params.Threads=1;model.Params.TimeLimit=120
            model.Params.OutputFlag=1;model.Params.LogToConsole=0;model.Params.LogFile=str(target/'native.log')
            write(target/'call.json',dict(UTC=utc(),Seed=0,Threads=1,model_SHA=sha(target/'model.mps'),state='BEFORE_OPTIMIZE'))
            tick=time.perf_counter();model.optimize();elapsed=time.perf_counter()-tick
            write(target/'return.json',dict(UTC=utc(),Status=model.Status,Runtime=model.Runtime,Work=model.Work,optimize_wall=elapsed))
            assert model.Status==gp.GRB.OPTIMAL
            point={v.VarName:v.X for v in model.getVars()};quality={k:model.getAttr(k) for k in ['ConstrVio','BoundVio','DualVio','ConstrResidual','DualResidual','ComplVio']}
            check=residual(model,point);assert max(quality.values())<=1e-6 and max(check['constraints'],check['bounds'])<=1e-6
            allrows=[]
            for c in model.getConstrs():
                e=model.getRow(c);allrows.append(dict(name=c.ConstrName,sense=c.Sense,rhs=c.RHS,Pi=c.Pi,Slack=c.Slack,CBasis=c.CBasis,terms={e.getVar(i).VarName:e.getCoeff(i) for i in range(e.size())}))
            cols={v.VarName:dict(LB=v.LB,UB=v.UB,Obj=v.Obj,X=v.X,RC=v.RC,VBasis=v.VBasis) for v in model.getVars()}
            save_gz(target/'primal_dual_matrix.json.gz',dict(columns=cols,rows=allrows,ObjCon=model.ObjCon,ModelSense=model.ModelSense))
            save_gz(target/'solution.json.gz',point)
            result=dict(role=role,variant=variant,L=model.ObjVal,g=point['G'],weighted_penalty=model.ObjVal-point['G'],
                inherited_RN_L=d['old']['L'],gain_over_RN=model.ObjVal-d['old']['L'],old_g=d['point']['G'],old_weighted_penalty=d['old']['L']-d['point']['G'],
                rows=model.NumConstrs,columns=model.NumVars,nonzeros=model.NumNZs,added_rows=len(rows),
                Runtime=model.Runtime,Work=model.Work,iterations=model.IterCount,optimize_wall=elapsed,
                quality=quality,residual=check,qualified=True,all_new_rows_Native_readback=True,
                objective_all_old_rows_bounds_cutoff_support_retained=True,
                activities=[row_activity(r,point) for r in block['rows']],old_activities=[row_activity(r,d['point']) for r in block['rows']],
                tau=math.fsum(point[f'Y_{i}'] for i in range(1,len(d['spec']['supports'])+1)),t=point['rn_t'],
                source=str(d['matrix'].relative_to(ROOT)),source_SHA=sha(d['matrix']),model_SHA=sha(target/'model.mps'),
                baseline_residual=baseline_check,Seed=0,Threads=1,affinity_mask=4,LP_Optimize=1,total_inside_seconds=time.perf_counter()-start,
                Native=binding(),writer_SHA=sha(__file__),math_SHA=sha(ROOT/'scripts/round145_math.py'))
            write(target/'scope.json',dict(RN=d['spec'],inherited_meta=d['meta'],inherited_source_SHA=sha(d['matrix'])))
            write(target/'result.json',result)
    print(json.dumps({k:result[k] for k in ['role','variant','L','g','weighted_penalty','gain_over_RN','Runtime','qualified']}),flush=True)

def run(role,variant):
    configure();assert metered('LP_'+role+'_'+variant,'diagnostic',[LP_PYTHON,'-B',__file__,'solve',role,variant],180,240)==0
if __name__=='__main__':
    if sys.argv[1]=='solve':solve(*sys.argv[2:])
    else:run(*sys.argv[2:])
