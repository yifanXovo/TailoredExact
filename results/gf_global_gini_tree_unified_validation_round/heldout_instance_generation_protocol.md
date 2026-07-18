# Held-out instance generation protocol

All six held-out V20/M3 instances were generated before any solver was run on them. The deterministic generator is `scripts/generate_hard_exact_stress_instances.py`, rule `hard_v20_m3_v1`, command:

```text
D:\msys64\ucrt64\bin\python.exe scripts/generate_hard_exact_stress_instances.py --suite round22-heldout
```

The preregistered unused seeds are tight-time 4101/4102, high-imbalance 4201/4202, and moderate 4301/4302. A targeted repository scan found no tracked benchmark evidence using those seed identifiers, so no advancement was necessary. The generator uses Python `random.Random(seed)`, a fixed three-cluster metric layout, V=20, M=3, Q=30, lambda=0.15, and the existing stress-specific inventory rules. The complete files and their SHA-256 values are frozen in `heldout_instance_manifest.csv` and `official_instance_manifest.csv`.

No difficulty, objective, runtime, root-gap, or algorithm-result filtering is permitted. No instance may be replaced. Stress labels are reporting metadata only and are prohibited from influencing algorithm resolution. All official solves pass `--T 3600`; the generator's tighter T labels for seeds 4101/4102 are retained as metadata, consistent with the existing Round 21 suite convention.
