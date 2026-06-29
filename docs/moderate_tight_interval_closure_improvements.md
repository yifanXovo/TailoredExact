# Moderate and Tight Interval Closure Improvements

The sealed completion round tested whether automatic checkpoint oracle
diagnostics could close the remaining moderate and tight V20 stress rows.

## Observed Blockers

`moderate_seed3301`:

- checkpoint UB: `0.0491525526647`;
- checkpoint LB: `0.00921610362464`;
- unresolved intervals: `10`;
- one low-Gini checkpoint leaf `[0.0092161, 0.0093121]` was proven infeasible
  by the exact cutoff MIP in `0.6786467` seconds;
- the full row remains noncertified because other leaves remain open and no
  complete safe merge exists.

`tight_T_seed3102`:

- checkpoint UB: `0.600704436685`;
- checkpoint LB: `0.450176109171`;
- unresolved intervals: `1`;
- checkpoint leaf `[0.150176, 0.18772]` timed out in the exact cutoff MIP;
- the row remains noncertified.

`moderate_seed3302`:

- checkpoint UB: `0.195636206549`;
- checkpoint LB: `0.0252187297505`;
- unresolved intervals: `6`;
- checkpoint leaf `[0.0252187, 0.0259829]` timed out.

## Generic Next Improvements

The next useful work is not instance-specific tuning. The generic improvements
should be:

- full in-solver automatic oracle over all final leaves, not one checkpoint
  leaf after interruption;
- exact leaf partitioning when a cutoff MIP times out;
- safe full-ledger merge of all oracle-closed child leaves;
- longer oracle budgets for leaves whose compact MIP makes bound progress;
- exact BPC fallback only on the remaining small partition with exact pricing
  closure.

No result from this round uses a focused interval row as a full certificate.
