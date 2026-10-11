"""Arm-local isolation of the inherited optional display publication only."""
import ctypes, os, time, traceback
from pathlib import Path
from round88_a1_g3 import atomic_status as original_atomic_status

class OptionalPublisher:
    def __init__(self, launch, publish=original_atomic_status):
        self.launch=launch; self.publish=publish; self.disabled=False
        self.failure=None; self.attempts=0; self.skipped=0; self.successes=0

    def __call__(self, path, value):
        if self.disabled:
            self.skipped+=1
            return
        self.attempts+=1
        try:
            self.publish(path,value)
            self.successes+=1
        except OSError as exc:
            frame=traceback.extract_tb(exc.__traceback__)[-1]
            self.failure=dict(number=self.launch['number'],id=self.launch['id'],arm=self.launch['arm'],
                path=str(path),process_seconds=value['process_seconds'],failed_unix=time.time(),
                errno=exc.errno,winerror=getattr(exc,'winerror',None),error_type=type(exc).__name__,
                error=str(exc),filename=exc.filename,filename2=getattr(exc,'filename2',None),
                failure_stage='os.replace' if frame.line and 'os.replace' in frame.line else 'optional_filesystem_open_write_close',
                source_function=frame.name,source_line=frame.lineno)
            self.disabled=True

    def receipt(self):
        return dict(schema='round113_optional_publication_v1',number=self.launch['number'],
            id=self.launch['id'],arm=self.launch['arm'],disabled=self.disabled,
            failure_count=int(self.failure is not None),first_failure=self.failure,
            attempts=self.attempts,successes=self.successes,disabled_calls_skipped=self.skipped,
            retries=0,sleeps=0,authoritative_samples_and_protections_unchanged=True,
            next_arm_uses_new_state=True)

class DenyDeleteHandle:
    """Controlled Win32 READ/WRITE sharing, deliberately without DELETE sharing."""
    def __init__(self,path): self.path=Path(path); self.handle=None
    def __enter__(self):
        assert os.name=='nt' and self.path.is_file()
        self.api=ctypes.WinDLL('kernel32',use_last_error=True)
        self.api.CreateFileW.argtypes=[ctypes.c_wchar_p,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_void_p,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_void_p]
        self.api.CreateFileW.restype=ctypes.c_void_p; self.api.CloseHandle.argtypes=[ctypes.c_void_p]
        self.handle=self.api.CreateFileW(str(self.path.resolve()),0x80000000,0x1|0x2,None,3,0x80,None)
        if self.handle==ctypes.c_void_p(-1).value: raise ctypes.WinError(ctypes.get_last_error())
        return self
    def __exit__(self,*args):
        if self.handle is not None:
            assert self.api.CloseHandle(self.handle)
            self.handle=None
