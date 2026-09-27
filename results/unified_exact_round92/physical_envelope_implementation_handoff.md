# Round92 physical-envelope v2: source handoff

Status: source-only candidate, **not compiled or executed**. Existing G1 001/002
receipts and the qualified v1 main/core/test binaries remain untouched. Native
G2 and performance G3 remain closed pending independent review and a separate
finite qualification admission.

The candidate branch now carries the raw binary64 pickup/drop coefficients and
each actual directed x-column arc alongside the writer-normalized canonical
duration coefficients. It validates identical support and builds one
coefficient-wise lower system, then runs one directed Floyd enclosure. It uses
the same named `1e-7` Evaluator tolerance, an outward horizon covering the
Evaluator's binary64 acceptance, and an upper quotient floor to form the
single `P_k <= B a_k` row. The old canonical duration row and the default-off
writer branch remain unchanged. A zero common service lower bound is an
explicit no-row result. Equality of quotient floors certifies **only the
chosen uniform surrogate envelope**, never the strongest physical or
canonical integer capacity.

Changed source: `include/PhysicalDurationTolerance.hpp`,
`include/Round92HandlingActivation.hpp`, `src/Round92HandlingActivation.cpp`,
`src/CplexBaseline.cpp`, `include/CanonicalCompactModel.hpp`,
`src/PaperExternalGiniTree.cpp`, `src/Evaluator.cpp`, `src/GurobiBaseline.cpp`,
`src/main.cpp`, `tests/round92_handling_activation_tests.cpp`,
`tests/round92_handling_integration_tests.cpp`, and
`tests/round92_handling_lp_readback.py`. The version-2 run-local cache key
compares raw and emitted arc presence/values, raw pickup/drop, emitted service,
T, physical tolerance and arithmetic-contract tag. The leaf ledger retains
model SHA/scope and adds version, common lower service and physical/common
horizons. G interval and incumbent epoch remain outside the mathematical key.

Candidate witness admission checks the original one-tour-per-vehicle domain,
global station uniqueness, operation identity, 64-bit load/inventory arithmetic
and `V*maxQ<=INT_MAX` before invoking the unchanged physical verifier. The
verifier's newly recomputed objective is the admitted U. Seed admission occurs
after route-pool selection and before cover/cutoff construction; the tree
rechecks it. The shared native wrapper checks the environment before/after
backend calls and re-admits every verified incumbent before returning it to
any UB/bound consumer. The backend's own incumbent and infeasibility-start
verification paths use the same opt-in guard. Round60/61/62 archive modes are
explicitly rejected with the R92 flag, including programmatic tree entry.
The tree entry independently requires the C6 nonblocking scheduling mode and
first-class K1 controller before any seed or backend action; the CLI applies
the same gate after preset resolution. This excludes alternate direct solve
paths that do not pass through the shared native wrapper.
The final tree witness is re-admitted. Any malformed evidence or unsafe FP
mode raises a reportable candidate error rather than falling back.

`Round92HandlingActivation.cpp` and `Evaluator.cpp` now require
`FLT_EVAL_METHOD==0` and reject fast-math at compile time. The helper checks
round-to-nearest and gradual underflow at each model use, including cache
hits; admission checks again immediately before physical verification.
The approved local FMA refinement leaves existing generic x64 compiler flags
and the Evaluator expression tree unchanged. No `-ffp-contract=off` or new
optimization flag has been introduced. A toolchain violating these conditions
must fail qualification; do not silently change baseline arithmetic.

Proposed one admitted finite qualification after the exclusive D6 run ends:
preserve only the v1 main/core/test binaries and their hashes inside the
existing Round92 build, then incrementally build affected targets once. Run
focused pure fixtures, export one fresh actual canonical model set, and do
one zero-Optimize LP readback. Check the dyadic `delta=2^-42` physical P=2
witness gives B>=2; ordinary T=5,c=2 still gives the nontrivial B=2 row;
raw-only arc changes invalidate the cache even when emitted LP bytes agree;
unsafe rounding rejects a cache hit; duplicate vehicle and unsupported count
domains fail before Evaluator; original F0/VD-P/row/cutoff identities remain;
the default-off LP SHA stays
`9872d149c970c99f2b0175929221fb42692c6915a68a4e57e94dd1492fb79a29`.
Retain every failed prefix and actual command cost. No Optimize belongs to G1.
The pure fixture was updated to size its raw arc rows before writes and to
bracket the new common-envelope dyadic quotient rather than compare its lower
endpoint with the old `T/c` quotient. A focused programmatic wrong-scheduling
fixture must fail at the R92 tree entry without creating a backend.
