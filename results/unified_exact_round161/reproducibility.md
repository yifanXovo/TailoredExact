# Bounded Round161 reproduction

The dependency is verified R160 delivery 53e5c62fbcf6bc24898b7d5d3ecb755e4331ab0b;
the branch is codex/round161-full-physical-rn. Work only under
E:/codes/ExactEBRP-work. WORKSPACE_POLICY.md applies. Stable GI-TBC/B and
historical main comparison data were not replaced.

The actual measured core C++ is pinned by measured_manifest.json (v3);
the RN-P C++/PE is separately pinned by measured_manifest_RNP.json (v6).
Qualification v1/v2/v5 and a failed v4 compile are separate, never promoted
to full-bridge or complete-method performance. Raw changed-source bytes are
inside the new evidence carrier, indexed by their actual SHA256. The later
clean CMake executable is an engineering build, not a measured sample.

Use the installed GNU C++17 toolchain and Gurobi 13.0.2 listed in the manifests.
A source build enables EXACT_EBRP_ENABLE_GUROBI=ON and the default-OFF option
EXACT_EBRP_BUILD_ROUND161_RESEARCH=ON, with GUROBI_ROOT pointing at the local
win64 installation. Build target Round161Research. The exact single-job
clean configure/build commands are in engineering/cmake_delivery.json.
No optimization, fast-math or tolerance override was introduced.

The standalone CLI is:

    Round161Research input T tp td lambda parent.txt output OLD|RN|RN-P LP|MIP seconds nodes

Use a new output directory. The finite bridge uses 300s/-1 for LP and
900s/4096 for MIP, Seed0/Threads1/MIPFocus0. A complete Native call would
pass -1 (unlimited nodes); no complete H/helper candidate was entered here.
The explicit export mode writes models/registries/Start without Optimize.

Restore only the new carrier using public_manifest.json and its archive/member
hashes. The two original input blobs use fixed commit/path/SHA references.
The offline old parent source has fixed R160 archive/member hashes in
input_manifest.json; no old archive download is required for a bounded readback.
Each NEW journal's call-0 witness already contains the same complete parent
routes/operations. To reconstruct parent.txt, write route count, then each
vehicle and complete node list (with its length), then pickup-drop for the
interior nodes. This is the unchanged C++ route input format.

scripts/round161_analyze.py, round161_envelope_diagnostic.py and the separate
round161_review.py read saved current-round evidence only. The final verifier
extracts only the existing R157 physical verify function's AST; no old imports,
producer, solver or old budget controller execute. The plot uses an isolated
Matplotlib target under the work-root temp directory and a task-local config
cache. Plot dependency installation and public I/O are separate costs.

The commercial DLL/license/credentials are excluded. The actual measured PEs,
objects and old verified archive remain available locally at their manifest
paths; public byte-identical PE reconstruction is not claimed. Source/model/
route/parameter/evidence recovery requires no Optimize and no old producer.
The finite anonymous public recovery and post-PR bounded cleanup receipts
are written by the delivery metadata commit.
