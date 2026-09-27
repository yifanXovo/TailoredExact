Finite intra-route descent retained small-instance and D6 gains but lost D7 route quality. This stage adds a uniform finite cross-route tail neighborhood to the same24-seed descent, with complete decoded acceptance and the unchanged one-hot/AM/Gurobi proof. The preset remains isolated and default-off; no internal time/Work policy or instance switch is added.

Based on Round70 final1cf8381206edd5925eca0b03185ac1cd7dc99d2a (PR131). All measured code and parameters were frozen before experiments.

- E7/S12/N12 certify in1.172/2.125/1.422s; measured small gains are retained.
- D6 gap0.006996067 is42.9% below P-GRB; no cross-route candidate is generated there, so this is preservation of the existing gain.
- D7 executes298 cross-route checks and178 accepted moves. At1200s its gap0.074188972 is35.4% below DS, but only7.3% below P-GRB, below the frozen practical threshold.
- D7 K1-R gap is0.018286596. DS-X retains only9.5% of K1's P-relative advantage; this serious protection loss remains explicit.

Validation:49/49 new CTests;16 performance+6 original-problem micros,95 experiment Optimize calls/6600.169s;75 witness-model checks,12 actual accepted/observed Starts,18 conservative checkpoints and348 compact artifacts pass. Official P remains original compact/native defaults; all arms share Gurobi13.0.2, Threads1, Seed0, PresolveAuto, original tolerances and uniform logical processor2. No rational certificate is claimed.

The stage closes at a real resource checkpoint with2% weekly usage remaining. Nine unlaunched D3/C2/D4 runs are explicitly unmeasured; no in-flight run was shortened or replaced. No reset credit was authorized or used. Overall acceptance and independent confirmation are not established. See final_report.md, result_tables.md, stage_decision.json and reproduce.md under results/unified_exact_round71/. Remaining validation must use a new stage and separate outputs.
