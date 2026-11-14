# Independent implementation/data admission before the formal matrix

Reviewer: independent `data_review` agent. Actual review date: 2026-11-14
(Asia/Shanghai). Decision: **admit the declared C166/B comparison once the
same already checked production PE is bound to the actual clean C++ source
commit and the fixed 12-position matrix is frozen with the required >=9h
remaining. No unresolved implementation/data blocker was found.** This is
diagnostic admission, not a performance or adoption conclusion.

## Actual checks completed

1. Read the actual `src/round166_qualification.cpp`,
   `scripts/round166_qualification.py`, `scripts/round166_campaign.py`,
   changed writer/policy/Start/backend/CLI sources, and the actual
   qualification outputs. All new model building, local LPs, native MIPs
   and finite physical enumeration are C++. Python orchestration/checking
   does not import a solver or make Optimize calls.
2. The algebra enumeration covers 4,550 interval/initial/capacity domains
   and 77,168 graph-state/g checks, plus the empty-domain and continuous-only
   product counterexamples. It checks legal internal stocks and absolute
   bit reconstruction. This finite test supplements the independently
   reviewed algebraic proof; it does not establish the general result by
   matching numerical objectives.
3. Read all 64 fixed local LP result rows. Native statuses are optimal and
   reported primal/dual/bound residuals remain <=1e-7. The full joint,
   breakpoint joint and breakpoint-plus-bit LPs match for both fixed
   objectives in all eight boundary configurations. The independent
   product/service reference is correctly weaker in the declared separator:
   its Z range is [0,2], while the shared-stock graph fixes Z=1.
4. Independently parsed all eight saved B/C166 canonical pairs (six fixed
   R163 roots and the first two deterministic child intervals) using the
   existing strict LP grammar. The maximum absolute signed LP-objective
   difference is 3.3306690738754696e-16. The maximum independently read actual
   Start row residual among these files is 3.765876499528531e-13.
5. Added the pure reusable checker `data_c166_model_check.py`. It checks
   the exact legal support set, all t/q continuous domains, absolute bit
   binaries and product domains, every declared representation row with
   multiplicity, and the original ratio/e epigraph and weighted objective.
   All eight model pairs pass. After subtracting the *complete declared*
   representation blocks on each side, the remaining common physical and
   valid row multisets, common column domains/types and objective match
   exactly. `data_c166_contract_results.json` retains per-model SHAs and
   per-station supports. This includes singleton-at-initial domains whose
   visit reconstruction loses every encoding coefficient; merely deleting
   rows containing encoding names would incorrectly report a difference.
6. Eight deliberate pure-data mutations were rejected: binary t,
   continuous bit, missing product row, changed mass RHS, absent e epigraph,
   an illegal support column, a changed objective and a deleted common
   physical row. See `data_contract_mutation_checks.json`. These tests make
   no solver calls.
7. The independently enumerated tiny physical case has optimal stocks
   (1,1), G=0, P=1, F=.15 and a returned load of 1. Station 1's stock 1 is
   an internal non-breakpoint of its support {0,2,3,4}. C166's saved complete
   fleet is 0-1-2-0 with pickup 2 and drop 1: prefix loads 2,1; unload 1
   at the depot; total handling 240s <=360s. The C++ oracle enumerates
   routes/stocks in a 480s superset for the initial-stock-3 case; its same
   optimum is feasible under 360s, so it also proves the scheduled tighter
   model's optimum. No stronger feasible-domain identity is inferred.
8. Actual native LP-to-MIP tests restore the full original VType vector on
   the **LP return**, and the following MIPs have integer/binary counts and
   .15 optima consistent with the declared models. S=0 MIPs return Y=(0,0),
   F=.3, and exact-zero-objective MIPs return Y=(2,2), F=0. All native Start
   submissions reported as expected are accepted and row-valid.
9. Four full controller smoke positions now have complete sealed producer
   and qualified reader records. Nonzero B/C166 each use four native calls,
   certify .15, complete own H, and have the same H semantic/fleet hashes.
   Zero B/C166 use zero native calls and retain the existing independent
   exact-zero full-domain nonnegative-floor certificate. The zero shortcut's
   H_complete=false is preserved, rather than claimed as a complete H search.
10. The old-library B export and current B export are byte-identical
    (5,952 bytes, SHA 75ea6bd896cca0957ed99169664d6ce642fdf89a19342465e528a4d7c516c274).
    Actual AP/RN/count/theta incompatibility probes return explicit errors
    and zero Optimize calls. The CLI flag/policy identity bypass identified
    in the initial review was corrected and read back.

## Calls, failures and identity

The qualification ledger totals **96 actual Optimize calls**: 64 local LP,
16 canonical root/child LP, eight tiny boundary/native calls and eight
nonzero controller calls. The four complete controller positions are
diagnostics, not formal performance observations. The reported diagnostic
outer window is about 539s, well below 3,600s; the pre-formal source/read-only
review does not add native calls. No 4,096-node development limit was added.

The B tiny restore producer completed its two calls, but the driver's old
post-read assertion looked for `integer_domain_restored` on the subsequent
MIP rather than on the completed LP. The assertion was fixed; B was not
rerun. Its original call/result files remain, and the missing post-assertion
B final-fleet file is disclosed in `reader_fix.json`. C166's full fleet and
the independent physical oracle provide the required non-breakpoint check.
The first nonzero C166 reader attempt ran before its independent contract
checker file was available. The producer stayed sealed; the reader was
continued without another producer or native call. Both verification attempts
are retained. No numerical/model failure is being reclassified as a healthy
run in either repair.

The smoke identity records honestly bind the WIP complete source hashes plus
the R165 predecessor commit; they do not prove that the new source existed
inside R165. Before formal production, freeze the actual committed source,
unchanged common PE, compiler/build manifest, Gurobi 13.0.2 DLL and all twelve
commands. Keep the WIP smoke identity as historical diagnostic evidence.

## Formal campaign reader and restrictions

The adapter explicitly recognizes the actual C166 algorithm identity,
checks candidate flag parameters, uses the independent C166 model checker,
keeps AP off and rejects leftover state/RN/theta columns. It retains the
inherited native log/source, physical fleet, cutoff-complement and full-cover
qualification. The new representation is not used to waive source or LP
quality checks. The common Start/own-H source remains each run's own producer;
the archived qualification parents are absent from formal argv.

The prospective order alternates B/C166 by fixed input index, not outcomes;
all inputs/Seed are already exposed. The twelve caps sum to 21,600s,
reservation sums to 25,200s, and Threads/MIPThreads/Seed/H-seed are fixed.
The campaign checks >=9h remaining at formal entry and does not set a native
node limit. All formal runs must remain serial and use the same common PE.

I also read back the later formal-clock correction: each formal position
starts a fresh Python `arm(position)` subprocess, so the inherited OS-wrapper
birth clock includes that arm's imports/startup and cannot accumulate earlier
arms' process age. The parent records the actual child PID and creation
FILETIME, waits serially, and implements the separate cap+900 fault watchdog
with an identity-checked process-tree termination. The producer's own cap,
cap-2 hard stop and inherited cap-6 native allocation are unchanged. Each
new arm checks that all remaining cap+300 reservations and at least 7,200s
for manuscript/review still fit. Source and helper hashes are frozen and
read back before formal execution. The multi-arm same-wrapper smoke clocks
remain diagnostic facts and are excluded from performance comparisons.

One operational limitation to retain: `panel()` conservatively refuses an
existing destination lacking a qualified endpoint. If a healthy formal
producer finishes but a reader fails, continue `execute()`/`verify()` on
that sealed destination explicitly and account every verification attempt;
do not restart the producer or blindly recreate the panel. The initial
entry-budget assertion is an entry condition, so any later read-only resume
must not misrepresent a fresh formal entry. This is not a reason to shorten
or skip a frozen arm.

The static and finite diagnostics do not guarantee less total model size
or faster MIP. For example, the tiny C166 model has fewer binaries but more
total columns/rows than B. The single complete panel must determine the
actual tradeoff. B remains default regardless of diagnostic success.
