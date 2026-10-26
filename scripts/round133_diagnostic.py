"""Fixed Round133 C diagnostics; importing or preparing starts no native work.

The primary agent alone starts each run through round133_common.metered.
No C incumbent, bound, matrix state or parameter cache is supplied to D.
"""
from pathlib import Path
from fractions import Fraction as F
import argparse, ast, copy, csv, gzip, hashlib, json, math, os, re, subprocess, sys, time
import round133_common as C

ROOT, OUT = C.ROOT, C.OUT
PLAN = OUT/'plans/C_diagnostics.json'
OLD = Path('E:/codes/ExactEBRP-work/worktrees/round132')
OLD_REL = Path('results/unified_exact_round132/campaign/C_group03/raw/02_SC-B20-S_S0_R1_S2R')
RESEARCH_SHA='eac4e778cacb316c61928d4a6f1e4c90c8397cc94e0dc528695773703e98cce2'
MODEL_SHA='028c942830f3456b55a0a40293044979980c904c3122f75cd9bb67e760855fc9'
INPUT_SHA='70ebad164c3da58c52d0ad7fce651a6f4d90f54323a939d6c109a17eaffb8b3c'

def relative(path): return Path(path).relative_to(ROOT).as_posix()

def prepare():
    started=time.perf_counter();assert not PLAN.exists(),'do not overwrite preregistration'
    original_freeze=ROOT/'results/unified_exact_round132/C_argv_freeze.json'
    frozen=C.read(original_freeze)
    launches=[launch for group in frozen['plans'] for launch in group['launches']
              if launch['panel']['id']=='SC-B20-S' and launch['seed']==0 and launch.get('expression')=='geom']
    assert len(launches)==1;old=launches[0]
    assert old['method']=='S2R' and old['cap_seconds']==1200
    assert C.sha(C.ORIGINAL_RESEARCH)==RESEARCH_SHA and C.sha(C.DLL)==C.DLL_SHA
    archived_launch=C.read(OLD/OLD_REL/'launch.json')
    assert old['command']==archived_launch['command'] and old['panel']==archived_launch['panel']
    scope=C.read(OLD/OLD_REL/'journal/event_5.json')
    assert scope['kind']=='call' and scope['call']==2 and scope['model_sha256']==MODEL_SHA
    deps=OUT/'dependencies/C';deps.mkdir(parents=True,exist_ok=True)
    input_path=deps/'SC-B20-S.txt'
    inp=C.git('show',C.BASE+':'+old['panel']['input_path'])
    assert hashlib.sha256(inp).hexdigest()==INPUT_SHA==old['panel']['input_sha256']
    if input_path.exists():assert input_path.read_bytes()==inp
    else:input_path.write_bytes(inp)
    model_path=deps/'SC-B20-S_S0_GEOM_terminal.lp'
    old_model=OLD/OLD_REL/'external/models/L0_epoch_0_generation_1.lp'
    model=old_model.read_bytes();assert hashlib.sha256(model).hexdigest()==MODEL_SHA
    if model_path.exists():assert model_path.read_bytes()==model
    else:model_path.write_bytes(model)
    panel=copy.deepcopy(old['panel']);panel['input_path']=panel['instance_path']=relative(input_path)
    r2_dest=OUT/'diagnostics/C_R2_original_GEOM'
    command=[];old_dest=old['destination']
    for argument in old['command']:
        command.append(argument.replace(old_dest,str(r2_dest)))
    command[0]=str(C.ORIGINAL_RESEARCH)
    command[command.index('--input')+1]=relative(input_path)
    # All non-path arguments must remain exactly as in the original launch.
    path_flags={'--input','--out','--log','--process-phase-ledger','--external-gini-artifact-dir',
                '--primal-heuristic-generation-log','--progress-log','--native-evidence-dir'}
    allowed={0}|{old['command'].index(flag)+1 for flag in path_flags}
    assert all(i in allowed or a==b for i,(a,b) in enumerate(zip(old['command'],command)))
    assert len(old['command'])==len(command)
    settings={k:scope['settings'][k] for k in ['Threads','Seed','Presolve','MIPGap','MIPGapAbs',
                                             'FeasibilityTol','IntFeasTol','OptimalityTol']}
    settings.update(MIPFocus=old['configuration']['MIPFocus'],Cuts=old['configuration']['Cuts'])
    start_receipt=C.read(OLD/OLD_REL/'external/native_logs/L0_terminal_mip.gurobi.log.round68.start.json')
    native_limit=start_receipt['native_deadline_remaining_at_optimize']
    assert native_limit==1168.6377467
    plan=dict(schema='round133-finite-C-preregistration-v1',UTC=C.utc(),status='FROZEN_BEFORE_NEW_NATIVE',
        source_commit=C.BASE,diagnostic_script=relative(Path(__file__)),script_SHA256=C.sha(__file__),
        category='C',category_cap_seconds=7200,experimental_and_related_total_cap_seconds=39600,
        newly_reserved_caps_seconds=2400,unused_caps_not_reassigned=True,
        diagnostic_only=True,no_formal_performance_replacement=True,no_C_to_D_information=True,
        serial_native=True,threads=1,mip_threads=1,affinity_mask=4,
        primary_agent_is_unique_meter_starter=True,
        native_library=dict(path=str(C.DLL),SHA256=C.DLL_SHA),
        original_PE=dict(path=str(C.ORIGINAL_RESEARCH),SHA256=RESEARCH_SHA),
        source_freeze=dict(path=relative(original_freeze),SHA256=C.sha(original_freeze),
                           old_launch=archived_launch,old_scope=scope),
        dependencies=[dict(path=relative(input_path),SHA256=INPUT_SHA,bytes=len(inp),
            original_commit=C.BASE,original_path=old['panel']['input_path']),
            dict(path=relative(model_path),SHA256=MODEL_SHA,bytes=len(model),original_commit=C.BASE,
                 original_carrier='results/unified_exact_round132/artifacts/campaign_C_group03.zip',
                 original_member=(OLD_REL/'external/models/L0_epoch_0_generation_1.lp').as_posix())],
        official_readout_references=[
            'https://docs.gurobi.com/projects/optimizer/en/current/reference/numericcodes/callbacks.html',
            'https://docs.gurobi.com/projects/optimizer/en/current/reference/attributes/quality.html'],
        panel=panel,
        C_R1=dict(status='NOT_NEEDED_INDEPENDENT_REVIEW_ACCEPTED',new_Optimize=0,cap_seconds=2400,
            basis='review/design_review.md and complete rational actual-matrix/own-physical counterexample',
            receipt='review/directed_old_evidence_receipt.json',
            scope='original native call remains REJECTED; internal numerical cause UNKNOWN'),
        C_R2=dict(status='REGISTERED_NOT_STARTED',cap_seconds=1200,
            inherited_external_hard_stop_seconds=old['hard_stop_seconds'],
            original_full_workflow=True,command=command,destination=relative(r2_dest),
            question='Does the unchanged original GEOM workflow again show native OPTIMAL versus physical gap?',
            changed_factors='input/output locations only; independently paid original complete H and Start',
            reads='original result/log/journal/ledger/Start/physical output; no final native vector hook in original PE',
            exit='one complete workflow only; ordinary nonreproduction/open/Lose does not authorize rerun'),
        C_R3=dict(status='REGISTERED_NOT_STARTED',cap_seconds=1200,category_R3_cap_seconds=3600,
            destination=relative(OUT/'diagnostics/C_R3_GEOM_matrix_replay'),
            model=relative(model_path),model_SHA256=MODEL_SHA,settings=settings,
            native_time_limit_seconds=native_limit,Optimize_limit=1,Start_count=0,
            question='Separate reconstructed service/integrality drift from g/e epigraph and rounded-row residual propagation',
            hypotheses=['native raw p/d or integer-coordinate drift changes the reconstructed physical objective',
                        'native g/e or ratio rows understate recomputed objective while service/route maps remain valid',
                        'cold replay does not reproduce original mismatch; retained original cause stays unresolved'],
            changed_factors='one cold matrix replay through same-DLL gurobipy with observation callback; no H/LP reuse/Start',
            same='saved complete typed matrix, input, original numerical settings, Seed, one thread, DLL',
            differences_from_original='cold model state and observer overhead; diagnostic is not original production or a repair/performance arm',
            readout=['all native MIPSOL vectors and final vector in original column order',
                     'raw MIP/MIPSOL callback scalar stream with counts and order',
                     'loaded original matrix/columns/types/bounds/objective identity',
                     'ObjVal/ObjBoundC/status/quality attributes and complete parameter readback',
                     'unrounded native service, reconstructed physical routes/inventory/G/P/F, native g/e components',
                     'row residuals linked to objective components; unavailable quality fields explicit unknown'],
            exit='one Optimize or native/resource/error stop; preserve failure and do not retune or repeat'))
    plan['preparation_outer_seconds']=time.perf_counter()-started
    C.write(PLAN,plan)
    print(json.dumps(dict(plan=relative(PLAN),SHA256=C.sha(PLAN),Optimize=0,C_R2=1200,C_R3=1200)))

def require_plan():
    assert os.environ.get('ROUND133_METERED_PARENT_LABEL'),'primary agent must launch via the common outer meter'
    p=C.read(PLAN);assert C.sha(__file__)==p['script_SHA256'],'diagnostic source changed after freeze'
    assert C.sha(C.DLL)==p['native_library']['SHA256']==C.DLL_SHA
    for item in p['dependencies']:assert C.sha(ROOT/item['path'])==item['SHA256']
    return p

def affinity():
    if os.name=='nt':
        import ctypes
        kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        kernel.GetCurrentProcess.restype=ctypes.c_void_p
        kernel.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t]
        assert kernel.SetProcessAffinityMask(kernel.GetCurrentProcess(),4)

def run_r2():
    tick=time.perf_counter();p=require_plan();r=p['C_R2'];dest=ROOT/r['destination']
    assert C.sha(C.ORIGINAL_RESEARCH)==p['original_PE']['SHA256']
    dest.mkdir(parents=True,exist_ok=False);affinity()
    C.write(dest/'launch.json',dict(registration_SHA256=C.sha(PLAN),command=r['command'],UTC=C.utc()))
    stopped=False
    with (dest/'stdout.log').open('xb') as so,(dest/'stderr.log').open('xb') as se:
        child=subprocess.Popen(r['command'],cwd=ROOT,env=C.environment(),stdout=so,stderr=se)
        birth=C.process_birth(child.pid);assert birth
        identity=dict(pid=child.pid,parent_pid=os.getpid(),command=r['command'],**birth)
        C.write(dest/'PID.json',identity)
        try:child.wait(timeout=max(.01,r['inherited_external_hard_stop_seconds']-(time.perf_counter()-tick)))
        except subprocess.TimeoutExpired:
            stopped=True;C._kill_owned_tree(child,identity,dest)
    elapsed=time.perf_counter()-tick
    result=C.read(dest/'result.json') if (dest/'result.json').exists() else None
    summary={k:result.get(k) for k in ['status','objective','G','P','lower_bound','upper_bound',
        'strict_certified_original_problem','external_gini_tree_failure_reason',
        'external_gini_tree_certificate_rejection_reason','external_gini_tree_optimize_count']} if result else None
    C.write(dest/'completion.json',dict(UTC=C.utc(),return_code=child.returncode,outer_seconds=elapsed,
        full_workflow=True,original_PE=True,timeout=stopped,result_present=result is not None,
        result_summary=summary,final_native_vector='unknown; unchanged original PE does not expose it',
        no_rerun_authorized_by_nonreproduction=True,diagnostic_not_formal=True))
    print(json.dumps(dict(C_R2='COMPLETED' if result is not None else 'FAILED_OUTPUT_MISSING',seconds=elapsed,summary=summary)))
    return 0 if child.returncode==0 and result is not None else 1

def safe_attr(model,name):
    try:
        value=model.getAttr(name)
        if isinstance(value,float) and not math.isfinite(value):return dict(available=False,value=None,reason='nonfinite')
        return dict(available=True,value=value)
    except Exception as error:return dict(available=False,value=None,reason=type(error).__name__+':'+str(error))

def run_r3():
    tick=time.perf_counter();p=require_plan();r=p['C_R3'];dest=ROOT/r['destination']
    dest.mkdir(parents=True,exist_ok=False);affinity()
    C.write(dest/'launch.json',dict(registration_SHA256=C.sha(PLAN),UTC=C.utc(),request=r))
    # This is the only native import and only Optimize in the whole script.
    from round99_gurobi_runtime import gp,binding
    runtime=binding();assert runtime['sha256']==C.DLL_SHA
    callback_errors=[];counts=dict(MIP=0,MIPSOL=0);final=None
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',1);env.setParam('LogFile',str(dest/'native.log'));env.start()
        with gp.read(str(ROOT/r['model']),env=env) as model:
            for name,value in r['settings'].items():model.setParam(name,value)
            model.setParam('TimeLimit',r['native_time_limit_seconds']);model.update()
            readback={name:model.getParamInfo(name)[2] for name in r['settings']}
            assert readback==r['settings']
            variables=model.getVars();names=model.getAttr('VarName',variables)
            assert len(names)==len(set(names)) and model.NumStart==0
            columns=[dict(name=v.VarName,type=v.VType,lower=v.LB,upper=v.UB,objective=v.Obj) for v in variables]
            # Bind the actual loaded matrix, not only its input text.
            matrix=[]
            for row in model.getConstrs():
                expr=model.getRow(row)
                matrix.append(dict(name=row.ConstrName,sense=row.Sense,RHS=row.RHS,
                    coefficients=[[expr.getVar(j).VarName,expr.getCoeff(j)] for j in range(expr.size())]))
            with gzip.open(dest/'loaded_matrix.json.gz','wt',encoding='utf-8') as stream:
                json.dump(dict(columns=columns,rows=matrix,objective_constant=model.ObjCon,
                    sense=model.ModelSense,fingerprint=model.Fingerprint),stream,allow_nan=False)
            C.write(dest/'columns.json',dict(columns=columns,original_column_order=True))
            C.write(dest/'binding.json',dict(runtime=runtime,model_SHA256=C.sha(ROOT/r['model']),
                model_dimensions=dict(rows=model.NumConstrs,columns=model.NumVars),
                requested=r['settings'],readback=readback,TimeLimit=model.Params.TimeLimit,
                NumStart=model.NumStart,H=0,LP=0,Optimize_planned=1,diagnostic_only=True))
            with gzip.open(dest/'callback_scalars.jsonl.gz','wt',encoding='utf-8') as scalars, \
                 gzip.open(dest/'MIPSOL_vectors.jsonl.gz','wt',encoding='utf-8') as vectors:
                sequence=0
                def callback(m,where):
                    nonlocal sequence
                    if where not in (gp.GRB.Callback.MIP,gp.GRB.Callback.MIPSOL):return
                    try:
                        sequence+=1;which='MIP' if where==gp.GRB.Callback.MIP else 'MIPSOL';counts[which]+=1
                        codes=gp.GRB.Callback
                        event=dict(sequence=sequence,kind=which,runtime=m.cbGet(codes.RUNTIME),work=m.cbGet(codes.WORK),
                            bound=m.cbGet(codes.MIP_OBJBND if which=='MIP' else codes.MIPSOL_OBJBND),
                            incumbent=m.cbGet(codes.MIP_OBJBST if which=='MIP' else codes.MIPSOL_OBJBST),
                            nodes=m.cbGet(codes.MIP_NODCNT if which=='MIP' else codes.MIPSOL_NODCNT))
                        if which=='MIPSOL':
                            event['objective']=m.cbGet(codes.MIPSOL_OBJ)
                            json.dump(dict(event,values=m.cbGetSolution(variables)),vectors,allow_nan=False);vectors.write('\n')
                        json.dump(event,scalars,allow_nan=False);scalars.write('\n')
                    except Exception as error:
                        callback_errors.append(dict(sequence=sequence,type=type(error).__name__,message=str(error)))
                        m.terminate()
                model.optimize(callback)
            attributes={name:safe_attr(model,name) for name in ['Status','SolCount','ObjVal','ObjBoundC','MIPGap',
                'Runtime','Work','NodeCount','IterCount','BarIterCount','MaxVio','BoundVio','BoundVioIndex',
                'BoundVioSum','ConstrVio','ConstrVioIndex','ConstrVioSum','IntVio','IntVioIndex','IntVioSum',
                'Kappa','KappaExact','ConcurrentWinMethod']}
            if model.SolCount:
                final=model.getAttr('X',variables)
                with (dest/'final_vector.csv').open('x',encoding='utf-8',newline='') as stream:
                    writer=csv.writer(stream);writer.writerow(['name','value','type'])
                    for column,value in zip(columns,final):writer.writerow([column['name'],repr(value),column['type']])
            C.write(dest/'native_return.json',dict(UTC=C.utc(),attributes=attributes,callback_counts=counts,
                callback_records=sequence,callback_errors=callback_errors,final_vector_available=final is not None,
                Optimize=1,Start=0,physical_readout='run analyze; independent post-native step',
                model_and_parameters_unchanged=True,internal_root_cause='not inferred from status'))
    C.write(dest/'completion.json',dict(UTC=C.utc(),outer_seconds=time.perf_counter()-tick,
        Optimize=1,callbacks=counts,callback_errors=callback_errors,final_vector_available=final is not None,
        diagnostic_only=True,no_repeat_on_open_or_nonreproduction=True))
    print(json.dumps(dict(C_R3='COMPLETED',seconds=time.perf_counter()-tick,callbacks=counts,callback_errors=callback_errors)))
    return 1 if callback_errors else 0

def reconstruct_routes(values,panel):
    routes=[];n=panel['V'];M=panel['M'];round_int=lambda x:int(math.floor(x+.5))
    for k in range(M):
        edges={i:[j for j in range(n+1) if i!=j and values.get(f'x_{k}_{i}_{j}',0)>.5] for i in range(n+1)}
        if not edges[0]:
            assert not any(edges.values()),'station cycle without depot'
            routes.append(dict(vehicle=k,nodes=[0,0],operations=[]));continue
        nodes=[0];seen=set()
        while True:
            i=nodes[-1];assert len(edges[i])==1,'nonunique native successor';j=edges[i][0];nodes.append(j)
            if j==0:break
            assert j not in seen,'native route cycle';seen.add(j);assert len(seen)<=n
        assert set(i for i,out in edges.items() if out)=={0}|seen,'unreconstructed active arcs'
        operations=[]
        for i in nodes[1:-1]:
            pickup=round_int(values[f'p_{k}_{i}']);drop=round_int(values[f'd_{k}_{i}'])
            assert pickup>=0 and drop>=0 and bool(pickup)!=bool(drop),'zero/two-way rounded service'
            operations.append(dict(station=i,pickup=pickup,drop=drop))
        routes.append(dict(vehicle=k,nodes=nodes,operations=operations))
    return routes

def analyze():
    tick=time.perf_counter();p=C.read(PLAN);dest=ROOT/p['C_R3']['destination']
    assert (dest/'completion.json').exists(),'native process must exit first'
    assert not (dest/'physical_residual_analysis.json').exists(),'do not repeat healthy analysis'
    import round108_reader as core
    with gzip.open(dest/'loaded_matrix.json.gz','rt',encoding='utf-8') as stream:matrix=json.load(stream)
    columns=matrix['columns'];names=[x['name'] for x in columns];panel=p['panel']
    records=[]
    def inspect_point(label,values,event=None):
        assert len(values)==len(columns);x=dict(zip(names,values));f={n:F.from_float(v) for n,v in x.items()}
        out=dict(label=label,event=event,native_G=x.get('G'),native_e={n:v for n,v in x.items() if re.fullmatch('e_\\d+',n)},
            native_r={n:v for n,v in x.items() if re.fullmatch('r_\\d+',n)},
            native_Y={n:v for n,v in x.items() if re.fullmatch('Y_\\d+',n)},
            native_service={n:v for n,v in x.items() if re.fullmatch('[pd]_\\d+_\\d+',n)},
            raw_point_SHA256=hashlib.sha256(json.dumps(values,separators=(',',':')).encode()).hexdigest())
        try:
            routes=reconstruct_routes(x,panel);physical=core.full_fleet(ROOT,panel,dict(routes=routes))
            out.update(physical_verified=True,physical=physical)
        except Exception as error:out.update(physical_verified=False,physical_error=type(error).__name__+':'+str(error))
        obj=F.from_float(matrix['objective_constant'])+sum(F.from_float(c['objective'])*f[c['name']] for c in columns)
        out['exact_loaded_objective']=str(obj);out['loaded_objective']=float(obj)
        maximum=F(0);violations=[]
        for row in matrix['rows']:
            residual=sum(F.from_float(a)*f[n] for n,a in row['coefficients'])-F.from_float(row['RHS'])
            violation=abs(residual) if row['sense']=='=' else max(F(0),residual if row['sense']=='<' else -residual)
            maximum=max(maximum,violation)
            if violation:
                families=sorted(set(n.split('_')[0] for n,a in row['coefficients']))
                violations.append(dict(name=row['name'],sense=row['sense'],violation=float(violation),
                    exact_violation=str(violation),families=families))
        violations.sort(key=lambda v:v['violation'],reverse=True)
        out['loaded_row_residuals']=dict(rows=len(matrix['rows']),maximum=float(maximum),exact_maximum=str(maximum),
            positive_residual_count=len(violations),largest=violations[:15],
            objective_component_rows=[v for v in violations if set(v['families'])&{'G','e','r','Y','h','zprod','state'}][:20])
        out['domain_residuals']=dict(max_bound_violation=max([0.]+[max(c['lower']-x[c['name']],x[c['name']]-c['upper'],0.) for c in columns]),
            max_integrality_violation=max([0.]+[abs(x[c['name']]-round(x[c['name']])) for c in columns if c['type'] in ['B','I']]),
            max_service_rounding=max([0.]+[abs(v-round(v)) for n,v in x.items() if re.fullmatch('[pd]_\\d+_\\d+',n)]))
        if out.get('physical_verified'):
            ph=out['physical'];out['objective_propagation']=dict(physical_minus_loaded=ph['F']-float(obj),
                physical_G_minus_native_G=ph['G']-x['G'],
                physical_penalty_contribution=panel['lambda']*ph['P'],
                native_penalty_contribution=float(obj)-x['G'])
        return out
    vector=dest/'final_vector.csv'
    if vector.exists():
        with vector.open(newline='',encoding='utf-8') as stream:rows=list(csv.DictReader(stream))
        assert [r['name'] for r in rows]==names
        records.append(inspect_point('native_final',[float(r['value']) for r in rows]))
    with gzip.open(dest/'MIPSOL_vectors.jsonl.gz','rt',encoding='utf-8') as stream:
        for index,line in enumerate(stream,1):
            value=json.loads(line);records.append(inspect_point(f'MIPSOL_{index}',value.pop('values'),value))
    C.write(dest/'physical_residual_analysis.json',dict(UTC=C.utc(),records=records,
        source_SHA256=C.sha(__file__),registration_SHA256=C.sha(PLAN),outer_seconds=time.perf_counter()-tick,
        Optimize=0,native_module_imports=0,arithmetic='exact rationals of loaded binary64 coefficients and raw binary64 point',
        diagnostic_only=True,not_a_MIP_tree_certificate=True,unknown_fields_retained=True))
    print(json.dumps(dict(points=len(records),seconds=time.perf_counter()-tick,
        final_objective_propagation=records[0].get('objective_propagation') if records else None)))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','run-r2','run-r3','analyze'])
    action=parser.parse_args().action
    if action=='prepare':prepare()
    elif action=='run-r2':sys.exit(run_r2())
    elif action=='run-r3':sys.exit(run_r3())
    else:analyze()
