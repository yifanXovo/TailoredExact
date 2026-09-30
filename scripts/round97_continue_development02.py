"""Continue registered arms after one explicitly acknowledged audited hard stop.

Preserves arm5 and the original queue failure. No retry, change of caps,
automatic acceptance of future interruptions, or replacement final result.
"""
import argparse
import json
import time
from pathlib import Path
import round97_development_v2 as development
import round97_vector_audit as vectors
from round97_campaign_v2 import ROOT, OUT, read, write, sha, ext, helper_bindings

CAMP=OUT/'development02'
ACK=CAMP/'hard_stop05_acknowledgement.json'
BLOCKS={(5,7):'d7_recovery01',(7,10):'v1_after_d7',(10,13):'f2_after_d7'}


def prefix(identity,count):
    acknowledgement=read(ACK)
    assert acknowledgement['number']==5 and acknowledgement['optimizer_calls']==0
    for path,expected in acknowledgement['source_bindings'].items():
        assert sha(ROOT/path)==expected,path
    rows=[json.loads(s) for s in (CAMP/'summary.jsonl').read_text().splitlines()]
    assert len(rows)==count
    assert [(r['number'],r['id'],r['arm']) for r in rows]==[
        (r['number'],r['id'],r['arm']) for r in identity['launches'][:count]]
    for row in rows:
        launch=identity['launches'][row['number']-1];raw=Path(launch['destination'])
        assert row['audit_passed'] and read(raw/'audit.json')['passed']
        assert row['completion']==read(raw/'completion.json')
        assert row['endpoint']==read(raw/'audit.json')['endpoint']
        if row['number']==5:
            assert (row['id'],row['arm'])==('D7','P-GRB')
            assert row['completion']['stop_reason']=='whole_run_hard_stop'
            assert row['completion']['within_cap'] and row['completion']['returncode']!=0
            assert row['endpoint']['source']=='interrupted_committed_evidence'
            assert not row['endpoint']['certificate'] and not (raw/'result.json').exists()
        else:
            assert row['completion']['returncode']==0 and row['completion']['stop_reason']=='normal_return'
    return rows


def check_prior_vectors(identity,count):
    for launch in identity['launches'][:count]:
        if launch['arm']=='P-GRB':continue
        source=Path(launch['destination'])/'external/round97/events.jsonl'
        if not source.exists():continue
        number=launch['number'];path=OUT/f'development02_{number:02d}_vectors.json'
        audit=read(path);assert audit['passed'] and audit['optimizer_calls']==0
        matches=[]
        for events_path in CAMP.glob('queue_*/events.jsonl'):
            matches.extend(e for e in map(json.loads,events_path.read_text().splitlines())
                           if e['phase']=='actual_model_vectors_passed' and e.get('number')==number)
        assert len(matches)==1 and matches[0]['audit_path']==path.relative_to(OUT).as_posix()
        assert matches[0]['audit_sha256']==sha(path)


def main(completed,through):
    ext.ensure_idle();label=BLOCKS[(completed,through)]
    identity=read(CAMP/'identity.json');prefix(identity,completed)
    check_prior_vectors(identity,completed);development.qualified()
    selected=identity['launches'][completed:through]
    assert all(not Path(r['destination']).exists() for r in selected)
    queue=CAMP/('queue_'+label);queue.mkdir(exist_ok=False)
    frozen=dict(batch_sha256=sha(CAMP/'identity.json'),queue_sha256=sha(__file__),
        acknowledgement_sha256=sha(ACK),helper_hashes=helper_bindings(),
        vector_checker_sha256=sha(vectors.__file__),completed_prefix=completed,
        new_launch_numbers=[r['number'] for r in selected],maximum_new_starts=len(selected),
        maximum_new_process_seconds=sum(r['cap_seconds'] for r in selected),
        policy='Preserve acknowledged interrupted arm5 without rerun; only original registered unstarted arms. Stop on any further failure or interruption.')
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
            assert sha(ACK)==frozen['acknowledgement_sha256']
            assert sha(__file__)==frozen['queue_sha256'] and sha(vectors.__file__)==frozen['vector_checker_sha256']
            for path,expected in frozen['helper_hashes'].items():assert sha(ROOT/path)==expected,path
            number=launch['number'];prefix(identity,number-1);check_prior_vectors(identity,number-1)
            record('launching_registered_arm',number=number,id=launch['id'],arm=launch['arm'])
            development.run(number)
            row=prefix(identity,number)[-1]
            record('registered_arm_audited',number=number,endpoint=row['endpoint'])
            ext.ensure_idle()
            source=Path(launch['destination'])/'external/round97/events.jsonl'
            if launch['arm']!='P-GRB' and source.exists():
                label=f'development02_{number:02d}_vectors'
                record('auditing_actual_model_vectors',number=number)
                tick=time.perf_counter();vectors.check(str(launch['destination']),label)
                path=OUT/(label+'.json');assert read(path)['passed']
                record('actual_model_vectors_passed',number=number,optimizer_calls=0,
                    wrapper_seconds=time.perf_counter()-tick,audit_path=path.relative_to(OUT).as_posix(),audit_sha256=sha(path))
            elif launch['arm']!='P-GRB':record('no_native_session_vectors',number=number,optimizer_calls=0)
        record('block_complete_requires_root_analysis',completed_prefix=through)
    except BaseException as error:
        record('stopped_failure_no_restart',error=repr(error));raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--completed',type=int,required=True)
    parser.add_argument('--through',type=int,required=True);args=parser.parse_args()
    main(args.completed,args.through)
