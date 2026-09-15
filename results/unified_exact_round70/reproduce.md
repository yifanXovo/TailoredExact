# Reproduction and artifact locations

Use the owned research branch codex/round70-vds-descent. Revision1 is a failed
qualification, retained under this root. Accepted campaign data and frozen
source/binary identities are under revision2/. Its build is build/round70_v2.
All clocks include complete paid startup and proof work on logical CPU2/mask4.

The local runtime is D:/msys64/ucrt64/bin/python.exe, with MinGW GNU14.2.0,
Gurobi13.0.2 and the Visual Studio bundled CMake. Release configuration uses
EXACT_EBRP_ENABLE_GUROBI=ON and GUROBI_ROOT=D:/gurobi1302/win64. Put
D:/msys64/ucrt64/bin and D:/gurobi1302/win64/bin first on PATH when running
executables directly. The Python launcher sets this for its owned child.

Read-only audit after the optimizer queue stops:

```powershell
D:/msys64/ucrt64/bin/python.exe scripts/package_round70.py
D:/msys64/ucrt64/bin/python.exe scripts/round70_startup_analysis.py
```

The package checks current source and executable against the frozen identity;
do not run it from a later changed source tree. It verifies routes, complete
frontier, original P fingerprints, native parameters, submitted/readback Start
vectors, actual model rows and DS descent records. It writes only revision2
analysis and compact evidence, never historical-stage or raw solver data.

Fresh same-byte replay into a new local directory, only when intentionally
opening a separately charged campaign:

```powershell
D:/msys64/ucrt64/bin/python.exe scripts/round70_reproduce.py --output build/round70_fresh_small --ids E7 S12 N12 --arms P-GRB VD-S DS --cap 120
```

This helper refuses overwrites, duplicate roles/arms, undeclared arm-role
combinations, inconsistent caps, an active original queue and changed binaries
or source. It is provided but not executed as an extra stage experiment.
Previously executed qualification is marked inherited in replay outputs.
Building elsewhere produces a new experimental identity; qualify it and run
fresh matched controls rather than pooling its timings with this campaign.

Committed compact evidence includes lossless CSV/log excerpts or gzip copies,
selected exact result fields, full physical endpoint witnesses and manifests.
Large raw models, complete native logs and executables remain under the local
paths in launch/build/model manifests. Original numerical certification is
reported as such; no strict rational certificate is produced.
