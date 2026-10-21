"""Once-only fixed manifest and small inherited-runner adapters, no Optimize."""
from round128_common import *
import copy

def initialize():
    assert git('rev-parse','HEAD').decode().strip()==BASE
    assert sha(E0)==E0_SHA and sha(E1)==E1_SHA and sha(DLL)==DLL_SHA
    prior=read(ROOT/'results/unified_exact_round127/E1_frozen.json')
    assert sha(COMPILER)==prior['compiler_SHA'] and sha(ARCHIVE)==prior['original_archive_SHA']
    for p in [OUT,TEMP,EVIDENCE,BUILD]:
        p.mkdir(parents=True,exist_ok=True)
        assert p.resolve().is_relative_to(WORK.resolve())
    write(OUT/'initialization.json',dict(UTC=utc(),base=BASE,R127_science='6b4f2e662b709590479732cfca2c6c3c5ff3dd20',
        PR189=dict(state='open',draft=True,merged=False,head=BASE,branch='codex/round127-integrated-diagnostics'),
        remote='https://github.com/yifanXovo/TailoredExact.git',applicable_AGENTS=[],
        main_HEAD='8dc274eb34ee6d8a575f0b94b57ef04476efc0f1',main_dirty_preserved=True,initially_active_solvers=[],
        E0_SHA=sha(E0),E1_SHA=sha(E1),DLL_SHA=sha(DLL),compiler_SHA=sha(COMPILER),frozen_core_archive_SHA=sha(ARCHIVE),
        free_bytes=shutil.disk_usage(WORK).free,peak_increment_allowance_bytes=20*1024**3,
        preledger_outer_upper_seconds=180,preledger_explanation='Conservative machine-work allowance for initial bounded reads, remote check, linked sparse checkout and setup; not conversation wall time. Subsequent substantial child lifetimes are separately metered.',
        R127_three_MD_arms_remain_unstarted=True,total_outer_limit=TOTAL_LIMIT,qualification_limit=QUAL_LIMIT))
    shutil.copyfile(ROOT/'results/unified_exact_round127/E0_identity.json',OUT/'E0_identity.json')
    shutil.copyfile(Path('C:/Users/Administrator/.codex/attachments/98dfaa99-db9c-4b67-8c46-ef9e274444d9/宸茬矘璐寸殑鏂囨湰.txt'),OUT/'goal.md')
    roles=copy.deepcopy(read(ROOT/'results/unified_exact_round127/input_manifest.json')['core_roles'])
    for p in roles:
        path=ROOT/p['input_path']
        if sha(path)!=p['input_sha256']:
            before=sha(path);path.write_bytes(git('show',BASE+':'+p['input_path']))
            write(OUT/('input_checkout_'+p['id']+'.json'),dict(before=before,blob_sha256=sha(path),source=BASE,normalization_only=True))
        assert sha(path)==p['input_sha256']
    groups=[]
    for j,(k,seed,methods) in enumerate([(0,0,['P','MB','MD-R','MS2']),(1,0,['MB','MD-R','MS2','P']),
        (2,0,['MD-R','MS2','P','MB']),(0,1,['MS2','MB']),(1,1,['MB','MS2'])],1):
        p=copy.deepcopy(roles[k]);p.update(gurobi_seed=seed,panel_kind='core' if j<=3 else 'support_seed1')
        groups.append(dict(number=j,name=f'campaign/{j:02d}_{p["id"]}_S{seed}',role=p,seed=seed,methods=methods,
            pairs=[['MB',b] for b in ['P','MD-R','MS2']]+[['MD-R','P'],['MS2','P']] if j<=3 else [['MB','MS2']]))
    assert sum(g['role']['cap_seconds']*len(g['methods']) for g in groups)==15600
    write(OUT/'experiment_manifest.json',dict(round=128,version='inclusive-root control v1',base=BASE,groups=groups,
        formal_arms=16,typed_pairs=17,distinct_inputs=3,seed_H=20260626,Threads=1,MIP_threads=1,affinity_mask=4,
        shutdown_reserve=30,native_offset=6,hard_stop_offset=2,MIPGap=0,MIPGapAbs=0,FeasibilityTol=1e-6,IntFeasTol=1e-5,OptimalityTol=1e-6,
        formal_nominal_seconds=15600,qualification_soft_seconds=1200,qualification_limit=3000,management_reference=600,
        maximum_plan=19200,total_outer_limit=TOTAL_LIMIT,sole_paper_method='frozen M-B / GI-TBC',
        P='original cold compact, no H/Start/cutoff',MD_R='own full H, inclusive static own-U0 root, one LP and one MIP',
        no_cross_arm_information=True,no_new_inputs_or_tuning=True,no_outcome_driven_retries=True,
        R127_not_relabelled_complete=True,comparison='unrounded T_cert; one-sided certification; both-open UNDETERMINED; invalid UNEVALUABLE'))
    write(OUT/'input_manifest.json',dict(roles=roles,all_known_research_roles=True,no_input_generation=True))
    # Reuse the complete inherited campaign and verification, changing only
    # identity/output routing and the explicit new diagnostic argument.
    text=(ROOT/'scripts/round127_campaign.py').read_text()
    text=text[:text.index('def smoke_prepare():')]
    text=text.replace('from round127_common import *','from round128_common import *').replace('E1','E2').replace('Round127ExportE0.exe','Round128ExportE2.exe')
    text=text.replace("cmd += ['--round127-mode','p' if arm=='P-GRB' else method.lower()]",
        "cmd += ['--round128-mode','md-r'] if method=='MD-R' else ['--round127-mode','p' if arm=='P-GRB' else method.lower()]")
    text=text.replace('Round127 v3 active.','Round128 active.').replace('from round127_evidence import verify,extension','from round128_evidence import verify,extension')
    text+='\nif __name__=="__main__":execute(sys.argv[1])\n'
    (ROOT/'scripts/round128_campaign.py').write_text(text,encoding='utf-8')
    text=(ROOT/'scripts/round127_build.py').read_text().replace('round127_common','round128_common').replace('E1','E2')
    (ROOT/'scripts/round128_build.py').write_text(text,encoding='utf-8')
    (OUT/'.gitignore').write_text('/fees/\n/campaign/\n/qualification/\n/recovery/\n/*.log\n',encoding='utf-8')
    (OUT/'RESUME.md').write_text('Round128 initialized. No formal arm started. Verify PID creation, seal and remaining budget before resuming.\n',encoding='utf-8')
    print(json.dumps(dict(initialized=True,groups=5,formal_arms=16,typed_pairs=17,budget=budget())))

def exporter():
    from round128_build import FLAGS,CHANGED
    exe=BUILD/'Round128ExportE2.exe'
    attempt=len(list((OUT/'fees').glob('build_exporter*')))+1
    assert metered(f'build_exporter_{attempt:02d}','build',[COMPILER,*FLAGS,ROOT/'scripts/round128_export.cpp',*[BUILD/(s+'.o') for s in CHANGED],ARCHIVE,'-o',exe])==0
    write(OUT/'exporter_identity.json',dict(E1=dict(path=str(WORK/'build-cache/round127/Round127ExportE1.exe'),SHA=sha(WORK/'build-cache/round127/Round127ExportE1.exe')),
        E2=dict(path=str(exe),SHA=sha(exe)),Optimize=0))

if __name__=='__main__':{'initialize':initialize,'exporter':exporter}[sys.argv[1]]()
