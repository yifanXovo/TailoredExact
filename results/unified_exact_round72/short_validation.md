# Round72 audited short-panel checkpoint

The unchanged DS-X candidate restores D3 certification and improves C2
certification time while preserving D4 protection against official P-GRB.
The predeclared long-run gate passes. D7 at3600s and broader confirmation
remain unfinished; the sustained research goal is not achieved.

Base73ce04d9a3c5031c2b5a1021523502f0a9a85168 / Round71 draft PR132.
Branch codex/round72-vdsx-validation. Execution-plan freeze6c0a230aed57bf3b145dc8c1f0175c7e258610a8;
bound-identity checkpointdff9d14e6. Compiled source3867214f480d0a4fef4d77f03404f9fd89fb8b42,
binary4f60ed8cd6f65c695947e8ac3bd525b77d28d94733faf2c9ef25d057a69023af.
All199 source hashes, reference executable and inherited test log match.
No new solver build, CTest batch or qualification Optimize call was executed.
The49 tests/39 native qualification calls belong to Round71.

## Complete outcomes under common300s caps

|Role|P-GRB|DS|DS-X|
|---|---|---|---|
|D3|Open gap0.003536339|Open gap0.001772843|Certified255.360s|
|C2|Open gap0.058481279|Certified154.219s|Certified111.234s|
|D4|Open gap0.310269996|Certified53.860s|Certified54.703s|

D3 DS-X certifies U0.04500155005562836 with LB0.04500155005562833.
Its complete parent-domain native MIP closes the proof; no child coverage is
lost. DS retains U0.04500155005562836/L0.04322870702341869, while P ends at
U0.04505416158053462/L0.04151782225242993. This recovers the certificate
lost by DS. It does not match the historical faster HGA-start VD-S result;
no current paired speed claim against that historical variant is made.

C2 certifies the same original objective0.8299634131717752 in both candidates.
DS-X saves42.985s,27.87%, relative to DS, passing the frozen material criterion.
P's LB remains0.7714821344222142. D4 both candidates certify0.506343307565206,
while P's LB remains0.19607331175073336. DS-X costs0.843s more than DS there,
below the frozen practical threshold. No statistical-equivalence claim is made.

The separate six UB-only startup diagnoses all pass physical and strict trace
checks. DS-X's cross-route checks/moves are47/28 onD3,94/22 onC2 and131/46
onD4. All full runs independently reproduce their respective diagnostic full
route hashes and logical descent traces, excluding elapsed timestamps. The
formal runs recompute and pay for startup; no diagnostic witness is imported.
Startup U improves on all three roles, while full effects differ: D3 recovers
a certificate, C2 accelerates certification, D4 has no material time difference.
This limits any claim that better initial U alone ensures faster proof.

## Trust, admission and costs

All9 full runs pass independent physical objective/routes/inventories,
configuration roundtrips, original P fingerprints, numerical bound consistency,
and full-domain interval coverage.22 retained-witness/model checks pass;
8 incompatible G intervals are explicitly identified, not mapped as feasible.
All11 eligible Starts are accepted in native logs and full vectors observed
by the qualified C++ MIPSOL observer. Independent replay verifies retained
submitted/readback vectors and model rows; full native event vectors were not
retained for a second replay. Three P controls have no added Start.

159 complete-run compact artifacts (150 lossless plus9 exact summaries),
989753 bytes, pass content/hash verification. The48 separate diagnostic
artifacts add54502 bytes. One observed offline packaging schema failure is
retained and repaired; no raw solver run was changed or repeated. Later
packaging additionally checks stored final inventories from routes.

Nine full runs cost1817.642s and36 native Optimize calls. The six diagnostics
add0.390s and zero Optimize calls:15 experiments,1818.032s total. Three separate
no-opt reference exports cost0.235s. No solver validity failure, watchdog or
startup-only deadline occurred. All arms use Gurobi13.0.2, Threads1, Seed0,
PresolveAuto, zero requested MIP gaps and original tolerances, on mask4 with
readback/restoration. Every startup, build, probe, native solve and exit is paid.
Offline QA is separately recorded and is not subtracted from process wall.

The architecture remains the default-off DS-X defined in algorithm.md and
the frozen mathematical note. Finite decoded descent and physical UB admission
leave the complete Gurobi proof intact. No resource-driven solver switch or
new-theory/rational-certificate claim is introduced. The experimental gate is
external to the solver and is not an instance rule.

## Next decision already declared

campaign/long_gate.json admits exactly three fresh D7 runs: P-GRB, K1-R,
DS-X, common3600s, maximum10800 additional process seconds. The audited nine
rows and pairs are retained as short_runs.csv/short_pairs.csv, with hashes of
all gate audits. R71's1200s DS-X result retained only9.5% of K1's advantage
over P, so protection remains a serious unresolved issue. The long window
tests persistence of that loss; it is not assumed to repair it. No repeats,
7200s extension or independent confirmation campaign is opened here.

Latest resource check permits ordinary use with97% remaining. The agent did
not redeem a reset. The earlier transition to100% has unknown cause. Original
dirty checkout, closed stages and main remain untouched. Resume using status.md,
the process ledger and reproduce.md; do not replace earlier observations.
