# V20/M3 Full Algorithm Stress Report

This report covers the V20/M3 hard-generated engineering instances under
`results/relaxation_bound_round/`.

## Metadata

New results correctly report:

`instance_scope = hard_generated_v20_m3`

These instances are not historical paper targets.

## Results

All six 300s improved-relaxation rows remain noncertified:

- `high_imbalance_seed3201`: gap `0.122744236967`
- `high_imbalance_seed3202`: gap `0.100084871258`
- `moderate_seed3301`: gap `0.130305288314`
- `moderate_seed3302`: gap `0.33021736845`
- `tight_T_seed3101`: gap `0.968587506517`
- `tight_T_seed3102`: gap `0.21895551065`

The representative 1200s row for `high_imbalance_seed3202` improved the gap to
`0.081673871528`, showing valid LB convergence but not closure.

## Interpretation

Native HGA-TGBC and local re-decode provide verified UBs. The V20/M3 failures
are lower-bound failures. The continuous vehicle-indexed relaxation is active
and certificate-safe, but still too weak for the hard stress set. BPC fallback
does not yet provide useful closed-node evidence before relaxation consumes the
budget.

Recommended next step: another targeted relaxation round, not broad benchmark
testing. Candidate work includes stronger station residual covers, vehicle flow
cover cuts, deterministic parallel interval relaxation, and a sharper policy for
when to stop splitting and run BPC.
