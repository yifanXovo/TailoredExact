"""Five exact-domain LP increments; no historical Optimize is repeated."""
import gzip
from itertools import product
from fractions import Fraction as F
from round143_lp import semantics, residual
from round145_lp import add_rows, save_gz
from round148_math import choose, compile_row, activity, alpha, downward
from round148_common import *
configure()


def inherited(role, carrier):
    folder = ROOT/'results/unified_exact_round146/LP'/f'{role}_{carrier}_GD'
    old = read(folder/'result.json')
    assert sha(folder/'model.mps') == old['model_SHA']
    return folder, old, read(folder/'compiled_rows.json'), json.loads(gzip.decompress((folder/'solution.json.gz').read_bytes()))


def screen():
    start = time.perf_counter()
    results = []
    for role, carrier in ROLES:
        folder, old, block, point = inherited(role, carrier)
        exact, cert = choose(block, point)
        row, transport = compile_row(exact, point, 'r148_affine_1')
        results.append(dict(role=role, carrier=carrier, old_L=old['L'], old_g=old['g'],
            new_affine_value=transport['ideal_violation']+old['g'],
            certificate=cert, transport=transport, row=row,
            source_model_SHA=sha(folder/'model.mps'), source_point_SHA=sha(folder/'solution.json.gz')))
    write(OUT/'offline_screen.json', dict(Optimize=0, Native_load=0,
        five_models_three_instances=True, results=results, seconds=time.perf_counter()-start))
    print(json.dumps([{k:r[k] for k in ('role','carrier','new_affine_value')} | {'violation':r['transport']['ideal_violation']} for r in results]))


def qualify():
    # Full integer enumeration checks validity on tiny support/physical domains,
    # including positive S / zero old GD rows, negative RHS and nonminimal g.
    from round143_math import denominator
    from round146_math import oracle
    configure()
    start = time.perf_counter()
    fixtures = [
        ('strict_zero_old_GD', {1:[1,2],2:[1,2]}, {1:1.,2:1.}, 2,4),
        ('heterogeneous_holes', {1:[0,2,5],2:[1,4],3:[0,3]}, {1:.1,2:1/3,3:1.7},3,7),
        ('fixed', {1:[2],2:[0,3],3:[1]}, {1:.125,2:.7,3:1.},3,5),
        ('fixed_denominator', {1:[1],2:[2]}, {1:1.,2:1.},3,3),
        ('zero_ratio', {1:[0,2],2:[1,3]}, {1:0.,2:.3},1,4),
        ('infeasible_state', {1:[0,10],2:[1,2]}, {1:.4,2:.2},1,3),
        ('zero_domain', {1:[0,1],2:[0,2]}, {1:.2,2:.7},0,3),
        ('infeasible_domain', {1:[2],2:[3]}, {1:1.,2:2.},0,4)]
    facts = []
    for tag, support, cs, bm, bmax in fixtures:
        spec = dict(supports=support,c_binary64=cs,Bminus=bm,B=bmax)
        root, states = oracle(spec)
        if not root['applicable']:
            facts.append(dict(tag=tag, omitted=True, reason=root['reason']))
            continue
        block = dict(applicable=True, scope=spec, states=[dict(i=i,y=y,feasible=v is not None,
            **({} if v is None else dict(lower=float(v['lower']),upper=float(v['upper'])))) for (i,y),v in states.items()])
        # Exact bounds in fixture: outward-round, matching production semantics.
        for st in block['states']:
            if st['feasible']:
                v=states[st['i'],st['y']]
                if F(st['lower']) > v['lower']:st['lower']=math.nextafter(st['lower'],-math.inf)
                if F(st['upper']) < v['upper']:st['upper']=math.nextafter(st['upper'],math.inf)
        vectors=[]
        for yy in product(*support.values()):
            ys=dict(zip(support,yy)); S=sum(F(cs[i])*ys[i] for i in support)
            if bm <= sum(yy) <= bmax and S > 0:
                G=sum(abs(F(cs[i])*ys[i]-F(cs[j])*ys[j]) for i in support for j in support if i<j)/(len(support)*S)
                p={'G':float(G)} | {f'Y_{i}':float(y) for i,y in ys.items()}
                p.update({f'state_{i}_{y}':float(ys[i]==y) for i,v in support.items() for y in v})
                vectors.append((p,G))
        # Mix integer points to produce consistent fractional separating input.
        point={k:math.fsum(p[k] for p,g in vectors)/len(vectors) for k in vectors[0][0]}
        point['G']=0.
        if tag=='strict_zero_old_GD':
            point={'G':0., 'Y_1':1.5, 'Y_2':2.,'state_1_1':.5,'state_1_2':.5,'state_2_1':0.,'state_2_2':1.}
        exact, cert=choose(block,point)
        row, transport=compile_row(exact,point,'fixture')
        for p,G in vectors:
            for g in (G,F(1)):
                assert g-sum(exact['rhs'].get(k,F(0))*F(v) for k,v in p.items() if k.startswith('state_')) >= 0
                assert F(row['terms'].get('G',0.))*g+sum(F(a)*F(p[k]) for k,a in row['terms'].items() if k!='G') >= 0
        if tag=='strict_zero_old_GD':
            assert abs(transport['ideal_violation']-1/12)<1e-14
            assert transport['negative_RHS_terms']>0
            # Deliberately violate a moment domain: one finite valid moment row.
            bad=dict(point,Y_1=100.)
            e,ce=choose(block,bad);assert e['kind']=='moment_upper'
            for p,G in vectors:assert sum(v*F(p[k]) for k,v in e['rhs'].items()) <= 0
        facts.append(dict(tag=tag, integer_points=len(vectors), nonminimal_epigraph_checked=True,
            exact_validity_PASS=True, transport=transport))
    for q in (F(-1,10**18),F(1,10**18),F(-1,3),F(1,3),F(0)):
        assert F(downward(q)) <= q
    write(OUT/'qualification_oracle.json',dict(PASS=True,Optimize=0,Native_load=0,
        seconds=time.perf_counter()-start,fixtures=facts))
    print('PASS exact oracle, strict fixture, signs, fixed/omitted domains, moment fallback')


def solve(role, carrier, iteration):
    iteration=int(iteration); assert 1<=iteration<=3
    folder, old, block, oldpoint = inherited(role,carrier)
    if iteration==1:
        source=folder/'model.mps';point=oldpoint;prior=[]
    else:
        parent=OUT/'LP'/f'{role}_{carrier}'/f'iteration{iteration-1}'
        previous=read(parent/'result.json');assert previous['qualified']
        source=parent/'model.mps';point=json.loads(gzip.decompress((parent/'solution.json.gz').read_bytes()))
        assert sha(source)==previous['model_SHA'];prior=read(parent/'rows.json')['all_rows']
    target=OUT/'LP'/f'{role}_{carrier}'/f'iteration{iteration}'
    target.mkdir(parents=True,exist_ok=False)
    start=time.perf_counter()
    exact, certificate=choose(block,point)
    row, transport=compile_row(exact,point,f'r148_shared_S_{iteration}')
    assert transport['transported_violation']>1e-8,transport
    write(target/'construction.json',dict(certificate=certificate,transport=transport,
        input_point_SHA=sha(folder/'solution.json.gz') if iteration==1 else sha(parent/'solution.json.gz'),
        input_model_SHA=sha(source), new_row=row))
    rows=prior+[row];write(target/'rows.json',dict(all_rows=rows,new_row=row))
    # Load only inside the metered solve process after construction.
    from round100_gurobi_runtime import gp,binding
    identity=binding();assert identity['sha256']==DLL_SHA
    kernel=ctypes.WinDLL('kernel32',use_last_error=True);kernel.GetCurrentProcess.restype=ctypes.c_void_p
    kernel.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t]
    assert kernel.SetProcessAffinityMask(kernel.GetCurrentProcess(),4)
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Threads',1);env.setParam('Seed',0);env.start()
        with gp.read(str(source),env=env) as model:
            assert not model.IsMIP
            before=semantics(model); names={v.VarName for v in model.getVars()};oldrows={c.ConstrName for c in model.getConstrs()}
            baseline_check=residual(model,point)
            assert max(baseline_check['constraints'],baseline_check['bounds'])<=1e-6
            if iteration==1:assert abs(baseline_check['objective']-old['L'])<1e-8
            assert all(model.getVarByName(k).LB>=0 and model.getVarByName(k).UB<=1 for k in exact['rhs'])
            counts=dict(rows=model.NumConstrs,columns=model.NumVars,nonzeros=model.NumNZs)
            add_rows(model,[row],gp)
            assert semantics(model,names,oldrows)==before
            model.write(str(target/'model.mps'))
        with gp.read(str(target/'model.mps'),env=env) as model:
            assert semantics(model,names,oldrows)==before
            for r in rows:
                con=model.getConstrByName(r['name']);e=model.getRow(con)
                assert con.Sense==r['sense'] and con.RHS==r['rhs']
                assert {e.getVar(i).VarName:e.getCoeff(i) for i in range(e.size())}==r['terms']
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
            remaining,rcert=choose(block,newpoint);_,rtransport=compile_row(remaining,newpoint,'not_added')
            # Numerical dual diagnostics use ordinary R134 tolerances. A tiny
            # reduced cost on an infinite-bound column is reported separately;
            # this is not an exact rational dual certificate.
            dual=model.ObjCon+math.fsum(con.Pi*con.RHS for con in model.getConstrs())
            infinite_rc=[]
            for v in model.getVars():
                bound=v.LB if v.RC>=0 else v.UB
                if abs(bound)<gp.GRB.INFINITY:dual+=v.RC*bound
                else:infinite_rc.append(abs(v.RC))
            result=dict(role=role,carrier=carrier,iteration=iteration,old_L=old['L'],L=model.ObjVal,
                gain=model.ObjVal-old['L'],previous_objective=baseline_check['objective'],
                incremental_gain=model.ObjVal-baseline_check['objective'],g=newpoint['G'],
                weighted_penalty=model.ObjVal-newpoint['G'],Status=model.Status,
                numerical_dual_objective=dual,numerical_primal_dual_gap=model.ObjVal-dual,
                infinite_bound_adverse_reduced_cost=max(infinite_rc or [0.]),
                qualified_LP_bound=model.ObjVal,exact_rational_optimality_certificate=False,
                qualified=True,quality=quality,residual=check,baseline_residual=baseline_check,
                before=counts,rows=model.NumConstrs,columns=model.NumVars,nonzeros=model.NumNZs,
                added_rows_total=len(rows),new_row_nonzeros=len(row['terms']),
                construction_seconds=construction,oracle_seconds=certificate['seconds'],
                optimize_wall=elapsed,Runtime=model.Runtime,Work=model.Work,iterations=model.IterCount,
                Seed=0,Threads=1,affinity_mask=4,model_SHA=sha(target/'model.mps'),
                solution_SHA=sha(target/'solution.json.gz'),source_model_SHA=sha(source),
                source_fixed_science=SCIENCE146,original_semantics_exactly_retained=True,
                actual_Native_row_readback=True,transport=transport,
                remaining_separation=rtransport,remaining_moment_slacks=rcert['moments'],
                added_row_activities=[dict(name=r['name'],violation=activity(r,newpoint)) for r in rows],
                no_variables_fixed_to_old_point=True,LP_Optimize=1,Native=identity,
                helper_SHA={f:sha(ROOT/'scripts'/f) for f in ['round148_math.py','round148_lp.py','round148_common.py']})
            write(target/'result.json',result)
    print(json.dumps({k:result[k] for k in ['role','carrier','iteration','old_L','L','gain','Runtime','remaining_separation']}),flush=True)


def run(action,*args):
    configure()
    if action=='qualify':
        assert metered('qualification_oracle','diagnostic',[PYTHON,'-B',__file__,'qualify'],reservation=120,timeout=150)==0
    elif action=='first':
        for role,carrier in ROLES:
            label=f'LP_{role}_{carrier}_1'
            assert metered(label,'diagnostic',[LP_PYTHON,'-B',__file__,'solve',role,carrier,1],reservation=180,timeout=240)==0
    elif action=='extra':
        role,carrier,iteration=args
        assert metered(f'LP_{role}_{carrier}_{iteration}','diagnostic',
            [LP_PYTHON,'-B',__file__,'solve',role,carrier,iteration],reservation=180,timeout=240)==0
    else:raise ValueError(action)


if __name__=='__main__':
    if sys.argv[1]=='screen':screen()
    elif sys.argv[1]=='solve':solve(*sys.argv[2:])
    elif sys.argv[1]=='qualify':qualify()
    elif sys.argv[1]=='run':run(*sys.argv[2:])
    else:run(*sys.argv[1:])
