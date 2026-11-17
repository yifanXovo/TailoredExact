"""Round171 receipts and byte bindings for the frozen C++ campaign."""

from pathlib import Path
import hashlib
import subprocess
import time

from round170_common import (
    DLL, DLL_SHA, MEASURED, PE, PE_SHA, ROOT, WORK, bind, env, git, read, sha, utc, write,
)

BASE = "f14a054627f79dba61cd5ffa00d3280499826335"
MAIN = "b2b940c1e517a72e226ec60fc49ff19651737632"
BRANCH = "codex/round171-frozen-b-n50"
PR_BASE = "codex/round170-reweight-confirmation"
REL = Path("results/unified_exact_round171")
OUT = ROOT / REL
TEMP = WORK / "temp/round171"
RAW = WORK / "raw/round171"
MASTER = ROOT / "results/benchmark_tables/GI_TBC_vs_P_GRB_All_Tested_Instances.csv"
MASTER_BASE_SHA = "ef96de583ff382fa8a303b92f86d30e43b8f863f786117b6ce3241d13d4e5b0c"
MASTER_BASE_BYTES = 76_970
CAP = 1200
MARGIN = 6
SEED = 0
AFFINITY = 4
SCIENCE_CAP = 25_200
SCIENCE_START = 1794950675.0


def blob(commit, path):
    relative = path.relative_to(ROOT) if isinstance(path, Path) and path.is_absolute() else Path(path)
    return subprocess.check_output(["git", "show", f"{commit}:{relative.as_posix()}"], cwd=ROOT)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def require_committed(path, revision="HEAD"):
    assert path.read_bytes() == blob(revision, path), f"{path} differs from {revision}"


def clock():
    now = time.time()
    inactive_path = OUT / "work_interruption.json"
    gaps = read(inactive_path)["inactive_intervals"] if inactive_path.is_file() else []
    inactive = sum(gap["end_epoch"] - gap["start_epoch"] for gap in gaps)
    gross = now - SCIENCE_START
    return dict(
        UTC=utc(), start_epoch=SCIENCE_START, measured_epoch=now, science_cap_seconds=SCIENCE_CAP,
        gross_elapsed_seconds=gross, inactive_continuation_seconds=inactive,
        occupied_conservative_seconds=gross - inactive,
        scope="Elapsed time less documented terminal inactive intervals. Git and public transfer are itemized separately.",
    )
