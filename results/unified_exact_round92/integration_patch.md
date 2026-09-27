# Round92 integration contract and applied source map

The integration described below has now been applied in the candidate source
and awaits independent review and G1 execution. The historical sketch remains
for comparison; `integration_implementation.md` records actual source paths,
telemetry and the finite zero-Optimize gate. No build or solver execution has
occurred on the integrated candidate.

The table below is the pre-integration blueprint and retains its original
anchors for review. The Round90 source freeze has ended and the isolated R92
candidate edits are now present; see `integration_implementation.md` for
what was actually applied. A1/B1/LP-G remain separate. No binary or build
artifact has been produced from the R92 integration.

| File / current anchor | Minimal future change |
| --- | --- |
| `include/Instance.hpp:478–484` | Add `bool round92_handling_activation=false;` beside the existing isolated flags. |
| `src/main.cpp:118–120,254–260,1416–1419` | Add `--round92-handling-activation true|false`; parse with `parseBoolValue`; return `research-round92-ensc-handling-activation` from `effectiveAlgorithmIdentity` when true. Keep default R83 identity unchanged. |
| `src/main.cpp:3308–3322` | Require the R83 ENS-C preset and `gcap-frontier`; reject `round88_constructive_only_descent`, `round89_native_ot_b1`, and `round90_lp_g_split`. |
| `src/main.cpp:3939–3955` | Snapshot uses `effectiveAlgorithmIdentity`, appends `round92_static_rounded_handling_activation_row`, and states the single default-off candidate in `preset_reason`. Existing heuristic candidate and emergency provenance already call `effectiveAlgorithmIdentity`; audit every other `algorithm_preset` writer before qualification. |
| `src/PaperExternalGiniTree.cpp:335–341` | Add the same R83/first-class-K1/isolation guard at the actual ENS-C entry, so a programmatic SolveOptions caller cannot bypass CLI rejection. Do not alter AM, K1, depth, deadlines or branch decisions. |
| `src/CplexBaseline.cpp:1–20,427–454,1800–1808` | Include the helper. Candidate-only, construct a normalized coefficient object once before the per-vehicle duration loop and feed **that same object** into the original duration row and `prepareRound92HandlingActivation`. Require F0 and actual x-column support; invalid input/proof identity fails before Optimize. `valid_input && !applicable` for emitted `c=0` uniformly records no row. Otherwise, after each original duration row append exactly `sum_i p_{k,i} - B sum_j x_{k,0,j} <= 0`, including `B=0` for no closed route. Off branch remains the old code verbatim. Keep one explicit per-run exact-key cache at the caller, not inside helper. |
| `include/CanonicalCompactModel.hpp` and `src/CplexBaseline.cpp:4225–4380` | Carry candidate-only row count, B, quotient/round-trip enclosure, preparation/cache costs and applicability reason into the canonical artifact and model ledger. Bind each leaf's source LP SHA after write. If emitted `c=0`, retain the original duration and record the valid no-row reason/cost. In all other applicable cases a missing/mismatched row or failed ledger write is a candidate failure. |
| `CMakeLists.txt` | When separately admitted, add `src/Round92HandlingActivation.cpp` to `EXACT_EBRP_LIB_SOURCES` and a pure `Round92HandlingActivationTests` target using the new test source. This is not a solver test target. |

The writer hook is narrowly specified by the following *candidate-only* code
shape. `Round92DurationCoefficients` must be built from the exact original
duration row's raw `instance.dist`, `cunit` and `T`; use the normalization below
for **both** the original row and helper input. This is an integration hunk,
not compiled source and not a second independent duration formulation:

```cpp
if (options.round92_handling_activation) {
    if (flow_variant != ConnectivityFlowVariant::Round20Current)
        throw std::runtime_error("round92_requires_original_F0");
    Round92DurationCoefficients coefficients;
    coefficients.horizon = instance.total_time_limit;
    // Validate raw cunit and each raw arc for finite/nonnegative before this.
    coefficients.pickup = round92CanonicalEmittedCoefficient(cunit);
    coefficients.directed_travel.resize(V + 1);
    for (int i = 0; i <= V; ++i) {
        coefficients.directed_travel[i].resize(V + 1);
        for (int j = 0; j <= V; ++j)
            if (i != j)
                coefficients.directed_travel[i][j] =
                    round92CanonicalEmittedCoefficient(instance.dist[i][j]);
    }
    // Explicit run-local cache may reuse only an exactly equal normalized key.
    const auto plan = prepareRound92HandlingActivation(coefficients);
    if (!plan.valid_input)
        throw std::runtime_error("round92_invalid_handling_proof:" + plan.reason);
    if (!plan.applicable) {
        if (plan.reason != "zero_handling_has_no_duration_quantity_bound")
            throw std::runtime_error("round92_unexpected_no_row:" + plan.reason);
        // Emitted c=0: keep the original duration, record this uniform
        // mathematically valid no-row outcome and its preparation cost.
    } else {
    for (int k = 0; k < M; ++k) {
        // Existing original duration Expr: use coefficients.directed_travel
        // and coefficients.pickup instead of independently reading instance.
        // It still writes the unchanged original <= coefficients.horizon row.
        Expr activation;
        for (int i = 1; i <= V; ++i)
            addTerm(activation, pName(k, i), 1.0);
        for (int j = 1; j <= V; ++j)
            addTerm(activation, xName(k, 0, j),
                    plan.activation_coefficient);
        writeConstraint(out, cid, activation, "<=", 0.0);
    }
    }
}
```

The actual edit must keep the appended row **next to each existing duration
row**, rather than writing a second independent duration loop. The sketch's
for-loop merely displays the row expression. If a coefficient that the helper
uses differs from parsed LP readback, stop before Optimize and preserve the
failed artifact. The solver readback must also confirm binary depot-out
variables, integer nonnegative pickups, F0 connectivity, old duration RHS,
all rows/columns and objective cutoff. A physical verifier, not this helper,
remains the incumbent authority.

The plan's `exact_integer_floor` describes telemetry, not a method switch. A
false value means the row is conservative and potentially weaker than the
ideal exact integer floor; it is still valid. The per-run cache key is
`(version, T, c, directed-travel matrix with present/
absent arcs)`, compared by exact binary64 values after canonical
normalization. It is independent of leaf G domain and incumbent epoch. A
different coefficient or arc support invalidates it; a cache hit retains the
same proof but records its own lookup cost. The proposal has no runtime
instance/size/time selector, altered solver tolerance, implicit optimization
budget, or model-read/LP-parse inside a leaf build.
