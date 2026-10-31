"""Matched production-capped RN source and one exact-box projected BASE LP.

The Python Fraction construction is an independent oracle for the production
directed-interval writer, not an online algorithm or a dual-repair optimizer.
"""
import gzip, collections
from fractions import Fraction as F
import round108_reader as parser
from round143_qualify import actual_spec, expected_rows
from round143_lp import residual, semantics
from round144_common import *
configure()

def outward(q, upper):
    d=float(q)
    if (F(d)<q) if upper else (F(d)>q): d=math.nextafter(d,math.inf if upper else -math.inf)
    assert (F(d)>=q) if upper else (F(d)<=q)
    return d

def projected(rows, bounds, drop=1e-12):
    """Actual >= dual convention. No stationarity or exact cancellation needed."""
    a=collections.defaultdict(F); b=F(0); repairs=[]; active=[]
    for row in rows:
        pi=F(row['Pi']); original=pi
        if row['sense']=='>': pi=max(pi,F(0))
        elif row['sense']=='<': pi=min(pi,F(0))
        else: assert row['sense']=='='
        if pi!=original: repairs.append(dict(name=row['name'],Pi=row['Pi'],used=float(pi)))
        if not pi: continue
        active.append(row['name']); b+=pi*F(row['rhs'])
        for k,v in row['terms'].items(): a[k]+=pi*F(v)
    sigma=F(0); residuals={}
    for k in list(a):
        if k.startswith('rn_'):
            lo,hi=bounds[k]; assert math.isfinite(lo) and math.isfinite(hi) and abs(hi)<1e100
            sigma+=max(a[k]*F(lo),a[k]*F(hi)); residuals[k]=str(a.pop(k))
    exact_rhs=b-sigma; correction=F(0); terms={}; dropped=[]
    for k,v in sorted(a.items()):
        assert k=='G' or k.startswith('state_'),k
        lo,hi=bounds[k]; assert abs(lo)<1e100 and abs(hi)<1e100
        coef=float(v)
        if abs(coef)<drop: coef=0.
        error=F(coef)-v; correction+=min(error*F(lo),error*F(hi))
        if coef: terms[k]=coef
        elif v: dropped.append(k)
    rhs=outward(exact_rhs+correction,False)
    return dict(name='r144_PC',sense='>',terms=terms,rhs=rhs,exact_terms={k:str(v) for k,v in a.items() if v},
        aggregate_rhs_exact=str(b),box_support_exact=str(sigma),exact_projected_rhs=str(exact_rhs),
        conversion_correction_exact=str(correction),total_rhs_loss=float(exact_rhs-F(rhs)),
        new_column_residuals_exact=residuals,max_abs_new_residual=max(map(lambda q:abs(float(F(q))),residuals.values()),default=0.),
        sign_repairs=repairs,source_rows=active,dropped_nonzero=dropped,arithmetic='Exact Fraction of actual binary64 Native rows, Pi and bounds',
        RN_columns=0,validity='RN combination >= b; upper box support; downward RHS and signed original-box conversion compensation')

def save_gz(path,value):
    with gzip.open(path,'wt',encoding='utf-8') as f: json.dump(value,f,separators=(',',':'),allow_nan=False)

def solve(role, variant='base', attempt=''):
    from round100_gurobi_runtime import gp,binding
    assert binding()['sha256']==DLL_SHA
    kernel=ctypes.WinDLL('kernel32',use_last_error=True);kernel.GetCurrentProcess.restype=ctypes.c_void_p
    kernel.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t]
    assert kernel.SetProcessAffinityMask(kernel.GetCurrentProcess(),4)
    tick=time.perf_counter(); oldroot=ROOT/'results/unified_exact_round143/inherited/roots'/role
    scope=read(oldroot/'scope.json'); assert variant=='base'
    source=oldroot/'inherited/original.lp';parsed=parser.lp_model(source)
    spec=actual_spec(parsed,scope['Bminus'],scope['B']);assert spec['applicable']
    target=OUT/'LP'/f'{role}_{variant}{attempt}';target.mkdir(parents=True,exist_ok=False)
    old=read(oldroot/variant/'result.json')
    point=json.loads(gzip.decompress((oldroot/variant/'solution.json.gz').read_bytes()))
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Seed',0);env.setParam('Threads',1);env.start()
        with gp.read(str(source),env=env) as base:
            for v in base.getVars(): v.VType=gp.GRB.CONTINUOUS
            base.update();oldsem=semantics(base);names={v.VarName for v in base.getVars()};oldrows={c.ConstrName for c in base.getConstrs()}
            check=residual(base,point);assert max(check['constraints'],check['bounds'])<1e-6 and abs(check['objective']-old['L'])<1e-8
            base.write(str(target/'base.mps'));rn=base.copy()
            supports={int(i):ys for i,ys in spec['supports'].items()};ut=spec['U_t']
            rn.addVar(lb=spec['L_t'],ub=ut,name='rn_t')
            for i,ys in supports.items():
                rn.addVar(lb=0.,ub=math.nextafter(ut*max(ys),math.inf) if max(ys) else 0.,name=f'rn_Y_{i}')
                for y in ys:rn.addVar(lb=0.,ub=ut,name=f'rn_w_{i}_{y}')
                for j in supports:
                    if i<j:rn.addVar(lb=0.,ub=1.,name=f'rn_h_{i}_{j}')
            rn.update();vs={v.VarName:v for v in rn.getVars()}
            expected=expected_rows(spec)
            for r in expected:
                e=gp.quicksum(v*vs[k] for k,v in r['terms'].items())
                rn.addConstr(e>=r['rhs'] if r['sense']=='>' else e<=r['rhs'] if r['sense']=='<' else e==r['rhs'],name=r['name'])
            rn.update();assert semantics(rn,names,oldrows)==oldsem
            rn.write(str(target/'source.mps'));rn.dispose()
            with gp.read(str(target/'source.mps'),env=env) as rn:
                assert semantics(rn,names,oldrows)==oldsem
                for r in expected:
                    c=rn.getConstrByName(r['name']);e=rn.getRow(c)
                    assert c.Sense==r['sense'] and c.RHS==r['rhs'] and {e.getVar(i).VarName:e.getCoeff(i) for i in range(e.size())}==r['terms']
                for model,label in [(rn,'source')]:
                    model.Params.Seed=0;model.Params.Threads=1;model.Params.TimeLimit=120
                    model.Params.LogToConsole=0;model.Params.OutputFlag=1;model.Params.LogFile=str(target/(label+'.log'))
                    write(target/(label+'_call.json'),dict(UTC=utc(),state='BEFORE_OPTIMIZE',Seed=0,Threads=1,model_SHA=sha(target/(label+'.mps'))))
                    start=time.perf_counter();model.optimize();elapsed=time.perf_counter()-start
                    write(target/(label+'_return.json'),dict(UTC=utc(),status=model.Status,Runtime=model.Runtime,Work=model.Work,optimize_wall=elapsed))
                assert rn.Status==gp.GRB.OPTIMAL
                cols={v.VarName:dict(LB=v.LB,UB=v.UB,Obj=v.Obj,X=v.X,RC=v.RC,VBasis=v.VBasis) for v in rn.getVars()}
                allrows=[]
                for c in rn.getConstrs():
                    e=rn.getRow(c);allrows.append(dict(name=c.ConstrName,sense=c.Sense,rhs=c.RHS,Pi=c.Pi,Slack=c.Slack,CBasis=c.CBasis,
                        terms={e.getVar(i).VarName:e.getCoeff(i) for i in range(e.size())}))
                save_gz(target/'primal_dual_matrix.json.gz',dict(columns=cols,rows=allrows,ObjCon=rn.ObjCon,ModelSense=rn.ModelSense))
                rn.write(str(target/'source.bas'));save_gz(target/'source_solution.json.gz',{k:v['X'] for k,v in cols.items()})
                bounds={k:(v['LB'],v['UB']) for k,v in cols.items()}
                pc=projected([r for r in allrows if r['name'].startswith('rn_')],bounds)
                write(target/'projection.json',pc)
                src=dict(L=rn.ObjVal,columns=rn.NumVars,rows=rn.NumConstrs,nonzeros=rn.NumNZs,Runtime=rn.Runtime,Work=rn.Work,iterations=rn.IterCount,
                    quality={k:rn.getAttr(k) for k in ['ConstrVio','BoundVio','DualVio','ConstrResidual','DualResidual','ComplVio']},
                    residual=residual(rn,{k:v['X'] for k,v in cols.items()}))
                write(target/'source_scope.json',dict(role=role,variant=variant,RN=spec,source=str(source.relative_to(ROOT)),source_SHA=sha(source),
                    original_semantics_retained=True,cutoff=scope['validated_U'],g_domain=[scope['alpha'],scope['beta']],
                    model_SHA=sha(target/'source.mps'),evidence_SHA=sha(target/'primal_dual_matrix.json.gz'),Native=binding()))
            e=gp.quicksum(v*base.getVarByName(k) for k,v in pc['terms'].items());base.addConstr(e>=pc['rhs'],name=pc['name']);base.update()
            assert semantics(base,names,oldrows)==oldsem and not any(v.VarName.startswith('rn_') for v in base.getVars())
            base.write(str(target/'compact.mps'))
        with gp.read(str(target/'compact.mps'),env=env) as model:
            assert semantics(model,names,oldrows)==oldsem
            c=model.getConstrByName(pc['name']);e=model.getRow(c)
            assert c.Sense==pc['sense'] and c.RHS==pc['rhs'] and {e.getVar(i).VarName:e.getCoeff(i) for i in range(e.size())}==pc['terms']
            model.Params.Seed=0;model.Params.Threads=1;model.Params.TimeLimit=120
            model.Params.OutputFlag=1;model.Params.LogToConsole=0;model.Params.LogFile=str(target/'compact.log')
            write(target/'compact_call.json',dict(UTC=utc(),state='BEFORE_OPTIMIZE',Seed=0,Threads=1,model_SHA=sha(target/'compact.mps')))
            start=time.perf_counter();model.optimize();elapsed=time.perf_counter()-start
            write(target/'compact_return.json',dict(UTC=utc(),status=model.Status,Runtime=model.Runtime,Work=model.Work,optimize_wall=elapsed))
            assert model.Status==gp.GRB.OPTIMAL
            xp={v.VarName:v.X for v in model.getVars()};save_gz(target/'compact_solution.json.gz',xp)
            compact=dict(L=model.ObjVal,columns=model.NumVars,rows=model.NumConstrs,nonzeros=model.NumNZs,Runtime=model.Runtime,Work=model.Work,iterations=model.IterCount,
                residual=residual(model,xp),quality={k:model.getAttr(k) for k in ['ConstrVio','BoundVio','DualVio','ConstrResidual','DualResidual','ComplVio']})
    result=dict(role=role,variant=variant,old_L=old['L'],source=src,compact=compact,source_gain=src['L']-old['L'],
        compact_gain=compact['L']-old['L'],root_retention_loss=src['L']-compact['L'],retention_fraction=(compact['L']-old['L'])/(src['L']-old['L']),
        added_RN_columns=0,added_PC_rows=1,PC_nonzeros=len(pc['terms']),compensation_loss=pc['total_rhs_loss'],
        saved_old_point_violation=pc['rhs']-math.fsum(v*point[k] for k,v in pc['terms'].items()),
        Seed=0,Threads=1,affinity_mask=4,LP_Optimize=2,complete_old_objective_matrix_cutoff_support_g_retained=True,
        source_SHA=sha(target/'source.mps'),compact_SHA=sha(target/'compact.mps'),projection_SHA=sha(target/'projection.json'),
        source_commit=git('rev-parse','HEAD').decode().strip(),writer_SHA=sha(__file__),total_inside_seconds=time.perf_counter()-tick)
    result['qualified']=all(max(r['quality'].values())<=1e-6 and max(r['residual']['constraints'],r['residual']['bounds'])<=1e-6 for r in [src,compact])
    write(target/'result.json',result);print(json.dumps(result),flush=True)

def run(role,attempt=''):
    configure();assert metered('LP_'+role+attempt,'diagnostic',[LP_PYTHON,'-B',__file__,'solve',role,'base',attempt],300,360)==0
if __name__=='__main__':
    if sys.argv[1]=='solve':solve(*sys.argv[2:])
    else:run(*sys.argv[2:])
