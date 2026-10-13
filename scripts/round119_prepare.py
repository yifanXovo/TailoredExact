"""Freeze fixed inputs/argv and actual final PE before any Round119 native run."""
from round119_common import *
import ast,copy,struct,subprocess
COMMON=dict(threads=1,mip_threads=1,gurobi_seed=0,gurobi_presolve=-1,gurobi_version='13.0.2',affinity_mask=4,
    native_limit_offset_seconds=6,hard_stop_offset_seconds=2,shutdown_margin_seconds=30,
    requested_mip_gap=0,requested_mip_gap_abs=0,FeasibilityTol=1e-6,OptimalityTol=1e-6,IntFeasTol=1e-5)
def inspect_input(p):
    text=(ROOT/p['input_path']).read_text();lines=text.splitlines();first=lines[0].split(maxsplit=2)
    V,M=int(first[0]),int(first[1]);Q=ast.literal_eval(first[2])
    assert (V,M,Q)==(p['V'],p['M'],p['Q_vector'])
    assert sha(ROOT/p['input_path'])==p['input_sha256']
    fields={k.strip():ast.literal_eval(v.strip()) for row in lines[1:] if '=' in row for k,v in [row.split('=',1)]}
    assert len(fields['capacity' if 'capacity' in fields else 'capacities'])==V+1
    return dict(V=V,M=M,Q_vector=Q,total_initial=sum(fields['initial'][1:]),total_target=sum(fields['target'][1:]),input_SHA=p['input_sha256'])
def command(p,arm,d,qualification_empty=False):
    import round90_lp_g_g3 as s
    prereg=dict(common=COMMON,candidate_binary=PE.relative_to(ROOT).as_posix(),candidate_binary_sha256=sha(PE))
    args=s.audited_runner_utilities.command_for(prereg,p,'P-GRB',d) if arm in ['P-GRB','P-S'] else s.command_for(prereg,p,'ENS-C',d)
    if arm=='P-S':args+=['--round112-ens-start-compact']
    if arm in ['M-B','MB-PC']:args+=['--round98-state-service','m-binary']
    if arm=='MB-PC':args+=['--round119-proof-contraction']
    if qualification_empty:args+=['--round119-qualification-empty-seed']
    assert '--round100-continuous-quantities' not in args
    assert args[args.index('--time-limit')+1]==str(p['cap_seconds']-6)
    return args
def write_fixture(path,n):
    capacity=[100000,2]+[2 if n==2 else 1]*(n-1);stock=[50000,2 if n==8 else 1]+[0]*(n-1)
    D=[0]+[1]*n;w=[0]+[1]*n;points=[(0.,0.)]+[(float(i),float(i%2)) for i in range(1,n+1)]
    text=f'{n} 1 [{2 if n==8 else 1}]\n'+''.join(f'{k} = {v!r}\n' for k,v in [('capacities',capacity),('initial',stock),('target',D),('weights',w),('min_ratio',[0.]*(n+1)),('points',points)])
    p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():assert p.read_text()==text
    else:p.write_text(text,encoding='utf-8')
    return sha(p)
def prepare():
    old=read(ROOT/'results/unified_exact_round118/production_identity.json')
    assert sha(DLL)==old['DLL_SHA']==DLL_SHA
    assert sha(Path(old['compiler']))==old['compiler_SHA']
    b=PE.read_bytes();offset=struct.unpack_from('<I',b,0x3c)[0];reserve,commit=struct.unpack_from('<QQ',b,offset+24+72)
    assert (reserve,commit)==(old['stack_reserve'],old['stack_commit'])
    cache=(PE.parent/'CMakeCache.txt').read_text();assert 'CMAKE_BUILD_TYPE:STRING=\n' in cache and 'CMAKE_CXX_FLAGS:STRING=\n' in cache
    write(OUT/'production_identity.json',dict(actual_base=BASE,source_commit_before_native=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),
        source_bindings=bindings(),production_PE_path=PE.relative_to(ROOT).as_posix(),production_PE_SHA=sha(PE),
        DLL_path=str(DLL),DLL_SHA=sha(DLL),compiler=old['compiler'],compiler_SHA=old['compiler_SHA'],build_type='',CXX_flags='',
        stack_reserve=reserve,stack_commit=commit,all_methods_same_final_PE=True,R118_PE_unchanged=True,
        previous_R118_PE_SHA=old['production_PE_SHA'],new_default_off_candidate=True,Threads=1,Seed=0,affinity_mask=4,
        exporter_SHA=sha(EXPORTER),default_ENS_changed=False,verified_UTC=utc()))
    n=copy.deepcopy(read(ROOT/'results/unified_exact_round118/input_manifest.json')['roles'][0]);n.update(cap_seconds=5400,method_order=['P-GRB','M-B','MB-PC'],panel_kind='development')
    f=copy.deepcopy(next(p for p in read(OUT/'historical/unified_exact_round98/development_inputs.json')['roles'] if p['id']=='F2'))
    f.update(cap_seconds=1200,method_order=['M-B','MB-PC','P-GRB'],panel_kind='development')
    c=copy.deepcopy(next(p for p in read(OUT/'historical/round98_confirmation_protocol01.json')['roles'] if p['id']=='C2'))
    c.update(id='R98-C2',cap_seconds=1800,method_order=['MB-PC','P-GRB','M-B'],panel_kind='development')
    meta=read(ROOT/'results/unified_exact_round116/input_manifest.json')
    e=copy.deepcopy(next(p for p in meta['roles'] if p['id']=='E50-C1'));e.update(cap_seconds=3600,method_order=['P-GRB','MB-PC','M-B'],panel_kind='conditional_confirmation')
    assert e['input_sha256']=='9de25da5486b956bad260bdb9c9ab50065eaf448ec271336e9eb75a1ba784b4f'
    h=copy.deepcopy(meta['qualification_roles'][0]);assert h['id']=='H100' and h['V']==20
    h.update(cap_seconds=120,method_order=['P-GRB','M-B','MB-PC'],panel_kind='qualification')
    tiny='reference/round119_qualification/micro_chain.txt';enum='reference/round119_qualification/micro_enumeration.txt'
    digest=write_fixture(tiny,8);enum_digest=write_fixture(enum,2)
    q=dict(id='MICRO-CHAIN',scenario_id='round119-explicit-empty-seed-nonperformance-fixture',V=8,M=1,Q_vector=[2],T_seconds=1000,
        pickup_seconds=60,drop_seconds=60,**{'lambda':.15},gurobi_seed=0,input_path=tiny,instance_path=tiny,
        input_sha256=digest,cap_seconds=300,method_order=['MB-PC'],panel_kind='qualification')
    roles=[n,f,c,e,h,q]
    for p in roles:
        p['instance_path']=p['input_path'];p['gurobi_seed']=0;p['lambda']=.15;p['pickup_seconds']=p['drop_seconds']=60
        p.setdefault('scenario_id',p['id']);inspect_input(p)
    write(OUT/'input_manifest.json',dict(development_roles=roles[:3],conditional_confirmation_role=e,qualification_roles=[h,q],
        enum_fixture=dict(input_path=enum,input_SHA=enum_digest,V=2,M=1,Q_vector=[1],T_seconds=1000),
        all_physical_parameters_frozen=True,roles_already_exposed=True,independent_generalization_claim=False))
    groups=[]
    for gn,p in enumerate(roles[:4],1):groups.append(dict(number=gn,id=p['id'],campaign=f'campaign/group{gn:02d}',conditional=gn==4,
        cap_seconds=p['cap_seconds'],methods=p['method_order'],nominal_seconds=3*p['cap_seconds'],management_reserve=120))
    plans=[]
    for name,p in [(g['campaign'],roles[g['number']-1]) for g in groups]+[('qualification/h100',h),('qualification/chain',q)]:
        launches=[]
        for number,arm in enumerate(p['method_order'],1):
            dest=OUT/name/'raw'/f'{number:02d}_{p["id"]}_S0_{arm}';profile=copy.deepcopy(p)
            profile['reference']=dict(fingerprint='REFERENCE_FINGERPRINT',rows='REFERENCE_ROWS',columns='REFERENCE_COLUMNS')
            group_number=next((g['number'] for g in groups if g['campaign']==name),0)
            launches.append(dict(number=number,group_number=group_number,
                global_launch_number=(group_number-1)*3+number if group_number else number,id=p['id'],arm=arm,seed=0,panel=profile,panel_kind=p['panel_kind'],destination=str(dest),
                cap_seconds=p['cap_seconds'],hard_stop_seconds=p['cap_seconds']-2,
                command=command(profile,arm,dest,name=='qualification/chain')))
        plans.append(dict(name=name,launches=launches))
    refs=[]
    for p in roles:
        dest=OUT/'qualification/reference'/p['id']
        refs.append('\t'.join([str(ROOT/p['input_path']),str(p['T_seconds']),'60','60','0.15',str(dest)]))
    (OUT/'qualification').mkdir(parents=True,exist_ok=True)
    (OUT/'qualification/reference.tsv').write_text('\n'.join(refs)+'\n',encoding='utf-8')
    write(OUT/'argv_freeze.json',dict(frozen_UTC=utc(),plans=plans,groups=groups,production_PE_SHA=sha(PE),DLL_SHA=sha(DLL),
        input_manifest_SHA=sha(OUT/'input_manifest.json'),no_formal_weak_initial_seed=True,
        deterministic_cold_reference_readback_slots=['REFERENCE_FINGERPRINT','REFERENCE_ROWS','REFERENCE_COLUMNS'],
        slot_rule='zero-Optimize fixed exporter resolves once before H100/formal; no numeric algorithm choice changes'))
    write(OUT/'protocol.json',dict(round=119,base=BASE,common=COMMON,groups=groups,pairs=[['MB-PC','M-B'],['MB-PC','P-GRB'],['M-B','P-GRB']],
        maximum_starts=40,maximum_outer_seconds=48000,qualification_maximum_starts=12,qualification_maximum_seconds=2400,
        planned_qualification=dict(wrapper_starts=1,native_children=5,outer_cap=1200,H100_caps=120,fixture_cap=300,Optimize_free_exporter=1,
            order='zero-Optimize exporter/finite checks -> explicit micro chain -> H100 P/M-B/MB-PC'),
        formal_development_arms=9,conditional_confirmation_arms=3,formal_nominal_seconds=36000,
        materiality={'a_U':'max(.001,.01*abs(U_C))','a_gap':'max(.001,.10*abs(gap_C))','a_t':'max(30,.10*t_C)'},
        original_evidence_tolerance=1e-7,signed_gap_preserved=True,deadline_not_reset=True,default_ENS_changed=False,
        no_extra_paid_child_probe=True,confirmation_only_after_all_four_original_admission_conditions=True,
        no_formal_retry_or_performance_revision=True,all_online_algorithm_work_in_T_produce=True))
    (OUT/'measurement_policy_v2.md').write_text((ROOT/'results/unified_exact_round118/measurement_policy_v2.md').read_text().split('Budgets are')[0]+
        '\nRound119 has four fixed three-arm groups, the last conditional. Total budgets are 40 starts/48000 outer seconds; qualification 12/2400. Every pending termination, returned-event check, transaction, new model/LP/MIP/Start and serialization is paid within the same absolute producer deadline. Post-seal verification creates no optimization evidence.\n',encoding='utf-8')
    write(OUT/'prospective_helper_freeze.json',dict(helpers=helpers(),source_bindings=bindings(),argv_SHA=sha(OUT/'argv_freeze.json'),PE_SHA=sha(PE)))
    print('fixed inputs, all argv, common final PE and helpers frozen; no native start')
def resolve():
    identity();freeze=read(OUT/'argv_freeze.json');assert freeze['production_PE_SHA']==sha(PE)
    for plan in freeze['plans']:
        camp=OUT/plan['name'];camp.mkdir(parents=True,exist_ok=True)
        launches=copy.deepcopy(plan['launches']);references={}
        for l in launches:
            reference=read(OUT/'qualification/reference'/l['id']/'build.json')
            assert reference['optimizer_calls']==0
            l['panel']['reference']=reference;references[l['id']]=reference
            l['command']=command(l['panel'],l['arm'],Path(l['destination']),plan['name']=='qualification/chain')
        write(camp/'identity.json',dict(prereg=dict(common=COMMON,candidate_binary=PE.relative_to(ROOT).as_posix(),candidate_binary_sha256=sha(PE)),
            prereg_sha256=sha(OUT/'protocol.json'),runner_sha256=sha(ROOT/'scripts/round119_campaign.py'),helpers=helpers(),source_hashes=bindings(),
            candidate_binary_sha256=sha(PE),dll_sha256=sha(DLL),measured_source_commit=identity()['source_commit_before_native'],
            delivery_base_commit=BASE,references=references,launches=launches,measurement_policy_SHA=sha(OUT/'measurement_policy_v2.md')))
    write(OUT/'candidate_identity.json',dict(production_identity_SHA=sha(OUT/'production_identity.json'),production_PE_SHA=sha(PE),DLL_SHA=sha(DLL),
        source_bindings=bindings(),helpers=helpers(),input_manifest_SHA=sha(OUT/'input_manifest.json'),argv_freeze_SHA=sha(OUT/'argv_freeze.json'),
        protocol_SHA=sha(OUT/'protocol.json'),default_ENS_changed=False,
        campaign_identities={p['name']:sha(OUT/p['name']/'identity.json') for p in freeze['plans']}))
if __name__=='__main__':{'prepare':prepare,'resolve':resolve}[sys.argv[1]]()
