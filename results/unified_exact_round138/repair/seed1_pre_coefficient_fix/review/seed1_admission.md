# Independent limited Seed1 admission

Decision: **ACCEPT** the exact matrix SHA256
`d7c02b71910cb9b493eb29f28f1d321864704554839a03c2f477f1e92f2743fb`.
Reviewer: `/root/independent_review`; 2026-10-29 (Asia/Shanghai).
No native run or commercial library was started by this review.

The selection is conditional on all eleven completed new Seed0 positions and
the eight-pair report SHA
`e7cad03e11f71ea843cedfabbe05dee599042a84a4669af39bfff46b259002bc`.
K20 tests the new certificate benefit (101.63538490096107s versus an open matched
1200s baseline). RB35-T2 tests the largest observed upper-endpoint regression,
0.05655759224710244, with worse signed gap despite higher L. K35 and RX35-T2
opposed endpoints remain in the primary report. This is finite selected
confirmation; it is not an independent validation sample or a runtime study.

| Position | Role | Method | Physical T | Lambda | Compute cap |
|---|---|---|---:|---:|---:|
| 1 | K-20-S | BASE | 5400 | 0.15 | 1200 |
| 2 | K-20-S | STOCK | 5400 | 0.15 | 1200 |
| 3 | R-B35-S-T2 | STOCK | 7200 | 0.055125275219827186 | 2400 |
| 4 | R-B35-S-T2 | BASE | 7200 | 0.055125275219827186 | 2400 |

The two roles are unique, both methods enter each pair, and the second pair
reverses method order. The four caps sum to 7200s. Actual CLI, panel, launch and
prereg use Gurobi Seed1; H remains the independent frozen 20260626 seed.
One thread, affinity 4, native `cap-6`, process cap and hard-stop `cap-2` remain.

I compared each actual command against its own Seed0 method after normalizing
only Seed and the fresh output directory: no other argument changed. Source,
input, identity, executable and matrix/selection/script hashes match. BASE uses
the unchanged frozen R137 PE and `baseline-r137` reader branch, including the
reviewed modern-lifecycle amendment; STOCK uses the same R138 PE/source and
four-row flag. AP/TC, controller, physical model and proof policy are unchanged.

All four destinations and fee labels were absent at review. No incoming Start,
incumbent, H solution, bound or tree path appears. The scaffold reuses the
unchanged primary arm function with only the admitted manifest lookup replaced,
so every method pays its independent own H, producer, proof and reader costs.
The primary source remains `83928377336a860acf78f684d1723a5040467bb5`.

The ledger had no open fee: charged new computation was 12182.041263099527s
and the remaining allowance was 74217.95873690047s, comfortably covering the
7200s maximum new caps. Nested H/LP/MIP/Work must not be charged again.
Keep Seed0 and adverse/open Seed1 outcomes, null open certificate times and
complete clock definitions. Later qualification, actual delivery and final
integration acceptance remain separate.
