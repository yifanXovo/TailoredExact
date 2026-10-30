# Round142 matched conditional source LPs

The fixed R141 diagnostic ZIP is bound by SHA256 8552f9cbc2927e16b9f1e77f470a31651e4764c9034daa0e1fb0f04ee7a10d31. Six LP-floor conditional sources retain their actual MPS matrix, complete objective and ObjCon, physical input/support, g endpoints, cutoff, stock, old TC, parent TC2, selected count side and conditional child TC2. The inherited member comparison is in inherited_dependencies.json.

C explicitly completes the selected or propagated linear ranges. Every saved original optimum satisfies these new ranges. Each new build reads the original MPS fingerprint, checks the full saved point against its rows and variable bounds, and confirms its identical objective. This yields twelve range-control equality witnesses with zero C Optimize, under the inherited numerical policy. It does not say the linear rows are globally redundant or provide a rational optimum certificate.

S adds the missing opposite selected linear range and four CP facets. ALL adds all propagated linear ranges and CP. Both keep the original full matrix; their serialized MPS fingerprints, objective coefficients/constant, new row coefficients, senses and RHS are read back exactly before Optimize. Every new solve is continuous, explicit Gurobi Seed0 / Threads1 / Presolve -1 on affinity4, serial, with unchanged FeasibilityTol and OptimalityTol 1e-6 and cap90. No diagnostic result is installed into the online method.

| Role / side | Original L | S L | ALL L | S floor |
| --- | --- | --- | --- | --- |
| K35/low | 0.241539946 | 0.241586247 | 0.241586247 | 0.241586147 |
| K35/high | 0.240140105 | 0.240163916 | 0.240163916 | 0.240163816 |
| RB35-T2/low | 0.146301753 | 0.146558193 | 0.146558193 | 0.146558093 |
| RB35-T2/high | 0.150566942 | 0.150566942 | 0.150566942 | 0.150566842 |
| K20/low | 0.255556703 | 0.255628878 | 0.255628878 | 0.255628778 |
| K20/high | 0.268192585 | 0.268192585 | 0.268192585 | 0.268192485 |

| Role | Original min cover | S min cover | Gain | ALL - S |
| --- | --- | --- | --- | --- |
| K35 | 0.240140105 | 0.240163916 | 2.381078e-05 | 6.10622664e-16 |
| RB35-T2 | 0.146301753 | 0.146558193 | 0.000256440319 | 1.99840144e-15 |
| K20 | 0.255556703 | 0.255628878 | 7.21752899e-05 | 2.22044605e-16 |

The same gains apply to the conservative min-floor, because the same 1e-7 downward policy and unchanged cutoff are used and the weaker side does not change. Tiny negative deltas on the two unchanged strong sides (about 1e-15) are numerical equality, not a loss from retaining and adding valid rows. S raises all three genuinely weaker sources, rather than only the nonbinding strong side. ALL gives no further optimized gain.

| Role / side / mode | Range + CP rows | Added NZ | Build s | Solve s | Work |
| --- | --- | --- | --- | --- | --- |
| K35/low/selected | 1 + 4 | 1740 | 0.7637321 | 1.0942527 | 3.08860822 |
| K35/low/all | 259 + 520 | 269076 | 2.8321559 | 1.6425792 | 4.7048634 |
| K35/high/selected | 1 + 4 | 1740 | 0.7130309 | 1.0143174 | 2.97393843 |
| K35/high/all | 259 + 520 | 269076 | 2.7097637 | 1.5277322 | 4.63071938 |
| RB35-T2/low/selected | 1 + 4 | 2067 | 0.7255687 | 2.7671835 | 8.12551965 |
| RB35-T2/low/all | 191 + 384 | 201821 | 2.309473 | 2.279775 | 6.91861481 |
| RB35-T2/high/selected | 1 + 4 | 2069 | 0.7411513 | 2.6646055 | 8.01056905 |
| RB35-T2/high/all | 191 + 384 | 201849 | 2.2583984 | 2.7375363 | 8.51905335 |
| K20/low/selected | 1 + 4 | 1675 | 0.2104587 | 0.1851563 | 0.396660662 |
| K20/low/all | 273 + 548 | 238293 | 1.9632385 | 0.2587213 | 0.7838151 |
| K20/high/selected | 1 + 4 | 1677 | 0.211486 | 0.1835115 | 0.438537196 |
| K20/high/all | 273 + 548 | 238307 | 2.0600525 | 0.2610274 | 0.795899214 |

K/W and endpoint counts are in reports/LP.csv. The newly constrained endpoints become active: K35 low beta-endpoint 8, K35 high alpha-endpoint 9, RB low beta-endpoint 5 and K20 low beta-endpoint 7. The old corresponding endpoints were 10.4765, 8.39817, 12.0380 and 10, while the average selectors already respected the conditional counts. Endpoints explain the missing freedom; no-division mass residuals establish row feasibility near g endpoints.

All twelve new LPs pass their inherited quality gates. Every result binds canonical/solution SHA, actual DLL identity, measured helper SHA and source revision. The initial pure-Python tiny fixture constructor failed before any Optimize; the retained corrected run passes. Its two helper versions are preserved at delivery instead of retagging earlier S results. This fixture-only repair leaves product generation unchanged.

The candidate is frozen uniformly to S. Selected uses four CP facets per source; ALL uses 384--548, without extra objective value on these domains. The mathematical explanation is other parent-family products plus selected conditional propagation, not a separate new propagation principle. The new rows enter the two scoped proof sources only, with one canonical append retaining count, child TC2 and all CP/range expected rows under the same SHA. The parent and original Native MIP keep their prior structure; only newly paid source floors change.

This finite LP study establishes strict missing product freedom and small positive optimized source/cover increments. It is not a complete BRP hull, gap-closure or Native speed theorem. The full-method report retains all entered positive/adverse results and complete clocks separately.
