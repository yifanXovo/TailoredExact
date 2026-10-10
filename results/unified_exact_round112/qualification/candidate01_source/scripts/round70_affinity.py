"""Uniform measurement affinity for an owned launcher and its children only."""
import ctypes, json, os, subprocess, sys, time
from contextlib import contextmanager
from ctypes import wintypes
from pathlib import Path

MASK=4  # Declared logical processor2; never chosen from performance results.

def kernel():
    assert os.name=='nt' and ctypes.sizeof(ctypes.c_void_p)==8
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.GetCurrentProcess.argtypes=[];k.GetCurrentProcess.restype=wintypes.HANDLE
    k.GetProcessAffinityMask.argtypes=[wintypes.HANDLE,ctypes.POINTER(ctypes.c_size_t),ctypes.POINTER(ctypes.c_size_t)]
    k.GetProcessAffinityMask.restype=wintypes.BOOL
    k.SetProcessAffinityMask.argtypes=[wintypes.HANDLE,ctypes.c_size_t]
    k.SetProcessAffinityMask.restype=wintypes.BOOL
    k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
    k.OpenProcess.restype=wintypes.HANDLE
    k.CloseHandle.argtypes=[wintypes.HANDLE];k.CloseHandle.restype=wintypes.BOOL
    return k

def read_masks(pid=None):
    k=kernel()
    handle=k.GetCurrentProcess() if pid is None else k.OpenProcess(0x1000,False,pid)
    if not handle:raise ctypes.WinError(ctypes.get_last_error())
    try:
        process=ctypes.c_size_t();system=ctypes.c_size_t()
        if not k.GetProcessAffinityMask(handle,ctypes.byref(process),ctypes.byref(system)):
            raise ctypes.WinError(ctypes.get_last_error())
        return dict(process_mask=process.value,system_mask=system.value)
    finally:
        if pid is not None:
            if not k.CloseHandle(handle):raise ctypes.WinError(ctypes.get_last_error())

def _set_current(mask):
    k=kernel()
    if not k.SetProcessAffinityMask(k.GetCurrentProcess(),mask):
        raise ctypes.WinError(ctypes.get_last_error())
    observed=read_masks()
    assert observed['process_mask']==mask,'Own launcher affinity readback mismatch'
    return observed

@contextmanager
def inherited_core(mask=MASK):
    assert mask>0 and mask&(mask-1)==0,'A single predeclared logical CPU is required'
    before=read_masks()
    assert mask&before['process_mask']==mask and mask&before['system_mask']==mask
    effective=_set_current(mask)
    record=dict(launcher_pid=os.getpid(),before=before,effective=effective,
        selected_logical_processor=mask.bit_length()-1,explicit_set_target='own launcher only')
    try:yield record
    finally:
        restored=_set_current(before['process_mask'])
        assert restored==before,'Own launcher affinity restoration mismatch'

def qualify():
    # This standalone command imports the old read-only query solely to reuse
    # its qualified parser. It never calls that module's output-writing main.
    import round69_topology
    root=Path(__file__).resolve().parents[1];out=root/'results/unified_exact_round70'
    assert not (out/'active_run.lock').exists()
    destination=out/'affinity_qualification.json'
    assert not destination.exists(),'Do not overwrite a measurement qualification'
    topology=round69_topology.topology()
    core=next(c for c in topology['cores'] if 2 in c['logical_processors'])
    assert core['group']==0 and core['efficiency_class']==max(topology['efficiency_classes'])
    before=read_masks();started=time.perf_counter()
    child_code='import json,sys;sys.path.insert(0,'+repr(str(Path(__file__).parent))+');from round70_affinity import read_masks;print(json.dumps(read_masks()))'
    with inherited_core() as binding:
        child=subprocess.Popen([sys.executable,'-c',child_code],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        parent_observation=read_masks(child.pid)
        stdout,stderr=child.communicate()
        assert child.returncode==0,stderr.decode(errors='replace')
        child_observation=json.loads(stdout)
        assert parent_observation==child_observation==binding['effective']
    assert read_masks()==before
    record=dict(binding=binding,child_readback_from_parent=parent_observation,
        child_self_readback=child_observation,restored=read_masks(),
        wall_seconds=time.perf_counter()-started,optimizer_calls=0,
        changed_unrelated_processes=False,algorithm_parameters_changed=False,
        scope='One owned Python parent and inherited child, no BRP solver or performance run')
    destination.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    (out/'host_topology.json').write_text(json.dumps(topology,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(record,indent=2))

if __name__=='__main__':qualify()
