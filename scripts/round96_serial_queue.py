"""Bounded remaining research queue; serial, fail closed, never resumes a paid arm.

This is orchestration of the already authorized complete experiments, not an
algorithm that allocates internal solver time or selects instance-wise winners.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from round96_prepare import ROOT,OUT,read,write,sha

ORDER=[('primal',range(1,4)),('external',range(4,7)),('primal',range(4,7)),
       ('external',range(7,10)),('primal',range(7,10)),('external',range(10,13)),
       ('primal',range(10,13)),('external',range(13,19))]

def sources():
    paths=['scripts/round96_serial_queue.py','scripts/round96_external.py','scripts/round96_primal.py',
           'scripts/round96_primal_launch.py','results/unified_exact_round96/primal_admission.json',
           'results/unified_exact_round96/external/identity.json','results/unified_exact_round96/primal/identity.json']
    return {path:sha(ROOT/path) for path in paths}

def prepare():
    identity={kind:read(OUT/kind/'identity.json') for kind in ['external','primal']};jobs=[]
    for kind,numbers in ORDER:
        for number in numbers:
            launch=identity[kind]['launches'][number-1]
            assert launch['number']==number and not (ROOT.__class__(launch['destination'])).exists()
            jobs.append(dict(campaign=kind,number=number,role=launch['id'],arm=launch['arm'],
                cap_seconds=launch['cap_seconds'],destination=launch['destination']))
    assert len(jobs)==27
    write(OUT/'serial_queue_plan.json',dict(jobs=jobs,bindings=sources(),optimizer_calls=0,
        required_completed_external_prefix=3,required_completed_primal_prefix=0,
        rationale='Finish a complete original-long-tail triple, then alternate whole role triples; frozen per-role arm orders and global external order are preserved. No outcomes of these unstarted jobs used.',
        stop_rule='Any runner, scope, physical, identity or resource failure stops the queue; no restart.'))

def run():
    plan=read(OUT/'serial_queue_plan.json');assert plan['bindings']==sources()
    import round96_external as external
    external.ensure_idle()
    prior=external.completed();assert len(prior)==3 and all(r['audit_passed'] for r in prior)
    assert not (OUT/'primal/summary.jsonl').exists()
    write(OUT/'serial_queue_started.json',dict(pid=os.getpid(),started_unix=time.time(),
        plan_sha256=sha(OUT/'serial_queue_plan.json'),planned_jobs=len(plan['jobs'])))
    records=[];started=time.perf_counter();error=None
    try:
        for job in plan['jobs']:
            assert not (OUT/'serial_queue_stop.json').exists(),'Administrative stop requested; preserve completed prefix'
            kind=job['campaign'];number=job['number'];stem=f'{kind}_run_{number:02d}'
            logfile=OUT/(stem+'.log');receipt=OUT/(stem+'.receipt.json')
            assert not logfile.exists() and not receipt.exists()
            script='scripts/round96_external.py' if kind=='external' else 'scripts/round96_primal_launch.py'
            command=[sys.executable,script,'run','--number',str(number)]
            write(OUT/(stem+'.outer_launch.json'),dict(job,command=command,started_unix=time.time()))
            print(json.dumps(dict(starting=job)),flush=True);tick=time.perf_counter()
            with logfile.open('x',encoding='utf-8') as stream:
                completed=subprocess.run(command,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT)
            row=dict(job,exit_code=completed.returncode,wall_seconds=time.perf_counter()-tick,
                scope='Outer runner including preflight and offline audit; native/process cost is nested, never added twice.')
            write(receipt,row);records.append(row)
            print(json.dumps(dict(finished=row)),flush=True)
            assert completed.returncode==0, 'preserve paid prefix and stop; no retry'
            if number%3==0:
                signal_path=OUT/kind/f'decision_signals_{job["role"]}.json'
                signals=read(signal_path)
                if signals['signals']:
                    review_path=OUT/f'serial_review_{kind}_{job["role"]}.json'
                    assert not review_path.exists()
                    write(OUT/f'serial_review_pending_{kind}_{job["role"]}.json',dict(
                        signal_path=signal_path.relative_to(ROOT).as_posix(),signal_sha256=sha(signal_path),
                        scope='Research interpretation pause after a completed triple; no optimizer is running.'))
                    print(json.dumps(dict(review_required=True,campaign=kind,role=job['role'],
                        signal_path=str(signal_path),review_path=str(review_path))),flush=True)
                    while not review_path.exists():
                        assert not (OUT/'serial_queue_stop.json').exists(),'Administrative stop during interpretation review'
                        time.sleep(1)
                    review=read(review_path)
                    assert review['continue_planned_runs'] is True and review['signal_sha256']==sha(signal_path)
    except BaseException as exc:
        error=repr(exc);raise
    finally:
        write(OUT/'serial_queue_completion.json',dict(records=records,error=error,
            completed=len(records),planned=len(plan['jobs']),elapsed_seconds=time.perf_counter()-started,
            passed=error is None and len(records)==len(plan['jobs'])))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','run']);args=parser.parse_args()
    globals()[args.action]()
