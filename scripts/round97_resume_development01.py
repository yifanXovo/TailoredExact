"""Recover the queue's status-file failure; only never-started arms 3 and 4.

The original launcher exited successfully. The first queue stopped before
vector audit or any additional solver launch because immutable write() was
incorrectly used for mutable status.json. Preserve that queue and its script.
"""
import json
import time
from pathlib import Path
import round97_campaign as campaign
import round97_vector_audit as vectors
from round97_campaign import OUT, read, write, sha

CAMP = OUT / 'development01'
QUEUE = CAMP / 'continuation_queue_recovery01'


def record(phase, **extra):
    row = dict(phase=phase, unix=time.time(), **extra)
    with (QUEUE / 'events.jsonl').open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(row) + '\n')
        stream.flush()
    temporary = QUEUE / 'status.json.tmp'
    temporary.write_text(json.dumps(row, indent=2) + '\n', encoding='utf-8')
    temporary.replace(QUEUE / 'status.json')
    print(json.dumps(row), flush=True)


def prefix(number):
    rows = [json.loads(line) for line in (CAMP / 'summary.jsonl').read_text().splitlines()]
    assert len(rows) == number and [r['number'] for r in rows] == list(range(1, number + 1))
    assert all(r['audit_passed'] and r['completion']['returncode'] == 0 for r in rows)
    return rows


def main():
    campaign.ext.ensure_idle()
    previous = CAMP / 'continuation_queue'
    prior_events = [json.loads(line) for line in (previous / 'events.jsonl').read_text().splitlines()]
    assert prior_events[-1]['phase'] == 'stopped_failure_no_restart'
    assert 'FileExistsError' in prior_events[-1]['error']
    assert not any(e['phase'] == 'launching_registered_arm' for e in prior_events)
    prefix(2)
    identity = read(CAMP / 'identity.json')
    assert identity['source_hashes'] == campaign.bindings()
    assert [r['arm'] for r in identity['launches']] == ['SHADOW', 'FEEDBACK', 'OFF', 'P-GRB']
    assert all(not Path(r['destination']).exists() for r in identity['launches'][2:])
    QUEUE.mkdir(exist_ok=False)
    write(QUEUE / 'identity.json', dict(inherited_batch_sha256=sha(CAMP / 'identity.json'),
        queue_sha256=sha(__file__), vector_checker_sha256=sha(vectors.__file__),
        previous_queue_identity_sha256=sha(previous / 'identity.json'),
        previous_queue_events_sha256=sha(previous / 'events.jsonl'),
        completed_prefix=2, new_launch_numbers=[3, 4], maximum_new_starts=2,
        maximum_new_process_seconds=7200,
        policy='Status I/O repair only. Audit completed arm2; run only original never-started arms3/4 serially; stop on failure, no retry/extension.'))
    try:
        record('auditing_arm2_vectors')
        vectors.check(str(CAMP / 'raw/02_F5_FEEDBACK'), 'development01_F5_feedback_vectors')
        for number in [3, 4]:
            assert sha(CAMP / 'identity.json') == read(QUEUE / 'identity.json')['inherited_batch_sha256']
            assert sha(vectors.__file__) == read(QUEUE / 'identity.json')['vector_checker_sha256']
            record('launching_registered_arm', number=number, arm=identity['launches'][number-1]['arm'])
            campaign.run('development01', number)
            completed = prefix(number)[-1]
            record('registered_arm_audited', number=number, endpoint=completed['endpoint'])
            if number == 3:
                campaign.ext.ensure_idle()
                record('auditing_arm3_vectors')
                vectors.check(str(CAMP / 'raw/03_F5_OFF'), 'development01_F5_off_vectors')
        record('complete', completed_registered_arms=[1, 2, 3, 4])
    except BaseException as error:
        record('stopped_failure_no_restart', error=repr(error))
        raise


if __name__ == '__main__':
    main()
