"""Frozen three-method campaigns using the inherited R100/R90 full supervisor."""
from round108_common import *
from round108_prepare import COMMON
import round100_campaign as original
import round90_lp_g_g3 as r90
from round100_idle import ensure_idle

original.BUILD=BUILD

def helpers():
    names=['round108_common.py','round108_prepare.py','round108_campaign.py',
        'round108_qualification.py','round108_native_inspect.py','round100_campaign.py',
        'round100_common.py','round100_idle.py','round90_lp_g_g3.py','round88_a1_g3.py',
        'round94_lpg_formal_recovery_v3.py','round94_lpg_contemporary.py',
        'round86_native_evidence.py','analyze_round61.py','round70_affinity.py',
        'round83_audit_v2.py','round75_startup.py','round96_external.py','round96_prepare.py',
        'generate_citibike443_regional_v1.py']
    return {'scripts/'+n:sha(ROOT/'scripts'/n) for n in names}

def prepare(name,protocol_path):
    protocol=read(protocol_path);camp=OUT/name;camp.mkdir(exist_ok=False)
    prereg=dict(common=COMMON,candidate_binary=(BUILD/'ExactEBRP.exe').relative_to(ROOT).as_posix(),
                candidate_binary_sha256=sha(BUILD/'ExactEBRP.exe'))
    launches=[];references={}
    for role in protocol['roles']:
        p=dict(role);assert sha(ROOT/p['input_path'])==p['input_sha256']
        folder=camp/'reference'/p['id'];folder.mkdir(parents=True)
        p['reference']=references[p['id']]=original.build_reference(p,folder)
        p['instance_path']=p['input_path']
        for arm in p['method_order']:
            assert arm in ['P-GRB','ENS-C','M-B']
            n=len(launches)+1;d=camp/'raw'/f'{n:02d}_{p["id"]}_{arm}'
            cmd=(r90.audited_runner_utilities.command_for(prereg,p,arm,d) if arm=='P-GRB'
                 else r90.command_for(prereg,p,'ENS-C',d))
            if arm=='M-B':cmd+=['--round98-state-service','m-binary']
            launches.append(dict(number=n,id=p['id'],arm=arm,panel=p,destination=str(d),stage=name,
                cap_seconds=p['cap_seconds'],hard_stop_seconds=p['cap_seconds']-2,command=cmd))
    value=dict(prereg=prereg,prereg_sha256=sha(protocol_path),runner_sha256=sha(__file__),source_hashes=bindings(),
        helpers=helpers(),candidate_binary_sha256=sha(BUILD/'ExactEBRP.exe'),dll_sha256=sha(DLL),
        protocol_path=str(Path(protocol_path).absolute()),references=references,launches=launches,
        reference_PE_SHA=sha(BUILD/'Round65ReferenceBuild.exe'),
        measured_source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        prepared_unix=time.time(),Optimize_calls=0)
    write(camp/'identity.json',value)
    print(json.dumps(dict(prepared=name,arms=len(launches),Optimize_calls=0)),flush=True)
    return value

def run(name,n,qualification=False):
    ensure_idle();camp=OUT/name;q=read(camp/'identity.json')
    assert q['source_hashes']==bindings() and q['helpers']==helpers()
    assert sha(__file__)==q['runner_sha256'] and sha(q['protocol_path'])==q['prereg_sha256']
    assert sha(BUILD/'ExactEBRP.exe')==q['candidate_binary_sha256'] and sha(DLL)==q['dll_sha256']
    if not qualification:
        gate=read(OUT/'review/performance_admission.json')
        assert gate['decision']=='ACCEPT' and gate['production_PE_SHA']==q['candidate_binary_sha256']
        assert gate['DLL_SHA']==q['dll_sha256'] and gate['source_bindings']==q['source_hashes']
        assert gate['qualification_identity_SHA']==sha(OUT/'qualification/identity.json')
        if name.startswith('confirmation'):
            assert read(OUT/'admission_decision.json')['bridge_pass'] is True
    records=[json.loads(s) for s in (camp/'summary.jsonl').read_text().splitlines()] if (camp/'summary.jsonl').exists() else []
    assert len(records)==n-1 and all(r['audit_passed'] for r in records),'never skip, rerun or splice'
    launch=q['launches'][n-1]
    assert not Path(launch['destination']).exists() and sha(ROOT/launch['panel']['input_path'])==launch['panel']['input_sha256']
    r90.CAMPAIGN=camp;r90.audit_launch=original.adapter
    rec=r90.run_one(launch,q['prereg'],q)
    group=[r for r in records+[rec] if r['id']==launch['id']]
    lows=[r['endpoint']['L'] for r in group];ups=[r['endpoint']['U'] for r in group if r['endpoint']['U'] is not None]
    assert not ups or max(lows)<=min(ups)+1e-7,'offline cross-arm contradiction'
    write(camp/f'cross_arm_{launch["id"]}_{len(group)}.json',dict(strongest_L=max(lows),best_physical_U=min(ups) if ups else None,
        passed=True,scope='offline contradiction check only; no combined certificate'))
    return rec

def billed(name,first,last,label):
    ensure_idle();q=read(OUT/name/'identity.json');b=budget()
    assert not b['unclosed'] and b['remaining_starts']>=last-first+2
    nominal=sum(x['cap_seconds'] for x in q['launches'][first-1:last])
    assert b['remaining_outer_seconds']>=nominal+120
    d=OUT/'fees'/label;d.mkdir(parents=True,exist_ok=False)
    write(d/'launch.json',dict(command=[sys.executable,__file__,'billed',name,str(first),str(last),label],
        engineering=False,conservative_process_starts=last-first+2,declared_native_children=last-first+1,
        actual_wrapper_processes=1,cap_seconds=nominal+120,budget_before=b,source_bindings=bindings(),
        production_PE_SHA=q['candidate_binary_sha256'],protocol_SHA=q['prereg_sha256']))
    write(d/'process.json',dict(pid=os.getpid(),parent_pid=os.getppid()))
    tick=time.perf_counter();code=0
    try:
        for n in range(first,last+1):
            arm_tick=time.perf_counter()
            write(d/f'{n:02d}_before.json',dict(number=n,id=q['launches'][n-1]['id'],arm=q['launches'][n-1]['arm']))
            rec=run(name,n)
            write(d/f'{n:02d}_after.json',dict(completed_and_audited=True))
            arm_seconds=time.perf_counter()-arm_tick
            dest=Path(q['launches'][n-1]['destination'])
            write(dest/'whole_arm_receipt.json',dict(number=n,id=rec['id'],arm=rec['arm'],
                complete_seconds=arm_seconds,completion_SHA=sha(dest/'completion.json'),audit_SHA=sha(dest/'audit.json'),
                original_supervisor_observed_seconds=rec['completion']['fully_observed_end_to_end_seconds'],
                includes_admission_identity_checks_startup_native_calls_callbacks_raw_writes_postexit_audit_crosscheck=True,
                scope='Measured wrapper entry before before-record through durable after-record; this timing receipt serialization is outer-fee overhead',
                native_time_added=False))
    except BaseException:
        code=1;raise
    finally:
        write(d/'receipt.json',dict(exit_code=code,outer_seconds=time.perf_counter()-tick,engineering=False,
            conservative_process_starts=last-first+2,stop_reason='normal_return' if code==0 else 'retained_campaign_failure'))

if __name__=='__main__':
    if sys.argv[1]=='billed':billed(sys.argv[2],int(sys.argv[3]),int(sys.argv[4]),sys.argv[5])
    else:raise ValueError('Preparation is paid by the declared qualification/reference wrapper')
