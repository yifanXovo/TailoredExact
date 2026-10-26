"""Run an explicitly selected contiguous block of frozen development arms.

No retries, extension, parallel optimization or automatic candidate choice.
Each actual-model vector audit runs only after its solver has exited.
"""
import argparse
import json
import time
from pathlib import Path
import round97_development_v2 as development
import round97_vector_audit as vectors
from round97_campaign_v2 import ROOT, OUT, read, write, sha, ext, helper_bindings

CAMP=OUT/'development02'


def prefix(identity, count):
    path=CAMP/'summary.jsonl'
    rows=[json.loads(s) for s in path.read_text().splitlines()] if path.exists() else []
    assert len(rows)==count
    assert [(r['number'],r['id'],r['arm']) for r in rows]==[
        (r['number'],r['id'],r['arm']) for r in identity['launches'][:count]]
    assert all(r['audit_passed'] and r['completion']['returncode']==0 and
               r['completion']['stop_reason']=='normal_return' for r in rows)
    return rows


def main(label, completed, through):
    ext.ensure_idle()
    assert label and all(c.isalnum() or c in '_-' for c in label)
    identity=read(CAMP/'identity.json')
    assert 0<=completed<through<=len(identity['launches'])
    prefix(identity,completed)
    prior_blocks=[]
    if completed:
        for status_path in CAMP.glob('queue_*/status.json'):
            status=read(status_path)
            if status.get('phase')=='block_complete_requires_root_analysis':
                prior_blocks.append((read(status_path.parent/'identity.json'),status_path.parent))
        covered=[]
        for previous,folder in sorted(prior_blocks,key=lambda item:item[0]['completed_prefix']):
            numbers=previous['new_launch_numbers']
            if numbers[-1]>completed:continue
            assert previous['batch_sha256']==sha(CAMP/'identity.json')
            assert previous['completed_prefix']==len(covered)
            events=[json.loads(s) for s in (folder/'events.jsonl').read_text().splitlines()]
            assert events[-1]['phase']=='block_complete_requires_root_analysis'
            for number in numbers:
                launch=identity['launches'][number-1]
                if launch['arm']=='P-GRB':continue
                receipts=[e for e in events if e.get('number')==number and
                          e['phase'] in ['actual_model_vectors_passed','no_native_session_vectors']]
                assert len(receipts)==1
                receipt=receipts[0]
                if receipt['phase']=='actual_model_vectors_passed':
                    path=OUT/receipt['audit_path']
                    assert sha(path)==receipt['audit_sha256'] and read(path)['passed']
                else:
                    assert not (Path(launch['destination'])/'external/round97/events.jsonl').exists()
            covered.extend(numbers)
        assert covered==list(range(1,completed+1)), 'Earlier block vector audit not successfully completed'
    selected=identity['launches'][completed:through]
    assert all(not Path(r['destination']).exists() for r in selected)
    development.qualified()
    queue=CAMP/('queue_'+label)
    queue.mkdir(exist_ok=False)
    frozen=dict(batch_sha256=sha(CAMP/'identity.json'),queue_sha256=sha(__file__),
        helper_hashes=helper_bindings(),
        vector_checker_sha256=sha(vectors.__file__),completed_prefix=completed,
        new_launch_numbers=[r['number'] for r in selected],maximum_new_starts=len(selected),
        maximum_new_process_seconds=sum(r['cap_seconds'] for r in selected),
        policy='Only this frozen contiguous block. Audit sequentially. Stop on failure; no retry, extension or candidate promotion.')
    write(queue/'identity.json',frozen)
    start=time.perf_counter()
    def record(phase,**extra):
        row=dict(phase=phase,unix=time.time(),queue_elapsed_seconds=time.perf_counter()-start,**extra)
        with (queue/'events.jsonl').open('a',encoding='utf-8') as stream:
            stream.write(json.dumps(row)+'\n');stream.flush()
        tmp=queue/'status.json.tmp'
        tmp.write_text(json.dumps(row,indent=2)+'\n',encoding='utf-8')
        tmp.replace(queue/'status.json')
        print(json.dumps(row),flush=True)
    try:
        for launch in selected:
            assert sha(CAMP/'identity.json')==frozen['batch_sha256']
            assert sha(__file__)==frozen['queue_sha256']
            assert sha(vectors.__file__)==frozen['vector_checker_sha256']
            for path,expected in frozen['helper_hashes'].items():
                assert sha(ROOT/path)==expected,path
            number=launch['number']
            prefix(identity,number-1)
            record('launching_registered_arm',number=number,id=launch['id'],arm=launch['arm'])
            development.run(number)
            row=prefix(identity,number)[-1]
            record('registered_arm_audited',number=number,endpoint=row['endpoint'])
            ext.ensure_idle()
            if launch['arm']!='P-GRB':
                source=Path(launch['destination'])/'external/round97/events.jsonl'
                if source.exists():
                    audit_label=f'development02_{number:02d}_vectors'
                    record('auditing_actual_model_vectors',number=number)
                    tick=time.perf_counter()
                    vectors.check(launch['destination'],audit_label)
                    record('actual_model_vectors_passed',number=number,optimizer_calls=0,
                        wrapper_seconds=time.perf_counter()-tick,
                        audit_path=audit_label+'.json',audit_sha256=sha(OUT/(audit_label+'.json')))
                else:record('no_native_session_vectors',number=number,optimizer_calls=0)
        record('block_complete_requires_root_analysis',completed_prefix=through)
    except BaseException as error:
        record('stopped_failure_no_restart',error=repr(error))
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--label',required=True)
    parser.add_argument('--completed',required=True,type=int)
    parser.add_argument('--through',required=True,type=int)
    args=parser.parse_args()
    main(args.label,args.completed,args.through)
