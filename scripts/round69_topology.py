"""Read Windows core topology only; never changes affinity or runs a solver."""
import ctypes,json,struct
from ctypes import wintypes
import round69_research as run

def topology():
    assert ctypes.sizeof(ctypes.c_void_p)==8,'This parser qualifies the current x64 host only'
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    query=kernel.GetLogicalProcessorInformationEx
    query.argtypes=[ctypes.c_int,ctypes.c_void_p,ctypes.POINTER(wintypes.DWORD)]
    query.restype=wintypes.BOOL
    length=wintypes.DWORD(0)
    assert not query(0,None,ctypes.byref(length)) and ctypes.get_last_error()==122
    data=ctypes.create_string_buffer(length.value)
    if not query(0,data,ctypes.byref(length)):raise ctypes.WinError(ctypes.get_last_error())
    raw=data.raw[:length.value];offset=0;cores=[]
    while offset<len(raw):
        relationship,size=struct.unpack_from('<II',raw,offset)
        assert relationship==0 and size>=48 and offset+size<=len(raw)
        flags,efficiency=struct.unpack_from('<BB',raw,offset+8)
        groups=struct.unpack_from('<H',raw,offset+30)[0]
        assert groups==1,'ProcessorCore must identify exactly one group on this host'
        mask,group=struct.unpack_from('<QH',raw,offset+32)
        logical=[bit for bit in range(64) if mask&(1<<bit)]
        assert bool(flags&1)==(len(logical)>1)
        cores.append(dict(core_record=len(cores),group=group,affinity_mask=mask,
            logical_processors=logical,SMT=bool(flags&1),efficiency_class=efficiency))
        offset+=size
    assert offset==len(raw)
    return dict(cores=cores,physical_core_count=len(cores),
        logical_processor_count=sum(len(c['logical_processors']) for c in cores),
        efficiency_classes=sorted({c['efficiency_class'] for c in cores}),
        optimizer_calls=0,affinity_changed=False,
        scope='Read-only Win32 topology for a prospective uniformly controlled measurement setup; not a diagnosis of where the prior run actually executed',
        source='https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-processor_relationship')

if __name__=='__main__':
    result=topology();run.write(run.OUT/'host_topology.json',result)
    print(json.dumps(result,indent=2))
