# Round 58 CitiBike443 paired benchmark

Round 58 is the first direct paired comparison of the frozen K1-AM-SF
mainline with plain Gurobi (P-GRB) on the replicated
`citibike443-regional-v1` family. The tested panel is a deterministic subset of
the 960 generated scenarios: 30 structural scenarios and 20 matched
route-horizon scenarios. The remaining 910 scenarios are sealed reserves for
future holdout work.

Selection was completed before any benchmark performance run. The primary
panel contains one row for every V/geography/inventory cell and uses a fixed
balanced M/Q/T schedule. The matched panel uses the other replicate for the
corresponding cell, lower M, Q=30, and T in {3600, 18000}. No result may cause
a selected scenario to be replaced with a reserve scenario.

K1-AM-SF is the unchanged `paper-k1-am-sf` preset: K0=1, midpoint splitting,
balanced normalized closure score, tau=0.08, and the F0-CLEAN sparse inner
MILP. P-GRB is one original compact MILP selected by `--method gurobi
--plain-baseline`; it has no Gini decomposition, tailored cuts, custom
branching, HGA start, imported route, known optimum, or archive bound. All
runs use the same frozen executable, Gurobi 13.0.2, one thread, Seed=0, and
automatic presolve.

Every scenario receives both mandatory fresh 3600-second arms. Longer fresh
runs are authorized only by the frozen rules in
`round58_staged_runtime_protocol.md`; 21600 seconds is the absolute maximum.
The official result for a method is the valid entered run with the largest
authorized cap. Earlier attempts count toward total experimental compute but
are never added to the official run's algorithm time or Work.

Every available official incumbent is independently checked against the
original instance. Its native route witness is archived without repair,
compaction, or post-optimization. Archive and verification time are recorded
separately and excluded from algorithm time. Certified witnesses and
noncertified best incumbents are labeled distinctly.

Final compact evidence, grouped analysis, common-horizon comparisons, and the
benchmark decision live under
`results/gf_citibike443_k1_vs_pgrb_round58/`. Full native logs remain local;
their inventory and reproduction commands are committed.

## Final outcome

All 100 mandatory screen arms and every frozen extension completed, for 149
fresh optimizer processes in total: 100 at 3600 seconds, 35 at 10800 seconds,
7 at 16200 seconds, and 7 at 21600 seconds. Nineteen pairs entered the
10800-second stage. The audit found no missing or unauthorized run.

K1-AM-SF certified 34/50 rows by 3600 seconds and at the final authorized cap.
P-GRB certified 30/50 at 3600 seconds and 31/50 finally. Both certified on 31
pairs: K1 was faster on 7 and P-GRB on 24; K1 used less Work on 28 and P-GRB
on 3. The shifted exact K1/P-GRB geometric-mean ratios were 2.83349 for wall
time and 0.450095 for Work. There were three K1-only certificates and no
P-GRB-only certificate.

At the largest common authorized horizon for the 16 neither-certified pairs,
K1 had the smaller relative gap on 13, P-GRB on 2, with one tie. Mean relative
gaps were 0.269174 for K1 and 0.330379 for P-GRB. One row met the historical
severe-regression definition, no row met the conservative long-run material
regression definition, and no false certificate or correctness failure was
found. All 100 required official native route packages passed independent
verification.

The final classification is `k1_am_sf_pgrb_advantage_mixed`. The panel shows a
K1 certificate-count and Work advantage and generally stronger open-row gaps,
but P-GRB is faster on most jointly certified rows. This is not stable universal
dominance. A second sealed panel selected in advance from the 910 unopened
reserves is required before a stronger paper-benchmark claim.
