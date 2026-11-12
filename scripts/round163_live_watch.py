"""Metadata-only OS binding monitor; never hashes or controls a solver."""
from pathlib import Path
import ctypes,json,os,time
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/unified_exact_round163'
K=ctypes.WinDLL('kernel32',use_last_error=True)
P=ctypes.WinDLL('psapi',use_last_error=True)
K.GetCurrentProcess.restype=ctypes.c_void_p
K.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t]
# Monitoring is outside the production CPU (mask4), uniformly for the panel.
assert K.SetProcessAffinityMask(K.GetCurrentProcess(),1)
K.OpenProcess.argtypes=[ctypes.c_ulong,ctypes.c_int,ctypes.c_ulong];K.OpenProcess.restype=ctypes.c_void_p
K.CloseHandle.argtypes=[ctypes.c_void_p]
K.GetProcessTimes.argtypes=[ctypes.c_void_p,*([ctypes.c_void_p]*4)]
K.GetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p]
P.EnumProcessModulesEx.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_ulong,ctypes.c_void_p,ctypes.c_ulong]
P.GetModuleFileNameExW.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_wchar_p,ctypes.c_ulong]

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,v):
    t=p.with_name(p.name+'.watchtmp');t.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8');os.replace(t,p)
def binding(origin):
    handle=K.OpenProcess(0x1000|0x10,False,origin['pid'])
    if not handle:return None
    try:
        created,exited,kernel,user=[ctypes.c_uint64() for _ in range(4)]
        if not K.GetProcessTimes(handle,*[ctypes.byref(v) for v in (created,exited,kernel,user)]):return None
        birth=created.value/10000000.-11644473600.
        assert abs(birth-origin['actual_creation_unix'])<.001
        process,system=ctypes.c_size_t(),ctypes.c_size_t()
        assert K.GetProcessAffinityMask(handle,ctypes.byref(process),ctypes.byref(system)) and process.value==4
        array=(ctypes.c_void_p*2048)();needed=ctypes.c_ulong()
        if not P.EnumProcessModulesEx(handle,array,ctypes.sizeof(array),ctypes.byref(needed),3):return None
        paths=[]
        for module in array[:needed.value//ctypes.sizeof(ctypes.c_void_p)]:
            name=ctypes.create_unicode_buffer(32768)
            if P.GetModuleFileNameExW(handle,module,name,len(name)):paths.append(name.value)
        dll=[p for p in paths if Path(p).name.lower()=='gurobi130.dll']
        if not dll:return None
        assert len(dll)==1
        return dict(UTC=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),PID=origin['pid'],CreationUnix=birth,
            PE=paths[0],DLL=[dict(ModuleName='gurobi130.dll',FileName=dll[0])],PrelaunchSHA=origin['PE_SHA'],
            ProcessorAffinity=process.value,HashingDuringTimedSolve=False,CommercialDLLPublished=False,
            observation='live OS module enumeration; observer affinity1, production affinity4')
    finally:K.CloseHandle(handle)

def main():
    matrix=read(OUT/'matrix_frozen.json');start=time.time();seen=set()
    while time.time()-start<72000:
        if (OUT/'panel_complete.json').exists():break
        try:
            active=read(OUT/'active_position.json');g=matrix['groups'][active['position']-1]
            path=OUT/g['group']/'runtime_os_binding.json'
            if path.exists():seen.add(g['position'])
            else:
                origin=Path(g['launch']['destination'])/'child_process_origin.json'
                if origin.exists():
                    value=binding(read(origin))
                    if value:
                        assert Path(value['PE'])==Path(g['launch']['command'][0])
                        write(path,value);seen.add(g['position']);print(json.dumps(dict(bound=g['position'],method=g['launch']['R163_method'])),flush=True)
        except FileNotFoundError:pass
        time.sleep(.25)
    write(OUT/'live_watch_closeout.json',dict(ended_unix=time.time(),started_unix=start,bound_positions=sorted(seen),
        observer_affinity=1,production_affinity=4,metadata_only=True,Optimize=0))
if __name__=='__main__':main()
