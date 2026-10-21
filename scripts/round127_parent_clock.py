"""Observe an existing loop's actual birth/exit; charge only fee-free gaps.

The observer does not suspend or alter the target. Its waiting lifetime overlaps
the target and is not an additional solve/task charge. Windows handle identity
prevents a reused PID from being treated as the original process.
"""
from round127_common import *
import ctypes
from ctypes import wintypes

def observe(pid,label,expected_birth):
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];kernel.OpenProcess.restype=wintypes.HANDLE
    kernel.GetProcessTimes.argtypes=[wintypes.HANDLE,*([ctypes.POINTER(wintypes.FILETIME)]*4)];kernel.GetProcessTimes.restype=wintypes.BOOL
    kernel.WaitForSingleObject.argtypes=[wintypes.HANDLE,wintypes.DWORD];kernel.WaitForSingleObject.restype=wintypes.DWORD
    kernel.GetExitCodeProcess.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)];kernel.GetExitCodeProcess.restype=wintypes.BOOL
    kernel.CloseHandle.argtypes=[wintypes.HANDLE]
    handle=kernel.OpenProcess(0x1000|0x100000,False,pid);assert handle,ctypes.get_last_error()
    def times():
        values=[wintypes.FILETIME() for _ in range(4)]
        assert kernel.GetProcessTimes(handle,*map(ctypes.byref,values))
        def epoch(t):return ((t.dwHighDateTime<<32)|t.dwLowDateTime)/10000000-11644473600
        return [epoch(t) for t in values[:2]]
    try:
        birth,_=times();assert abs(birth-expected_birth)<1,('target creation identity mismatch',pid,birth,expected_birth)
        print(json.dumps(dict(observing_pid=pid,actual_birth_unix=birth,label=label,no_target_mutation=True)),flush=True)
        assert kernel.WaitForSingleObject(handle,0xffffffff)==0
        birth,end=times();code=wintypes.DWORD();assert kernel.GetExitCodeProcess(handle,ctypes.byref(code))
    finally:kernel.CloseHandle(handle)
    intervals=[]
    for p in (OUT/'fees').glob('*/receipt.json'):
        r=read(p)
        if r.get('outer_interval_complement'):continue
        if not all(k in r for k in ['start_unix','end_unix']):continue
        a=max(birth,r['start_unix']);b=min(end,r['end_unix'])
        if b>a:intervals.append((a,b,p.parent.name))
    intervals.sort();covered=[]
    for a,b,name in intervals:
        if covered and a<=covered[-1][1]:covered[-1][1]=max(covered[-1][1],b);covered[-1][2].append(name)
        else:covered.append([a,b,[name]])
    gaps=[];cursor=birth
    for a,b,names in covered:
        if a>cursor:gaps.append([cursor,a])
        cursor=max(cursor,b)
    if end>cursor:gaps.append([cursor,end])
    gap_seconds=sum(b-a for a,b in gaps);d=OUT/'fees'/label;assert not d.exists();d.mkdir()
    write(d/'launch.json',dict(UTC=utc(),kind='management',target_pid=pid,actual_parent_birth_unix=birth,actual_parent_exit_unix=end,command=['read-only process handle observer'],measurement='actual loop lifetime minus union of already-metered child fee intervals'))
    write(d/'receipt.json',dict(exit_code=int(code.value),outer_seconds=gap_seconds,outer_interval_complement=True,actual_parent_birth_unix=birth,actual_parent_exit_unix=end,covered_fee_intervals=covered,uncovered_intervals=gaps,nested_seconds_added=False,observer_wait_not_charged_again=True))
    print(json.dumps(dict(label=label,parent_exit=int(code.value),management_gap_seconds=gap_seconds,child_intervals=len(intervals),budget=budget())),flush=True)
if __name__=='__main__':observe(int(sys.argv[1]),sys.argv[2],float(sys.argv[3]))
