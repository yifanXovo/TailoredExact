"""Finite setup from exact R122 authorities; reuse no solving state or routes."""
from round123_common import *
import copy
OLD=WORK/'worktrees/round122'

def prepare():
    workspace(); assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()==BASE
    prior=read(OLD/'results/unified_exact_round122/production_identity.json')
    assert sha(PE)==prior['production_PE_SHA']==PE_SHA and sha(DLL)==prior['DLL_SHA']==DLL_SHA
    assert bindings()==prior['source_bindings'] and len(bindings())==216
    write(OUT/'production_identity.json',dict(prior,round=123,actual_base=BASE,
        production_PE_path=str(PE),source_commit_before_native=SOURCE,original_PE_reused_in_place=True,verified_UTC=utc()))
    dirty=subprocess.check_output(['git','status','--short','-uno'],cwd=MAIN).decode().splitlines()
    write(OUT/'initialization_receipt.json',dict(main_HEAD=subprocess.check_output(['git','rev-parse','HEAD'],cwd=MAIN).decode().strip(),
        main_tracked_status=dirty,main_dirty_SHA={s[3:]:sha(MAIN/s[3:]) for s in dirty},workspace=workspace(),
        applicable_AGENTS_found=[],same_round_preexisting=False,PR184=dict(state='OPEN',Draft=True,head=BASE),
        no_solver_active_at_initial_inventory=True,UTC=utc(),
        fetch_note='Initial git fetch invoked automatic maintenance/prune; no manual gc/prune requested. Subsequent task Git uses gc.auto=0/maintenance.auto=false.'))
    shutil.copyfile(Path('C:/Users/Administrator/.codex/attachments/77e90f7b-9b78-42e5-8fb2-d0ebfbec1a06/已粘贴的文本.txt'),OUT/'goal.md')
    oldout=OLD/'results/unified_exact_round122'
    formal_old=read(oldout/'campaign/group05/identity.json')
    qual_old=read(oldout/'qualification/h100_seed1/identity.json')
    write(OUT/'inherited_helper_names.json',sorted(formal_old['helpers']))
    settings=copy.deepcopy(formal_old['prereg']); settings['common']['gurobi_seed']=0
    settings['candidate_binary']=str(PE); settings['candidate_binary_sha256']=PE_SHA
    plans=[]
    for name,authority,cap,kind in [('campaign/group01',formal_old,18000,'known_instance_predeclared_long_window'),
            ('qualification/h100_seed0',qual_old,120,'qualification')]:
        launches=[]; refs={}
        for n,arm in enumerate(METHODS,1):
            oldlaunch=next(l for l in authority['launches'] if l['arm']==arm)
            p=copy.deepcopy(oldlaunch['panel']); p.update(gurobi_seed=0,cap_seconds=cap,method_order=METHODS,panel_kind=kind)
            if sha(ROOT/p['input_path'])!=p['input_sha256']:
                blob=subprocess.check_output(['git','show',BASE+':'+p['input_path']],cwd=ROOT)
                assert hashlib.sha256(blob).hexdigest()==p['input_sha256']
                (ROOT/p['input_path']).write_bytes(blob)
                write(OUT/'engineering/input_byte_normalization.json',dict(input=p['input_path'],
                    reason='Git checkout CRLF conversion; restore exact pinned Git input blob',SHA=p['input_sha256'],native_starts=0))
            d=OUT/name/'raw'/f'{n:02d}_{p["id"]}_S0_{arm}'
            olddest=oldlaunch['destination']; cmd=[v.replace(olddest,str(d)) for v in oldlaunch['command']]
            cmd[0]=str(PE)
            for key,val in [('--gurobi-seed','0'),('--time-limit',str(cap-6)),('--process-wall-time-limit',str(cap))]: cmd[cmd.index(key)+1]=val
            # Input is a repository-relative authority; no old model/solution/proof is loaded.
            assert not any(v.startswith(('--round112','--round119','--round120','--round100-continuous')) for v in cmd)
            assert ('--round98-state-service' in cmd)==(arm=='M-B')
            assert '18000' not in cmd or cap==18000
            launches.append(dict(number=n,group_number=1 if kind!='qualification' else 0,id=p['id'],arm=arm,seed=0,
                panel=p,panel_kind=kind,destination=str(d),cap_seconds=cap,hard_stop_seconds=cap-2,command=cmd))
            refs[p['id']]=p['reference']
        camp=OUT/name; camp.mkdir(parents=True,exist_ok=True)
        for role,ref in refs.items():
            oldref=Path(authority['launches'][0]['destination']).parents[1]/'reference'/role
            target=camp/'reference'/role; target.mkdir(parents=True,exist_ok=False)
            for fn in ['build.json','original.lp']: shutil.copyfile(oldref/fn,target/fn)
            assert sha(target/'original.lp')==ref['canonical_sha256'] and read(target/'build.json')['optimizer_calls']==0
        plans.append(dict(name=name,launches=launches,references=refs))
    formal=plans[0]['launches']; p=formal[0]['panel']
    assert p['id']=='PB-C50-S' and p['V']==50 and p['M']==4 and p['T_seconds']==10800 and p['lambda']==.15
    assert p['input_sha256']=='3e17bd07ae0abbfebfd8264540e6f5bd737a0d4506c4b6e96950936153db9992'
    write(OUT/'input_manifest.json',dict(roles=[p],qualification_roles=[plans[1]['launches'][0]['panel']],
        prior_known_role=True,new_independent_problems=0,source_ref=BASE))
    write(OUT/'argv_freeze.json',dict(plans=plans,groups=[dict(number=1,id=p['id'],source='CITI',V=50,seed=0,
        campaign=plans[0]['name'],methods=METHODS,cap_seconds=18000,nominal_seconds=54000,management_reserve=360)],UTC=utc()))
    write(OUT/'protocol.json',dict(round=123,base=BASE,production_source=SOURCE,common=settings['common'],
        formal_methods=METHODS,pairs=PAIRS,formal_arms=3,formal_nominal_seconds=54000,total_outer_limit=TOTAL_LIMIT,
        qualification_plan=QUAL_PLAN,qualification_authorized_limit=QUAL_LIMIT,management_reference=360,
        physical_T_seconds=10800,produce_cap_seconds=18000,native_shutdown_reserve=30,evidence_tolerance=1e-7,
        checkpoints=[3600,7200,10800,14400,18000],checkpoints_offline_existing_observations_only=True,
        final_fleet_defines_main_U=True,historical_minimum_F_is_descriptive=True,
        H_seed=20260626,H='full24+1 original closure',cold_independent_methods=True,
        no_R122_route_bound_tree_basis_cutoff_cache_loaded=True,new_input_or_Seed_or_variant=False,
        default_ENS_changed=False,D1_selection_closed=True,no_extra_time_or_group=True))
    (OUT/'measurement_policy_v2.md').write_text((ROOT/'results/unified_exact_round120/measurement_policy_v2.md').read_text(encoding='utf-8').split('R120:')[0]+
        '\nR123: one known PB-C50-S role, three independent Seed0 methods, each produce cap18000 including seal. T10800 is physical. T_verify is actual required post-seal verification including waiting/recovery. Group checks are separate. Final fleet U is main; historical min F is descriptive. Total outer70000; qualification plan2000/limit4000; no start count gate.\n',encoding='utf-8')
    freeze(plans,settings)
    print(json.dumps(dict(prepared=True,source_files=216,helpers=len(helpers()),workspace=workspace())))

def freeze(plans=None,settings=None):
    assert not list((OUT/'campaign').glob('*/raw/*/launch.json'))
    assert not list((OUT/'qualification').glob('*/raw/*/launch.json'))
    plans=plans or read(OUT/'argv_freeze.json')['plans']
    settings=settings or read(OUT/'campaign/group01/identity.json')['prereg']
    hs=helpers()
    for plan in plans:
        write(OUT/plan['name']/'identity.json',dict(prereg=settings,prereg_sha256=sha(OUT/'protocol.json'),
            runner_sha256=sha(ROOT/'scripts/round123_runner.py'),helpers=hs,source_hashes=bindings(),
            candidate_binary_sha256=PE_SHA,dll_sha256=DLL_SHA,measured_source_commit=SOURCE,
            delivery_base_commit=BASE,references=plan['references'],launches=plan['launches'],
            measurement_policy_SHA=sha(OUT/'measurement_policy_v2.md')))
    write(OUT/'candidate_identity.json',dict(production_identity_SHA=sha(OUT/'production_identity.json'),
        production_PE_SHA=PE_SHA,DLL_SHA=DLL_SHA,source_bindings=bindings(),helpers=hs,
        input_manifest_SHA=sha(OUT/'input_manifest.json'),argv_freeze_SHA=sha(OUT/'argv_freeze.json'),
        protocol_SHA=sha(OUT/'protocol.json'),campaign_identities={p['name']:sha(OUT/p['name']/'identity.json') for p in plans}))

if __name__=='__main__': {'prepare':prepare,'freeze':freeze}[sys.argv[1]]()

