# Round 39 protocol frozen before official comparison

Round 39 creates a new, independent 24-instance V<=12 benchmark with exactly
eight structurally labelled small-easy, small-medium, and small-hard cases.
Generation, rejection, and classification use only frozen instance data; no
solver time, work, node, bound, incumbent, gap, certificate, or winner field
may influence selection. Historical instances and tables remain unchanged.

The primary comparison is the same original compact model under P-GRB versus
the validated C6 exact framework with HGA-LIGHT-1000. LIGHT changes only the
uniform completed-generation stagnation threshold from FULL's 2000 to 1000;
population, seed 20260626, operators, decoder, repair, selection, exact model,
strengthening, K=4 decomposition, scheduler, rho=0.01 split rule, and
certificate path are unchanged. The default remains C6-HGA-FULL.

All runs are contemporaneous, serial, one-thread Gurobi 13.0.2, exact Seed 0,
zero exact gaps, and process-entry timed. The 21,600-second limit is an
engineering watchdog, not a benchmark horizon: incomplete rows must be
preserved and extended before final reporting. No known optimum, prior archive,
or comparator incumbent enters either arm. Every primary row must reach a
strict original-problem certificate or be reported separately as unresolved.

The FULL guard subset was predeclared by structural stratum coverage before
official runs: slots small-easy-01, small-medium-04, and small-hard-08. Guard
analysis compares startup UB, startup/exact/total time, initial LP ledger,
target/requeue/split/closure event sequences, and final certificate. It will
not be expanded unless evidence requires it.
