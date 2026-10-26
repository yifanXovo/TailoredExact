"""Actual independent pre-CLI contract review; no native or producer import.

Reads frozen authorities and complete reference LPs. Executes selected actual
helper functions in bounded memory fixtures. All outputs are review receipts.
"""
from pathlib import Path
import ast, collections, contextlib, copy, csv, datetime, hashlib, json, math, os, re, shutil, sys, time, types
import independent_review_round122 as inputs

ROOT=inputs.ROOT;OUT=inputs.OUT;REVIEW=inputs.REVIEW
read=inputs.read;sha=inputs.sha
WORK=Path('E:/codes/ExactEBRP-work')
METHODS=['P-GRB','ENS-C','M-B','MB-D1']
PAIRS=[['MB-D1','P-GRB'],['M-B','P-GRB'],['ENS-C','P-GRB'],['MB-D1','M-B'],['MB-D1','ENS-C'],['M-B','ENS-C']]
PE_SHA='5471f9c199c016e26178e6fc83aba42e5d2e1ee797735d68a864dbada4c7cbba'
DLL_SHA='9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88'
SOURCE='355eefd2be3fe5651195681faf7b3a63ee4032f8'

def node(file,name):
    return next(n for n in ast.parse((ROOT/file).read_text(encoding='utf-8-sig')).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name)

def extract(file,name,namespace,remove_imports=()):
    tree=copy.deepcopy(node(file,name))
    class Strip(ast.NodeTransformer):
        def visit_Import(self,n):
            return None if all(q.name in remove_imports for q in n.names) else n
        def visit_ImportFrom(self,n):
            return None if n.module in remove_imports else n
    tree=Strip().visit(tree)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[tree],type_ignores=[])),str(file)+'::independent_memory_execution','exec'),namespace)
    return namespace[name]

def frozen_bindings():
    c=read(OUT/'candidate_identity.json');p=read(OUT/'production_identity.json');f=read(OUT/'prospective_helper_freeze.json')
    old=read(ROOT/'results/unified_exact_round121/production_identity.json')
    assert c['production_PE_SHA']==p['production_PE_SHA']==old['production_PE_SHA']==PE_SHA
    assert c['DLL_SHA']==p['DLL_SHA']==old['DLL_SHA']==DLL_SHA
    assert p['source_commit_before_native']==SOURCE
    pe=Path(p['production_PE_path']);dll=Path(p['DLL_path'])
    assert sha(pe)==PE_SHA and sha(dll)==DLL_SHA
    assert c['source_bindings']==p['source_bindings']==old['source_bindings']==f['source_bindings']
    actual_sources={x.relative_to(ROOT).as_posix():sha(x) for x in sorted([ROOT/'CMakeLists.txt']+[
        p for folder in ['src','include'] for p in (ROOT/folder).rglob('*') if p.suffix in ['.cpp','.inc','.hpp','.h']])}
    assert actual_sources==c['source_bindings']
    assert c['helpers']==f['helpers']
    for name,h in c['helpers'].items(): assert sha(ROOT/name)==h,('changed helper',name)
    for key,name in [('input_manifest_SHA','input_manifest.json'),('argv_freeze_SHA','argv_freeze.json'),('protocol_SHA','protocol.json'),('production_identity_SHA','production_identity.json')]:
        assert c[key]==sha(OUT/name),(key,name)
    assert f['argv_SHA']==sha(OUT/'argv_freeze.json') and f['protocol_SHA']==sha(OUT/'protocol.json')
    # Walk every recorded Python helper, including nested function imports.
    helper_set=set(c['helpers']);edges=[]
    for name in sorted(helper_set):
        if not name.endswith('.py'): continue
        source=(ROOT/name).read_text(encoding='utf-8-sig');tree=ast.parse(source)
        for n in ast.walk(tree):
            mods=[q.name for q in n.names] if isinstance(n,ast.Import) else [n.module] if isinstance(n,ast.ImportFrom) else []
            for mod in mods:
                if not mod:continue
                local='scripts/'+mod+'.py'
                if (ROOT/local).is_file():
                    assert local in helper_set,('unbound local import',name,local);edges.append((name,local))
                elif re.match(r'^(round\d+_|read_round\d+|qualify_round\d+|compare_round\d+|generate_citibike)',mod):
                    raise AssertionError(('missing expected local helper',name,mod))
    return c,dict(source_files=len(actual_sources),helper_files=len(helper_set),local_import_edges=len(edges),
        PE_path=str(pe),PE_SHA=sha(pe),DLL_path=str(dll),DLL_SHA=sha(dll),
        source_before_native=SOURCE,all_source_bytes_equal_R121=True,all_frozen_helper_bytes_equal=True)

def lp_reference(path):
    """Separate parser for the saved single-line LP, not an inherited reader."""
    order=[];seen=set();bounds={};types_map={};rows=[];objective=None;section=None
    def add(name):
        assert re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',name),name
        if name not in seen:seen.add(name);order.append(name)
    def linear(body):
        parts=body.split();terms=collections.defaultdict(float);constant=0.;i=0;sign=1.
        while i<len(parts):
            token=parts[i]
            if token in ['+','-']:sign=1. if token=='+' else -1.;i+=1;continue
            try:value=float(token)
            except ValueError:
                add(token);terms[token]+=sign;i+=1
            else:
                assert math.isfinite(value)
                if i+1<len(parts) and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',parts[i+1]):
                    name=parts[i+1];add(name);terms[name]+=sign*value;i+=2
                else:constant+=sign*value;i+=1
            sign=1.
        return dict(terms),constant
    with path.open(encoding='utf-8') as f:
        for raw in f:
            s=raw.strip()
            if not s or s.startswith('\\'):continue
            if s in ['Minimize','Subject To','Bounds','Generals','Binaries','End']:section=s;continue
            if section=='Minimize':
                assert objective is None;objective=linear(s.split(':',1)[1])
            elif section=='Subject To':
                body=s.split(':',1)[1];match=re.search(r'(<=|>=|=)\s*([-+0-9.eE]+)\s*$',body);assert match
                terms,constant=linear(body[:match.start()]);rows.append((terms,match[1],float(match[2])-constant))
            elif section=='Bounds':
                lo,op,name,op2,hi=s.split();assert op==op2=='<=' and name not in bounds
                add(name);bounds[name]=(float(lo),float(hi))
            elif section in ['Generals','Binaries']:
                for name in s.split():
                    add(name);assert name not in types_map;types_map[name]='I' if section=='Generals' else 'B'
            else:raise AssertionError(('unknown LP grammar',section,s))
    assert section=='End' and set(bounds)==seen and objective is not None
    return order,bounds,{n:types_map.get(n,'C') for n in order},rows,objective

def references_and_argv(c):
    protocol=read(OUT/'protocol.json');argv=read(OUT/'argv_freeze.json');m=read(OUT/'input_manifest.json')
    assert protocol['pairs']==PAIRS and len(argv['groups'])==8
    assert protocol['maximum_outer_seconds']==100000 and protocol['qualification_soft_seconds']==3000 and protocol['qualification_authorized_seconds']==6000
    assert protocol['native_reserve']==30 and protocol['evidence_tolerance']==1e-7 and protocol['own_H_seed']==20260626
    expected_common=dict(threads=1,mip_threads=1,gurobi_seed='per-group frozen 0/1',gurobi_presolve=-1,gurobi_version='13.0.2',affinity_mask=4,
        native_limit_offset_seconds=6,hard_stop_offset_seconds=2,shutdown_margin_seconds=30,requested_mip_gap=0,requested_mip_gap_abs=0,
        FeasibilityTol=1e-6,OptimalityTol=1e-6,IntFeasTol=1e-5)
    assert protocol['common']==expected_common
    prod=read(OUT/'production_identity.json');pe=Path(prod['production_PE_path']);facts=[]
    for p in m['new_roles']:
        directory=OUT/'qualification/reference'/p['id'];b=read(directory/'build.json');native=read(directory/'native_metadata.json')
        assert b['optimizer_calls']==native['Optimize']==0 and sha(directory/'original.lp')==b['canonical_sha256']
        order,bounds,vtypes,rows,obj=lp_reference(directory/'original.lp')
        assert len(order)==b['columns']==native['columns'] and len(rows)==b['rows']==native['rows']
        assert native['objective_sense']==1 and native['objective_constant']==obj[1]==0
        with (directory/'native_columns.csv').open(encoding='utf-8',newline='') as f: columns=list(csv.DictReader(f))
        assert len(columns)==len(order)
        for j,(name,col) in enumerate(zip(order,columns)):
            assert int(col['index'])==j and col['type']==vtypes[name]
            assert (float(col['lower']),float(col['upper']))==bounds[name]
            assert float(col['objective'])==obj[0].get(name,0.)
        with (directory/'native_rows.csv').open(encoding='utf-8',newline='') as f: native_rows=list(csv.DictReader(f))
        assert len(native_rows)==len(rows)
        for j,(row,col) in enumerate(zip(rows,native_rows)):
            assert int(col['index'])==j and col['sense']=={'<=':'<','>=':'>','=':'='}[row[1]] and float(col['RHS'])==row[2]
        facts.append(dict(id=p['id'],canonical_SHA=b['canonical_sha256'],rows=len(rows),columns=len(order),
            independently_parsed_native_type_counts=dict(collections.Counter(vtypes.values())),native_all_columns_bounds_objective_and_row_RHS_equal=True,Optimize=0))
    # Execute actual R88/R90 command builders and the final thin adapter in memory.
    pns=dict(ROOT=ROOT,Path=Path);pcommand=extract('scripts/round88_a1_g3.py','command_for',pns)
    wns=dict(ROOT=ROOT,Path=Path);wcommand=extract('scripts/round90_lp_g_g3.py','command_for',wns)
    fake_supervisor=types.SimpleNamespace(command_for=wcommand,audited_runner_utilities=types.SimpleNamespace(command_for=pcommand))
    ns=dict(COMMON=expected_common,PE=pe,PE_SHA=PE_SHA,METHODS=METHODS,s=fake_supervisor)
    command=extract('scripts/round122_prepare.py','command',ns,remove_imports=('round90_lp_g_g3',))
    launch_count=0;formal_count=0;qualification=[]
    for plan in argv['plans']:
        identity_path=OUT/plan['name']/'identity.json';i=read(identity_path)
        assert sha(identity_path)==c['campaign_identities'][plan['name']]
        assert i['helpers']==c['helpers'] and i['source_hashes']==c['source_bindings']
        assert i['candidate_binary_sha256']==PE_SHA and i['dll_sha256']==DLL_SHA
        assert i['prereg_sha256']==sha(OUT/'protocol.json') and i['measurement_policy_SHA']==sha(OUT/'measurement_policy_v2.md')
        assert i['runner_sha256']==sha(ROOT/'scripts/round122_campaign.py')
        assert len(plan['launches'])==len(i['launches'])
        if plan['name'].startswith('campaign/'):
            groupno=int(plan['name'][-2:]);group=argv['groups'][groupno-1];p=m['roles'][groupno-1]
            assert group['number']==groupno and group['methods']==inputs.ORDERS[groupno-1]
            assert group['id']==p['id'] and group['seed']==p['gurobi_seed'] and group['cap_seconds']==p['cap_seconds']
            assert group['fixed_unconditional'] and group['management_reserve']==120
            assert [l['arm'] for l in i['launches']]==p['method_order'];formal_count+=len(i['launches'])
        else:
            assert plan['name'] in ['qualification/h100_seed0','qualification/h100_seed1']
            expected=METHODS if plan['name'].endswith('seed1') else ['MB-D1']
            assert [l['arm'] for l in i['launches']]==expected
        for l,declared in zip(i['launches'],plan['launches']):
            d=Path(l['destination']);p=l['panel'];arm=l['arm'];args=l['command']
            assert d.resolve().is_relative_to(WORK.resolve()) and not d.exists()
            assert sha(ROOT/p['input_path'])==p['input_sha256'] and l['seed']==p['gurobi_seed']
            assert l['hard_stop_seconds']==l['cap_seconds']-2
            assert args==command(p,arm,d)
            assert Path(args[0]).resolve()==pe.resolve() and args.count('--gurobi-seed')==1
            def val(flag):return args[args.index(flag)+1]
            assert val('--gurobi-seed')==str(l['seed']) and val('--time-limit')==str(l['cap_seconds']-6)
            assert val('--process-wall-time-limit')==str(l['cap_seconds']) and val('--process-shutdown-margin')=='30'
            assert val('--threads')==val('--mip-threads')=='1' and val('--gurobi-presolve')=='-1'
            assert ('--plain-baseline' in args)==(arm=='P-GRB')
            assert ('--round98-state-service' in args)==(arm in ['M-B','MB-D1'])
            assert ('--round120-native-proof-d1' in args)==(arm=='MB-D1')
            if arm!='P-GRB':
                assert val('--algorithm-preset')=='research-round83-vds-equal-net-exchange'
                assert val('--round90-lp-g-split')=='false'
                assert val('--round65-witness-audit')==val('--round65-hga-zero-stop')=='true'
            forbidden=['--round120-native-proof-d0','--round119','--round120-qualification','--round112-ens-start-compact','--round100-continuous-quantities']
            assert not any(a.startswith(x) for a in args for x in forbidden)
            ref=OUT/'qualification/reference'/l['id'];build=read(ref/'build.json')
            assert p['reference']==build and build['optimizer_calls']==0
            assert sha(ref/'original.lp')==build['canonical_sha256']
            assert sha(OUT/plan['name']/'reference'/l['id']/'original.lp')==build['canonical_sha256']
            if arm=='P-GRB':assert val('--round24-expected-gurobi-model-fingerprint')==str(build['fingerprint'])
            # Frozen placeholders may be replaced only by the zero-Optimize fingerprint.
            expected=list(declared['command'])
            for j,x in enumerate(expected):
                if x=='REFERENCE_FINGERPRINT':expected[j]=str(build['fingerprint'])
            assert args==expected
            launch_count+=1
            if plan['name'].startswith('qualification/'):
                assert l['id']=='H100' and l['cap_seconds']==120
                qualification.append(dict(plan=plan['name'],arm=arm,seed=l['seed'],cap=l['cap_seconds']))
    assert launch_count==37 and formal_count==32 and len(qualification)==5
    assert sum(g['nominal_seconds'] for g in argv['groups'])==79200 and sum(g['management_reserve'] for g in argv['groups'])==960
    known=read(OUT/'qualification/known_reference_binding.json')
    assert known['original_input_SHA']==m['qualification_roles'][0]['input_sha256']
    assert all(sha(OUT/'qualification/reference/H100'/n)==h for n,h in known['files'].items())
    return dict(formal_argv_positions=32,known_fixture_qualification_positions=qualification,actual_command_builder_memory_executions=launch_count,
        complete_zero_Optimize_reference_recheck=facts,nominal_formal_seconds=79200,management_reference_seconds=960,
        all_formal_and_CLI_destinations_unstarted=True,reference01_fee_SHA=sha(OUT/'fees/reference01/receipt.json'))

def fee_fixture():
    state={};writes=[]
    class MemoryPath:
        def __truediv__(self,x):return self
        def exists(self):return state.get('exists',False)
        def mkdir(self,**kwargs):writes.append('mkdir')
    common=dict(paid_starts=9999,remaining_outer_seconds=100000,qualification_seconds=0,unclosed=[])
    ns=dict(workspace=lambda:{'root':'E:/codes/ExactEBRP-work'},process_origin=lambda:(10.,20.),budget=lambda:state['budget'],
        OUT=MemoryPath(),QUAL_LIMIT=6000,sys=types.SimpleNamespace(argv=['memory']),ROOT=ROOT,
        os=types.SimpleNamespace(getpid=lambda:123),utc=lambda:'MEMORY',write=lambda p,v:writes.append(v))
    fn=extract('scripts/round122_common.py','fee_begin',ns,remove_imports=('round115_common',))
    cases=[('exact_total',dict(remaining_outer_seconds=81960),1800,True,True),
        ('short_total',dict(remaining_outer_seconds=81959.999),1800,True,False),
        ('qualification_exact_6000',dict(qualification_seconds=4200),1800,True,True),
        ('qualification_over_6000',dict(qualification_seconds=4200.001),1800,True,False),
        ('soft_3000_is_not_hard',dict(qualification_seconds=2000),1800,True,True),
        ('unclosed_parent',dict(unclosed=['old']),1800,True,False),
        ('many_observed_starts_are_allowed',dict(paid_starts=99999),1800,True,True)]
    checked=[]
    for name,change,cap,qual,should_pass in cases:
        state['budget']=dict(common,**change);state['exists']=False;writes.clear()
        try:fn('case',5,cap,qual,dict(starts=999999,seconds=80160))
        except AssertionError:passed=False
        else:passed=True
        assert passed==should_pass,(name,passed)
        checked.append(dict(case=name,admitted=passed,expected=should_pass))
    return dict(actual_final_fee_begin_memory_executed=True,cases=checked,no_files_or_processes=True)

def clock_fixture():
    events=[];store={};clock=[205.]
    def perf():clock[0]+=1;return clock[0]
    fake_time=types.SimpleNamespace(perf_counter=perf,time=lambda:1000.+clock[0])
    def rd(p):return store[Path(p).name]
    def wr(p,v):
        name=Path(p).name;events.append(name);store[name]=copy.deepcopy(v);clock[0]+=1
    store.update({'producer_receipt.json':dict(producer_seal_SHA='HASH',native_stopped_no_reentry=True,t0_perf=100.,t_produce_perf=200.),
        'producer_seal.json':dict(required_SHA={'result.json':'HASH'}),'observations.json':[],
        'completion.json':{},'independent_evidence.json':dict(own_U=1.),
        'production_checks.json':dict(final_physical_verification={'F':1.}), 'result.json':{}})
    def adapter(l,observations,completion,identity):return dict(passed=True,native_proof_qualified=True)
    inherited=types.SimpleNamespace(adapter=adapter,last_metrics={})
    legacy_ns=dict(Path=Path,read=rd,write=wr,sha=lambda p:'HASH',time=fake_time,types=types,
        inherited=inherited,independent=lambda *a:None,ClaimRejection=type('ClaimRejection',(Exception,),{}))
    inherited_verify=extract('scripts/round115_verify.py','verify',legacy_ns)
    class Models:
        def clear(self):events.append('model_cache_cleared')
    @contextlib.contextmanager
    def extension():yield
    @contextlib.contextmanager
    def activate(v):yield
    def event_chain(*args):events.append('actual_extension_event_audit');clock[0]+=5;return {'installed':0}
    ns=dict(Path=Path,ROOT=ROOT,read=rd,write=wr,sha=lambda p:'HASH',extension=extension,
        audit=types.SimpleNamespace(journal=lambda *a:dict(calls={},not_started_ids=set())),ArmModels=Models,
        logs=types.SimpleNamespace(build=lambda *a:dict(bindings=[],actual=[]),activate=activate),
        prior=types.SimpleNamespace(NEW=['MB-D0','MB-D1']),event_chain=event_chain,
        verifier=types.SimpleNamespace(verify=inherited_verify))
    fn=extract('scripts/round122_evidence.py','verify',ns)
    fn(dict(destination='MEMORY',arm='MB-D1'),{})
    total=store['arm_total_receipt.json'];p=store['producer_receipt.json']
    assert events.index('actual_extension_event_audit')<events.index('round120_extended_verification.json')<events.index('verification_closeout.json')<events.index('arm_total_receipt.json')
    assert total['T_verify']==total['t_verified_perf']-p['t_produce_perf']
    assert total['T_total']==total['t_verified_perf']-p['t0_perf']
    assert total['T_total']==100.+total['T_verify']
    return dict(final_evidence_verify_and_inherited_final_clock_actually_executed_in_memory=True,
        event_order=events,T_produce=100.,T_verify=total['T_verify'],T_total=total['T_total'],
        required_D1_event_model_writes_inside_T_verify=True,no_native_model_or_files_written=True)

def stage_fixture():
    fn=extract('scripts/round122_decision.py','decide',{})
    values=[]
    for j in range(1,9):
        values.append(dict(group={'number':j,'V':20 if j in [1,2] else 35 if j in [3,4,7] else 50},
            arms=[dict(arm=a,formal_protocol_qualified=True,actually_executed=True,certificate=False) for a in METHODS],
            pairs=[dict(candidate=a,control=b,evaluable=True,classification='WIN' if a=='MB-D1' else 'TIE',severe_regression=False) for a,b in PAIRS],
            mechanism=[dict(arm='MB-D1',installed=1,actual_extended_Optimize=1)]))
    cases=[]
    def check(name,x,expected,valid=True,risk=False,blockers=()):
        r=fn(x,valid,risk,blockers);assert r['stage']==expected,(name,r);cases.append(dict(case=name,stage=r['stage']))
    check('positive_literal_conditions',values,'FREEZE_D1_AS_PAPER_BENCHMARK_CANDIDATE')
    check('invalid_input_identity',values,'BLOCKED',valid=False)
    check('proven_source_error_priority',values,'PROOF_RELIABILITY_PRIORITY',risk=True,blockers=('capacity',))
    check('missing_group',values[:-1],'BLOCKED')
    x=copy.deepcopy(values);x[1]['group']['number']=1;check('duplicate_group',x,'BLOCKED')
    x=copy.deepcopy(values)
    for v in x[:2]:next(p for p in v['pairs'] if (p['candidate'],p['control'])==('MB-D1','P-GRB'))['classification']='LOSS'
    check('two_new_primary_losses',x,'DO_NOT_SELECT_D1_AS_PAPER_PRIMARY')
    x=copy.deepcopy(values);next(p for p in x[7]['pairs'] if (p['candidate'],p['control'])==('MB-D1','P-GRB'))['severe_regression']=True
    check('Seed1_severe_veto',x,'DO_NOT_SELECT_D1_AS_PAPER_PRIMARY')
    x=copy.deepcopy(values)
    for v in x:v['mechanism'][0].update(installed=0,actual_extended_Optimize=0)
    check('complete_no_exposure_is_mixed_not_BLOCKED',x,'BENCHMARK_MIXED_NO_NEW_PRIMARY_SELECTION')
    return dict(actual_final_stage_function_executed=True,cases=cases,no_performance_observation_invented=True)

def workspace_review():
    capacity=read(OUT/'workspace_capacity.json');inventory=read(OUT/'workspace_inventory.json')
    assert (OUT/'workspace_plan.md').is_file() and capacity['minimum_group_start_free_bytes']==40*1024**3
    assert capacity['peak_incremental_upper_bytes']==sum(capacity[k] for k in ['raw_projection_bytes','carrier_upper_bytes','pack_intermediate_bytes','one_restore_bytes','sparse_code_authorities_build_bytes','safety_margin_bytes'])
    paths=[ROOT,OUT,WORK/'temp/round122',WORK/'evidence/round122',WORK/'restore']
    for p in paths:
        assert p.resolve().is_relative_to(WORK.resolve())
        for q in [p,*p.parents]:
            if q.exists():assert not q.is_symlink() and not q.is_junction()
    free=shutil.disk_usage(WORK).free
    assert free>capacity['peak_incremental_upper_bytes'] and free>capacity['minimum_group_start_free_bytes']
    receipt=read(OUT/'fees/reference01/receipt.json')
    assert receipt['exit_code']==0 and receipt['actual_native_children']==1 and receipt['actual_exit_observed']
    assert receipt['qualification'] and receipt['outer_seconds_upper']<300 and not receipt['nested_native_seconds_added']
    assert receipt['outer_seconds_upper']+1500+80160<100000
    assert receipt['outer_seconds_upper']+1500<6000
    # Exercise actual environment/identity-independent workspace binding after all
    # filesystem predicates were checked. No producer module is imported.
    fake_os=types.SimpleNamespace(environ={})
    ns=dict(ROOT=ROOT,WORK=WORK,OUT=OUT,TEMP=WORK/'temp/round122',EVIDENCE=WORK/'evidence/round122',MAIN=Path('E:/codes/ExactEBRP'),
        os=fake_os,shutil=shutil)
    # mkdir calls in workspace() target already-existing directories only.
    result=extract('scripts/round122_common.py','workspace',ns)()
    assert Path(fake_os.environ['TEMP'])==Path(fake_os.environ['TMP'])==WORK/'temp/round122'
    return dict(workspace_plan_SHA=sha(OUT/'workspace_plan.md'),inventory_SHA=sha(OUT/'workspace_inventory.json'),
        capacity_SHA=sha(OUT/'workspace_capacity.json'),free_bytes_observed=free,peak_incremental_upper_bytes=capacity['peak_incremental_upper_bytes'],
        no_reparse_redirection=True,actual_workspace_function_process_env_binding_checked=True,
        E_root_bound_paths=[str(p) for p in paths],remaining_fixed_formal_obligations_seconds=80160,
        maximum_planned_after_reference_plus_CLI_seconds=receipt['outer_seconds_upper']+1500+80160)

def check():
    start=time.perf_counter();c,binding=frozen_bindings();candidate_before=sha(OUT/'candidate_identity.json')
    previous_inputs=read(REVIEW/'independent_inputs_01.json')
    assert previous_inputs['script_SHA']==sha(REVIEW/'independent_review_round122.py')
    assert previous_inputs['input_manifest_SHA']==sha(OUT/'input_manifest.json')
    independently_again=inputs.input_review();assert independently_again['roles']==previous_inputs['roles']
    refs=references_and_argv(c);fees=fee_fixture();clocks=clock_fixture();stages=stage_fixture();workspace=workspace_review()
    c2,binding2=frozen_bindings();assert c2==c and binding2==binding and sha(OUT/'candidate_identity.json')==candidate_before
    assert not (REVIEW/'pre_contract.json').exists() and not (REVIEW/'performance_admission.json').exists()
    value=dict(decision='ACCEPT',scope='Frozen 32-position formal design and five known-fixture pre-CLI qualifications; formal launch remains contingent on actual successful qualification and fee closure.',
        UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),reviewer='actual independent delegated executor /root/contract_review',
        script_SHA=sha(__file__),candidate_identity_SHA=candidate_before,helpers=c['helpers'],source_bindings=c['source_bindings'],
        frozen_bindings=binding,input_rederivation_SHA=sha(REVIEW/'independent_inputs_01.json'),input_manifest_SHA=sha(OUT/'input_manifest.json'),
        argv_SHA=sha(OUT/'argv_freeze.json'),protocol_SHA=sha(OUT/'protocol.json'),workspace=workspace,references_and_argv=refs,
        actual_memory_fee_guard_cases=fees,actual_memory_verification_clock_case=clocks,actual_stage_cases=stages,
        source_specific_FAMILY_rows_targets_and_serialization_independently_recomputed=True,
        frozen_D1_source_only_own_paid_original_root_pair_first_integer_gate_no_forced_exposure=True,
        ENS_C_Seed1_branch_and_integer_quantity_contract_present=True,
        PE_DLL_production_sources_or_measured_helpers_changed=False,native_starts=0,Optimize=0,native_compiles=0,Git=0,
        limitations=['No new solver or Optimize was launched by this reviewer; actual Seed0/1 native settings, complete models, Starts, returns, physical routes and H equality must pass the recorded five known-fixture CLI qualifications.',
            'D1 exposure is never forced. This review preserves prior mathematical qualifications and frozen source/PE/DLL identities; it does not certify performance, a new nonzero certificate, or future raw not yet produced.',
            'The complete 32 arms, 48 independently replayed pairs, full V50 fleet/model/Start scope review, public restore and final cleanup remain required.'],
        seconds=time.perf_counter()-start)
    inputs.save_receipt('pre_contract.json',value)
    text='\n'.join(['# Independent Round122 pre-CLI contract review','',
        '**Decision: ACCEPT for the frozen design and bounded five known-fixture CLI qualifications.** Formal performance launch remains gated by actual qualification and closed fees.','',
        'A separate implementation recomputed both source bindings and all six complete serialized input byte strings, parsed fields, station mappings, anchors, ties, targets, stock correction/sign repair, weights and depot. The exact eight groups, 32 positions, 48 pairs and 79200 nominal seconds match the user protocol.','',
        'All production sources match R121; PE/DLL SHA values match the frozen requested identities. Every recorded helper and local import dependency is present and SHA-bound. All 37 planned formal/qualification argv vectors were actually recomputed from the frozen original command builders and final thin adapter; all destinations were unstarted. Six complete cold LPs were independently parsed and compared with every native column type/bound/objective and row sense/RHS from the zero-Optimize export.','',
        'Actual final fee-guard, verification-clock and stage functions were executed in memory. Boundary cases accept the 6000-second qualification maximum, preserve the complete formal reservation, treat the 3000-second soft plan and startup count correctly, reject insufficient/unclosed states, preserve proof priority and severe-loss vetoes, and retain complete no-exposure results as mixed. The final clock fixture includes extension/model writes before the inherited verification closeout and satisfies T_total = T_produce + T_verify.','',
        'The E-root path/capacity plan and actual no-reparse resolution were checked; process TEMP/TMP binding was exercised. The existing 16.66-second zero-Optimize reference fee is closed; 1500 seconds of planned CLI qualification plus 80160 seconds of formal obligations fit both authorized ceilings.','',
        'Remaining required facts: actual known-fixture Seed0/1 CLI models/Starts/settings/returns/physical checks and complete H, then all fixed formal positions and independent post-formal replay, public-carrier restore and safe cleanup. No native launch, Optimize, native compile, Git action, measured-helper edit or historical raw edit occurred in this review.',''])
    with (REVIEW/'pre_contract.md').open('x',encoding='utf-8',newline='\n') as f:f.write(text)

if __name__=='__main__':check()
