"""Finish only the registered, never-started qualification arms after arm1.

Run only after the arm1 launcher exits. Audits and solvers are strictly
sequential; any failure ends the queue with no retry or budget extension.
"""
import json
import time
from pathlib import Path
import round97_campaign_v2 as campaign
import round97_vector_audit as vectors
from round97_campaign_v2 import OUT, read, write, sha

CAMP = OUT/'qualification03'
QUEUE = CAMP/'continuation_queue'


def record(phase, **extra):
    row = dict(phase=phase,unix=time.time(),**extra)
    with (QUEUE/'events.jsonl').open('a',encoding='utf-8') as stream:
        stream.write(json.dumps(row)+'\n')
        stream.flush()
    temporary=QUEUE/'status.json.tmp'
    temporary.write_text(json.dumps(row,indent=2)+'\n',encoding='utf-8')
    temporary.replace(QUEUE/'status.json')
    print(json.dumps(row),flush=True)


def prefix(number):
    rows=[json.loads(s) for s in (CAMP/'summary.jsonl').read_text().splitlines()]
    assert len(rows)==number and [r['number'] for r in rows]==list(range(1,number+1))
    launches=read(CAMP/'identity.json')['launches'][:number]
    assert [(r['number'],r['id'],r['arm']) for r in rows]==[
        (r['number'],r['id'],r['arm']) for r in launches]
    assert all(r['audit_passed'] and r['completion']['returncode']==0 and
               r['completion']['stop_reason']=='normal_return' for r in rows)
    return rows


def main():
    campaign.ext.ensure_idle()
    prefix(1)
    identity=read(CAMP/'identity.json')
    assert [(r['id'],r['arm']) for r in identity['launches']]==[
        ('F5','SHADOW'),('F5','FEEDBACK'),('F2','FEEDBACK')]
    assert all(not Path(r['destination']).exists() for r in identity['launches'][1:])
    campaign.ready_build()
    QUEUE.mkdir(exist_ok=False)
    frozen=dict(batch_sha256=sha(CAMP/'identity.json'),queue_sha256=sha(__file__),
        vector_checker_sha256=sha(vectors.__file__),maximum_new_starts=2,
        maximum_new_process_seconds=1140,completed_prefix=1,new_launch_numbers=[2,3],
        policy='Audit arm1; run registered arms2/3 serially with actual-matrix audits between. Stop on any failure. No extension, retry or promotion.')
    write(QUEUE/'identity.json',frozen)
    try:
        for number in [1,2,3]:
            assert sha(CAMP/'identity.json')==frozen['batch_sha256']
            assert sha(__file__)==frozen['queue_sha256']
            assert sha(vectors.__file__)==frozen['vector_checker_sha256']
            launch=identity['launches'][number-1]
            if number>1:
                record('launching_registered_arm',number=number,id=launch['id'],arm=launch['arm'])
                campaign.run('qualification03',number)
                completed=prefix(number)[-1]
                record('registered_arm_audited',number=number,endpoint=completed['endpoint'])
            campaign.ext.ensure_idle()
            record('auditing_actual_model_vectors',number=number)
            label=f'qualification03_{number:02d}_vectors'
            tick=time.perf_counter()
            vectors.check(launch['destination'],label)
            record('actual_model_vectors_passed',number=number,
                   wrapper_seconds=time.perf_counter()-tick,optimizer_calls=0,
                   audit_path=label+'.json',audit_sha256=sha(OUT/(label+'.json')))
        record('complete_requires_root_qualification_decision',completed_registered_arms=[1,2,3])
    except BaseException as error:
        record('stopped_failure_no_restart',error=repr(error))
        raise


if __name__=='__main__':main()
