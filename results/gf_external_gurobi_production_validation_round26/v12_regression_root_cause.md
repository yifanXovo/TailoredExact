# V12 regression root-cause analysis

All 12 preregistered runs completed with return code zero, strict original-
problem certificates, passing independent verification, and passing sensitive-
marker scans. P-GRB Work is identical across repetitions, confirming the
deterministic native baseline.

## V12_M1

P-GRB median certificate wall time is 36.498s;
C0 is 37.559s (ratio
1.0291). C0 uses 34.781 Work
versus P-GRB's 53.573. The small 2.9% wall overhead is
repeatable fixed external/HGA/model orchestration, not excess native search,
and is inside the frozen 5% materiality bound.

## V12_M2

P-GRB median certificate wall time is 179.187s;
C0 is 183.022s (ratio
1.0214). Wall ordering flips in
1 of three matched repetitions, but deterministic
structure does not: C0 median Work is 341.716 versus
282.097 for P-GRB (ratio
1.2113). C0 performs six model reads/fresh
restarts, eight optimize calls, and five root-relaxation executions at the
median, versus one of each for P-GRB.

The controlling trace rules out delayed controlling-leaf scheduling: selected
leaves are controlling, and the three easy initial leaves close in well under
one second each. Model generation plus read time is about one second and is not
material. The hard initial interval receives a 30-second attempt and a second
60-second fresh-root attempt before the deterministic split; one child later
repeats the same 30/60 pattern. Thus the dominant structural cause is delayed
partitioning through repeated same-leaf optimize calls and repeated
presolve/root search. Wall variability partially masks this structural Work,
so the correct classification is **mixed timing noise and structural external
overhead**. It is not mainly initial-leaf allocation, scheduler starvation,
model I/O, or a numerical failure.

The evidence-supported uniform prototype is therefore to split every eligible
unresolved external-tree leaf after one attempt instead of two. This changes
only when an exact atomic partition occurs; it does not change coverage,
inherited lower bounds, cutoffs, or certificate semantics.
