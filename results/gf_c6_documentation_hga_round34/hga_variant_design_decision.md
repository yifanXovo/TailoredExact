# HGA startup variant design decision

## Frozen baseline

`C6-HGA-FULL` is unchanged: native HGA-TGBC, seed 20260626, population 24,
current decoder/operators, generation-stagnation stopping, and 2,000 completed
generations without strict global-best improvement. Local exact-phase
re-decoding remains disabled. It is the validated C6 mainline regardless of
Round 34 exploratory results.

## Historical trajectory analysis before Round 34 solver results

All 18 frozen Round 33 C6 generation logs were replayed as if the identical
run had stopped after 250, 500, or 1,000 generations without a strict global
best improvement. The resulting final-fitness matches to HGA-FULL were:

| Candidate stagnation | Matches FULL final fitness | Misses a later improvement |
|---:|---:|---:|
| 250 | 15/18 | 3/18 |
| 500 | 17/18 | 1/18 |
| 1,000 | 18/18 | 0/18 |

The 500 candidate misses the later improvement on the Round 33 M1/Q20
moderate identity. The 250 candidate also misses later improvements on the
M3/Q20 high-imbalance and M3/Q30 moderate identities. These facts come only
from frozen historical logs; no new short solve was used to choose a favorable
setting.

## Predeclared decision

Round 34 retains exactly one reduced setting:

- `C6-HGA-LIGHT`: same HGA in every respect, with the uniform stagnation count
  reduced from 2,000 to **1,000**.

No second reduced setting is justified: 500 already has a known loss and 1,000
removes half of the guaranteed post-improvement tail while reproducing all 18
historical final HGA fitness values. The same setting applies to every V, M, Q,
and scenario. Mutation, crossover, population, selection, decoder, repair, and
seed are not tuned.

## Predeclared development set

The seven identities in `hga_development_manifest.csv` cover M1 high,
moderate, and tight; M2 moderate and tight; and M3 high and tight. They balance
Q20/Q30 as four versus three. The development work runs heuristic-only FULL,
LIGHT, and the existing deterministic SIMPLE constructor to answer two gates:

1. Does LIGHT reproduce the verifier-passed FULL incumbent quality on this
   balanced subset while reducing the measured generation tail?
2. Does SIMPLE produce a verifier-passed original solution on every identity?

The set is not used to alter the LIGHT count per instance or to modify any C6
exact decision.

## Official freeze rule

If FULL and LIGHT both pass independent verification on all seven development
identities, LIGHT-1000 is frozen for the official matrix even if one incumbent
is weaker. If SIMPLE passes all seven, it is also frozen as a uniform official
arm; otherwise it is documented and excluded. The freeze records commands,
instances, hashes, source, executable, and fingerprints before official
results. No startup arm is dispatched by instance characteristics.

The final version of this document will append development measurements and
the official inclusion decision; the rules above were written before any new
Round 34 solver result.
