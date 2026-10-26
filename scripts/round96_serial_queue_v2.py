"""Continue only the 24 never-started jobs after offline reader recovery.

Original queue and paid evidence stay immutable. Every completed triple gets
an idle review boundary; this orchestration never changes a solver's policy.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from round96_prepare import ROOT,OUT,read,write,sha
import round96_primal_recovery_v2 as primal
import round96_external as external

def bindings():
    paths=['scripts/round96_serial_queue_v2.py','scripts/round96_primal_recovery_v2.py',
        'scripts/round96_external.py','results/unified_exact_round96/serial_queue_plan.json',
        'results/unified_exact_round96/serial_queue_completion.json',
        'results/unified_exact_round96/primal_v2/identity.json',
        'results/unified_exact_round96/primal_v2/admission.json']
    return {p:sha(ROOT/p) for p in paths}

def prepare():
    external.ensure_idle();old=read(OUT/'serial_queue_completion.json')
    assert old['completed']==3 and not old['passed']
    assert len(external.completed())==3
    prefix=primal.records();assert len(prefix)==3 and all(r['audit_passed'] for r in prefix)
    jobs=read(OUT/'serial_queue_plan.json')['jobs'][3:]
    assert len(jobs)==24 and all(not Path(j['destination']).exists() for j in jobs)
    write(OUT/'serial_queue_v2_plan.json',dict(jobs=jobs,bindings=bindings(),
        paid_restarts=0,optimizer_calls=0,
        reason='Legacy audit arm-label dispatch corrected by offline replay; continue only unchanged never-started commands. Add idle review boundaries after every triple for compact analysis without CPU contention.'))

def run():
    plan=read(OUT/'serial_queue_v2_plan.json');assert plan['bindings']==bindings()
    external.ensure_idle();assert len(external.completed())==3 and len(primal.records())==3
    write(OUT/'serial_queue_v2_started.json',dict(pid=os.getpid(),started_unix=time.time(),
        plan_sha256=sha(OUT/'serial_queue_v2_plan.json'),planned_jobs=24))
    records=[];start=time.perf_counter();error=None
    try:
        for job in plan['jobs']:
            assert not (OUT/'serial_queue_stop.json').exists()
            kind=job['campaign'];number=job['number'];stem=f'{kind}_run_{number:02d}'
            logfile=OUT/(stem+'.log');receipt=OUT/(stem+'.receipt.json')
            assert not logfile.exists() and not receipt.exists() and not Path(job['destination']).exists()
            script='scripts/round96_external.py' if kind=='external' else 'scripts/round96_primal_recovery_v2.py'
            command=[sys.executable,script,'run','--number',str(number)]
            write(OUT/(stem+'.outer_launch.json'),dict(job,command=command,started_unix=time.time()))
            print(json.dumps(dict(starting=job)),flush=True);tick=time.perf_counter()
            with logfile.open('x',encoding='utf-8') as stream:
                result=subprocess.run(command,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT)
            row=dict(job,exit_code=result.returncode,wall_seconds=time.perf_counter()-tick,
                scope='Outer wrapper; process/native costs are nested and not added twice.')
            write(receipt,row);records.append(row);print(json.dumps(dict(finished=row)),flush=True)
            assert result.returncode==0,'Stop and preserve; no paid restart'
            if number%3==0:
                campaign=OUT/('primal_v2' if kind=='primal' else 'external')
                signal=campaign/f'decision_signals_{job["role"]}.json';assert signal.exists()
                review=OUT/f'serial_review_v2_{kind}_{job["role"]}.json';assert not review.exists()
                write(OUT/f'serial_review_v2_pending_{kind}_{job["role"]}.json',dict(
                    signal_path=signal.relative_to(ROOT).as_posix(),signal_sha256=sha(signal),
                    scope='Completed triple; no optimizer running. Review all signs, including no severe signal.'))
                print(json.dumps(dict(review_required=True,role=job['role'],campaign=kind,review_path=str(review))),flush=True)
                while not review.exists():
                    assert not (OUT/'serial_queue_stop.json').exists();time.sleep(1)
                decision=read(review)
                assert decision['continue_planned_runs'] is True and decision['signal_sha256']==sha(signal)
    except BaseException as exc:
        error=repr(exc);raise
    finally:
        write(OUT/'serial_queue_v2_completion.json',dict(records=records,error=error,
            completed=len(records),planned=24,elapsed_seconds=time.perf_counter()-start,
            passed=error is None and len(records)==24))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','run']);args=parser.parse_args()
    globals()[args.action]()
