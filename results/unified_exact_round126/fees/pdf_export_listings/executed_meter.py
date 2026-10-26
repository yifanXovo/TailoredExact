from pathlib import Path
import sys,subprocess,time,os
root=Path('E:/codes/ExactEBRP-work/worktrees/round126');sys.path.insert(0,str(root/'scripts'))
from round126_common import *
from round126_run import child_creation
label='pdf_export_listings';b=budget();assert set(b['unclosed'])<=set(['review_quant'])
assert b['remaining_outer_seconds']>=900+1800+3600
folder=OUT/'fees'/label;folder.mkdir(exist_ok=False)
code=Path(__file__).read_bytes();(folder/'executed_meter.py').write_bytes(code)
cmd=[str(PYTHON),'-B','scripts/round126_export.py']
write(folder/'launch.json',dict(UTC=utc(),command=cmd,cwd=str(ROOT),kind='engineering',outer_limit=900,reserved_remaining_seconds=3600,parallel_unclosed_reserved_seconds=1800,budget_before=b,controller_pid=os.getpid(),parallel_engineering_only_after_all_formal_exit=True))
tick=time.perf_counter()
with (folder/'stdout.log').open('xb') as so,(folder/'stderr.log').open('xb') as se:
    child=subprocess.Popen(cmd,cwd=ROOT,env=environment(),stdout=so,stderr=se);birth=child_creation(child)
    write(folder/'PID.json',dict(pid=child.pid,parent_pid=os.getpid(),actual_creation_unix=birth,command=cmd))
    rc=child.wait()
elapsed=max(time.perf_counter()-tick,time.time()-birth)
write(folder/'receipt.json',dict(exit_code=rc,actual_exit_observed=True,outer_seconds_upper=elapsed,child_creation_unix=birth,exit_observed_unix=time.time(),actual_native_starts=0,nested_native_seconds_added=False,limit_exceeded=elapsed>900,controller_elapsed_seconds=time.perf_counter()-tick))
print(json.dumps(dict(label=label,exit_code=rc,seconds=elapsed,budget=budget())))
if rc:print((folder/'stderr.log').read_text(encoding='utf-8',errors='replace')[-5000:])
sys.exit(rc)
