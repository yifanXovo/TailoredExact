# BPC Tree Plateau Diagnosis

BPC tree and pricing are not the dominant bottleneck in the current targeted
round.

Evidence:

- V12 M1 relaxation-only 1200s certifies without entering BPC.
- V12 M1 fallback 300s starts one node and one pricing call, but because the
  row spends less time on relaxation, final LB is worse than the relaxation-only
  300s row.
- V20/M3 fallback rows did not produce closed tree evidence; their summaries
  still show zero useful pricing time and unresolved intervals.

The current fallback mechanism is certificate-safe because incomplete BPC
closure is not used as lower-bound proof. Its diagnostic value is that it
confirms BPC is not yet the next bottleneck for these rows. The main unresolved
issue is still interval relaxation strength and scheduling.
