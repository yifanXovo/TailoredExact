"""Two fixed root domains, three continuous LP layers; never H or an integer MIP."""
from round134_common import *
from round134_count_bound import count_coefficients,downward
from fractions import Fraction as F
import collections,gzip,re,shutil

def compile_exporter():
    from round134_build import FLAGS,SYSTEM,objects
    from round130_common import ARCHIVE
    target=BUILD/'Round134RootExport.exe'
    assert metered('root_exporter_compile','E',[COMPILER,*FLAGS,ROOT/'scripts/round130_export.cpp',
        *objects(),ARCHIVE,*SYSTEM,'-o',target],reservation=120,timeout=120)==0
    write(OUT/'math/root_exporter_build.json',dict(UTC=utc(),PE=str(target),PE_SHA=sha(target),
        source='scripts/round130_export.cpp',source_SHA=sha(ROOT/'scripts/round130_export.cpp'),
        linked_object_SHA={str(p):sha(p) for p in objects()},archive_SHA=sha(ARCHIVE),
        compiler_SHA=sha(COMPILER),Optimize=0,source_production_matrix_writer_unchanged=True))

def prepare():
    import round108_reader as core
    freeze=read(ROOT/'results/unified_exact_round132/D_argv_freeze.json');roots=[]
    for role,index in [('K-20-S',4),('K-35-U',10)]:
        source=next(l for l in freeze['plans'][index]['launches'] if l['method']=='S2')
        assert source['id']==role and source['seed']==0
        d=Path(source['destination']);observations=read(d/'observations.json')
        call=next(x['payload'] for x in observations if x['payload']['kind']=='call')
        witness=next(x['payload'] for x in observations if x['payload']['kind']=='witness' and x['payload']['call']==0)
        assert call['lower_g']==0 and call['upper_g']==call['cutoff']
        p=source['panel'];physical=core.full_fleet(ROOT,p,copy_dict(witness))
        assert abs(physical['F']-call['cutoff'])<=1e-12
        old=Path(call['model_path']);assert sha(old)==call['model_sha256']
        folder=OUT/'math/roots'/role;folder.mkdir(parents=True,exist_ok=False)
        output=folder/'current_export'
        args=[BUILD/'Round134RootExport.exe',ROOT/p['input_path'],p['T_seconds'],
            call['lower_g'],call['upper_g'],call['cutoff'],'ms2',output]
        assert metered('root_export_'+role,'E',args,reservation=60,timeout=60)==0
        current=output/'original.lp'
        before,after=core.lp_model(old),core.lp_model(current)
        assert before['bounds']==after['bounds'] and before['types']==after['types']
        assert before==after,'current S2 root differs from fixed historical root: inspect before any LP'
        assert not any(not terms and sense=='<=' and rhs<0 for terms,sense,rhs in after['rows'])
        final=read(d/'result.json');best=core.full_fleet(ROOT,p,copy_dict(final))
        snapshot=dict(role=role,panel=p,root_scope=call,old_source_pin='52b02252ba47e8228b73e071d6ed692385a4f816',
            old_carrier=f'campaign_D_group{index+1:02}.zip',
            old_matrix_SHA=sha(old),current_matrix_SHA=sha(current),
            exact_current_and_old_canonical_matrix_equal=True,
            current_export_build=read(output/'build.json'),
            old_cutoff_own_startup_witness=witness,startup_physical=physical,
            archived_best_physical=best,old_result_SHA=sha(d/'result.json'),
            current_source_commit=read(OUT/'candidate_manifest.json')['source_commit'],
            production_change_has_no_matrix_change=True,
            no_new_H_no_MIP_no_cutoff_selection=True,all_stations_included=True,
            layers=['S2_LP','S2_LP_PLUS_OLD_STATE_PENALTY','S2_LP_PLUS_OLD_STATE_PENALTY_PLUS_TC'],
            per_layer_LP_cap_seconds=120,comparison_is_loaded_matrix_numeric_not_original_rational_proof=True)
        write(folder/'scope.json',snapshot);roots.append(dict(role=role,scope_SHA=sha(folder/'scope.json'),matrix_SHA=sha(current)))
    write(OUT/'math/root_plan.json',dict(UTC=utc(),roots=roots,positions=6,
        order=[(r['role'],layer) for r in roots for layer in range(3)],
        created_before_root_LP_results=True,no_integer_solve=True,TC_production=False))

def copy_dict(v):
    import copy
    return copy.deepcopy(v)

def construction(model,p):
    tick=time.perf_counter();variables={v.VarName:v for v in model.getVars()}
    supports=collections.defaultdict(list)
    for name in variables:
        m=re.fullmatch(r'state_(\d+)_(\d+)',name)
        if m:supports[int(m[1])].append(int(m[2]))
    assert set(supports)==set(range(1,p['V']+1))
    ratio={};rows={}
    for con in model.getConstrs():
        if con.Sense!='=' or con.RHS!=0:continue
        row=model.getRow(con)
        if row.size()!=2:continue
        terms={row.getVar(j).VarName:F(row.getCoeff(j)) for j in range(row.size())}
        for name,coef in terms.items():
            match=re.fullmatch(r'r_(\d+)',name)
            if not match:continue
            i=int(match[1]);stock=f'Y_{i}'
            if stock in terms and coef>0 and terms[stock]<0:
                assert coef==1,'record a mapping before using a differently scaled ratio row'
                ratio[i]=-terms[stock];rows[i]=dict(name=con.ConstrName,coefficients={n:str(a) for n,a in terms.items()},RHS='0')
    assert set(ratio)==set(supports)
    B=p['total_initial'];tc=count_coefficients(supports,ratio,B)
    assert not tc['inventory_domain_infeasible']
    coeff={f'state_{i}_{y}':dict(exact=str(value),written=downward(value),written_exact=str(F(downward(value)))) for (i,y),value in tc['coefficients'].items() if value}
    penalty={f'state_{i}_{y}':dict(exact=str(abs(ratio[i]*y-1)),written=downward(abs(ratio[i]*y-1)),
        written_exact=str(F(downward(abs(ratio[i]*y-1))))) for i,ys in supports.items() for y in ys}
    return dict(loaded_ratio_rows=rows,ratio_coefficients={i:str(v) for i,v in ratio.items()},
        supports=dict(supports),B=B,thresholds=tc['thresholds'],minima=tc['minima'],R=tc['R'],
        TC_coefficients=coeff,old_penalty_coefficients=penalty,seconds=time.perf_counter()-tick,
        threshold_decisions_exact=True,all_written_coefficients_rounded_down=True,
        ideal_ratios_not_mixed_with_loaded_coefficients=True)

def solve(role,layer):
    assert layer in range(3)
    runtime=read(OUT/'math/root_runtime_repair.json')
    assert sha(sys.executable)==runtime['python_SHA256']
    # This import deliberately happens only in an explicit serial LP process.
    from round100_gurobi_runtime import gp,binding
    folder=OUT/'math/roots'/role;scope=read(folder/'scope.json');p=scope['panel']
    target=folder/f'layer{layer}';target.mkdir(exist_ok=False)
    tick=time.perf_counter();identity=binding();assert identity['sha256']==DLL_SHA
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        with gp.read(str(folder/'current_export/original.lp'),env=env) as model:
            model.Params.Threads=1;model.Params.Seed=0;model.Params.Presolve=-1
            model.Params.TimeLimit=120;model.Params.FeasibilityTol=1e-6;model.Params.OptimalityTol=1e-6
            model.Params.LogFile=str(target/'native.log')
            model.Params.OutputFlag=1;model.Params.LogToConsole=0
            for v in model.getVars():v.VType=gp.GRB.CONTINUOUS
            model.update();variables={v.VarName:v for v in model.getVars()}
            assert model.IsMIP==0 and model.ModelSense==1
            ctor=construction(model,p);write(target/'construction.json',ctor)
            before=dict(rows=model.NumConstrs,columns=model.NumVars,nonzeros=model.NumNZs)
            added=[]
            if layer>=1:
                for i,ys in ctor['supports'].items():
                    i=int(i);terms={f'state_{i}_{y}':ctor['old_penalty_coefficients'][f'state_{i}_{y}']['written'] for y in ys}
                    name=f'r134_old_state_penalty_{i}'
                    model.addConstr(variables[f'e_{i}']>=gp.quicksum(c*variables[n] for n,c in terms.items()),name=name)
                    added.append(dict(name=name,sense='>=',lhs={f'e_{i}':1},rhs_coefficients=terms))
            if layer==2:
                terms={n:c['written'] for n,c in ctor['TC_coefficients'].items()}
                h=[f'h_{i}_{j}' for i in range(1,p['V']+1) for j in range(i+1,p['V']+1)]
                model.addConstr(gp.quicksum(variables[n] for n in h)>=gp.quicksum(c*variables[n] for n,c in terms.items()),name='r134_TC')
                added.append(dict(name='r134_TC',sense='>=',lhs={n:1 for n in h},rhs_coefficients=terms))
            model.update();assert model.NumVars==before['columns'] and model.IsMIP==0
            write(target/'added_rows.json',added)
            construction_end=time.perf_counter();model.optimize();solved=time.perf_counter()
            write(target/'native_return.json',dict(UTC=utc(),Status=model.Status,Runtime=model.Runtime,
                Work=model.Work,SolCount=model.SolCount,IsMIP=model.IsMIP,Optimize=1,
                model_released_by_context_on_exit=True))
            quality={}
            for name in ('ConstrVio','BoundVio','DualVio','ConstrResidual','DualResidual','ComplVio'):
                try:quality[name]=model.getAttr(name)
                except (gp.GurobiError,AttributeError):quality[name]=None
            primal=bool(model.SolCount)
            value=model.ObjVal if primal else None
            native_bound=None
            try:native_bound=model.ObjBound
            except (gp.GurobiError,AttributeError):pass
            if native_bound is not None and (not math.isfinite(native_bound) or abs(native_bound)>1e90):native_bound=None
            optimal=model.Status==gp.GRB.OPTIMAL
            lower=value if optimal else native_bound
            vectors={v.VarName:v.X for v in model.getVars()} if primal else {}
            if primal:
                with gzip.open(target/'solution.json.gz','wt',encoding='utf-8') as stream:json.dump(vectors,stream,separators=(',',':'))
            residuals=[]
            for row in added:
                if not primal:break
                lhs=math.fsum(c*vectors[n] for n,c in row['lhs'].items())
                rhs=math.fsum(c*vectors[n] for n,c in row['rhs_coefficients'].items())
                residuals.append(dict(name=row['name'],lhs=lhs,rhs=rhs,signed_slack=lhs-rhs))
            record=dict(UTC=utc(),role=role,layer=layer,scope_SHA=sha(folder/'scope.json'),
                source_matrix_SHA=sha(folder/'current_export/original.lp'),construction_SHA=sha(target/'construction.json'),
                native_identity=identity,LP_only=True,MIP_Optimize=0,LP_Optimize=1,Status=model.Status,
                optimal=optimal,primal_objective=value,numerical_lower=lower,
                native_ObjBound=native_bound,primal_value_not_used_as_lower_without_OPTIMAL=True,
                qualification='NUMERICAL_OPTIMAL_LP' if optimal else 'BOUND_ONLY' if lower is not None else 'UNKNOWN',
                rigorous_rational_lower_certificate=False,quality=quality,added_row_residuals=residuals,
                before=before,after=dict(rows=model.NumConstrs,columns=model.NumVars,nonzeros=model.NumNZs),
                Work=model.Work,nodes=model.NodeCount,iterations=model.IterCount,barrier_iterations=model.BarIterCount,
                solver_runtime=model.Runtime,construct_and_load_seconds=construction_end-tick,
                optimize_wall_seconds=solved-construction_end,total_before_final_output_seconds=time.perf_counter()-tick,
                same_parameters_same_domain_independent_continuous_model=True)
            write(target/'result.json',record)
    print(json.dumps(dict(role=role,layer=layer,status=record['qualification'],L=lower,quality=quality)))

def run():
    plan=read(OUT/'math/root_plan.json')
    runtime=read(OUT/'math/root_runtime_repair.json');python=Path(runtime['python'])
    assert sha(python)==runtime['python_SHA256']
    for role,layer in plan['order']:
        if (OUT/'math/roots'/role/f'layer{layer}/result.json').exists():continue
        label=f'root_{role}_layer{layer}'
        if (OUT/'fees'/label).exists():
            assert label==runtime['failed_label']
            assert read(OUT/'fees'/label/'receipt.json')['exit_code']==1
            assert not (OUT/'math/roots'/role/f'layer{layer}').exists(),'existing native work must be inspected, never automatically repeated'
            label+='_runtime02'
        assert metered(label,'E',[python,ROOT/'scripts/round134_roots.py','solve',role,layer],reservation=180,timeout=360)==0

if __name__=='__main__':
    action=sys.argv[1]
    if action=='compile':compile_exporter()
    elif action=='prepare':
        tick=time.perf_counter();before=budget()['by_category']['E']
        try:prepare()
        finally:
            # Parent parsing/copy/comparison work only; nested zero-Optimize
            # exporter outers have already been metered and are subtracted.
            nested=budget()['by_category']['E']-before
            path=OUT/'infra/external_costs.json';cost=read(path)
            cost['processes'].append(dict(kind='E',label='fixed_root_preparation_nonnested',
                outer_seconds=max(0.,time.perf_counter()-tick-nested),nested_exporter_seconds_excluded=nested,native_Optimize=0))
            write(path,cost)
    elif action=='solve':solve(sys.argv[2],int(sys.argv[3]))
    elif action=='run':run()
