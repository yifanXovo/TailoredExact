"""Bound final PE, original four entries, six zero-Optimize references."""
from round122_common import *
import copy, struct
import round120_prepare as original
from round100_idle import ensure_idle
COMMON=dict(original.COMMON,gurobi_seed='per-group frozen 0/1')
EXPORTER=WORK/'build-cache/round122-reference/Round122Reference.exe'
ARCHIVE=Path('C:/Users/Administrator/.codex/worktrees/round120-native-proof-disjunction/ExactEBRP/build/research/round120/libexact_ebrp_core.a')
HREF=Path('C:/Users/Administrator/.codex/worktrees/round121-frozen-d1-confirmation/ExactEBRP/results/unified_exact_round121/qualification/reference/H100')

def command(p,arm,d):
    import round90_lp_g_g3 as s
    prereg=dict(common=dict(COMMON,gurobi_seed=p['gurobi_seed']),candidate_binary=str(PE),candidate_binary_sha256=PE_SHA)
    args=s.audited_runner_utilities.command_for(prereg,p,'P-GRB',d) if arm=='P-GRB' else s.command_for(prereg,p,'ENS-C',d)
    if arm in ['M-B','MB-D1']:args+=['--round98-state-service','m-binary']
    if arm=='MB-D1':args+=['--round120-native-proof-d1']
    args[args.index('--gurobi-seed')+1]=str(p['gurobi_seed'])
    assert args.count('--gurobi-seed')==1 and args[args.index('--time-limit')+1]==str(p['cap_seconds']-6)
    assert not any(x.startswith(('--round119','--round120-qualification','--round100-continuous-quantities')) for x in args)
    assert arm in METHODS
    return args

def prepare():
    workspace();identity();m=read(OUT/'input_manifest.json');groups=[];plans=[]
    for n,p in enumerate(m['roles'],1):
        assert sha(ROOT/p['input_path'])==p['input_sha256']
        groups.append(dict(number=n,id=p['id'],source=p['source'],V=p['V'],seed=p['gurobi_seed'],campaign=f'campaign/group{n:02d}',methods=p['method_order'],
            cap_seconds=p['cap_seconds'],nominal_seconds=4*p['cap_seconds'],management_reserve=120,fixed_unconditional=True,panel_kind=p['panel_kind']))
    h=copy.deepcopy(m['qualification_roles'][0]);h0=copy.deepcopy(h)
    h0.update(gurobi_seed=0,method_order=['MB-D1'])
    for name,p in [(g['campaign'],m['roles'][g['number']-1]) for g in groups]+[('qualification/h100_seed1',h),('qualification/h100_seed0',h0)]:
        gn=next((g['number'] for g in groups if g['campaign']==name),0);launches=[]
        for n,arm in enumerate(p['method_order'],1):
            d=OUT/name/'raw'/f'{n:02d}_{p["id"]}_S{p["gurobi_seed"]}_{arm}';profile=copy.deepcopy(p)
            profile['reference']=dict(fingerprint='REFERENCE_FINGERPRINT',rows='REFERENCE_ROWS',columns='REFERENCE_COLUMNS')
            launches.append(dict(number=n,group_number=gn,global_launch_number=(gn-1)*4+n if gn else n,id=p['id'],arm=arm,seed=p['gurobi_seed'],
                panel=profile,panel_kind=p['panel_kind'],destination=str(d),cap_seconds=p['cap_seconds'],hard_stop_seconds=p['cap_seconds']-2,
                command=command(profile,arm,d)))
        plans.append(dict(name=name,launches=launches))
    assert len(groups)==8 and sum(g['nominal_seconds'] for g in groups)==79200
    write(OUT/'argv_freeze.json',dict(plans=plans,groups=groups,PE_SHA=PE_SHA,DLL_SHA=DLL_SHA,UTC=utc(),formal_arms=32,formal_pairs=48,
        reference_slots='six fresh zero-Optimize original compact builds; finite existing H100 canonical authority',no_cross_arm_solution_bound_proof_or_Start=True))
    write(OUT/'protocol.json',dict(round=122,base=BASE,production_source=SOURCE,common=COMMON,groups=groups,pairs=PAIRS,
        maximum_outer_seconds=TOTAL_LIMIT,qualification_soft_seconds=QUAL_PLAN,qualification_authorized_seconds=QUAL_LIMIT,
        qualification_start_count_is_not_a_hard_gate=True,formal_arms=32,formal_pairs=48,new_problems=6,fixed_Seed1_blocks=2,
        formal_nominal_seconds=79200,management_reference=960,qualification_plan=dict(children=6,wrapper=1,reference_Optimize=0,
            real_known_fixture_CLI=dict(Seed1=METHODS,Seed0=['MB-D1']),each_CLI_cap=120,outer_cap=1800),
        paired_rule='unchanged round108_decisions.pair; independently recompute all48',native_reserve=30,evidence_tolerance=1e-7,
        own_H_seed=20260626,own_H_semantics='full24+1 closure/exchange',all_online_work_in_T_produce=True,
        clock='T_verify closes after added model/event/Start audits and all required serialization; group reconciliation separately charged',
        no_extra_role_variant_or_valid_performance_retry=True,default_ENS_changed=False,D0_ablation_only_not_run=True,MB_PC_stopped=True,
        stage_priority=['PROOF_RELIABILITY_PRIORITY','BLOCKED','DO_NOT_SELECT_D1_AS_PAPER_PRIMARY','FREEZE_D1_AS_PAPER_BENCHMARK_CANDIDATE','BENCHMARK_MIXED_NO_NEW_PRIMARY_SELECTION']))
    policy=(ROOT/'results/unified_exact_round120/measurement_policy_v2.md').read_text(encoding='utf-8').split('R120:')[0]
    (OUT/'measurement_policy_v2.md').write_text(policy+'\nR122: 32 unconditional positions, 48 pairs, six new problems and two fixed Seed1 groups. T_produce pays all own online work and seal; T_verify pays all subsequent required audits, including D1 extension; group reconciliation is separate. Outer100000, qualification soft3000/authorized6000, no start-count hard ceiling. Same original reserve30.\n',encoding='utf-8')
    q=OUT/'qualification';q.mkdir(exist_ok=True)
    (q/'reference_batch.tsv').write_text(''.join('\t'.join(map(str,[ROOT/p['input_path'],p['T_seconds'],60,60,.15,q/'reference'/p['id']]))+'\n' for p in m['new_roles']),encoding='utf-8')
    target=q/'reference/H100';target.mkdir(parents=True,exist_ok=False)
    for name in ['build.json','original.lp']:
        src=HREF/name;shutil.copyfile(src,target/name);assert sha(src)==sha(target/name)
    assert read(target/'build.json')['optimizer_calls']==0 and sha(target/'original.lp')==read(target/'build.json')['canonical_sha256']
    write(q/'known_reference_binding.json',dict(source=str(HREF),files={n:sha(target/n) for n in ['build.json','original.lp']},
        original_input_SHA=h['input_sha256'],no_solver_or_performance_result_reused=True))
    write(OUT/'prospective_helper_freeze.json',dict(source_bindings=bindings(),helpers=helpers(),PE_SHA=PE_SHA,
        argv_SHA=sha(OUT/'argv_freeze.json'),protocol_SHA=sha(OUT/'protocol.json')))
    print('32 positions/eight groups, 48 pairs and five known-fixture CLI frozen; no Optimize')

def compile_exporter():
    workspace();ensure_idle();prod=identity();tick=time.perf_counter();d=OUT/'engineering/reference_compile';d.mkdir(parents=True,exist_ok=False)
    compiler=Path(prod['compiler']);assert sha(compiler)==prod['compiler_SHA'];EXPORTER.parent.mkdir(parents=True,exist_ok=True)
    cmd=[str(compiler),'-std=c++17','-DEXACT_EBRP_ENABLE_GUROBI=1','-I'+str(ROOT/'include'),'-ID:/gurobi1302/win64/include',str(ROOT/'scripts/round122_reference.cpp'),str(ARCHIVE),'-o',str(EXPORTER)]
    write(d/'launch.json',dict(command=cmd,compiler_SHA=sha(compiler),frozen_core_archive_SHA=sha(ARCHIVE),source_commit=SOURCE,production_PE_SHA_before=sha(PE),Optimize=0))
    with (d/'stdout.log').open('xb') as so,(d/'stderr.log').open('xb') as se:r=subprocess.run(cmd,cwd=ROOT,env=environment(),stdout=so,stderr=se,timeout=600)
    write(d/'receipt.json',dict(exit_code=r.returncode,engineering_seconds=time.perf_counter()-tick,Optimize=0,native_starts=0,
        production_PE_SHA_after=sha(PE),exporter_SHA=sha(EXPORTER) if EXPORTER.exists() else None))
    assert r.returncode==0;identity();print('Six-input zero-Optimize exporter compiled; original final PE unchanged')

def resolve():
    identity();f=read(OUT/'argv_freeze.json')
    for plan in f['plans']:
        camp=OUT/plan['name'];camp.mkdir(parents=True,exist_ok=True);launches=copy.deepcopy(plan['launches']);refs={}
        for l in launches:
            ref=OUT/'qualification/reference'/l['id'];build=read(ref/'build.json')
            assert build['optimizer_calls']==0 and sha(ref/'original.lp')==build['canonical_sha256']
            l['panel']['reference']=build;refs[l['id']]=build;l['command']=command(l['panel'],l['arm'],Path(l['destination']))
        # One campaign-local authority per role; these are small, immutable cold references.
        for role in refs:
            target=camp/'reference'/role;assert not target.exists();shutil.copytree(OUT/'qualification/reference'/role,target)
        write(camp/'identity.json',dict(prereg=dict(common=dict(COMMON,gurobi_seed=launches[0]['seed']),candidate_binary=str(PE),candidate_binary_sha256=PE_SHA),
            prereg_sha256=sha(OUT/'protocol.json'),runner_sha256=sha(ROOT/'scripts/round122_campaign.py'),helpers=helpers(),source_hashes=bindings(),
            candidate_binary_sha256=PE_SHA,dll_sha256=DLL_SHA,measured_source_commit=SOURCE,delivery_base_commit=BASE,references=refs,launches=launches,
            measurement_policy_SHA=sha(OUT/'measurement_policy_v2.md')))
    write(OUT/'candidate_identity.json',dict(production_identity_SHA=sha(OUT/'production_identity.json'),production_PE_SHA=PE_SHA,DLL_SHA=DLL_SHA,
        source_bindings=bindings(),helpers=helpers(),input_manifest_SHA=sha(OUT/'input_manifest.json'),argv_freeze_SHA=sha(OUT/'argv_freeze.json'),protocol_SHA=sha(OUT/'protocol.json'),
        default_ENS_changed=False,campaign_identities={p['name']:sha(OUT/p['name']/'identity.json') for p in f['plans']}))

def refreeze():
    # Only administrative/read-only revisions before any real CLI producer exists.
    old=read(OUT/'candidate_identity.json');f=read(OUT/'argv_freeze.json')
    assert not list((OUT/'campaign').glob('*/raw/*/launch.json'))
    assert not list((OUT/'qualification').glob('h100_*/raw/*/launch.json'))
    hs=helpers()
    for plan in f['plans']:
        p=OUT/plan['name']/'identity.json';i=read(p);i['helpers']=hs;write(p,i)
    value=dict(old,helpers=hs,campaign_identities={p['name']:sha(OUT/p['name']/'identity.json') for p in f['plans']})
    write(OUT/'candidate_identity.json',value)
    write(OUT/'prospective_helper_freeze.json',dict(source_bindings=bindings(),helpers=hs,PE_SHA=PE_SHA,
        argv_SHA=sha(OUT/'argv_freeze.json'),protocol_SHA=sha(OUT/'protocol.json')))
    write(OUT/'qualification/pre_CLI_helper_revision.json',dict(before=old['helpers'],after=hs,
        reason='independent contract review: precise actual/uncertain starts; complete verification clock; invalid-input blocker and exact group sets',
        before_any_CLI_or_formal_producer=True,zero_Optimize_references_unchanged=True,production_source_or_PE_changed=False))

if __name__=='__main__':{'prepare':prepare,'compile':compile_exporter,'resolve':resolve,'refreeze':refreeze}[sys.argv[1]]()
