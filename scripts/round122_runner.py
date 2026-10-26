"""Direct OS-exit accounting for one child wrapper; optionally eight serial groups."""
from round122_common import *
from qualify_round120 import child_creation

def run(kind,label,number=None):
    workspace();b=budget();assert not b['unclosed'],b
    args=['scripts/qualify_round122.py',kind,label] if kind in ['reference','cli'] else ['scripts/round122_campaign.py',str(number),label]
    cmd=[str(PYTHON),'-B',*args];start=time.perf_counter();unix=time.time()
    log=OUT/'controller'/label;log.mkdir(parents=True,exist_ok=False)
    with (log/'stdout.log').open('xb') as so,(log/'stderr.log').open('xb') as se:
        child=subprocess.Popen(cmd,cwd=ROOT,env=environment(),stdout=so,stderr=se)
        try:
            birth=child_creation(child)
            write(log/'launch.json',dict(pid=child.pid,parent_pid=os.getpid(),actual_creation_unix=birth,command=cmd,
                controller_pid=os.getpid(),controller_actual_creation_unix=child_creation(subprocess_proxy()),
                controller_startup_is_additional_observed_process=True))
            code=child.wait()
        except BaseException:
            # Only this just-created, owned wrapper and its descendants are eligible.
            if child.poll() is None:
                subprocess.run(['taskkill','/PID',str(child.pid),'/T','/F'],capture_output=True)
                if child.poll() is None:child.kill()
            child.wait();raise
    end=time.perf_counter();ended=time.time();d=OUT/'fees'/label
    launch=read(d/'launch.json');pending=read(d/'pending_exit_receipt.json')
    assert pending['wrapper_pid']==child.pid and pending['exit_code']==code
    seconds=max(pending['outer_seconds_lower'],end-start,ended-birth)
    write(d/'receipt.json',dict(pending,outer_seconds_upper=seconds,actual_exit_observed=True,exit_observed_unix=ended,
        process_creation_unix=birth,actual_exit_code=code,controller_elapsed=end-start,
        wrapper_import_creation_trailer_and_exit_included=True,nested_native_seconds_added=False,
        controller_process_count=1,controller_wait_is_nested_not_added_again=True))
    write(log/'receipt.json',dict(exit_code=code,seconds=end-start,budget=budget()))
    print(json.dumps(dict(label=label,exit_code=code,outer_seconds=seconds,budget=budget())),flush=True)
    assert code==0,dict(label=label,exit_code=code)
    return code

def subprocess_proxy():
    # child_creation only needs the live process handle; current-process pseudo-handle is valid.
    import ctypes,types
    api=ctypes.WinDLL('kernel32',use_last_error=True);api.GetCurrentProcess.restype=ctypes.c_void_p
    return types.SimpleNamespace(_handle=api.GetCurrentProcess())

def formal():
    for n in range(1,9):
        if (OUT/'fees'/f'formal{n:02d}'/'receipt.json').exists():
            assert read(OUT/'fees'/f'formal{n:02d}'/'receipt.json')['exit_code']==0;continue
        run('formal',f'formal{n:02d}',n)

if __name__=='__main__':
    if sys.argv[1]=='all-formal':formal()
    elif sys.argv[1]=='formal':run('formal',sys.argv[3],int(sys.argv[2]))
    else:run(sys.argv[1],sys.argv[2])
