"""Observe runtime modules and meter a separate read-only audit for each return."""

import argparse
import ctypes
import os
from pathlib import Path
import subprocess
import sys
import time

from round171_common import CAP, DLL, DLL_SHA, OUT, PE, PE_SHA, ROOT, TEMP, bind, read, utc, write


def live_modules(pid):
    """Check loaded paths on the actual producer without running solver code."""
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    open_process = kernel.OpenProcess
    open_process.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
    open_process.restype = ctypes.c_void_p
    query_module = kernel.K32GetModuleFileNameExW
    query_module.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_ulong]
    query_module.restype = ctypes.c_ulong
    list_modules = kernel.K32EnumProcessModules
    list_modules.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong, ctypes.POINTER(ctypes.c_ulong)]
    list_modules.restype = ctypes.c_int
    close_handle = kernel.CloseHandle
    close_handle.argtypes = [ctypes.c_void_p]
    handle = open_process(0x410, False, pid)  # PROCESS_QUERY_INFORMATION | PROCESS_VM_READ
    if not handle:
        return []
    try:
        modules = (ctypes.c_void_p * 512)()
        needed = ctypes.c_ulong()
        if not list_modules(handle, modules, ctypes.sizeof(modules), ctypes.byref(needed)):
            return []
        if needed.value > ctypes.sizeof(modules):
            return []
        paths = []
        for module in modules[:needed.value // ctypes.sizeof(ctypes.c_void_p)]:
            buffer = ctypes.create_unicode_buffer(32768)
            if query_module(handle, module, buffer, len(buffer)):
                paths.append(Path(buffer.value))
        return paths
    finally:
        close_handle(handle)


def observe_runtime():
    active_path = OUT / "active_position.json"
    if not active_path.is_file():
        return
    active = read(active_path)
    path = OUT / "runtime_readbacks" / f"{active['position']:02d}.json"
    if path.is_file() or time.time() > active["deadline_epoch"]:
        return
    executable, library = Path(PE).resolve(), Path(DLL).resolve()
    modules = [module.resolve() for module in live_modules(active["pid"])]
    actual_library = next((module for module in modules if module.name.lower() == "gurobi130.dll"), None)
    if executable in modules and actual_library:
        pe_identity, dll_identity = bind(executable), bind(actual_library)
        assert actual_library == library and pe_identity["SHA256"] == PE_SHA and dll_identity["SHA256"] == DLL_SHA
        write(path, dict(
            UTC=utc(), position=active["position"], role=active["role"], arm=active["arm"],
            pid=active["pid"], process_start_epoch=active["started_epoch"], Native_Seed=active["Native_Seed"],
            affinity_mask=active["affinity_mask"], affinity_set=active["affinity_set"],
            PE=pe_identity, DLL=dll_identity, verified_live_module=True,
        ))


def measure_audit(position):
    n = position["position"]
    directory = Path(position["directory"])
    audit_path = OUT / "review" / f"complete_audit_{n:02d}.json"
    if audit_path.is_file():
        return True
    completion_path = directory / "completion.json"
    completion = read(completion_path)
    assert completion["rc"] == 0 and completion["process_outer_seconds"] <= CAP, "Producer needs diagnosis"
    records = OUT / "review" / "audit_process_costs.json"
    attempts = read(records) if records.is_file() else []
    number = 1 + sum(row["position"] == n for row in attempts)
    folder = OUT / "review" / "attempt_logs"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"audit_{n:02d}_attempt_{number:02d}.log"
    command = [sys.executable, "-B", str(ROOT / "scripts/round171_audit.py"), str(n)]
    start = time.time()
    tick = time.perf_counter()
    with path.open("xb") as handle:
        p = subprocess.run(command, check=False, cwd=ROOT, stdout=handle, stderr=subprocess.STDOUT,
                           env={**os.environ, "TEMP": str(TEMP), "TMP": str(TEMP)})
    elapsed = time.perf_counter() - tick
    attempts.append(dict(
        position=n, attempt=number, start_epoch=start, end_epoch=time.time(), UTC=utc(), rc=p.returncode,
        command=command, audit_process_outer_seconds=elapsed, Optimize=0, log=bind(path),
        reader=bind(ROOT / "scripts/round171_audit.py"),
        audit=bind(audit_path) if p.returncode == 0 else None,
    ))
    write(records, attempts)
    if p.returncode:
        print(f"AUDIT FAILED position={n} attempt={number} log={path}", flush=True)
    else:
        print(path.read_text(encoding="utf-8").strip(), flush=True)
    return p.returncode == 0


def watch():
    positions = read(OUT / "matrix_frozen.json")["positions"]
    revisited = set()
    has_seen_producer = (OUT / "producer.lock").exists()
    while True:
        observe_runtime()
        for position in positions:
            number = position["position"]
            directory = Path(position["directory"])
            if number in revisited or not (directory / "completion.json").is_file():
                continue
            completion = read(directory / "completion.json")
            if completion["rc"] == 0 and completion["process_outer_seconds"] <= CAP:
                measure_audit(position)
            revisited.add(number)
        if (OUT / "panel_complete.json").is_file() and len(revisited) == len(positions):
            break
        active = (OUT / "producer.lock").exists()
        if has_seen_producer and not active and not (OUT / "panel_complete.json").is_file():
            raise RuntimeError("Producer supervision stopped. Preserve all returned data and inspect the receipts.")
        has_seen_producer |= active
        time.sleep(2)
    audit_count = sum((OUT / "review" / f"complete_audit_{n:02d}.json").is_file() for n in revisited)
    print(f"AUDITED {audit_count}/{len(positions)} producer positions", flush=True)
    return audit_count == len(positions)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("positions", type=int, nargs="*")
    args = parser.parse_args()
    matrix = read(OUT / "matrix_frozen.json")
    if args.positions:
        results = [measure_audit(matrix["positions"][n - 1]) for n in args.positions]
        sys.exit(0 if all(results) else 1)
    sys.exit(0 if watch() else 1)
