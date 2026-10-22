# Round129 finite candidate selection

Execution: **COMPLETE**. Decision: **`RECOMMEND_UNIFORM_MS2_AS_PAPER_CANDIDATE`**.

All five conditions were frozen before generation and evaluated on the complete qualified fixed panel. Four new problems supply the prospective denominator; PB-C20-B is a separate protection role. Seed repeats and shared comparisons are not independent new problems.

| Condition | Requirement | Result |
| --- | --- | --- |
| 1 | Retain per-Seed and both-Seed new-problem certification counts relative to MB | True |
| 2 | Add no per-Seed P-certified/method-open risk relative to MB | True |
| 3 | Retain every protected MB certificate and avoid a large slowdown at both Seeds | True |
| 4 | One new input has eligible triple deletion and material MS2/MB support at both Seeds | True |
| 5 | One new input gives direct MS2/P certification Wins at both Seeds | True |

Certificate counts by Seed: `{"0": {"P": 1, "MB": 2, "MS2": 2}, "1": {"P": 1, "MB": 2, "MS2": 2}}`. Both-Seed-certified problem counts: `{"P": 1, "MB": 2, "MS2": 2}`. P-certified/method-open counts: `{"0": {"MB": 0, "MS2": 0}, "1": {"MB": 0, "MS2": 0}}`.

New inputs meeting condition 4: `["UC-C20-U"]`; condition 5: `["UC-B20-B", "UC-C20-U"]`. Full per-Seed support, protection losses and all reverse directions are retained in the JSON decision, arms/pairs and support table.

| New input | Seed0 condition-4 evidence | Seed1 condition-4 evidence | Condition5 at both Seeds |
| --- | --- | --- | --- |
| UC-C15-S | BOTH_OPEN | BOTH_OPEN | False |
| UC-B20-B | both certified; saving 0.387s versus required 10.000s | both certified; saving 0.185s versus required 10.000s | True |
| UC-C20-U | both certified; saving 147.147s versus required 70.153s | both certified; saving 151.415s versus required 63.252s | True |
| UC-B30-S | BOTH_OPEN | BOTH_OPEN | False |

Displayed times are rounded; all threshold decisions use the unrounded authority.

Recommend one uniform MS2 configuration as the sole method candidate for the next paper revision. Its exact version map is original E2 `--round127-mode mb` to original E2 `--round127-mode ms2`, with only triple support omitted for every input. Adoption requires the user's choice: repository defaults, current full-M-B paper identity and historical tables remain intact. A migrated paper must replace every claimed main-method performance table with measurements of that same MS2 version, including the R122 larger roles and R126/R127/R128 historical layers if retained as main-method evidence; old MB numbers cannot be relabelled. This finite panel does not establish V50/V60 safety. No migration experiment is executed here.

Deletion of valid rows at an identical scope preserves the physical integer optimum and can only weaken or preserve the mathematical optimal LP lower bound. Certification time has no corresponding monotonicity. This decision uses complete certificates and producer clocks, with null open times and ratios only on both-certified intersections.
