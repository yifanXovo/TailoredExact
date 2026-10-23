"""Disjoint non-native delivery meters; never a formal experimental runner."""
from round132_common import *
from round132_release import idle

def run(label,command,timeout):
    idle();d=OUT/'delivery_costs'/label;d.mkdir(parents=True,exist_ok=False)
    tick=time.perf_counter();start=time.time();command=list(map(str,command))
    write(d/'launch.json',dict(UTC=utc(),kind='separate_delivery',command=command,cwd=str(ROOT),
        G1=False,timeout_seconds=timeout,nested_child_time_not_added=True))
    code=None;error=None
    with (d/'stdout.log').open('xb') as so,(d/'stderr.log').open('xb') as se:
        p=subprocess.Popen(command,cwd=ROOT,env=environment(),stdout=so,stderr=se)
        write(d/'PID.json',dict(pid=p.pid,parent_pid=os.getpid(),start_unix=start,command=command))
        try:code=p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            # Only this owned delivery child; formal solvers are prohibited by
            # the readiness guard. Preserve all partial outputs and diagnose.
            p.terminate();p.wait(timeout=30);code=p.returncode;error='finite delivery timeout; preserve attempt and inspect'
    seconds=time.perf_counter()-tick
    write(d/'receipt.json',dict(UTC=utc(),exit_code=code,error=error,seconds=seconds,
        G1_seconds=0,separately_reported_seconds=seconds,exit_observed=True,start_unix=start,end_unix=time.time(),
        no_formal_window_changed=True,outer_process_counted_once=True))
    print(json.dumps(dict(label=label,exit_code=code,seconds=seconds,error=error)),flush=True)
    if code or error:print((d/'stderr.log').read_text(encoding='utf-8',errors='replace')[-6000:],flush=True)
    return 1 if error else code

def account():
    closed=[];active=[]
    for p in sorted((OUT/'delivery_costs').glob('*/launch.json')):
        r=p.parent/'receipt.json'
        if not r.exists():active.append(p.parent.name);continue
        v=read(r);closed.append(dict(label=p.parent.name,**v))
    base=budget();value=dict(UTC=utc(),**base,delivery_process_receipts=closed,active_delivery_receipts=active,
        separate_postverify_from_G1_receipts=base['separately_reported_seconds'],
        separate_delivery_process_seconds=sum(r['seconds'] for r in closed),
        separate_measured_total_seconds=base['separately_reported_seconds']+sum(r['seconds'] for r in closed),
        writing_static_manual_wall_cost='Estimate only: overlapping wall time from initialization to current delivery; not exact CPU, and not added to measured serial subprocess costs',
        no_nested_H_LP_MIP_or_child_delivery_cost_added=True,
        delivery_plan=read(OUT/'delivery_cost_plan.json'))
    write(OUT/'resource_accounting.json',value);return value

if __name__=='__main__':
    action=sys.argv.pop(1)
    if action=='account':print(json.dumps(account()))
    elif action=='run':sys.exit(run(sys.argv[1],sys.argv[3:],float(sys.argv[2])))
    else:raise ValueError(action)
