# C4 design decision

## Diagnosed mechanisms

The retained completed Round 28 C3 rows launched 5,764 cold native
optimizations: 4,107 LPs and 1,657 terminal MIPs. Every call reread a model and
reran presolve; terminal MIPs consumed 80.4% of recorded LP-plus-MIP Work.
C3 produced zero LP-bound prunes. Of 2,027 unconditional splits with both
immediate child LPs observed, 723 (35.7%) gave no strict one-level controlling
bound gain.

The Moderate6301 evidence is pre-exact, not a C3 tree failure. Round 28 wrote
the generation trajectory before best extraction, the compact re-decoder, and
verification. Round 29 instrumentation further exposed that the optional local
re-decode repair starts a second generation-stagnation HGA; in Round 28 it had
no effective local wall stop and could consume the remaining process window.

## Selected candidate

C4 is a combined exact candidate:

1. the complete one-level LP-benefit split rule;
2. same-leaf in-memory model retention from a complete LP to the exact
   terminal parent MIP;
3. explicit restoration of every original integer/binary variable type before
   the MIP;
4. no LP basis submission and no native-tree reuse claim;
5. no MIP start;
6. the redundant local re-decode repair disabled uniformly by the frozen
   command.

## Exact algorithm

The complete improving Gini range is partitioned into four exact initial
intervals. Best valid lower bound selects the next leaf. The leaf's complete
LP is solved. An LP-infeasible leaf is empty and a leaf whose valid LP bound
cannot improve the independently verified incumbent is fathomed.

For an eligible midpoint split, both child LP relaxations must terminate with
valid complete statuses. Let `b` be the complete parent LP bound and let `b0`
and `b1` be the feasible child LP bounds, treating an infeasible child as
`+infinity`. C4 splits atomically if either child is infeasible or

`min(b0, b1) > b + 1e-7`.

Otherwise the split is declined, both speculative child models are discarded,
and the complete unsplit parent interval MIP is solved exactly. Structurally
ineligible leaves also receive an exact parent MIP. Interrupted solves leave
the leaf open.

Frozen geometry is four initial intervals, binary midpoint children, maximum
depth eight, minimum width `1e-4`, and certificate tolerance `1e-7`.

## Rejected alternatives

- Execution-only C3 retention was rejected as primary because it removes a
  reread but not the dominant terminal Work or low-value leaf creation.
- Unconditional C3 with basis transfer was rejected because no complete,
  audited row/column basis mapping was yet demonstrated.
- A new inequality family was rejected because the evidence points first to
  refinement and terminal creation; no broadly valid, ablated new family was
  established.
- Work-, time-, node-, retry-, family-, size-, and instance-based thresholds
  are forbidden and absent.

## Expected gain and fail-closed behavior

The split rule targets low-value refinement and terminal-MIP proliferation.
Same-leaf retention removes the second disk read/model creation for terminal
parents. If original variable types cannot be captured and restored, the LP
terminal gate is invalidated and C4 fails closed. If either child LP is
incomplete, no split decision is accepted. If a model fingerprint, coverage,
bound, lifecycle, or verifier gate fails, strict certification is rejected.

## Pre-freeze development decision

The prescribed six-instance, 60-second C3/C4 matrix completed 12/12 processes
without an external watchdog. C4 improved the valid LB on all five cases where
both exact trees ran. The largest early mechanism change was Tight3101:
C3 LB `0.00698721` versus C4 LB `0.0519281`, with five declined splits.
C4 reused 48 and 24 same-leaf models on V12_M1 and V12_M2, respectively.
On Moderate6301, C3's second HGA consumed the work window before exact-tree
entry, while the uniformly no-repair C4 entered the exact phase.

A separate Moderate4301 cold-versus-retained microbenchmark found 54/54 common
LP status/objective checks, 49/49 common split decisions, and 24/24 common
terminal-MIP status/model checks identical. No fallback prototype was needed.
The combined candidate above is therefore frozen without a threshold change.
