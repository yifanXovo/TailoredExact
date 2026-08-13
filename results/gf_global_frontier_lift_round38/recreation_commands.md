# Round 38 recreation commands

Run from the repository root with the existing licensed child environment.
The runner injects the license path into each child process and never writes
credentials into artifacts.  Every stage is serial, checksum-resumable, and
refuses to overwrite an incomplete or identity-mismatched run.

```powershell
D:\msys64\ucrt64\bin\python.exe scripts\freeze_round38_smoke.py
D:\msys64\ucrt64\bin\python.exe scripts\run_round38_smoke.py
D:\msys64\ucrt64\bin\python.exe scripts\analyze_round38_smoke.py

D:\msys64\ucrt64\bin\python.exe scripts\freeze_round38_diagnostic.py
D:\msys64\ucrt64\bin\python.exe scripts\run_round38_diagnostic.py
D:\msys64\ucrt64\bin\python.exe scripts\analyze_round38_diagnostic.py

D:\msys64\ucrt64\bin\python.exe scripts\freeze_round38_confirmation.py
D:\msys64\ucrt64\bin\python.exe scripts\run_round38_confirmation.py
D:\msys64\ucrt64\bin\python.exe scripts\analyze_round38_confirmation.py

D:\msys64\ucrt64\bin\python.exe scripts\finalize_round38_evidence.py
D:\msys64\ucrt64\bin\python.exe scripts\audit_round38_final.py
```

The frozen matrices, commands, input checksums, executable checksum, source
fingerprints, per-run artifact manifests, and completion markers provide the
reproduction identities.  `smoke_runs/`, `diagnostic_runs/`,
`confirmation_runs/`, and `invalidated_attempts/` are intentionally ignored;
their compact hashes are in `local_raw_manifest.csv` and the invalidated
attempt manifest/summary.
