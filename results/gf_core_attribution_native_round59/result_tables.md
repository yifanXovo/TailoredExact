# Audited result tables

All performance caps are 120 seconds end to end. ✓ means an original-problem engineering certificate; its number is process time in seconds. Other entries are the terminal relative gap, **not solve time**. Bounds and absolute gaps are in the linked CSV. Diagnostic ✓ is explicitly restricted-state only.

| ID | Frozen role | P-GRB | K1-H | K1-S | Single-S |
| --- | --- | --- | --- | --- | --- |
| D1 | zero objective startup regression | ✓ 0.15 | ✓ 1.55 | ✓ 0.35 | ✓ 0.31 |
| D2 | positive objective long-T regression | ✓ 9.56 | ✓ 30.06 | ✓ 7.46 | ✓ 7.21 |
| D3 | historical major witness | 11.98% gap | 7.85% gap | 14.43% gap | 14.82% gap |
| D4 | historical strong positive control | 77.16% gap | 5.28% gap | ✓ 90.26 | ✓ 90.05 |
| D5 | V20 K1 advantage | 58.37% gap | 28.55% gap | 19.07% gap | 19.07% gap |
| D6 | V30 long-T lower-bound stagnation | 12.52% gap | 100.00% gap | 26.71% gap | 26.71% gap |
| D7 | V50 long-T mixed; long native routes | 62.39% gap | 100.00% gap | 70.97% gap | 70.94% gap |
| D8 | positive objective nonzero proof work | ✓ 2.06 | ✓ 2.52 | ✓ 1.57 | ✓ 1.54 |
| C1 | confirmation small shortage | 27.06% gap | 24.45% gap | 25.34% gap | 25.34% gap |
| C2 | confirmation V20 short horizon | 10.66% gap | 7.30% gap | 7.51% gap | 6.83% gap |

[Full-instance bounds, absolute gaps and work](full_instance_results.csv); [matched pairs](paired_results.csv).

## Current-model root LP pack-removal ablation

The removed-pack arm retains connectivity flow and cutoff-derived bounds; it is not original compact.

| ID | Model | LP bound | Work | Seconds | Presolved rows | Columns |
| --- | --- | --- | --- | --- | --- | --- |
| D2 | F0-minus-pack_connectivity_retained | 0.01923 | 0.0945 | 0.135 | 6234 | 3279 |
| D2 | F0 | 0.01923 | 0.1119 | 0.262 | 6576 | 3281 |
| D3 | F0-minus-pack_connectivity_retained | 0.02055 | 0.0457 | 0.091 | 2502 | 1344 |
| D3 | F0 | 0.02055 | 0.0727 | 0.122 | 3658 | 1346 |
| D4 | F0-minus-pack_connectivity_retained | 0.03993 | 0.0945 | 0.113 | 2509 | 1352 |
| D4 | F0 | 0.09395 | 0.1145 | 0.140 | 3546 | 1354 |

## Native execution and search (restricted states)

| ID | Arm | LB | Verified UB | Gap % | Certificate seconds | Work | Nodes | Iterations/node |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| D3 | F0 | 0.03863 | 0.04500 | 14.16 | — | 186.98 | 11076 | 113.5 |
| D3 | Monitor | 0.03863 | 0.04500 | 14.16 | — | 187.12 | 11082 | 113.5 |
| D3 | Pool | 0.03756 | 0.05660 | 33.64 | — | 187.36 | 12372 | 111.0 |
| D3 | Static | 0.04069 | 0.04500 | 9.57 | — | 180.76 | 20632 | 105.3 |
| D4 | F0 | 0.50634 | 0.50634 | 0.00 | 90.29 | 140.87 | 19132 | 35.3 |
| D4 | Monitor | 0.50634 | 0.50634 | 0.00 | 90.61 | 140.87 | 19132 | 35.3 |
| D4 | Pool | 0.50634 | 0.50634 | 0.00 | 70.52 | 114.04 | 15849 | 43.8 |
| D4 | Static | 0.50634 | 0.50634 | 0.00 | 93.77 | 145.24 | 21823 | 35.9 |
| D3 | Focus1 | 0.03811 | 0.04531 | 15.88 | — | 183.43 | 15492 | 136.1 |
| D4 | Focus1 | 0.45172 | 0.50634 | 10.79 | — | 168.32 | 15399 | 52.4 |

## Literal original compact/F0 (restricted states, separate same-build pairs)

| ID | Model | LB | Verified UB | Gap % | Certificate seconds | Work |
| --- | --- | --- | --- | --- | --- | --- |
| D3 | F0 | 0.03857 | 0.04500 | 14.28 | — | 183.81 |
| D3 | OriginalCompact | 0.04106 | 0.04500 | 8.76 | — | 176.11 |
| D4 | F0 | 0.50634 | 0.50634 | 0.00 | 92.58 | 140.87 |
| D4 | OriginalCompact | 0.12868 | 0.50634 | 74.59 | — | 193.89 |

## Frozen incumbent startup-exhaustion diagnostics (restricted states)

| ID | State | Model | LB | Verified UB | Gap % | Certificate seconds | Work |
| --- | --- | --- | --- | --- | --- | --- | --- |
| D6 | startup_state | F0-minus-pack_connectivity_retained | 0.13997 | 0.16647 | 15.92 | — | 249.57 |
| D6 | startup_state | F0 | 0.13821 | 0.18859 | 26.71 | — | 253.70 |
| D7 | startup_state | F0 | 0.19508 | 0.67124 | 70.94 | — | 284.33 |

## Observation cost

| ID | Samples | Sampling seconds | Eligible callback checks | Read failures |
| --- | --- | --- | --- | --- |
| D3 | 4 | 0.004422 | 130 | 0 |
| D4 | 4 | 0.004629 | 128 | 0 |

The unmonitored arm retains existing native progress telemetry. The added monitor never submits cuts, starts or hints. One timing pair does not estimate a statistically stable overhead distribution.
