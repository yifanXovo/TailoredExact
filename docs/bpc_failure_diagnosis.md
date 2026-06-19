# BPC Failure Diagnosis

Date: 2026-06-14.

Scope: full `gcap-frontier` route-load BPC for the original objective. Compact strengthened/tailored results are auxiliary only. Plain CPLEX is the benchmark. CPLEX-incumbent-warmed diagnostics are not pure BPC performance.

Detailed interval rows are in `docs/bpc_interval_diagnostics.csv`. Load/order samples and no-cut conclusions are in `docs/load_order_diagnostics.csv`.

## Run-Level Summary

| Instance/run | Status | UB | LB | Gap | Wall (s) | Unresolved | Open nodes | Diagnosis |
|---|---|---:|---:|---:|---:|---:|---:|---|
| V10 M2 average, BPC 4w | optimal | 0.463263009179 | 0.463263009179 | 0 | 589.0030 | 0 | 0 | Pure-BPC certificate; plain CPLEX did not certify in 1200s. |
| V10 M1, BPC final closure | optimal | 0.492625123580 | 0.492625123580 | 0 | 641.0844 | 0 | 0 | Pure-BPC certificate; no CPLEX incumbent. |
| V10 M1, plain CPLEX | optimal | 0.492625123580 | 0.492625123580 | 0 | 63.3175 | 0 | 0 | Benchmark certifies faster. |
| V10 M1, strengthened compact | optimal | 0.492625123580 | 0.492625123580 | 0 | 166.3436 | 0 | 0 | Auxiliary exact certificate, not BPC. |
| V10 M2 low, BPC local/pool | not closed | 0.831494993816 | 0.820406010310 | 0.0133362 | 1200.6103 | 18 | 22 | Pure BPC remains open. |
| V10 M2 low, strengthened compact 1200s | optimal | 0.824301313135 | 0.824301313135 | 0 | 938.1948 | 0 | 0 | Portfolio fallback certificate, not BPC. |
| V10 M2 low, plain CPLEX | not certified | 0.824301313135 | 0.793050728170 | 0.0379116 | 300.0874 | 0 | 0 | Benchmark incumbent matches optimum but did not certify. |
| V12 M1, BPC 3600s | not closed | 0.695790527408 | 0.690938092526 | 0.0069740 | 3622.6885 | 26 | 34 | Earlier near miss. |
| V12 M1, BPC 7200s | optimal | 0.690938574743 | 0.690938574743 | 0 | 5280.7002 | 0 | 0 | Pure-BPC certificate after improved incumbent and frontier bound closure. |
| V12 M1, strengthened compact | optimal | 0.690938574743 | 0.690938574743 | 0 | 123.3197 | 0 | 0 | Auxiliary exact certificate, not BPC. |
| V12 M1, plain CPLEX | optimal | 0.690938574743 | 0.690938574743 | 0 | 9.2284 | 0 | 0 | Benchmark certifies fastest. |
| V12 M2, BPC local/pool | not closed | 0.404618571401 | 0.350523627890 | 0.1336937 | 1200.5870 | 14 | 18 | Pure BPC remains weak. |
| V12 M2, strengthened compact | not certified | 0.366168793171 | 0.258189227130 | 0.2948901 | 300.2094 | 0 | 0 | Better incumbent but weak compact lower bound. |
| V12 M2, plain CPLEX | not certified | 0.365626842595 | 0.304969452260 | 0.1658997 | 300.2167 | 0 | 0 | Benchmark has best incumbent but no certificate. |

## Implemented Improvement Directions

### BPC Final Closure

V10 M1 and V12 M1 were closed by deeper adaptive interval splitting and focused retry. V10 M1 closed a final interval around `[0.245632,0.245636]` with exact branch-price retry. V12 M1 closed after the retry phase found an improved incumbent with objective `0.690938574743`; the remaining frontier was then bound-fathomed by valid route-mask/Gini lower bounds.

The V12 M1 audit is careful about this point: one retry row has `complete=false` and open retry nodes, but the final certificate does not rely on that retry tree as a closed pricing-tree proof. It relies on the full frontier ledger after the improved incumbent, with `unresolved_intervals=0`, `invalid_bound_intervals=0`, top-level `open_nodes=0`, and `gap=0`.

### Strengthened Compact Fallback

The strengthened compact branch-and-cut is now an important exact portfolio module:

- V10 M1 average: certified in `166.3436s`.
- V10 M2 low: certified in `938.1948s`.
- V12 M1 average: certified in `123.3197s`.
- V12 M2 average: not certified in `300.2094s`.

These are original-problem compact certificates when optimal, but they are not BPC certificates.

### Station-Operation Relaxation Cuts

The final-inventory/Gini interval relaxation includes:

```text
p_i + d_i <= U_i v_i
p_i + d_i >= v_i
U_i = max(min(Y_i^initial,Qmax), min(C_i-Y_i^initial,Qmax)).
```

The proof and zero-operation caveat are in `docs/station_operation_cut_proof.md`. The cuts remain enabled for certificate-producing runs.

## Remaining Open Case: V12 M2 Average

V12 M2 is now the only open target in the portfolio table. The best current portfolio incumbent is from compact B&C:

```text
UB = 0.366168793171
```

The best current valid portfolio lower bound is from pure BPC:

```text
LB = 0.350523627890
```

This leaves a valid portfolio gap of about `0.0427266`. The failure is mixed:

- BPC lower bounds remain weak in low-Gini intervals.
- Compact B&C finds a strong incumbent but has a weaker lower bound.
- Strong BPC-owned incumbent smokes improved UB but not enough to close the lower-bound gap.
- No sampled route support provided a proof of load-order infeasibility, so no load-order cut was added.

The next valid improvement direction is an exact route-support infeasibility oracle or Benders-style support cuts, plus stronger compact/BPC bound sharing with a formal proof.

## Recommendation

The paper algorithm should be a tailored exact portfolio:

1. Run pure full Gini-frontier route-load BPC.
2. If BPC stalls, run strengthened compact branch-and-cut fallback.
3. Report pure-BPC, original-compact, plain-CPLEX, and diagnostics separately.

Pure BPC certifies V10 M2 average, V10 M1 average, and V12 M1 average. The compact fallback certifies V10 M2 low. V12 M2 remains open and is the main bottleneck for the next research pass.
