# Round 52 reproduction commands

Run from the repository root on the recorded Windows/Gurobi environment. Every native process is bounded by the runner's 1800-second process cap.

```powershell
$py = 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$exe = 'build/round52/ExactEBRP.exe'

# Rebuild and unit/live-test the frozen source.
& 'D:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe' --build build/round52 --config Release
ctest --test-dir build/round52 --output-on-failure

# Recreate the deterministic independent inputs and certificate preflight.
& $py scripts/generate_round52_validation_instances.py
& $py scripts/run_round52_fingerprint_preflight.py --panel validation --executable $exe
& $py scripts/run_round52_fingerprint_preflight.py --panel holdout --executable $exe

# Reproduce/resume the 48 official final rows.
foreach ($panel in @('validation', 'holdout')) {
  foreach ($method in @('P-GRB', 'K1-AM-FINAL')) {
    & $py scripts/run_round52_final_panel.py --panel $panel --method $method --executable $exe
  }
}

# Rebuild all compact audits and verify their strict gates.
& $py scripts/finalize_round52_final_panels.py
Get-FileHash -Algorithm SHA256 $exe
```

The expected executable hash is `d245c76f6397c757894610d8f5238cfeb971761ff7e05edf51058e451d810151`. The P-GRB fingerprint preflight is certificate plumbing only; it must complete before official P-GRB bound rows and does not authorize source or algorithm changes.
