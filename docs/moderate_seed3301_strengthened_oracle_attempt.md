# moderate_seed3301 Strengthened Oracle Attempt

`moderate_seed3301` is now certified under the sealed unified command template.

Result:

- objective = LB = UB = `0.0491525526647`;
- status = `optimal`;
- `certified_original_problem=true`;
- `unresolved_intervals=0`;
- `open_nodes=0`;
- automatic interval oracle attempted `9` leaves and closed `9`;
- `oracle_bound_merged_leaves=9`;
- certificate basis: full Gini frontier completed by exact interval oracle
  infeasibility/bound certificates.

The main change from the previous round is that low-Gini final leaves are no
longer left with diagnostic timeout evidence.  The strengthened original compact
oracle adds Gini spread rows, penalty-domain inventory tightening, required
movement rows, and aggregate handling rows.  The remaining leaves that were
previously stuck now close inside the automatic full-ledger merge.

The row uses no archive scanning, known UB injection, external incumbent, or
manual focus interval.
