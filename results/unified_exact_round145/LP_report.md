# Round145 finite matched LP decision

RN baselines are reused from sealed R144 production-capped sources; no baseline reoptimization. Every new optimization uses Seed0, Threads1, affinity4, serial timing and the complete original objective, old matrix, finite bounds, cutoff, support and g domain. Values are qualified numerical continuous optima, not Native MIP roots or rational certificates.

| Role | Addition to RN | Complete objective | Gain over RN | G | Weighted penalty | Runtime s | Rows / columns / NZ |
| --- | --- | --- | --- | --- | --- | --- | --- |
| K-20-S | joint | 0.222808939661 | 0.0276597872199 | 0.0512292189366 | 0.171579720724 | 0.436 | 7967 / 3758 / 43608 |
| K-35-U | joint | 0.234508197894 | 0.00641770096996 | 0.0729697193223 | 0.161538478571 | 2.675 | 25970 / 11177 / 173376 |
| K-35-U | NC | 0.23449076673 | 0.00640026980576 | 0.0729522881581 | 0.161538478571 | 1.878 | 25966 / 11177 / 173092 |
| K-35-U | O | 0.229222197461 | 0.00113170053681 | 0.0676837188891 | 0.161538478571 | 2.274 | 25970 / 11177 / 173305 |
| K-35-U | O_joint | 0.234508197894 | 0.00641770096996 | 0.0729697193223 | 0.161538478571 | 2.494 | 25976 / 11177 / 175691 |
| K-35-U | TS | 0.231536862694 | 0.00344636577044 | 0.0699983841228 | 0.161538478571 | 0.373 | 25968 / 11177 / 171274 |
| R-X20-S-T1 | joint | 0.396339103751 | 0.00657748753964 | 0.175198938992 | 0.221140164759 | 0.18 | 6737 / 2834 / 38187 |
| R-X20-S-T1 | NC | 0.389761616211 | 0 | 0.172107340457 | 0.217654275754 | 0.163 | 6733 / 2834 / 38023 |
| R-X20-S-T1 | TS | 0.396339103751 | 0.00657748753964 | 0.175198938992 | 0.221140164759 | 0.0509999 | 6735 / 2834 / 37554 |

K35 joint exceeds strong old O by0.00528600043315; O+joint matches joint to numerical precision. This is nested same-objective numerical information gain, not a global formulation dominance claim. NC and TS each improve K35; the joint exceeds NC alone by1.7431164196e-5. RX20 NC alone has zero objective increment, while TS gives the whole measured0.00657748754 joint increment; an NC-violating TS optimum is not a claim that all TS optima violate NC. K20, previously a no-PC RN-P role, now gains0.02765978722. No second no-PC role LP is needed to choose the candidate.

| Role | Compiled transported compact objective | Joint-source loss | Increment retained | PC NZ / RN columns |
| --- | --- | --- | --- | --- |
| K-35-U | 0.234508197894 | 2.75335310107e-14 | 0.999999999996 | 366 / 0 |
| R-X20-S-T1 | 0.396339103751 | 1.72639680329e-14 | 0.999999999997 | 49 / 0 |

Actual compiled interval arithmetic, full added-block row list, exact Fraction box-validity checks and Native coefficient/RHS readback are retained. NC/TS add6 source rows and zero columns beyond RN. One original-variable PC and zero RN columns remain in each formal compact model. The two compact LPs use the diagnostic actual floating source; production R140-down NC and outward TS rows have their own compiled oracle/readback, and the short actual production health confirms K20 objective agreement to≈5e-16.

The11 new standalone LPs comprise6 cells of the two-role NC/TS/joint diagnostic, strong O and nested O+joint, one former no-PC joint source and2 compiled compact solves. Saved primal/dual matrices retain all activities, signed coefficients, count ranges, quality and source costs. The initial baseline_residual labeling error was corrected from saved old points and matrices with zero Optimize; the amendment and original helper hashes are preserved.

Decision: route B, one uniform BASE+RN+NC+TS source projected once after current own H/initial root. No old stock/count add-on source, all-threshold products, repeat separation, floor grid or second full route A panel is opened.
