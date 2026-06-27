# Relaxation Plateau Diagnosis

## Regenerated V12

V12 M2 remains certified with the original paper-core 300s command and native
HGA-TGBC UB:

- objective/LB/UB: `0.718504070755`
- certificate: relaxation-only full-frontier certificate
- unresolved intervals: `0`
- pricing calls: `0`

V12 M1 now certifies under a 1200s paper-core run:

- objective/LB/UB: `0.357200583208`
- runtime: `474.6660521s`
- bound time: `460.8823549s`
- pricing calls: `0`
- certificate: relaxation-only full-frontier certificate

The 300s V12 M1 rows remain noncertified, so the closure is time-budget
sensitive but no longer structurally blocked.

## V20/M3

All six hard-generated V20/M3 rows remain noncertified. The new continuous
vehicle-indexed relaxation is active in these rows, but the relaxation lower
bounds still do not reach the verified incumbent cutoffs. The best observed
V20/M3 improvement is `high_imbalance_seed3202`, whose gap decreased from about
`0.12395` in the previous stress summary to `0.10008` at 300s and `0.08167` at
1200s.

The next bottleneck is stronger large-instance-valid lower bounds. Since
route-mask enumeration is not certifying for V20/M3, future work should target
stronger vehicle-indexed flow/capacity cuts, station residual covers, and
deterministic parallel relaxation.

## Relaxation Closure Round Update

The follow-up relaxation-closure round confirms that lower-bound closure remains
the active bottleneck.

V12 M1:

- canonical 300s: LB `0.332675660948`, UB `0.357200583208`, gap
  `0.0686586848205`;
- critical pre-split 300s: LB `0.329549359470`, gap `0.0774109143105`, worse
  than canonical scheduling;
- 2-worker 300s: same LB/gap as canonical scheduling;
- 600s: certified at objective `0.357200583208` after `481.106s`;
- BPC fallback 300s: one node and one pricing call, but no exact closure and a
  weaker LB `0.331296710948`.

V20/M3:

- multi-station route-duration cover cuts are valid but inactive under current
  `T=3600` stress data;
- station residual cuts add safe domain evidence but are not the main driver;
- `mip-light` compact-flow relaxation materially improves three of six 300s
  stress gaps: `high_imbalance_seed3201`, `high_imbalance_seed3202`, and
  `tight_T_seed3101`;
- `high_imbalance_seed3202_miplight_1200s` reaches gap `0.0317627113992`,
  improving on the previous 1200s gap `0.081673871528`.

The next bottleneck is per-interval relaxation variant selection. `mip-light`
is strong on high-imbalance rows but weakens moderate rows and `tight_T_seed3102`
in short runs.
