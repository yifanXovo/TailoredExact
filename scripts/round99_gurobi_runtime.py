"""Bind Python diagnostic readers to the exact production Gurobi DLL."""
import ctypes,hashlib
from pathlib import Path
PRODUCTION=Path('D:/gurobi1302/win64/bin/gurobi130.dll')
# Dependency resolution reuses an already loaded DLL with this module name.
_production_runtime=ctypes.WinDLL(str(PRODUCTION),use_last_error=True)
import gurobipy as gp
def binding():
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.GetModuleHandleW.argtypes=[ctypes.c_wchar_p];kernel.GetModuleHandleW.restype=ctypes.c_void_p
    kernel.GetModuleFileNameW.argtypes=[ctypes.c_void_p,ctypes.c_wchar_p,ctypes.c_uint];kernel.GetModuleFileNameW.restype=ctypes.c_uint
    handle=kernel.GetModuleHandleW('gurobi130.dll');assert handle
    path=ctypes.create_unicode_buffer(32768);assert kernel.GetModuleFileNameW(handle,path,len(path))
    actual=Path(path.value);hash_file=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    kernel.GetCurrentProcess.restype=ctypes.c_void_p
    psapi=ctypes.WinDLL('psapi',use_last_error=True)
    psapi.EnumProcessModules.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_void_p),ctypes.c_uint,ctypes.POINTER(ctypes.c_uint)]
    psapi.EnumProcessModules.restype=ctypes.c_int
    modules=(ctypes.c_void_p*2048)();needed=ctypes.c_uint()
    assert psapi.EnumProcessModules(kernel.GetCurrentProcess(),modules,ctypes.sizeof(modules),ctypes.byref(needed))
    assert needed.value<=ctypes.sizeof(modules)
    engines=[]
    for module in list(modules)[:needed.value//ctypes.sizeof(ctypes.c_void_p)]:
        name=ctypes.create_unicode_buffer(32768)
        if kernel.GetModuleFileNameW(module,name,len(name)) and Path(name.value).name.lower()=='gurobi130.dll':engines.append(name.value)
    assert len(engines)==1,('multiple engine copies loaded',engines)
    record=dict(path=str(actual),sha256=hash_file(actual),production_sha256=hash_file(PRODUCTION),loaded_engine_modules=engines)
    assert record['sha256']==record['production_sha256'],record
    return record
