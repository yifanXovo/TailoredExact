# BPC Leaf Closure Diagnosis

BPC fallback remains non-core for the current sealed evidence.

In this round:

- `moderate_seed3301`: BPC fallback attempted `2` remaining leaves, closed `0`;
- `tight_T_seed3102`: BPC fallback was available but did not close leaves;
- `high_imbalance_seed3201`: BPC fallback was available but did not close leaves.

No row used BPC fallback as lower-bound evidence. Generated route/column
evidence, if any, remains UB-only and verifier-gated. The next BPC task is to
make interval-specific exact pricing closure operational on the same leaf model
used by the frontier/oracle, or keep BPC fallback diagnostic.
