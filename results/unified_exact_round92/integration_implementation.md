# Round92 handling/activation integration: source freeze for review

This is the isolated, default-off ENS-C research candidate. No build,
import, test, or Optimize has run on this source. The single added family is
`sum_i p_k_i <= B sum_j x_k_0_j`, with one row per vehicle and the helper's
uniform safe upper-floor `B`; there is no vehicle-capacity sum-pickup rule,
time slice, extra cut family, changed startup, AM gate, depth, solver tolerance,
or LP-G/native-B1/A1 combination. `--round92-handling-activation true` gives
external identity `research-round92-ensc-rounded-handling-activation`; the
unflagged Round83 ENS-C identity and writer branch remain unchanged.

The candidate writer validates nonnegative finite physical duration inputs,
constructs the full actual x-column support (all directed off-diagonal arcs),
and canonicalizes every arc and the common pickup coefficient once with the
same addTerm/writeExpr suppression and near-unit rules. The original duration
row consumes that object, and the pure Round92 helper proves its integer
coefficient from that very object. F0, strengthened interval model and an
explicit run-local cache are mandatory; the Paper entry also checks first
class K1/R83/method and excludes A1, B1 and LP-G. Exact binary64 key equality
includes the construction-version tag, T, c, every arc-presence bit and
directed value. Incumbent epoch/G domain is intentionally absent from the
physical key. Cache hits reuse only the proof; misses pay the full O(V³)
directed shortest-path enclosure. Candidate-only `round92_handling_activation_rows.csv`
flushes leaf/model SHA, row IDs/count, B, applicability reason, floor status,
cache/cost and quotient bounds before native Optimize. A valid emitted c=0
uniformly records no row; other invalid/missing-row/ledger failures stop.
The canonical artifact SHA still binds the complete written model.

The newly added G1 sources are `Round92HandlingActivationTests` (independent
two-station integer oracle, dyadic quotient, physical `P>Q` loaded return,
runtime rounding/FTZ/DAZ rejection and cache-key invalidation),
`Round92HandlingIntegrationTests` (zero-Optimize real canonical fixture with
frozen Round91 off-LP SHA, two new rows and run-local reuse/invalidation),
`round92_handling_lp_readback.py` (Gurobi read without Optimize: original
row multiset/objective/cutoff/G/F0/variable domains and actual new/duration
coefficients), and the pre-Optimize CLI identity/combination check. The pure
test does not itself certify the parsed LP or the algorithm.

After independent source review, the proposed **single finite G1 execution**
is: configure once in `build/research/round92-handling-activation` using Ninja,
`D:/msys64/ucrt64/bin/g++.exe`, `-DEXACT_EBRP_ENABLE_GUROBI=ON`,
`-DGUROBI_ROOT=D:/gurobi1302/win64`; build the main executable plus the two
Round92 tests once; run the pure and CLI tests once; run the integration
exporter once into a new preserved directory; then use the already qualified
`build/research/round88-ot/venv/Scripts/python.exe` to perform **one**
zero-Optimize Gurobi LP readback on that directory. Capture full commands,
binary/source hashes, actual off SHA, all output and failed attempts/costs.
If any identity or parsed coefficient differs, stop before any solver run.
G2/G3 require separate root admission; this document authorizes neither.

Proposed exact PowerShell commands from the repository root, to be issued
only under a later G1 lease (the output directory must not already exist):

```powershell
cmake -S . -B build/research/round92-handling-activation -G Ninja '-DCMAKE_CXX_COMPILER=D:/msys64/ucrt64/bin/g++.exe' '-DCMAKE_MAKE_PROGRAM=D:/Program Files/Microsoft Visual Studio/2022/Professional/Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe' '-DEXACT_EBRP_ENABLE_GUROBI=ON' '-DGUROBI_ROOT=D:/gurobi1302/win64'
cmake --build build/research/round92-handling-activation --target ExactEBRP Round92HandlingActivationTests Round92HandlingIntegrationTests
ctest --test-dir build/research/round92-handling-activation --output-on-failure -R '^(Round92HandlingActivationTests|Round92HandlingActivationCliTests)$'
build/research/round92-handling-activation/Round92HandlingIntegrationTests.exe results/unified_exact_round92/qualification_001/canonical_export
build/research/round88-ot/venv/Scripts/python.exe tests/round92_handling_lp_readback.py results/unified_exact_round92/qualification_001/canonical_export
```

The two new CTest entries are pure and fail-before-input CLI checks; the
integration exporter and parser readback each have zero Optimize calls.
Frozen R83/R88/R89/R90 regression selection and any actual tiny native solve
remain a separate later gate after these checks and independent review.

The passive Paper depth-summary-zero issue is left untouched: it does not
enter the proof or this model, and fixing it without a focused source/fixture
review would broaden the candidate change.
