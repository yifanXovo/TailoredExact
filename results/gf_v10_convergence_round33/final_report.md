# Round 33 final report

## Outcome

Classification: `v10_exact_convergence_crossover_mixed`.

Round 33 completed 52/52 frozen rows with 0 process failures,
0 valid time-limited rows, and 0 false certificates.
The frozen C6 C++ algorithm was unchanged. All primary times are strict
certificate times from process entry (`final_process_wall_time_seconds`), not
solver-only or exact-phase runtimes.

## V10 exact convergence

P-GRB strictly certified 18/18 V10 instances and C6 certified
18/18. Certificate-time outcomes were C6/P-GRB/tie/unresolved =
10/8/0/0. The median P-GRB/C6 speedup over
both-certified rows was 1.3237635881298069.
With a one-second shift, geometric-mean certificate times were
14.235169800238044 seconds for P-GRB and
9.371968116947423 seconds for C6.

The complete paper-facing 18-row table is `convergence_time_matrix.csv`.
Scenario, M, Q, and M-by-Q summaries retain all group outcomes without
mixing Round 32 raw evidence.

## Validation, anchors, and repeatability

The two V12 anchors produced 2/2 P-GRB and
2/2 C6 strict certificates. All
12 repeatability arm rows were valid: True. Certificate
states, objectives, Work, times, and C6 HGA/target/split sequences are in
`stage3_repeatability.csv`.

Post-run analysis repair: the first analysis pass treated C6's present-but-
empty `verified_incumbent_objective` field as NaN. The reporting code now uses
that field when finite and otherwise uses the authoritative top-level
`objective`. This analysis-only repair changed no solver result, timing,
certificate, fingerprint, executable, or frozen C++ input.

Observed proof AUC and gap-threshold times use real left-continuous events,
including a real final-result event when needed. No interpolation or
post-final-event extension is used. Solver-native optimality, strict
original-problem certification, strict certificate time, and time-limited
runtime are distinct fields in every public row.

## C6 mechanisms

Across official and repeat C6 rows, the run records contain
36 atomic splits,
63 native targets,
40 exact-closure launches,
76 child-lookahead pairs, and
41 requeues. C6 total native Work was
881.2588677555577 and peak recorded memory was
0.158732416 GB.

## Stable algorithm decision

C6 remains the validated tailored Gurobi mainline regardless of small-case
timing outcomes. Round 33 creates no C7, changes no rho or scheduling rule,
and is independent benchmark-completion evidence rather than an
algorithm-selection round.


## Evidence package

The package contains 1902 files excluding its self-manifest and
totals 190147414 bytes. 23 large artifacts were
compressed losslessly and every restoration hash was verified. The largest
retained artifact is `results/gf_v10_convergence_round33/runs/stage3__round33_v10_high_imbalance_M3_Q30_seed1765289896__p_grb__repeat1__3600s/progress.csv.gz`
(4971487 bytes). A package-wide license-marker scan found
zero hits.
