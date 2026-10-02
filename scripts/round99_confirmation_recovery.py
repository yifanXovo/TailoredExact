"""Read-only checkpoint audit and finite recovery setup; never starts a solver.

The original stopped attempt is retained. Recovery replays its command once
from scratch, then only the two never-started original arms. No state import.
"""
import copy,json,shutil,time,subprocess
import round99_campaign as campaign
from round99_common import *

def prepare():
    campaign.ext.ensure_idle()
    original=OUT/'confirmation01';q=read(original/'identity.json')
    assert q['source_hashes']==bindings() and q['helpers']==campaign.helpers()
    assert q['candidate_binary_sha256']==sha(BUILD/'ExactEBRP.exe')
    assert q['runner_sha256']==sha(ROOT/'scripts/round99_campaign.py')
    assert q['dll_sha256']==sha('D:/gurobi1302/win64/bin/gurobi130.dll')
    assert sha(q['input_manifest'])==q['prereg_sha256']
    prefix=[json.loads(s) for s in (original/'summary.jsonl').read_text().splitlines()]
    assert len(prefix)==6 and all(x['audit_passed'] for x in prefix)
    launch=q['launches'][6];d=Path(launch['destination'])
    assert not (d/'completion.json').exists() and not (d/'result.json').exists()
    old_pid=read(d/'affinity.json')['pid']
    # PID absence supplements the missing session handle; PID reuse is rejected.
    info=subprocess.check_output(['powershell','-NoProfile','-Command',
        f'Get-CimInstance Win32_Process -Filter "ProcessId={old_pid}" | Select-Object ProcessId,Name,CommandLine | ConvertTo-Json -Compress'],text=True)
    assert not info.strip(),info
    samples=[json.loads(s) for s in (d/'samples.jsonl').read_text().splitlines()]
    final_sample=samples[-1];assert final_sample['observed_events']>0
    paths=sorted((d/'journal').glob('event_*.commit'),key=lambda p:int(p.stem.split('_')[1]))
    assert len(paths)==final_sample['observed_events']
    records=[]
    for seq,path in enumerate(paths,1):
        available=next(s['process_seconds'] for s in samples if s['observed_events']>=seq)
        records.append(campaign.r90.evidence.receipt(path,available,launch['cap_seconds']))
    audit=campaign.r90.evidence.audit(ROOT,launch['panel'],records,q['candidate_binary_sha256'])
    campaign.r90.evidence.finalize_endpoint(ROOT,launch['panel'],launch['arm'],audit,records,None,
        'external_session_interruption',launch['panel']['reference'])
    audit['passed']=True
    audit['scope']='committed checkpoint only; original exit, final result and exact outer duration unavailable; no complete-window claim'
    write(d/'interrupted_observations.json',records);write(d/'interrupted_audit.json',audit)
    receipt=dict(number=7,role='N3',arm='M-B',failed=True,optimizer_calls=audit['native_calls_started'],
        calls_returned=audit['native_calls_returned'],charged_outer_seconds=launch['cap_seconds'],
        exact_actual_outer_seconds=None,last_verified_process_seconds=final_sample['process_seconds'],
        actual_measurement_scope='Exact exit duration unavailable; reserve/charge the full predeclared3600s allowance conservatively, not measured runtime.',
        stop_reason='external_session_interruption',old_child_pid=old_pid,child_absence_verified=True,
        original_completion_missing=True,original_result_missing=True,checkpoint_endpoint=audit['endpoint'],
        checkpoint_audit_sha256=sha(d/'interrupted_audit.json'),original_identity_sha256=sha(original/'identity.json'),
        no_restart_state_import=True,no_stitching=True,checked_unix=time.time())
    write(d/'interruption_receipt.json',receipt)
    write(original/'interruption_manifest.json',dict(original_identity_sha256=sha(original/'identity.json'),
        passed_prefix=6,interrupted_number=7,never_started_numbers=[8,9],
        interruption_receipt_sha256=sha(d/'interruption_receipt.json'),recovery_campaign='confirmation_recovery01'))
    recovered=OUT/'confirmation_recovery01';recovered.mkdir(exist_ok=False)
    new=copy.deepcopy(q);new['launches']=[]
    for number,old in enumerate(q['launches'][6:],1):
        old_dest=old['destination'];dest=str(recovered/'raw'/f'{number:02d}_{old["id"]}_{old["arm"]}')
        item=copy.deepcopy(old);item.update(number=number,destination=dest,stage='confirmation_recovery01',
            original_number=old['number'],recovery_kind='one_explicit_fresh_repeat' if number==1 else 'never_started_original_arm')
        item['command']=[s.replace(old_dest,dest) for s in old['command']]
        assert item['command']!=old['command'] and not Path(dest).exists()
        new['launches'].append(item)
    new.update(planned_starts=3,maximum_process_seconds=10800,prepared_unix=time.time(),
        original_identity_sha256=sha(original/'identity.json'),recovery_setup_sha256=sha(__file__),
        no_algorithm_input_or_build_change=True,interrupted_original_never_reused=True)
    new['references']={'N3':q['references']['N3']}
    ref=recovered/'reference/N3';ref.mkdir(parents=True)
    old_ref=original/'reference/N3'
    for name in ['build.json','original.lp']:shutil.copy2(old_ref/name,ref/name)
    assert sha(ref/'original.lp')==q['references']['N3']['canonical_sha256']
    write(ref/'completion.json',dict(returncode=0,optimizer_calls=0,outer_seconds=0,copy_only=True,
        already_billed_parent='confirmation01/reference_batch',source_batch_receipt_sha256=sha(original/'reference_batch_receipt.json')))
    write(ref/'launch.json',dict(copy_only=True,optimizer_calls=0,source=str(old_ref)))
    write(recovered/'identity.json',new)
    write(recovered/'recovery_plan.json',dict(fresh_repeat_starts=1,never_started_original_starts=2,
        optimizer_calls='durable journal actual calls',caps=[3600,3600,3600],method_order=['M-B','ENS-C','P-GRB'],
        no_automatic_retry=True,maximum_total_billed_starts_including_final_audit=72,
        conservative_interrupted_allowance_seconds=3600,reason='Both previous observer/session handles missing and native PID verified absent; preserve interruption and do not concatenate windows.'))
    print(json.dumps(receipt));print('prepared only3 recovery arms; zero native work in this setup')

if __name__=='__main__':prepare()
