"""Bounded real Win32 Job/ready/descendant cleanup qualification.

This intentionally launches only Python sleepers, never the EBRP binary.
"""

from __future__ import annotations

import ctypes
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import round88_quantity_probe as probe


def alive(pid: int) -> bool:
    api = ctypes.windll.kernel32
    api.OpenProcess.argtypes = (ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32)
    api.OpenProcess.restype = ctypes.c_void_p
    api.GetExitCodeProcess.argtypes = (ctypes.c_void_p,
                                       ctypes.POINTER(ctypes.c_uint32))
    api.GetExitCodeProcess.restype = ctypes.c_int
    api.CloseHandle.argtypes = (ctypes.c_void_p,)
    handle = api.OpenProcess(0x1000, False, pid)
    if not handle:
        return False
    try:
        exit_code = ctypes.c_uint32()
        if not api.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
            raise RuntimeError("GetExitCodeProcess failed")
        return exit_code.value == 259  # STILL_ACTIVE
    finally:
        api.CloseHandle(handle)


def child(marker: Path) -> None:
    marker.write_text(str(os.getpid()), encoding="ascii")
    time.sleep(30)


def parent(ready: Path, marker: Path) -> None:
    for _ in range(500):
        if ready.is_file():
            break
        time.sleep(0.01)
    else:
        os._exit(4)
    subprocess.Popen([sys.executable, __file__, "child", str(marker)],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(500):
        if marker.is_file():
            os._exit(0)
        time.sleep(0.01)
    os._exit(5)


def qualify() -> None:
    if os.name != "nt":
        raise RuntimeError("Win32 qualification requires Windows")
    with tempfile.TemporaryDirectory(prefix="r88_a2_job_") as folder:
        root = Path(folder)
        ready, marker = root / "ready", root / "child.pid"
        job = probe._WindowsJob()
        process = None
        child_pid = None
        try:
            process = subprocess.Popen(
                [sys.executable, __file__, "parent", str(ready), str(marker)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            job.assign(process)
            time.sleep(0.05)
            if marker.exists():
                raise AssertionError("descendant launched before ready flag")
            ready.write_text("job assigned\n", encoding="ascii")
            process.wait(timeout=8)
            if process.returncode != 0 or not marker.is_file():
                raise AssertionError("parent did not launch child and exit")
            child_pid = int(marker.read_text(encoding="ascii"))
            if not alive(child_pid):
                raise AssertionError("descendant not alive before Job close")
            job.close()
            for _ in range(200):
                if not alive(child_pid):
                    break
                time.sleep(0.01)
            else:
                raise AssertionError("descendant survived kill-on-close Job")
            print("PASS ready_gate parent_exited=0 descendant_terminated=1 pid=" +
                  str(child_pid))
        finally:
            job.close()
            if process is not None and process.poll() is None:
                probe._kill_process_tree(process, None)
            if child_pid is not None and alive(child_pid):
                subprocess.run(["taskkill", "/PID", str(child_pid), "/T", "/F"],
                               capture_output=True, check=False)
                raise AssertionError("cleanup needed for escaped descendant")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "parent":
        parent(Path(sys.argv[2]), Path(sys.argv[3]))
    elif len(sys.argv) > 1 and sys.argv[1] == "child":
        child(Path(sys.argv[2]))
    else:
        qualify()
