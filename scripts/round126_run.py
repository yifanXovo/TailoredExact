"""One actual child/exit meter. Waiting inside a child is never added twice."""
from round126_common import *
def child_creation(child):
    import ctypes
    from ctypes import wintypes
    api=ctypes.WinDLL('kernel32',use_last_error=True)
    api.GetProcessTimes.argtypes=[wintypes.HANDLE,*([ctypes.POINTER(wintypes.FILETIME)]*4)]
    values=[wintypes.FILETIME() for _ in range(4)]
    assert api.GetProcessTimes(wintypes.HANDLE(int(child._handle)),*(ctypes.byref(x) for x in values))
    return ((values[0].dwHighDateTime<<32)+values[0].dwLowDateTime)/1e7-11644473600.

def run(label,kind,limit,reserve,args):
    workspace();b=budget();assert not b['unclosed'],b
    assert b['remaining_outer_seconds']>=limit+reserve,b
    if kind=='qualification':assert b['qualification_seconds']+limit<=QUAL_LIMIT
    d=OUT/'fees'/label;d.mkdir(parents=True,exist_ok=False)
    cmd=[str(PYTHON),'-B',*args];tick=time.perf_counter();start=time.time()
    write(d/'launch.json',dict(UTC=utc(),command=cmd,cwd=str(ROOT),kind=kind,outer_limit=limit,
        reserved_remaining_seconds=reserve,budget_before=b,controller_pid=os.getpid()))
    with (d/'stdout.log').open('xb') as so,(d/'stderr.log').open('xb') as se:
        child=subprocess.Popen(cmd,cwd=ROOT,env=environment(),stdout=so,stderr=se)
        birth=child_creation(child)
        write(d/'PID.json',dict(pid=child.pid,parent_pid=os.getpid(),actual_creation_unix=birth,command=cmd))
        # Do not impose a second normal-exit cutoff. Every producer keeps its inherited cap/deadline.
        rc=child.wait()
    end=time.perf_counter();ended=time.time()
    observed=max(end-tick,ended-birth)
    native=[]
    if kind=='formal':
        n=int(args[-1]);i=read(OUT/f'campaign/group{n:02d}/identity.json')
        for l in i['launches']:
            p=Path(l['destination'])/'child_process_origin.json'
            if p.exists():native.append(read(p))
    if kind=='qualification':
        p=OUT/'qualification/reference_receipt.json'
        if p.exists():native=read(p).get('native_processes',[])
    write(d/'receipt.json',dict(exit_code=rc,actual_exit_observed=True,outer_seconds_upper=observed,
        child_creation_unix=birth,exit_observed_unix=ended,actual_native_starts=len(native),
        native_process_identities=native,nested_native_seconds_added=False,
        limit_exceeded=observed>limit,controller_elapsed_seconds=end-tick))
    print(json.dumps(dict(label=label,exit_code=rc,outer_seconds=observed,budget=budget())),flush=True)
    if rc:print((d/'stderr.log').read_text(encoding='utf-8',errors='replace')[-6000:],flush=True)
    assert observed<=limit,('outer task exceeded declared reservation',observed,limit)
    return rc

if __name__=='__main__':
    if sys.argv[1]=='all-formal':
        for n in range(1,7):
            label=f'formal{n:02d}'
            if (OUT/'fees'/label/'receipt.json').exists():
                assert read(OUT/'fees'/label/'receipt.json')['exit_code']==0;continue
            groups=read(OUT/'argv_freeze.json')['groups'];g=groups[n-1]
            reserve=sum(q['nominal_seconds']+q['management_reserve'] for q in groups[n:])
            rc=run(label,'formal',g['nominal_seconds']+360,reserve,['scripts/round126_campaign.py',str(n)])
            if rc:sys.exit(rc)
    else:
        sys.exit(run(sys.argv[1],sys.argv[2],float(sys.argv[3]),float(sys.argv[4]),sys.argv[5:]))
