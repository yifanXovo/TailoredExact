"""Round-local long research window with normal-stop-first watchdog.

Same receipt/budget/PID-birth contract as the inherited serial meter. The
larger capacity is only for this user's 36-hour offline study, not a
production time-switch mechanism or a global process-policy change.
"""
from round158_common import *

def metered(label,kind,args,reservation,timeout,cwd):
    assert 28800<float(timeout)<=TOTAL
    assert not os.environ.get('ROUND140_METERED_PARENT_LABEL')
    before=meter.budget();assert not before['unclosed'],before
    assert 0<float(reservation)<=before['remaining_G1_seconds']
    assert kind in meter.LIMITS and float(reservation)<=before['category_remaining'][kind]
    folder=OUT/'fees'/label;folder.mkdir(parents=True,exist_ok=False)
    command=list(map(str,args));tick=time.perf_counter();started=time.time();child=None;identity=None;failure=None;timeout_hit=False
    # Long research children have the level/label pair in their arguments.
    assert Path(command[2]).name=='round158_level.py'
    research_label=command[5];request_folder=OUT/'level'/research_label
    assert Path(research_label).name==research_label and research_label not in ('.','..','default')
    write(folder/'launch.json',dict(UTC=utc(),kind=kind,command=command,cwd=str(cwd),
        timeout_seconds=float(timeout),reservation_seconds=float(reservation),budget_before=before,
        parent_pid=os.getpid(),parent_birth=meter.process_birth(os.getpid()),
        normal_terminate_request_seconds=float(timeout)-120,normal_terminate_grace_seconds=120,
        per_round_long_offline_capacity=True,supervisor_SHA=sha(__file__)))
    env=meter.environment();env['ROUND140_METERED_PARENT_LABEL']=label
    with (folder/'stdout.log').open('xb') as stdout,(folder/'stderr.log').open('xb') as stderr:
        try:
            child=subprocess.Popen(command,cwd=cwd,env=env,stdout=stdout,stderr=stderr,creationflags=subprocess.CREATE_NO_WINDOW)
            birth=meter.process_birth(child.pid);assert birth is not None,'long research child exited before identity capture'
            identity=dict(pid=child.pid,parent_pid=os.getpid(),command=command,**birth);write(folder/'PID.json',identity)
            requested=False
            while child.poll() is None:
                elapsed=time.perf_counter()-tick
                if elapsed>=float(timeout)-120 and not requested:
                    write(request_folder/'TERMINATE.json',dict(UTC=utc(),reason='outer watchdog normal-stop-first at declared offline capacity',
                        source_fee=label,save_and_verify_after_Optimize=True));requested=True
                    write(folder/'normal_terminate_request.json',dict(UTC=utc(),elapsed=elapsed,request=str(request_folder/'TERMINATE.json')))
                if elapsed>=float(timeout):
                    timeout_hit=True;meter._kill_owned_tree(child,identity,folder);break
                try:child.wait(timeout=min(30.,max(.1,float(timeout)-elapsed)))
                except subprocess.TimeoutExpired:pass
        except BaseException as error:
            failure=dict(type=type(error).__name__,message=str(error),UTC=utc());write(folder/'supervisor_failure.json',failure)
            if child is not None and child.poll() is None and identity:
                write(folder/'pending_exit.json',dict(failure=failure,identity=identity,
                    still_alive=meter.process_snapshot(identity),no_automatic_rerun=True));raise
    rc=127 if child is None else int(child.returncode);elapsed=time.perf_counter()-tick
    write(folder/'receipt.json',dict(exit_code=rc,outer_seconds=elapsed,G1_seconds=elapsed,
        separately_reported_seconds=0.,start_unix=started,end_unix=time.time(),timeout=timeout_hit,
        supervisor_failure=failure,exit_observed=True,nested_H_LP_MIP_not_added=True,budget_category=kind))
    after=meter.budget();print(json.dumps(dict(label=label,exit_code=rc,outer_seconds=elapsed,budget=after)),flush=True)
    assert after['remaining_G1_seconds']>=0,after
    return 124 if timeout_hit else (1 if failure else rc)
