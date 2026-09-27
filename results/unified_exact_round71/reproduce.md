# Reproduction and audit entry points

Use branch codex/round71-interroute-descent and the source freeze in
build_v1.json. The qualified local build is build/round71. Source199-file
hashes, binary/reference-binary hashes, tests, native runtime versions and
input identities are recorded. Later changed source is a different identity;
do not run earlier-stage packagers from this working tree.

Runtime: D:/msys64/ucrt64/bin/python.exe, GNU14.2.0 MinGW, Gurobi13.0.2 and the
Visual Studio bundled CMake. Release uses EXACT_EBRP_ENABLE_GUROBI=ON and
GUROBI_ROOT=D:/gurobi1302/win64. Direct executables need D:/msys64/ucrt64/bin
and D:/gurobi1302/win64/bin first on PATH; the owned launcher supplies this.
All measured arms inherit logical processor2/mask4 and retain actual readback.

After the optimizer queue stops, regenerate derived audits and tables:

```powershell
D:/msys64/ucrt64/bin/python.exe scripts/package_round71.py
D:/msys64/ucrt64/bin/python.exe scripts/round71_startup_analysis.py
D:/msys64/ucrt64/bin/python.exe scripts/round71_checkpoints.py
D:/msys64/ucrt64/bin/python.exe scripts/round71_report.py
D:/msys64/ucrt64/bin/python.exe scripts/round71_delivery.py
```

These commands make zero optimizer calls. The last checks packaged hashes,
lossless content and exact result-summary fields. They check frozen source/binary,
physical routes, full frontier, original P fingerprints, native parameters,
submitted/readback Start vectors and actual model rows. The descent audit
checks actual cross-route generated/decoded/accepted counts, strict gain and
terminal exhaustion. Executed native logs must identify Gurobi13.0.2; no DLL
hash was frozen. They write current-stage derived evidence only. Add --complete
to the report after stage_decision.json records the completed bounded campaign
or the predeclared reason for leaving its remaining panel unopened.

The checkpoint helper uses process clocks and full verified-event hashes,
never generation0 or backdated final routes. It retains signed bounds and the
limitations of buffered intermediate telemetry. Only same-cap final endpoints
enter performance pairs. A startup-only global deadline is independently
qualified with analytical LB0 and cannot invent a tree or certificate.

To intentionally open a separately charged fresh replay of identical bytes:

```powershell
D:/msys64/ucrt64/bin/python.exe scripts/round71_reproduce.py --output build/round71_fresh_small --ids E7 S12 N12 --arms P-GRB DS DS-X --cap 120
```

The helper rejects overwrites, active original queues, changed source/binary,
duplicate roles/arms, undeclared combinations and inconsistent caps. It marks
the49 earlier CTests and39 native qualification calls as inherited, not newly
executed. This replay helper is provided, not run as an extra stage experiment.
A new build requires separate qualification and fresh matched controls.

Committed evidence contains full physical witnesses, lossless CSV/gzip data,
exact selected result fields and content/source manifests. Large raw models,
complete native logs and binaries remain local at manifest paths. This stage
reports numerical certification under original tolerances, not rational proof.
