"""Pure-rational independent oracle for the Round88 OT closure row builder.

No solver import, LP read, model creation, or Optimize is needed.
"""

from __future__ import annotations

from fractions import Fraction as F
import itertools
import json
import os
import random
import subprocess
import sys
from pathlib import Path
import tempfile
import time
import types
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from round88_ot_closure import (_WindowsJob, _scan, _wait_with_deadline,
                                fast_pair_cut, model_row_signature,
                                row_signature, supervise_prepare)
from round88_ot_math import h_name, q_name, ratio, row_value, state_name


def sign(value: F, tie: int) -> int:
    return -1 if value < 0 else 1 if value > 0 else tie


def naive(kind, i, j, supports, targets, a, b, values, tie=1):
    """Deliberately rescan all states per interval and update every coefficient."""
    levels = sorted({F(y, targets[k]) for k in (i, j) for y in supports[k]})
    coeff = {h_name(i, j): b-a if kind == "B2" else F(1)}
    signs = []
    intervals = []
    a_values = []
    b_values = []
    exact = {name: F.from_float(value) for name, value in values.items()}
    for lo, hi in zip(levels, levels[1:]):
        delta = hi-lo
        aa = sum((exact[state_name(i, y)] for y in supports[i]
                  if ratio(y, targets[i]) <= lo), F(0)) - sum(
            (exact[state_name(j, y)] for y in supports[j]
             if ratio(y, targets[j]) <= lo), F(0))
        bb = sum((exact[q_name(i, y)] for y in supports[i]
                  if ratio(y, targets[i]) <= lo), F(0)) - sum(
            (exact[q_name(j, y)] for y in supports[j]
             if ratio(y, targets[j]) <= lo), F(0))
        alpha, beta = ((sign(aa, tie), 0) if kind == "B1" else
                       (sign(b*aa-bb, tie), sign(bb-a*aa, tie)))
        s_factor = F(alpha) if kind == "B1" else b*alpha-a*beta
        q_factor = F(0) if kind == "B1" else F(beta-alpha)
        for k, direction in ((i, 1), (j, -1)):
            for y in supports[k]:
                if ratio(y, targets[k]) <= lo:
                    sn = state_name(k, y)
                    qn = q_name(k, y)
                    coeff[sn] = coeff.get(sn, F(0))-delta*s_factor*direction
                    coeff[qn] = coeff.get(qn, F(0))-delta*q_factor*direction
        signs.append((alpha, beta))
        intervals.append(delta)
        a_values.append(float(aa))
        b_values.append(float(bb))
    return ({key: value for key, value in coeff.items() if value},
            tuple(signs), tuple(intervals), tuple(a_values), tuple(b_values))


def exhaustive_maximum(kind, i, j, supports, targets, a, b, values):
    """Enumerate the independent extreme row family on micro supports."""
    levels = sorted({ratio(y, targets[k]) for k in (i, j) for y in supports[k]})
    point = {name: F.from_float(value) for name, value in values.items()}
    terms = []
    for lo, hi in zip(levels, levels[1:]):
        aa = sum((point[state_name(i, y)] for y in supports[i]
                  if ratio(y, targets[i]) <= lo), F(0)) - sum(
            (point[state_name(j, y)] for y in supports[j]
             if ratio(y, targets[j]) <= lo), F(0))
        bb = sum((point[q_name(i, y)] for y in supports[i]
                  if ratio(y, targets[i]) <= lo), F(0)) - sum(
            (point[q_name(j, y)] for y in supports[j]
             if ratio(y, targets[j]) <= lo), F(0))
        terms.append((hi-lo, aa, bb))
    h = point[h_name(i, j)]
    options = ([(-1, 0), (1, 0)] if kind == "B1" else
               list(itertools.product((-1, 1), repeat=2)))
    rhs_max = max((sum((delta*(alpha*aa if kind == "B1" else
                                 (b*alpha-a*beta)*aa+(beta-alpha)*bb)
                        for (delta, aa, bb), (alpha, beta) in zip(terms, signs)), F(0))
                   for signs in itertools.product(options, repeat=len(terms))), default=F(0))
    return rhs_max-(h if kind == "B1" else (b-a)*h)


def random_composition(rng, total, count):
    cuts = sorted([0, total] + [rng.randrange(total+1) for _ in range(count-1)])
    return [cuts[k+1]-cuts[k] for k in range(count)]


def allocate(rng, capacity, amount):
    answer = [0]*len(capacity)
    remaining = amount
    for k in rng.sample([i for i, n in enumerate(capacity) for _ in range(n)], amount):
        # Duplicate sampled indices represent distinct unit tokens.
        answer[k] += 1
        remaining -= 1
    assert remaining == 0 and all(x <= y for x, y in zip(answer, capacity))
    return answer


class FastPairExactReferenceTests(unittest.TestCase):
    def check_case(self, supports, targets, a, b, values, tie=1):
        point = {name: F.from_float(value) for name, value in values.items()}
        for kind in (("B1", "B2") if a < b else ("B1",)):
            fast = fast_pair_cut(kind, 1, 2, supports, targets, a, b, values, tie)
            coeff, signs, intervals, a_values, b_values = naive(
                kind, 1, 2, supports, targets, a, b, values, tie)
            self.assertEqual(fast.coeff, coeff)
            self.assertEqual(fast.signs, signs)
            self.assertEqual(fast.intervals, intervals)
            self.assertEqual(fast.a_values, a_values)
            self.assertEqual(fast.b_values, b_values)
            self.assertEqual(row_value(fast.coeff, point), row_value(coeff, point))
            if tie in (-1, 1):
                self.assertEqual(-row_value(fast.coeff, point),
                                 exhaustive_maximum(kind, 1, 2, supports,
                                                    targets, a, b, values))
            self.assertNotEqual(row_signature(fast, supports, targets, a, b, "a"*64),
                                row_signature(fast, supports, targets, a, b, "b"*64))

    def test_heterogeneous_targets_shared_ratios_and_zero_mass(self):
        supports = {1: [0, 1, 2, 3], 2: [0, 1, 2, 4]}
        targets = {1: 3, 2: 4}
        values = {h_name(1, 2): 0.0}
        s1 = [0.0, 0.25, 0.25, 0.5]
        s2 = [0.125, 0.375, 0.0, 0.5]
        q1 = [0.0, 0.125, 0.125, 0.25]
        q2 = [0.0, 0.25, 0.0, 0.25]
        for k, s, q in ((1, s1, q1), (2, s2, q2)):
            for y, sv, qv in zip(supports[k], s, q):
                values[state_name(k, y)] = sv
                values[q_name(k, y)] = qv
        for tie in (-1, 0, 1):
            self.check_case(supports, targets, F(0), F(1), values, tie)

    def test_zero_ties_equal_domain_and_narrow_positive_width(self):
        supports = {1: [0, 1, 2], 2: [0, 1, 2]}
        targets = {1: 2, 2: 2}
        values = {h_name(1, 2): 0.0}
        for k in supports:
            for y, s in zip(supports[k], [0.25, 0.5, 0.25]):
                values[state_name(k, y)] = s
                values[q_name(k, y)] = 0.5*s
        for tie in (-1, 0, 1):
            self.check_case(supports, targets, F(1, 2), F(1, 2), values, tie)
            self.check_case(supports, targets, F(1, 4), F(1, 4)+F(1, 2**20), values, tie)
        with self.assertRaises(ValueError):
            fast_pair_cut("B2", 1, 2, supports, targets, F(1, 2), F(1, 2), values)

    def test_family_provenance_and_identical_model_row_dedup(self):
        supports = {1: [0, 1], 2: [0, 1]}
        targets = {1: 1, 2: 1}
        values = {h_name(1, 2): 0.0}
        for k, masses in ((1, [0.75, 0.25]), (2, [0.25, 0.75])):
            for y, mass in zip(supports[k], masses):
                values[state_name(k, y)] = mass
                values[q_name(k, y)] = mass/2
        first = fast_pair_cut("B1", 1, 2, supports, targets, F(0), F(1), values)
        second = fast_pair_cut("B2", 1, 2, supports, targets, F(0), F(1), values)
        self.assertEqual(first.coeff, second.coeff)
        self.assertNotEqual(row_signature(first, supports, targets, F(0), F(1), "a"*64),
                            row_signature(second, supports, targets, F(0), F(1), "a"*64))
        self.assertEqual(model_row_signature(first, supports, targets, F(0), F(1), "a"*64),
                         model_row_signature(second, supports, targets, F(0), F(1), "a"*64))

    def test_random_feasible_endpoint_couplings(self):
        rng = random.Random(20260927)
        supports = {1: [0, 2, 4], 2: [0, 3, 5]}
        targets = {1: 4, 2: 5}
        a, b = F(1, 4), F(3, 4)
        for _ in range(64):
            values = {h_name(1, 2): rng.randrange(0, 17)/16}
            for k in supports:
                masses = random_composition(rng, 16, 3)
                upper = allocate(rng, masses, 8)
                self.assertEqual(sum(masses), 16)
                self.assertEqual(sum(upper), 8)
                for y, mass, up in zip(supports[k], masses, upper):
                    s = F(mass, 16)
                    q = a*s+(b-a)*F(up, 16)
                    values[state_name(k, y)] = float(s)
                    values[q_name(k, y)] = float(q)
            self.check_case(supports, targets, a, b, values)


class ClosureStateTests(unittest.TestCase):
    def test_all_pair_scan_terminal_states_without_solver(self):
        supports = {1: [0, 1], 2: [0, 1]}
        targets = {1: 1, 2: 1}
        values = {h_name(1, 2): 0.0}
        for k, masses in ((1, [1.0, 0.0]), (2, [0.0, 1.0])):
            for y, mass in zip(supports[k], masses):
                values[state_name(k, y)] = mass
                values[q_name(k, y)] = 0.5*mass
        fake = types.ModuleType("round88_ot_diagnostic")
        fake.reliable = lambda coeff, scale, violation, point, residual: (
            violation > 1e-6, "selected" if violation > 1e-6 else
            "violation_below_numerical_margin", 1e-6)
        with tempfile.TemporaryDirectory() as folder, mock.patch.dict(
                sys.modules, {"round88_ot_diagnostic": fake}):
            root = Path(folder)
            first = root / "first"
            first.mkdir()
            added = _scan(values, supports, targets, F(0), F(1), "B1", "a"*64,
                          0.0, set(), first)
            self.assertEqual(added["status"], "add_all_reliable_new_rows")
            self.assertEqual(len(added["new_rows"]), 1)
            self.assertEqual(added["candidate_count"], 1)
            existing = root / "existing"
            existing.mkdir()
            old = _scan(values, supports, targets, F(0), F(1), "B1", "a"*64,
                        0.0, {added["new_rows"][0][3]}, existing)
            self.assertEqual(old["status"], "existing_row_violation_or_numeric_rejection")
            self.assertEqual(old["existing_reliably_violated_count"], 1)
            tiny = root / "tiny"
            tiny.mkdir()
            values[h_name(1, 2)] = 1.0-1e-7
            borderline = _scan(values, supports, targets, F(0), F(1), "B1", "a"*64,
                               0.0, set(), tiny)
            self.assertEqual(borderline["status"], "no_reliable_new_row")
            closed = root / "closed"
            closed.mkdir()
            values[h_name(1, 2)] = 1.1
            no_gap = _scan(values, supports, targets, F(0), F(1), "B1", "a"*64,
                           0.0, set(), closed)
            self.assertEqual(no_gap["status"], "complete_scan_no_observed_violation")

    def test_failed_shared_preparation_keeps_external_receipt(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder) / "new_preparation"
            failed = subprocess.CompletedProcess(args=["fake"], returncode=7,
                                                 stdout="", stderr="synthetic failure")
            with mock.patch("round88_ot_closure.subprocess.run", return_value=failed):
                self.assertEqual(supervise_prepare(out), 7)
            receipt = __import__("json").loads(
                (out / "preparation_supervision.json").read_text(encoding="utf-8"))
            self.assertEqual(receipt["status"], "preparation_failed")
            self.assertEqual(receipt["returncode"], 7)
            self.assertGreaterEqual(receipt["external_launch_to_exit_wall_seconds"], 0)


@unittest.skipUnless(os.environ.get("ROUND88_OT_CLOSURE_TOY_OPTIMIZE") == "1",
                     "controlled toy Optimize requires separate qualification slot")
class GurobiToyIntegrationTests(unittest.TestCase):
    def test_hand_calculated_ot_row_changes_lp_bound_from_zero_to_one(self):
        import gurobipy as gp
        from gurobipy import GRB
        from round88_ot_diagnostic import add_cut, reliable

        out = Path(os.environ["ROUND88_OT_CLOSURE_TOY_OUT_DIR"])
        out.mkdir(parents=True, exist_ok=False)
        model = gp.Model("round88_ot_closure_toy")
        model.Params.Threads = 1
        model.Params.Seed = 0
        model.Params.Presolve = -1
        model.Params.FeasibilityTol = 1e-6
        model.Params.OptimalityTol = 1e-6
        model.Params.LogToConsole = 0
        model.Params.LogFile = str(out / "gurobi.log")
        model.Params.OutputFlag = 1
        values = {}
        for station, masses in ((1, [1.0, 0.0]), (2, [0.0, 1.0])):
            for y, mass in enumerate(masses):
                model.addVar(lb=mass, ub=mass, name=state_name(station, y))
                model.addVar(lb=0.5*mass, ub=0.5*mass, name=q_name(station, y))
                values[state_name(station, y)] = mass
                values[q_name(station, y)] = 0.5*mass
        h = model.addVar(lb=0.0, name=h_name(1, 2))
        model.setObjective(h, GRB.MINIMIZE)
        model.update()
        model.write(str(out / "toy_original.lp"))
        model.optimize()  # toy call 1: h=0 from its sole lower bound
        self.assertEqual(model.Status, GRB.OPTIMAL)
        self.assertAlmostEqual(model.ObjVal, 0.0, places=9)
        values[h_name(1, 2)] = h.X
        supports = {1: [0, 1], 2: [0, 1]}
        targets = {1: 1, 2: 1}
        cut = fast_pair_cut("B1", 1, 2, supports, targets, F(0), F(1), values)
        self.assertEqual(-row_value(cut.coeff,
                                    {k: F.from_float(v) for k, v in values.items()}), F(1))
        accepted, reason, margin = reliable(cut.coeff, F(1), 1.0, values, 0.0)
        self.assertTrue(accepted)
        self.assertEqual(reason, "selected")
        self.assertEqual(margin, 1e-6)
        add_cut(model, cut.coeff, "toy_ot_b1")
        model.update()
        model.write(str(out / "toy_augmented.lp"))
        model.optimize()  # toy call 2: independent hand result h>=|0-1|=1
        self.assertEqual(model.Status, GRB.OPTIMAL)
        self.assertAlmostEqual(model.ObjVal, 1.0, places=9)
        self.assertAlmostEqual(h.X, 1.0, places=9)
        (out / "toy_result.json").write_text(json.dumps({
            "toy_optimize_calls": 2, "original_objective": 0.0,
            "augmented_objective": model.ObjVal,
            "hand_expected_augmented_objective": 1.0,
            "primal_h": h.X, "row_exact": {k: str(v) for k, v in cut.coeff.items()},
            "original_cut_violation": 1.0, "reliability_margin": margin,
            "violation_over_margin": 1.0/margin,
            "gurobi_version": gp.gurobi.version()}, indent=2) + "\n",
            encoding="utf-8")


@unittest.skipUnless(os.name == "nt", "Win32 Job Object qualification")
class Win32ProcessTreeTests(unittest.TestCase):
    def test_job_close_terminates_child_and_descendant(self):
        """A tiny Python grandchild stands in for a solver process tree."""
        with tempfile.TemporaryDirectory() as folder:
            pid_file = Path(folder) / "grandchild.pid"
            ready_file = Path(folder) / "ready.flag"
            program = """
import pathlib
import subprocess
import sys
import time
ready = pathlib.Path(sys.argv[2])
deadline = time.monotonic() + 5
while not ready.exists() and time.monotonic() < deadline:
    time.sleep(0.01)
if not ready.exists():
    raise RuntimeError('job assignment handshake failed')
p = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])
pathlib.Path(sys.argv[1]).write_text(str(p.pid))
time.sleep(60)
"""
            job = _WindowsJob()
            child = subprocess.Popen(
                [sys.executable, "-c", program, str(pid_file), str(ready_file)],
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            grandchild_pid = None
            grandchild_alive = False
            try:
                job.assign(child)
                ready_file.write_text("assigned", encoding="ascii")
                until = time.monotonic()+5
                while not pid_file.is_file() and time.monotonic() < until:
                    time.sleep(0.02)
                self.assertTrue(pid_file.is_file(), "grandchild never started")
                grandchild_pid = int(pid_file.read_text())
                _, _, timed_out = _wait_with_deadline(child, job, 0.2)
                self.assertTrue(timed_out)
                child.wait(timeout=5)
                api = __import__("ctypes").windll.kernel32
                api.OpenProcess.argtypes = (__import__("ctypes").c_uint,
                                            __import__("ctypes").c_int,
                                            __import__("ctypes").c_uint)
                api.OpenProcess.restype = __import__("ctypes").c_void_p
                api.GetExitCodeProcess.argtypes = (__import__("ctypes").c_void_p,
                                                  __import__("ctypes").c_void_p)
                api.CloseHandle.argtypes = (__import__("ctypes").c_void_p,)
                handle = api.OpenProcess(0x1000, 0, grandchild_pid)
                if handle:
                    code = __import__("ctypes").c_ulong()
                    try:
                        self.assertTrue(api.GetExitCodeProcess(handle,
                                                               __import__("ctypes").byref(code)))
                        grandchild_alive = code.value == 259
                        self.assertNotEqual(code.value, 259, "grandchild survived job close")
                    finally:
                        api.CloseHandle(handle)
            finally:
                job.close()
                if child.poll() is None:
                    subprocess.run(["taskkill", "/PID", str(child.pid), "/T", "/F"],
                                   capture_output=True, check=False)
                    child.wait(timeout=5)
                if grandchild_pid is not None and grandchild_alive:
                    subprocess.run(["taskkill", "/PID", str(grandchild_pid), "/T", "/F"],
                                   capture_output=True, check=False)


if __name__ == "__main__":
    unittest.main()
