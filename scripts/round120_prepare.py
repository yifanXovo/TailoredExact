"""Fixed R120 roles, argv, qualified runtime identity; no native process."""
from round120_common import *
import ast,copy,struct
COMMON=dict(threads=1,mip_threads=1,gurobi_seed=0,gurobi_presolve=-1,gurobi_version='13.0.2',affinity_mask=4,
    native_limit_offset_seconds=6,hard_stop_offset_seconds=2,shutdown_margin_seconds=30,
    requested_mip_gap=0,requested_mip_gap_abs=0,FeasibilityTol=1e-6,OptimalityTol=1e-6,IntFeasTol=1e-5)
EXPORTER=ROOT/'build/research/round120/Round120Qualification.exe'
DIAGNOSTIC=ROOT/'build/research/round120/Round120LpDiagnostics.exe'
def command(p,arm,d,empty=False,export=False):
    import round90_lp_g_g3 as s
    prereg=dict(common=COMMON,candidate_binary=PE.relative_to(ROOT).as_posix(),candidate_binary_sha256=sha(PE))
    args=s.audited_runner_utilities.command_for(prereg,p,'P-GRB',d) if arm in ['P-GRB','P-S'] else s.command_for(prereg,p,'ENS-C',d)
    if arm=='P-S':args+=['--round112-ens-start-compact']
    if arm in ['M-B','MB-D0','MB-D1']:args+=['--round98-state-service','m-binary']
    if arm in ['MB-D0','MB-D1']:args+=['--round120-native-proof-'+arm[-2:].lower()]
    if empty:args+=['--round120-qualification-empty-seed']
    if export:args+=['--round120-qualification-export-only']
    assert '--round119-proof-contraction' not in args and '--round100-continuous-quantities' not in args
    assert args[args.index('--time-limit')+1]==str(p['cap_seconds']-6)
    return args
def inspect_input(p):
    raw=(ROOT/p['input_path']).read_text();lines=raw.splitlines();v,m,q=lines[0].split(maxsplit=2)
    assert (int(v),int(m),ast.literal_eval(q))==(p['V'],p['M'],p['Q_vector'])
    assert sha(ROOT/p['input_path'])==p['input_sha256']
def prepare():
    old=read(OLD/'results/unified_exact_round119/input_manifest.json')
    selected={p['id']:copy.deepcopy(p) for p in old['development_roles']+old['qualification_roles']}
    f,c,n=selected['F2'],selected['R98-C2'],selected['N40-R1-S']
    # Input/physical metadata only: explicitly discard every historical fleet,
    # diagnostic cutoff/bound and old cold-reference field from the plans.
    for p in selected.values():
        for k in list(p):
            if k.startswith(('historical_','diagnostic_')) or k=='reference':p.pop(k)
        p['instance_path']=p['input_path'];inspect_input(p)
    f.update(cap_seconds=1200,method_order=['P-GRB','M-B','MB-D0','MB-D1'],panel_kind='core')
    c.update(cap_seconds=1800,method_order=['MB-D1','MB-D0','M-B','P-GRB'],panel_kind='core')
    n.update(cap_seconds=5400,method_order=['M-B','MB-D1','P-GRB','MB-D0'],panel_kind='conditional_followup')
    h,q=selected['H100'],selected['MICRO-CHAIN'];h.update(cap_seconds=120,
        method_order=['P-GRB','ENS-C','M-B','P-S','MB-D0','MB-D1'],panel_kind='qualification')
    q.update(cap_seconds=300,method_order=['MB-D1'],panel_kind='qualification',scenario_id='round120-explicit-legal-empty-start')
    enum=dict(old['enum_fixture'],id='MICRO-ENUM',input_sha256=old['enum_fixture']['input_SHA'],instance_path=old['enum_fixture']['input_path'],
        pickup_seconds=60,drop_seconds=60,**{'lambda':.15})
    write(OUT/'input_manifest.json',dict(core_roles=[f,c],conditional_role=n,qualification_roles=[h,q],enum_fixture=enum,
        historical_fleets_cutoffs_bounds_removed=True,E50_not_authorized=True,independent_generalization_claim=False))
    prod=read(OLD/'results/unified_exact_round119/production_identity.json')
    assert sha(DLL)==prod['DLL_SHA']==DLL_SHA and sha(prod['compiler'])==prod['compiler_SHA']
    b=PE.read_bytes();offset=struct.unpack_from('<I',b,0x3c)[0];reserve,commit=struct.unpack_from('<QQ',b,offset+24+72)
    assert (reserve,commit)==(prod['stack_reserve'],prod['stack_commit'])
    cache=(PE.parent/'CMakeCache.txt').read_text();assert 'CMAKE_BUILD_TYPE:STRING=\n' in cache and 'CMAKE_CXX_FLAGS:STRING=\n' in cache
    write(OUT/'production_identity.json',dict(actual_base=BASE,
        source_commit_before_native=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),
        source_bindings=bindings(),production_PE_path=PE.relative_to(ROOT).as_posix(),production_PE_SHA=sha(PE),
        DLL_path=str(DLL),DLL_SHA=sha(DLL),compiler=prod['compiler'],compiler_SHA=prod['compiler_SHA'],
        build_type='',CXX_flags='',stack_reserve=reserve,stack_commit=commit,
        qualification_exporter_SHA=sha(EXPORTER),LP_diagnostic_SHA=sha(DIAGNOSTIC),
        all_methods_same_final_PE=True,Threads=1,Seed=0,affinity_mask=4,default_ENS_changed=False,
        R119_PE_preserved=True,R119_stop_preserved=True,verified_UTC=utc()))
    groups=[dict(number=j,id=p['id'],campaign=f'campaign/group{j:02d}',conditional=j==3,
        cap_seconds=p['cap_seconds'],methods=p['method_order'],nominal_seconds=4*p['cap_seconds'],management_reserve=120)
        for j,p in enumerate([f,c,n],1)]
    plans=[]
    for name,p in [(g['campaign'],[f,c,n][g['number']-1]) for g in groups]+[('qualification/chain',q),('qualification/h100',h)]:
        launches=[]
        for number,arm in enumerate(p['method_order'],1):
            dest=OUT/name/'raw'/f'{number:02d}_{p["id"]}_S0_{arm}';profile=copy.deepcopy(p)
            profile['reference']=dict(fingerprint='REFERENCE_FINGERPRINT',rows='REFERENCE_ROWS',columns='REFERENCE_COLUMNS')
            gn=next((g['number'] for g in groups if g['campaign']==name),0)
            launches.append(dict(number=number,group_number=gn,global_launch_number=(gn-1)*4+number if gn else number,
                id=p['id'],arm=arm,seed=0,panel=profile,panel_kind=p['panel_kind'],destination=str(dest),
                cap_seconds=p['cap_seconds'],hard_stop_seconds=p['cap_seconds']-2,command=command(profile,arm,dest,name=='qualification/chain')))
        plans.append(dict(name=name,launches=launches))
    exports=[]
    for p in [f,c]:
        profile=copy.deepcopy(p);profile.update(cap_seconds=120,panel_kind='paid_proof_export_qualification')
        dest=OUT/'qualification'/('export_'+p['id'])
        exports.append(dict(id=p['id'],destination=str(dest),cap_seconds=120,command=command(profile,'MB-D1',dest,export=True),panel=profile))
    write(OUT/'argv_freeze.json',dict(plans=plans,groups=groups,qualification_exports=exports,PE_SHA=sha(PE),DLL_SHA=sha(DLL),
        formal_weak_start_or_export_flag=False,frozen_UTC=utc(),reference_slots='resolved exactly once by fixed zero-Optimize exporter'))
    qdir=OUT/'qualification';qdir.mkdir(exist_ok=True)
    refs=[f,c,n,h,q,enum]
    (qdir/'reference.tsv').write_text(''.join('\t'.join([str(ROOT/p['input_path']),str(p['T_seconds']),'60','60','0.15',str(qdir/'reference'/p['id'])])+'\n' for p in refs),encoding='utf-8')
    steps=[dict(kind='zero_Optimize_native_matrix_Start_reference',command=[str(EXPORTER),str(qdir/'reference.tsv'),str(qdir/'native_contract02'),str(ROOT/enum['input_path'])],outer_cap=300,Optimize=0),
        dict(kind='real_CLI_chain',plan='qualification/chain',outer_cap=300,Optimize='original_controller_actual_requests'),
        *[dict(kind='paid_proof_export',**e,outer_cap=120,Optimize='only_original_root_and_child_LPs') for e in exports],
        dict(kind='fixed_six_complete_LP_diagnostics',command=[str(DIAGNOSTIC),str(qdir/'diagnostics.tsv')],outer_cap=850,
            Optimize=6,per_Optimize_cap=120,roles=['F2','R98-C2'],order=['D0 original objective','D1 original objective','D0 maximum conditional violation']),
        dict(kind='H100_final_PE_six_CLI',plan='qualification/h100',outer_cap=720,children=6)]
    write(OUT/'qualification_plan.json',dict(steps=steps,children=11,wrapper=1,outer_cap=3000,
        total_qualification_limit_starts=16,total_qualification_limit_seconds=3600,diagnostic_values='deterministic own exported proof slots only',
        no_formal_feedback=True,no_hidden_grid=True))
    write(OUT/'protocol.json',dict(round=120,base=BASE,common=COMMON,groups=groups,
        pairs=[['MB-D1','M-B'],['MB-D1','P-GRB'],['MB-D1','MB-D0'],['MB-D0','M-B'],['MB-D0','P-GRB'],['M-B','P-GRB']],
        maximum_starts=40,maximum_outer_seconds=48000,qualification_maximum_starts=16,qualification_maximum_seconds=3600,
        core_arms=8,conditional_N40_arms=4,formal_nominal_seconds=33600,management_reserve=360,
        materiality='unchanged round108_decisions.pair, replayed on all nine R119 published pairs',
        original_evidence_tolerance=1e-7,no_extra_probe=True,no_valid_proof_triggered_interrupt=True,
        conditional_admission='all core qualified; actual D1 exposure; material D1/M-B gain; material D1/D0 gain and no severe D0 loss; no severe P or two P losses; D1 certificates >= M-B',
        no_formal_retry_revision_or_additional_role=True,default_ENS_changed=False,all_online_work_in_T_produce=True))
    text=(ROOT/'results/unified_exact_round118/measurement_policy_v2.md').read_text(encoding='utf-8').split('Budgets are')[0]
    (OUT/'measurement_policy_v2.md').write_text(text+'\nR120: same three-clock policy, 40/48000 outer budget, qualification 16/3600; all installation, audits, mapping, writes and callbacks paid online. Eight fixed core arms and four predeclared conditional N40 positions. No unexecuted counterfactual cost subtraction.\n',encoding='utf-8')
    write(OUT/'prospective_helper_freeze.json',dict(source_bindings=bindings(),helpers=helpers(),PE_SHA=sha(PE),argv_SHA=sha(OUT/'argv_freeze.json')))
    print('Round120 fixed inputs/argv/final PE/qualification plan frozen; Optimize=0')
def resolve():
    identity();f=read(OUT/'argv_freeze.json')
    for plan in f['plans']:
        camp=OUT/plan['name'];camp.mkdir(parents=True,exist_ok=True);launches=copy.deepcopy(plan['launches']);refs={}
        for l in launches:
            reference=read(OUT/'qualification/reference'/l['id']/'build.json');assert reference['optimizer_calls']==0
            l['panel']['reference']=reference;refs[l['id']]=reference
            l['command']=command(l['panel'],l['arm'],Path(l['destination']),plan['name']=='qualification/chain')
        # The inherited current-only reader requires these fresh, purely
        # input-dependent cold matrix authorities inside each campaign.
        for role in refs:
            source=OUT/'qualification/reference'/role;target=camp/'reference'/role;target.mkdir(parents=True,exist_ok=True)
            for p in sorted(source.iterdir()):
                if not p.is_file():continue
                dest=target/p.name
                if dest.exists():assert sha(dest)==sha(p)
                else:dest.write_bytes(p.read_bytes())
        write(camp/'identity.json',dict(prereg=dict(common=COMMON,candidate_binary=PE.relative_to(ROOT).as_posix(),candidate_binary_sha256=sha(PE)),
            prereg_sha256=sha(OUT/'protocol.json'),runner_sha256=sha(ROOT/'scripts/round120_campaign.py'),helpers=helpers(),source_hashes=bindings(),
            candidate_binary_sha256=sha(PE),dll_sha256=sha(DLL),measured_source_commit=identity()['source_commit_before_native'],
            delivery_base_commit=BASE,references=refs,launches=launches,measurement_policy_SHA=sha(OUT/'measurement_policy_v2.md')))
    write(OUT/'candidate_identity.json',dict(production_identity_SHA=sha(OUT/'production_identity.json'),production_PE_SHA=sha(PE),DLL_SHA=sha(DLL),
        source_bindings=bindings(),helpers=helpers(),input_manifest_SHA=sha(OUT/'input_manifest.json'),argv_freeze_SHA=sha(OUT/'argv_freeze.json'),
        protocol_SHA=sha(OUT/'protocol.json'),default_ENS_changed=False,
        campaign_identities={p['name']:sha(OUT/p['name']/'identity.json') for p in f['plans']}))
if __name__=='__main__':{'prepare':prepare,'resolve':resolve}[sys.argv[1]]()
