# Final unified method: ENS-C

One preset: `research-round83-vds-equal-net-exchange`, qualified source
`4496078f25c0cdad1cf7a5c39835fd23121e8978`, executable SHA256
`25b7ec3a6d89d9f0f921c2984fbb1d9876f36f67e617af144275c88b44e6255e`.
R84–R86 change no algorithm or parameter. The full source-grounded definition
and proof references remain [R83 unified method](../unified_exact_round83/unified_method.md)
and [exchange mathematics](../unified_exact_round83/mathematics.md). Their old
pending-confirmation statements are superseded by R86 evidence, not by new math.

## Problem and applicability

Y_i=b_i+sum_k(d_ki-p_ki), r_i=Y_i/D_i, S=sum_i r_i, H=sum_(i<j)|r_i-r_j|,
F=H/(V*S)+lambda*sum_i w_i|r_i-1|, with original G=0 when S=0. Retain positive
targets, original station/weight parsing, disjoint visits and one nonzero
one-way integer operation at each visited station. Empty departure, loaded
return allowed, prefix loads in[0,Q_k]. Duration is travel+c_pick*pickup+
c_drop*station_drop+c_drop*return_load = travel+(c_pick+c_drop)*pickup <=T.
Q does not bound cumulative pickup; station inventory need not be conserved.
The complete strengthened method requires symmetric metric travel and inherited
nonnegative penalties. Its metric guard is active; isolated nonmetric tests do
not qualify the entire method for that broader class.

## Algorithm and uniform rules

```text
Start the sole process clock; validate the original problem.
Construct and physically verify a joint-insertion witness.
Fully decode24 fixed-seed random orders plus its constructive order;
  run declared strict decoded descent and retain the best verified witness.
Alternate strict insertion/quantity closure with the best feasible move in
  balanced relocation UNION equal-net contiguous-block exchange, until exhausted.
Pass an objective-improving witness through the outer handoff rule.
Whenever verified numerical zero closes against F>=0, return that certificate.
Establish one complete Gini-interval cover using VD-P and static F0.
While obligations remain and the sole global deadline has not ended:
  use valid child LP bounds to split, target the exact parent, or close it;
  maintain the complete cover and each bound's scope;
  map/check/read back one eligible paid full Start for each necessary native MIP;
  accept original U only after physical/objective verification.
Return numerical certification only when verified U and full-domain L close.
```

All model work, probes, Start verification, native calls and exit are paid.
Native calls may stop at mathematical targets with obligations retained; there
is no component seconds/Work allocation, history-based switch or archived route.

|Part|Uniform rule and meaning|
|---|---|
|Startup|Seed20260626;24 random orders plus1 constructive; no evolutionary generation loop|
|Decoder|`nGreedyLU_RA_compact_full`, compaction mode1; greedy/remove zero/redecode/keep better; legacy iterations10 is ignored, not a10-pass gate|
|Cache|200000 entries then clear; changes recomputation cost, not stopping logic|
|Strict closure|Insertion gain/duration proposal versus best legal single/opposite-pair quantity proposal; lower F, ties insertion; gain>1e-12, prediction agreement<=1e-10|
|Neutral closure|All balanced blocks/recipient legs plus equal-net pairs of nonempty contiguous blocks; recipient Q and original full-duration checks; strict decrease of descending sorted vehicle-duration tuple|
|Neutral ties|Relocation before exchange, then source/first/last/target/target-first/target-last|
|Outer handoff|F improvement>1e-10; neutral-only routes need not become native Starts|
|VD-P|One-hot inventory state product, original penalty epigraph retained|
|F0|Two propagation passes, support<=3, at most50000 subsets; strengthening size, not runtime allowance|
|AM|K0=1, midpoint, depth8, minimum width1e-4; terminal unresolved regions go to complete MIP|
|AM score|g_j=clip((b_j-B)/max(U-B,max(cert_tol,1e-12)),0,1); eta=min g, mu=mean g; active eta*mu threshold .08|
|AM action|No strict child-disjunction gain: exact parent; sufficient score: atomic two-child cover; small positive gain: parent target min(b0,b1), requeue|
|Native|Gurobi13.0.2, Threads1, Seed0, PresolveAuto, requested gaps0; no dynamic user cuts/custom branching|

Legacy output threshold .01/frontier intervals4 are compatibility fields,
not active AM rules. Old timed local oracles are unreachable in active startup.
Logical neighborhood/strengthening limits are not renamed runtime slices.
Parameters are uniform empirical choices, not theoretical optima.

## Correctness, design and efficiency

VD-P uses sum s_iy=1, Y_i=sum y*s_iy, gamma_L*s_iy<=q_iy<=gamma_U*s_iy,
sum q_iy=G and Z_i=sum y*q_iy. The unique selected integer state has q=G,
so Z_i=G*Y_i, and every original allowed inventory/product point extends to it.
This requires valid domain/interval bounds; the full coupled LP is not claimed
an integer hull. Retained F0 scope/proofs are linked in the full R83 definition.

Balanced relocation has net0; two exchanged blocks have equal, possibly nonzero,
net. Outside-block prefixes and terminal loads are preserved. Check each incoming
block's relative prefix extrema at its recipient entry load/actual Q, recompute
full travel/handling and physically verify. Operations/Y/F are unchanged. Finite
strict (computed F, duration tuple) descent prevents cycles; the duration proxy
can expose strict improvements but does not prove faster native optimization.

The interval cover never drops unresolved regions. Atomic replacement, scoped
bounds and verified-incumbent cutoff reasoning preserve necessary optimality
obligations. A full Start only guides search: equal-Q label normalization is
verified, all columns/rows/objective mapped, submission read back, native loading
logged. Ineligible Starts are skipped without domain restriction. Starts are not L.

Native feasibility/integrality/optimality tolerances remain1e-6/1e-5/1e-6;
physical-time/proof closure1e-7; verified-zero1e-12. Signed tiny gaps stay signed;
material contradictions fail validation. Zero requested gap is not rational proof.

The contribution is a justified, source-verified and measured composition of
inventory representation, full proof scheduling, finite physical search and
actual native integration. Generic block exchange/relocation/multistart and
disjunctions are not claimed new theory. Actual Starts and22 F6 exchanges prove
execution, not componentwise speed causality; full wall/U/L trajectories measure
efficiency. See `goal_evidence_scope.md` for accepted gains and D7/F5 tradeoffs.

Recommend this single explicit research preset for the supported joint primal
and proof objective, keeping stable defaults unchanged pending user merge choice.
No instance-based ENS/K1/BDS selection is proposed. Reproduction identities,
commands, dependencies and closed-producer guards are in `reproduce.md`.
