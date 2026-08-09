# Round 34 frozen protocol before new solver results

Round 34 documents and observes the validated C6 exact framework. It does not
create C7 or change C6 mathematical decisions. The default `C6-HGA-FULL` arm
retains seed 20260626, generation-stagnation stopping, and 2000 generations
without strict improvement. `C6-HGA-LIGHT` changes only that final count to
1000. `C6-SIMPLE-START` uses the already implemented three-mode deterministic
greedy constructor and the same independent original-problem verifier.

All post-incumbent C6 options are identical: four initial intervals; binary
midpoint splitting; depth 8; width 1e-4; rho 0.01; full static inherited row
pack; presolve off; traditional search; no native MIP start; one thread; the
Round 31 nonblocking native-bound scheduler and lifecycle; and certificate
tolerance 1e-7. Startup time, verification, construction, exact search, and
finalization all count from process entry.

The complete-convergence cases were selected from historical evidence only:
V12_M2, the Round 32 V20/M2 high-imbalance anchor, and the Round 33 V10/M3/Q30
high-imbalance reference. No Round 34 trial selected a case. P-GRB and
C6-HGA-FULL receive a 7200-second process-entry cap.

The seven development identities, 18 V10 official identities, four transfer
anchors, and five repeat identities are predeclared in their CSV manifests.
Historical Round 33 HGA logs give full-fitness matches of 15/18,
17/18, and 18/18 for the natural candidate
stagnation values 250, 500, and 1000. Therefore 1000 is the predeclared primary
LIGHT candidate. Development is a viability/replication gate, not a parameter
sweep. At most this one reduced setting is retained.

Official startup rows use a 3600-second cap. Runs are serial, paired on the
same machine, Gurobi 13.0.2, Seed 0 for exact Gurobi, automatic plain-Gurobi
presolve, zero exact gaps, and one effective thread. Partial native MIP bounds
may strengthen open leaves but never close them. A deadline preserves open
coverage and yields a time-limited, non-certified result.

Fresh canonical fingerprints are generated for all 22 identities before the
official matrix. The executable, source hashes, protocol, commands, instances,
fingerprints, chosen variants, and matrices are frozen before official solver
results. Raw Round 32/33 rows remain read-only historical evidence and are not
mixed into Round 34 official tables.
