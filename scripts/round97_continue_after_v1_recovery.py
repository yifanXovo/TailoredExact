"""Continue only registered unstarted arms after exact arm9 sidecar recovery.

Original failed audit and summary row remain unchanged. Future failures still
stop; the recovery is not a general audit override or permission to rerun.
"""
import argparse
import json
import time
from pathlib import Path
import round97_campaign_v2 as campaign
import round97_development_v2 as development
import round97_vector_audit as vectors
import round97_continue_development02 as previous
import round97_recover_v1_interruption as recovery
from round97_interrupted_evidence import validate_outcome
from round97_campaign_v2 import ROOT, OUT, read, write, sha, ext, r90, helper_bindings

CAMP=OUT/'development02'
BLOCKS={(9,10):'v1_p_after_recovery09',(10,13):'f2_after_recovery09'}
RECEIPT=OUT/'engineering/development02_hard_stop09_recovery02/receipt.json'


def prefix(identity,count):
    restored=recovery.validate()
    assert read(RECEIPT)['exit_code']==0 and read(RECEIPT)['optimizer_calls']==0
    rows=[json.loads(s) for s in (CAMP/'summary.jsonl').read_text().splitlines()]
    assert len(rows)==count
    assert [(r['number'],r['id'],r['arm']) for r in rows]==[
        (r['number'],r['id'],r['arm']) for r in identity['launches'][:count]]
    for row in rows:
        launch=identity['launches'][row['number']-1];raw=Path(launch['destination'])
        audit=read(raw/'audit.json');completion=read(raw/'completion.json')
        assert row['completion']==completion and row['audit_passed']==audit['passed']
        assert row['endpoint']==audit['endpoint']
        if row['number']==9:
            assert audit['passed'] is False and row==restored['original_summary_prefix'][8]
            assert completion==restored['completion']
        else:
            assert audit['passed']
            validate_outcome(launch,audit,completion)
    previous.check_prior_vectors(identity,min(count,8))
    for launch in identity['launches'][9:count]:
        if launch['arm']=='P-GRB':continue
        raw=Path(launch['destination'])
        if not (raw/'external/round97/events.jsonl').exists():continue
        path=OUT/f"development02_{launch['number']:02d}_vectors.json"
        assert read(path)['passed'] and read(path)['optimizer_calls']==0
        matches=[e for p in CAMP.glob('queue_*/events.jsonl') for e in map(json.loads,p.read_text().splitlines())
                 if e['phase']=='actual_model_vectors_passed' and e.get('number')==launch['number']]
        assert len(matches)==1 and matches[0]['audit_sha256']==sha(path)
    return rows


def identity_check(identity):
    development.qualified()
    assert identity['source_hashes']==campaign.bindings()
    assert identity['development_runner_sha256']==sha(development.__file__)
    assert identity['runner_sha256']==sha(campaign.__file__)
    assert identity['qualification_gate_sha256']==sha(development.GATE)
    assert identity['prereg_sha256']==sha(OUT/'research_state.md')
    assert identity['revision_plan_sha256']==sha(OUT/'revision02_plan.md')
    assert identity['build_identity_sha256']==sha(OUT/'production_v2_identity.json')
    assert identity['candidate_binary_sha256']==sha(campaign.BUILD/'ExactEBRP.exe')
    assert identity['dll_sha256']==sha('D:/gurobi1302/win64/bin/gurobi130.dll')
    for mapping in ('helper_hashes','inherited_reference_bindings'):
        for path,expected in identity[mapping].items():assert sha(ROOT/path)==expected,path


def main(completed,through):
    ext.ensure_idle();label=BLOCKS[(completed,through)]
    identity=read(CAMP/'identity.json');identity_check(identity);prefix(identity,completed)
    selected=identity['launches'][completed:through]
    assert all(not Path(r['destination']).exists() for r in selected)
    queue=CAMP/('queue_'+label);queue.mkdir(exist_ok=False)
    frozen=dict(batch_sha256=sha(CAMP/'identity.json'),queue_sha256=sha(__file__),
        recovery_sha256=sha(recovery.RECOVERY),recovery_receipt_sha256=sha(RECEIPT),
        helper_hashes=helper_bindings(),new_launch_numbers=[r['number'] for r in selected],
        maximum_new_starts=len(selected),maximum_new_process_seconds=sum(r['cap_seconds'] for r in selected),
        policy='Exact arm9 independently recovered; original raw failed audit/summary preserved. Arm5 prior acknowledgement retained. Unstarted registered arms only; stop on any new abnormality.')
    write(queue/'identity.json',frozen);start=time.perf_counter()
    def record(phase,**extra):
        row=dict(phase=phase,unix=time.time(),queue_elapsed_seconds=time.perf_counter()-start,**extra)
        with (queue/'events.jsonl').open('a',encoding='utf-8') as stream:
            stream.write(json.dumps(row)+'\n');stream.flush()
        tmp=queue/'status.json.tmp';tmp.write_text(json.dumps(row,indent=2)+'\n');tmp.replace(queue/'status.json')
        print(json.dumps(row),flush=True)
    try:
        for launch in selected:
            assert sha(CAMP/'identity.json')==frozen['batch_sha256']
            assert sha(__file__)==frozen['queue_sha256']
            assert sha(recovery.RECOVERY)==frozen['recovery_sha256']
            assert sha(RECEIPT)==frozen['recovery_receipt_sha256']
            for path,expected in frozen['helper_hashes'].items():assert sha(ROOT/path)==expected,path
            identity_check(identity);number=launch['number'];prefix(identity,number-1)
            assert sha(ROOT/launch['panel']['input_path'])==launch['panel']['input_sha256']
            ext.ensure_idle();record('launching_registered_arm',number=number,id=launch['id'],arm=launch['arm'])
            # Explicit reviewed admission replaces only campaign.run's all-pass
            # prefix assertion. The frozen launch, supervisor and auditor remain.
            r90.CAMPAIGN=CAMP;r90.audit_launch=campaign.auditor
            r90.run_one(launch,identity['prereg'],identity)
            raw=Path(launch['destination']);audit=read(raw/'audit.json');completion=read(raw/'completion.json')
            assert completion['stop_reason']=='normal_return' and completion['returncode']==0
            assert audit['passed'];record('registered_arm_audited',number=number,endpoint=audit['endpoint'])
            ext.ensure_idle()
            if launch['arm']!='P-GRB' and (raw/'external/round97/events.jsonl').exists():
                vector_label=f'development02_{number:02d}_vectors';tick=time.perf_counter()
                record('auditing_actual_model_vectors',number=number)
                vectors.check(str(raw),vector_label);path=OUT/(vector_label+'.json')
                assert read(path)['passed']
                record('actual_model_vectors_passed',number=number,optimizer_calls=0,
                    wrapper_seconds=time.perf_counter()-tick,audit_path=path.relative_to(OUT).as_posix(),audit_sha256=sha(path))
            prefix(identity,number)
        record('block_complete_requires_root_analysis',completed_prefix=through)
    except BaseException as error:
        record('stopped_failure_no_restart',error=repr(error));raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--completed',type=int,required=True)
    p.add_argument('--through',type=int,required=True);a=p.parse_args();main(a.completed,a.through)
