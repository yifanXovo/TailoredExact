# Round 22 native-trajectory monotonicity erratum

The production matrix frozen at source commit `909479293bfa8b64893b3697d86ec24a1ee22b4a` completed 19 Stage 2 rows and then stopped on `stage2__tight_T_seed3101__s1__900s__dense_on`. Its authoritative trace had 6,952 retained events and 15 negative native best-bound steps. The two largest were `1.000000000001e-6`, reported by consecutive documented read-only relaxation snapshots at processed-node transitions 922→923 and 1172→1173. The native status was 108, the runtime was 882.3037448 seconds, and the final raw bound `0.043790170799157389` exactly matched the native final result JSON. Timestamps, files, flush, finalization, hashes, model gate, lifecycle, and endpoint evidence were valid.

The immediately preceding integrity erratum used `1e-6 * max(1, |previous|, |current|)` as a magnitude cutoff. This second independent source-native counterexample proves that no magnitude cutoff establishes whether a documented callback value is corrupt. Raising or adding another tolerance would only tune the audit to observed data.

Before accepting any production-matrix row, Round 22 now freezes these durable rules in both the shared C++ audit and the official runner:

- Raw native best bound, incumbent, and processed-node values remain full precision and are never clamped, enveloped, rounded, suppressed, or repaired.
- Every bound decrease, incumbent increase, and processed-node decrease is reported with its count and maximum step.
- Native monotonicity is diagnostic-only at every magnitude and cannot invalidate an otherwise authoritative trace.
- Structural integrity remains fail-closed for non-strict timestamps, missing solver-final evidence, final-record/native-JSON endpoint mismatch, parse or file failures, unsuccessful flush/finalization, and hash/model/lifecycle violations.
- None of these diagnostics can promote a solver status, establish optimality, alter model correctness or independent feasibility verification, change objectives or final bounds, or enter the S0/S1/plain decision rule as repaired data.

The 19 completed rows and this stopped row are excluded from the replacement matrix and retained under `attempts/pre_monotonicity_erratum_90947929`. The source, executable, Stage 0, complete Stage 1, and production matrix are refrozen and rerun from the beginning.
