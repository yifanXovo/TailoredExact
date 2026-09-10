
# Reproduction commands

Run from `E:\codes\ExactEBRP`.  These commands perform data audit, generation and
validation only; none launches an optimizer.

```powershell
& 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts/generate_citibike443_regional_v1.py --phase audit-pilot
& 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts/generate_citibike443_regional_v1.py --phase full
& 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts/generate_citibike443_regional_v1.py --phase validate
```

The validation phase compiles `scripts/round57_parser_probe.cpp` together with
the current `src/Parser.cpp` at `-O0` and parses all 240 input files.  It does not
link or launch ExactEBRP optimization code.  It also regenerates the deterministic
dataset in a guarded temporary directory, requires byte equality for every file,
and removes only that temporary directory.

Future performance commands are stored per row in
`reference/citibike443-regional-v1/manifests/T_scenario_manifest.csv`.  They are documentation
only in this round.  A recommended next experiment is a preregistered structural
screen of all 960 rows followed by a balanced subset comparing K1-AM-SF and
P-GRB, using identical T, one thread, fixed solver budgets and no result-based
instance replacement.
