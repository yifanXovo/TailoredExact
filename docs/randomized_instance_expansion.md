# Randomized Instance Expansion

## Generator

The deterministic generator is:

```powershell
python scripts\generate_capacity_inventory_variants.py
```

Round output:

```text
reference/generated_variants/
reference/generated_variants/manifest.csv
```

## Rule

For each base instance, the generator preserves network structure,
coordinates, distances, vehicle count, vehicle capacities, route-duration
convention, lambda convention, weights, and station ordering. It regenerates:

- station capacity in `[20, 50]`;
- initial inventory in `[0, capacity]`;
- target inventory in `[1, capacity]`.

The target is strictly positive to avoid ratio division issues. At least one
station has positive initial inventory. The text format remains parser
compatible.

## Manifest

The manifest records base path, base SHA256, output path, variant SHA256, seed,
V, M, total initial inventory, total target inventory, capacity and inventory
ranges, and generation rule version.

## Benchmark Scope

These files are regenerated engineering benchmarks. They are not historical
paper targets unless a future audit matches them to original benchmark files
and records source hashes.
