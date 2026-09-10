# Round 56 source of truth

- Base: `06b4c0634cbb85d3440be88511c736dd3282fdc9` / `412de9e5c5e5e2c90d18634abe83ebf72b0abc1a`; draft PR [#113](https://github.com/yifanXovo/TailoredExact/pull/113) remains untouched.
- Branch: `codex/round56-paper-benchmark-time-horizon`.
- Evidence: `results/gf_paper_benchmark_time_horizon_round56/`; reference data: `reference/round56_paper_candidate/`.
- Algorithm: corrected K1-AM-SF / `paper-k1-am-sf`; no research candidate.
- Operational horizons: 1800, 3600, 10800, and 18000 seconds.
- Common statistical horizon: 3600 seconds; exactly nine frozen V>=20/T=18000 rows may extend to 7200 seconds.
- Authoritative data are the frozen descriptors, official result JSON, one native final witness per available verified solution, independent archive verification, and compact hash inventories.
