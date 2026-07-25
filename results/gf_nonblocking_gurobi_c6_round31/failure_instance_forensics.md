# Round 31 failure-instance forensics

## Scope and method

This audit is read-only over the frozen Round 30 evidence. It covers the four
C5 final-LB losses against P-GRB, all specified AUC regressions, and the
retained C0 advantages on `moderate_seed3302` and `tight_T_seed5102`.
Historical result files were not modified.

The reconstructed event histories join complete parent and child LP ledgers,
split decisions, partial native targets, global-bound events, terminal MIP
calls, leaf coverage, and native logs. C5-minus-P-GRB deltas below use the
common independently verified upper bound and complete observed common-window
AUC.

## Aggregate structural findings

Across the 17 primary C5 rows:

- C5 made 55 explicit parent-LP selections and 305 two-child lookahead
  decisions, for 610 child LP calls and 779.8957 child-LP Work.
- After 30/55 parent LPs, the selected leaf was no longer strictly below the
  next open leaf and could have been safely requeued before child lookahead.
  This would have deferred 60 child calls and 184.3732 Work immediately.
- On the other 25/55 parent-LP selections, a finite higher next-leaf bound
  existed and supplied a parameter-free native parent target. Thus every
  observed parent-LP selection had a mathematical parent-first transition.
- C5 opened 94 small-gain target phases. Eight closed exactly. All 86 target
  attainments that remained open were followed by a mandatory delayed split
  even though the strengthened parent had caught the frozen child bound
  within tolerance. These 86 splits had zero immediate global-LB gain.
- Eighty-two no-gain parents entered terminal MIP processing. They consumed
  7,079.3107 of 7,214.2386 total terminal-MIP Work (98.13%); 12 ran until the
  process deadline.
- The ten critical instances account for 63 terminal MIP calls, 4,004.5581
  Work, and eight deadline-blocking terminal leaves.

The evidence rejects universal child-first processing and the C5 forced
delayed split. It supports a parent-native-first frontier-balancing state
before child lookahead.

## Instance diagnoses

### V12_M1

C5 and P-GRB both certify, but C5 AUC is lower by `0.08260149` and runtime is
54.153 seconds versus 34.856 seconds. Terminal work is not the dominant
failure. The loss is decomposition overhead: repeated parent/child LP work,
seven target phases, four attained-and-forced splits, and multiple small
terminal closures reconstruct proof structure that P-GRB keeps in one native
tree.

Classification: child-lookahead dominated; forced-delayed-split overhead;
native-tree fragmentation.

### V12_M2

Both arms certify, but C5 AUC is lower by `0.06134825` and runtime is
228.234 seconds versus 169.249 seconds. C5 used 17 target phases, 16 forced
post-target splits, and 33 terminal MIPs totaling 336.013 Work. The endpoint
is exact, but the proof path is fragmented and slower.

Classification: forced-delayed-split overhead; repeated exact-closure
fragments; native-tree fragmentation.

### high_imbalance_seed6202

C5 loses final LB by `0.39586774` and AUC by `0.11912494`. Parent LP
processing already made two of four selected root intervals safe to requeue.
Instead, C5 proceeded through child lookahead and launched a no-gain terminal
MIP on `L3`. That leaf was no longer the unique lower-bound bottleneck, yet it
consumed 238.322 seconds, 603.148 Work, and 700 nodes to the deadline.

The root relaxation itself used only 19.48 Work; most effort was native
cut-loop and branch-and-bound continuation. This is the clearest
noncontrolling-leaf blocking failure.

Classification: no-gain parent blocking; insufficient interleaving;
child-lookahead dominated; expensive branch-and-bound continuation.

### moderate_seed3302

C5 beats P-GRB in final LB by `0.01053692` and AUC by `0.05013036`, but it
does not recover C0's final LB: C0 exceeds C5 by `0.02001647`. All three
explicit parent-LP selections were safe to requeue before lookahead. C5 later
spent 401.139 terminal Work across eight calls.

C0's advantage comes from broad parent-native processing and partial-bound
harvesting, not from a different canonical interval formulation. The
transferable event is the valid native bound; C0's 30-second quantum is not
transferable.

Classification: insufficient parent-native progression; avoidable early
child lookahead; fragmented terminal closure.

### moderate_seed5302

C5 has a small final-LB win (`0.00107391`) but an AUC loss
(`0.00155061`). It immediately partitions the controlling region and then
spends 549.607 Work in two depth-one no-gain terminal MIPs, one of which
blocks for 180.331 seconds.

The initial parent had a finite next-leaf target, so native parent
progression could precede the split. Once split, neither child exposed a
useful next target in the frozen C5 order. The failure is premature
partitioning followed by two expensive native proofs rather than one
balanced parent progression.

Classification: immediate-split dominated; no-gain child blocking;
expensive branch-and-bound continuation.

### moderate_seed6301

C5 wins final LB by `0.06153769` but loses AUC by `0.04792147`. Two deep
no-gain terminal leaves consume 290.169 Work. Each explores only one node,
while the logs report 2,756 cuts in total. This is root/cut-loop concentration
rather than a broad native tree. Two root parent selections could have
deferred four child LPs and 47.426 Work.

Classification: expensive root/cut-loop processing; no-gain blocking;
avoidable child lookahead; final stagnation.

### tight_T_seed4101

C5 loses final LB by `0.06101649` and AUC by `0.09543943`. Root leaf `L1`
was safe to requeue after its parent LP, but C5 performed both child LPs and
then a no-gain terminal MIP. That MIP consumed 283.155 seconds, 590.957 Work,
and 2,803 nodes to the deadline.

Classification: no-gain parent blocking; insufficient interleaving;
child-lookahead dominated; expensive branch-and-bound continuation.

### tight_T_seed5102

C5 loses final LB by `0.01745164` and AUC by `0.04196624`; C0 exceeds C5
by `0.11068551` final LB and `0.24200181` observed AUC. After the `L2`
parent LP, `L2` was already above the next open interval. C5 nevertheless
solved both children, observed zero disjunction gain, and launched a
275.039-second, 476.049-Work, 3,502-node terminal MIP.

C0 instead returned valid partial bounds from multiple root intervals to its
scheduler. Its advantage establishes the value of broad partial-bound
interleaving, while its time quanta and attempt policy remain forbidden.

Classification: canonical no-gain noncontrolling-parent block; insufficient
interleaving; expensive branch-and-bound continuation.

### tight_T_seed5103

C5 loses final LB by `0.00643573` and AUC by `0.01323736`. Root leaf `L2`
was safe to requeue after its LP. C5 continued into a no-gain terminal MIP
that used 262.226 seconds, 482.104 Work, and 2,755 nodes to the deadline.

Classification: no-gain parent blocking; insufficient interleaving;
child-lookahead dominated; expensive branch-and-bound continuation.

### tight_T_seed6102

C5 wins final LB by `0.05188126` but loses AUC by `0.00479441`. Two parent
selections could have deferred four child LPs totaling 79.850 Work. Three
deep no-gain terminal calls consume 222.933 Work while exploring one node
each and reporting 2,418 cuts. The loss is concentrated in root/cut-loop
processing and delayed bound delivery.

Classification: expensive root/cut-loop processing; no-gain blocking;
avoidable child lookahead; final stagnation.

## LP and model patterns

The external complete interval model is materially larger than the plain
compact MILP. Average retained sizes on the audited subsets are:

| size | P-GRB rows/cols/nonzeros | C5 rows/cols/nonzeros |
|---|---|---|
| V12 | 1,272 / 604 / 5,186 | 8,788 / 841 / 86,484 |
| V20 | 5,067 / 2,113 / 23,343 | 11,912 / 3,376 / 67,369 |
| V50 | 27,653 / 10,536 / 135,619 | 93,018 / 18,189 / 665,820 |

C0 and C5 use matching complete interval-model families on shared instances,
so C0's retained advantages cannot be attributed to a smaller mathematical
leaf formulation. P-GRB benefits from one continuous native tree. C5 pays
multiple presolve, root, cut-loop, and branch-and-bound starts across interval
models. Same-leaf model-object reuse does not prove preservation of cuts,
pseudocosts, basis, presolve state, incumbents, or the native tree.

The failure set contains two distinct native costs:

- high-imbalance and V20 tight-T deadline leaves spend most Work after the
  root in branch-and-bound continuation;
- V50 `moderate_seed6301` and `tight_T_seed6102` spend hundreds of Work at
  one explored node with large cut counts, consistent with expensive root
  cut loops and degeneracy.

No retained primal/dual vector, binding-row-family, reduced-cost, or
fractional-flow export is complete enough to support a new inequality family.
The broad evidence points to scheduling and premature partitioning, not a
uniform missing cut. Round 31 therefore adds no new cut family.

## Design consequence

The evidence-led primary hypothesis is a universal
`OPEN_NATIVE_BOUNDED` state with parent-native-first processing:

1. merge a complete parent LP bound;
2. requeue immediately if the leaf no longer occupies the lowest frontier;
3. otherwise process its native parent MIP to the next strictly higher
   relevant open-leaf bound or verified cutoff;
4. requeue on target attainment without claiming native-tree continuation;
5. perform child lookahead only when no higher frontier target exists and the
   leaf remains controlling;
6. split only when the child disjunction still has current normalized gain
   at least `rho=0.01`;
7. never force a split after the parent catches the child bound;
8. use exact closure only when no finite higher scheduling milestone or
   useful current split remains.

This rule uses no new tunable parameter.
