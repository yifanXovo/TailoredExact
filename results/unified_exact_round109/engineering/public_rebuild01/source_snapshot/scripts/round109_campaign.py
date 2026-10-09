"""One billed wrapper per frozen group; exactly one original production child per arm."""
import time
_entry_tick=time.perf_counter()
from round109_common import *
from round109_prepare import COMMON
import round109_seed_audit as seed_audit
import round100_campaign as inherited
import round90_lp_g_g3 as supervisor
from round100_idle import ensure_idle
import shutil, traceback, ctypes

def wrapper_start_tick():
    class FileTime(ctypes.Structure):_fields_=[('low',ctypes.c_uint32),('high',ctypes.c_uint32)]
    creation,exit_time,kernel,user=FileTime(),FileTime(),FileTime(),FileTime()
    api=ctypes.WinDLL('kernel32',use_last_error=True)
    api.GetCurrentProcess.restype=ctypes.c_void_p
    assert api.GetProcessTimes(ctypes.c_void_p(api.GetCurrentProcess()),ctypes.byref(creation),ctypes.byref(exit_time),ctypes.byref(kernel),ctypes.byref(user))
    unix=((creation.high<<32)+creation.low)/10000000-11644473600
    return time.perf_counter()-(time.time()-unix),unix

def helpers():
    names=['round109_common.py','round109_prepare.py','round109_data.py','round109_campaign.py','round109_seed_audit.py','round109_seed_scope.py','round109_seed_recovery.py',
        'round108_reader.py','round108_scopes.py','round108_decisions.py','round107_reader.py','round99_pure_start_audit.py',
        'round100_campaign.py','round100_common.py','round100_idle.py','round90_lp_g_g3.py','round88_a1_g3.py',
        'round94_lpg_formal_recovery_v3.py','round94_lpg_contemporary.py','round86_native_evidence.py','analyze_round61.py',
        'round70_affinity.py','round83_audit_v2.py','round75_startup.py','round96_external.py','round96_prepare.py',
        'generate_citibike443_regional_v1.py','round109_reference_batch.cpp']
    return {'scripts/'+n:sha(ROOT/'scripts'/n) for n in names}

def known_role():
    p=copy_role=read(ROOT/'results/unified_exact_round100/holdout_protocol01.json')['roles'][0].copy()
    p.update(cap_seconds=120,method_order=['P-GRB','ENS-C','M-B'],gurobi_seed=0,panel_kind='qualification')
    assert p['id']=='H100' and p['V']==20 and p['M']==2 and p['Q_vector']==[13,21]
    return p

def prepare_batch():
    ensure_idle();check_identity();q=OUT/'qualification';q.mkdir(exist_ok=False)
    roles=read(OUT/'input_manifest.json')['roles']+[known_role()]
    lines=[]
    for p in roles:
        d=q/'reference'/p['id'];d.mkdir(parents=True)
        lines.append('\t'.join(map(str,[p['input_path'],p['T_seconds'],p['pickup_seconds'],p['drop_seconds'],p['lambda'],d])))
    with (q/'reference_batch.tsv').open('x',encoding='utf-8',newline='\n') as f:f.write('\n'.join(lines)+'\n')
    plan=dict(wrappers=2,native_children=6,conservative_starts=8,outer_cap_seconds=1200,CLI_children=5,
        CLI_each_cap_seconds=120,CLI_specs=[dict(id='H100',seed=s,arm=a) for s,aa in [(0,['P-GRB','ENS-C','M-B']),(1,['P-GRB','M-B'])] for a in aa],
        reference_child_count=1,reference_export_roles=[p['id'] for p in roles],batch_input_SHA=sha(q/'reference_batch.tsv'),
        batch_source_SHA=sha(ROOT/'scripts/round109_reference_batch.cpp'),batch_PE_SHA=sha(BUILD/'Round109ReferenceBatch.exe'),
        reference_writer_source_SHA=sha(ROOT/'src/round65_reference_build.cpp'),zero_reference_Optimize_presolve_solution_Start=True,
        no_new_input_performance_pilot=True,formal_remaining_reserve=dict(starts=57,nominal_seconds=88200,group_overhead_seconds=1800))
    write(q/'plan.json',plan)
    print('qualification batch/5 CLI plan frozen; Optimize=0')

def build_launches(camp,groups,protocol_path):
    prereg=dict(common=COMMON,candidate_binary=(BUILD/'ExactEBRP.exe').relative_to(ROOT).as_posix(),candidate_binary_sha256=PE_SHA)
    references={};launches=[]
    for group_no,p in enumerate(groups,1):
        p=p.copy();assert sha(ROOT/p['input_path'])==p['input_sha256']
        ref_source=OUT/'qualification/reference'/p['id'];ref=read(ref_source/'build.json')
        assert ref['optimizer_calls']==0 and ref['canonical_sha256']==sha(ref_source/'original.lp')
        target=camp/'reference'/p['id']
        if not target.exists():
            target.mkdir(parents=True)
            for filename in ['original.lp','build.json']:shutil.copyfile(ref_source/filename,target/filename)
            write(target/'copy_provenance.json',dict(source=ref_source.relative_to(ROOT).as_posix(),source_SHA=sha(ref_source/'original.lp'),native_processes=0))
        p.update(reference=ref,instance_path=p['input_path']);references[p['id']]=ref
        for arm in p['method_order']:
            number=len(launches)+1;dest=camp/'raw'/f'{number:02d}_{p["id"]}_S{p["gurobi_seed"]}_{arm}'
            cmd=(supervisor.audited_runner_utilities.command_for(prereg,p,arm,dest) if arm=='P-GRB' else supervisor.command_for(prereg,p,'ENS-C',dest))
            cmd[cmd.index('--gurobi-seed')+1]=str(p['gurobi_seed'])
            if arm=='M-B':cmd+=['--round98-state-service','m-binary']
            launches.append(dict(number=number,group_number=p.get('number',group_no),id=p['id'],arm=arm,seed=p['gurobi_seed'],
                panel=p,panel_kind=p['panel_kind'],destination=str(dest),stage=p['panel_kind'],cap_seconds=p['cap_seconds'],
                hard_stop_seconds=p['cap_seconds']-2,command=cmd))
    value=dict(prereg=prereg,prereg_sha256=sha(protocol_path),protocol_path=str(protocol_path),runner_sha256=sha(__file__),
        source_hashes=bindings(),helpers=helpers(),candidate_binary_sha256=PE_SHA,dll_sha256=DLL_SHA,
        measured_source_commit='b5db3f038f64215766a54498d8acc82e384de733',delivery_base_commit=BASE,
        references=references,launches=launches,prepared_unix=time.time(),Optimize_calls=0)
    write(camp/'identity.json',value);return value

def freeze_launches():
    check_identity();q=OUT/'qualification';assert read(q/'batch_export_receipt.json')['passed']
    cli=q/'cli01';cli.mkdir()
    h=known_role();second=dict(h,gurobi_seed=1,method_order=['P-GRB','M-B'])
    build_launches(cli,[h,second],q/'plan.json')
    main=read(OUT/'input_manifest.json')['roles'];byid={p['id']:p for p in main}
    groups=main+[dict(byid[s['id']],**s,panel_kind='seed') for s in read(OUT/'protocol.json')['seed_checks']]
    camp=OUT/'campaign';camp.mkdir();identity=build_launches(camp,groups,OUT/'protocol.json')
    assert len(identity['launches'])==42 and sum(x['cap_seconds'] for x in identity['launches'])==88200
    write(OUT/'candidate_identity.json',dict(production_PE_SHA=PE_SHA,DLL_SHA=DLL_SHA,source_bindings=bindings(),helpers=helpers(),
        original_candidate_contract_SHA=sha(OUT/'candidate_contract_freeze.json'),recipe_SHA=sha(OUT/'generation_recipe.json'),
        input_manifest_SHA=sha(OUT/'input_manifest.json'),protocol_SHA=sha(OUT/'protocol.json'),
        campaign_identity_SHA=sha(camp/'identity.json'),full_argv=[x['command'] for x in identity['launches']],
        qualification_argv=[x['command'] for x in read(cli/'identity.json')['launches']],
        full_time_contract='arm admission through native/startup/writes/physical-scope audit and wrapper crosscheck',
        measured_production_source_commit='b5db3f038f64215766a54498d8acc82e384de733',delivery_base_commit=BASE,
        default_ENS_changed=False,planned_total_starts=65,starts_reserve=7,nominal_seconds=88200))
    print('all42 actual argv and same candidate identities frozen; Optimize=0')

def records(camp):return [json.loads(line) for line in (camp/'summary.jsonl').read_text().splitlines()] if (camp/'summary.jsonl').exists() else []

def run(name,n,qualification=False):
    ensure_idle();check_identity();camp=OUT/name;q=read(camp/'identity.json')
    assert q['source_hashes']==bindings() and q['helpers']==helpers() and q['runner_sha256']==sha(__file__)
    assert q['prereg_sha256']==sha(q['protocol_path'])
    previous=records(camp);assert len(previous)==n-1 and all(r['audit_passed'] for r in previous),'only next never-started arm'
    launch=q['launches'][n-1];assert not Path(launch['destination']).exists()
    assert sha(ROOT/launch['panel']['input_path'])==launch['panel']['input_sha256']
    if not qualification:
        gate=read(OUT/'review/performance_admission.json');assert gate['decision']=='ACCEPT'
        assert gate['production_PE_SHA']==PE_SHA and gate['DLL_SHA']==DLL_SHA
        assert gate['candidate_identity_SHA']==sha(OUT/'candidate_identity.json')
        assert gate['campaign_identity_SHA']==sha(camp/'identity.json')
        assert gate['qualification_identity_SHA']==sha(OUT/'qualification/identity.json')
    supervisor.CAMPAIGN=camp;supervisor.audit_launch=seed_audit.adapter
    rec=supervisor.run_one(launch,q['prereg'],q)
    same=[r for r in previous+[rec] if r['id']==launch['id']]
    lower=[r['endpoint']['L'] for r in same];upper=[r['endpoint']['U'] for r in same if r['endpoint']['U'] is not None]
    assert not upper or max(lower)<=min(upper)+1e-7,'offline contradictory cross-arm physical/native evidence'
    write(camp/f'cross_arm_{launch["id"]}_{len(same)}.json',dict(strongest_L=max(lower),best_physical_U=min(upper) if upper else None,
        passed=True,scope='offline contradiction check only; never combined certificate or injected knowledge'))
    return rec

def full_remaining_reserve():
    q=read(OUT/'campaign/identity.json');done=len(records(OUT/'campaign'));remaining=q['launches'][done:]
    groups=len({x['group_number'] for x in remaining})
    return dict(starts=len(remaining)+groups,nominal_seconds=sum(x['cap_seconds'] for x in remaining),overhead_seconds=120*groups)

def billed(name,first,last,label,qualification=False):
    outer_tick,creation_unix=wrapper_start_tick();ensure_idle();check_identity();camp=OUT/name;q=read(camp/'identity.json');b=budget()
    children=last-first+1;nominal=sum(x['cap_seconds'] for x in q['launches'][first-1:last]);remaining=full_remaining_reserve()
    assert not b['unclosed'] and len(records(camp))==first-1
    if qualification:
        assert b['remaining_starts']>=children+1+remaining['starts']
        assert b['remaining_outer_seconds']>=nominal+120+remaining['nominal_seconds']+remaining['overhead_seconds']
    else:
        assert b['remaining_starts']>=remaining['starts']
        assert b['remaining_outer_seconds']>=remaining['nominal_seconds']+remaining['overhead_seconds']
        assert len({x['group_number'] for x in q['launches'][first-1:last]})==1
    d=OUT/'fees'/label;d.mkdir(parents=True,exist_ok=False)
    write(d/'launch.json',dict(command=[sys.executable,__file__,'billed',name,str(first),str(last),label]+(['--qualification'] if qualification else []),
        cwd=str(ROOT),conservative_process_starts=children+1,declared_native_children=children,actual_wrapper_processes=1,
        cap_seconds=nominal+120,budget_before=b,all_remaining_fixed_reserve=remaining,wrapper_creation_unix=creation_unix,
        qualification=qualification,source_bindings=bindings(),helpers=helpers(),production_PE_SHA=PE_SHA,DLL_SHA=DLL_SHA))
    snapshots=d/'source_snapshot';snapshots.mkdir()
    for helper_name,digest in helpers().items():
        target=snapshots/helper_name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/helper_name).read_bytes())
    write(d/'process.json',dict(pid=os.getpid(),parent_pid=os.getppid()))
    code=0;reason='normal_return'
    try:
        for number in range(first,last+1):
            arm_tick=time.perf_counter();launch=q['launches'][number-1]
            write(d/f'{number:02d}_before.json',dict(number=number,id=launch['id'],arm=launch['arm'],seed=launch['seed']))
            rec=run(name,number,qualification)
            write(d/f'{number:02d}_after.json',dict(completed_and_audited=True))
            dest=Path(launch['destination']);seconds=time.perf_counter()-arm_tick
            write(dest/'whole_arm_receipt.json',dict(number=number,id=rec['id'],arm=rec['arm'],seed=launch['seed'],complete_seconds=seconds,
                completion_SHA=sha(dest/'completion.json'),audit_SHA=sha(dest/'audit.json'),
                original_supervisor_observed_seconds=rec['completion']['fully_observed_end_to_end_seconds'],
                includes_admission_identity_checks_startup_native_calls_callbacks_raw_writes_postexit_audit_crosscheck=True))
            assert seconds<=launch['cap_seconds'],'full arm exceeded frozen cap'
    except BaseException:
        code=1;reason='actual_exception';(d/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:
        value=dict(exit_code=code,outer_seconds=time.perf_counter()-outer_tick,stop_reason=reason,conservative_process_starts=children+1,
            timing_basis='actual wrapper process creation through native/postexit audit/closure; nested seconds not added',
            actual_native_children_with_launch=sum((Path(x['destination'])/'launch.json').exists() for x in q['launches'][first-1:last]))
        write(d/'receipt.json',value);print(json.dumps(value),flush=True)
    if qualification:
        all_records=records(camp);assert len(all_records)==5
        import csv
        integer=[];LPs=[];starts=[]
        for record in all_records:
            dest=Path(record['destination']);observations=read(dest/'observations.json')
            assert all(r['payload']['settings']==seed_audit.expected(q['launches'][record['number']-1]['seed']) for r in observations if r['payload']['kind']=='call')
            if record['arm']!='P-GRB':
                ledger=dest/'external/paper_optimize_ledger.csv'
                with ledger.open(newline='') as f:rows=list(csv.DictReader(f))
                integer.append(any(x['solve_kind']!='LP' for x in rows));LPs.append(any(x['solve_kind']=='LP' for x in rows))
                starts.extend(str(p.relative_to(ROOT)) for p in (dest/'external/native_logs').glob('*.round68.start.json') if read(p).get('submitted'))
        assert all(integer) and all(LPs) and starts,'actual original LP/MIP/Start must be reached'
        assert any(r['endpoint']['certificate'] for r in all_records),'legal full termination required'
        write(OUT/'qualification/identity.json',dict(passed=True,production_PE_SHA=PE_SHA,DLL_SHA=DLL_SHA,source_bindings=bindings(),
            current_CLI_records=all_records,qualified_argv=[x['command'] for x in q['launches']],
            actual_seeds=[x['seed'] for x in q['launches']],LP_reached=LPs,MIP_reached=integer,submitted_Starts=starts,
            legal_terminations=len(all_records),batch_export_receipt_SHA=sha(OUT/'qualification/batch_export_receipt.json'),
            qualification_campaign_identity_SHA=sha(camp/'identity.json'),not_performance=True))

def batch_export():
    outer_tick,creation_unix=wrapper_start_tick();ensure_idle();check_identity();q=OUT/'qualification';b=budget();plan=read(q/'plan.json')
    assert not b['unclosed'] and b['remaining_starts']>=65 and b['remaining_outer_seconds']>=88200+1800+1200
    d=OUT/'fees/qualification_prepare01';d.mkdir(parents=True,exist_ok=False)
    command=[str(BUILD/'Round109ReferenceBatch.exe'),str(q/'reference_batch.tsv')]
    write(d/'launch.json',dict(command=command,cwd=str(ROOT),conservative_process_starts=2,declared_native_children=1,
        actual_wrapper_processes=1,zero_Optimize=True,budget_before=b,qualification_plan_SHA=sha(q/'plan.json'),
        exporter_PE_SHA=sha(BUILD/'Round109ReferenceBatch.exe'),exporter_source_SHA=sha(ROOT/'scripts/round109_reference_batch.cpp'),
        wrapper_creation_unix=creation_unix))
    write(d/'process.json',dict(pid=os.getpid(),parent_pid=os.getppid()));code=None
    try:
        with (d/'stdout.log').open('xb') as so,(d/'stderr.log').open('xb') as se:
            child=subprocess.Popen(command,cwd=ROOT,env=env(),stdout=so,stderr=se)
            write(d/'child_process.json',dict(pid=child.pid,parent_pid=os.getpid()))
            code=child.wait(timeout=300)
        assert code==0
        builds={p.parent.name:read(p) for p in (q/'reference').glob('*/build.json')}
        assert len(builds)==13 and all(v['optimizer_calls']==0 for v in builds.values())
        for id,value in builds.items():assert value['canonical_sha256']==sha(q/'reference'/id/'original.lp')
        assert 'batch_complete\t13\tOptimize=0' in (d/'stdout.log').read_text()
        write(q/'batch_export_receipt.json',dict(passed=True,actual_native_processes=1,Optimize=0,presolve=0,solution_or_Start_generated=False,
            reference_writer_source_SHA=sha(ROOT/'src/round65_reference_build.cpp'),batch_PE_SHA=sha(BUILD/'Round109ReferenceBatch.exe'),
            plan_SHA=sha(q/'plan.json'),reference_models=builds,stdout_SHA=sha(d/'stdout.log')))
    finally:write(d/'receipt.json',dict(exit_code=code,outer_seconds=time.perf_counter()-outer_tick,conservative_process_starts=2,stop_reason='normal_return' if code==0 else 'failure'))
    print('13 exact original cold matrices from one batch child; zero Optimize',flush=True)

if __name__=='__main__':
    action=sys.argv[1]
    if action=='prepare-batch':prepare_batch()
    elif action=='batch-export':batch_export()
    elif action=='freeze-launches':freeze_launches()
    elif action=='billed':billed(sys.argv[2],int(sys.argv[3]),int(sys.argv[4]),sys.argv[5],'--qualification' in sys.argv[6:])
    else:raise ValueError(action)
