"""One directly billed wrapper per fixed group, one final PE per native arm."""
import time
_entry_tick=time.perf_counter()
from round110_common import *
from round109_prepare import COMMON
import round109_campaign as inherited_campaign
import round109_seed_audit as seed_audit
import round90_lp_g_g3 as supervisor
from round100_idle import ensure_idle
import csv, inspect, shutil, traceback

def helpers():
    names=set(inherited_campaign.helpers())
    names.update(['scripts/round110_campaign.py','scripts/round110_common.py'])
    return {p:sha(ROOT/p) for p in sorted(names)}

def build_launches(camp,groups,protocol_path):
    production=check_identity();PE_SHA=production['production_PE_SHA']
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
            write(target/'copy_provenance.json',dict(source=ref_source.relative_to(ROOT).as_posix(),source_SHA=sha(ref_source/'original.lp'),native_processes=0,
                original_round109_reference_exact_reuse=True,writer_source_SHA=sha(ROOT/'src/round65_reference_build.cpp')))
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
        measured_source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),delivery_base_commit=BASE,
        references=references,launches=launches,prepared_unix=time.time(),Optimize_calls=0)
    write(camp/'identity.json',value);return value

def freeze_launches():
    production=check_identity();q=OUT/'qualification'
    assert read(q/'parser_equivalence_receipt.json')['passed'] and read(q/'main_entry_receipt.json')['passed']
    cli=q/'cli01';cli.mkdir()
    h=inherited_campaign.known_role();second=dict(h,gurobi_seed=1,method_order=['P-GRB','M-B'])
    build_launches(cli,[h,second],q/'plan.json')
    main=read(OUT/'input_manifest.json')['roles'];byid={p['id']:p for p in main}
    groups=main+[dict(byid[s['id']],**s,panel_kind='seed') for s in read(OUT/'protocol.json')['seed_checks']]
    camp=OUT/'campaign';camp.mkdir();identity=build_launches(camp,groups,OUT/'protocol.json')
    assert len(identity['launches'])==42 and sum(x['cap_seconds'] for x in identity['launches'])==88200
    old=read(ROOT/'results/unified_exact_round109/campaign/identity.json')
    for a,b in zip(old['launches'],identity['launches']):
        assert (a['number'],a['id'],a['arm'],a['seed'],a['cap_seconds'])==(b['number'],b['id'],b['arm'],b['seed'],b['cap_seconds'])
        def normalized(command):
            return [('<FINAL_PE>' if i==0 else arg.replace('E:\\codes\\ExactEBRP-round109','<ROOT>').replace(str(ROOT),'<ROOT>').replace('unified_exact_round109','<ROUND>').replace('unified_exact_round110','<ROUND>').replace(OLD_PE_SHA,'<PE_SHA>').replace(production['production_PE_SHA'],'<PE_SHA>')) for i,arg in enumerate(command)]
        assert normalized(a['command'])==normalized(b['command']),('argv drift',a['number'])
    write(OUT/'candidate_contract_freeze.json',dict(original_round109_contract_SHA=sha(ROOT/'results/unified_exact_round109/candidate_contract_freeze.json'),
        candidate='original R100 M-B',base=BASE,production_identity_SHA=sha(OUT/'production_identity.json'),source_bindings=bindings(),
        no_math_search_change=True,no_new_mechanism=True,original_42_numerical_argv_equal=True,
        input_preset='research-round83-vds-equal-net-exchange',appended_argv=['--round98-state-service','m-binary'],
        effective_identity='research-round99-ensc-discrete-structure-m-binary',round100_continuous_quantities=False,default_ENS_changed=False))
    write(OUT/'candidate_identity.json',dict(production_PE_SHA=production['production_PE_SHA'],DLL_SHA=DLL_SHA,source_bindings=bindings(),helpers=helpers(),
        original_candidate_contract_SHA=sha(OUT/'candidate_contract_freeze.json'),recipe_SHA=sha(OUT/'generation_recipe.json'),
        input_manifest_SHA=sha(OUT/'input_manifest.json'),protocol_SHA=sha(OUT/'protocol.json'),campaign_identity_SHA=sha(camp/'identity.json'),
        full_argv=[x['command'] for x in identity['launches']],qualification_argv=[x['command'] for x in read(cli/'identity.json')['launches']],
        full_time_contract='arm admission through native/startup/writes/physical-scope audit and wrapper crosscheck',
        measured_production_source_commit=identity['measured_source_commit'],delivery_base_commit=BASE,default_ENS_changed=False,
        planned_total_starts=73,starts_reserve=23,nominal_seconds=88200))
    print('all42 original numerical argv and new campaign identity frozen; no native process')

def records(camp):
    return [json.loads(line) for line in (camp/'summary.jsonl').read_text().splitlines()] if (camp/'summary.jsonl').exists() else []

def supervised_run(launch,identity,arm_tick):
    # The inherited function is retained exactly except two durable clock writes.
    # It still launches one PE, observes the same journal and calls the same audit.
    source=inspect.getsource(supervisor.run_one)
    marker='    write_new(destination / "observations.json", observations)\n'
    assert source.count(marker)==1
    source=source.replace(marker,marker+'    write_new(destination / "native_end_receipt.json", dict(complete_seconds_until_native_end=time.perf_counter()-_arm_tick, completion_SHA=sha(destination / "completion.json"), observations_SHA=sha(destination / "observations.json"), ended_unix=time.time()))\n')
    marker='    write_new(destination / "audit.json", audited)\n'
    assert source.count(marker)==1
    source=source.replace(marker,marker+'    write_new(destination / "postexit_audit_receipt.json", dict(complete_seconds_until_audit_end=time.perf_counter()-_arm_tick, audit_SHA=sha(destination / "audit.json"), audit_passed=audited["passed"], ended_unix=time.time()))\n')
    namespace=dict(vars(supervisor));namespace.update(CAMPAIGN=Path(launch['destination']).parents[1],audit_launch=seed_audit.adapter,_arm_tick=arm_tick)
    exec(compile(source,__file__+'::inherited_supervisor','exec'),namespace)
    return namespace['run_one'](launch,identity['prereg'],identity)

def full_remaining_reserve():
    q=read(OUT/'campaign/identity.json');done=len(records(OUT/'campaign'));remaining=q['launches'][done:]
    groups=len({x['group_number'] for x in remaining})
    return dict(starts=len(remaining)+groups,nominal_seconds=sum(x['cap_seconds'] for x in remaining),overhead_seconds=120*groups)

def billed(name,first,last,label,qualification=False):
    tick,creation=process_origin();ensure_idle();production=check_identity();camp=OUT/name;identity=read(camp/'identity.json');b=budget()
    assert identity['source_hashes']==bindings() and identity['helpers']==helpers() and identity['runner_sha256']==sha(__file__)
    assert identity['prereg_sha256']==sha(identity['protocol_path']) and not b['unclosed']
    previous=records(camp);assert len(previous)==first-1 and all(r['audit_passed'] for r in previous)
    children=last-first+1;nominal=sum(x['cap_seconds'] for x in identity['launches'][first-1:last]);remaining=full_remaining_reserve()
    assert b['remaining_starts']>=(children+1+remaining['starts'] if qualification else remaining['starts'])
    assert b['remaining_outer_seconds']>=remaining['nominal_seconds']+remaining['overhead_seconds']+(nominal+120 if qualification else 0)
    if qualification:assert b['qualification_starts']+children+1<=20 and b['qualification_seconds']+nominal+120<=2000
    else:
        gate=read(OUT/'review/performance_admission.json');assert gate['decision']=='ACCEPT'
        assert gate['production_PE_SHA']==production['production_PE_SHA'] and gate['DLL_SHA']==DLL_SHA
        assert gate['candidate_identity_SHA']==sha(OUT/'candidate_identity.json') and gate['campaign_identity_SHA']==sha(camp/'identity.json')
        assert gate['qualification_identity_SHA']==sha(OUT/'qualification/identity.json')
        assert len({x['group_number'] for x in identity['launches'][first-1:last]})==1
    d=OUT/'fees'/label;d.mkdir(parents=True,exist_ok=False)
    write(d/'launch.json',dict(command=[sys.executable,__file__,'billed',name,str(first),str(last),label]+(['--qualification'] if qualification else []),
        cwd=str(ROOT),conservative_process_starts=children+1,declared_native_children=children,actual_wrapper_processes=1,
        cap_seconds=nominal+120,budget_before=b,all_remaining_fixed_reserve=remaining,wrapper_creation_unix=creation,
        qualification=qualification,source_bindings=bindings(),helpers=helpers(),production_PE_SHA=production['production_PE_SHA'],DLL_SHA=DLL_SHA))
    for path in helpers():
        target=d/'source_snapshot'/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/path).read_bytes())
    write(d/'process.json',dict(pid=os.getpid(),parent_pid=os.getppid()));code=0
    try:
        for number in range(first,last+1):
            arm_tick=time.perf_counter();check_identity();launch=identity['launches'][number-1]
            assert not Path(launch['destination']).exists() and sha(ROOT/launch['panel']['input_path'])==launch['panel']['input_sha256']
            write(d/f'{number:02d}_before.json',dict(number=number,id=launch['id'],arm=launch['arm'],seed=launch['seed'],started_unix=time.time()))
            rec=supervised_run(launch,identity,arm_tick)
            same=[r for r in records(camp) if r['id']==launch['id'] and identity['launches'][r['number']-1]['seed']==launch['seed']]
            lower=[r['endpoint']['L'] for r in same];upper=[r['endpoint']['U'] for r in same if r['endpoint']['U'] is not None]
            assert not upper or max(lower)<=min(upper)+1e-7,'offline contradictory cross-arm physical/native evidence'
            dest=Path(launch['destination']);seconds=time.perf_counter()-arm_tick
            write(dest/'whole_arm_receipt.json',dict(number=number,id=rec['id'],arm=rec['arm'],seed=launch['seed'],complete_seconds=seconds,
                completion_SHA=sha(dest/'completion.json'),audit_SHA=sha(dest/'audit.json'),original_supervisor_observed_seconds=rec['completion']['fully_observed_end_to_end_seconds'],
                includes_admission_identity_checks_startup_native_calls_callbacks_raw_writes_postexit_audit_crosscheck=True))
            write(d/f'{number:02d}_after.json',dict(completed_and_audited=True,whole_arm_receipt_SHA=sha(dest/'whole_arm_receipt.json')))
            assert seconds<=launch['cap_seconds'],'full arm exceeded frozen cap'
    except BaseException:
        code=1;(d/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:
        write(d/'receipt.json',dict(exit_code=code,outer_seconds=time.perf_counter()-tick,stop_reason='normal_return' if code==0 else 'actual_exception',
            conservative_process_starts=children+1,qualification=qualification,
            actual_native_children_with_launch=sum((Path(x['destination'])/'launch.json').exists() for x in identity['launches'][first-1:last]),
            nested_seconds_added=False,earlier_failure_slots_refunded=False))
        print(json.dumps(read(d/'receipt.json')),flush=True)
    if qualification:
        all_records=records(camp);assert len(all_records)==5;LP=[];MIP=[];starts=[]
        for record in all_records:
            dest=Path(record['destination']);observations=read(dest/'observations.json')
            assert all(r['payload']['settings']==seed_audit.expected(identity['launches'][record['number']-1]['seed']) for r in observations if r['payload']['kind']=='call')
            if record['arm']!='P-GRB':
                with (dest/'external/paper_optimize_ledger.csv').open(newline='') as f: rows=list(csv.DictReader(f))
                LP.append(any(x['solve_kind']=='LP' for x in rows));MIP.append(any(x['solve_kind']!='LP' for x in rows))
                starts.extend(str(p.relative_to(ROOT)) for p in (dest/'external/native_logs').glob('*.round68.start.json') if read(p).get('submitted'))
        assert all(LP) and all(MIP) and starts and any(r['endpoint']['certificate'] for r in all_records)
        write(OUT/'qualification/identity.json',dict(passed=True,production_PE_SHA=production['production_PE_SHA'],DLL_SHA=DLL_SHA,source_bindings=bindings(),
            current_CLI_records=all_records,qualified_argv=[x['command'] for x in identity['launches']],actual_seeds=[x['seed'] for x in identity['launches']],
            LP_reached=LP,MIP_reached=MIP,submitted_Starts=starts,legal_terminations=5,not_performance=True,
            parser_equivalence_receipt_SHA=sha(OUT/'qualification/parser_equivalence_receipt.json'),main_entry_receipt_SHA=sha(OUT/'qualification/main_entry_receipt.json'),
            qualification_campaign_identity_SHA=sha(camp/'identity.json')))

if __name__=='__main__':
    if sys.argv[1]=='freeze-launches':freeze_launches()
    elif sys.argv[1]=='billed':billed(sys.argv[2],int(sys.argv[3]),int(sys.argv[4]),sys.argv[5],'--qualification' in sys.argv[6:])
    else:raise ValueError(sys.argv[1])
