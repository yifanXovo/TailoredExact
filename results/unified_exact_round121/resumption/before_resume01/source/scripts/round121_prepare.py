"""Manifest-only role/Seed/cap wiring; original PE and optimizer settings."""
from round121_common import *
import ast,copy,csv,collections,shutil,traceback
import round120_prepare as prior
from round100_idle import ensure_idle
COMMON=dict(prior.COMMON,gurobi_seed='per-role frozen 0/1')
EXPORTER=ROOT/'build/research/round121-reference/Round121Reference.exe'
ARCHIVE=Path('C:/Users/Administrator/.codex/worktrees/round120-native-proof-disjunction/ExactEBRP/build/research/round120/libexact_ebrp_core.a')
def command(p,arm,d):
    args=prior.command(p,arm,d);args[args.index('--gurobi-seed')+1]=str(p['gurobi_seed'])
    assert args.count('--gurobi-seed')==1
    assert '--round120-qualification-empty-seed' not in args and '--round120-qualification-export-only' not in args
    return args
def prepare():
    identity();m=read(OUT/'input_manifest.json');groups=[];plans=[];counter=0
    for n,p in enumerate(m['roles'],1):
        assert sha(ROOT/p['input_path'])==p['input_sha256']
        v,vehicles,q=(ROOT/p['input_path']).read_text().splitlines()[0].split(maxsplit=2)
        assert (int(v),int(vehicles),ast.literal_eval(q))==(p['V'],p['M'],p['Q_vector'])
        groups.append(dict(number=n,id=p['id'],seed=p['gurobi_seed'],campaign=f'campaign/group{n:02d}',methods=p['method_order'],
            cap_seconds=p['cap_seconds'],nominal_seconds=len(p['method_order'])*p['cap_seconds'],management_reserve=120,
            fixed_unconditional=True,panel_kind=p['panel_kind']))
    for name,p in [(g['campaign'],m['roles'][g['number']-1]) for g in groups]+[('qualification/h100',m['qualification_roles'][0])]:
        gn=next((g['number'] for g in groups if g['campaign']==name),0);launches=[]
        for number,arm in enumerate(p['method_order'],1):
            if gn:counter+=1
            d=OUT/name/'raw'/f'{number:02d}_{p["id"]}_S{p["gurobi_seed"]}_{arm}';profile=copy.deepcopy(p)
            profile['reference']=dict(fingerprint='REFERENCE_FINGERPRINT',rows='REFERENCE_ROWS',columns='REFERENCE_COLUMNS')
            launches.append(dict(number=number,group_number=gn,global_launch_number=counter if gn else number,
                id=p['id'],arm=arm,seed=p['gurobi_seed'],panel=profile,panel_kind=p['panel_kind'],destination=str(d),
                cap_seconds=p['cap_seconds'],hard_stop_seconds=p['cap_seconds']-2,command=command(profile,arm,d)))
        plans.append(dict(name=name,launches=launches))
    assert counter==16 and sum(g['nominal_seconds'] for g in groups)==37200
    write(OUT/'argv_freeze.json',dict(plans=plans,groups=groups,PE_SHA=PE_SHA,DLL_SHA=DLL_SHA,frozen_UTC=utc(),
        no_weak_H_export_diagnostic_or_cross_arm_input=True,reference_slots='new 3 from one zero-Optimize batch; existing F2/C2/H100 safe cold references'))
    write(OUT/'protocol.json',dict(round=121,base=BASE,production_source=SOURCE,common=COMMON,groups=groups,
        maximum_starts=40,maximum_outer_seconds=48000,qualification_maximum_starts=8,qualification_maximum_seconds=1800,
        formal_arms=16,formal_pairs=18,new_problems=3,known_Seed1_blocks=2,formal_nominal_seconds=37200,management_reserve=600,
        qualification_plan=dict(parent=1,reference_exporter=1,H100_Seed1_children=4,outer_cap=1200,each_CLI_cap=120,exporter_cap=300),
        paired_rule='unchanged round108_decisions.pair; independent all18 R120 replay',
        no_formal_retry_revision_additional_role_Seed_or_window=True,default_ENS_changed=False,D0_only_F2_Seed1=True,
        all_online_work_in_T_produce=True,native_reserve=30,evidence_tolerance=1e-7,own_H_seed=20260626,own_H_semantics='full24+1 closure/exchange',
        stage_priority=['PROOF_RELIABILITY_PRIORITY','BLOCKED','STOP_FROZEN_D1_CONFIRMATION','ADVANCE_FROZEN_D1_TO_PAPER_BENCHMARK','RETAIN_D1_AS_DEVELOPMENT_COMPONENT']))
    policy=(ROOT/'results/unified_exact_round120/measurement_policy_v2.md').read_text(encoding='utf-8')
    (OUT/'measurement_policy_v2.md').write_text(policy.split('R120:')[0]+'\nR121: frozen production PE; 16 unconditional positions, 5 wrappers, 18 pairs, 3 prospective same-source problems and 2 known Seed1 blocks. Total40/48000, qualification8/1800. Each own H/LP/Start and all online work paid; native reserve30 unchanged. Group verification is group outer cost; no unexecuted counterfactual subtraction.\n',encoding='utf-8')
    q=OUT/'qualification';q.mkdir(exist_ok=True)
    (q/'reference_batch.tsv').write_text(''.join('\t'.join(map(str,[ROOT/p['input_path'],p['T_seconds'],60,60,.15,q/'reference'/p['id']]))+'\n' for p in m['new_roles']),encoding='utf-8')
    write(OUT/'prospective_helper_freeze.json',dict(source_bindings=bindings(),helpers=helpers(),PE_SHA=PE_SHA,
        argv_SHA=sha(OUT/'argv_freeze.json'),protocol_SHA=sha(OUT/'protocol.json')))
    print('all16 positions/five wrappers and H100 four Seed1 CLI frozen; no Optimize')
def compile_exporter():
    ensure_idle();identity();tick=time.perf_counter();d=OUT/'engineering/reference_compile02';d.mkdir(parents=True,exist_ok=False)
    compiler=Path(identity()['compiler']);assert sha(compiler)==identity()['compiler_SHA'];EXPORTER.parent.mkdir(parents=True,exist_ok=True)
    cmd=[str(compiler),'-std=c++17','-DEXACT_EBRP_ENABLE_GUROBI=1','-I'+str(ROOT/'include'),'-ID:/gurobi1302/win64/include',str(ROOT/'scripts/round121_reference.cpp'),str(ARCHIVE),'-o',str(EXPORTER)]
    write(d/'launch.json',dict(command=cmd,compiler_SHA=sha(compiler),frozen_core_archive_SHA=sha(ARCHIVE),source_commit=SOURCE,
        production_PE_SHA_before=sha(PE),Optimize=0,native_starts=0,engineering=True))
    with (d/'stdout.log').open('xb') as so,(d/'stderr.log').open('xb') as se:r=subprocess.run(cmd,cwd=ROOT,env=environment(),stdout=so,stderr=se,timeout=600)
    write(d/'receipt.json',dict(exit_code=r.returncode,seconds=time.perf_counter()-tick,Optimize=0,native_starts=0,
        production_PE_SHA_after=sha(PE),exporter_SHA=sha(EXPORTER) if EXPORTER.exists() else None))
    assert r.returncode==0;identity();print('read-only batch exporter compiled; original production PE unchanged')
def resolve():
    identity();m=read(OUT/'input_manifest.json');f=read(OUT/'argv_freeze.json')
    for p in [m['roles'][0],m['roles'][2],m['qualification_roles'][0]]:
        source=ARCHIVE.parents[3]/'results/unified_exact_round120/qualification/reference'/p['id'];dest=OUT/'qualification/reference'/p['id']
        assert not dest.exists();shutil.copytree(source,dest)
        assert read(dest/'build.json')['optimizer_calls']==0
    for plan in f['plans']:
        camp=OUT/plan['name'];camp.mkdir(parents=True,exist_ok=True);launches=copy.deepcopy(plan['launches']);refs={}
        for l in launches:
            ref=OUT/'qualification/reference'/l['id'];build=read(ref/'build.json')
            assert build['optimizer_calls']==0 and sha(ref/'original.lp')==build['canonical_sha256']
            l['panel']['reference']=build;refs[l['id']]=build;l['command']=command(l['panel'],l['arm'],Path(l['destination']))
        for role in refs:shutil.copytree(OUT/'qualification/reference'/role,camp/'reference'/role)
        write(camp/'identity.json',dict(prereg=dict(common=dict(COMMON,gurobi_seed=launches[0]['seed']),candidate_binary=PE.relative_to(ROOT).as_posix(),candidate_binary_sha256=PE_SHA),
            prereg_sha256=sha(OUT/'protocol.json'),runner_sha256=sha(ROOT/'scripts/round121_campaign.py'),helpers=helpers(),source_hashes=bindings(),
            candidate_binary_sha256=PE_SHA,dll_sha256=DLL_SHA,measured_source_commit=SOURCE,delivery_base_commit=BASE,references=refs,launches=launches,
            measurement_policy_SHA=sha(OUT/'measurement_policy_v2.md')))
    write(OUT/'candidate_identity.json',dict(production_identity_SHA=sha(OUT/'production_identity.json'),production_PE_SHA=PE_SHA,DLL_SHA=DLL_SHA,
        source_bindings=bindings(),helpers=helpers(),input_manifest_SHA=sha(OUT/'input_manifest.json'),argv_freeze_SHA=sha(OUT/'argv_freeze.json'),protocol_SHA=sha(OUT/'protocol.json'),
        default_ENS_changed=False,campaign_identities={p['name']:sha(OUT/p['name']/'identity.json') for p in f['plans']}))
if __name__=='__main__':{'prepare':prepare,'compile':compile_exporter,'resolve':resolve}[sys.argv[1]]()
