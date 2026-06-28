# Full Frontier Ledger Merge Protocol

Focused interval evidence is not a full certificate by itself.  The merge
protocol is:

1. Start from a full-frontier final leaf ledger.
2. Accept a focused result only if its interval exactly matches a final leaf,
   or if a set of focused intervals exactly partitions that leaf.
3. Reject merge if there is any gap, overlap, instance mismatch, stale
   incumbent cutoff, or solver timeout masquerading as closure.
4. Preserve inherited lower bounds only when the interval scope remains valid.
5. Mark the full result certified only when every final leaf is bound-fathomed,
   empty, an exact BPC tree closure, or a proven infeasible interval cutoff MIP.

The round merge audit for `moderate_seed3301` is:

`results/v20_replication_round/ledger_merge_audit.csv`.

It closed nine leaves by exact cutoff-oracle infeasibility, but left interval
`1` unresolved because the oracle status was `time limit exceeded`.  The merge
summary is therefore `certificate_incomplete`, which is the intended behavior.
