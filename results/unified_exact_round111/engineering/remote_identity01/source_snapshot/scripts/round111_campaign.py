"""Fixed six-arm serial wrapper; unchanged native supervision and argv.

First arm clock includes wrapper creation/import/admission. Subsequent arm
clocks start before their own identity work. Cache is arm-local in the adapter.
"""
import time
_entry_tick=time.perf_counter()
from round111_common import *
import copy, csv, inspect, shutil, traceback
import round109_campaign as inherited_campaign
import round111_seed_audit as audit
import round109_seed_audit as inherited_audit
import round90_lp_g_g3 as supervisor
from round100_idle import ensure_idle

def helpers():
    names=set(inherited_campaign.helpers())
    names.update(['scripts/round111_common.py','scripts/round111_campaign.py','scripts/round111_seed_audit.py',
        'scripts/round103_common.py','scripts/round101_common.py','scripts/round110_common.py'])
    return {p:sha(ROOT/p) for p in sorted(names)}

def records(camp):
    p=camp/'summary.jsonl'
    return [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines()] if p.exists() else []

def prepare():
    check_identity()
    for target,source,numbers in [('campaign','campaign',range(37,43)),('qualification/cli01','qualification/cli01',[4,5])]:
        old=read(OLD_ROOT/OLD/source/'identity.json');camp=OUT/target;camp.mkdir(parents=True,exist_ok=False)
        launches=[];references={}
        for newnum,oldnum in enumerate(numbers,1):
            previous=old['launches'][oldnum-1];launch=copy.deepcopy(previous)
            launch.update(number=newnum,old_R110_number=oldnum,group_number=(newnum+1)//2)
            dest=camp/'raw'/f'{newnum:02d}_{launch["id"]}_S1_{launch["arm"]}'
            olddest=previous['destination'];launch['destination']=str(dest)
            launch['command']=[str(PE) if i==0 else arg.replace(olddest,str(dest)) for i,arg in enumerate(previous['command'])]
            assert len(launch['command'])==len(previous['command'])
            for i,(a,b) in enumerate(zip(previous['command'],launch['command'])):
                assert i==0 or a==b or (a.startswith(olddest) and b==a.replace(olddest,str(dest)))
            p=launch['panel'];assert sha(ROOT/p['input_path'])==p['input_sha256'] and launch['seed']==p['gurobi_seed']==1
            if p['id'] not in references:
                ref=camp/'reference'/p['id'];ref.mkdir(parents=True)
                for name in ['original.lp','build.json']:shutil.copyfile(OLD_ROOT/OLD/source/'reference'/p['id']/name,ref/name)
                assert sha(ref/'original.lp')==p['reference']['canonical_sha256'] and read(ref/'build.json')==p['reference']
                references[p['id']]=p['reference']
            launches.append(launch)
        ident=dict(prereg=dict(old['prereg'],candidate_binary=PE.relative_to(ROOT).as_posix()),
            prereg_sha256=sha(OUT/'protocol.json'),protocol_path=str(OUT/'protocol.json'),runner_sha256=sha(__file__),
            helpers=helpers(),source_hashes=bindings(),candidate_binary_sha256=PE_SHA,dll_sha256=DLL_SHA,
            measured_source_commit=read(OUT/'production_identity.json').get('production_repair_commit','382cbcddc00fad4b1ed44fe8e9d9862f77cf5fba'),
            delivery_base_commit=BASE,references=references,launches=launches,prepared_unix=time.time(),Optimize_calls=0)
        write(camp/'identity.json',ident)
    formal=read(OUT/'campaign/identity.json');assert len(formal['launches'])==6 and sum(l['cap_seconds'] for l in formal['launches'])==12600
    write(OUT/'candidate_identity.json',dict(production_PE_SHA=PE_SHA,DLL_SHA=DLL_SHA,source_bindings=bindings(),helpers=helpers(),
        production_identity_SHA=sha(OUT/'production_identity.json'),protocol_SHA=sha(OUT/'protocol.json'),
        input_manifest_SHA=sha(OUT/'input_manifest.json'),campaign_identity_SHA=sha(OUT/'campaign/identity.json'),
        qualification_campaign_identity_SHA=sha(OUT/'qualification/cli01/identity.json'),
        full_argv=[l['command'] for l in formal['launches']],
        qualification_argv=[l['command'] for l in read(OUT/'qualification/cli01/identity.json')['launches']],
        R110_original_argv_paths_only_change=True,formal_fixed_old_numbers=list(range(37,43)),
        evidence_layer='R110_MAIN_36_PLUS_R111_SEED_6',default_ENS_changed=False))
    print('six formal and two qualification argv frozen, no native launch')

def supervised_run(launch,identity,arm_tick):
    source=inspect.getsource(supervisor.run_one)
    marker='    write_new(destination / "observations.json", observations)\n';assert source.count(marker)==1
    source=source.replace(marker,marker+'    write_new(destination / "native_end_receipt.json", dict(complete_seconds_until_native_end=time.perf_counter()-_arm_tick, completion_SHA=sha(destination / "completion.json"), observations_SHA=sha(destination / "observations.json"), ended_unix=time.time()))\n')
    marker='    write_new(destination / "audit.json", audited)\n';assert source.count(marker)==1
    source=source.replace(marker,marker+'    write_new(destination / "postexit_audit_receipt.json", dict(complete_seconds_until_audit_end=time.perf_counter()-_arm_tick, audit_SHA=sha(destination / "audit.json"), audit_passed=audited["passed"], ended_unix=time.time()))\n')
    namespace=dict(vars(supervisor),CAMPAIGN=Path(launch['destination']).parents[1],audit_launch=audit.adapter,_arm_tick=arm_tick)
    exec(compile(source,__file__+'::inherited_supervisor','exec'),namespace)
    return namespace['run_one'](launch,identity['prereg'],identity)

def remaining_reserve():
    camp=OUT/'campaign';ident=read(camp/'identity.json');left=ident['launches'][len(records(camp)):]
    groups=len({x['group_number'] for x in left})
    return dict(starts=len(left)+groups,nominal_seconds=sum(x['cap_seconds'] for x in left),overhead_seconds=120*groups)

def billed(name,first,last,label,qualification=False):
    tick,creation=process_origin();camp=OUT/name;ident=read(camp/'identity.json');before=budget()
    count=last-first+1;nominal=sum(x['cap_seconds'] for x in ident['launches'][first-1:last]);reserve=remaining_reserve()
    d=OUT/'fees'/label;d.mkdir(parents=True,exist_ok=False)
    write(d/'launch.json',dict(command=[str(PYTHON),'-X','utf8',__file__,'billed',name,str(first),str(last),label]+(['--qualification'] if qualification else []),
        cwd=str(ROOT),conservative_process_starts=count+1,declared_native_children=count,actual_wrapper_processes=1,
        qualification=qualification,cap_seconds=nominal+120,budget_before=before,remaining_formal_reserve=reserve,
        wrapper_creation_unix=creation,helpers=helpers(),PE_SHA=PE_SHA,DLL_SHA=DLL_SHA))
    write(d/'process.json',dict(pid=os.getpid(),parent_pid=os.getppid()))
    for path in helpers():
        target=d/'source_snapshot'/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/path).read_bytes())
    code=0
    try:
        assert qualification==(name=='qualification/cli01'),'explicit qualification flag and campaign disagree'
        ensure_idle();check_identity()
        assert not before['unclosed'] and before['remaining_starts']>=reserve['starts']+(count+1 if qualification else 0)
        assert before['remaining_outer_seconds']>=reserve['nominal_seconds']+reserve['overhead_seconds']+(nominal+120 if qualification else 0)
        assert ident['helpers']==helpers() and ident['source_hashes']==bindings() and ident['runner_sha256']==sha(__file__)
        assert ident['prereg_sha256']==sha(OUT/'protocol.json')
        prefix=records(camp);assert len(prefix)==first-1 and all(r['audit_passed'] for r in prefix)
        if qualification:
            assert before['qualification_starts']+count+1<=8 and before['qualification_seconds']+nominal+120<=600
            envelope=read(OUT/'qualification/envelope.json');assert envelope['passed'] and envelope['helper_SHA']==sha(audit.__file__)
        else:
            gate=read(OUT/'review/performance_admission.json');assert gate['decision']=='ACCEPT'
            assert gate['production_PE_SHA']==PE_SHA and gate['DLL_SHA']==DLL_SHA
            assert gate['candidate_identity_SHA']==sha(OUT/'candidate_identity.json') and gate['campaign_identity_SHA']==sha(camp/'identity.json')
            assert gate['qualification_identity_SHA']==sha(OUT/'qualification/identity.json')
        assert len({l['group_number'] for l in ident['launches'][first-1:last]})==1
        for number in range(first,last+1):
            arm_tick=tick if number==first else time.perf_counter()
            check_identity();launch=ident['launches'][number-1]
            assert not Path(launch['destination']).exists() and sha(ROOT/launch['panel']['input_path'])==launch['panel']['input_sha256']
            write(d/f'{number:02d}_before.json',dict(number=number,id=launch['id'],arm=launch['arm'],started_unix=time.time()))
            rec=supervised_run(launch,ident,arm_tick)
            same=[r for r in records(camp) if r['id']==launch['id']]
            lower=[r['endpoint']['L'] for r in same];upper=[r['endpoint']['U'] for r in same if r['endpoint']['U'] is not None]
            assert not upper or max(lower)<=min(upper)+1e-7,'offline contradictory cross-arm evidence'
            dest=Path(launch['destination'])
            write(dest/'audit_execution_metrics.json',audit.last_metrics)
            seconds=time.perf_counter()-arm_tick
            write(dest/'whole_arm_receipt.json',dict(number=number,id=launch['id'],arm=launch['arm'],seed=1,complete_seconds=seconds,
                completion_SHA=sha(dest/'completion.json'),audit_SHA=sha(dest/'audit.json'),
                original_supervisor_observed_seconds=rec['completion']['fully_observed_end_to_end_seconds'],
                includes_admission_identity_checks_startup_native_calls_callbacks_raw_writes_postexit_audit_crosscheck=True,
                first_arm_includes_wrapper_creation_import_and_group_admission=number==first))
            write(d/f'{number:02d}_after.json',dict(completed_and_audited=True,whole_arm_receipt_SHA=sha(dest/'whole_arm_receipt.json')))
            assert seconds<=launch['cap_seconds'],'full arm exceeded frozen cap'
        if qualification:
            recs=records(camp);assert len(recs)==2
            mb=Path(ident['launches'][1]['destination'])
            with (mb/'external/paper_optimize_ledger.csv').open(newline='') as f:rows=list(csv.DictReader(f))
            starts=[p for p in (mb/'external/native_logs').glob('*.round68.start.json') if read(p).get('submitted')]
            assert any(r['solve_kind']=='LP' for r in rows) and any(r['solve_kind']!='LP' for r in rows) and starts
            write(OUT/'qualification/identity.json',dict(passed=True,production_PE_SHA=PE_SHA,DLL_SHA=DLL_SHA,
                source_bindings=bindings(),helpers=helpers(),current_CLI_records=recs,
                qualified_argv=[l['command'] for l in ident['launches']],LP_reached=True,MIP_reached=True,
                submitted_Starts=[p.relative_to(ROOT).as_posix() for p in starts],legal_terminations=2,not_performance=True,
                qualification_campaign_identity_SHA=sha(camp/'identity.json'),envelope_SHA=sha(OUT/'qualification/envelope.json')))
    except BaseException:
        code=1;(d/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:
        write(d/'receipt.json',dict(exit_code=code,outer_seconds=time.perf_counter()-tick,stop_reason='normal_return' if code==0 else 'actual_exception',
            conservative_process_starts=count+1,qualification=qualification,
            actual_native_children_with_launch=sum((Path(l['destination'])/'launch.json').exists() for l in ident['launches'][first-1:last]),
            nested_seconds_added=False,earlier_failure_slots_refunded=False))
        print(json.dumps(read(d/'receipt.json')),flush=True)

if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare()
    elif sys.argv[1]=='billed':billed(sys.argv[2],int(sys.argv[3]),int(sys.argv[4]),sys.argv[5],'--qualification' in sys.argv[6:])
    else:raise ValueError(sys.argv[1])
