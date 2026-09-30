"""Finish exactly the already registered arms 2..4; never restart an arm."""
import argparse
import ctypes as ct
import json
import subprocess
import time
from pathlib import Path
import round97_campaign as campaign
import round97_vector_audit as vectors
from round97_campaign import ROOT, OUT, read, write, sha

CAMP = OUT/'development01'
QUEUE = CAMP/'continuation_queue'


def record(phase, **extra):
    row = dict(phase=phase, unix=time.time(), **extra)
    with (QUEUE/'events.jsonl').open('a') as f:
        f.write(json.dumps(row)+'\n')
        f.flush()
    write(QUEUE/'status.json', row)
    print(json.dumps(row), flush=True)


def wait_existing(pid):
    kernel = ct.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes = [ct.c_ulong, ct.c_int, ct.c_ulong]
    kernel.OpenProcess.restype = ct.c_void_p
    kernel.WaitForSingleObject.argtypes = [ct.c_void_p, ct.c_ulong]
    kernel.WaitForSingleObject.restype = ct.c_ulong
    kernel.GetExitCodeProcess.argtypes = [ct.c_void_p, ct.POINTER(ct.c_ulong)]
    kernel.CloseHandle.argtypes = [ct.c_void_p]
    handle = kernel.OpenProcess(0x100000 | 0x1000, False, pid)
    assert handle, ('expected live launcher missing; inspect before further work', pid, ct.get_last_error())
    try:
        raw = subprocess.check_output(['powershell.exe', '-NoProfile', '-Command',
            f'Get-CimInstance Win32_Process -Filter "ProcessId = {pid} OR ParentProcessId = {pid}" | '
            'Select-Object ProcessId,ParentProcessId,Name,CommandLine | ConvertTo-Json -Compress'], text=True)
        processes = json.loads(raw)
        if isinstance(processes, dict):
            processes = [processes]
        parent = next(p for p in processes if p['ProcessId'] == pid)
        assert parent['Name'].lower() == 'python.exe'
        assert parent['CommandLine'].endswith('scripts/round97_development.py run --number 2')
        children = [p for p in processes if p['ParentProcessId'] == pid and p['Name'] == 'ExactEBRP.exe']
        assert len(children) == 1 and str(CAMP/'raw/02_F5_FEEDBACK') in children[0]['CommandLine']
        write(QUEUE/'observed_existing_process.json', dict(parent=parent, child=children[0]))
        record('waiting_for_existing_arm2', launcher_pid=pid, solver_pid=children[0]['ProcessId'])
        while True:
            status = kernel.WaitForSingleObject(handle, 60000)
            if status == 0:
                break
            assert status == 258, ('process wait failed; never infer completion', status, ct.get_last_error())
        code = ct.c_ulong()
        assert kernel.GetExitCodeProcess(handle, ct.byref(code))
        assert code.value == 0, ('existing launcher failed; no further launches', code.value)
    finally:
        kernel.CloseHandle(handle)


def checked_prefix(number):
    rows = [json.loads(s) for s in (CAMP/'summary.jsonl').read_text().splitlines()]
    assert len(rows) == number and all(r['audit_passed'] for r in rows)
    assert rows[-1]['number'] == number
    return rows[-1]


def main(pid):
    QUEUE.mkdir(exist_ok=False)
    identity = read(CAMP/'identity.json')
    assert [r['arm'] for r in identity['launches']] == ['SHADOW', 'FEEDBACK', 'OFF', 'P-GRB']
    assert identity['source_hashes'] == campaign.bindings()
    assert len([json.loads(s) for s in (CAMP/'summary.jsonl').read_text().splitlines()]) == 1
    write(QUEUE/'identity.json', dict(watched_launcher_pid=pid,
        inherited_batch_sha256=sha(CAMP/'identity.json'), queue_sha256=sha(__file__),
        vector_checker_sha256=sha(vectors.__file__), new_launch_numbers=[3, 4],
        maximum_new_starts=2, maximum_new_process_seconds=7200,
        policy='Wait for exact live arm2 launcher; require successful full prefix; audit retained vectors only while idle; run only registered arms3/4; stop on any failure; no restart or extension.'))
    try:
        wait_existing(pid)
        checked_prefix(2)
        campaign.ext.ensure_idle()
        record('auditing_arm2_vectors')
        vectors.check(str(CAMP/'raw/02_F5_FEEDBACK'), 'development01_F5_feedback_vectors')
        for number in [3, 4]:
            assert sha(CAMP/'identity.json') == read(QUEUE/'identity.json')['inherited_batch_sha256']
            record('launching_registered_arm', number=number, arm=identity['launches'][number-1]['arm'])
            campaign.run('development01', number)
            row = checked_prefix(number)
            record('registered_arm_audited', number=number, endpoint=row['endpoint'])
            if number == 3:
                campaign.ext.ensure_idle()
                record('auditing_arm3_vectors')
                vectors.check(str(CAMP/'raw/03_F5_OFF'), 'development01_F5_off_vectors')
        record('complete', completed_registered_arms=[1, 2, 3, 4])
    except BaseException as error:
        record('stopped_failure_no_restart', error=repr(error))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--watch-pid', type=int, required=True)
    args = parser.parse_args()
    main(args.watch_pid)
