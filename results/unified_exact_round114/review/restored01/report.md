# Round114 independent restored-root review

**Decision: ACCEPT_RESTORED_BLOCKED_EVIDENCE.** The restored evidence is complete under its manifest, and the already performed offline reconstruction reproduces all 33 packaged core result files exactly. This accepts the restored **BLOCKED evidence delivery**. It does not certify completion of the four-method collection, native solver reproducibility, new scientific qualifications, a Git commit, or a remote publication.

Review identity: independent subagent `/root/whole_goal_review`, review `restored01`. Observation began 2026-10-11T16:23:40.5172346+00:00; signature preparation was timestamped 2026-10-11T16:33:19.0204884+00:00.

## Scope and isolation

Artifact reads were confined to `E:/codes/ExactEBRP-round114-public` and `E:/codes/ExactEBRP-round114-restored`. All shell commands used the restored root as their working directory. No original Round114 worktree, earlier worktree, Git checkout fallback, repository object, or remote was read for this review. No solver, qualification driver, compiler, formal arm, or additional complete reader reconstruction was started.

The only added files are this report and `signed_review.json` in `review/restored01/`. Existing restored members, sources, raw records, clocks, and permissions were not edited. These two files are subsequent review receipts outside the scientific carrier; acceptance does not require repacking that carrier.

## Independently checked byte closure

The public carrier is one 43,954,162-byte `evidence.tar.gz`, SHA256 `132a2011ffaa3c271156c7cec1813c48541a52591e7bf80f41cabefc77e70b71`, with no parts and below 95 MiB. The manifest SHA256 is `b541248c7a12fce4a4768adc7d0903f3d3a207056841e0d71da705139c044d28`.

I streamed all 4,850 regular archive members and read their restored counterparts. Every archive and restored member matched its manifest size and SHA256; total member bytes were 417,755,054. The archive contained no duplicate, symlink, special, absolute, or escaping member. The candidate/admission source maps were checked against the manifest and the restored bytes: all 206 source files and 47 runtime helpers matched. Candidate, admission, dependency-closure, restore, reader, and public-export receipts have explicit path/SHA bindings in the signature.

The public standalone restorer SHA256 is `c3380da4ac002bb2d794ea3d17103eaba3991b74bb022453b557b4145fc3bc36`. Its restore path validates its own manifest identity, requires a destination that does not already exist, validates every extracted member, and rejects path escape and non-regular members. The root `restore_receipt.json` records an actual successful empty-root restoration with rc 0, zero Optimize calls, and 3.6425462999613956 seconds of measured engineering time. This review verified the restored member bytes; it did not repeat extraction.

## Offline reconstruction and root binding

The actual pre-existing explicit-root reconstruction receipt is `engineering/restored_reader01/receipt.json`; output is in `rebuilt/`. It records rc 0, zero Optimize calls, 15.1394345 seconds of actual engineering time, field limit 67,108,864, and no original-worktree fallback.

I independently compared all 33 core JSON/CSV files in `rebuilt/` with `results/unified_exact_round114/reports_final/`. Every parsed field was equal, including the reader identity, and every corresponding file SHA256 was equal. The comparison included 27,188 CSV fields. The signature retains the 33 exact file hashes.

The final reader SHA256 is **`625692f6091a93c49bb08fbcd78ea4c9a74924da705cfafae22def74a0369ef1`**. The portable-path implementation resolves supported artifact prefixes under the explicit restored root and rejects unsupported absolute paths. Static inherited runner constants do not establish an artifact fallback for this reconstruction. The corrected packaged whole-goal signature also binds this final reader; its SHA256 is `16a82d5dec9fd52d2c88fe80cc7ba683a8cd324bd765336680aa10b4e5fcd03d`. The intermediate reader/report snapshots remain historical evidence, with their disclosed identities.

## Preserved scientific result

The reconstructed result remains **BLOCKED**. Four formal positions were planned; only P-GRB and M-ENS were actually executed. P-GRB is the one new qualified formal measurement, with formal U 0.03994210048354935 and whole-arm time 3573.223369550775 seconds. M-ENS returned normally at the native level but its true whole-arm time was 3605.688342700014 seconds, exceeding the frozen 3600-second gate. Its qualified endpoint, gap, and certificate are null, and its formal-performance flag is false. P-S and M-B remain unstarted. This cap failure cannot be converted to qualification by restoration, reader repair, or a rerun.

The inherited 15 qualified measurements plus P-GRB give 16. The old 21 evaluable pairs remain 21; all six new pairs remain unevaluable, with null deltas. The old G50 cold P3 missing endpoint/whole-arm fields remain null. Both vectors remain incomplete attribution. No restored diagnostic is promoted into a paired formal result.

The frozen fee records remain closed: 11 conservative starts and 7368.394686511601 seconds, with no pending fee. This review added zero native/qualification starts. It accepts the preserved clocks and qualification rules; it does not certify a successful completion of all four methods or an upgraded scientific conclusion.

## Exclusions and limits

No carrier member had a forbidden executable, DLL, license, private-key, or credential filename/extension under the checked list. No actual standalone PEM private-key header or WLSSecret/WLSAccessID parameter output was found in the checked log/JSON/JSONL/text records. The private-key marker in the public restorer is a scanner string literal, not a private key. This is a specifically scoped artifact/record check, not proof that arbitrary secrets can never exist.

Native executable/DLL/license artifacts are deliberately excluded from this evidence carrier. Their recorded identities and prior raw execution evidence are retained, but this review neither reconstructs a licensed native runtime nor reproduces solver execution. It does not independently determine hidden Gurobi internal causes, check Git blobs, confirm the reported scientific commit or push, or verify a PR. Those require their own receipts and authority.

## Actual engineering time

The independently executed member/hash/core comparison took **6.190451100002974 seconds**. The review's observed UTC wall interval through signature preparation was **578.5032538 seconds**; it includes inspection, reasoning, and this comparison. The comparison duration is nested in that wall interval and must not be added again.

Restoration (3.6425462999613956 seconds) and the earlier explicit-root reader (15.1394345 seconds) are separate actual receipt times, performed before this review. They are engineering times, not solver time. Subsequent file persistence/final handoff time, CPU/human/orchestration breakdown, and any unmeasured duration are **unknown**, not zero.

Initial review probes used an incorrect receipt prefix, assumed an incorrect manifest property, and overmatched the restorer's scanner literal. Each was corrected within the allowed roots. These were read-only review probe errors, with no alteration of the payload, no failed native execution, and no scientific reinterpretation.

Signed evidence and all limitations are in `signed_review.json`.

