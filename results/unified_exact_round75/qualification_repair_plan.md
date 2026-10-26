# Prospective qualification repair allocation after v1

V1 source af1d7a591 has a successful build and55/56 passing tests. The new
51-comparison independent oracle passes2293 feasible neighbors and rejects
infeasible load/time/stock cases. Its actual QDS-X CLI startup succeeds, but
the outer C6 contract rejects the unregistered preset before any Optimize.
No certificate is claimed. All four older CLI fixtures and the native Start
fixture still pass. V1 paid100.8464643s and75 actual Optimize calls, within
its original90-call allocation. Raw build/tests/results remain immutable.

Repair: add only the explicit QDS-X preset to the existing finite-descent
startup contract in PaperExternalGiniTree.cpp. The original seed/stop/population
requirements and all other proof gates remain. No mathematical neighborhood,
criterion, test expectation or fallback is changed to pass this failure.

The now-inspected actual native tiny CLI uses18 calls (17 probes and1 MIP),
not the smaller count initially estimated for planning. V2's added QDS-X
and JDS-X controls therefore require36 calls on top of the existing75.
Before V2 execution, amend its qualification ceiling to120 actual Optimize
calls; the one remaining V3 repair slot, if needed, has the same ceiling.
The original plan.md and V1 hash stay unchanged. Configure60s/build600s/
serial-tests600s ceilings remain. This is a prospective, disclosed resource
correction, not a change to the formal algorithm or retrospective relabeling.
Maximum from this checkpoint is two repair batches at120 calls each; no
additional startup or full-performance runs are admitted.

The new controller entry must pass the unchanged real native CLI certificate
test and the full56-test suite before the ten planned startup runs may launch.
