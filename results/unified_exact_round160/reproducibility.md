# Round160 fixed evidence and reproduction

The measured C++ source commit is `d1da99b85219f4f0a1b5a703fc6ebf1c6dee4431`,
on dependency `51473276867e802ce729aae3d4a2563ea23a8fe8`. Frozen PE, source,
compiler, DLL, object/archive and command hashes are in candidate_manifest.json.
The standalone v3 and v4 identities differ; engineering/build_v3.json and
runtime_recovery.json identify the actual core-v1/v2 science executable.
The later CMake import-library dependency fixes clean linking only. Its build
is separately recorded in engineering/cmake_delivery.json and is not a sample.

Use a checkout of the final science commit identified in publication.json.
The public_manifest hashes actual staged Git bytes, not working-tree CRLF
assumptions. Its self hash and science commit are recorded in the recovery
receipt. All archives and their member indexes are under artifacts. Restore
only these new archives and the four old input Git blobs listed in the manifest;
no old archive replay is required. Extract members relative to the checkout,
rejecting absolute or parent-traversal paths. Verify archive/member SHA256 and
lengths. Public restoration performs no compilation or Optimize.

The one actual anonymous public recovery is recorded in
public_restore_receipt.json; its finite implementation is
scripts/round160_delivery.py::restore. Source scripts and proof/physical raw
evidence remain public; measured project executables and the commercial DLL
are retained locally, excluded from public carriers along with credentials
and protected dirty-file inventories. A fresh clean compile is not asserted
bit-identical to the measured timestamp-bearing PE.

For a new licensed local build, CMake enables the optional Gurobi backend via
EXACT_EBRP_ENABLE_GUROBI=ON and GUROBI_ROOT, and the standalone tool via
EXACT_EBRP_BUILD_ROUND160_RESEARCH=ON. Use the recorded GNU C++17 flags without
optimization/fast-math changes. The production switch is default off:
--round160-physical-neighborhood on additionally requires the frozen E+
gcap-frontier/ms2/RN/proof-only settings. Do not treat a new execution as a
repeat of the saved performance sample or launch it as part of recovery.

confirmation_matrix.json and each group identity/launch/PID record bind all
eight fresh production commands and inputs. The campaign owns an eight-arm
matrix/admission/loop, rather than calling the hard-coded R156 freeze. Saved
round160_endpoint.json files and reports/complete.csv separate T_produce,
T_verify, T_total and T_cert. A qualified open certificate state is not an
actual certificate. Only RX20T1 has a time to certificate. Local calls are
added to common-RN and engine counts because the old journal omits them.

For physical review, trajectory_analysis_v1/v2 contain every accepted
Y/owner/route/operation and original-J decomposition. Each raw block includes
its full parent, B, actual cuts, run summaries, MPS, complete Start and Native
log/result. The formal on-arm round160 trees retain the same details.
The same-agent final saved-evidence audit checks original T and Fraction J,
outside inventories/owners, indivisible runs/order, one actual saved matrix
solution, own-state provenance, single deadlines, identities and proof-source
separation without Optimize. final_review.json records the actual PASS. This
does not claim independent personnel or exact global proofs from local MIPs.

All scientific fees, including failures and final reporting correction, are
closed in cost_report.json. Compile/public I/O is separate. Later public I/O
fees and cleanup are delivery metadata; a science snapshot cannot contain its
own later recovery receipt. The fixed science commit is therefore retained
while the normal delivery head advances, without force push or self-reference
commits. No old producer, P-GRB benchmark, full-fleet UNKNOWN fallback or
multi-Seed sweep is required for this round's finite conclusion.
