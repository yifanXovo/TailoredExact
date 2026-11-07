# Reproduction boundaries and fixed inputs

The scientific entry is the isolated Round157 worktree. goal.md is the exact
attached instruction file. production_plan.md records the initial offline
allowances; mathematical_analysis.md distinguishes original-T fleet
feasibility, finite objective-invariant families, time lower bounds and
global objective-level coverage.

The inherited source base is e10ffd01de6cf2fa9db71ba5a51f7d9eab8efb05,
R156 fixed science751de842a0264a146701de6669b1f3dd6dc764b1. Existing R137 inputs
and K20's R132 input are referenced by fixed commit/path/hash rather than
repacked. The preselected physical queries use:

| Role | Original relative input | SHA256 |
|---|---|---|
| RX35 | results/unified_exact_round137/inputs/R-X35-S.txt | c874d76142dc4e3ca43072d89a45d95a0f90c790d5bb4c06ca06c85dab0fbbd2 |
| NB35 | results/unified_exact_round137/inputs/N-B35-S.txt | 80c75e509adba393e0f693043de0fff7412d97f92ee295465edaa011bde98c98 |

The files' original physical parameters, coefficients, scope and inventory
witnesses are bound by inventory_sources.json and inventory_families.json.
The latter contains the actual finite member vectors and positive-control
routes inline. No old optimization needs to run to reconstruct a query.
The preparation script captures this machine's historical source pointers;
it is not a portable command to rerun on an arbitrary future HEAD. Use the
saved source/member evidence, not a guessed old absolute path.

The following command is a fresh scientific experiment, requires the
qualified commercial Gurobi13.0.2 runtime, and must use a new label/output.
It is not part of public byte recovery:

```powershell
& 'E:/codes/ExactEBRP/build/research/round88-ot/venv/Scripts/python.exe' -B `
  scripts/round157_common.py NEW_LABEL 1860 round157_fleet.py `
  R-X35-S-T2 1 family NEW_LABEL 4096 1800
```

ROOT derives from the source checkout. Configure the existing verified
interpreter only in the task adapter when relocating; do not change global
settings or substitute an unverified DLL. The production DLL identity is
9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88.
No compiler or new production PE is required by the standalone Python fleet
interface. The inherited R156 production PE identity is kept separately
from these Python/native diagnostic calls.

Every call preserves its exact inventory condition, canonical model,
parameters, actual solver return, Work/nodes and any full route witness.
The launch source snapshots bind the executed bytes. An open fee must be
reconciled by actual PID/birth or receipt before another serial run starts.
Never reuse a label, overwrite a failed attempt, infer INFEAS from a
truncated run, or treat a resource assignment as a fleet route.

The new-only carrier and manifest bind only this round's source
and evidence. One bounded anonymous fixed-commit restore checks hashes,
sizes and members without Optimize, compilation or old producer execution.
Required inherited inputs/source and older carriers retain their own fixed
reference identities. Cleanup follows the workspace policy only after an
actual passed restore; zero deletion is allowed and unique evidence stays.

Use publication.json's fixed_science_commit for the bounded byte-recovery
command `python -B scripts/round157_delivery.py restore COMMIT`. The
production dependency/runtime is not executed by this recovery. The actual
successful receipt and destination, followed by metadata-only cleanup,
are recorded in RESUME.md and the delivery JSON files. They are not claimed
by the science manifest before the remote files have actually been read.
Mutable delivery metadata is normally committed afterward; it is excluded
from that fixed science manifest to avoid a circular commit/hash claim.

The complete E+R panel is deliberately not started: both preselected RX35
families are impossible, the one finite26-vector repricing has no global
lower gain, and the full-domain resource MIP stalls. No offline stock or
proof is presented as a self-paid complete arm. The exact result tables,
source snapshots, failed attempts and final fee ledger retain that outcome.
