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

## Relaxation Closure Round Update

The next round added V20-safe multi-station cover cuts, station residual domain
cuts, and an optional compact-flow relaxation.

| case | previous 300s gap | best new gap | row |
|---|---:|---:|---|
| `high_imbalance_seed3201` | 0.122744236967 | 0.0682096293371 | `miplight_300s` |
| `high_imbalance_seed3202` | 0.100084871258 | 0.0544001976401 | `miplight_300s` |
| `tight_T_seed3101` | 0.968587506517 | 0.333333333333 | `miplight_300s` |
| `tight_T_seed3102` | 0.218955510650 | 0.168318012854 | `lp_1200s` |

The `high_imbalance_seed3202_miplight_1200s` row ends with LB
`1.69375051373`, UB `1.74931345205`, and gap `0.0317627113992`.

The compact-flow `mip-light` variant is the strongest new V20 lower-bound
component, but it is not uniformly dominant. It worsens the moderate rows in
300s. BPC fallback remains diagnostic: it either does not trigger before the
relaxation budget is consumed or does not close exact pricing.
