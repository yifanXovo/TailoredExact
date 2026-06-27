# Hard V20/M3 Stress Instance Generation

`scripts/generate_hard_exact_stress_instances.py` defines a deterministic
regenerated engineering benchmark suite under `reference/hard_stress/V20_M3/`.
The local machine lacked a usable Python interpreter, so the same generation
logic was executed once through PowerShell to produce the committed instance
files and manifest.

Generation rule:

- `V=20`, `M=3`, `Q=30`.
- Station capacities are integers in `[20, 50]`.
- Initial inventories are in `[0, capacity]`.
- Targets are in `[1, capacity]`.
- Coordinates use a three-cluster metric pattern with the depot near the
  cluster center.
- Stress classes are `tight_T`, `high_imbalance`, and `moderate`.
- The manifest records seed, SHA256, total initial inventory, total target
  inventory, surplus/deficit counts, `T`, and rule version.

These instances are not historical paper targets. They are designed to expose
whether the exact phase can improve UB or close valid lower bounds when the
initial native HGA-TGBC incumbent is unlikely to be trivially optimal.
