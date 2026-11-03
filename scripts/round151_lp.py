"""Saved pure-B roots: finite same-domain C then P LP, never re-solve B/C20."""
import csv,gzip
import round108_reader as parser
from round143_lp import semantics,residual
from round145_lp import add_rows,save_gz
from round150_lp import affinity,readback
from round151_math import compiled,scope_from_model,rows
from round151_common import *
def prepare():
    configure()
    from round100_gurobi_runtime import gp,binding
    native=binding();assert native['sha256']==DLL_SHA;affinity()
    reuse=read(OUT/'reuse_index.json');facts=[]
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Threads',1);env.setParam('Seed',0);env.start()
        for record in reuse['domains']:
            tick=time.perf_counter();role=record['role'];d=WORK/'restore/round151-inherited'/role
            source=d/'external/models/L0_epoch_0_generation_1.lp'
            assert sha(source)==next(r['SHA256'] for r in record['members'] if r['member'].endswith(source.name))
            source_text=source.read_text(encoding='utf-8');assert all(x not in source_text for x in ['r146_GD_','r149_PF_','r151_cap_'])
            panel=next(g['launch']['panel'] for g in read(ROOT/'results/unified_exact_round137/matrix_frozen.json')['groups'] if g['launch']['id']==role)
            scope=scope_from_model(parser.lp_model(source),max(0,panel['total_initial']-sum(panel['Q_vector'])),panel['total_initial'])
            ar=compiled(scope,OUT/'LP/arithmetic'/f'{role}.json')
            assert rows(ar)==ar['rows']
            crows,prows=rows(ar,mode='conditional'),rows(ar,mode='uniform')
            status=read(d/'external/round127_root_lp_status.json');assert status['complete'] and status['extra_Optimize']==0
            with (d/'external/round127_root_lp.csv').open(encoding='utf-8-sig',newline='') as f:
                point={r['name']:float(r['value']) for r in csv.DictReader(f)}
            obs=[v['payload'] for v in read(d/'observations.json')]
            quality=next(v for v in obs if v['kind']=='native_quality')
            # Native LP quality is carried by the bound event; MIP-style ObjVal
            # can be null for this LP export. The full saved point is checked.
            bound=next(v for v in obs if v['kind']=='bound' and v['call']==quality['call'])
            oldL=bound['native_bound']
            variants=[]
            with gp.read(str(source),env=env) as model:
                integer_types=sum(v.VType!='C' for v in model.getVars())
                for v in model.getVars():v.VType='C'
                model.update();assert not model.IsMIP and all(v.VType=='C' for v in model.getVars())
                assert set(point)=={v.VarName for v in model.getVars()} and len(point)==status['columns']
                before=semantics(model);baseline=residual(model,point)
                assert max(baseline['constraints'],baseline['bounds'])<=1e-6,baseline
                assert abs(baseline['objective']-oldL)<1e-8
                names=set(point);oldrows={c.ConstrName for c in model.getConstrs()}
                counts=dict(columns=model.NumVars,rows=model.NumConstrs,nonzeros=model.NumNZs)
                violations={tag:[math.fsum(a*point[k] for k,a in r['terms'].items()) for r in rr] for tag,rr in [('P',prows),('C',crows)]}
                if role=='N-B35-S':
                    for tag,rr in [('C',crows),('P',prows)]:
                        target=OUT/'LP'/f'{role}_{tag}';target.mkdir(parents=True,exist_ok=False)
                        with model.copy() as variant:
                            add_rows(variant,rr,gp);assert semantics(variant,names,oldrows)==before
                            variant.write(str(target/'model.mps'))
                        with gp.read(str(target/'model.mps'),env=env) as variant:
                            assert semantics(variant,names,oldrows)==before
                            assert not variant.IsMIP and variant.NumVars==counts['columns']
                            assert variant.NumConstrs==counts['rows']+len(rr)
                            readback(variant,rr)
                            after=dict(columns=variant.NumVars,rows=variant.NumConstrs,nonzeros=variant.NumNZs)
                        write(target/'rows.json',rr)
                        construction=dict(role=role,variant=tag,source_model_SHA=sha(source),model_SHA=sha(target/'model.mps'),
                            scope=scope,before=counts,after=after,old_B_L=oldL,baseline_residual=baseline,
                            original_integer_columns_relaxed=integer_types,all_variables_free=True,old_semantics_retained=True,
                            old_optimal_quality=quality,source_fixed_science=SCIENCE150,
                            actual_added_rows=len(rr),actual_added_nonzeros=sum(len(r['terms']) for r in rr),
                            old_point_violation_count=sum(v>1e-8 for v in violations[tag]),old_point_max_violation=max(violations[tag] or [0.]),
                            construction_seconds=time.perf_counter()-tick,Native=native,baseline_Optimize_new=0)
                        write(target/'construction.json',construction)
                        variants.append(dict(variant=tag,model_SHA=sha(target/'model.mps'),rows_SHA=sha(target/'rows.json'),construction_SHA=sha(target/'construction.json')))
            facts.append(dict(role=role,scope=scope,old_B_L=oldL,baseline_residual=baseline,old_qualified_numeric_point=True,
                actual_C_rows=len(crows),actual_P_rows=len(prows),state_count=len(ar['states']),
                conditional_stricter_than_uniform=sum(s['transported_beta']<ar['transported_beta0'] for s in ar['states']),
                uniform_only_states=sum(s['transported_beta']==ar['transported_beta0'] for s in ar['states']),
                violation_count={k:sum(v>1e-8 for v in values) for k,values in violations.items()},
                max_violation={k:max(values or [0.]) for k,values in violations.items()},
                C20_new_LP_unnecessary=role=='N-C20-U' and max(violations['C'] or [0.])<=1e-6,
                variants=variants,arithmetic_SHA=sha(OUT/'LP/arithmetic'/f'{role}.json')))
    write(OUT/'LP_frozen.json',dict(UTC=utc(),domains=facts,LP_cap=120,Seed=0,Threads=1,
        maximum_new_Optimize=2,baseline_new_Optimize=0,C20_new_Optimize=0,
        LP_script_SHA=sha(__file__),math_SHA=sha(ROOT/'scripts/round151_math.py'),
        initially_solve='C',P_only_if_C_has_distinguishable_gain=True,actual_C_subset_P_subset_B=True))
    print(json.dumps(facts,default=str))
def solve(tag):
    configure();assert tag in ['C','P']
    frozen=read(OUT/'LP_frozen.json');assert frozen['LP_script_SHA']==sha(__file__)
    assert frozen['math_SHA']==sha(ROOT/'scripts/round151_math.py')
    if tag=='P':
        c=read(OUT/'LP/N-B35-S_C/result.json');assert c['qualified'] and c['L']-c['old_B_L']>1e-8
    item=next(v for d in frozen['domains'] if d['role']=='N-B35-S' for v in d['variants'] if v['variant']==tag)
    target=OUT/'LP'/f'N-B35-S_{tag}';assert not (target/'call.json').exists(),'Never reenter an Optimize'
    assert sha(target/'model.mps')==item['model_SHA'] and sha(target/'rows.json')==item['rows_SHA']
    old=read(target/'construction.json');assert sha(target/'construction.json')==item['construction_SHA']
    from round100_gurobi_runtime import gp,binding
    native=binding();assert native['sha256']==DLL_SHA;affinity()
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Threads',1);env.setParam('Seed',0);env.start()
        with gp.read(str(target/'model.mps'),env=env) as model:
            assert not model.IsMIP and all(v.VType=='C' for v in model.getVars())
            readback(model,read(target/'rows.json'))
            model.Params.TimeLimit=120;model.Params.FeasibilityTol=1e-6;model.Params.OptimalityTol=1e-6
            model.Params.OutputFlag=1;model.Params.LogToConsole=0;model.Params.LogFile=str(target/'native.log')
            write(target/'call.json',dict(UTC=utc(),model_SHA=item['model_SHA'],Native=native,LP_Optimize=1,cap=120,Seed=0,Threads=1))
            tick=time.perf_counter();model.optimize();elapsed=time.perf_counter()-tick
            write(target/'return.json',dict(UTC=utc(),Status=model.Status,Runtime=model.Runtime,Work=model.Work,optimize_wall=elapsed))
            result=dict(variant=tag,Status=model.Status,qualified=False,old_B_L=old['old_B_L'],model_SHA=item['model_SHA'],
                Runtime=model.Runtime,Work=model.Work,iterations=model.IterCount,optimize_wall=elapsed,Seed=0,Threads=1,
                baseline_Optimize_new=0,LP_Optimize=1,all_variables_free=True,exact_rational_optimality_certificate=False,
                actual_added_rows=old['actual_added_rows'],actual_added_nonzeros=old['actual_added_nonzeros'],Native=native)
            if model.SolCount:
                point={v.VarName:v.X for v in model.getVars()};save_gz(target/'solution.json.gz',point)
                quality={k:model.getAttr(k) for k in ['ConstrVio','BoundVio','DualVio','ConstrResidual','DualResidual','ComplVio']}
                check=residual(model,point);dual=model.ObjCon+math.fsum(c.Pi*c.RHS for c in model.getConstrs())
                terms=[];infinite=[]
                for v in model.getVars():
                    bound=v.LB if v.RC>=0 else v.UB
                    if abs(bound)<gp.GRB.INFINITY:terms.append(v.RC*bound)
                    else:infinite.append(abs(v.RC))
                dual+=math.fsum(terms)
                save_gz(target/'dual.json.gz',dict(Pi={c.ConstrName:c.Pi for c in model.getConstrs()},RC={v.VarName:v.RC for v in model.getVars()}))
                result.update(L=model.ObjVal,g=point['G'],weighted_penalty=model.ObjVal-point['G'],quality=quality,residual=check,
                    numerical_dual_objective=dual,numerical_primal_dual_gap=model.ObjVal-dual,
                    infinite_bound_adverse_reduced_cost=max(infinite or [0.]),gain_over_B=model.ObjVal-old['old_B_L'],
                    qualified=model.Status==gp.GRB.OPTIMAL and max(quality.values())<=1e-6 and max(check['constraints'],check['bounds'])<=1e-6,
                    solution_SHA=sha(target/'solution.json.gz'),dual_SHA=sha(target/'dual.json.gz'))
            write(target/'result.json',result)
    print(json.dumps(result),flush=True)
if __name__=='__main__':
    configure()
    if sys.argv[1]=='prepare':prepare()
    elif sys.argv[1]=='solve':solve(sys.argv[2])
    elif sys.argv[1]=='meter_prepare':assert metered('LP_prepare_v2','diagnostic',[LP_PYTHON,'-B',__file__,'prepare'],180,240)==0
    elif sys.argv[1]=='run':assert metered('LP_'+sys.argv[2],'diagnostic',[LP_PYTHON,'-B',__file__,'solve',sys.argv[2]],180,240)==0
