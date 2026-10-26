# Round 54 reproduction commands

Build a clean Gurobi-enabled tree:

```powershell
cmake -S . -B build/repro-round54 -DCMAKE_BUILD_TYPE=Release -DEXACT_EBRP_ENABLE_GUROBI=ON
cmake --build build/repro-round54 --config Release -j
ctest --test-dir build/repro-round54 --output-on-failure
```

Run the stable preset:

```powershell
build/repro-round54/ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-k1-am-sf --input <instance> --lambda 0.15 --T 3600 --time-limit <seconds> --threads 1 --mip-threads 1 --out <result.json>
```

Run the six semantic sentinels and regenerate concise manifests:

```powershell
python scripts/audit_round54_paper_preset.py
python scripts/generate_round54_manifests.py
```

Reproduce the P-GRB correction only with the original Round 53 official executable and its verified SHA-256:

```powershell
python scripts/run_round54_pgrb_fingerprint_preflight.py
python scripts/recertify_round53_pgrb.py
```

The fixed-interval summary runner is `scripts/run_round54_fixed_interval_stage.py`. Its frozen commands, official executable identity, and all entered compact rows are committed; native logs remain local and are covered by the local-raw inventory.
