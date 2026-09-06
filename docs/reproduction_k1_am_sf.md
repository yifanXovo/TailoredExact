# Reproducing K1-AM-SF

Round 55 uses the first-class controller implementation and the corrected
incumbent-epoch cache identity. Historical pre-fix performance rows must not be
mixed with this corrected baseline.

## Build

```powershell
cmake -S . -B build/repro-round55 -DCMAKE_BUILD_TYPE=Release -DEXACT_EBRP_ENABLE_GUROBI=ON
cmake --build build/repro-round55 --config Release -j
```

## Stable paper command

```powershell
build/repro-round55/ExactEBRP.exe --method gcap-frontier `
  --algorithm-preset paper-k1-am-sf --input <instance> `
  --lambda 0.15 --T 3600 --time-limit 300 `
  --threads 1 --mip-threads 1 --out <result.json>
```

The aliases `k1-am-f0` and `paper-k1-am-f0` must produce the same semantic
configuration. Use `scripts/run_round55_stable_requalification.py` for the
eleven frozen sentinels. That audit reuses completed matching rows and keeps
bulky raw files under the local-only evidence tree.

The Round 55 semantic audit is reproduced by
`scripts/run_round55_stable_requalification.py`. Fixed-interval formulation
rows use `scripts/run_round55_fixed_interval_stage.py`; the full controller
integration uses `scripts/run_round55_k1_integration.py`. These scripts bind
every resumable row to the input hash, final executable hash, preset/policy,
cap, and artifact directory.

## Plain Gurobi contextual benchmark

```powershell
build/repro-round55/ExactEBRP.exe --method gurobi --plain-baseline `
  --input <instance> --lambda 0.15 --T 3600 --time-limit 3600 `
  --threads 1 --mip-threads 1 --gurobi-seed 0 --gurobi-presolve -1 `
  --gurobi-model-export <model.lp> --out <result.json>
```

Strict P-GRB evidence additionally requires a pre-frozen expected fingerprint,
actual readback equality, lifecycle validity, independent solution checking,
and objective recomputation. Round 55 uses the reusable
`scripts/pgrb_fingerprint_pipeline.py` through the hard-gated sealed-panel
runner, keeping discovery separate from benchmark performance.

## Tests and evidence

```powershell
ctest --test-dir build/official-round55-final-6d0818126 --output-on-failure
python scripts/run_round55_stable_requalification.py `
  --executable build/official-round55-final-6d0818126/ExactEBRP.exe
```

The complete commands, hashes, gate decisions, and local-raw inventory are in
`results/gf_k1_am_sf_station_state_chain_round55/reproduction_commands.md` and
the final evidence inventory.

The Round 55 K1 evidence consists of 34 initial 1,800-second rows and 10
conditional 3,600-second rows. Re-run the same panel only from the frozen
manifests; do not open the sealed runner because
`k1_integration_decision.json` records `gate_pass=false`.

## Round 56 paper-candidate screen

Round 56 uses the source-frozen executable under
`build/official-round56-paper-dataset-75e585211/`. The exact executable hash,
all 50 commands, scenario identities, operational T values, and 3600/7200
process caps are recorded in
`results/gf_paper_benchmark_time_horizon_round56/execution_manifest.json`.

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
D:\msys64\ucrt64\bin\python.exe scripts\run_round56_official.py --run
D:\msys64\ucrt64\bin\python.exe scripts\round56_route_archive.py --all-completed
D:\msys64\ucrt64\bin\python.exe scripts\analyze_round56_results.py
D:\msys64\ucrt64\bin\python.exe scripts\run_round56_repeatability.py --run
```

The runner permits only one official optimizer process at a time. Do not add
known bounds, archive scanning, imported incumbents, focus-only modes, prior
interval bounds, alternative presets, or instance-specific settings. Route
archiving rereads the native witness and does not invoke another optimization.

## Round 58 CitiBike443 paired benchmark

Round 58 uses the source-frozen executable at
`build/official-round58-citibike443-8ec0e1e15/ExactEBRP.exe` with SHA-256
`0f7570d4c421b9d2f4cb2941bf4d426fe396a25b26ef1c0618df0f3a675333f2`.
Expected P-GRB model fingerprints were frozen before timed benchmark runs.

```powershell
& 'D:\msys64\ucrt64\bin\python.exe' scripts\run_round58_paired_benchmark.py --preflight
& 'D:\msys64\ucrt64\bin\python.exe' scripts\run_round58_paired_benchmark.py --stage screen
& 'D:\msys64\ucrt64\bin\python.exe' scripts\run_round58_paired_benchmark.py --stage long
& 'D:\msys64\ucrt64\bin\python.exe' scripts\run_round58_paired_benchmark.py --stage near
& 'D:\msys64\ucrt64\bin\python.exe' scripts\finalize_round58_evidence.py
```

The runner is hash-resumable and permits one optimizer process at a time. Do
not rerun the fingerprint-discovery preflight after the benchmark-start flag is
set. The complete commands, hashes, staged rules, and local-raw inventory are
under `results/gf_citibike443_k1_vs_pgrb_round58/`.
