# Prospective JDS-C implementation and startup qualification

The initial two diagnoses are complete. Based on their explicit residual
insertion opportunity, admit one uniform physical closure after the existing
JDS-X startup. The new default-off preset is
research-round76-vds-physical-closure (JDS-C). It inherits JDS-X, not the
separately null QDS-X pipeline, and uses the already-qualified proposal APIs.

## Exact scope of this heuristic extension

At each current verified physical witness:

1. Obtain the R73 best gain/duration proposal over every legal new/unvisited
   single or equal pickup/drop insertion. This API finds a proposal iff that
   declared insertion neighborhood contains a strict improving F move.
2. Obtain the R75 minimum-F proposal over the complete declared physical
   single/pair quantity neighborhood on currently served stations.
3. If neither exists, report joint neighborhood exhaustion. Otherwise choose
   the smaller proposed original F, breaking exact objective ties in favor of
   insertion, rebuild the complete routes and verify physical/original-objective
   agreement. Adopt only improvement above1e-12, with1e-10 objective agreement.
   Repeat. No accepted move is neutral. A numerical mismatch retains the
   previous witness, is explicitly reported and fails experimental acceptance.

This is selection between two proposal rules, not a claim to choose the
minimum-F member of their union: R73 ranks insertion by gain/duration.
Exhaustion nevertheless means neither declared neighborhood contains a strict
improvement at the heuristic tolerance. Quantity deletion can make a station
eligible for later insertion at a different position/vehicle. Both APIs use
the current physical witness, never a historical route.

Every accepted step decreases the deterministically recomputed F of a finite
integer inventory state. No inventory can recur, so the process is finite.
There is no arbitrary pass count or internal CPU/Work cutoff. The sole global
deadline ends the whole algorithm and cannot trigger a fallback or restart.
All insertion/quantity/verification/trace work is paid. The original outer
incumbent threshold1e-10, original feasibility tolerances and full VD-S proof
remain unchanged. This extension does not yet add a served-pair relocation or
neutral workload-balancing rule; those hypotheses remain untested alternatives.

Correctness comes from original physical UB verification and unchanged complete
proof coverage. The design addresses a demonstrated physical handoff gap and
allows quantities to react to new service. Efficiency is not inferred from
the diagnostic: it requires actual self-starting and complete-method evidence.
No theoretical novelty is claimed for generic insertion/quantity descent.

## Newly admitted bounded work

- Implement one small composition module with initial/final physical snapshots
  and a replayable per-move trace, the actual CLI preset, metadata and explicit
  outer startup contract entry. Keep all existing defaults unchanged.
- Add one structural composition test and one actual native CLI test, bringing
  the expected full suite from56 to58. Existing proposal correctness oracles
  remain independent; check finite strict descent, both proposal types,
  original physical witnesses, joint exhaustion, invalid input and deadline.
- One isolated full qualification batch plus at most one repair revision.
  Per batch: configure<=60s, build<=600s, serial tests<=600s, <=150 Optimize.
  The existing suite uses111; the added tiny native CLI is expected to use18.
  Preserve all failed versions/costs. Do not compile alongside an optimizer.
- After qualification passes, ten fresh startup-only runs on this new binary:
  JDS-X and JDS-C for D3/C2/D4/D6/D7, each whole-process cap<=30s, total<=300s,
  zero Optimize. Freeze all input/source/binary/command identities before launch.
  Require unchanged first25 descent paths and independent replay of every new
  physical move, with explicit deadline or rejection outcomes retained.
- No complete MIP performance, long budget or independent confirmation run is
  admitted here. Review startup results and costs first, then separately freeze
  a decisive common-budget comparison with fresh P and necessary K1 controls.
  A better startup alone must not repeat R73/R74's unsupported full-method hope.

The R71/R74 practical criteria and overall goal are unchanged. This is exposed
development evidence; no independent confirmation has been opened. Complete
this substantive implementation/verification stage and publish its own draft
PR after meaningful results, without merging main or claiming overall success.
