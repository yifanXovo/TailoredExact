# Reproducing K1-AM-SF

## Build

```powershell
cmake -S . -B build/repro-round54 -DCMAKE_BUILD_TYPE=Release -DEXACT_EBRP_ENABLE_GUROBI=ON
cmake --build build/repro-round54 --config Release -j
```

## Stable paper command

```powershell
build/repro-round54/ExactEBRP.exe --method gcap-frontier `
  --algorithm-preset paper-k1-am-sf --input <instance> `
  --lambda 0.15 --T 3600 --time-limit 300 `
  --threads 1 --mip-threads 1 --out <result.json>
```

The aliases `k1-am-f0` and `paper-k1-am-f0` must produce the same semantic
configuration. Use `scripts/audit_round54_paper_preset.py` for the six frozen
sentinels. That audit reuses completed matching rows and keeps bulky raw files
under the local-only evidence tree.

## Plain Gurobi contextual benchmark

```powershell
build/repro-round54/ExactEBRP.exe --method gurobi --plain-baseline `
  --input <instance> --lambda 0.15 --T 3600 --time-limit 3600 `
  --threads 1 --mip-threads 1 --gurobi-seed 0 --gurobi-presolve -1 `
  --gurobi-model-export <model.lp> --out <result.json>
```

Strict P-GRB evidence additionally requires a pre-frozen expected fingerprint,
actual readback equality, lifecycle validity, independent solution checking,
and objective recomputation. The Round 53 correction can be reproduced with
`scripts/run_round54_pgrb_fingerprint_preflight.py` followed by
`scripts/recertify_round53_pgrb.py`; it requires the original Round 53 official
executable hash recorded in the correction manifest.

## Tests and evidence

```powershell
ctest --test-dir build/official-round54-b6784e930 --output-on-failure
python scripts/audit_round54_paper_preset.py
```

The complete commands, hashes, gate decisions, and local-raw inventory are in
`results/gf_k1_am_sf_inventory_route_round54/reproduction_commands.md` and the
final evidence inventory.
