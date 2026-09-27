# Round 58 CitiBike443 paired benchmark

## Decision

The frozen benchmark classification is `k1_am_sf_pgrb_advantage_mixed`.

- Completion: `round58_complete`.
- Dataset: `citibike443_paired_panel_complete`.
- Benchmark: `k1_am_sf_pgrb_advantage_mixed`.
- Runtime: `six_hour_extensions_used`.
- Scale: `scale_mixed`.
- Routes: `paired_native_route_archive_complete`.

The local `citibike443-regional-v1` family was regenerated and hash-validated before selection. The exact tested identifiers and parameters are frozen in `round58_complete_panel.csv`: a deterministic 50-scenario subset (30 structural and 20 matched route-horizon scenarios) of the 960-scenario family. The exact 910 unopened reserves are listed in `round58_reserve_inventory.csv`. Primary cells use the lower canonical landscape SHA-256, while each matched cell uses the other corresponding replicate under the frozen inventory rotation. Every V/geography/inventory/M/Q/T stratum required by the design is represented. No scenario was replaced after performance was observed, and K1-AM-SF was not tuned.

## Execution completeness

- Mandatory 3600-second arms completed: 100 / 100.
- Total fresh optimizer processes entered: 149.
- Maximum entered process cap: 21600 seconds.
- K1 certificates by 3600 seconds: 34 / 50.
- P-GRB certificates by 3600 seconds: 30 / 50.
- Scenario pairs entering the 10800-second stage: 19.
- Rows entering 16200/21600 seconds: 7 / 7.
- K1 final certificates: 34 / 50.
- P-GRB final certificates: 31 / 50.
- Both certified: 31 / 50.
- Among both-certified rows, faster counts K1/P-GRB/tie: 7 / 24 / 0.
- Among both-certified rows, lower-Work counts K1/P-GRB/tie: 28 / 3 / 0.
- Historical severe regressions: 1.
- Long-run material regressions: 0.
- False certificates / other correctness failures: 0 / 0.
- Required native route packages verified: 100 / 100.
- Material 3600-second fresh-rerun differences: 12.
- Total experimental compute: 783691.5662757 seconds and 1755117.2402471807 Work units.

Every optimizer run used the same frozen executable, Gurobi 13.0.2, one thread, Seed=0, and automatic presolve. P-GRB was the one original compact MILP with no HGA or imported route; K1 used the frozen `paper-k1-am-sf` preset. Longer runs were fresh processes authorized only by the frozen staged policy, and their screen time was not added to reported algorithm time.

## Paired outcomes

- `both_certified_k1_faster`: 7
- `both_certified_pgrb_faster`: 24
- `both_certified_tie`: 0
- `k1_only_certified`: 3
- `pgrb_only_certified`: 0
- `neither_certified_k1_better_bound`: 13
- `neither_certified_pgrb_better_bound`: 1
- `neither_certified_mixed`: 2
- `invalid_pair`: 0


The paired exact shifted time geometric means are 22.041705285223003 seconds for K1 and 7.1319259558439025 seconds for P-GRB, giving K1/P-GRB ratio 2.833486852971696. The shifted Work geometric means are 3.7388201561075602 and 9.528492029777532, giving ratio 0.4500948609454086. These exact metrics use only scenarios on which both methods strictly certified. Capped rows retain their qualified LB, independently verified UB, and explicit absolute/relative/scaled gaps; no invented solve time is assigned.

Among 16 pairs for which neither method certified and both qualified gaps were available at the largest common authorized horizon, smaller-gap counts K1/P-GRB/tie were 13 / 2 / 1. Their mean qualified relative gaps were 0.2691738341168901 for K1 and 0.33037949386660015 for P-GRB. Dominance counts using LB, verified UB, relative gap, and scaled gap jointly are reported in the paired outcomes above and row-by-row in `common_horizon_comparisons.csv`.

## Structural variation

### By V

- V=12: n=10, certificates K1/P-GRB=10/10, shifted exact time ratio=3.0304979584862908, shifted exact Work ratio=0.7133674470479672.
- V=20: n=10, certificates K1/P-GRB=9/8, shifted exact time ratio=2.4278604869477998, shifted exact Work ratio=0.26989906998635993.
- V=30: n=10, certificates K1/P-GRB=3/2, shifted exact time ratio=3.3137049425782674, shifted exact Work ratio=0.036494187502442876.
- V=50: n=10, certificates K1/P-GRB=2/1, shifted exact time ratio=10.157151668579937, shifted exact Work ratio=0.030400300127762132.
- V=8: n=10, certificates K1/P-GRB=10/10, shifted exact time ratio=2.5571887644756974, shifted exact Work ratio=0.9252000415524366.

### By geography

- geographic_regime=compact: n=25, certificates K1/P-GRB=16/15, shifted exact time ratio=3.0499008294610546, shifted exact Work ratio=0.5181513975182803.
- geographic_regime=regional: n=25, certificates K1/P-GRB=18/16, shifted exact time ratio=2.6445663526337606, shifted exact Work ratio=0.3944332095606801.

### By inventory

- inventory_regime=balanced: n=16, certificates K1/P-GRB=13/11, shifted exact time ratio=3.4078160593748414, shifted exact Work ratio=0.322650001541331.
- inventory_regime=shortage: n=18, certificates K1/P-GRB=9/9, shifted exact time ratio=2.0214989224786533, shifted exact Work ratio=0.8542034122867438.
- inventory_regime=surplus: n=16, certificates K1/P-GRB=12/11, shifted exact time ratio=3.1056372732701703, shifted exact Work ratio=0.37171613797658104.

### By geographic replicate

- replicate=1: n=22, certificates K1/P-GRB=15/14, shifted exact time ratio=3.1127895784879573, shifted exact Work ratio=0.3580762813190785.
- replicate=2: n=28, certificates K1/P-GRB=19/17, shifted exact time ratio=2.622392416693656, shifted exact Work ratio=0.543380432616833.

### By M

- M=1: n=14, certificates K1/P-GRB=14/14, shifted exact time ratio=3.3371422842129586, shifted exact Work ratio=0.8775580410031848.
- M=2: n=13, certificates K1/P-GRB=13/12, shifted exact time ratio=1.9230481536879045, shifted exact Work ratio=0.4476908213756976.
- M=3: n=10, certificates K1/P-GRB=4/3, shifted exact time ratio=3.9676335255204602, shifted exact Work ratio=0.10729014379281163.
- M=4: n=7, certificates K1/P-GRB=2/1, shifted exact time ratio=10.157151668579937, shifted exact Work ratio=0.030400300127762132.
- M=5: n=3, certificates K1/P-GRB=1/1, shifted exact time ratio=3.0511434245802804, shifted exact Work ratio=0.045737049490352184.
- M=7: n=3, certificates K1/P-GRB=0/0, shifted exact time ratio=None, shifted exact Work ratio=None.

### By fleet density V/M

- fleet_density_V_over_M=10.0: n=14, certificates K1/P-GRB=9/7, shifted exact time ratio=2.201133915837273, shifted exact Work ratio=0.21213526731875762.
- fleet_density_V_over_M=12.0: n=7, certificates K1/P-GRB=7/7, shifted exact time ratio=4.5739635415962505, shifted exact Work ratio=0.8257960359701301.
- fleet_density_V_over_M=12.5: n=7, certificates K1/P-GRB=2/1, shifted exact time ratio=10.157151668579937, shifted exact Work ratio=0.030400300127762132.
- fleet_density_V_over_M=4.0: n=3, certificates K1/P-GRB=3/3, shifted exact time ratio=2.8673247097779337, shifted exact Work ratio=0.9082415464773692.
- fleet_density_V_over_M=6.0: n=6, certificates K1/P-GRB=4/4, shifted exact time ratio=1.4770269605063413, shifted exact Work ratio=0.2778579744587578.
- fleet_density_V_over_M=6.666666666666667: n=3, certificates K1/P-GRB=2/2, shifted exact time ratio=4.165957190792771, shifted exact Work ratio=0.20594446027265353.
- fleet_density_V_over_M=7.142857142857143: n=3, certificates K1/P-GRB=0/0, shifted exact time ratio=None, shifted exact Work ratio=None.
- fleet_density_V_over_M=8.0: n=7, certificates K1/P-GRB=7/7, shifted exact time ratio=2.4347633127822412, shifted exact Work ratio=0.9325645580565648.

### By T

- T=10800: n=7, certificates K1/P-GRB=5/5, shifted exact time ratio=4.796199978318799, shifted exact Work ratio=0.5268434154189304.
- T=1800: n=8, certificates K1/P-GRB=6/4, shifted exact time ratio=0.683468936040348, shifted exact Work ratio=0.5430232076510476.
- T=18000: n=17, certificates K1/P-GRB=13/13, shifted exact time ratio=8.13870677259955, shifted exact Work ratio=0.3342138394338079.
- T=3600: n=18, certificates K1/P-GRB=10/9, shifted exact time ratio=0.8668233693579661, shifted exact Work ratio=0.5832103126299245.

### By Q

- Q=20: n=15, certificates K1/P-GRB=11/10, shifted exact time ratio=3.6037886556221, shifted exact Work ratio=0.45533349974503096.
- Q=30: n=35, certificates K1/P-GRB=23/21, shifted exact time ratio=2.5269041441612576, shifted exact Work ratio=0.4476214974141565.



## Interpretation and route evidence

Final results with a verified incumbent have native, non-post-optimized route packages under `solutions/<scenario>/<method>/`. Archive construction and independent verification time are excluded from solver time. Unequal final horizons are explicitly labeled; bound comparisons used the largest common authorized horizon rather than comparing a six-hour row directly with a one-hour row.

This paired panel supports only the stated frozen-panel qualification; it is not universal validation of the generated family. A second sealed panel drawn from the 910 untouched reserves is still required for a stronger paper benchmark claim. The recommended next step is to freeze that holdout selection before opening any additional solver result, then repeat the unchanged paired protocol.
