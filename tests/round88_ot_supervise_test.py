"""Whole-process deadline and manifest identity tests without a solver."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import round88_ot_supervise as supervisor


class FakeProcess:
    def __init__(self, command, timed_out=False):
        self.command = command
        self.timed_out = timed_out
        self.returncode = None
        self.communicate_timeouts = []
        self.terminated = False

    def communicate(self, timeout):
        self.communicate_timeouts.append(timeout)
        if self.timed_out and not self.terminated:
            raise subprocess.TimeoutExpired(self.command, timeout)
        if not self.timed_out:
            out = Path(self.command[self.command.index("--out-dir") + 1])
            out.mkdir()
            manifest = Path(self.command[self.command.index("--manifest") + 1])
            (out / "result.json").write_text(json.dumps({
                "manifest_sha256": supervisor.file_sha(manifest)}), encoding="utf-8")
            self.returncode = 0
        return "stdout", "stderr"

    def terminate(self):
        self.terminated = True
        self.returncode = -15

    def kill(self):
        self.returncode = -9


class SupervisionTests(unittest.TestCase):
    def run_fake(self, timed_out):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "manifest.json"
            manifest.write_text("{}", encoding="utf-8")
            out = root / "run"
            created = []
            def popen(command, **_):
                process = FakeProcess(command, timed_out)
                created.append(process)
                return process
            clocks = iter([0.0, 0.5, 2.1 if timed_out else 1.0, 1.0])
            with mock.patch.object(sys, "argv", ["supervise", "--manifest", str(manifest),
                                                 "--out-dir", str(out),
                                                 "--whole-process-limit-seconds", "2"]), \
                 mock.patch.object(supervisor.subprocess, "Popen", side_effect=popen), \
                 mock.patch.object(supervisor.time, "perf_counter", side_effect=lambda: next(clocks)), \
                 redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                code = supervisor.main()
            return code, json.loads((out / "supervision.json").read_text()), created[0]

    def test_subprocess_gets_only_remaining_whole_process_time(self):
        code, receipt, process = self.run_fake(False)
        self.assertEqual(code, 0)
        self.assertEqual(process.communicate_timeouts, [1.5])
        self.assertEqual(receipt["status"], "diagnostic_process_finished")
        self.assertTrue(receipt["manifest_identity_consistent"])

    def test_whole_process_timeout_is_unknown_and_terminated(self):
        code, receipt, process = self.run_fake(True)
        self.assertEqual(code, 124)
        self.assertTrue(process.terminated)
        self.assertEqual(receipt["status"], "unknown_whole_process_deadline")


if __name__ == "__main__":
    unittest.main()
